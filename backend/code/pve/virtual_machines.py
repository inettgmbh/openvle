import ipaddress

from proxmoxer.core import ResourceException
from pydantic import UUID4

from controllers.changelog import CRUDChangelog
from controllers.sub_tasks import CRUDSubTask
from controllers.tags import CRUDTag
from core.core_utils import db_save, vm_ip_in_subnet
from core.mariadb import SessionLocal
from models import (
    Changelog,
    Guacamole,
    GuacamoleConnectionProfile,
    ObjectPermission,
    SubTask,
    Tag,
)
from models.templates import Template as TemplateModel
from models.virtual_machines import VirtualMachine as VirtualMachineModel

from .worker_utils import *


class ProxmoxVirtualMachine:
    def __init__(self, kvs_task_object_id: UUID4, kvs_vm_id: UUID4):
        try:
            # System
            self.settings = Settings()
            # Connections
            self.db = None
            self.pve_connection = None
            self.proxmox = None
            # DB Objects
            self.kvs_vm = None
            self.source_template = None
            self.source_vm = None
            # ID attributes
            self.kvs_vm_id = kvs_vm_id
            self.source_vm_id = None
            self.kvs_task_object_id = kvs_task_object_id
            # Generated attributes
            self.pve_vm_config = None
            self.target_node = None
            self.source_vm_node = None
            self.new_vmid = None
            self.pve_task = None
            self.pve_task_success = None
            self.request_user_id = None

        except:
            raise CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                500,
                "Failed to initialise ProxmoxVirtualMachine worker class",
            )

    def _start_process(self):
        # Open connection to DB
        self.db = SessionLocal()
        # Get and update Task object
        CRUDSubTask(SubTask).worker_process_start(
            self.db, self.kvs_task_object_id
        )
        self.request_user_id = self.db.get(
            SubTask, self.kvs_task_object_id
        ).createdById
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
                503,
                "Failed to retrieve required parameters from PVE",
            )

    def _get_vm_and_template_objects(self):
        # Get kvs_vm VirtualMachine object
        if self.kvs_vm_id:
            self.kvs_vm = self.db.get(VirtualMachineModel, self.kvs_vm_id)
            if not self.kvs_vm:
                self.db.close()
                raise CRUDSubTask(SubTask).worker_process_fail(
                    self.kvs_task_object_id,
                    404,
                    f"VirtualMachine with ID '{self.kvs_vm_id}' not found in database",
                )
        # Get source_template Template object
        if self.kvs_vm:
            self.source_template = self.db.get(
                TemplateModel, self.kvs_vm.template
            )
            if not self.source_template:
                self.db.close()
                raise CRUDSubTask(SubTask).worker_process_fail(
                    self.kvs_task_object_id,
                    404,
                    f"Template with ID '{self.kvs_vm.template}' not found in database",
                )
        # Get source_vm VirtualMachine object
        if self.source_vm_id:
            self.source_vm = self.db.get(VirtualMachineModel, self.source_vm_id)
            if not self.source_vm:
                self.db.close()
                raise CRUDSubTask(SubTask).worker_process_fail(
                    self.kvs_task_object_id,
                    404,
                    f"VirtualMachine with ID '{self.source_vm_id}' not found in database",
                )

    def _pve_vm_init(self):
        # Check if the VirtualMachine object already has a proxmoxId (VirtualMachine might already exist on PVE)
        if self.kvs_vm.proxmoxId:
            # Check if VirtualMachine exists on PVE
            try:
                vm_on_pve = (
                    self.proxmox.nodes(
                        ProxmoxCluster().pve_get_node(self.kvs_vm.proxmoxId)
                    )
                    .qemu(self.kvs_vm.proxmoxId)
                    .config.get()
                )
                if vm_on_pve:
                    self.pve_task_success = True
                    return
            # ResourceException indicates that a VirtualMachine with that proxmoxId does not exist on the PVE
            except ResourceException:
                pass
            except:
                error_response = CRUDSubTask(SubTask).worker_process_fail(
                    self.kvs_task_object_id,
                    502,
                    "Failed to retrieve VirtualMachine config from PVE",
                )
                self.db.close()
                raise TaskException(error_response)
        self.new_vmid = self.pve_connection.next_vm_id(db=self.db)
        self.kvs_vm.proxmoxId = self.new_vmid
        self.kvs_vm.status = "cloning"
        self.kvs_vm = self.db.merge(self.kvs_vm)
        self.db.add(self.kvs_vm)
        self.db.commit()
        self.db.refresh(self.kvs_vm)

    async def _check_task_status(self):
        if self.pve_task_success:
            return True
        if self.pve_task:
            pve_task_status = await kvs_await_pve_task_exit(self.pve_task)
            if pve_task_status:  # If true, task succeeded
                self.pve_task_success = True
                return True
            else:
                self.db.close()
                raise CRUDSubTask(SubTask).worker_process_fail(
                    self.kvs_task_object_id, 408, "Request to PVE has timed out"
                )
        else:
            self.db.close()
            raise CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                408,
                "Invalid or no process response to PVE request",
            )

    def _parse_excluded_ips(self, excluded_ips_str: str):
        excluded_ips = set()
        if excluded_ips_str:
            for entry in excluded_ips_str.split(","):
                entry = entry.strip().replace(" ", "")  # Remove whitespaces
                if "-" in entry:  # Range of IPs
                    start_ip, end_ip = entry.split("-")
                    start_ip = ipaddress.ip_address(start_ip)
                    end_ip = ipaddress.ip_address(end_ip)
                    for ip_int in range(int(start_ip), int(end_ip) + 1):
                        excluded_ips.add(ipaddress.ip_address(ip_int))
                elif "/" in entry:
                    excluded_ips.update(ipaddress.ip_network(entry).hosts())
                else:
                    excluded_ips.add(ipaddress.ip_address(entry))
        return excluded_ips

    def _get_next_available_ip(self):
        # Generate network object
        network = ipaddress.ip_network(
            f"{self.settings.pve_vms_network}{self.settings.pve_vms_subnet}"
        )
        # Parse excluded IPs and ranges
        excluded_ips = self._parse_excluded_ips(
            self.settings.pve_vms_excluded_ips
        )
        excluded_ips.add(
            ipaddress.ip_address(self.settings.pve_vms_gateway)
        )  # Ensure gateway is excluded

        # Fetch all allocated IPs from the database
        allocated_ips = {
            ipaddress.ip_address(vm.ipv4)
            for vm in self.db.query(VirtualMachineModel).all()
            if vm.ipv4
        }

        # Combine excluded and allocated IPs
        unavailable_ips = excluded_ips.union(allocated_ips)

        # Iterate over the network's hosts to find the first free IP
        for ip in network.hosts():
            # Check if the last octet is .0 or .255 and skip it
            if str(ip).split(".")[-1] in ["0", "1", "254", "255"]:
                continue
            if ip not in unavailable_ips:
                return ip

        self.db.close()
        raise CRUDSubTask(SubTask).worker_process_fail(
            self.kvs_task_object_id,
            503,
            "No available IP addresses left in the subnet.",
        )

    def _merge_pve_and_kvs_tags(
        self,
        proxmox_id: str,
        kvs_vm_id: UUID4,
        object_type: str = "VirtualMachine",
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
                db=self.db, objectId=kvs_vm_id, objectType=object_type
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

    def _pve_clone_template(self):
        try:
            new_vm_tags = self._merge_pve_and_kvs_tags(
                proxmox_id=self.source_template.proxmoxId,
                kvs_vm_id=self.kvs_vm.id,
            )
            self.pve_task = (
                self.proxmox.nodes(
                    ProxmoxCluster().pve_get_node(
                        self.source_template.proxmoxId
                    )
                )
                .qemu(self.source_template.proxmoxId)
                .clone.post(
                    newid=self.new_vmid,
                    name=self.kvs_vm.name,
                    full=1 if settings.pve_vms_full_clone_default else 0,
                    target=self.target_node,
                    pool=settings.pve_vms_pool,
                )
            )
        except Exception as exc:
            self.db.close()
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"template_clone operation failed for {self.kvs_vm.name}",
            )
            raise CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    def _pve_clone_vm(self):
        try:
            new_vm_tags = self._merge_pve_and_kvs_tags(
                proxmox_id=self.source_template.proxmoxId,
                kvs_vm_id=self.kvs_vm.id,
            )
            self.pve_task = (
                self.proxmox.nodes(
                    ProxmoxCluster().pve_get_node(self.source_vm.proxmoxId)
                )
                .qemu(self.source_vm.proxmoxId)
                .clone.post(
                    newid=self.new_vmid,
                    name=self.kvs_vm.name,
                    target=self.target_node,
                    pool=settings.pve_vms_pool,
                )
            )
        except Exception as exc:
            self.db.close()
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"vm_clone operation failed for {self.kvs_vm.name}",
            )
            raise CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    def _pve_config_get(self, vmid: int):
        try:
            return (
                self.proxmox.nodes(ProxmoxCluster().pve_get_node(vmid))
                .qemu(vmid)
                .config.get()
            )
        except Exception as exc:
            self.db.close()
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"Unable to retrieve {self.kvs_vm.name} config from PVE",
            )
            raise CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    def _pve_status_get(self, vmid: int):
        try:
            return (
                self.proxmox.nodes(ProxmoxCluster().pve_get_node(vmid))
                .qemu(vmid)
                .status.current.get()["status"]
            )
        except Exception as exc:
            self.db.close()
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"Unable to retrieve {self.kvs_vm.name} status from PVE",
            )
            raise CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    def _get_current_smbios1_uuid(self):
        """Read the existing SMBIOS UUID from the VM's PVE config."""
        try:
            config = self._pve_config_get(self.kvs_vm.proxmoxId)
            smbios1 = config.get("smbios1", "")
            for part in smbios1.split(","):
                if part.startswith("uuid="):
                    return part.split("=", 1)[1]
        except Exception:
            pass
        return None

    def _build_smbios1_string(self):
        """Build SMBIOS type 1 string for Proxmox VM config.

        Uses base64 encoding (base64=1) so that arbitrary values
        (UUIDs, names with special characters) pass PVE validation.
        Preserves the existing PVE-assigned UUID.
        """
        import base64

        from models.events import Event as EventModel

        family = "null"
        if self.kvs_vm.event:
            event = self.db.get(EventModel, self.kvs_vm.event)
            if event and event.slug:
                family = event.slug

        def b64(val):
            return base64.b64encode(str(val).encode()).decode()

        parts = ["base64=1"]

        # Preserve the PVE-assigned UUID
        existing_uuid = self._get_current_smbios1_uuid()
        if existing_uuid:
            parts.append(f"uuid={existing_uuid}")

        fields = {
            "manufacturer": b64(self.settings.project_title),
            "product": b64(f"name={self.kvs_vm.name}"),
            "version": b64(f"template_id={self.kvs_vm.template}"),
            "serial": b64(f"vm_id={self.kvs_vm.id}"),
            "sku": b64("null"),
            "family": b64(f"event_slug={family}"),
        }

        parts.extend(f"{k}={v}" for k, v in fields.items())
        return ",".join(parts)

    def _pve_update(self):
        try:
            if self.kvs_vm.cpu % 2 == 0:
                pve_cores = int(self.kvs_vm.cpu / 2)
            else:
                pve_cores = self.kvs_vm.cpu
            kwargs = {
                "name": self.kvs_vm.name,
                "cores": pve_cores,
                "memory": self.kvs_vm.ram,
                "description": self.kvs_vm.description,
                "agent": "1",
            }
            if self.settings.pve_vms_smbios_metadata:
                kwargs["smbios1"] = self._build_smbios1_string()
            self.proxmox.nodes(
                ProxmoxCluster().pve_get_node(self.kvs_vm.proxmoxId)
            ).qemu(self.kvs_vm.proxmoxId).config.put(**kwargs)
        except Exception as exc:
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"vm_update operation failed for {self.kvs_vm.name}",
            )
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    def _pve_tags_update(self, tag_to_remove: str = None):
        try:
            vm_tags = self._merge_pve_and_kvs_tags(
                proxmox_id=self.kvs_vm.proxmoxId,
                kvs_vm_id=self.kvs_vm.id,
                pve_tags_merge=True,
                tag_to_remove=tag_to_remove,
            )
            self.proxmox.nodes(
                ProxmoxCluster().pve_get_node(self.kvs_vm.proxmoxId)
            ).qemu(self.kvs_vm.proxmoxId).config.put(tags=vm_tags)
        except Exception as exc:
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"vm_tags_update operation failed for {self.kvs_vm.name}",
            )
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    def _pve_delete(self):
        if self.kvs_vm.proxmoxId:
            try:
                # Check if VM exists on PVE before trying to delete
                resource_list = self.proxmox.cluster.resources.get()
                exists = any(
                    vm.get("vmid") == self.kvs_vm.proxmoxId
                    for vm in resource_list
                )
                if exists:
                    self.pve_task = (
                        self.proxmox.nodes(
                            ProxmoxCluster().pve_get_node(self.kvs_vm.proxmoxId)
                        )
                        .qemu(self.kvs_vm.proxmoxId)
                        .delete()
                    )
                else:
                    self.pve_task_success = True
            except ResourceException:
                self.pve_task_success = True
                pass
            except Exception as exc:
                self.db.close()
                status, safe_msg = format_pve_exception_for_user(
                    exc,
                    prefix=f"vm_delete operation failed for {self.kvs_vm.name}",
                )
                raise CRUDSubTask(SubTask).worker_process_fail(
                    self.kvs_task_object_id,
                    status,
                    safe_msg,
                )
        else:
            self.pve_task_success = True

    def _kvs_vm_delete(self):
        # Delete VM from database and delete any related changelogs, object_permissions and connection_profiles
        try:
            self.db.delete(self.kvs_vm)
            changelogs = (
                self.db.query(Changelog)
                .filter(
                    Changelog.objectId == self.kvs_vm_id,
                    Changelog.object == "VirtualMachine",
                )
                .all()
            )
            if changelogs:
                for changelog in changelogs:
                    self.db.delete(changelog)
            object_permissions = self.db.query(ObjectPermission).filter(
                ObjectPermission.object_id == self.kvs_vm_id,
                ObjectPermission.object_type == "VirtualMachine",
            )
            if object_permissions:
                for perm in object_permissions:
                    self.db.delete(perm)
            tags = self.db.query(Tag).filter(
                Tag.objectId == self.kvs_vm_id,
                Tag.objectType == "VirtualMachine",
            )
            for tag in tags:
                self.db.delete(tag)
            connection_profiles = (
                self.db.query(GuacamoleConnectionProfile)
                .filter(
                    GuacamoleConnectionProfile.objectType == "VirtualMachine",
                    GuacamoleConnectionProfile.objectId == self.kvs_vm_id,
                )
                .all()
            )
            if connection_profiles:
                for interface in connection_profiles:
                    self.db.delete(interface)
                    # Final check to see if related Guacamole objects have been deleted
                    guacamole = (
                        self.db.query(Guacamole)
                        .filter(Guacamole.connection_profile == interface.id)
                        .all()
                    )
                    if guacamole:
                        from core.guacamole import guacamole_delete

                        for guac in guacamole:
                            try:
                                guacamole_delete(guac.identifier)
                                self.db.delete(guac)
                            except:
                                continue
            self.db.commit()
        except:
            old_status = self.kvs_vm.status
            self.kvs_vm.status = "deleted"
            self.kvs_vm.proxmoxId = None
            self.kvs_vm = self.db.merge(self.kvs_vm)
            self.db.add(self.kvs_vm)
            self.db.commit()
            status_changelog = CRUDChangelog(Changelog)._create_for_changes(
                db=self.db,
                user_id=self.request_user_id,
                object_type="VirtualMachine",
                object_id=self.kvs_vm.id,
                changes=[
                    {
                        "field": "status",
                        "value_old": old_status,
                        "value_new": self.kvs_vm.status,
                    }
                ],
            )
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                424,
                "The VirtualMachine has been deleted from Proxmox but could not be deleted from the database. The VirtualMachine object status has been updated to 'deleted'",
            )

    def _pve_ha_configured(self) -> bool:
        try:
            vm_ha_state = self.proxmox.cluster.ha.resources.get(
                f"vm:{self.kvs_vm.proxmoxId}"
            )
            if vm_ha_state:
                return True
        except ResourceException:
            return False
        except:
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                503,
                "Error retrieving HA status from PVE",
            )

    def _pve_ha_set(
        self,
        ha_state: str = "started",
        ha_max_restart: int = 5,
        ha_max_relocate: int = 5,
    ):
        # Check if HA is already configured
        HA_CONFIGURED = self._pve_ha_configured()
        # PVE API call to add VM to HA
        try:
            if HA_CONFIGURED:
                self.proxmox.cluster.ha.resources(
                    f"vm:{self.kvs_vm.proxmoxId}"
                ).put(
                    state=ha_state,
                    max_restart=ha_max_restart,
                    max_relocate=ha_max_relocate,
                )
            else:
                self.proxmox.cluster.ha.resources.post(
                    sid=f"vm:{self.kvs_vm.proxmoxId}",
                    state=ha_state,
                    max_restart=ha_max_restart,
                    max_relocate=ha_max_relocate,
                )
        except Exception as exc:
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"vm_ha_add operation failed for {self.kvs_vm.name}",
            )
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    def _pve_ha_remove(self):
        try:
            self.proxmox.cluster.ha.resources(self.kvs_vm.proxmoxId).delete()
        except ResourceException:
            self.pve_task_success = True
        except Exception as exc:
            if self._pve_ha_configured():
                status, safe_msg = format_pve_exception_for_user(
                    exc,
                    prefix=f"vm_ha_remove operation failed for {self.kvs_vm.name}",
                )
                return CRUDSubTask(SubTask).worker_process_fail(
                    self.kvs_task_object_id,
                    status,
                    safe_msg,
                )
            else:
                return CRUDSubTask(SubTask).worker_process_success(
                    self.kvs_task_object_id, 200, "VirtualMachine not in PVE HA"
                )

    def _pve_actions_stop(self):
        # PVE API call to stop the VirtualMachine
        try:
            self.pve_task = (
                self.proxmox.nodes(
                    ProxmoxCluster().pve_get_node(self.kvs_vm.proxmoxId)
                )
                .qemu(self.kvs_vm.proxmoxId)
                .status.stop.post()
            )
        except ResourceException:
            self.pve_task_success = True
        except Exception as exc:
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"vm_actions_stop operation failed for {self.kvs_vm.name}",
            )
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    def _pve_actions_start(self):
        # PVE API call to start the VirtualMachine
        try:
            self.pve_task = (
                self.proxmox.nodes(
                    ProxmoxCluster().pve_get_node(self.kvs_vm.proxmoxId)
                )
                .qemu(self.kvs_vm.proxmoxId)
                .status.start.post()
            )
        except Exception as exc:
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"vm_actions_start operation failed for {self.kvs_vm.name}",
            )
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    def _pve_actions_shutdown(self):
        # PVE API call to shut down the VirtualMachine
        try:
            self.pve_task = (
                self.proxmox.nodes(
                    ProxmoxCluster().pve_get_node(self.kvs_vm.proxmoxId)
                )
                .qemu(self.kvs_vm.proxmoxId)
                .status.shutdown.post()
            )
        except Exception as exc:
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"vm_actions_shutdown operation failed for {self.kvs_vm.name}",
            )
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    def _pve_actions_reboot(self):
        # PVE API call to shut down the VirtualMachine
        try:
            self.pve_task = (
                self.proxmox.nodes(
                    ProxmoxCluster().pve_get_node(self.kvs_vm.proxmoxId)
                )
                .qemu(self.kvs_vm.proxmoxId)
                .status.reboot.post()
            )
        except Exception as exc:
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"vm_actions_reboot operation failed for {self.kvs_vm.name}",
            )
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    def _pve_actions_reset(self):
        # PVE API call to shut down the VirtualMachine
        try:
            self.pve_task = (
                self.proxmox.nodes(
                    ProxmoxCluster().pve_get_node(self.kvs_vm.proxmoxId)
                )
                .qemu(self.kvs_vm.proxmoxId)
                .status.reset.post()
            )
        except Exception as exc:
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"vm_actions_reset operation failed for {self.kvs_vm.name}",
            )
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    def _pve_actions_resume(self):
        # PVE API call to shut down the VirtualMachine
        try:
            self.pve_task = (
                self.proxmox.nodes(
                    ProxmoxCluster().pve_get_node(self.kvs_vm.proxmoxId)
                )
                .qemu(self.kvs_vm.proxmoxId)
                .status.resume.post()
            )
        except Exception as exc:
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"vm_actions_resume operation failed for {self.kvs_vm.name}",
            )
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    def _pve_actions_pause(self):
        # PVE API call to shut down the VirtualMachine
        try:
            self.pve_task = (
                self.proxmox.nodes(
                    ProxmoxCluster().pve_get_node(self.kvs_vm.proxmoxId)
                )
                .qemu(self.kvs_vm.proxmoxId)
                .status.suspend.post()
            )
        except Exception as exc:
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"vm_actions_pause operation failed for {self.kvs_vm.name}",
            )
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    def _pve_actions_hibernate(self):
        # PVE API call to shut down the VirtualMachine
        try:
            self.pve_task = (
                self.proxmox.nodes(
                    ProxmoxCluster().pve_get_node(self.kvs_vm.proxmoxId)
                )
                .qemu(self.kvs_vm.proxmoxId)
                .status.suspend.post(todisk=1)
            )
        except Exception as exc:
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"vm_actions_hibernate operation failed for {self.kvs_vm.name}",
            )
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    def _pve_actions_migrate(self, target_node: str):
        vm_status = self._pve_status_get(self.kvs_vm.proxmoxId)
        # PVE API call to migrate the VirtualMachine
        try:
            current_node = ProxmoxCluster().pve_get_node(self.kvs_vm.proxmoxId)
            if vm_status == "running":
                self.pve_task = (
                    self.proxmox.nodes(current_node)
                    .qemu(self.kvs_vm.proxmoxId)
                    .migrate.post(target=target_node, online=1)
                )
            else:
                self.pve_task = (
                    self.proxmox.nodes(current_node)
                    .qemu(self.kvs_vm.proxmoxId)
                    .migrate.post(target=target_node)
                )
        except Exception as exc:
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"vm_actions_migrate operation failed for {self.kvs_vm.name}",
            )
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    def _pve_ci_update(self, new_ip: str):
        try:
            self.proxmox.nodes(
                ProxmoxCluster().pve_get_node(self.kvs_vm.proxmoxId)
            ).qemu(self.kvs_vm.proxmoxId).config.set(
                ciuser=self.settings.pve_vms_ciuser,
                cipassword=self.settings.pve_vms_cipassword,
                searchdomain=self.settings.pve_vms_dns_domain,
                nameserver=self.settings.pve_vms_dns_server,
                ciupgrade=1 if self.settings.pve_vms_ciupgrade else 0,
                ipconfig0=f"ip={new_ip}{settings.pve_vms_subnet},gw={settings.pve_vms_gateway}",
            )

        except Exception as exc:
            self.db.close()
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"vm_cloudinit_update operation failed for {self.kvs_vm.name}",
            )
            raise CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    def _pve_ci_add(self):
        try:
            self.proxmox.nodes(
                ProxmoxCluster().pve_get_node(self.kvs_vm.proxmoxId)
            ).qemu(self.kvs_vm.proxmoxId).cloudinit.put()
        except Exception as exc:
            self.db.close()
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"vm_cloudinit_add operation failed for {self.kvs_vm.name}",
            )
            raise CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

    def _pve_ci_drive_attach(self):
        try:
            self.proxmox.nodes(
                ProxmoxCluster().pve_get_node(self.kvs_vm.proxmoxId)
            ).qemu(self.kvs_vm.proxmoxId).config.put(
                scsi30=f"{self.settings.pve_ci_drive}:cloudinit"
            )
        except ResourceException as e:
            if "cloud-init drive is already attached" in str(e):
                pass
            else:
                self.db.close()
                raise CRUDSubTask(SubTask).worker_process_fail(
                    self.kvs_task_object_id,
                    500,
                    "An unknown ResourceException was encountered",
                )
        except:
            self.db.close()
            raise CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id, 503, "Failed to attach cloudinit drive"
            )

    def _pve_ipv4_get(self):
        try:
            VM_RUNNING = False
            while not VM_RUNNING:
                vm_current_status = (
                    self.proxmox.nodes(
                        ProxmoxCluster().pve_get_node(self.kvs_vm.proxmoxId)
                    )
                    .qemu(self.kvs_vm.proxmoxId)
                    .status.current.get()["status"]
                )
                if vm_current_status == "running":
                    VM_RUNNING = True
                time.sleep(5)
            time.sleep(5)
        except Exception as exc:
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"vm_status_get operation failed for {self.kvs_vm.name}",
            )
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

        # PVE API call to get VirtualMachine network interfaces
        try:
            vm_interfaces = self.proxmox(
                f"/nodes/{ProxmoxCluster().pve_get_node(self.kvs_vm.proxmoxId)}/qemu/{self.kvs_vm.proxmoxId}/agent/network-get-interfaces"
            ).get()
            vm_interfaces = vm_interfaces["result"]

        except Exception as exc:
            status, safe_msg = format_pve_exception_for_user(
                exc,
                prefix=f"vm_ipv4_get operation failed for {self.kvs_vm.name}",
            )
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                status,
                safe_msg,
            )

        # Check if an IP from one of the Network Adapters is in the VirtualMachine subnet
        try:
            VIRTUAL_MACHINE_ON_SUBNET = vm_ip_in_subnet(vm_interfaces)
        except:
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                500,
                "Unable to process VirtualMachine network interfaces",
            )
        # Refresh VM object to get latest DB state (avoids MariaDB error
        # 1020 if another worker modified the row during the polling loop)
        self.db.refresh(self.kvs_vm)
        # Set VM status to running if not already set
        if self.kvs_vm.status != "running" and VM_RUNNING:
            old_status = self.kvs_vm.status
            self.kvs_vm.status = "running"
            db_save(self.db, self.kvs_vm)
            CRUDChangelog(Changelog)._create_for_changes(
                db=self.db,
                user_id=self.request_user_id,
                object_type="VirtualMachine",
                object_id=self.kvs_vm.id,
                changes=[
                    {
                        "field": "status",
                        "value_old": old_status,
                        "value_new": self.kvs_vm.status,
                    }
                ],
            )
        if not VIRTUAL_MACHINE_ON_SUBNET:
            self.db.refresh(self.kvs_vm)
            if self.kvs_vm.ipv4 != "0.0.0.0":
                self.kvs_vm.ipv4 = "0.0.0.0"
                db_save(self.db, self.kvs_vm)
            CRUDSubTask(SubTask).worker_process_success(
                self.kvs_task_object_id,
                200,
                f"VirtualMachine is not in PVE VirtualMachine Subnet {self.settings.pve_vm_subnet}",
            )

        else:
            self.db.refresh(self.kvs_vm)
            if self.kvs_vm.ipv4 != VIRTUAL_MACHINE_ON_SUBNET:
                self.kvs_vm.ipv4 = VIRTUAL_MACHINE_ON_SUBNET
                db_save(self.db, self.kvs_vm)
            CRUDSubTask(SubTask).worker_process_success(
                self.kvs_task_object_id,
                200,
                f"VirtualMachine IPv4 {self.kvs_vm.ipv4} has been saved to the database!",
            )

    # Callable worker tasks
    async def create_from_template(self):
        """
        Clone PVE Template into a VirtualMachine
        """
        self._start_process()
        self.target_node = self.pve_connection.get_free_node()
        self._get_vm_and_template_objects()
        self._pve_vm_init()
        if not self.pve_task_success:
            self._pve_clone_template()
            await self._check_task_status()
        if self.pve_task_success:
            old_status = self.kvs_vm.status
            self.kvs_vm.status = "stopped"
            self.kvs_vm = self.db.merge(self.kvs_vm)
            self.db.add(self.kvs_vm)
            self.db.commit()
            status_changelog = CRUDChangelog(Changelog)._create_for_changes(
                db=self.db,
                user_id=self.request_user_id,
                object_type="VirtualMachine",
                object_id=self.kvs_vm.id,
                changes=[
                    {
                        "field": "status",
                        "value_old": old_status,
                        "value_new": self.kvs_vm.status,
                    }
                ],
            )
            self.db.close()
            CRUDSubTask(SubTask).worker_process_success(
                self.kvs_task_object_id,
                201,
                "VirtualMachine creation successful!",
            )

    async def create_from_vm(self, source_vm_id: UUID4):
        """
        Clone PVE VirtualMachine into a VirtualMachine
        """
        self.source_vm_id = source_vm_id
        self._start_process()
        self.target_node = self.pve_connection.get_free_node()
        self._get_vm_and_template_objects()
        self._pve_vm_init()
        self._pve_clone_vm()
        await self._check_task_status()
        if self.pve_task_success:
            old_status = self.kvs_vm.status
            self.kvs_vm.status = "stopped"
            self.kvs_vm = self.db.merge(self.kvs_vm)
            self.db.add(self.kvs_vm)
            self.db.commit()
            status_changelog = CRUDChangelog(Changelog)._create_for_changes(
                db=self.db,
                user_id=self.request_user_id,
                object_type="VirtualMachine",
                object_id=self.kvs_vm.id,
                changes=[
                    {
                        "field": "status",
                        "value_old": old_status,
                        "value_new": self.kvs_vm.status,
                    }
                ],
            )
            self.db.close()
            CRUDSubTask(SubTask).worker_process_success(
                self.kvs_task_object_id,
                201,
                "VirtualMachine creation successful!",
            )

    async def create_from_vm_without_db(self):
        """
        Clone PVE VirtualMachine into a VirtualMachine without creating a new VirtualMachine object in the database (Used when creating a Template based on a VirtualMachine)
        """
        self.source_vm_id = self.kvs_vm_id
        self._start_process()
        self.target_node = self.pve_connection.get_free_node()
        self._get_vm_and_template_objects()
        self.new_vmid = self.pve_connection.next_vm_id(db=self.db)
        self._pve_clone_vm()
        await self._check_task_status()
        if self.pve_task_success:
            vm_config = (
                self.proxmox.nodes(self.target_node)
                .qemu(self.new_vmid)
                .config.get()
            )
            vm_config["vmid"] = self.new_vmid
            CRUDSubTask(SubTask).worker_process_success(
                self.kvs_task_object_id,
                201,
                "VirtualMachine creation successful!",
            )
            self.db.close()
            return vm_config

    async def update(self):
        """
        Update PVE VirtualMachine
        """
        self._start_process()
        self._get_vm_and_template_objects()
        pve_vm_config_before = self._pve_config_get(self.kvs_vm.proxmoxId)
        self._pve_update()
        # Check if CPU or RAM was updated and if so, set VirtualMachine.status to "Changes pending reboot" and then log success
        if self.kvs_vm.cpu != pve_vm_config_before["cores"] or (
            self.kvs_vm.ram != pve_vm_config_before["memory"]
            and self.kvs_vm.status != "stopped"
        ):
            if self.kvs_vm.status == "running":
                self.kvs_vm.status = "changes pending reboot"
                status_changelog = CRUDChangelog(Changelog)._create_for_changes(
                    db=self.db,
                    user_id=self.request_user_id,
                    object_type="VirtualMachine",
                    object_id=self.kvs_vm.id,
                    changes=[
                        {
                            "field": "status",
                            "value_old": "running",
                            "value_new": self.kvs_vm.status,
                        }
                    ],
                )
            self.kvs_vm = self.db.merge(self.kvs_vm)
            self.db.add(self.kvs_vm)
            self.db.commit()
            self.db.refresh(self.kvs_vm)
        self.db.close()
        CRUDSubTask(SubTask).worker_process_success(
            self.kvs_task_object_id, 200, "VirtualMachine update successful!"
        )

    async def update_tags(self, tag_to_remove: str = False):
        """
        Update tags for PVE VirtualMachine
        """
        self._start_process()
        self._get_vm_and_template_objects()
        self._pve_tags_update(tag_to_remove=tag_to_remove)
        self.db.close()
        CRUDSubTask(SubTask).worker_process_success(
            self.kvs_task_object_id,
            200,
            "VirtualMachine tags updated successfully!",
        )

    async def delete(self):
        self._start_process()
        self._get_vm_and_template_objects()
        is_protected = self.kvs_vm.prevent_delete
        pve_protected = False
        if not is_protected and self.kvs_vm.proxmoxId:
            try:
                pve_config = (
                    self.proxmox.nodes(
                        ProxmoxCluster().pve_get_node(self.kvs_vm.proxmoxId)
                    )
                    .qemu(self.kvs_vm.proxmoxId)
                    .config.get()
                )
                if pve_config.get("protection") == 1:
                    self.kvs_vm.prevent_delete = True
                    db_save(self.db, self.kvs_vm)
                    is_protected = True
                    pve_protected = True
            except ResourceException:
                # VM not found on PVE (e.g. 404, 501) — assume not protected, proceed with deletion
                pass
        if is_protected:
            self.db.close()
            source = "Proxmox VE" if pve_protected else "the database"
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                403,
                f"This VirtualMachine may not be deleted. It is protected on {source}.",
            )
        self._pve_delete()
        if not self.pve_task_success:
            await self._check_task_status()
        if self.pve_task_success:
            self._kvs_vm_delete()
            self.db.close()
            CRUDSubTask(SubTask).worker_process_success(
                self.kvs_task_object_id,
                200,
                "VirtualMachine deletion successful!",
            )
        else:
            self.db.close()
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                503,
                "PVE VirtualMachine deletion failed",
            )

    async def ha_set(
        self,
        ha_state: str = "started",
        ha_max_restart: int = 5,
        ha_max_relocate: int = 5,
    ):
        """
        :param ha_state: Requested resource state. The CRM reads this state and acts accordingly
        :param ha_max_restart: Maximal number of tries to restart the service on a node after its start failed
        :param ha_max_relocate: Maximal number of service relocate tries when a service failes to start
        This function is used by the RQ Worker to add the specified VM to HA on Proxmox
        """
        self._start_process()
        self._get_vm_and_template_objects()
        self._pve_ha_set(
            ha_state=ha_state,
            ha_max_restart=ha_max_restart,
            ha_max_relocate=ha_max_relocate,
        )
        # Verify that VM has been added to HA and update Task object with Success status
        if self._pve_ha_configured():
            self.db.close()
            CRUDSubTask(SubTask).worker_process_success(
                self.kvs_task_object_id,
                200,
                "VirtualMachine successfully added to HA!",
            )
        else:
            self.db.close()
            return CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id, 500, "PVE HA configuration failed"
            )

    async def ha_remove(self):
        """ """
        self._start_process()
        self._get_vm_and_template_objects()
        self._pve_ha_remove()
        # Check if VM is still in HA
        attempt = 0
        while not self.pve_task_success:
            try:
                ha_state = self.proxmox.cluster.ha.resources(
                    self.kvs_vm.proxmoxId
                ).get()
                if ha_state:
                    attempt += 1
                    if attempt > 10:
                        self.db.close()
                        return CRUDSubTask(SubTask).worker_process_fail(
                            self.kvs_task_object_id,
                            503,
                            "Request to PVE failed",
                        )
                    time.sleep(
                        self.settings.pve_api_poll_rate
                    )  # Restart loop after sleeping for duration set in .env (in seconds)
            except ResourceException:
                self.pve_task_success = True

        self.db.close()
        CRUDSubTask(SubTask).worker_process_success(
            self.kvs_task_object_id,
            200,
            "VirtualMachine successfully removed from HA!",
        )

    async def actions_stop(self):
        self._start_process()
        self._get_vm_and_template_objects()
        self._pve_actions_stop()
        await self._check_task_status()
        if self.pve_task_success:
            try:
                old_status = self.kvs_vm.status
                self.kvs_vm.status = "stopped"
                self.kvs_vm = self.db.merge(self.kvs_vm)
                self.db.add(self.kvs_vm)
                self.db.commit()
                status_changelog = CRUDChangelog(Changelog)._create_for_changes(
                    db=self.db,
                    user_id=self.request_user_id,
                    object_type="VirtualMachine",
                    object_id=self.kvs_vm.id,
                    changes=[
                        {
                            "field": "status",
                            "value_old": old_status,
                            "value_new": self.kvs_vm.status,
                        }
                    ],
                )
                self.db.close()
                CRUDSubTask(SubTask).worker_process_success(
                    self.kvs_task_object_id,
                    200,
                    "VirtualMachine has been stopped!",
                )
            except:
                self.db.close()
                raise CRUDSubTask(SubTask).worker_process_success(
                    self.kvs_task_object_id,
                    200,
                    "VirtualMachine action was successful however the new status 'stopped' could not be set.",
                )

    async def actions_start(self):
        self._start_process()
        self._get_vm_and_template_objects()
        self._pve_actions_start()
        await self._check_task_status()
        if self.pve_task_success:
            try:
                old_status = self.kvs_vm.status
                self.kvs_vm.status = "running"
                self.kvs_vm = self.db.merge(self.kvs_vm)
                self.db.add(self.kvs_vm)
                self.db.commit()
                status_changelog = CRUDChangelog(Changelog)._create_for_changes(
                    db=self.db,
                    user_id=self.request_user_id,
                    object_type="VirtualMachine",
                    object_id=self.kvs_vm.id,
                    changes=[
                        {
                            "field": "status",
                            "value_old": old_status,
                            "value_new": self.kvs_vm.status,
                        }
                    ],
                )
                self.db.close()
                CRUDSubTask(SubTask).worker_process_success(
                    self.kvs_task_object_id,
                    200,
                    "VirtualMachine has been started!",
                )

            except:
                self.db.close()
                raise CRUDSubTask(SubTask).worker_process_success(
                    self.kvs_task_object_id,
                    200,
                    "VirtualMachine action was successful however the new status 'running' could not be set.",
                )

    async def actions_shutdown(self):
        self._start_process()
        self._get_vm_and_template_objects()
        self._pve_actions_shutdown()
        await self._check_task_status()
        if self.pve_task_success:
            try:
                old_status = self.kvs_vm.status
                self.kvs_vm.status = "stopped"
                self.kvs_vm = self.db.merge(self.kvs_vm)
                self.db.add(self.kvs_vm)
                self.db.commit()
                status_changelog = CRUDChangelog(Changelog)._create_for_changes(
                    db=self.db,
                    user_id=self.request_user_id,
                    object_type="VirtualMachine",
                    object_id=self.kvs_vm.id,
                    changes=[
                        {
                            "field": "status",
                            "value_old": old_status,
                            "value_new": self.kvs_vm.status,
                        }
                    ],
                )
                self.db.close()
                CRUDSubTask(SubTask).worker_process_success(
                    self.kvs_task_object_id,
                    200,
                    "VirtualMachine has been shut down!",
                )

            except:
                self.db.close()
                raise CRUDSubTask(SubTask).worker_process_success(
                    self.kvs_task_object_id,
                    200,
                    "VirtualMachine action was successful however the new status 'stopped' could not be set.",
                )

    async def actions_reboot(self):
        self._start_process()
        self._get_vm_and_template_objects()
        self._pve_actions_reboot()
        await self._check_task_status()
        if self.pve_task_success:
            try:
                old_status = self.kvs_vm.status
                self.kvs_vm.status = "running"
                self.kvs_vm = self.db.merge(self.kvs_vm)
                self.db.add(self.kvs_vm)
                self.db.commit()
                status_changelog = CRUDChangelog(Changelog)._create_for_changes(
                    db=self.db,
                    user_id=self.request_user_id,
                    object_type="VirtualMachine",
                    object_id=self.kvs_vm.id,
                    changes=[
                        {
                            "field": "status",
                            "value_old": old_status,
                            "value_new": self.kvs_vm.status,
                        }
                    ],
                )
                self.db.close()
                CRUDSubTask(SubTask).worker_process_success(
                    self.kvs_task_object_id, 200, "VirtualMachine has rebooted!"
                )

            except:
                self.db.close()
                raise CRUDSubTask(SubTask).worker_process_success(
                    self.kvs_task_object_id,
                    200,
                    "VirtualMachine action was successful however the new status 'running' could not be set.",
                )

    async def actions_reset(self):
        self._start_process()
        self._get_vm_and_template_objects()
        self._pve_actions_reset()
        await self._check_task_status()
        if self.pve_task_success:
            try:
                old_status = self.kvs_vm.status
                self.kvs_vm.status = "running"
                self.kvs_vm = self.db.merge(self.kvs_vm)
                self.db.add(self.kvs_vm)
                self.db.commit()
                status_changelog = CRUDChangelog(Changelog)._create_for_changes(
                    db=self.db,
                    user_id=self.request_user_id,
                    object_type="VirtualMachine",
                    object_id=self.kvs_vm.id,
                    changes=[
                        {
                            "field": "status",
                            "value_old": old_status,
                            "value_new": self.kvs_vm.status,
                        }
                    ],
                )
                self.db.close()
                CRUDSubTask(SubTask).worker_process_success(
                    self.kvs_task_object_id, 200, "VirtualMachine has reset!"
                )

            except:
                self.db.close()
                raise CRUDSubTask(SubTask).worker_process_success(
                    self.kvs_task_object_id,
                    200,
                    "VirtualMachine action was successful however the new status 'running' could not be set.",
                )

    async def actions_resume(self):
        self._start_process()
        self._get_vm_and_template_objects()
        self._pve_actions_resume()
        await self._check_task_status()
        if self.pve_task_success:
            try:
                old_status = self.kvs_vm.status
                self.kvs_vm.status = "running"
                self.kvs_vm = self.db.merge(self.kvs_vm)
                self.db.add(self.kvs_vm)
                self.db.commit()
                status_changelog = CRUDChangelog(Changelog)._create_for_changes(
                    db=self.db,
                    user_id=self.request_user_id,
                    object_type="VirtualMachine",
                    object_id=self.kvs_vm.id,
                    changes=[
                        {
                            "field": "status",
                            "value_old": old_status,
                            "value_new": self.kvs_vm.status,
                        }
                    ],
                )
                self.db.close()
                CRUDSubTask(SubTask).worker_process_success(
                    self.kvs_task_object_id, 200, "VirtualMachine has resumed!"
                )

            except:
                self.db.close()
                raise CRUDSubTask(SubTask).worker_process_success(
                    self.kvs_task_object_id,
                    200,
                    "VirtualMachine action was successful however the new status 'stopped' could not be set.",
                )

    async def actions_pause(self):
        self._start_process()
        self._get_vm_and_template_objects()
        self._pve_actions_pause()
        await self._check_task_status()
        if self.pve_task_success:
            try:
                old_status = self.kvs_vm.status
                self.kvs_vm.status = "paused"
                self.kvs_vm = self.db.merge(self.kvs_vm)
                self.db.add(self.kvs_vm)
                self.db.commit()
                status_changelog = CRUDChangelog(Changelog)._create_for_changes(
                    db=self.db,
                    user_id=self.request_user_id,
                    object_type="VirtualMachine",
                    object_id=self.kvs_vm.id,
                    changes=[
                        {
                            "field": "status",
                            "value_old": old_status,
                            "value_new": self.kvs_vm.status,
                        }
                    ],
                )
                self.db.close()
                CRUDSubTask(SubTask).worker_process_success(
                    self.kvs_task_object_id, 200, "VirtualMachine has paused!"
                )

            except:
                self.db.close()
                raise CRUDSubTask(SubTask).worker_process_success(
                    self.kvs_task_object_id,
                    200,
                    "VirtualMachine action was successful however the new status 'paused' could not be set.",
                )

    async def actions_hibernate(self):
        self._start_process()
        self._get_vm_and_template_objects()
        self._pve_actions_hibernate()
        await self._check_task_status()
        if self.pve_task_success:
            try:
                old_status = self.kvs_vm.status
                self.kvs_vm.status = "hibernated"
                self.kvs_vm = self.db.merge(self.kvs_vm)
                self.db.add(self.kvs_vm)
                self.db.commit()
                status_changelog = CRUDChangelog(Changelog)._create_for_changes(
                    db=self.db,
                    user_id=self.request_user_id,
                    object_type="VirtualMachine",
                    object_id=self.kvs_vm.id,
                    changes=[
                        {
                            "field": "status",
                            "value_old": old_status,
                            "value_new": self.kvs_vm.status,
                        }
                    ],
                )
                self.db.close()
                CRUDSubTask(SubTask).worker_process_success(
                    self.kvs_task_object_id,
                    200,
                    "VirtualMachine has hibernated!",
                )
            except:
                self.db.close()
                raise CRUDSubTask(SubTask).worker_process_success(
                    self.kvs_task_object_id,
                    200,
                    "VirtualMachine action was successful however the new status 'hibernated' could not be set.",
                )

    async def actions_migrate(self, target_node: str):
        self._start_process()
        self._get_vm_and_template_objects()
        await proxmox_node_info_periodic()
        if self.kvs_vm.proxmoxNode == self.target_node:
            self.db.close()
            return CRUDSubTask(SubTask).worker_process_success(
                self.kvs_task_object_id,
                200,
                f"VirtualMachine is already on node: {self.kvs_vm.proxmoxNode}",
            )
        self._pve_actions_migrate(target_node=target_node)
        await self._check_task_status()
        if self.pve_task_success:
            self.db.close()
            CRUDSubTask(SubTask).worker_process_success(
                self.kvs_task_object_id,
                200,
                "VirtualMachine has been migrated successfully!",
            )

    async def ipv4_get(self):
        self._start_process()
        self._get_vm_and_template_objects()
        self._pve_ipv4_get()
        await proxmox_node_info_periodic()
        self.db.close()
        CRUDSubTask(SubTask).worker_process_success(
            self.kvs_task_object_id,
            200,
            f"VirtualMachine IPv4 {self.kvs_vm.ipv4} has been saved to the database!",
        )

    async def ipv4_set(self):
        self._start_process()
        self._get_vm_and_template_objects()
        new_ip = self._get_next_available_ip()
        self._pve_ci_update(str(new_ip))
        self._pve_ci_add()
        self._pve_ci_drive_attach()
        try:
            self.kvs_vm.ipv4 = str(new_ip)
            self.kvs_vm = self.db.merge(self.kvs_vm)
            self.db.add(self.kvs_vm)
            self.db.commit()
            self.db.close()
            CRUDSubTask(SubTask).worker_process_success(
                self.kvs_task_object_id,
                200,
                f"VirtualMachine IPv4 {self.kvs_vm.ipv4} has been saved to the database!",
            )
        except:
            self.db.close()
            raise CRUDSubTask(SubTask).worker_process_fail(
                self.kvs_task_object_id,
                424,
                f"Cloudinit drive was successfully attached but there was an error updating VirtualMachine with new ipv4: {new_ip!s}",
            )
