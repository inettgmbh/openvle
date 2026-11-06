import re
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from proxmoxer.core import ResourceException
from rq import Queue, Retry
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.config import Settings
from core.exceptions import (
    BadRequestError,
    JobEnqueueError,
    ObjectInUseError,
    ObjectNotFound,
    OperationDependencyMissing,
    ProtectedObjectError,
    ProxmoxConnectionError,
    ProxmoxRequestError,
    ProxmoxResourceNotFound,
    RequiredParameterMissingError,
)
from core.redis import queue_pve_vm_actions, queue_pve_vm_clone
from models import (
    OS,
    Application,
    Course,
    Event,
    GuacamoleConnectionProfile,
    ObjectPermission,
    Tag,
    Template,
    VirtualMachine,
)
from models.associations import (
    course_template_association_table,
    template_event_association_table,
)
from models.sub_tasks import SubTask as SubTaskModel
from models.tasks import Task as TaskModel
from pve.cluster import ProxmoxCluster
from pve.templates import ProxmoxTemplate
from pve.virtual_machines import ProxmoxVirtualMachine
from schemas.guacamole_connection_profiles import (
    GuacamoleConnectionProfileCreate,
)
from schemas.sub_tasks import SubTaskCreate
from schemas.tasks import TaskCreate
from schemas.templates import TemplateCreate, TemplateUpdate, TemplateUpdateApps

from .base import CRUDBase
from .guacamole_connection_profiles import CRUDGuacamoleConnectionProfile
from .object_permissions import CRUDObjectPermission
from .sub_tasks import CRUDSubTask
from .tags import CRUDTag
from .tasks import CRUDTask

settings = Settings()

from middlewares.i18n import _


class CRUDTemplate(CRUDBase[Template, TemplateCreate, TemplateUpdate]):
    def __init__(self, db: Session = None, id: Any = None):
        self.model = Template
        self.db_obj = db.get(Template, id) if id is not None else None

    # Get template by name
    def get_by_name(self, db: Session, *, name: str) -> Template | None:
        return db.query(Template).filter(Template.name == name).first()

    # Internal functions
    def _update_subtask_job_id(
        self, db: Session, sub_task_id: Any, job_id: Any
    ):
        sub_task = CRUDBase(SubTaskModel).get(db, sub_task_id)
        sub_task.job_id = job_id
        db.add(sub_task)
        self._commit(db)

    def _create_interfaces(self, db: Session, request: Request, interfaces):
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
            except:
                continue  # TODO

    def _subtask_vm_clone(
        self,
        db: Session,
        request: Request,
        parent_task_id: Any,
        queue: Queue,
        source_vm_id: Any,
        task_dependencies: list = None,
    ):
        # Create SubTask objects and enqueue job (CLONE *without creating VirtualMachine object in DB)
        sub_task_clone_schema = SubTaskCreate(
            name=f"Clone VirtualMachine: {self.db_obj.name}",
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
                    sub_task_clone.id, source_vm_id
                ).create_from_vm_without_db,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
                job_timeout=600,
                result_ttl=86400,
            )
        else:
            job_clone = queue.enqueue(
                ProxmoxVirtualMachine(
                    sub_task_clone.id, source_vm_id
                ).create_from_vm_without_db,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
                job_timeout=600,
                result_ttl=86400,
            )
        if not job_clone:
            raise JobEnqueueError(job_key="vm_clone")
        self._update_subtask_job_id(db, sub_task_clone.id, job_clone.id)
        return job_clone

    def _subtask_vm_convert(
        self,
        db: Session,
        request: Request,
        parent_task_id: Any,
        queue: Queue,
        job_clone: Any,
        source_vm_id: Any,
        task_dependencies: list = None,
    ):
        # Create SubTask objects and enqueue job (CONVERT)
        sub_task_convert_schema = SubTaskCreate(
            name=f"Convert {self.db_obj.name} into Template",
            object_type="VirtualMachine",
            object_id=self.db_obj.id,
            action="vm_convert",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_convert = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_convert_schema
        )
        if not task_dependencies:
            job_convert = queue.enqueue(
                ProxmoxTemplate(sub_task_convert.id, self.db_obj.id).create,
                source_vm_id=source_vm_id,
                depends_on_task_id=job_clone.id,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_convert = queue.enqueue(
                ProxmoxTemplate(sub_task_convert.id, self.db_obj.id).create,
                source_vm_id=source_vm_id,
                depends_on_task_id=job_clone.id,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_convert:
            raise JobEnqueueError(job_key="vm_convert")
        self._update_subtask_job_id(db, sub_task_convert.id, job_convert.id)
        return job_convert

    def _subtask_template_update(
        self,
        db: Session,
        request: Request,
        parent_task_id: Any,
        queue: Queue,
        task_dependencies: list = None,
    ):
        # Create SubTask objects and enqueue job (UPDATE)
        sub_task_update_schema = SubTaskCreate(
            name=f"Update {self.db_obj.name} with correct resource data",
            object_type="Template",
            object_id=self.db_obj.id,
            action="template_update",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_update = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_update_schema
        )
        if not task_dependencies:
            job_update = queue.enqueue(
                ProxmoxTemplate(sub_task_update.id, self.db_obj.id).update,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_update = queue.enqueue(
                ProxmoxTemplate(sub_task_update.id, self.db_obj.id).update,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_update:
            raise JobEnqueueError(job_key="template_update")
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
            name=f"Update {self.db_obj.name} tags",
            object_type="Template",
            object_id=self.db_obj.id,
            action="template_tags_update",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_update = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_update_schema
        )
        if not task_dependencies:
            job_tags_update = queue.enqueue(
                ProxmoxTemplate(sub_task_update.id, self.db_obj.id).update_tags,
                tag_to_remove=tag_to_remove,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_tags_update = queue.enqueue(
                ProxmoxTemplate(sub_task_update.id, self.db_obj.id).update_tags,
                tag_to_remove=tag_to_remove,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_tags_update:
            raise JobEnqueueError(job_key="template_tags_update")
        self._update_subtask_job_id(db, sub_task_update.id, job_tags_update.id)
        return job_tags_update

    def _subtask_template_delete(
        self,
        db: Session,
        request: Request,
        parent_task_id: Any,
        queue: Queue,
        task_dependencies: list = None,
    ):
        # Create SubTask objects and enqueue job (UPDATE)
        sub_task_delete_schema = SubTaskCreate(
            name=f"Delete {self.db_obj.name}",
            object_type="Template",
            object_id=self.db_obj.id,
            action="template_delete",
            attempt=0,
            parent_task=parent_task_id,
        )
        sub_task_delete = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_delete_schema
        )
        if not task_dependencies:
            job_delete = queue.enqueue(
                ProxmoxTemplate(sub_task_delete.id, self.db_obj.id).delete,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        else:
            job_delete = queue.enqueue(
                ProxmoxTemplate(sub_task_delete.id, self.db_obj.id).delete,
                depends_on=task_dependencies,
                retry=Retry(
                    max=settings.worker_max_retry, interval=[10, 30, 60]
                ),
            )
        if not job_delete:
            raise JobEnqueueError(job_key="template_delete")
        self._update_subtask_job_id(db, sub_task_delete.id, job_delete.id)
        return job_delete

    # Create Template from source_vm
    def create(
        self, db: Session, request: Request, *, obj_in: TemplateCreate
    ) -> Template:
        obj_in_data = jsonable_encoder(obj_in)
        source_vm = CRUDBase(VirtualMachine).get(db, obj_in.source_vm)
        if not source_vm.proxmoxId:
            raise OperationDependencyMissing(
                message=_("Source VirtualMachine has no proxmoxId")
            )
        if source_vm.status != "stopped":
            raise OperationDependencyMissing(
                message=_(
                    "The provided source_vm may only be cloned and converted in status 'stopped'."
                )
            )
        obj_in_data.pop("source_vm")
        self._initialize_object_fields(
            db=db, obj_data_in=obj_in_data, request=request
        )
        self.db_obj.os = source_vm.os
        self.db_obj.name = str(self.db_obj.name)[:100]
        self.db_obj = self._commit(db, self.db_obj)
        # Create tags for new Template based on source_vm_conf
        source_vm_tags = CRUDTag(Tag)._get_tags_for_object_internal(
            db=db, objectId=source_vm.id, objectType="VirtualMachine"
        )
        if source_vm_tags:
            CRUDTag(Tag)._inherit_tags(
                db=db,
                source_object_id=source_vm.id,
                target_object_id=self.db_obj.id,
                source_object_type="VirtualMachine",
                target_object_type="Template",
            )
        # Create Task object
        new_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(name=f"Create Template: {self.db_obj.name}"),
        )
        job_clone = self._subtask_vm_clone(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_clone,
            source_vm_id=source_vm.id,
        )
        job_convert = self._subtask_vm_convert(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_clone,
            job_clone=job_clone,
            source_vm_id=source_vm.id,
            task_dependencies=[job_clone],
        )
        job_update = self._subtask_template_update(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_actions,
            task_dependencies=[job_clone, job_convert],
        )
        self.db_obj.status = "queued"
        # Create object_full ObjectPermission for object creator
        CRUDObjectPermission(ObjectPermission).create_full(
            db, request, "Template", self.db_obj.id, request.user.id
        )
        interfaces = db.query(GuacamoleConnectionProfile).filter(
            GuacamoleConnectionProfile.objectId == source_vm.id,
            GuacamoleConnectionProfile.objectType == "VirtualMachine",
        )
        self._create_interfaces(db, request, interfaces)
        return self._commit(db, self.db_obj)

    # Update Template
    def update(
        self, id: Any, db: Session, request: Request, *, obj_in: TemplateUpdate
    ) -> Template:
        self.db_obj = self.get(db, id)
        obj_data = jsonable_encoder(self.db_obj)
        update_data = self._merge_request_with_db_object(obj_in, obj_data)
        # Handling of Template OS
        if "os" in update_data:
            os = CRUDBase(OS).get(db=db, id=obj_in.os)
            self.db_obj.os = os.id
        self._update_meta(request)
        # Create Task object
        new_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(name=f"Update Template: {self.db_obj.name}"),
        )
        job_update = self._subtask_template_update(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_clone,
        )
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    # Update template Applications
    def update_apps(
        self,
        id: Any,
        db: Session,
        request: Request,
        *,
        obj_in: TemplateUpdateApps,
    ) -> Template:
        self.db_obj = self.get(db, id)
        obj_data = jsonable_encoder(self.db_obj)
        update_data = self._merge_request_with_db_object(obj_in, obj_data)
        # Handling of Apps
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

    # Delete object with ID
    def delete(self, db: Session, request: Request, id: Any):
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
                model_name=Template.__name__,
                operation="template_delete",
                source="Proxmox VE" if pve_protected else None,
            )
        vm_count = (
            db.query(func.count(VirtualMachine.id))
            .filter(VirtualMachine.template == id)
            .scalar()
        )

        course_count = (
            db.query(func.count())
            .select_from(course_template_association_table)
            .filter(course_template_association_table.c.template_id == id)
            .scalar()
        )

        event_count = (
            db.query(func.count())
            .select_from(template_event_association_table)
            .filter(template_event_association_table.c.template_id == id)
            .scalar()
        )

        references = {
            VirtualMachine.__name__: vm_count,
            Course.__name__: course_count,
            Event.__name__: event_count,
        }
        references = {
            name: count for name, count in references.items() if count
        }
        if references:
            raise ObjectInUseError(
                model_name=Template.__name__, references=references
            )
        # Create Task object
        new_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(name=f"Delete Template: {self.db_obj.name}"),
        )
        job_delete = self._subtask_template_delete(
            db=db,
            request=request,
            parent_task_id=new_task.id,
            queue=queue_pve_vm_actions,
        )
        self.db_obj.status = "Deleting"
        self.db_obj = self._commit(db, self.db_obj)

    def load_from_pve(
        self,
        db: Session,
        request: Request,
        proxmox_id: int,
        load_tags: bool = False,
    ) -> Template:
        # Get config for template
        conf = self.get_pve_template(db, proxmox_id)
        # Get storage value from first disk
        pve_disk_keys = ["scsi0", "sata0", "ide0", "virtio0"]
        pve_temp_disk = 0
        for key in pve_disk_keys:
            if key in conf:
                match = re.search(r"size=(\d+)G", conf[key])
                if match:
                    pve_temp_disk = int(match.group(1))
                    break  # Stop after the first match
        # Create new Template in DB with values of PVE Template
        self.db_obj = Template(
            id=uuid.uuid4(),
            name=conf["name"],
            status="available",
            proxmoxId=proxmox_id,
            proxmoxNode=conf["node"],
            cpu=conf["cores"],
            ram=conf["memory"],
            disk=pve_temp_disk,
            prevent_delete=False,
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc),
            createdById=request.user.id,
            updatedById=request.user.id,
        )
        if conf["description"]:
            self.db_obj.description = conf["description"]
        self.db_obj = self._commit(db, self.db_obj)
        if load_tags:
            # Create Tags for Template
            CRUDTag(Tag)._create_for_pve_tags_list(
                db=db,
                objectId=self.db_obj.id,
                objectType="Template",
                pve_tags=conf["tags"],
            )
        return self.db_obj

    def get_pve_template(self, db: Session, proxmox_id: int):
        # Check if Template already exists in DB with proxmox_id
        temp_in_db = (
            db.query(Template).filter(Template.proxmoxId == proxmox_id).first()
        )
        if temp_in_db:
            raise BadRequestError(
                message=_(
                    "Template with {proxmox_id} already exists as {temp_in_db.name}"
                ).format(proxmox_id=proxmox_id, temp_in_db=temp_in_db)
            )
        # PVE connection
        try:
            proxmox_conn = ProxmoxCluster()
        except:
            raise ProxmoxConnectionError()
        # Get config from PVE
        try:
            node = proxmox_conn.pve_get_node(proxmox_id)
            conf = (
                proxmox_conn.proxmox.nodes(node).qemu(proxmox_id).config.get()
            )
        except:
            raise BadRequestError(
                message=_("Unable to retrieve Template from PVE")
            )
        if not conf:
            raise ProxmoxResourceNotFound(
                resource_type="Template",
                field_type="vmid",
                field_value=proxmox_id,
            )
        # Assert config is from a Template
        if conf.get("template") != 1:
            raise BadRequestError(
                message=_(
                    "The provided proxmox_id is a VirtualMachine, not a Template"
                )
            )
        conf["node"] = node
        return conf


template = CRUDTemplate(Template)
