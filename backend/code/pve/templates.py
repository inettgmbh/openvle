from proxmoxer.core import ResourceException
from pydantic import UUID4
from rq.job import Job

from controllers.sub_tasks import CRUDSubTask
from controllers.tags import CRUDTag
from core.core_utils import db_save
from core.mariadb import SessionLocal
from core.redis import redis_connection
from models import (
    Changelog,
    GuacamoleConnectionProfile,
    ObjectPermission,
    SubTask,
    Tag,
    VirtualMachine,
)
from models.templates import Template as TemplateModel

from .worker_utils import *

db = SessionLocal()


class ProxmoxTemplate:
    def __init__(self, kvs_task_object_id: UUID4, kvs_template_id: UUID4):
        try:
            # Connections
            self.db = None
            self.pve_connection = None
            self.proxmox = None
            # DB Objects
            self.kvs_template = None
            self.source_vm = None
            # ID attributes
            self.kvs_template_id = kvs_template_id
            self.source_vm_id = None
            self.kvs_task_object_id = kvs_task_object_id
            # Generated attributes
            self.pve_source_vmid = None
            self.pve_task = None
            self.pve_task_success = None

        except:
            raise CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                502,
                "Failed to initialise ProxmoxVirtualMachine worker class",
            )

    def _start_process(self):
        # Open connection to DB
        self.db = SessionLocal()
        # Get and update Task object
        CRUDSubTask(SubTask).worker_process_start(
            self.db, self.kvs_task_object_id
        )
        # Connect to PVE
        self._pve_init()

    def _pve_init(self):
        # Initiate connection to PVE
        try:
            self.pve_connection = ProxmoxCluster()
            self.proxmox = self.pve_connection.proxmox
        except:
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                502,
                "Failed to retrieve required parameters from PVE",
            )

    async def _check_task_status(self):
        # Break early if success was declared early
        if self.pve_task_success:
            return True

        if self.pve_task:
            pve_task_status = await kvs_await_pve_task_exit(self.pve_task)
            if pve_task_status:  # If true, task succeeded
                self.pve_task_success = True
                return True
            else:
                raise CRUDSubTask(SubTask).worker_process_fail(
                    self.kvs_task_object_id, 408, "Request to PVE has timed out"
                )
        else:
            raise CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                408,
                "Invalid or no process response to PVE request",
            )

    def _pve_config_get(self, vmid: int):
        try:
            return (
                self.proxmox.nodes(ProxmoxCluster().pve_get_node(vmid))
                .qemu(vmid)
                .config.get()
            )
        except Exception as exc:
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"Unable to retrieve config from PVE for Template with ID: {vmid}",
            )
            raise CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    def _get_vm_and_template_objects(self):
        # Get  Template object
        self.kvs_template = self.db.get(TemplateModel, self.kvs_template_id)
        if not self.kvs_template:
            raise CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                404,
                f"Template with ID '{self.kvs_template_id}' not found in database",
            )
        # Get source_vm VirtualMachine object
        if self.source_vm_id:
            self.source_vm = self.db.get(VirtualMachine, self.source_vm_id)
            if not self.source_vm:
                raise CRUDSubTask(SubTask).worker_process_fail(
                    self.kvs_task_object_id,
                    404,
                    f"VirtualMachine with ID '{self.source_vm_id}' not found in database",
                )

    def _job_get(self, task_id: str):
        # Get return_value of previous task from redis
        try:
            task_return_value = Job.fetch(
                id=task_id, connection=redis_connection
            ).return_value()
            if not task_return_value:
                return CRUDSubTask(SubTask).worker_process_fail(
                    self.kvs_task_object_id,
                    404,
                    "Error retrieving task objects from database",
                )
        except:
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                404,
                "Error retrieving job objects from database",
            )
        return task_return_value

    def _merge_pve_and_kvs_tags(
        self,
        proxmox_id: str,
        kvs_template_id: UUID4,
        object_type: str = "Template",
        sort_tags: bool = True,
        pve_tags_merge: bool = False,
        tag_to_remove: str = None,
    ) -> str:
        # Get current PVE tags
        pve_tags: list[str] = []
        if pve_tags_merge:
            pve_config = self._pve_config_get(proxmox_id)
            pve_tags_str = pve_config.get("tags")
            pve_tags = pve_tags_str.split(";") if pve_tags_str else []

        # Get KVS tags
        kvs_tags = (
            CRUDTag(Tag)._convert_kvs_to_pve(
                db=self.db, objectId=kvs_template_id, objectType=object_type
            )
            or []
        )

        # Merge and deduplicate
        if sort_tags:
            all_tags = sorted(set(pve_tags) | set(kvs_tags))
        else:
            # Preserve tag order: keep existing PVE tags, then append new KVS tags
            all_tags = list(pve_tags)
            for t in kvs_tags:
                if t not in all_tags:
                    all_tags.append(t)

        if tag_to_remove:
            all_tags = [t for t in all_tags if t != tag_to_remove]

        # Return as string
        return ",".join(all_tags) if all_tags else ""

    def _pve_update(self):
        # PVE API call to update a Template
        try:
            if self.kvs_template.cpu % 2 == 0:
                pve_cores = int(self.kvs_template.cpu / 2)
            else:
                pve_cores = self.kvs_template.cpu
            self.proxmox.nodes(
                ProxmoxCluster().pve_get_node(self.kvs_template.proxmoxId)
            ).qemu(self.kvs_template.proxmoxId).config.put(
                name=self.kvs_template.name,
                cores=pve_cores,
                memory=self.kvs_template.ram,
                description=self.kvs_template.description,
            )
        except Exception as exc:
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"template_update operation failed for {self.kvs_template.name}",
            )
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    def _pve_tags_update(self, tag_to_remove: str = None):
        try:
            template_tags = self._merge_pve_and_kvs_tags(
                proxmox_id=self.kvs_template.proxmoxId,
                kvs_template_id=self.kvs_template.id,
                pve_tags_merge=True,
                tag_to_remove=tag_to_remove,
            )
            self.proxmox.nodes(
                ProxmoxCluster().pve_get_node(self.kvs_template.proxmoxId)
            ).qemu(self.kvs_template.proxmoxId).config.put(tags=template_tags)
        except Exception as exc:
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"template_tags_update operation failed for {self.kvs_template.name}",
            )
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    def _pve_delete(self):
        if not self.kvs_template.proxmoxId:
            self.pve_task_success = True
            return
        try:
            self.pve_task = (
                self.proxmox.nodes(
                    ProxmoxCluster().pve_get_node(self.kvs_template.proxmoxId)
                )
                .qemu(self.kvs_template.proxmoxId)
                .delete()
            )
        except ResourceException:
            self.pve_task_success = True
            self._kvs_template_delete()
            return CRUDSubTask(SubTask).worker_process_success(
                self.kvs_task_object_id, 200, "Template deletion successful!"
            )
        except Exception as exc:
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"template_delete operation failed for {self.kvs_template.name}",
            )
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    def _kvs_template_delete(self):
        # Delete Template from database and delete any related changelogs, object_permissions and connection_profiles
        try:
            self.db.delete(self.kvs_template)
            changelogs = (
                self.db.query(Changelog)
                .filter(
                    Changelog.objectId == self.kvs_template_id,
                    Changelog.object == "Template",
                )
                .all()
            )
            if changelogs:
                for changelog in changelogs:
                    self.db.delete(changelog)
            object_permissions = self.db.query(ObjectPermission).filter(
                ObjectPermission.object_id == self.kvs_template_id,
                ObjectPermission.object_type == "Template",
            )
            if object_permissions:
                for perm in object_permissions:
                    self.db.delete(perm)
            tags = self.db.query(Tag).filter(
                Tag.objectId == self.kvs_template_id,
                Tag.objectType == "Template",
            )
            for tag in tags:
                self.db.delete(tag)
            connection_profiles = (
                self.db.query(GuacamoleConnectionProfile)
                .filter(
                    GuacamoleConnectionProfile.objectType == "Template",
                    GuacamoleConnectionProfile.objectId == self.kvs_template_id,
                )
                .all()
            )
            if connection_profiles:
                for interface in connection_profiles:
                    self.db.delete(interface)
            self.db.commit()
        except:
            self.kvs_template.status = "deleted"
            self.kvs_template.proxmoxId = None
            self.kvs_template = self.db.merge(self.kvs_template)
            self.db.add(self.kvs_template)
            self.db.commit()
            self.db.refresh(self.kvs_template)
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                500,
                "The Template has been deleted from Proxmox but could not be deleted from the database. The Template object status has been updated to 'deleted'",
            )

    def _pve_vm_convert(self):
        # PVE API call to convert the PVE VirtualMachine into a Template
        try:
            self.pve_task = (
                self.proxmox.nodes(
                    ProxmoxCluster().pve_get_node(self.pve_source_vmid)
                )
                .qemu(self.pve_source_vmid)
                .template.post()
            )
        except Exception as exc:
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"vm_convert operation failed for {self.pve_source_vmid}",
            )
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    async def create(self, source_vm_id: UUID4, depends_on_task_id: str):
        self.source_vm_id = source_vm_id
        self._start_process()
        self.pve_source_vmid = self._job_get(depends_on_task_id)["vmid"]
        self._get_vm_and_template_objects()
        self.kvs_template.proxmoxId = self.pve_source_vmid
        self.kvs_template.proxmoxNode = ProxmoxCluster().pve_get_node(
            self.pve_source_vmid
        )
        self.kvs_template.status = "available"
        self.kvs_template = self.db.merge(self.kvs_template)
        self.db.add(self.kvs_template)
        self.db.commit()
        self.db.refresh(self.kvs_template)
        self._pve_vm_convert()
        await self._check_task_status()
        if self.pve_task_success:
            self.db.close()
            CRUDSubTask(SubTask).worker_process_success(
                self.kvs_task_object_id,
                200,
                "VirtualMachine conversion successful!",
            )
        else:
            self.kvs_template.proxmoxId = None
            self.kvs_template.proxmoxNode = None
            self.kvs_template.status = "error"
            self.kvs_template = self.db.merge(self.kvs_template)
            self.db.add(self.kvs_template)
            self.db.commit()
            self.db.close()
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id, 403, "VirtualMachine conversion failed"
            )

    async def update(self):
        """
        Update PVE Template
        """
        self._start_process()
        self._get_vm_and_template_objects()
        self._pve_update()
        self.db.close()
        CRUDSubTask(SubTask).worker_process_success(
            self.kvs_task_object_id, 201, "Template update successful!"
        )

    async def update_tags(self, tag_to_remove: str = False):
        """
        Update tags for PVE Template
        """
        self._start_process()
        self._get_vm_and_template_objects()
        self._pve_tags_update(tag_to_remove=tag_to_remove)
        self.db.close()
        CRUDSubTask(SubTask).worker_process_success(
            self.kvs_task_object_id, 201, "Template tags updated successfully!"
        )

    async def delete(self):
        self._start_process()
        self._get_vm_and_template_objects()
        is_protected = self.kvs_template.prevent_delete
        pve_protected = False
        if not is_protected and self.kvs_template.proxmoxId:
            try:
                pve_config = (
                    self.proxmox.nodes(
                        ProxmoxCluster().pve_get_node(
                            self.kvs_template.proxmoxId
                        )
                    )
                    .qemu(self.kvs_template.proxmoxId)
                    .config.get()
                )
                if pve_config.get("protection") == 1:
                    self.kvs_template.prevent_delete = True
                    db_save(self.db, self.kvs_template)
                    is_protected = True
                    pve_protected = True
            except ResourceException:
                # Template not found on PVE (e.g. 404, 501) — assume not protected, proceed with deletion
                pass
        if is_protected:
            self.db.close()
            source = "Proxmox VE" if pve_protected else "the database"
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                403,
                f"This Template may not be deleted. It is protected on {source}.",
            )
        self._pve_delete()
        await self._check_task_status()
        if self.pve_task_success:
            self._kvs_template_delete()
            self.db.close()
            CRUDSubTask(SubTask).worker_process_success(
                self.kvs_task_object_id, 200, "Template deletion successful!"
            )
