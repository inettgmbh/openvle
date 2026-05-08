from datetime import datetime, timezone

from controllers.changelog import CRUDChangelog
from core.config import Settings
from core.core_utils import db_save, get_system_user
from core.mariadb import SessionLocal
from core.mongodb import db as mongodb
from models import *
from models import (
    Template as TemplateModel,
    VirtualMachine as VirtualMachineModel,
)

from .cluster import ProxmoxCluster

settings = Settings()

mongodb = mongodb["pve_node_info"]


# Create pve_node_info object in MongoDB. Used in proxmox_node_info_periodic
def create_pve_node_info(vm_list_new, template_list_new, node_list_new):
    nodeInfo = {
        "name": "PVE resource list",
        "qemu_vm_list": vm_list_new,
        "qemu_template_list": template_list_new,
        "node_list": node_list_new,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    mongodb.insert_one(nodeInfo)
    print("Creating new 'PVE resource list' entry")  # TODO: See KVS-372


# Update pve_node_info object in MongoDB. Used in proxmox_node_info_periodic
def update_pve_node_info(
    obj_in: str, vm_list_new: list, template_list_new: list, node_list_new: list
):
    try:
        new_values = {
            "$set": {
                "qemu_vm_list": vm_list_new,
                "qemu_template_list": template_list_new,
                "node_list": node_list_new,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        }
        mongodb.update_one({"name": obj_in}, new_values)
        return
    except:
        return False


# Get pve_node_info object from MongoDB. Used in proxmox_node_info_periodic
def get_pve_node_info(name: str) -> dict:
    item = mongodb.find_one({"name": name})
    if not item:
        return {}  # If the entry does not exist, return false
    return item


# Periodic task to update the DB with new resource data provided by Proxmox
async def proxmox_node_info_periodic():
    from controllers.sub_tasks import CRUDSubTask

    # Set db variable to MariaDB session
    try:
        db = SessionLocal()
    except:
        return "PVE periodic task unable to connect to MariaDB"

    try:
        sub_task = (
            db.query(SubTask)
            .filter(SubTask.job_id == "proxmox_node_info_periodic")
            .first()
        )
        CRUDSubTask(SubTask).worker_process_start(db, sub_task.id)
        # Get NEW proxmox resource list from PVE
        proxmox = ProxmoxCluster().proxmox
        try:
            resource_list_new = proxmox.cluster.resources.get()
        except:
            return CRUDSubTask(SubTask).worker_process_fail(
                sub_task.id,
                500,
                "PVE periodic task unable to retrieve cluster resources list",
            )

        vm_list_new = []
        template_list_new = []
        node_list_new = []
        # Get old resource list from MongoDB
        resource_list_old: dict = get_pve_node_info("PVE resource list")

        # If no entry exists for resource list, save new data to DB and finish.
        for resource in resource_list_new:
            # Add all VirtualMachines and Templates to list
            if "type" not in resource:
                continue
            elif resource["type"] == "qemu":
                if "template" in resource and resource["template"] == 1:
                    template_list_new.append(resource)
                else:
                    vm_list_new.append(resource)
            elif resource["type"] == "node":
                node_list_new.append(resource)

        # Case: No entry exists for "PVE resource list"
        if not resource_list_old:
            create_pve_node_info(vm_list_new, template_list_new, node_list_new)
            CRUDSubTask(SubTask).worker_process_success(
                sub_task.id, 201, "PVE periodic initialisation successful"
            )
            return

        # Check if any VirtualMachines or Templates exist in database. If not, break early
        try:
            vm_list_all = db.query(VirtualMachineModel).all()
            template_list_all = db.query(TemplateModel).all()
            if not vm_list_all and not template_list_all:
                return CRUDSubTask(SubTask).worker_process_success(
                    sub_task.id,
                    200,
                    "No VirtualMachines or Templates found in MariaDB",
                )
        except:
            return CRUDSubTask(SubTask).worker_process_fail(
                sub_task.id,
                400,
                "Unable to retrieve VirtualMachines or Templates from MariaDB",
            )

        # Iterate through VirtualMachines in MariaDB
        if vm_list_all:
            # Build dict for O(1) lookup by proxmoxId
            vm_by_proxmox_id = {
                vm.proxmoxId: vm for vm in vm_list_all if vm.proxmoxId
            }
            # Iterate through VirtualMachines in vm_list_new
            for pve_vm_new in vm_list_new:
                # Get corresponding VirtualMachine from dict
                vm_in_db = vm_by_proxmox_id.get(pve_vm_new["vmid"])

                # CASE: VirtualMachine does not exist on database, Skip
                if not vm_in_db:
                    continue

                # CASE: VirtualMachine is in a transition state, Skip
                if vm_in_db.status in ["starting", "deleting", "stopping"]:
                    continue

                # CASE: VirtualMachine is new
                if vm_in_db.status in ["cloning", "queued"]:
                    if not vm_in_db.ipv4:
                        continue
                    # Update VirtualMachine on DB with current status and node
                    try:
                        db.refresh(vm_in_db)
                        if vm_in_db.status not in ["cloning", "queued"]:
                            continue
                        old_status = vm_in_db.status
                        vm_in_db.status = pve_vm_new["status"]
                        vm_in_db.proxmoxNode = pve_vm_new["node"]
                        db_save(db, vm_in_db)
                        CRUDChangelog(Changelog)._create_for_changes(
                            db=db,
                            user_id=get_system_user().id,
                            object_type="VirtualMachine",
                            object_id=vm_in_db.id,
                            changes=[
                                {
                                    "field": "status",
                                    "value_old": old_status,
                                    "value_new": vm_in_db.status,
                                }
                            ],
                        )
                        continue
                    except Exception:
                        db.rollback()
                        continue

                # CASE: VirtualMachine status has changed
                if pve_vm_new["status"] != vm_in_db.status:
                    # Update VirtualMachine on DB with current status
                    try:
                        db.refresh(vm_in_db)
                        if pve_vm_new["status"] == vm_in_db.status:
                            continue
                        old_status = vm_in_db.status
                        vm_in_db.status = pve_vm_new["status"]
                        db_save(db, vm_in_db)
                        CRUDChangelog(Changelog)._create_for_changes(
                            db=db,
                            user_id=get_system_user().id,
                            object_type="VirtualMachine",
                            object_id=vm_in_db.id,
                            changes=[
                                {
                                    "field": "status",
                                    "value_old": old_status,
                                    "value_new": vm_in_db.status,
                                }
                            ],
                        )
                    except Exception:
                        db.rollback()
                        continue

                # CASE: VirtualMachine node has changed
                if pve_vm_new["node"] != vm_in_db.proxmoxNode:
                    # Update VirtualMachine on DB with current node
                    try:
                        db.refresh(vm_in_db)
                        if pve_vm_new["node"] == vm_in_db.proxmoxNode:
                            continue
                        old_node = vm_in_db.proxmoxNode
                        vm_in_db.proxmoxNode = pve_vm_new["node"]
                        db_save(db, vm_in_db)
                        CRUDChangelog(Changelog)._create_for_changes(
                            db=db,
                            user_id=get_system_user().id,
                            object_type="VirtualMachine",
                            object_id=vm_in_db.id,
                            changes=[
                                {
                                    "field": "proxmoxNode",
                                    "value_old": old_node,
                                    "value_new": vm_in_db.proxmoxNode,
                                }
                            ],
                        )
                    except Exception:
                        db.rollback()
                        continue

        # Iterate through Templates in MariaDB
        if template_list_all:
            # Build dict for O(1) lookup by proxmoxId
            template_by_proxmox_id = {
                t.proxmoxId: t for t in template_list_all if t.proxmoxId
            }
            # Iterate through Templates in template_list_new
            for pve_template_new in template_list_new:
                # Get corresponding Template from dict
                template_in_db = template_by_proxmox_id.get(
                    pve_template_new["vmid"]
                )

                # CASE: Template does not exist on database, Skip
                if not template_in_db:
                    continue

                # CASE: Templates was created (VirtualMachine was converted)
                if template_in_db.status in ["cloning", "queued"]:
                    # Update Template on DB with current node and set status to "available"
                    try:
                        db.refresh(template_in_db)
                        if template_in_db.status not in ["cloning", "queued"]:
                            continue
                        template_in_db.proxmoxNode = pve_template_new["node"]
                        template_in_db.status = "available"
                        db_save(db, template_in_db)
                        continue
                    except Exception:
                        db.rollback()
                        continue

                # CASE: Template node has changed
                if pve_template_new["node"] != template_in_db.proxmoxNode:
                    # Update Template on DB with current node
                    try:
                        db.refresh(template_in_db)
                        if (
                            pve_template_new["node"]
                            == template_in_db.proxmoxNode
                        ):
                            continue
                        old_node = template_in_db.proxmoxNode
                        template_in_db.proxmoxNode = pve_template_new["node"]
                        db_save(db, template_in_db)
                        CRUDChangelog(Changelog)._create_for_changes(
                            db=db,
                            user_id=get_system_user().id,
                            object_type="Template",
                            object_id=template_in_db.id,
                            changes=[
                                {
                                    "field": "proxmoxNode",
                                    "value_old": old_node,
                                    "value_new": template_in_db.proxmoxNode,
                                }
                            ],
                        )
                    except Exception:
                        db.rollback()
                        continue

        # Update resource_list_old with resource_list_new
        update_pve_node_info(
            "PVE resource list", vm_list_new, template_list_new, node_list_new
        )

        return CRUDSubTask(SubTask).worker_process_success(
            sub_task.id, 200, "PVE periodic task successful", db
        )
    finally:
        db.close()
