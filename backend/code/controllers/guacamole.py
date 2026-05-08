import re
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from rq import Queue, Retry
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.config import Settings
from core.exceptions import (
    BadRequestError,
    InvalidOperationForObject,
    JobEnqueueError,
    ObjectDeleteIntegrityError,
    ObjectNotFound,
    OperationDependencyMissing,
)
from core.guacamole import (
    guacamole_delete,
    guacamole_delete_worker,
    guacamole_hostname_update,
    provision_guacamole,
    provision_guacamole_worker,
)
from core.redis import queue_guacamole
from middlewares.i18n import _
from models import (
    Changelog,
    Event,
    Guacamole,
    GuacamoleConnectionProfile,
    ObjectPermission,
    SubTask as SubTaskModel,
    Tag,
    Task as TaskModel,
    User,
    VirtualMachine,
)
from schemas.guacamole import GuacamoleCreate, GuacamoleUpdate
from schemas.sub_tasks import SubTaskCreate
from schemas.tasks import TaskCreate

from .base import CRUDBase
from .object_permissions import CRUDObjectPermission
from .sub_tasks import CRUDSubTask
from .tasks import CRUDTask

settings = Settings()


class CRUDGuacamole(CRUDBase[Guacamole, GuacamoleCreate, GuacamoleUpdate]):
    def __init__(self, db: Session = None, id: Any = None):
        self.model = Guacamole
        self.db_obj = db.get(Guacamole, id) if id is not None else None

    # Get Guacamole by name
    def get_by_name(self, db: Session, *, name: str) -> Guacamole | None:
        guac = db.query(Guacamole).filter(Guacamole.name == name).first()
        return guac

    def _update_subtask_job_id(
        self, db: Session, sub_task_id: Any, job_id: Any
    ):
        sub_task = CRUDBase(SubTaskModel).get(db, sub_task_id)
        sub_task.job_id = job_id
        db.add(sub_task)
        self._commit(db)

    def _subtask_guacamole_provision(
        self,
        db: Session,
        request: Request,
        parent_task_id: Any,
        queue: Queue,
        user: User,
        connection_profile: GuacamoleConnectionProfile,
        virtual_machine: VirtualMachine,
        db_obj_id: Any = None,
        task_dependencies: list = None,
    ):
        guac_id = db_obj_id if db_obj_id is not None else self.db_obj.id
        guac_object = self._get(db, guac_id)
        # Create SubTask objects and enqueue job (Provision)
        sub_task_provision_schema = SubTaskCreate(
            name="Provision Guacamole connection",
            object_type="Guacamole",
            object_id=guac_object.id,
            action="guacamole_provision",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_provision = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_provision_schema
        )
        if not task_dependencies:
            job_provision = queue.enqueue(
                provision_guacamole_worker,
                username=user.username,
                connection_name=guac_object.name,
                connection_hostname=virtual_machine.ipv4,
                kvs_gcp_id=connection_profile.id,
                kvs_task_object_id=sub_task_provision.id,
                kvs_guacamole_id=guac_object.id,
                kvs_vm_id=virtual_machine.id,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_provision = queue.enqueue(
                provision_guacamole_worker,
                username=user.username,
                connection_name=guac_object.name,
                connection_hostname=virtual_machine.ipv4,
                kvs_gcp_id=connection_profile.id,
                kvs_task_object_id=sub_task_provision.id,
                kvs_guacamole_id=guac_object.id,
                kvs_vm_id=virtual_machine.id,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_provision:
            raise JobEnqueueError(job_key="guacamole_provision")
        self._update_subtask_job_id(db, sub_task_provision.id, job_provision.id)
        return job_provision

    def _subtask_guacamole_delete(
        self,
        db: Session,
        parent_task_id: Any,
        queue: Queue,
        request: Request = None,
        task_dependencies: list = None,
    ):
        # Create SubTask objects and enqueue job (GUAC_DELETE)
        sub_task_guac_delete_schema = SubTaskCreate(
            name="Delete Guacamole connections",
            object_type="Guacamole",
            object_id=self.db_obj.id,
            action="guac_delete",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_guac_delete = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_guac_delete_schema
        )
        if not task_dependencies:
            job_guac_delete = queue.enqueue(
                guacamole_delete_worker,
                kvs_guacamole_id=self.db_obj.id,
                kvs_task_object_id=sub_task_guac_delete.id,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_guac_delete = queue.enqueue(
                guacamole_delete_worker,
                kvs_guacamole_id=self.db_obj.id,
                kvs_task_object_id=sub_task_guac_delete.id,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_guac_delete:
            raise JobEnqueueError(job_key="guac_delete")
        self._update_subtask_job_id(
            db, sub_task_guac_delete.id, job_guac_delete.id
        )
        return job_guac_delete

    # Create Guacamole
    def create(
        self, db: Session, request: Request, *, obj_in: GuacamoleCreate
    ) -> Guacamole:
        obj_in_data = jsonable_encoder(obj_in)
        # Check if provided connection_profile exists
        connection_profile = CRUDBase(GuacamoleConnectionProfile).get(
            db=db, id=obj_in.connection_profile
        )
        # Check if VirtualMachine.ipv4 is valid
        if connection_profile.objectType != "VirtualMachine":
            raise InvalidOperationForObject(
                operation="guacamole_create",
                object_type=connection_profile.objectType,
            )
        virtual_machine = CRUDBase(VirtualMachine).get(
            db=db, id=connection_profile.objectId
        )
        if not virtual_machine.ipv4 or virtual_machine.ipv4 == "0.0.0.0":
            raise OperationDependencyMissing(
                message=_("VirtualMachine does not have a valid IPv4 address.")
            )
        # Initialise new model object
        self._initialize_object_fields(
            db=db, obj_data_in=obj_in_data, request=request
        )
        # Check if provided userId exists
        user = db.get(User, obj_in.userId)
        if not user:
            raise ObjectNotFound(
                id=self.db_obj.userId, model_name=User.__name__
            )
        # Check if provided eventId exists
        if obj_in.eventId:
            event = CRUDBase(Event).get(db=db, id=obj_in.eventId)
            self.db_obj.eventId = event.id
        self.db_obj.userId = user.id
        self.db_obj.connection_profile = connection_profile.id
        self.db_obj.name = str(self.db_obj.name)[:100]
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        virtual_machine.guacamoles.append(self.db_obj)
        db.add(virtual_machine)
        db.commit()
        db.refresh(self.db_obj)
        db.refresh(virtual_machine)
        # Create Task object
        new_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(
                name=f"Provision Guacamole connection for {user.username}",
            ),
        )
        self._subtask_guacamole_provision(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_guacamole,
            user=user,
            connection_profile=connection_profile,
            virtual_machine=virtual_machine,
        )
        CRUDObjectPermission(ObjectPermission).create_full(
            db, request, "Guacamole", self.db_obj.id, user.id
        )
        return self.db_obj

    # Update Guacamole
    def update(
        self, id: Any, db: Session, request: Request, *, obj_in: GuacamoleUpdate
    ) -> Guacamole | None:
        self.db_obj = self.get(db, id)
        obj_data = jsonable_encoder(self.db_obj)
        update_data = self._merge_request_with_db_object(obj_in, obj_data)
        self._update_meta(request)
        return self._commit(db, self.db_obj)

    # Delete object with ID
    def delete(self, db: Session, id: Any) -> Guacamole | None:
        self.db_obj = self.get(db, id)
        try:
            check = guacamole_delete(identifier=self.db_obj.identifier)
            if not check:
                raise BadRequestError(message=str(check))
            db.delete(self.db_obj)
            changelogs = db.query(Changelog).filter(Changelog.objectId == id)
            for changelog in changelogs:
                db.delete(changelog)
            object_permissions = db.query(ObjectPermission).filter(
                ObjectPermission.object_id == id
            )
            for perm in object_permissions:
                db.delete(perm)
            tags = db.query(Tag).filter(
                Tag.objectId == id, Tag.objectType == self.model.__name__
            )
            for tag in tags:
                db.delete(tag)
            db.commit()
            return {
                "detail": _("{model} with ID {id} has been deleted.").format(
                    model=self.model.__name__, id=id
                )
            }
        except IntegrityError:
            raise ObjectDeleteIntegrityError(model_name=self.model.__name__)
        except Exception as e:
            raise BadRequestError()

    # Provision Guacamole connection
    def provision(self, db: Session, id: Any) -> Guacamole | None:
        self.db_obj = self.get(db, id)
        # Check if Guacamole has already been provisioned
        if self.db_obj.identifier:
            raise BadRequestError(
                message=_("Guacamole connection has already been provisioned")
            )
        # Check if provided connection_profile exists
        connection_profile = CRUDBase(GuacamoleConnectionProfile).get(
            db=db, id=self.db_obj.connection_profile
        )
        # Check if VirtualMachine.ipv4 is valid
        virtual_machine = CRUDBase(VirtualMachine).get(
            db=db, id=connection_profile.objectId
        )
        if not virtual_machine.ipv4 or virtual_machine.ipv4 == "0.0.0.0":
            raise OperationDependencyMissing(
                message=_("VirtualMachine does not have a valid IPv4 address.")
            )
        event_slug = None
        if virtual_machine.event:
            event = CRUDBase(Event)._get(db=db, id=virtual_machine.event)
            if event:
                event_slug = event.slug
        # Check if provided userId exists
        user = db.get(User, self.db_obj.userId)
        if not user:
            raise ObjectNotFound(
                id=self.db_obj.userId, model_name=User.__name__
            )
        # Replace placeholder text in name if Guacamole was created for an Event
        self.db_obj.name = re.sub(
            r"(?<=-)(PROV)(?=-)",
            str(virtual_machine.proxmoxId),
            self.db_obj.name,
        )
        # Provision Guacamole connection
        guac_provision = provision_guacamole(
            username=user.username,
            connection_name=self.db_obj.name,
            connection_hostname=virtual_machine.ipv4,
            connection_port=connection_profile.port,
            connection_username=connection_profile.username,
            connection_password=connection_profile.password,
            connection_protocol=connection_profile.protocol.lower(),
            event_slug=event_slug,
        )
        # Save identifier on success
        if isinstance(guac_provision, int):
            self.db_obj.identifier = guac_provision
            self._update_meta()
            self.db_obj = self._commit(db, self.db_obj)
        else:
            raise BadRequestError(
                message=_(
                    "The following error occurred while provisioning Guacamole connection: {guac_provision}"
                ).format(guac_provision=guac_provision)
            )
        return self.db_obj

    def update_hostname(
        self, db: Session, id: Any, hostname: str
    ) -> Guacamole | None:
        self.db_obj = self.get(db, id)
        # Check if Guacamole has been provisioned
        if not self.db_obj.identifier:
            raise BadRequestError(
                message=_(
                    f"Guacamole connection '{self.db_obj.name}' has not been provisioned."
                )
            )
        connection_profile = db.get(
            GuacamoleConnectionProfile, self.db_obj.connection_profile
        )
        # Update Guacamole connection hostname
        guac_resp = guacamole_hostname_update(
            identifier=self.db_obj.identifier,
            connection_name=self.db_obj.name,
            connection_hostname=hostname,
            connection_protocol=connection_profile.protocol,
        )

        if isinstance(guac_resp, str):
            raise BadRequestError(
                message=_(
                    "The following error occurred while updating Guacamole connection '{guac_name}' hostname: {guac_resp}"
                ).format(guac_name=self.db_obj.name, guac_resp=guac_resp)
            )

        # Update DB record with new hostname
        self.db_obj.connection_hostname = hostname
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj


guacamole = CRUDGuacamole(Guacamole)
