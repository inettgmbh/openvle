from fastapi import APIRouter, Depends

from controllers.virtual_machines import *
from core import dependencies
from core.exceptions import (
    DuplicateFieldException,
    PermissionDenied,
)
from models import (
    Application as ApplicationModel,
    Guacamole as GuacamoleModel,
    VirtualMachine as VirtualMachineModel,
)
from schemas.apps import ApplicationList
from schemas.guacamole import GuacamoleList
from schemas.proxmox import (
    ProxmoxRRDConsolidation,
    ProxmoxRRDTimeframe,
    ProxmoxVMMetricsList,
)
from schemas.virtual_machines import *

router = APIRouter(
    prefix="/virtual_machines",
    tags=["vms"],
    responses={404: {"detail": "Not found"}},
)


# Create new VirtualMachine
@router.post(
    "/",
    status_code=201,
    response_model=VirtualMachine,
    operation_id="vms_create",
    summary="Create VirtualMachine",
    dependencies=[Depends(dependencies.get_current_user)],
)
def create_virtual_machine(
    *,
    virtual_machine_in: VirtualMachineCreate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "vms_create",
        request,
        db=db,
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).create_from_template(
            db=db, request=request, obj_in=virtual_machine_in
        )
    else:
        raise PermissionDenied()


# Returns all VirtualMachines
@router.get(
    "/",
    status_code=200,
    response_model=VirtualMachineList,
    operation_id="vms_read_all",
    summary="Get VirtualMachines",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_virtual_machines(
    request: Request,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "vms_read",
        request,
        db=db,
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).get_multi(
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDVirtualMachine(VirtualMachineModel).get_multi_auth(
            request=request,
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Get VirtualMachine with ID
@router.get(
    "/{id}",
    status_code=200,
    response_model=VirtualMachine,
    operation_id="vms_read_one",
    summary="Get VirtualMachine",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_virtual_machine(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "vms_read", request, id, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).get(db, id)
    else:
        raise PermissionDenied()


# Update VirtualMachine
@router.put(
    "/{id}",
    status_code=200,
    response_model=VirtualMachine,
    operation_id="vms_update",
    summary="Update VirtualMachine",
    dependencies=[Depends(dependencies.get_current_user)],
)
def update_virtual_machine(
    *,
    id: UUID4,
    virtual_machine_in: VirtualMachineUpdate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "vms_update", request, id, db=db
    ).has_permission():
        # Check if virtual_machine with the same name already exists
        db_name = CRUDVirtualMachine(VirtualMachineModel).get_by_name(
            db, name=virtual_machine_in.name
        )
        if db_name and db_name.id != id:
            raise DuplicateFieldException(field="name")
        # Check if a DIFFERENT virtual_machine with the same Key already exists
        return CRUDVirtualMachine(VirtualMachineModel).update(
            db=db, request=request, obj_in=virtual_machine_in, id=id
        )
    else:
        raise PermissionDenied()


# Get ipv4 for VirtualMachine from PVE
@router.get(
    "/{id}/ipv4",
    status_code=200,
    operation_id="vms_ipv4_get",
    summary="Get VirtualMachine ipv4 address from PVE",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_virtual_machine_ipv4(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "vms_read", request, id, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).get_ipv4(id, db)
    else:
        raise PermissionDenied()


# Update VirtualMachine's Apps
@router.put(
    "/{id}/applications",
    status_code=200,
    response_model=VirtualMachine,
    operation_id="vms_apps_update",
    summary="Update VirtualMachine Apps",
    dependencies=[Depends(dependencies.get_current_user)],
)
def update_virtual_machine_apps(
    *,
    id: UUID4,
    virtual_machine_in: VirtualMachineUpdateApps,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "vms_update", request, id, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).update_apps(
            db=db, request=request, obj_in=virtual_machine_in, id=id
        )
    else:
        raise PermissionDenied()


# Delete VirtualMachine with ID
@router.delete(
    "/{id}",
    status_code=200,
    operation_id="vms_delete",
    summary="Delete VirtualMachine",
    dependencies=[Depends(dependencies.get_current_user)],
)
def delete_virtual_machine(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "vms_delete", request, id, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).delete(db, request, id)
    else:
        raise PermissionDenied()


# Returns a VirtualMachine's apps
@router.get(
    "/{id}/applications",
    status_code=200,
    response_model=ApplicationList,
    operation_id="vms_application_read_all",
    summary="Get VirtualMachine's Applications",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_virtual_machine_apps(
    request: Request,
    id: UUID4,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "vms_read", request, id, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).get_multi_association(
            parent_model=ApplicationModel,
            child_model=VirtualMachineModel,
            parent_field_name="vms",
            child_field_name="id",
            field_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDVirtualMachine(
            VirtualMachineModel
        ).get_multi_association_auth(
            request=request,
            parent_model=ApplicationModel,
            child_model=VirtualMachineModel,
            parent_field_name="vms",
            child_field_name="id",
            field_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Get all Guacamole for VirtualMachine
@router.get(
    "/{id}/guacamole",
    status_code=200,
    response_model=GuacamoleList,
    operation_id="vms_guacamole_read_all",
    summary="Get all Guacamole associated with VirtualMachine",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_virtual_machine_guacamole(
    request: Request,
    id: UUID4,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
) -> dict:
    if dependencies.PermissionChecker(
        "vms_read", request, id, db=db
    ).has_permission():
        return CRUDGuacamole(GuacamoleModel).get_multi_foreign_key(
            foreign_key_field="vmId",
            foreign_key_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDGuacamole(GuacamoleModel).get_multi_foreign_key_auth(
            request=request,
            foreign_key_field="vmId",
            foreign_key_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Virtual machine actions - CLONE
@router.post(
    "/{id}/actions/clone",
    status_code=200,
    response_model=VirtualMachine,
    operation_id="vms_actions_clone",
    summary="Clone a VirtualMachine into another VirtualMachine",
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machine_actions_clone(
    *,
    id: UUID4,
    obj_in: VirtualMachineClone,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "vms_create", request, id, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).actions_clone(
            db=db, request=request, obj_in=obj_in, id=id
        )
    else:
        raise PermissionDenied()


# Virtual machine actions - MIGRATE
@router.post(
    "/{id}/actions/migrate",
    status_code=200,
    response_model=VirtualMachine,
    operation_id="vms_actions_migrate",
    summary="Migrate a VirtualMachine from one node to another",
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machine_actions_migrate(
    *,
    id: UUID4,
    obj_in: VirtualMachineMigrate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "vms_update", request, id, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).actions_migrate(
            db=db, request=request, obj_in=obj_in, id=id
        )
    else:
        raise PermissionDenied()


# Virtual machine actions - HA_GET
@router.get(
    "/{id}/actions/ha",
    status_code=200,
    operation_id="vms_actions_ha_get",
    summary="Get HA state for VirtualMachine on the PVE",
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machine_actions_ha_get(
    *, id: UUID4, db: Session = Depends(dependencies.get_db), request: Request
) -> dict:
    if dependencies.PermissionChecker(
        "vms_read", request, id, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).actions_ha_get(
            db=db, request=request, id=id
        )
    else:
        raise PermissionDenied()


# Virtual machine actions - HA_SET
@router.post(
    "/{id}/actions/ha",
    status_code=200,
    response_model=VirtualMachine,
    operation_id="vms_actions_ha_add",
    summary="Set VirtualMachine HA parameters on the PVE",
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machine_actions_ha_add(
    *,
    id: UUID4,
    obj_in: VirtualMachineHaAdd,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "vms_update", request, id, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).actions_ha_add(
            db=db, request=request, obj_in=obj_in, id=id
        )
    else:
        raise PermissionDenied()


# Virtual machine actions - HA_REMOVE
@router.delete(
    "/{id}/actions/ha",
    status_code=200,
    response_model=VirtualMachine,
    operation_id="vms_actions_ha_remove",
    summary="Remove VirtualMachine from cluster HA",
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machine_actions_ha_remove(
    *, id: UUID4, db: Session = Depends(dependencies.get_db), request: Request
) -> dict:
    if dependencies.PermissionChecker(
        "vms_update", request, id, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).actions_ha_remove(
            db=db, request=request, id=id
        )
    else:
        raise PermissionDenied()


# Virtual machine actions - STOP
@router.post(
    "/{id}/actions/stop",
    status_code=200,
    response_model=VirtualMachine,
    operation_id="vms_actions_stop",
    summary="Stop VirtualMachine",
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machine_actions_stop(
    *, id: UUID4, db: Session = Depends(dependencies.get_db), request: Request
) -> dict:
    if dependencies.PermissionChecker(
        ["vms_actions_stop", "object_reset"], request, id, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).actions_stop(
            db=db, request=request, id=id
        )
    else:
        raise PermissionDenied()


# Virtual machine actions - START
@router.post(
    "/{id}/actions/start",
    status_code=200,
    response_model=VirtualMachine,
    operation_id="vms_actions_start",
    summary="Start VirtualMachine",
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machine_actions_start(
    *, id: UUID4, db: Session = Depends(dependencies.get_db), request: Request
) -> dict:
    if dependencies.PermissionChecker(
        ["vms_actions_start", "object_reset"], request, id, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).actions_start(
            db=db, request=request, id=id
        )
    else:
        raise PermissionDenied()


# Virtual machine actions - REBOOT
@router.post(
    "/{id}/actions/reboot",
    status_code=200,
    response_model=VirtualMachine,
    operation_id="vms_actions_reboot",
    summary="Reboot VirtualMachine",
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machine_actions_reboot(
    *, id: UUID4, db: Session = Depends(dependencies.get_db), request: Request
) -> dict:
    if dependencies.PermissionChecker(
        ["vms_actions_reboot", "object_reset"], request, id, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).actions_reboot(
            db=db, request=request, id=id
        )
    else:
        raise PermissionDenied()


# Virtual machine actions - RESET
@router.post(
    "/{id}/actions/reset",
    status_code=200,
    response_model=VirtualMachine,
    operation_id="vms_actions_reset",
    summary="Reset VirtualMachine",
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machine_actions_reset(
    *, id: UUID4, db: Session = Depends(dependencies.get_db), request: Request
) -> dict:
    if dependencies.PermissionChecker(
        ["vms_actions_reset", "object_reset"], request, id, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).actions_reset(
            db=db, request=request, id=id
        )
    else:
        raise PermissionDenied()


# Virtual machine actions - PAUSE
@router.post(
    "/{id}/actions/pause",
    status_code=200,
    response_model=VirtualMachine,
    operation_id="vms_actions_pause",
    summary="Pause VirtualMachine",
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machine_actions_pause(
    *, id: UUID4, db: Session = Depends(dependencies.get_db), request: Request
) -> dict:
    if dependencies.PermissionChecker(
        "vms_actions_pause", request, id, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).actions_pause(
            db=db, request=request, id=id
        )
    else:
        raise PermissionDenied()


# Virtual machine actions - SHUTDOWN
@router.post(
    "/{id}/actions/shutdown",
    status_code=200,
    response_model=VirtualMachine,
    operation_id="vms_actions_shutdown",
    summary="Shut down VirtualMachine",
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machine_actions_shutdown(
    *, id: UUID4, db: Session = Depends(dependencies.get_db), request: Request
) -> dict:
    if dependencies.PermissionChecker(
        ["vms_actions_shutdown", "object_reset"], request, id, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).actions_shutdown(
            db=db, request=request, id=id
        )
    else:
        raise PermissionDenied()


# Virtual machine actions - RESUME
@router.post(
    "/{id}/actions/resume",
    status_code=200,
    response_model=VirtualMachine,
    operation_id="vms_actions_resume",
    summary="Resume VirtualMachine",
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machine_actions_resume(
    *, id: UUID4, db: Session = Depends(dependencies.get_db), request: Request
) -> dict:
    if dependencies.PermissionChecker(
        ["vms_actions_resume", "object_reset"], request, id, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).actions_resume(
            db=db, request=request, id=id
        )
    else:
        raise PermissionDenied()


# Virtual machine rrd data
@router.get(
    "/{id}/rrddata",
    status_code=200,
    operation_id="vm_rrddata_read",
    summary="Read vm RRD statistic data",
    response_model=ProxmoxVMMetricsList,
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machine_get_rrddata(
    id: UUID4,
    request: Request,
    timeframe: ProxmoxRRDTimeframe = ProxmoxRRDTimeframe.HOUR,
    cf: ProxmoxRRDConsolidation = ProxmoxRRDConsolidation.AVERAGE,
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "vms_read", request, id, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).get_rrddata(
            db=db,
            id=id,
            cf=cf,
            timeframe=timeframe,
        )
    else:
        raise PermissionDenied()


# Virtual machines bulk actions - START
@router.post(
    "/bulk-actions/start",
    status_code=200,
    operation_id="vms_bulk_actions_start",
    summary="Start multiple VirtualMachines",
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machines_bulk_actions_start(
    *,
    obj_in: VirtualMachineIdList,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "vms_actions_start", request, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).bulk_start(
            db=db, request=request, obj_in=obj_in
        )
    else:
        raise PermissionDenied()


# Virtual machines bulk actions - STOP
@router.post(
    "/bulk-actions/stop",
    status_code=200,
    operation_id="vms_bulk_actions_stop",
    summary="Stop multiple VirtualMachines",
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machines_bulk_actions_stop(
    *,
    obj_in: VirtualMachineIdList,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "vms_actions_stop", request, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).bulk_stop(
            db=db, request=request, obj_in=obj_in
        )
    else:
        raise PermissionDenied()


# Virtual machines bulk actions - PAUSE
@router.post(
    "/bulk-actions/pause",
    status_code=200,
    operation_id="vms_bulk_actions_pause",
    summary="Pause multiple VirtualMachines",
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machines_bulk_actions_pause(
    *,
    obj_in: VirtualMachineIdList,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "vms_actions_pause", request, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).bulk_pause(
            db=db, request=request, obj_in=obj_in
        )
    else:
        raise PermissionDenied()


# Virtual machines bulk actions - RESET
@router.post(
    "/bulk-actions/reset",
    status_code=200,
    operation_id="vms_bulk_actions_reset",
    summary="Reset multiple VirtualMachines",
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machines_bulk_actions_reset(
    *,
    obj_in: VirtualMachineIdList,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "vms_actions_reset", request, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).bulk_reset(
            db=db, request=request, obj_in=obj_in
        )
    else:
        raise PermissionDenied()


# Virtual machines bulk actions - REBOOT
@router.post(
    "/bulk-actions/reboot",
    status_code=200,
    operation_id="vms_bulk_actions_reboot",
    summary="Reboot multiple VirtualMachines",
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machines_bulk_actions_reboot(
    *,
    obj_in: VirtualMachineIdList,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "vms_actions_reboot", request, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).bulk_reboot(
            db=db, request=request, obj_in=obj_in
        )
    else:
        raise PermissionDenied()


# Virtual machines bulk actions - SHUTDOWN
@router.post(
    "/bulk-actions/shutdown",
    status_code=200,
    operation_id="vms_bulk_actions_shutdown",
    summary="Shut down multiple VirtualMachines",
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machines_bulk_actions_shutdown(
    *,
    obj_in: VirtualMachineIdList,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "vms_actions_shutdown", request, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).bulk_shutdown(
            db=db, request=request, obj_in=obj_in
        )
    else:
        raise PermissionDenied()


# Virtual machines bulk actions - RESUME
@router.post(
    "/bulk-actions/resume",
    status_code=200,
    operation_id="vms_bulk_actions_resume",
    summary="Resume multiple VirtualMachines",
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machines_bulk_actions_resume(
    *,
    obj_in: VirtualMachineIdList,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "vms_actions_resume", request, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).bulk_resume(
            db=db, request=request, obj_in=obj_in
        )
    else:
        raise PermissionDenied()


# Virtual machines bulk actions - HA ADD
@router.post(
    "/bulk-actions/ha",
    status_code=200,
    operation_id="vms_bulk_actions_ha_add",
    summary="Add multiple VirtualMachines to HA",
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machines_bulk_actions_ha_add(
    *,
    obj_in: VirtualMachineBulkHaAdd,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "vms_update", request, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).bulk_ha_add(
            db=db, request=request, obj_in=obj_in
        )
    else:
        raise PermissionDenied()


# Virtual machines bulk actions - HA REMOVE
@router.delete(
    "/bulk-actions/ha",
    status_code=200,
    operation_id="vms_bulk_actions_ha_remove",
    summary="Remove multiple VirtualMachines from HA",
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machines_bulk_actions_ha_remove(
    *,
    obj_in: VirtualMachineIdList,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "vms_update", request, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).bulk_ha_remove(
            db=db, request=request, obj_in=obj_in
        )
    else:
        raise PermissionDenied()


# Virtual machines bulk actions - MIGRATE
@router.post(
    "/bulk-actions/migrate",
    status_code=200,
    operation_id="vms_bulk_actions_migrate",
    summary="Migrate multiple VirtualMachines to a target node",
    dependencies=[Depends(dependencies.get_current_user)],
)
def virtual_machines_bulk_actions_migrate(
    *,
    obj_in: VirtualMachineBulkMigrate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "vms_update", request, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).bulk_migrate(
            db=db, request=request, obj_in=obj_in, target_node=obj_in.targetNode
        )
    else:
        raise PermissionDenied()
