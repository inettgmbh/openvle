from fastapi import APIRouter, Depends
from pydantic import UUID4

from controllers.system import *
from core import dependencies
from core.exceptions import PermissionDenied
from models import SystemSetting as SystemSettingModel
from schemas.system import (
    SystemSetting,
    SystemSettingList,
    SystemSettingWithoutAuditList,
)

router = APIRouter(
    prefix="/system",
    tags=["system"],
    responses={404: {"detail": "Not found"}},
)


# Get system settings
@router.get(
    "/settings",
    status_code=200,
    response_model=Union[SystemSettingList, SystemSettingWithoutAuditList],
    operation_id="system_read",
    summary="Get system settings",
)
async def get_system_settings(
    request: Request,
    limit: int = 200,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "key",
    sort_order: str = "asc",
    db: Session = Depends(dependencies.get_db),
):
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    current_user = await dependencies.get_current_user_optional(
        db=db, token=token
    )
    permissionSet = False

    if current_user:
        checker = dependencies.PermissionChecker("system_read", request, db=db)
        permissionSet = checker.has_permission()

    return CRUDSystemSetting(SystemSettingModel).get_filtered(
        db=db,
        current_user=current_user,
        permissionSet=permissionSet,
        limit=limit,
        page=page,
        sort_by=sort_by,
        sort_order=sort_order,
        search_field=search_field,
        search_value=search_value,
    )


# Update system settings
@router.put(
    "/settings/{id}",
    status_code=200,
    response_model=SystemSetting,
    operation_id="system_update",
    summary="Update system setting",
    dependencies=[Depends(dependencies.get_current_user)],
)
def update_system_settings(
    *,
    id: UUID4,
    system_setting_in: SystemSettingUpdate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> SystemSettingModel:
    if dependencies.PermissionChecker(
        "system_update", request, id, db=db
    ).has_permission():
        return CRUDSystemSetting(SystemSettingModel).update(
            db=db, request=request, id=id, obj_in=system_setting_in
        )  # type: ignore
    else:
        raise PermissionDenied()
