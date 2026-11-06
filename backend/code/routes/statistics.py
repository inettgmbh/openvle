from fastapi import APIRouter, Depends, Request
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from core import dependencies
from core.config import Settings
from core.exceptions import ProxmoxConnectionError
from core.responses import READ_RESPONSES
from models import (
    Course,
    Event,
    EventStatus,
    EventsUser,
    Guacamole,
    ObjectPermission,
    Template,
    User,
    VirtualMachine,
)
from pve.cluster import ProxmoxCluster

settings = Settings()

router = APIRouter(
    prefix="/statistics",
    tags=["statistics"],
    responses=READ_RESPONSES,
)


# Returns cluster logs
@router.get(
    "/dashboard",
    status_code=200,
    operation_id="statistics_dashboard_read",
    summary="Get statistics dashboard based on User permissions",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_statistics_dashboard(
    request: Request, db: Session = Depends(dependencies.get_db)
):
    try:
        user_is_admin = dependencies.PermissionChecker(
            "dashboards_admins", request, db=db
        ).has_permission()
    except:
        user_is_admin = False
    try:
        user_is_advanced = dependencies.PermissionChecker(
            "dashboards_verwaltende", request, db=db
        ).has_permission()
    except:
        user_is_advanced = False
    # Construct dashboard for User
    dashboard_base = {
        "vms": {
            "own_total": db.query(VirtualMachine)
            .join(
                ObjectPermission,
                and_(
                    ObjectPermission.object_type == VirtualMachine.__name__,
                    ObjectPermission.object_id == (VirtualMachine.id),
                    ObjectPermission.entity_id == request.user.id,
                    ObjectPermission.entity_type == "User",
                ),
            )
            .count(),
            "own_running": db.query(VirtualMachine)
            .join(
                ObjectPermission,
                and_(
                    ObjectPermission.object_type == VirtualMachine.__name__,
                    ObjectPermission.object_id == (VirtualMachine.id),
                    ObjectPermission.entity_id == request.user.id,
                    ObjectPermission.entity_type == "User",
                ),
            )
            .filter(VirtualMachine.status == "running")
            .count(),
        },
        "courses": {
            "own_total": db.query(Course)
            .filter(Course.createdById == request.user.id)
            .count()
        },
        "events": {
            "own_total": db.query(EventsUser)
            .filter(EventsUser.user_id == request.user.id)
            .distinct()
            .count(),
            "own_running": db.query(Event)
            .join(EventsUser, Event.id == EventsUser.event_id)
            .join(EventStatus, Event.status == EventStatus.id)
            .filter(EventsUser.user_id == request.user.id)
            .filter(EventStatus.name == "Aktiv")
            .distinct()
            .count(),
        },
        "connections": {
            "own_total": db.query(Guacamole)
            .filter(Guacamole.userId == request.user.id)
            .count(),
        },
    }
    # Include further dashboard attributes if User has dashboards_verwaltende or dashboards_admins permissions
    if user_is_admin or user_is_advanced:
        # users
        dashboard_base["users"] = {
            "all_total": db.query(User).count(),
            "all_active": db.query(User)
            .filter(User.status == "Active")
            .count(),
            "all_locked": db.query(User)
            .filter(User.status != "Active")
            .count(),
        }
        # courses
        dashboard_base["courses"]["all_total"] = db.query(Course).count()
        # events
        dashboard_base["events"]["all_total"] = db.query(Event).count()
        dashboard_base["events"]["all_running"] = (
            db.query(Event)
            .join(EventStatus, Event.status == EventStatus.id)
            .filter(EventStatus.name == "Aktiv")
            .count()
        )
        # connections
        dashboard_base["connections"]["all_total"] = db.query(Guacamole).count()
        # resources
        total_disk_template = db.query(
            func.sum(Template.disk).label("total_disk_template")
        ).one()
        total_resources_vms = db.query(
            func.sum(VirtualMachine.cpu).label("total_cpu"),
            func.sum(VirtualMachine.ram).label("total_ram"),
            func.sum(VirtualMachine.disk).label("total_disk"),
        ).one()
        if (
            total_resources_vms.total_disk
            and total_disk_template.total_disk_template
        ):
            total_resources_disk = (
                total_resources_vms.total_disk
                + total_disk_template.total_disk_template
            )
        elif (
            total_resources_vms.total_disk
            and not total_disk_template.total_disk_template
        ):
            total_resources_disk = total_resources_vms.total_disk
        elif total_disk_template.total_disk_template:
            total_resources_disk = total_disk_template.total_disk_template
        else:
            total_resources_disk = 0
        # Get PVE resource data
        try:
            # Connect to PVE
            proxmox = ProxmoxCluster().proxmox
        except:
            raise ProxmoxConnectionError()
        # Set variables to store resource data
        disk_total = 0
        disk_used = 0
        cpu_total = 0
        cpu_used = 0
        ram_total = 0
        ram_used = 0
        # Get node count
        nodes_list = proxmox.nodes.get()
        node_count = 0
        node_count_online = 0
        node_index = 0
        for node in nodes_list:
            if node["type"] != "node":
                node_index += 1
                continue
            try:
                # Aggregate CPU and RAM information
                cpu_total += node["maxcpu"]
                cpu_used += (
                    node["cpu"] * node["maxcpu"]
                )  # 'cpu' is a ratio of used CPU
                ram_total += node["maxmem"]
                ram_used += node["mem"]
                disk_total += node["maxdisk"]
                disk_used += node["disk"]
                # Store CPU, Ram and storage information
                nodes_list[node_index]["node_status"] = {
                    "cpu_total": node["maxcpu"],
                    "cpu_used": node["cpu"] * node["maxcpu"],
                    "ram_total": node["maxmem"],
                    "ram_used": node["mem"],
                    "storage_total": node["maxdisk"],
                    "storage_used": node["disk"],
                }
            except KeyError:
                # Store CPU, Ram and storage information
                nodes_list[node_index]["node_status"] = {
                    "cpu_total": 0,
                    "cpu_used": 0,
                    "ram_total": 0,
                    "ram_used": 0,
                    "storage_total": 0,
                    "storage_used": 0,
                }
            node_count += 1
            if node["status"] == "online":
                node_count_online += 1
            # Add 1 to node_index
            node_index += 1
        # Convert from bytes to GB
        total_disk_gb = disk_total / (1024**3)
        used_disk_gb = disk_used / (1024**3)
        total_ram_gb = ram_total / (1024**3)
        used_ram_gb = ram_used / (1024**3)
        dashboard_base["resources"] = {
            "cpu": {
                "usable": cpu_total,
                "used": cpu_used,
                "allocated_max": total_resources_vms.total_cpu
                if total_resources_vms.total_cpu
                else 0,
                "unit": "cores",
            },
            "ram": {
                "usable": total_ram_gb,
                "used": used_ram_gb,
                "allocated_max": int(total_resources_vms.total_ram / 1024)
                if total_resources_vms.total_ram
                else 0,
                "unit": "GB",
            },
            "storage": {
                "total": total_disk_gb,
                "used": used_disk_gb,
                "allocated_max": total_resources_disk,
                "unit": "GB",
            },
            "nodes": {"total": node_count, "online": node_count_online},
        }
    # Include all attributes if User has dashboards_admins permission
    if user_is_admin:
        # vms
        dashboard_base["vms"]["all_total"] = db.query(VirtualMachine).count()
        dashboard_base["vms"]["all_running"] = (
            db.query(VirtualMachine)
            .filter(VirtualMachine.status == "running")
            .count()
        )
        dashboard_base["vms"]["all_error"] = (
            db.query(VirtualMachine)
            .filter(VirtualMachine.status == "error")
            .count()
        )
        dashboard_base["nodes"] = {}
        # nodes
        for node in nodes_list:
            if node["type"] != "node":
                node_index += 1
                continue
            # Get KVS VirtualMachine/Template resource data for VirtualMachines/Templates on given node
            template_storage_subquery = (
                db.query(func.sum(Template.disk).label("total_disk_template"))
                .filter(Template.proxmoxNode == node["node"])
                .one()
            )
            total_resources_vms_node = (
                db.query(
                    func.sum(VirtualMachine.cpu).label("total_cpu"),
                    func.sum(VirtualMachine.ram).label("total_ram"),
                    func.sum(VirtualMachine.disk).label("total_disk"),
                )
                .filter(VirtualMachine.proxmoxNode == node["node"])
                .one()
            )
            if (
                total_resources_vms_node.total_disk
                and template_storage_subquery.total_disk_template
            ):
                total_resources_disk = (
                    total_resources_vms_node.total_disk
                    + template_storage_subquery.total_disk_template
                )
            elif (
                total_resources_vms_node.total_disk
                and not template_storage_subquery.total_disk_template
            ):
                total_resources_disk = total_resources_vms_node.total_disk
            elif template_storage_subquery.total_disk_template:
                total_resources_disk = (
                    template_storage_subquery.total_disk_template
                )
            else:
                total_resources_disk = 0
            dashboard_base["nodes"][node["node"]] = {
                "hostname": node["node"],
                "fqdn": str(node["node"]) + "." + settings.pve_fqdn,
                "status": node["status"],
                "resources": {
                    "cpu": {
                        "usable": node["node_status"]["cpu_total"],
                        "used": node["node_status"]["cpu_used"],
                        "allocated_max": total_resources_vms_node.total_cpu
                        if total_resources_vms_node.total_cpu
                        else 0,
                        "unit": "cores",
                    },
                    "ram": {
                        "usable": node["node_status"]["ram_total"] / (1024**3),
                        "used": node["node_status"]["ram_used"] / (1024**3),
                        "allocated_max": int(
                            total_resources_vms_node.total_ram / 1024
                        )
                        if total_resources_vms_node.total_ram
                        else 0,
                        "unit": "GB",
                    },
                    "storage": {
                        "total": node["node_status"]["storage_total"]
                        / (1024**3),
                        "used": node["node_status"]["storage_used"] / (1024**3),
                        "allocated_max": total_resources_disk,
                        "unit": "GB",
                    },
                },
            }
    return dashboard_base
