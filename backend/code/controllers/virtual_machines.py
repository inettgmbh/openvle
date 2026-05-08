import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from proxmoxer.core import ResourceException
from pydantic import UUID4
from rq import Queue, Retry
from sqlalchemy import and_
from sqlalchemy.orm import Session

from core.config import Settings
from core.core_utils import (
    get_system_user,
    request_user_validation,
    vm_ip_in_subnet,
)
from core.exceptions import (
    BadRequestError,
    BulkActionRequirementMissing,
    BulkObjectNotFound,
    InvalidFieldValue,
    JobEnqueueError,
    ObjectNotFound,
    OperationDependencyMissing,
    ProtectedObjectError,
    ProxmoxConnectionError,
    ProxmoxRequestError,
    ProxmoxResourceNotFound,
    RequiredParameterMissingError,
)
from core.guacamole import guacamole_delete_worker
from core.messages import msg_vm_already_running, msg_vm_already_stopped
from core.redis import queue_guacamole, queue_pve_vm_actions, queue_pve_vm_clone
from models import (
    Application,
    Changelog,
    Event,
    EventsUser,
    Guacamole,
    GuacamoleConnectionProfile,
    Mail,
    ObjectPermission,
    Role as RoleModel,
    Tag,
    Template,
    User,
    VirtualMachine,
)
from models.sub_tasks import SubTask as SubTaskModel
from models.tasks import Task as TaskModel
from pve.cluster import ProxmoxCluster
from pve.pve_node_info import get_pve_node_info, proxmox_node_info_periodic
from pve.virtual_machines import ProxmoxVirtualMachine
from schemas.guacamole_connection_profiles import (
    GuacamoleConnectionProfileCreate,
)
from schemas.proxmox import (
    ProxmoxRRDConsolidation,
    ProxmoxRRDTimeframe,
)
from schemas.sub_tasks import SubTaskCreate
from schemas.tasks import TaskCreate
from schemas.virtual_machines import (
    VirtualMachineBulkHaAdd,
    VirtualMachineClone,
    VirtualMachineCreate,
    VirtualMachineEventCreate,
    VirtualMachineHaAdd,
    VirtualMachineIdList,
    VirtualMachineMigrate,
    VirtualMachineUpdate,
    VirtualMachineUpdateApps,
)

from .base import CRUDBase
from .changelog import CRUDChangelog
from .guacamole import CRUDGuacamole
from .guacamole_connection_profiles import CRUDGuacamoleConnectionProfile
from .mails import CRUDMail
from .object_permissions import CRUDObjectPermission
from .sub_tasks import CRUDSubTask
from .tags import CRUDTag
from .tasks import CRUDTask

settings = Settings()
from middlewares.i18n import _


class CRUDVirtualMachine(
    CRUDBase[VirtualMachine, VirtualMachineCreate, VirtualMachineUpdate]
):
    def __init__(self, db: Session = None, id: Any = None):
        self.model = VirtualMachine
        self.db_obj = db.get(VirtualMachine, id) if id is not None else None
        self.vm_list = None

    # Get VM by name
    def get_by_name(self, db: Session, *, name: str) -> VirtualMachine | None:
        return (
            db.query(VirtualMachine).filter(VirtualMachine.name == name).first()
        )

    def _create_event_tag(self, db: Session, event_slug: str):
        new_tag = Tag(
            key="event",
            value=str(event_slug).lower(),
            objectId=self.db_obj.id,
            objectType="VirtualMachine",
            id=uuid.uuid4(),
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc),
            updatedById=get_system_user(db).id,
            createdById=get_system_user(db).id,
        )
        db.add(new_tag)
        db.commit()
        db.refresh(new_tag)
        return new_tag

    # Create VM based on a template
    def create_from_template(
        self, db: Session, request: Request, *, obj_in: VirtualMachineCreate
    ) -> VirtualMachine:
        obj_in_data = jsonable_encoder(obj_in)
        CREATE_GUACAMOLE = True if obj_in.create_guacamole else False
        obj_in_data.pop("create_guacamole")
        self._initialize_object_fields(
            db=db, obj_data_in=obj_in_data, request=request
        )
        source_template = CRUDBase(Template).get(db, self.db_obj.template)
        if not source_template.proxmoxId:
            raise OperationDependencyMissing(
                message=_("Source Template has no proxmoxId")
            )
        if source_template.apps:
            self.db_obj.apps = source_template.apps
        self.db_obj.template = source_template.id
        self.db_obj.os = source_template.os
        self.db_obj.disk = source_template.disk
        self.db_obj.name = str(self.db_obj.name)[:100]
        # Check Template operating system
        try:
            # PVE connection
            proxmox = ProxmoxCluster().proxmox
            template_conf = (
                proxmox.nodes(
                    ProxmoxCluster().pve_get_node(source_template.proxmoxId)
                )
                .qemu(source_template.proxmoxId)
                .config.get()
            )
        except:
            raise ProxmoxConnectionError()
        template_os_type = template_conf["ostype"]
        self.db_obj = self._commit(db, self.db_obj)
        # Create tags for new VM based on template_conf
        source_template_tags = template_conf.get("tags")
        if source_template_tags:
            CRUDTag(Tag)._inherit_tags(
                db=db,
                source_object_id=source_template.id,
                target_object_id=self.db_obj.id,
                source_object_type="Template",
                target_object_type="VirtualMachine",
            )
        deploy_jobs = []
        # Create Task object
        new_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(name=f"Create VirtualMachine {self.db_obj.name}"),
        )
        job_clone = self._subtask_template_clone(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_clone,
        )
        deploy_jobs.append(job_clone)
        job_update = self._subtask_update(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_actions,
            task_dependencies=[job_clone],
        )
        deploy_jobs.append(job_update)
        # Assign or retrieve IP based on settings.pve_ci_enabled
        if settings.pve_ci_enabled:
            match template_os_type:
                case os_type if os_type in [
                    "wxp",
                    "w2k",
                    "w2k3",
                    "w2k8",
                    "wvista",
                    "win7",
                    "win8",
                    "win10",
                    "win11",
                ]:
                    job_ha_add = self._subtask_ha_add(
                        db=db,
                        request=request,
                        parent_task_id=new_task.id,
                        queue=queue_pve_vm_actions,
                        task_dependencies=[job_clone, job_update],
                    )
                    deploy_jobs.append(job_ha_add)
                    job_ipv4_get = self._subtask_ipv4_get(
                        db=db,
                        request=request,
                        parent_task_id=new_task.id,
                        queue=queue_pve_vm_actions,
                        task_dependencies=[job_clone, job_update, job_ha_add],
                    )
                    deploy_jobs.append(job_ipv4_get)
                case os_type if os_type in ["l24", "l26", "solaris", "other"]:
                    job_ipv4_set = self._subtask_ipv4_set(
                        db=db,
                        request=request,
                        parent_task_id=new_task.id,
                        queue=queue_pve_vm_actions,
                        task_dependencies=[job_clone, job_update],
                    )
                    deploy_jobs.append(job_ipv4_set)
                    job_ha_add = self._subtask_ha_add(
                        db=db,
                        request=request,
                        parent_task_id=new_task.id,
                        queue=queue_pve_vm_actions,
                        task_dependencies=[job_clone, job_update, job_ipv4_set],
                    )
                    deploy_jobs.append(job_ha_add)
        else:
            job_ha_add = self._subtask_ha_add(
                db=db,
                request=request,
                parent_task_id=new_task.id,
                queue=queue_pve_vm_actions,
                task_dependencies=[job_clone, job_update],
            )
            deploy_jobs.append(job_ha_add)
            job_ipv4_get = self._subtask_ipv4_get(
                db=db,
                request=request,
                parent_task_id=new_task.id,
                queue=queue_pve_vm_actions,
                task_dependencies=[job_clone, job_update, job_ha_add],
            )
            deploy_jobs.append(job_ipv4_get)

        self.db_obj.status = "queued"
        CRUDObjectPermission(ObjectPermission).create_full(
            db, request, "VirtualMachine", self.db_obj.id, request.user.id
        )
        interfaces = db.query(GuacamoleConnectionProfile).filter(
            GuacamoleConnectionProfile.objectId == source_template.id,
            GuacamoleConnectionProfile.objectType == "Template",
        )
        new_interfaces = self._create_interfaces(db, request, interfaces)
        if CREATE_GUACAMOLE and new_interfaces:
            user = CRUDBase(User).get(db, request.user.id)
            for interface in new_interfaces:
                job_provision = self._create_and_enqueue_guacamole(
                    db=db,
                    request=request,
                    parent_task_id=new_task.id,
                    queue=queue_guacamole,
                    task_dependencies=deploy_jobs,
                    user=user,
                    interface=interface,
                )
        return self._commit(db, self.db_obj)

    # Create VM based on a template for an event
    def create_from_template_event(
        self,
        db: Session,
        request: Request = None,
        *,
        obj_in: VirtualMachineEventCreate,
    ):
        """
        Used during CRUDEvents.actions_start to deploy a VirtualMachine and Guacamole for an Event.
        ObjectPermissions are also created for the new VirtualMachine and Guacamole objects.
        Objects owned by a non-teacher have additional ObjectPermissions and Guacamole objects created for each teacher assigned to the Event.
        """
        user = CRUDBase(User).get(db, obj_in.user)
        event = CRUDBase(Event).get(db, obj_in.event)
        obj_in_data = jsonable_encoder(obj_in)
        obj_in_data.pop("user")
        obj_in_data.pop("event")
        obj_in_data.pop("create_guacamole")
        self._initialize_object_fields(
            db=db, obj_data_in=obj_in_data, request=request
        )
        source_template = CRUDBase(Template).get(db, obj_in.template)
        self.db_obj.template = source_template.id
        self.db_obj.os = source_template.os
        self.db_obj.disk = source_template.disk
        self.db_obj.event = event.id
        self.db_obj.name = str(self.db_obj.name)[:100]
        if source_template.apps:
            self.db_obj.apps = source_template.apps
        # Check Template operating system
        try:
            # PVE connection
            proxmox = ProxmoxCluster().proxmox
            template_conf = (
                proxmox.nodes(
                    ProxmoxCluster().pve_get_node(source_template.proxmoxId)
                )
                .qemu(source_template.proxmoxId)
                .config.get()
            )
        except:
            raise ProxmoxConnectionError()
        template_os_type = template_conf["ostype"]
        self.db_obj = self._commit(db, self.db_obj)
        user.vms.append(self.db_obj)
        db.add(user)
        self._commit(db)
        db.refresh(user)
        db.refresh(self.db_obj)
        # Create Tag for Event
        event_tag = self._create_event_tag(db=db, event_slug=event.slug)
        # Create tags for new VM based on template_conf
        source_template_tags = template_conf.get("tags")
        if source_template_tags:
            CRUDTag(Tag)._inherit_tags(
                db=db,
                source_object_id=source_template.id,
                target_object_id=self.db_obj.id,
                source_object_type="Template",
                target_object_type="VirtualMachine",
            )
        # Create list to store worker tasks
        worker_tasks = []
        # Create Task object - VirtualMachine
        new_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(
                name=f"Create VirtualMachine from T{source_template.proxmoxId} for {user.username}",
                event_id=event.id,
            ),
        )
        # Create SubTask objects and enqueue jobs
        job_clone = self._subtask_template_clone(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_clone,
        )
        job_update = self._subtask_update(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_actions,
            task_dependencies=[job_clone],
        )
        job_tag_update = self._subtask_tags_update(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_actions,
            task_dependencies=[job_clone, job_update],
        )
        # Assign or retrieve IP based on settings.pve_ci_enabled
        if settings.pve_ci_enabled:
            match template_os_type:
                case os_type if os_type in [
                    "wxp",
                    "w2k",
                    "w2k3",
                    "w2k8",
                    "wvista",
                    "win7",
                    "win8",
                    "win10",
                    "win11",
                ]:
                    job_ha_add = self._subtask_ha_add(
                        db=db,
                        request=request,
                        parent_task_id=new_task.id,
                        queue=queue_pve_vm_actions,
                        task_dependencies=[job_clone, job_update],
                    )
                    job_ipv4_get = self._subtask_ipv4_get(
                        db=db,
                        request=request,
                        parent_task_id=new_task.id,
                        queue=queue_pve_vm_actions,
                        task_dependencies=[job_clone, job_update, job_ha_add],
                    )
                case os_type if os_type in ["l24", "l26", "solaris", "other"]:
                    job_ipv4_set = self._subtask_ipv4_set(
                        db=db,
                        request=request,
                        parent_task_id=new_task.id,
                        queue=queue_pve_vm_actions,
                        task_dependencies=[job_clone, job_update],
                    )
                    job_ha_add = self._subtask_ha_add(
                        db=db,
                        request=request,
                        parent_task_id=new_task.id,
                        queue=queue_pve_vm_actions,
                        task_dependencies=[job_clone, job_update, job_ipv4_set],
                    )
        else:
            job_ha_add = self._subtask_ha_add(
                db=db,
                request=request,
                parent_task_id=new_task.id,
                queue=queue_pve_vm_actions,
                task_dependencies=[job_clone, job_update],
            )
            job_ipv4_get = self._subtask_ipv4_get(
                db=db,
                request=request,
                parent_task_id=new_task.id,
                queue=queue_pve_vm_actions,
                task_dependencies=[job_clone, job_update, job_ha_add],
            )
        self.db_obj.status = "queued"
        db.add(self.db_obj)
        # Get EventsUser information for creation Guacamoles and ObjectPermissions
        role_teacher = (
            db.query(RoleModel).filter(RoleModel.key == "lehrende").first()
        )
        event_users_teachers = (
            db.query(EventsUser)
            .filter(
                EventsUser.event_id == event.id,
                EventsUser.role_id == role_teacher.id,
            )
            .all()
        )
        # Batch-fetch teacher User IDs
        teacher_user_ids = [eu.user_id for eu in event_users_teachers]
        event_teachers = teacher_user_ids

        # ObjectPermission creation - VirtualMachine
        try:
            # Create ObjectPermission for object owner
            if user.id not in event_teachers:
                CRUDObjectPermission(ObjectPermission).create_reset(
                    db, request, "VirtualMachine", self.db_obj.id, user.id
                )
            else:
                CRUDObjectPermission(ObjectPermission).create_full(
                    db, request, "VirtualMachine", self.db_obj.id, user.id
                )
            # Create ObjectPermission for each teacher in event
            for teacher in event_teachers:
                # Skip self if object owner is teacher
                if user.id == teacher:
                    continue
                CRUDObjectPermission(ObjectPermission).create_full(
                    db, request, "VirtualMachine", self.db_obj.id, teacher
                )
        except Exception as e:
            print(f"UNABLE TO CREATE OBJECT PERMISSION: {e}")

        # Creates a Guacamole object (and relevant ObjectPermissions) for user
        def create_and_enqueue_guacamole(
            interface: GuacamoleConnectionProfile,
            event: Event,
            user: User,
            is_teacher: bool = False,
            student_username: str = None,
            task_dependencies: list = None,
        ):
            if is_teacher:
                new_name = str(
                    f"{event.name}-{user.username}-PROV-{student_username}-{interface.protocol}"
                )
            else:
                new_name = str(
                    f"{event.name}-{user.username}-PROV-{interface.protocol}"
                )
            # Create Guacamole for assigned user
            try:
                new_guac = Guacamole(
                    id=uuid.uuid4(),
                    name=new_name,
                    guacd_hostname="",
                    guacd_port=4822,
                    guacd_encryption=True,
                    connection_profile=interface.id,
                    userId=user.id,
                    eventId=event.id,
                    createdAt=datetime.now(timezone.utc),
                    updatedAt=datetime.now(timezone.utc),
                    createdById=request_user_validation(db, request),
                    updatedById=request_user_validation(db, request),
                )
                db.add(new_guac)
                self.db_obj.guacamoles.append(new_guac)
                db.add(self.db_obj)
                self._commit(db)
                db.refresh(self.db_obj)
                db.refresh(new_guac)
                # Create Task object
                new_task_schema = TaskCreate(
                    name=f"Provision Guacamole connection for {user.username}",
                    event_id=event.id,
                )
                new_task = CRUDTask(TaskModel).create(
                    db=db, request=request, obj_in=new_task_schema
                )
                job_provision = CRUDGuacamole(
                    Guacamole
                )._subtask_guacamole_provision(
                    db=db,
                    request=request,
                    parent_task_id=new_task.id,
                    queue=queue_guacamole,
                    user=user,
                    connection_profile=interface,
                    virtual_machine=self.db_obj,
                    db_obj_id=new_guac.id,
                    task_dependencies=task_dependencies,
                )
                # Add job_provision to worker tasks list
                worker_tasks.append(job_provision)
                # ObjectPermission creation - Guacamole
                try:
                    # Create ObjectPermission for object owner
                    CRUDObjectPermission(ObjectPermission).create_full(
                        db,
                        request,
                        "Guacamole",
                        new_guac.id,
                        self.db_obj.createdById,
                    )
                    # Create ObjectPermission for each teacher in event
                    for teacher in event_teachers:
                        # Skip self if object owner is teacher
                        if user.id == teacher:
                            continue
                        try:
                            CRUDObjectPermission(ObjectPermission).create_full(
                                db, request, "Guacamole", new_guac.id, teacher
                            )
                        except Exception as e:
                            print(f"UNABLE TO CREATE OBJECT PERMISSION: {e}")
                except Exception as e:
                    print(e)
                    ...
            except Exception as e:
                print(e)

        # Create GuacamoleConnectionProfile for each GuacamoleConnectionProfile in source_template
        interfaces = (
            db.query(GuacamoleConnectionProfile)
            .filter(
                GuacamoleConnectionProfile.objectId == source_template.id,
                GuacamoleConnectionProfile.objectType == "Template",
            )
            .all()
        )
        new_interfaces = self._create_interfaces(db, request, interfaces)
        # Batch-fetch teacher User objects for guacamole creation
        teachers_by_id = {}
        if event.guacamole and event_teachers:
            teachers_by_id = {
                u.id: u
                for u in db.query(User)
                .filter(User.id.in_(event_teachers))
                .all()
            }
        for interface in new_interfaces:
            # Create Guacamole objects for each GuacamoleConnectionProfile
            if event.guacamole:
                # Main user creation
                create_and_enqueue_guacamole(
                    interface,
                    event,
                    user,
                    task_dependencies=[
                        job_clone,
                        job_update,
                        job_ha_add,
                        job_ipv4_get,
                    ],
                )

                # Create Guacamole for each user with the "Lehrende" role in the event
                for teacher in event_teachers:
                    # Skip self if object owner is teacher
                    if user.id == teacher:
                        continue
                    teacher_db = teachers_by_id.get(teacher)
                    if not teacher_db:
                        continue
                    create_and_enqueue_guacamole(
                        interface,
                        event,
                        teacher_db,
                        is_teacher=True,
                        student_username=user.username,
                        task_dependencies=[
                            job_clone,
                            job_update,
                            job_ha_add,
                            job_ipv4_get,
                        ],
                    )
        return {"VirtualMachine": self.db_obj, "worker_tasks": worker_tasks}

    # Clone a VM
    def actions_clone(
        self,
        id: Any,
        db: Session,
        request: Request,
        *,
        obj_in: VirtualMachineClone,
    ) -> VirtualMachine:
        # Check if VirtualMachine with id exists
        source_vm = self._get(db, id)
        if not source_vm:
            raise ObjectNotFound(model_name=VirtualMachine.__name__, id=id)
        if not source_vm.proxmoxId:
            raise OperationDependencyMissing(
                message=_("Source VirtualMachine has no proxmoxId")
            )
        if source_vm.status != "stopped":
            raise OperationDependencyMissing(
                message=_(
                    "VirtualMachines may only be cloned in status 'stopped'."
                )
            )
        obj_in_data = jsonable_encoder(obj_in)
        CREATE_GUACAMOLE = True if obj_in.create_guacamole else False
        obj_in_data.pop("create_guacamole")
        self._initialize_object_fields(
            db=db, obj_data_in=obj_in_data, request=request
        )
        self.db_obj.template = source_vm.template
        self.db_obj.os = db.get(Template, source_vm.template).os
        self.db_obj.disk = source_vm.disk
        self.db_obj.name = str(self.db_obj.name)[:100]
        if source_vm.apps:
            self.db_obj.apps = source_vm.apps
        # Check source_vm operating system
        try:
            # PVE connection
            proxmox = ProxmoxCluster().proxmox
            source_vm_conf = (
                proxmox.nodes(
                    ProxmoxCluster().pve_get_node(source_vm.proxmoxId)
                )
                .qemu(source_vm.proxmoxId)
                .config.get()
            )
        except:
            raise ProxmoxConnectionError()
        source_vm_os_type = source_vm_conf["ostype"]
        self.db_obj = self._commit(db, self.db_obj)
        # Create tags for new VM based on source_vm_conf
        source_vm_tags = source_vm_conf.get("tags")
        if source_vm_tags:
            CRUDTag(Tag)._inherit_tags(
                db=db,
                source_object_id=source_vm.id,
                target_object_id=self.db_obj.id,
                source_object_type="VirtualMachine",
                target_object_type="VirtualMachine",
            )
        deploy_jobs = []
        # Create Task object
        new_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(
                name=f"Create VirtualMachine: {self.db_obj.name}"
            ),
        )
        job_clone = self._subtask_vm_clone(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_clone,
            source_vm_id=source_vm.id,
        )
        deploy_jobs.append(job_clone)
        job_update = self._subtask_update(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_actions,
            task_dependencies=[job_clone],
        )
        deploy_jobs.append(job_update)
        # Assign or retrieve IP based on settings.pve_ci_enabled
        if settings.pve_ci_enabled:
            match source_vm_os_type:
                case os_type if os_type in [
                    "wxp",
                    "w2k",
                    "w2k3",
                    "w2k8",
                    "wvista",
                    "win7",
                    "win8",
                    "win10",
                    "win11",
                ]:
                    job_ha_add = self._subtask_ha_add(
                        db=db,
                        request=request,
                        parent_task_id=new_task.id,
                        queue=queue_pve_vm_actions,
                        task_dependencies=[job_clone, job_update],
                    )
                    deploy_jobs.append(job_ha_add)
                    job_ipv4_get = self._subtask_ipv4_get(
                        db=db,
                        request=request,
                        parent_task_id=new_task.id,
                        queue=queue_pve_vm_actions,
                        task_dependencies=[job_clone, job_update, job_ha_add],
                    )
                    deploy_jobs.append(job_ipv4_get)
                case os_type if os_type in ["l24", "l26", "solaris", "other"]:
                    job_ipv4_set = self._subtask_ipv4_set(
                        db=db,
                        request=request,
                        parent_task_id=new_task.id,
                        queue=queue_pve_vm_actions,
                        task_dependencies=[job_clone, job_update],
                    )
                    deploy_jobs.append(job_ipv4_set)
                    job_ha_add = self._subtask_ha_add(
                        db=db,
                        request=request,
                        parent_task_id=new_task.id,
                        queue=queue_pve_vm_actions,
                        task_dependencies=[job_clone, job_update, job_ipv4_set],
                    )
                    deploy_jobs.append(job_ha_add)
        else:
            job_ha_add = self._subtask_ha_add(
                db=db,
                request=request,
                parent_task_id=new_task.id,
                queue=queue_pve_vm_actions,
                task_dependencies=[job_clone, job_update],
            )
            deploy_jobs.append(job_ha_add)
            job_ipv4_get = self._subtask_ipv4_get(
                db=db,
                request=request,
                parent_task_id=new_task.id,
                queue=queue_pve_vm_actions,
                task_dependencies=[job_clone, job_update, job_ha_add],
            )
            deploy_jobs.append(job_ipv4_get)

        self.db_obj.status = "queued"
        CRUDObjectPermission(ObjectPermission).create_full(
            db, request, "VirtualMachine", self.db_obj.id, request.user.id
        )
        interfaces = db.query(GuacamoleConnectionProfile).filter(
            GuacamoleConnectionProfile.objectId == source_vm.id,
            GuacamoleConnectionProfile.objectType == "VirtualMachine",
        )
        new_interfaces = self._create_interfaces(db, request, interfaces)
        if CREATE_GUACAMOLE and new_interfaces:
            user = CRUDBase(User).get(db, request.user.id)
            for interface in new_interfaces:
                job_provision = self._create_and_enqueue_guacamole(
                    db=db,
                    request=request,
                    parent_task_id=new_task.id,
                    queue=queue_guacamole,
                    task_dependencies=deploy_jobs,
                    user=user,
                    interface=interface,
                )
        return self._commit(db, self.db_obj)

    # Update VirtualMachine
    def update(
        self,
        id: Any,
        db: Session,
        request: Request,
        *,
        obj_in: VirtualMachineUpdate,
    ) -> VirtualMachine:
        # Check if object exists before attempting update
        self.db_obj = self.get(db, id)

        # Check if RAM or CPU was changed
        def ram_cpu_changed(db_obj: VirtualMachine) -> bool:
            ram_old = db_obj.ram
            cpu_old = db_obj.cpu
            if obj_in.ram:
                if ram_old != obj_in.ram:
                    return True
            if obj_in.cpu:
                if cpu_old != obj_in.cpu:
                    return True
            return False

        NEEDS_RESTART = ram_cpu_changed(self.db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        # Check if restart_vm is True
        RESTART_VM = False
        if "restart_vm" in update_data:
            if update_data["restart_vm"]:
                RESTART_VM = True
            update_data.pop("restart_vm")
        # If neither CPU nor RAM was changed, set RESTART_VM to false regardless of user input
        if RESTART_VM and not NEEDS_RESTART:
            RESTART_VM = False
        obj_data = jsonable_encoder(self.db_obj)
        for field in obj_data:
            if field in update_data:
                setattr(self.db_obj, field, update_data[field])
        self._update_meta(request)
        # Create Task object
        new_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(
                name=f"Update VirtualMachine: {self.db_obj.name}"
            ),
        )
        job_update = self._subtask_update(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_actions,
        )
        if RESTART_VM:
            job_reboot = self._subtask_actions_reboot(
                db=db,
                request=request,
                parent_task_id=new_task.id,
                queue=queue_pve_vm_actions,
                task_dependencies=[job_update],
            )
            self.db_obj.status = "Rebooting"
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    # Delete object with ID
    def delete(self, db: Session, request: Request, id: Any) -> VirtualMachine:
        self.db_obj = self.get(db, id)
        is_protected = self.db_obj.prevent_delete
        pve_protected = False
        if not is_protected and self.db_obj.proxmoxId:
            try:
                proxmox = ProxmoxCluster()
                pve_config = (
                    proxmox.proxmox.nodes(
                        proxmox.pve_get_node(self.db_obj.proxmoxId)
                    )
                    .qemu(self.db_obj.proxmoxId)
                    .config.get()
                )
                if pve_config.get("protection") == 1:
                    self.db_obj.prevent_delete = True
                    db.add(self.db_obj)
                    db.commit()
                    db.refresh(self.db_obj)
                    is_protected = True
                    pve_protected = True
            except ResourceException:
                pass
        if is_protected:
            raise ProtectedObjectError(
                model_name=VirtualMachine.__name__,
                operation="vm_delete",
                source="Proxmox VE" if pve_protected else None,
            )
        # Create Task object - Delete VirtualMachine
        task_name = f"Delete VirtualMachine (ID={self.db_obj.proxmoxId})"
        if self.db_obj.event:
            task_name += " for Event"
        new_task_vm_schema = TaskCreate(
            name=task_name, event_id=self.db_obj.event
        )
        new_task_vm = CRUDTask(TaskModel).create(
            db=db, request=request, obj_in=new_task_vm_schema
        )
        # Check for any Guacamole objects assigned to VirtualMachine and delete them along with the VirtualMachine
        guacamole_delete_jobs = []
        guac_conn_profs = (
            db.query(GuacamoleConnectionProfile)
            .filter(
                GuacamoleConnectionProfile.objectId == id,
                GuacamoleConnectionProfile.objectType == "VirtualMachine",
            )
            .all()
        )
        gcp_ids = [gcp.id for gcp in guac_conn_profs]
        guacamole_list = (
            (
                db.query(Guacamole)
                .filter(Guacamole.connection_profile.in_(gcp_ids))
                .all()
            )
            if gcp_ids
            else []
        )
        if guacamole_list:
            for guac_obj in guacamole_list:
                job_guac_delete = self._subtask_vm_guac_delete(
                    db=db,
                    request=request,
                    parent_task_id=new_task_vm.id,
                    queue=queue_guacamole,
                    guacamole_id=guac_obj.id,
                )
                guacamole_delete_jobs.append(job_guac_delete)
            job_ha_remove = self._subtask_ha_remove(
                db=db,
                request=request,
                parent_task_id=new_task_vm.id,
                queue=queue_pve_vm_actions,
                task_dependencies=guacamole_delete_jobs,
            )
        else:
            job_ha_remove = self._subtask_ha_remove(
                db=db,
                request=request,
                parent_task_id=new_task_vm.id,
                queue=queue_pve_vm_actions,
            )

        job_stop = self._subtask_actions_stop(
            db=db,
            request=request,
            parent_task_id=new_task_vm.id,
            queue=queue_pve_vm_actions,
            task_dependencies=[job_ha_remove],
        )
        job_delete = self._subtask_vm_delete(
            db=db,
            request=request,
            parent_task_id=new_task_vm.id,
            queue=queue_pve_vm_clone,
            task_dependencies=[job_ha_remove, job_stop],
        )
        self.db_obj.status = "deleting"
        self.db_obj = self._commit(db, self.db_obj)

        # Notify Users with ObjectPermissions for given VirtualMachine
        USERS_WITH_OBJ_PERMS = (
            db.query(User)
            .join(
                ObjectPermission,
                and_(
                    ObjectPermission.entity_type == "User",
                    ObjectPermission.entity_id == User.id,
                ),
            )
            .filter(
                ObjectPermission.object_id == self.db_obj.id,
                ObjectPermission.object_type == "VirtualMachine",
            )
            .distinct()
        )
        for user in USERS_WITH_OBJ_PERMS:
            new_mail = CRUDMail(Mail).create_system_mail(
                db=db,
                user=user,
                context_objects=[self.db_obj],
                mail_action_slug="vm_delete_started",
                event_id=self.db_obj.event,
            )

    # Update VirtualMachine Applications
    def update_apps(
        self,
        id: Any,
        db: Session,
        request: Request,
        *,
        obj_in: VirtualMachineUpdateApps,
    ) -> VirtualMachine:
        self.db_obj = self.get(db, id)
        obj_data = jsonable_encoder(self.db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(self.db_obj, field, update_data[field])

        # Handling of apps
        if "apps" not in update_data:
            raise RequiredParameterMissingError(parameter_name="apps")
        app_keys = [app["key"] for app in update_data["apps"]]
        apps_by_key = {
            a.key: a
            for a in db.query(Application)
            .filter(Application.key.in_(app_keys))
            .all()
        }
        apps_list = []
        for app in update_data["apps"]:
            new_app = apps_by_key.get(app["key"])
            if not new_app:
                raise ObjectNotFound(
                    model_name=Application.__name__, key=app["key"]
                )
            apps_list.append(new_app)
        self.db_obj.apps = apps_list

        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    def actions_migrate(
        self,
        id: Any,
        db: Session,
        request: Request,
        *,
        obj_in: VirtualMachineMigrate,
    ) -> VirtualMachine:
        self.db_obj = self.get(db, id)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        try:
            proxmox_node_info_periodic()
        except:
            raise ProxmoxConnectionError()
        # Check if targetNode is valid
        pve_node_names = []
        for node in get_pve_node_info("PVE resource list")["node_list"]:
            pve_node_names.append(node["node"])
        if update_data["targetNode"] not in pve_node_names:
            raise ProxmoxResourceNotFound(
                resource_type="node",
                field_type="name",
                field_value=update_data["targetNode"],
            )
        # Check if VirtualMachine is already on targetNode
        if self.db_obj.proxmoxNode == update_data["targetNode"]:
            raise BadRequestError(
                message=_(
                    "VirtualMachine is already on node: '{target_node}'"
                ).format(target_node=update_data["targetNode"])
            )
        # Create Task object
        new_task_schema = TaskCreate(
            name=f"Migrate VirtualMachine (ID={self.db_obj.proxmoxId})"
        )
        new_task = CRUDTask(TaskModel).create(
            db=db, request=request, obj_in=new_task_schema
        )
        # Create SubTask objects and enqueue job (MIGRATE)
        sub_task_migrate_schema = SubTaskCreate(
            name="Migrate VirtualMachine",
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            action="vm_migrate",
            attempt=0,
            parent_task=new_task.id,
        )
        sub_task_migrate = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_migrate_schema
        )
        job_migrate = queue_pve_vm_actions.enqueue(
            ProxmoxVirtualMachine(
                sub_task_migrate.id, self.db_obj.id
            ).actions_migrate,
            target_node=update_data["targetNode"],
            retry=Retry(max=settings.worker_max_retry, interval=[10, 30, 60]),
        )
        if not job_migrate:
            raise JobEnqueueError(job_key="vm_migrate")
        old_status = self.db_obj.status
        self.db_obj.status = "migrating"
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        status_changelog = CRUDChangelog(Changelog)._create_for_changes(
            db=db,
            user_id=request.user.id,
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            changes=[
                {
                    "field": "status",
                    "value_old": old_status,
                    "value_new": self.db_obj.status,
                }
            ],
        )
        return self.db_obj

    # Get VirtualMachine HA state
    def actions_ha_get(self, id: Any, db: Session, request: Request) -> dict:
        self.db_obj = self.get(db, id)
        # PVE connection
        try:
            proxmox = ProxmoxCluster().proxmox
        except:
            raise ProxmoxConnectionError()
        # Get VirtualMachine HA State
        try:
            ha_state = proxmox.cluster.ha.resources(self.db_obj.proxmoxId).get()
            return ha_state
        except ResourceException:
            return {
                "type": "vm",
                "state": "ignored",
                "max_relocate": 0,
                "max_restart": 0,
                "digest": None,
            }
        except _:
            raise ProxmoxRequestError()

    # Add VirtualMachine to HA
    def actions_ha_add(
        self,
        id: Any,
        db: Session,
        request: Request,
        *,
        obj_in: VirtualMachineHaAdd,
    ) -> VirtualMachine:
        self.db_obj = self.get(db, id)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        # Create Task object
        new_task_schema = TaskCreate(
            name=f"Add VirtualMachine to HA (ID={self.db_obj.proxmoxId})"
        )
        new_task = CRUDTask(TaskModel).create(
            db=db, request=request, obj_in=new_task_schema
        )
        job_ha_add = self._subtask_ha_add(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_actions,
            ha_state=update_data["ha_state"],
            ha_max_restart=update_data["ha_max_restart"],
            ha_max_relocate=update_data["ha_max_relocate"],
        )
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    # Remove VirtualMachine from HA
    def actions_ha_remove(
        self, db: Session, request: Request, id: Any
    ) -> VirtualMachine:
        self.db_obj = self.get(db, id)
        # Create Task object
        new_task_schema = TaskCreate(
            name=f"Remove VirtualMachine from cluster HA (ID={self.db_obj.proxmoxId})"
        )
        new_task = CRUDTask(TaskModel).create(
            db=db, request=request, obj_in=new_task_schema
        )
        job_ha_remove = self._subtask_ha_remove(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_actions,
        )
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    # Start VirtualMachine
    def actions_start(
        self, db: Session, request: Request, id: Any
    ) -> VirtualMachine:
        # Check if VirtualMachine is already running
        try:
            proxmox_node_info_periodic()
        except:
            raise ProxmoxConnectionError()
        self.db_obj = self.get(db, id)
        if self.db_obj.status == "running":
            raise BadRequestError(message=_(msg_vm_already_running))
        # Create Task object
        new_task_schema = TaskCreate(
            name=f"Start VirtualMachine (ID={self.db_obj.proxmoxId})"
        )
        new_task = CRUDTask(TaskModel).create(
            db=db, request=request, obj_in=new_task_schema
        )
        job_start = self._subtask_actions_start(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_actions,
        )
        old_status = self.db_obj.status
        self.db_obj.status = "starting"
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        status_changelog = CRUDChangelog(Changelog)._create_for_changes(
            db=db,
            user_id=request.user.id,
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            changes=[
                {
                    "field": "status",
                    "value_old": old_status,
                    "value_new": self.db_obj.status,
                }
            ],
        )
        return self.db_obj

    # Stop VirtualMachine
    def actions_stop(
        self, db: Session, request: Request, id: Any
    ) -> VirtualMachine:
        # Check if VirtualMachine is already stopped
        try:
            proxmox_node_info_periodic()
        except:
            raise ProxmoxConnectionError()
        self.db_obj = self.get(db, id)
        if self.db_obj.status == "stopped":
            raise BadRequestError(message=_(msg_vm_already_stopped))
        # Create Task object
        new_task_schema = TaskCreate(
            name=f"Stop VirtualMachine (ID={self.db_obj.proxmoxId})"
        )
        new_task = CRUDTask(TaskModel).create(
            db=db, request=request, obj_in=new_task_schema
        )
        # Create SubTask objects and enqueue job (STOP)
        job_stop = self._subtask_actions_stop(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_actions,
        )
        old_status = self.db_obj.status
        self.db_obj.status = "stopping"
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        status_changelog = CRUDChangelog(Changelog)._create_for_changes(
            db=db,
            user_id=request.user.id,
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            changes=[
                {
                    "field": "status",
                    "value_old": old_status,
                    "value_new": self.db_obj.status,
                }
            ],
        )
        return self.db_obj

    # Pause VirtualMachine
    def actions_pause(
        self, db: Session, request: Request, id: Any
    ) -> VirtualMachine:
        # Check if VirtualMachine is already running
        try:
            proxmox_node_info_periodic()
        except:
            raise ProxmoxConnectionError()
        self.db_obj = self.get(db, id)
        if self.db_obj.status == "paused":
            raise BadRequestError(
                message=_("VirtualMachine is already paused.")
            )
        # Create Task object
        new_task_schema = TaskCreate(
            name=f"Pause VirtualMachine (ID={self.db_obj.proxmoxId})"
        )
        new_task = CRUDTask(TaskModel).create(
            db=db, request=request, obj_in=new_task_schema
        )
        # Create SubTask objects and enqueue job (PAUSE)
        job_pause = self._subtask_actions_pause(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_actions,
        )
        old_status = self.db_obj.status
        self.db_obj.status = "pausing"
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        status_changelog = CRUDChangelog(Changelog)._create_for_changes(
            db=db,
            user_id=request.user.id,
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            changes=[
                {
                    "field": "status",
                    "value_old": old_status,
                    "value_new": self.db_obj.status,
                }
            ],
        )
        return self.db_obj

    # Reset VirtualMachine
    def actions_reset(
        self, db: Session, request: Request, id: Any
    ) -> VirtualMachine:
        self.db_obj = self.get(db, id)
        if self.db_obj.status not in ["running"]:
            raise BadRequestError(
                message=_(
                    "Only VirtualMachines in status 'running' my be reset."
                )
            )
        # Create Task object
        new_task_schema = TaskCreate(
            name=f"Reset VirtualMachine (ID={self.db_obj.proxmoxId})"
        )
        new_task = CRUDTask(TaskModel).create(
            db=db, request=request, obj_in=new_task_schema
        )
        job_reset = self._subtask_actions_reset(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_actions,
        )
        old_status = self.db_obj.status
        self.db_obj.status = "resetting"
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        status_changelog = CRUDChangelog(Changelog)._create_for_changes(
            db=db,
            user_id=request.user.id,
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            changes=[
                {
                    "field": "status",
                    "value_old": old_status,
                    "value_new": self.db_obj.status,
                }
            ],
        )
        return self.db_obj

    # Reboot VirtualMachine
    def actions_reboot(
        self, db: Session, request: Request, id: Any
    ) -> VirtualMachine:
        self.db_obj = self.get(db, id)
        if self.db_obj.status not in ["running"]:
            raise BadRequestError(
                message=_(
                    "Only VirtualMachines in status 'running' my be rebooted."
                )
            )
        # Create Task object
        new_task_schema = TaskCreate(
            name=f"Reboot VirtualMachine (ID={self.db_obj.proxmoxId})"
        )
        new_task = CRUDTask(TaskModel).create(
            db=db, request=request, obj_in=new_task_schema
        )
        job_reboot = self._subtask_actions_reboot(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_actions,
        )
        old_status = self.db_obj.status
        self.db_obj.status = "rebooting"
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        status_changelog = CRUDChangelog(Changelog)._create_for_changes(
            db=db,
            user_id=request.user.id,
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            changes=[
                {
                    "field": "status",
                    "value_old": old_status,
                    "value_new": self.db_obj.status,
                }
            ],
        )
        return self.db_obj

    # Shut down VirtualMachine
    def actions_shutdown(
        self, db: Session, request: Request, id: Any
    ) -> VirtualMachine:
        # Check if VirtualMachine is already stopped
        try:
            proxmox_node_info_periodic()
        except:
            raise ProxmoxConnectionError()
        self.db_obj = self.get(db, id)
        if self.db_obj.status == "stopped":
            raise BadRequestError(message=_(msg_vm_already_stopped))
        # Create Task object
        new_task_schema = TaskCreate(
            name=f"Shut down VirtualMachine (ID={self.db_obj.proxmoxId})"
        )
        new_task = CRUDTask(TaskModel).create(
            db=db, request=request, obj_in=new_task_schema
        )
        job_shutdown = self._subtask_actions_shutdown(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_actions,
        )
        old_status = self.db_obj.status
        self.db_obj.status = "shutting down"
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        status_changelog = CRUDChangelog(Changelog)._create_for_changes(
            db=db,
            user_id=request.user.id,
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            changes=[
                {
                    "field": "status",
                    "value_old": old_status,
                    "value_new": self.db_obj.status,
                }
            ],
        )
        return self.db_obj

    # Resume VirtualMachine
    def actions_resume(
        self, db: Session, request: Request, id: Any
    ) -> VirtualMachine:
        # Check if VirtualMachine is already running
        try:
            proxmox_node_info_periodic()
        except:
            raise ProxmoxConnectionError()
        self.db_obj = self.get(db, id)
        if self.db_obj.status == "running":
            raise BadRequestError(message=_(msg_vm_already_running))
        # Create Task object
        new_task_schema = TaskCreate(
            name=f"Resume VirtualMachine (ID={self.db_obj.proxmoxId})"
        )
        new_task = CRUDTask(TaskModel).create(
            db=db, request=request, obj_in=new_task_schema
        )
        job_resume = self._subtask_actions_resume(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_actions,
        )
        old_status = self.db_obj.status
        self.db_obj.status = "Resuming"
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        status_changelog = CRUDChangelog(Changelog)._create_for_changes(
            db=db,
            user_id=request.user.id,
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            changes=[
                {
                    "field": "status",
                    "value_old": old_status,
                    "value_new": self.db_obj.status,
                }
            ],
        )
        return self.db_obj

    # Hibernate VirtualMachine
    def actions_hibernate(
        self, db: Session, request: Request, id: Any
    ) -> VirtualMachine:
        # Check if VirtualMachine is already running
        try:
            proxmox_node_info_periodic()
        except:
            raise ProxmoxConnectionError()
        self.db_obj = self.get(db, id)

        # Check if VirtualMachine is locked
        def is_vm_locked(db_vm) -> bool:
            try:
                vm_current_status = (
                    ProxmoxCluster()
                    .proxmox.nodes(
                        ProxmoxCluster().pve_get_node(db_vm.proxmoxId)
                    )
                    .qemu(db_vm.proxmoxId)
                    .status.current.get()
                )
            except:
                raise ProxmoxRequestError()
            if "lock" not in vm_current_status:
                return False
            vm_status = vm_current_status["status"]
            vm_lock = vm_current_status["lock"]
            return vm_status == "stopped" and vm_lock == "suspended"

        if is_vm_locked(self.db_obj):
            raise BadRequestError(
                message=_("VirtualMachine is already hibernated.")
            )
        # Create Task object
        new_task_schema = TaskCreate(
            name=f"Hibernate VirtualMachine (ID={self.db_obj.proxmoxId})"
        )
        new_task = CRUDTask(TaskModel).create(
            db=db, request=request, obj_in=new_task_schema
        )
        job_hibernate = self._subtask_actions_hibernate(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_actions,
        )
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    def bulk_start(
        self,
        db: Session,
        request: Request,
        obj_in: VirtualMachineIdList,
        event_id: Any = None,
    ):
        self._ensure_pve()
        self.vm_list = self._validate_vm_ids_exist(
            db, obj_in.vms, skip_status=["running"]
        )
        parent_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(
                name=f"Start {len(self.vm_list)} VirtualMachines",
                event_id=event_id,
            ),
        )
        enqueued, skipped = 0, []
        for vm in self.vm_list:
            if vm.status in ["running"]:
                skipped.append(str(vm.id))
                continue
            self.db_obj = vm
            job = self._subtask_actions_start(
                db=db,
                request=request,
                parent_task_id=parent_task.id,
                queue=queue_pve_vm_actions,
            )
            old_status = self.db_obj.status
            self.db_obj.status = "starting"
            self._update_meta(request)
            self.db_obj = self._commit(db, self.db_obj)
            status_changelog = CRUDChangelog(Changelog)._create_for_changes(
                db=db,
                user_id=request.user.id,
                object_type="VirtualMachine",
                object_id=self.db_obj.id,
                changes=[
                    {
                        "field": "status",
                        "value_old": old_status,
                        "value_new": self.db_obj.status,
                    }
                ],
            )
            if not job:
                raise JobEnqueueError(job_key="vm_start")
            enqueued += 1
        if enqueued == 0:
            self._delete_empty_parents(db=db, parent_task_id=parent_task.id)
            raise BulkActionRequirementMissing(
                message="All VirtualMachines already in status 'running'"
            )
        return {
            "task_id": parent_task.id,
            "enqueued": enqueued,
            "skipped": skipped,
        }

    def bulk_stop(
        self,
        db: Session,
        request: Request,
        obj_in: VirtualMachineIdList,
        event_id: Any = None,
    ):
        self._ensure_pve()
        self.vm_list = self._validate_vm_ids_exist(
            db, obj_in.vms, skip_status=["stopped"]
        )
        parent_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(
                name=f"Stop {len(self.vm_list)} VirtualMachines",
                event_id=event_id,
            ),
        )
        enqueued, skipped = 0, []
        for vm in self.vm_list:
            if vm.status in ["stopped", "stopping"]:
                skipped.append(str(vm.id))
                continue
            self.db_obj = vm
            job = self._subtask_actions_stop(
                db=db,
                request=request,
                parent_task_id=parent_task.id,
                queue=queue_pve_vm_actions,
            )
            old_status = self.db_obj.status
            self.db_obj.status = "stopping"
            self._update_meta(request)
            self.db_obj = self._commit(db, self.db_obj)
            status_changelog = CRUDChangelog(Changelog)._create_for_changes(
                db=db,
                user_id=request.user.id,
                object_type="VirtualMachine",
                object_id=self.db_obj.id,
                changes=[
                    {
                        "field": "status",
                        "value_old": old_status,
                        "value_new": self.db_obj.status,
                    }
                ],
            )
            if not job:
                raise JobEnqueueError(job_key="vm_stop")
            enqueued += 1
        if enqueued == 0:
            self._delete_empty_parents(db=db, parent_task_id=parent_task.id)
            raise BulkActionRequirementMissing(
                message="All VirtualMachines already in status 'stopped'"
            )
        return {
            "task_id": parent_task.id,
            "enqueued": enqueued,
            "skipped": skipped,
        }

    def bulk_pause(
        self,
        db: Session,
        request: Request,
        obj_in: VirtualMachineIdList,
        event_id: Any = None,
    ):
        self._ensure_pve()
        self.vm_list = self._validate_vm_ids_exist(
            db, obj_in.vms, skip_status=["paused"]
        )
        parent_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(
                name=f"Pause {len(self.vm_list)} VirtualMachines",
                event_id=event_id,
            ),
        )
        enqueued, skipped = 0, []
        for vm in self.vm_list:
            if vm.status in ["paused", "pausing"]:
                skipped.append(str(vm.id))
                continue
            self.db_obj = vm
            job = self._subtask_actions_pause(
                db=db,
                request=request,
                parent_task_id=parent_task.id,
                queue=queue_pve_vm_actions,
            )
            old_status = self.db_obj.status
            self.db_obj.status = "pausing"
            self._update_meta(request)
            self.db_obj = self._commit(db, self.db_obj)
            status_changelog = CRUDChangelog(Changelog)._create_for_changes(
                db=db,
                user_id=request.user.id,
                object_type="VirtualMachine",
                object_id=self.db_obj.id,
                changes=[
                    {
                        "field": "status",
                        "value_old": old_status,
                        "value_new": self.db_obj.status,
                    }
                ],
            )
            if not job:
                raise JobEnqueueError(job_key="vm_pause")
            enqueued += 1
        if enqueued == 0:
            self._delete_empty_parents(db=db, parent_task_id=parent_task.id)
            raise BulkActionRequirementMissing(
                message="All VirtualMachines already in status 'paused'"
            )
        return {
            "task_id": parent_task.id,
            "enqueued": enqueued,
            "skipped": skipped,
        }

    def bulk_reset(
        self,
        db: Session,
        request: Request,
        obj_in: VirtualMachineIdList,
        event_id: Any = None,
    ):
        self._ensure_pve()
        self.vm_list = self._validate_vm_ids_exist(
            db, obj_in.vms, allowed_status=["running"]
        )
        parent_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(
                name=f"Reset {len(self.vm_list)} VirtualMachines",
                event_id=event_id,
            ),
        )
        enqueued, skipped = 0, []
        for vm in self.vm_list:
            if vm.status not in ["running"]:
                skipped.append(str(vm.id))
                continue
            self.db_obj = vm
            job = self._subtask_actions_reset(
                db=db,
                request=request,
                parent_task_id=parent_task.id,
                queue=queue_pve_vm_actions,
            )
            old_status = self.db_obj.status
            self.db_obj.status = "resetting"
            self._update_meta(request)
            self.db_obj = self._commit(db, self.db_obj)
            status_changelog = CRUDChangelog(Changelog)._create_for_changes(
                db=db,
                user_id=request.user.id,
                object_type="VirtualMachine",
                object_id=self.db_obj.id,
                changes=[
                    {
                        "field": "status",
                        "value_old": old_status,
                        "value_new": self.db_obj.status,
                    }
                ],
            )
            if not job:
                raise JobEnqueueError(job_key="vm_reset")
            enqueued += 1
        if enqueued == 0:
            self._delete_empty_parents(db=db, parent_task_id=parent_task.id)
            raise BulkActionRequirementMissing(
                message="All VirtualMachines need to be in status 'running' before being reset"
            )
        return {
            "task_id": parent_task.id,
            "enqueued": enqueued,
            "skipped": skipped,
        }

    def bulk_reboot(
        self,
        db: Session,
        request: Request,
        obj_in: VirtualMachineIdList,
        event_id: Any = None,
    ):
        self._ensure_pve()
        self.vm_list = self._validate_vm_ids_exist(
            db, obj_in.vms, allowed_status=["running"]
        )
        parent_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(
                name=f"Reboot {len(self.vm_list)} VirtualMachines",
                event_id=event_id,
            ),
        )
        enqueued, skipped = 0, []
        for vm in self.vm_list:
            if vm.status not in ["running"]:
                skipped.append(str(vm.id))
                continue
            self.db_obj = vm
            job = self._subtask_actions_reboot(
                db=db,
                request=request,
                parent_task_id=parent_task.id,
                queue=queue_pve_vm_actions,
            )
            old_status = self.db_obj.status
            self.db_obj.status = "rebooting"
            self._update_meta(request)
            self.db_obj = self._commit(db, self.db_obj)
            status_changelog = CRUDChangelog(Changelog)._create_for_changes(
                db=db,
                user_id=request.user.id,
                object_type="VirtualMachine",
                object_id=self.db_obj.id,
                changes=[
                    {
                        "field": "status",
                        "value_old": old_status,
                        "value_new": self.db_obj.status,
                    }
                ],
            )
            if not job:
                raise JobEnqueueError(job_key="vm_reboot")
            enqueued += 1
        if enqueued == 0:
            self._delete_empty_parents(db=db, parent_task_id=parent_task.id)
            raise BulkActionRequirementMissing(
                message="All VirtualMachines need to be in status 'running' before being rebooted"
            )
        return {
            "task_id": parent_task.id,
            "enqueued": enqueued,
            "skipped": skipped,
        }

    def bulk_shutdown(
        self,
        db: Session,
        request: Request,
        obj_in: VirtualMachineIdList,
        event_id: Any = None,
    ):
        self._ensure_pve()
        self.vm_list = self._validate_vm_ids_exist(
            db, obj_in.vms, allowed_status=["running"]
        )
        parent_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(
                name=f"Shutdown {len(self.vm_list)} VirtualMachines",
                event_id=event_id,
            ),
        )
        enqueued, skipped = 0, []
        for vm in self.vm_list:
            if not vm or vm.status not in ["running"]:
                skipped.append(str(vm.id))
                continue
            self.db_obj = vm
            job = self._subtask_actions_shutdown(
                db=db,
                request=request,
                parent_task_id=parent_task.id,
                queue=queue_pve_vm_actions,
            )
            old_status = self.db_obj.status
            self.db_obj.status = "shutting down"
            self._update_meta(request)
            self.db_obj = self._commit(db, self.db_obj)
            status_changelog = CRUDChangelog(Changelog)._create_for_changes(
                db=db,
                user_id=request.user.id,
                object_type="VirtualMachine",
                object_id=self.db_obj.id,
                changes=[
                    {
                        "field": "status",
                        "value_old": old_status,
                        "value_new": self.db_obj.status,
                    }
                ],
            )
            if not job:
                raise JobEnqueueError(job_key="vm_shutdown")
            enqueued += 1
        if enqueued == 0:
            self._delete_empty_parents(db=db, parent_task_id=parent_task.id)
            raise BulkActionRequirementMissing(
                message="All VirtualMachines need to be in status 'running' before shutting down"
            )
        return {
            "task_id": parent_task.id,
            "enqueued": enqueued,
            "skipped": skipped,
        }

    def bulk_resume(
        self,
        db: Session,
        request: Request,
        obj_in: VirtualMachineIdList,
        event_id: Any = None,
    ):
        self._ensure_pve()
        self.vm_list = self._validate_vm_ids_exist(
            db, obj_in.vms, skip_status=["running"]
        )
        parent_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(
                name=f"Resume {len(self.vm_list)} VirtualMachines",
                event_id=event_id,
            ),
        )
        enqueued, skipped = 0, []
        for vm in self.vm_list:
            if not vm or vm.status in ["running", "resuming"]:
                skipped.append(str(vm.id))
                continue
            self.db_obj = vm
            job = self._subtask_actions_resume(
                db=db,
                request=request,
                parent_task_id=parent_task.id,
                queue=queue_pve_vm_actions,
            )
            old_status = self.db_obj.status
            self.db_obj.status = "resuming"
            self._update_meta(request)
            self.db_obj = self._commit(db, self.db_obj)
            status_changelog = CRUDChangelog(Changelog)._create_for_changes(
                db=db,
                user_id=request.user.id,
                object_type="VirtualMachine",
                object_id=self.db_obj.id,
                changes=[
                    {
                        "field": "status",
                        "value_old": old_status,
                        "value_new": self.db_obj.status,
                    }
                ],
            )
            if not job:
                raise JobEnqueueError(job_key="vm_resume")
            enqueued += 1
        if enqueued == 0:
            self._delete_empty_parents(db=db, parent_task_id=parent_task.id)
            raise BulkActionRequirementMissing(
                message="All VirtualMachines are already in status 'running'"
            )
        return {
            "task_id": parent_task.id,
            "enqueued": enqueued,
            "skipped": skipped,
        }

    def bulk_hibernate(
        self,
        db: Session,
        request: Request,
        obj_in: VirtualMachineIdList,
        event_id: Any = None,
    ):
        self._ensure_pve()
        self.vm_list = self._validate_vm_ids_exist(db, obj_in.vms)
        parent_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(
                name=f"Hibernate {len(self.vm_list)} VirtualMachines",
                event_id=event_id,
            ),
        )
        enqueued, skipped = 0, []
        for vm in self.vm_list:
            try:
                vm_current_status = (
                    ProxmoxCluster()
                    .proxmox.nodes(ProxmoxCluster().pve_get_node(vm.proxmoxId))
                    .qemu(vm.proxmoxId)
                    .status.current.get()
                )
            except:
                raise ProxmoxRequestError()
            if "lock" not in vm_current_status:
                return False
            vm_status = vm_current_status["status"]
            vm_lock = vm_current_status["lock"]
            if vm_status == "stopped" and vm_lock == "suspended":
                skipped.append(str(vm.id))
                continue
            self.db_obj = vm
            job = self._subtask_actions_hibernate(
                db=db,
                request=request,
                parent_task_id=parent_task.id,
                queue=queue_pve_vm_actions,
            )
            self._update_meta(request)
            self.db_obj = self._commit(db, self.db_obj)
            if not job:
                raise JobEnqueueError(job_key="vm_hibernate")
            enqueued += 1
        if enqueued == 0:
            self._delete_empty_parents(db=db, parent_task_id=parent_task.id)
            raise BulkActionRequirementMissing(
                message="All VirtualMachines are suspended"
            )
        return {
            "task_id": parent_task.id,
            "enqueued": enqueued,
            "skipped": skipped,
        }

    def bulk_ha_add(
        self,
        db: Session,
        request: Request,
        obj_in: VirtualMachineBulkHaAdd,
        event_id: Any = None,
    ):
        self._ensure_pve()
        self.vm_list = self._validate_vm_ids_exist(db, obj_in.vms)
        parent_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(
                name=f"Add {len(self.vm_list)} VirtualMachines to HA",
                event_id=event_id,
            ),
        )
        enqueued, skipped = 0, []
        for vm in self.vm_list:
            self.db_obj = vm
            job = self._subtask_ha_add(
                db=db,
                request=request,
                parent_task_id=parent_task.id,
                queue=queue_pve_vm_actions,
                ha_state=obj_in.ha_state,
                ha_max_restart=obj_in.ha_max_restart,
                ha_max_relocate=obj_in.ha_max_relocate,
            )
            self._update_meta(request)
            self.db_obj = self._commit(db, self.db_obj)
            if not job:
                raise JobEnqueueError(job_key="vm_ha_add")
            enqueued += 1
        return {"task_id": parent_task.id, "enqueued": enqueued}

    def bulk_ha_remove(
        self,
        db: Session,
        request: Request,
        obj_in: VirtualMachineIdList,
        event_id: Any = None,
    ):
        self._ensure_pve()
        self.vm_list = self._validate_vm_ids_exist(db, obj_in.vms)
        parent_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(
                name=f"Remove {len(self.vm_list)} VirtualMachines from HA",
                event_id=event_id,
            ),
        )
        enqueued, skipped = 0, []
        for vm in self.vm_list:
            self.db_obj = vm
            job = self._subtask_ha_remove(
                db=db,
                request=request,
                parent_task_id=parent_task.id,
                queue=queue_pve_vm_actions,
            )
            self._update_meta(request)
            self.db_obj = self._commit(db, self.db_obj)
            if not job:
                raise JobEnqueueError(job_key="vm_ha_remove")
            enqueued += 1
        return {"task_id": parent_task.id, "enqueued": enqueued}

    def bulk_migrate(
        self,
        db: Session,
        request: Request,
        obj_in: VirtualMachineIdList,
        target_node: str,
        event_id: Any = None,
    ):
        self._ensure_pve()
        pve_node_names = [
            n["node"]
            for n in get_pve_node_info("PVE resource list")["node_list"]
        ]
        if target_node not in pve_node_names:
            raise ProxmoxResourceNotFound(
                resource_type="node", field_type="name", field_value=target_node
            )
        self.vm_list = self._validate_vm_ids_exist(db, obj_in.vms)
        parent_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(
                name=f"Migrate {len(self.vm_list)} VirtualMachines to {target_node}",
                event_id=event_id,
            ),
        )
        enqueued, skipped = 0, []

        for vm in self.vm_list:
            if (
                not vm
                or vm.proxmoxNode == target_node
                or vm.status == "migrating"
            ):
                skipped.append(str(vm.id))
                continue
            self.db_obj = vm
            sub = CRUDSubTask(SubTaskModel).create(
                db=db,
                request=request,
                obj_in=SubTaskCreate(
                    name="Migrate VirtualMachine",
                    object_type="VirtualMachine",
                    object_id=vm.id,
                    action="vm_migrate",
                    attempt=0,
                    parent_task=parent_task.id,
                ),
            )
            job = queue_pve_vm_actions.enqueue(
                ProxmoxVirtualMachine(sub.id, vm.id).actions_migrate,
                target_node=target_node,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
            if not job:
                raise JobEnqueueError(job_key="vm_migrate")
            old_status = self.db_obj.status
            self.db_obj.status = "migrating"
            self._update_meta(request)
            self.db_obj = self._commit(db, self.db_obj)
            status_changelog = CRUDChangelog(Changelog)._create_for_changes(
                db=db,
                user_id=request.user.id,
                object_type="VirtualMachine",
                object_id=self.db_obj.id,
                changes=[
                    {
                        "field": "status",
                        "value_old": old_status,
                        "value_new": self.db_obj.status,
                    }
                ],
            )
            enqueued += 1
        if enqueued == 0:
            self._delete_empty_parents(db=db, parent_task_id=parent_task.id)
            raise BulkActionRequirementMissing(
                message="All VirtualMachines are already on target node"
            )

        return {
            "task_id": parent_task.id,
            "enqueued": enqueued,
            "skipped": skipped,
        }

    # Get ipv4 of VirtualMachine from PVE
    def get_ipv4(self, id: Any, db: Session):
        # PVE connection
        try:
            proxmox = ProxmoxCluster().proxmox
        except:
            raise ProxmoxConnectionError()
        self.db_obj = self.get(db, id)
        # Get VirtualMachine Network Interfaces
        try:
            vm_interfaces = proxmox(
                f"/nodes/{ProxmoxCluster().pve_get_node(self.db_obj.proxmoxId)}/qemu/{self.db_obj.proxmoxId}/agent/network-get-interfaces"
            ).get()["result"]
        except ResourceException:
            raise BadRequestError(
                message=_(
                    "Unable to retrieve ipv4 from PVE as VirtualMachine is not running"
                )
            )
        except:
            raise ProxmoxRequestError()

        # Check if an IP from one of the Network Adapters is in the VirtualMachine subnet
        VIRTUAL_MACHINE_ON_SUBNET = vm_ip_in_subnet(vm_interfaces)
        if not VIRTUAL_MACHINE_ON_SUBNET:
            if self.db_obj.ipv4 != "0.0.0.0":
                self.db_obj.ipv4 = "0.0.0.0"
                self.db_obj = self._commit(db, self.db_obj)
            return _(
                "VirtualMachine is not in PVE VirtualMachine Subnet {subnet}"
            ).format(subnet=settings.pve_vm_subnet)
        elif self.db_obj.ipv4 != VIRTUAL_MACHINE_ON_SUBNET:
            self.db_obj.ipv4 = VIRTUAL_MACHINE_ON_SUBNET
            self.db_obj = self._commit(db, self.db_obj)

        # Update all related Guacamole objects with new hostname(ipv4)
        if self.db_obj.guacamoles:
            for guac in self.db_obj.guacamoles:
                guac_obj = CRUDGuacamole(Guacamole).update_hostname(
                    db=db, id=guac.id, hostname=self.db_obj.ipv4
                )
        return self.db_obj.ipv4

    # Get rrddata
    def get_rrddata(
        self,
        db: Session,
        *,
        id: Any,
        timeframe: ProxmoxRRDTimeframe = ProxmoxRRDTimeframe.HOUR,
        cf: ProxmoxRRDConsolidation = ProxmoxRRDConsolidation.AVERAGE,
    ):
        if isinstance(id, str):
            try:
                id = uuid.UUID(id)
            except:
                raise InvalidFieldValue(field="id", value=id)
        self.db_obj = db.get(self.model, id)
        if not self.db_obj:
            raise ObjectNotFound(id=id, model_name=self.model.__name__)

        try:
            proxmox = ProxmoxCluster().proxmox
        except Exception:
            raise ProxmoxConnectionError()

        try:
            node_rrddata = (
                proxmox.nodes(self.db_obj.proxmoxNode)
                .qemu(self.db_obj.proxmoxId)
                .rrddata.get(cf=cf.value, timeframe=timeframe.value)
            )
        except ResourceException:
            raise BadRequestError(
                message=_(
                    "Either the consolidation function or timeframe entered is invalid."
                )
            )

        return node_rrddata

    def _validate_vm_ids_exist(
        self,
        db: Session,
        vm_ids: list[Any],
        skip_status: list = None,
        allowed_status: list = None,
    ) -> list:
        found_vms = (
            db.query(VirtualMachine).filter(VirtualMachine.id.in_(vm_ids)).all()
        )
        found_ids = {str(vm.id) for vm in found_vms}
        missing = [str(x) for x in vm_ids if str(x) not in found_ids]
        if missing:
            raise BulkObjectNotFound(model_name="VirtualMachine", ids=missing)
        if skip_status:
            skip_status_count = sum(
                1 for vm in found_vms if vm.status not in skip_status
            )
            if skip_status_count == 0:
                raise BulkActionRequirementMissing(
                    message="All VirtualMachines are in an invalid state for this action"
                )
        elif allowed_status:
            allowed_status_count = sum(
                1 for vm in found_vms if vm.status in allowed_status
            )
            if allowed_status_count == 0:
                raise BulkActionRequirementMissing(
                    message="All VirtualMachines are in an invalid state for this action"
                )
        self.vm_ids = found_ids
        self.vm_list = found_vms
        return self.vm_list

    # Internal functions
    def _update_subtask_job_id(
        self, db: Session, sub_task_id: Any, job_id: Any
    ):
        sub_task = CRUDBase(SubTaskModel).get(db, sub_task_id)
        sub_task.job_id = job_id
        db.add(sub_task)
        self._commit(db)

    def _create_interfaces(self, db: Session, request: Request, interfaces):
        new_interfaces = []
        for interface in interfaces:
            try:
                # Create GuacamoleConnectionProfiles
                new_conn_profile = GuacamoleConnectionProfileCreate(
                    objectId=self.db_obj.id,
                    objectType=self.model.__name__,
                    port=interface.port,
                    protocol=interface.protocol,
                    username=interface.username,
                    password=interface.password,
                )
                db_connection_profile = CRUDGuacamoleConnectionProfile(
                    GuacamoleConnectionProfile
                ).create(db=db, request=request, obj_in=new_conn_profile)
                new_interfaces.append(db_connection_profile)
            except:
                continue  # TODO
        return new_interfaces

    def _subtask_update(
        self,
        db: Session,
        request: Request,
        parent_task_id: Any,
        queue: Queue,
        task_dependencies: list = None,
    ):
        # Create SubTask objects and enqueue job (UPDATE)
        sub_task_update_schema = SubTaskCreate(
            name="Update VirtualMachine with new resource data",
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            action="vm_update",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_update = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_update_schema
        )
        if not task_dependencies:
            job_update = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_update.id, self.db_obj.id
                ).update,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_update = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_update.id, self.db_obj.id
                ).update,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_update:
            raise JobEnqueueError(job_key="vm_update")
        self._update_subtask_job_id(db, sub_task_update.id, job_update.id)
        return job_update

    def _subtask_tags_update(
        self,
        db: Session,
        request: Request,
        parent_task_id: Any,
        queue: Queue,
        task_dependencies: list = None,
        tag_to_remove: str = None,
    ):
        # Create SubTask objects and enqueue job (UPDATE)
        sub_task_update_schema = SubTaskCreate(
            name="Update VirtualMachine tags",
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            action="vm_tags_update",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_update = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_update_schema
        )
        if not task_dependencies:
            job_tags_update = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_update.id, self.db_obj.id
                ).update_tags,
                tag_to_remove=tag_to_remove,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_tags_update = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_update.id, self.db_obj.id
                ).update_tags,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_tags_update:
            raise JobEnqueueError(job_key="vm_tags_update")
        self._update_subtask_job_id(db, sub_task_update.id, job_tags_update.id)
        return job_tags_update

    def _subtask_template_clone(
        self,
        db: Session,
        request: Request,
        parent_task_id: Any,
        queue: Queue,
        task_dependencies: list = None,
    ):
        # Create SubTask objects and enqueue job (UPDATE)
        sub_task_clone_schema = SubTaskCreate(
            name="Clone Template into VirtualMachine",
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            action="template_clone",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_clone = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_clone_schema
        )
        if not task_dependencies:
            job_clone = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_clone.id, self.db_obj.id
                ).create_from_template,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_clone = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_clone.id, self.db_obj.id
                ).create_from_template,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_clone:
            raise JobEnqueueError(job_key="template_clone")
        self._update_subtask_job_id(db, sub_task_clone.id, job_clone.id)
        return job_clone

    def _subtask_vm_clone(
        self,
        db: Session,
        request: Request,
        parent_task_id: Any,
        queue: Queue,
        source_vm_id: Any,
        task_dependencies: list = None,
    ):
        # Create SubTask objects and enqueue job (UPDATE)
        sub_task_clone_schema = SubTaskCreate(
            name="Clone VirtualMachine",
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            action="vm_clone",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_clone = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_clone_schema
        )
        if not task_dependencies:
            job_clone = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_clone.id, self.db_obj.id
                ).create_from_vm,
                source_vm_id=source_vm_id,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_clone = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_clone.id, self.db_obj.id
                ).create_from_vm,
                source_vm_id=source_vm_id,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_clone:
            raise JobEnqueueError(job_key="vm_clone")
        self._update_subtask_job_id(db, sub_task_clone.id, job_clone.id)
        return job_clone

    def _subtask_vm_delete(
        self,
        db: Session,
        parent_task_id: Any,
        queue: Queue,
        request: Request = None,
        task_dependencies: list = None,
    ):
        # Create SubTask objects and enqueue job (DELETE)
        sub_task_delete_schema = SubTaskCreate(
            name="Delete VirtualMachine",
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            action="vm_delete",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_delete = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_delete_schema
        )
        if not task_dependencies:
            job_delete = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_delete.id, self.db_obj.id
                ).delete,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_delete = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_delete.id, self.db_obj.id
                ).delete,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_delete:
            raise JobEnqueueError(job_key="vm_delete")
        self._update_subtask_job_id(db, sub_task_delete.id, job_delete.id)
        return job_delete

    def _subtask_ha_add(
        self,
        db: Session,
        request: Request,
        parent_task_id: Any,
        queue: Queue,
        task_dependencies: list = None,
        **kwargs,
    ):
        # Create SubTask objects and enqueue job (HA_ADD)
        sub_task_ha_add_schema = SubTaskCreate(
            name="Add VirtualMachine to cluster HA",
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            action="vm_ha_add",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_ha_add = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_ha_add_schema
        )
        if not task_dependencies:
            job_ha_add = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_ha_add.id, self.db_obj.id
                ).ha_set,
                **kwargs,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_ha_add = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_ha_add.id, self.db_obj.id
                ).ha_set,
                depends_on=task_dependencies,
                **kwargs,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_ha_add:
            raise JobEnqueueError(job_key="vm_ha_add")
        self._update_subtask_job_id(db, sub_task_ha_add.id, job_ha_add.id)
        return job_ha_add

    def _subtask_ha_remove(
        self,
        db: Session,
        parent_task_id: Any,
        queue: Queue,
        request: Request = None,
        task_dependencies: list = None,
    ):
        # Create SubTask objects and enqueue job (HA_REMOVE) - Dependant on guac_delete jobs
        sub_task_ha_remove_schema = SubTaskCreate(
            name="Remove VirtualMachine from HA",
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            action="ha_remove",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_ha_remove = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_ha_remove_schema
        )
        if not task_dependencies:
            job_ha_remove = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_ha_remove.id, self.db_obj.id
                ).ha_remove,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_ha_remove = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_ha_remove.id, self.db_obj.id
                ).ha_remove,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_ha_remove:
            raise JobEnqueueError(job_key="ha_remove")
        self._update_subtask_job_id(db, sub_task_ha_remove.id, job_ha_remove.id)
        return job_ha_remove

    def _subtask_ipv4_get(
        self,
        db: Session,
        request: Request,
        parent_task_id: Any,
        queue: Queue,
        task_dependencies: list = None,
    ):
        # Create SubTask objects and enqueue job (IPV4_GET)
        sub_task_ipv4_get_schema = SubTaskCreate(
            name="Get IPv4 of VirtualMachine",
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            action="vm_ipv4_get",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_ipv4_get = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_ipv4_get_schema
        )
        if not task_dependencies:
            job_ipv4_get = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_ipv4_get.id, self.db_obj.id
                ).ipv4_get,
                retry=Retry(
                    max=int(settings.worker_max_retry) + 5,
                    interval=[10, 30, 60, 90, 120],
                ),
            )
        else:
            job_ipv4_get = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_ipv4_get.id, self.db_obj.id
                ).ipv4_get,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_ipv4_get:
            raise JobEnqueueError(job_key="vm_ipv4_get")
        self._update_subtask_job_id(db, sub_task_ipv4_get.id, job_ipv4_get.id)
        return job_ipv4_get

    def _subtask_ipv4_set(
        self,
        db: Session,
        request: Request,
        parent_task_id: Any,
        queue: Queue,
        task_dependencies: list = None,
    ):
        # Create SubTask objects and enqueue job (IPV4_SET)
        sub_task_ipv4_set_schema = SubTaskCreate(
            name="Set IPv4 of VirtualMachine",
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            action="vm_ipv4_set",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_ipv4_set = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_ipv4_set_schema
        )
        if not task_dependencies:
            job_ipv4_set = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_ipv4_set.id, self.db_obj.id
                ).ipv4_set,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_ipv4_set = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_ipv4_set.id, self.db_obj.id
                ).ipv4_set,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_ipv4_set:
            raise JobEnqueueError(job_key="vm_ipv4_set")
        self._update_subtask_job_id(db, sub_task_ipv4_set.id, job_ipv4_set.id)
        return job_ipv4_set

    def _subtask_actions_reboot(
        self,
        db: Session,
        request: Request,
        parent_task_id: Any,
        queue: Queue,
        task_dependencies: list = None,
    ):
        # Create SubTask objects and enqueue job (REBOOT)
        sub_task_reboot_schema = SubTaskCreate(
            name="Reboot VirtualMachine",
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            action="vm_reboot",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_reboot = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_reboot_schema
        )
        if not task_dependencies:
            job_reboot = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_reboot.id, self.db_obj.id
                ).actions_reboot,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_reboot = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_reboot.id, self.db_obj.id
                ).actions_reboot,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_reboot:
            raise JobEnqueueError(job_key="vm_reboot")
        self._update_subtask_job_id(db, sub_task_reboot.id, job_reboot.id)
        return job_reboot

    def _subtask_actions_stop(
        self,
        db: Session,
        parent_task_id: Any,
        queue: Queue,
        request: Request = None,
        task_dependencies: list = None,
    ):
        # Create SubTask objects and enqueue job (STOP)
        sub_task_stop_schema = SubTaskCreate(
            name="Stop VirtualMachine",
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            action="vm_stop",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_stop = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_stop_schema
        )
        if not task_dependencies:
            job_stop = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_stop.id, self.db_obj.id
                ).actions_stop,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_stop = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_stop.id, self.db_obj.id
                ).actions_stop,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_stop:
            raise JobEnqueueError(job_key="vm_stop")
        self._update_subtask_job_id(db, sub_task_stop.id, job_stop.id)
        return job_stop

    def _subtask_actions_start(
        self,
        db: Session,
        request: Request,
        parent_task_id: Any,
        queue: Queue,
        task_dependencies: list = None,
    ):
        # Create SubTask objects and enqueue job (START)
        sub_task_start_schema = SubTaskCreate(
            name="Start VirtualMachine",
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            action="vm_start",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_start = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_start_schema
        )
        if not task_dependencies:
            job_start = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_start.id, self.db_obj.id
                ).actions_start,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_start = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_start.id, self.db_obj.id
                ).actions_start,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_start:
            raise JobEnqueueError(job_key="vm_start")
        self._update_subtask_job_id(db, sub_task_start.id, job_start.id)
        return job_start

    def _subtask_actions_pause(
        self,
        db: Session,
        request: Request,
        parent_task_id: Any,
        queue: Queue,
        task_dependencies: list = None,
    ):
        # Create SubTask objects and enqueue job (PAUSE)
        sub_task_pause_schema = SubTaskCreate(
            name="Pause VirtualMachine",
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            action="vm_pause",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_pause = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_pause_schema
        )
        if not task_dependencies:
            job_pause = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_pause.id, self.db_obj.id
                ).actions_pause,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_pause = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_pause.id, self.db_obj.id
                ).actions_pause,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_pause:
            raise JobEnqueueError(job_key="vm_pause")
        self._update_subtask_job_id(db, sub_task_pause.id, job_pause.id)
        return job_pause

    def _subtask_actions_reset(
        self,
        db: Session,
        request: Request,
        parent_task_id: Any,
        queue: Queue,
        task_dependencies: list = None,
    ):
        # Create SubTask objects and enqueue job (RESET)
        sub_task_reset_schema = SubTaskCreate(
            name="Reset VirtualMachine",
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            action="vm_reset",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_reset = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_reset_schema
        )
        if not task_dependencies:
            job_reset = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_reset.id, self.db_obj.id
                ).actions_reset,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_reset = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_reset.id, self.db_obj.id
                ).actions_reset,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_reset:
            raise JobEnqueueError(job_key="vm_reset")
        self._update_subtask_job_id(db, sub_task_reset.id, job_reset.id)
        return job_reset

    def _subtask_actions_shutdown(
        self,
        db: Session,
        request: Request,
        parent_task_id: Any,
        queue: Queue,
        task_dependencies: list = None,
    ):
        # Create SubTask objects and enqueue job (SHUTDOWN)
        sub_task_shutdown_schema = SubTaskCreate(
            name="Shut down VirtualMachine",
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            action="vm_shutdown",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_shutdown = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_shutdown_schema
        )
        if not task_dependencies:
            job_shutdown = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_shutdown.id, self.db_obj.id
                ).actions_shutdown,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_shutdown = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_shutdown.id, self.db_obj.id
                ).actions_shutdown,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_shutdown:
            raise JobEnqueueError(job_key="vm_shutdown")
        self._update_subtask_job_id(db, sub_task_shutdown.id, job_shutdown.id)
        return job_shutdown

    def _subtask_actions_resume(
        self,
        db: Session,
        request: Request,
        parent_task_id: Any,
        queue: Queue,
        task_dependencies: list = None,
    ):
        # Create SubTask objects and enqueue job (SHUTDOWN)
        sub_task_resume_schema = SubTaskCreate(
            name="Resume VirtualMachine",
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            action="vm_resume",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_resume = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_resume_schema
        )
        if not task_dependencies:
            job_resume = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_resume.id, self.db_obj.id
                ).actions_resume,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_resume = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_resume.id, self.db_obj.id
                ).actions_resume,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_resume:
            raise JobEnqueueError(job_key="vm_resume")
        self._update_subtask_job_id(db, sub_task_resume.id, job_resume.id)
        return job_resume

    def _subtask_actions_hibernate(
        self,
        db: Session,
        request: Request,
        parent_task_id: Any,
        queue: Queue,
        task_dependencies: list = None,
    ):
        # Create SubTask objects and enqueue job (HIBERNATE)
        sub_task_hibernate_schema = SubTaskCreate(
            name="hibernate VirtualMachine",
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            action="vm_hibernate",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_hibernate = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_hibernate_schema
        )
        if not task_dependencies:
            job_hibernate = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_hibernate.id, self.db_obj.id
                ).actions_hibernate,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_hibernate = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_hibernate.id, self.db_obj.id
                ).actions_hibernate,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_hibernate:
            raise JobEnqueueError(job_key="vm_hibernate")
        self._update_subtask_job_id(db, sub_task_hibernate.id, job_hibernate.id)
        return job_hibernate

    def _subtask_vm_guac_delete(
        self,
        db: Session,
        parent_task_id: Any,
        queue: Queue,
        guacamole_id: Any,
        request: Request = None,
        task_dependencies: list = None,
    ):
        # Create SubTask objects and enqueue job (GUAC_DELETE)
        sub_task_guac_delete_schema = SubTaskCreate(
            name="Delete Guacamole objects for VirtualMachine",
            object_type="Guacamole",
            object_id=guacamole_id,
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
                kvs_guacamole_id=guacamole_id,
                kvs_task_object_id=sub_task_guac_delete.id,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_guac_delete = queue.enqueue(
                guacamole_delete_worker,
                kvs_guacamole_id=guacamole_id,
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

    def _create_and_enqueue_guacamole(
        self,
        db: Session,
        request: Request,
        parent_task_id: Any,
        queue: Queue,
        user: User,
        interface: GuacamoleConnectionProfile,
        event: Event = None,
        task_dependencies: list = None,
    ):
        event_id = event.id if event is not None else None
        # Create Guacamole for assigned user
        try:
            new_guac = Guacamole(
                id=uuid.uuid4(),
                name=f"{self.db_obj.name}-{interface.protocol}-{user.username}",
                guacd_hostname="",
                guacd_port=4822,
                guacd_encryption=True,
                connection_profile=interface.id,
                userId=user.id,
                eventId=event_id,
                createdAt=datetime.now(timezone.utc),
                updatedAt=datetime.now(timezone.utc),
                createdById=request_user_validation(db, request),
                updatedById=request_user_validation(db, request),
            )
            db.add(new_guac)
            self.db_obj.guacamoles.append(new_guac)
            self._commit(db, self.db_obj)
            if not task_dependencies:
                job_provision = CRUDGuacamole(
                    Guacamole
                )._subtask_guacamole_provision(
                    db=db,
                    request=request,
                    parent_task_id=parent_task_id,
                    queue=queue,
                    user=user,
                    connection_profile=interface,
                    virtual_machine=self.db_obj,
                    db_obj_id=new_guac.id,
                )
            else:
                job_provision = CRUDGuacamole(
                    Guacamole
                )._subtask_guacamole_provision(
                    db=db,
                    request=request,
                    parent_task_id=parent_task_id,
                    queue=queue,
                    user=user,
                    connection_profile=interface,
                    virtual_machine=self.db_obj,
                    db_obj_id=new_guac.id,
                    task_dependencies=task_dependencies,
                )
            # Create ObjectPermission for object owner
            CRUDObjectPermission(ObjectPermission).create_full(
                db, request, "Guacamole", new_guac.id, self.db_obj.createdById
            )
            return job_provision
        except Exception as e:
            print(e)

    # Utility used in bulk Guacamole creation
    def _create_and_enqueue_guacamole_event(
        self,
        db: Session,
        request: Request,
        interface: GuacamoleConnectionProfile,
        event: Event,
        user: User,
        parent_task: UUID4,
        is_teacher: bool = False,
        student_username: str = None,
    ):
        if is_teacher:
            new_name = str(
                f"{event.name}-{user.username}-PROV-{student_username}-{interface.protocol}"
            )
        else:
            new_name = str(
                f"{event.name}-{user.username}-PROV-{interface.protocol}"
            )
        name_pattern = new_name.replace("PROV", "%")
        db_guac = (
            db.query(Guacamole)
            .filter(Guacamole.name.like(name_pattern))
            .first()
        )
        if db_guac:
            return {"guac_object": db_guac, "created": False}

        # Create Guacamole for assigned user
        try:
            new_guac = Guacamole(
                id=uuid.uuid4(),
                name=new_name,
                guacd_hostname="",
                guacd_port=4822,
                guacd_encryption=True,
                connection_profile=interface.id,
                userId=user.id,
                eventId=event.id,
                createdAt=datetime.now(timezone.utc),
                updatedAt=datetime.now(timezone.utc),
                createdById=request_user_validation(db, request),
                updatedById=request_user_validation(db, request),
            )
            db.add(new_guac)
            self.db_obj.guacamoles.append(new_guac)
            db.add(self.db_obj)
            self._commit(db)
            db.refresh(self.db_obj)
            db.refresh(new_guac)
            job_provision = CRUDGuacamole(
                Guacamole
            )._subtask_guacamole_provision(
                db=db,
                request=request,
                parent_task_id=parent_task,
                queue=queue_guacamole,
                user=user,
                connection_profile=interface,
                virtual_machine=self.db_obj,
                db_obj_id=new_guac.id,
            )
            # Create ObjectPermission for object owner
            CRUDObjectPermission(ObjectPermission).create_full(
                db,
                request,
                "Guacamole",
                new_guac.id,
                self.db_obj.createdById,
            )
            # Create ObjectPermission for each teacher in event
            # Use cached teacher IDs if available, otherwise query
            if (
                not hasattr(self, "_event_teacher_ids_cache")
                or self._event_teacher_ids_cache.get("event_id") != event.id
            ):
                role_teacher = (
                    db.query(RoleModel)
                    .filter(RoleModel.key == "lehrende")
                    .first()
                )
                event_users_teachers = (
                    db.query(EventsUser)
                    .filter(
                        EventsUser.event_id == event.id,
                        EventsUser.role_id == role_teacher.id,
                    )
                    .all()
                )
                self._event_teacher_ids_cache = {
                    "event_id": event.id,
                    "teacher_ids": [u.user_id for u in event_users_teachers],
                }
            event_teacher_ids = self._event_teacher_ids_cache["teacher_ids"]
            for teacher in event_teacher_ids:
                # Skip self if object owner is teacher
                if user.id == teacher:
                    continue
                CRUDObjectPermission(ObjectPermission).create_full(
                    db, request, "Guacamole", new_guac.id, teacher
                )
        except Exception as e:
            print(e)
        return {"guac_object": new_guac, "created": True}

    def _ensure_pve(self):
        try:
            proxmox = ProxmoxCluster().proxmox
        except Exception:
            raise ProxmoxConnectionError()

    def _delete_empty_parents(self, db: Session, parent_task_id: UUID4):
        try:
            parent_task = db.get(TaskModel, parent_task_id)
            db.delete(parent_task)
            db.commit()
        except Exception as e:
            db.rollback()
            raise BadRequestError(
                message=f"Failed to delete empty parent task {parent_task_id}: {e}"
            )


virtual_machine = CRUDVirtualMachine(VirtualMachine)
