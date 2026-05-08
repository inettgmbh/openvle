from fastapi import APIRouter, Depends, Request
from pydantic import UUID4
from sqlalchemy.orm import Session

from controllers.guacamole_connection_profiles import *
from core import dependencies
from core.exceptions import PermissionDenied
from models import GuacamoleConnectionProfile as GuacamoleConnectionProfileModel
from schemas.guacamole_connection_profiles import (
    GuacamoleConnectionProfile,
    GuacamoleConnectionProfileClone,
    GuacamoleConnectionProfileCreate,
    GuacamoleConnectionProfileList,
)

router = APIRouter(
    prefix="/guacamole-connection-profiles",
    tags=["guacamole-connection-profiles"],
    responses={404: {"detail": "Not found"}},
)


# Create new GuacamoleConnectionProfile
@router.post(
    "/",
    status_code=201,
    response_model=GuacamoleConnectionProfile,
    operation_id="guacamole_connection_profiles_create",
    summary="Create GuacamoleConnectionProfile",
    dependencies=[Depends(dependencies.PermissionChecker())],
)
def create_guacamole_connection_profile(
    *,
    gcp_in: GuacamoleConnectionProfileCreate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "guacamole_connection_profiles_create", request, db=db
    ).has_permission():
        return CRUDGuacamoleConnectionProfile(
            GuacamoleConnectionProfileModel
        ).create(db=db, request=request, obj_in=gcp_in)
    else:
        raise PermissionDenied()


# Returns all GuacamoleConnectionProfiles
@router.get(
    "/",
    status_code=200,
    response_model=GuacamoleConnectionProfileList,
    operation_id="guacamole_connection_profiles_read_all",
    summary="Get GuacamoleConnectionProfiles",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_guacamole_connection_profiles(
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
        "guacamole_connection_profiles_read", request, db=db
    ).has_permission():
        return CRUDGuacamoleConnectionProfile(
            GuacamoleConnectionProfileModel
        ).get_multi(
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDGuacamoleConnectionProfile(
            GuacamoleConnectionProfileModel
        ).get_multi_auth(
            request=request,
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Get GuacamoleConnectionProfile with ID
@router.get(
    "/{id}",
    status_code=200,
    operation_id="guacamole_connection_profiles_read_one",
    summary="Get GuacamoleConnectionProfile",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_guacamole_connection_profile(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "guacamole_connection_profiles_read", request, id, db=db
    ).has_permission():
        return CRUDGuacamoleConnectionProfile(
            GuacamoleConnectionProfileModel
        ).get(db, id)
    else:
        raise PermissionDenied()


# Clone a GuacamoleConnectionProfile
@router.post(
    "/{id}/clone",
    status_code=201,
    response_model=GuacamoleConnectionProfile,
    operation_id="guacamole_connection_profiles_clone",
    summary="Clone a GuacamoleConnectionProfile",
    dependencies=[Depends(dependencies.PermissionChecker())],
)
def clone_guacamole_connection_profile(
    *,
    id: UUID4,
    gcp_in: GuacamoleConnectionProfileClone,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "guacamole_connection_profiles_create", request, db=db
    ).has_permission():
        return CRUDGuacamoleConnectionProfile(
            GuacamoleConnectionProfileModel
        ).clone(db=db, id=id, request=request, obj_in=gcp_in)
    else:
        raise PermissionDenied()


# Delete GuacamoleConnectionProfile with ID
@router.delete(
    "/{id}",
    status_code=200,
    operation_id="guacamole_connection_profiles_delete",
    summary="Delete GuacamoleConnectionProfile",
    dependencies=[Depends(dependencies.get_current_user)],
)
def delete_guacamole_connection_profile(
    id: UUID4, request: Request, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "guacamole_connection_profiles_delete", request, id, db=db
    ).has_permission():
        return CRUDGuacamoleConnectionProfile(
            GuacamoleConnectionProfileModel
        ).delete(db, id)
    else:
        raise PermissionDenied()


# Returns all GuacamoleConnectionProfiles for ObjectId and objectType
@router.get(
    "/{objectType}/{objectId}",
    status_code=200,
    response_model=GuacamoleConnectionProfileList,
    operation_id="guacamole_connection_profiles_objects_read_all",
    summary="Get GuacamoleConnectionProfiles by objectType and objectId",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_gcp_for_object(
    objectId: UUID4,
    objectType: str,
    request: Request,
    limit: int = 100,
    page: int = 1,
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "guacamole_connection_profiles_read", request, objectId, db=db
    ).has_permission():
        return CRUDGuacamoleConnectionProfile(
            GuacamoleConnectionProfileModel
        ).get_gcps_for_object(
            db=db,
            objectId=objectId,
            objectType=objectType,
            limit=limit,
            page=page,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDGuacamoleConnectionProfile(
            GuacamoleConnectionProfileModel
        ).get_gcps_for_object_auth(
            request=request,
            db=db,
            objectId=objectId,
            objectType=objectType,
            limit=limit,
            page=page,
            sort_by=sort_by,
            sort_order=sort_order,
        )
