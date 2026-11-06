import os

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from proxmoxer.core import ResourceException
from sqlalchemy.orm import Session
from starlette.background import BackgroundTasks

from core import dependencies
from core.config import Settings
from core.exceptions import (
    BadRequestError,
    PermissionDenied,
    ProxmoxConnectionError,
)
from core.responses import BASE_RESPONSES, HTTP_400, build_description
from middlewares.i18n import _
from models import Template
from pve.cluster import ProxmoxCluster
from schemas.proxmox import (
    ProxmoxNodeMetricsList,
    ProxmoxRRDConsolidation,
    ProxmoxRRDDataSource,
    ProxmoxRRDTimeframe,
)

router = APIRouter(
    prefix="/proxmox",
    tags=["proxmox"],
    responses=BASE_RESPONSES,
)


# Returns cluster logs
@router.get(
    "/cluster/logs",
    status_code=200,
    operation_id="cluster_logs_read_all",
    summary="Get PVE cluster logs",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns the task log from the Proxmox cluster.",
        permission="proxmox_read",
    ),
)
def get_cluster_logs(
    request: Request, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "proxmox_read", request, db=db
    ).has_permission():
        # PVE connection
        try:
            proxmox = ProxmoxCluster().proxmox
        except:
            raise ProxmoxConnectionError()
        # Get cluster logs
        cluster_logs = proxmox.cluster.log.get()
        return cluster_logs
    else:
        raise PermissionDenied()


# Returns cluster resources
@router.get(
    "/cluster/resources",
    status_code=200,
    operation_id="cluster_resources_read_all",
    summary="Get PVE cluster resources",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns all resources currently tracked by the Proxmox cluster.",
        permission="proxmox_read",
    ),
)
def get_cluster_resources(
    request: Request, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "proxmox_read", request, db=db
    ).has_permission():
        # PVE connection
        try:
            proxmox = ProxmoxCluster().proxmox
        except:
            raise ProxmoxConnectionError()
        # Get cluster resources
        cluster_resources = proxmox.cluster.resources.get()
        return cluster_resources
    else:
        raise PermissionDenied()


# Returns cluster status
@router.get(
    "/cluster/status",
    status_code=200,
    operation_id="cluster_status_read",
    summary="Get PVE cluster status",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns the current status of the Proxmox cluster.",
        permission="proxmox_read",
    ),
)
def get_cluster_status(
    request: Request, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "proxmox_read", request, db=db
    ).has_permission():
        # PVE connection
        try:
            proxmox = ProxmoxCluster().proxmox
        except:
            raise ProxmoxConnectionError()
        # Get cluster status
        cluster_status = proxmox.cluster.status.get()
        return cluster_status
    else:
        raise PermissionDenied()


# Returns cluster tasks
@router.get(
    "/cluster/tasks",
    status_code=200,
    operation_id="cluster_tasks_read_all",
    summary="Get PVE cluster tasks",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns active and recent tasks from the Proxmox cluster.",
        permission="proxmox_read",
    ),
)
def get_cluster_tasks(
    request: Request, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "proxmox_read", request, db=db
    ).has_permission():
        # PVE connection
        try:
            proxmox = ProxmoxCluster().proxmox
        except:
            raise ProxmoxConnectionError()
        # Get cluster tasks
        cluster_tasks = proxmox.cluster.tasks.get()
        return cluster_tasks
    else:
        raise PermissionDenied()


# Returns cluster counts
@router.get(
    "/cluster/counts",
    status_code=200,
    operation_id="cluster_counts_read_all",
    summary="Get PVE cluster counts",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns VM counts by status (total, running, stopped) from the Proxmox cluster.",
        permission="proxmox_read",
    ),
)
def get_cluster_counts(
    request: Request, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "proxmox_read", request, db=db
    ).has_permission():
        # PVE connection
        try:
            proxmox = ProxmoxCluster().proxmox
        except:
            raise ProxmoxConnectionError()
        # Get cluster resources
        cluster_resources = proxmox.cluster.resources.get()
        # Create lists
        vm_list_all = []
        vm_list_running = []
        vm_list_stopped = []
        # Iterate through resource list to add each VM to list based on status
        for resource in cluster_resources:
            if "vmid" in resource:
                vm_list_all.append(resource)
                if resource["status"] == "running":
                    vm_list_running.append(resource)
                elif resource["status"] == "stopped":
                    vm_list_stopped.append(resource)
        # Create response based on lists created above
        vm_counts = {
            "vms_total": len(vm_list_all),
            "vms_running": len(vm_list_running),
            "vms_stopped": len(vm_list_stopped),
        }
        return vm_counts
    else:
        raise PermissionDenied()


# Returns all nodes on cluster
@router.get(
    "/nodes",
    status_code=200,
    operation_id="nodes_read_all",
    summary="Get list of nodes on cluster",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns the list of nodes in the Proxmox cluster with their status, IP, and FQDN.",
        permission="proxmox_read",
    ),
)
def get_nodes_all(request: Request, db: Session = Depends(dependencies.get_db)):
    if dependencies.PermissionChecker(
        "proxmox_read", request, db=db
    ).has_permission():
        # PVE connection
        try:
            proxmox = ProxmoxCluster().proxmox
        except:
            raise ProxmoxConnectionError()
        settings = Settings()
        # Get cluster tasks
        cluster_status = proxmox.cluster.status.get()
        nodes_list = []
        for item in cluster_status:
            if item["type"] == "cluster":
                continue
            node_data = {
                "name": item["name"],
                "online": item["online"],
                "ip": item["ip"],
                "node_id": item["nodeid"],
                "fqdn": str(item["name"]) + "." + settings.pve_fqdn,
            }
            nodes_list.append(node_data)
        return nodes_list
    else:
        raise PermissionDenied()


# Returns node rrd graphic
@router.get(
    "/nodes/{node}/rrd",
    status_code=200,
    operation_id="nodes_rrd_read",
    responses={**HTTP_400},
    summary="Read node RRD statistics (returns PNG)",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns an RRD statistic graph as a PNG image for a Proxmox node.",
        permission="proxmox_read",
    ),
)
def get_node_rrd(
    node: str,
    background_tasks: BackgroundTasks,
    request: Request,
    datasource: ProxmoxRRDDataSource = ProxmoxRRDDataSource.CPU,
    timeframe: ProxmoxRRDTimeframe = ProxmoxRRDTimeframe.HOUR,
    cf: ProxmoxRRDConsolidation = ProxmoxRRDConsolidation.AVERAGE,
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "proxmox_read", request, db=db
    ).has_permission():
        # PVE connection
        try:
            proxmox = ProxmoxCluster().proxmox
        except:
            raise ProxmoxConnectionError()

        try:
            # Get node rrd
            node_rrd = proxmox.nodes(node).rrd.get(
                cf=cf, ds=datasource, timeframe=timeframe
            )
        except ResourceException:
            raise BadRequestError(
                message=_(
                    "Either the consolidation function or datasource or timeframe entered is invalid."
                )
            )

        file_path = f"./tmp/{node}_{datasource}_{timeframe}.png"

        # Save image
        with open(file_path, "wb") as f:
            f.write(node_rrd["image"].encode("raw_unicode_escape"))

        # Create background task to delete image after return
        def delete_file(path: str):
            os.remove(path)

        background_tasks.add_task(delete_file, file_path)

        return FileResponse(file_path)
    else:
        raise PermissionDenied()


# Returns node rrd data
@router.get(
    "/nodes/{node}/rrddata",
    status_code=200,
    operation_id="nodes_rrddata_read",
    responses={**HTTP_400},
    summary="Read node RRD statistic data",
    response_model=ProxmoxNodeMetricsList,
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns RRD metric data for a Proxmox node.",
        permission="proxmox_read",
    ),
)
def get_node_rrddata(
    node: str,
    request: Request,
    timeframe: ProxmoxRRDTimeframe = ProxmoxRRDTimeframe.HOUR,
    cf: ProxmoxRRDConsolidation = ProxmoxRRDConsolidation.AVERAGE,
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "proxmox_read", request, db=db
    ).has_permission():
        try:
            proxmox = ProxmoxCluster().proxmox
        except Exception:
            raise ProxmoxConnectionError()

        try:
            node_rrddata = proxmox.nodes(node).rrddata.get(
                cf=cf.value, timeframe=timeframe.value
            )
        except ResourceException:
            raise BadRequestError(
                message=_(
                    "Either the consolidation function or timeframe entered is invalid."
                )
            )

        return node_rrddata
    else:
        raise PermissionDenied()


# Returns PVE config for proxmox_id
@router.get(
    "/templates/load",
    status_code=200,
    operation_id="template_load_get",
    responses={**HTTP_400},
    summary="Get config for Template on PVE",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Fetches the raw configuration for a PVE template by its Proxmox VM ID.",
        permission="templates_create",
        notes=[
            "The PVE VM must already be configured as a template on Proxmox.",
        ],
    ),
)
def get_template(
    proxmox_id: int,
    request: Request,
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "templates_create", request, db=db
    ).has_permission():
        from controllers.templates import CRUDTemplate

        conf = CRUDTemplate(Template).get_pve_template(db, proxmox_id)
        return conf
    else:
        raise PermissionDenied()


# Creates Template based on proxmox_id of Template on PVE
@router.post(
    "/templates/load",
    status_code=200,
    operation_id="template_load_create",
    responses={**HTTP_400},
    summary="Create Template in DB based on Template on PVE",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Imports a PVE template into the database by reading its configuration from Proxmox.",
        permission="templates_create",
        notes=[
            "The PVE VM must already be configured as a template on Proxmox.",
            "The `proxmoxId` must not already be registered in the database.",
        ],
    ),
)
def create_template(
    proxmox_id: int,
    request: Request,
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "templates_create", request, db=db
    ).has_permission():
        from controllers.templates import CRUDTemplate

        template = CRUDTemplate(Template).load_from_pve(db, request, proxmox_id)
        return template
    else:
        raise PermissionDenied()
