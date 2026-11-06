from fastapi import APIRouter, Depends, Request
from pydantic import UUID4
from sqlalchemy.orm import Session

from controllers.object_permissions import *
from core import dependencies
from core.exceptions import PermissionDenied
from core.responses import (
    BASE_RESPONSES,
    READ_RESPONSES,
    WRITE_RESPONSES,
    build_description,
)
from models.object_permissions import ObjectPermission as ObjectPermissionModel
from schemas.base import PaginationPageDetails
from schemas.object_permissions import (
    OBJECT_SCOPED_TYPES,
    DeactivatedObjectTypes,
    ObjectPermission,
    ObjectPermissionCreate,
    ObjectPermissionList,
    ObjectPermissionTypeSchemaList,
    get_permission_schema_for_type,
)

router = APIRouter(
    prefix="/object-permissions",
    tags=["object-permissions"],
    responses=BASE_RESPONSES,
)


# Get valid permission keys for all known object types
@router.get(
    "/keys",
    status_code=200,
    response_model=ObjectPermissionTypeSchemaList,
    response_model_by_alias=True,
    operation_id="object_permissions_keys_all",
    summary="Get valid permission keys for all object types",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns the valid permission keys for every supported object type.",
        permission="object_permissions_read",
    ),
)
def get_permission_keys_all(
    request: Request, db: Session = Depends(dependencies.get_db)
):
    if not dependencies.PermissionChecker(
        "object_permissions_read", request, db=db
    ).has_permission():
        raise PermissionDenied()
    all_types = OBJECT_SCOPED_TYPES + [t.value for t in DeactivatedObjectTypes]
    items = [get_permission_schema_for_type(t) for t in sorted(all_types)]
    total = len(items)
    return ObjectPermissionTypeSchemaList(
        pageDetails=PaginationPageDetails(
            page=1,
            perPage=total,
            pageCount=1,
            totalCount=total,
        ),
        items=items,
    )


# Create new ObjectPermissions
@router.post(
    "/",
    status_code=201,
    response_model=ObjectPermission,
    operation_id="object_permissions_create",
    responses=WRITE_RESPONSES,
    summary="Create ObjectPermission",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Grants an object-level permission to a user or role for a specific object.",
        permission="object_permissions_create",
    ),
)
def create_permission(
    *,
    permission_in: ObjectPermissionCreate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "object_permissions_create", request, db=db
    ).has_permission():
        return CRUDObjectPermission(ObjectPermissionModel).create(
            db=db, request=request, obj_in=permission_in
        )
    else:
        raise PermissionDenied()


# Returns all ObjectPermissions
@router.get(
    "/",
    status_code=200,
    response_model=ObjectPermissionList,
    operation_id="object_permissions_read_all",
    summary="Get ObjectPermissions",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a paginated list of all object-level permissions.",
        permission="object_permissions_read",
    ),
)
def get_permissions(
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
        "object_permissions_read", request, db=db
    ).has_permission():
        return CRUDObjectPermission(ObjectPermissionModel).get_multi(
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        raise PermissionDenied()


# Returns ObjectPermissions for object_type and object_id
@router.get(
    "/{object_type}/{object_id}",
    status_code=200,
    response_model=ObjectPermissionList,
    operation_id="object_permissions_object_read_all",
    responses=READ_RESPONSES,
    summary="Get ObjectPermissions",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns all object-level permissions for a specific object type and ID.",
        permission="object_permissions_read",
    ),
)
def get_permissions_for_type_id(
    request: Request,
    object_type: str,
    object_id: UUID4,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "object_permissions_read", request, db=db
    ).has_permission():
        return CRUDObjectPermission(ObjectPermissionModel).get_multi_type_id(
            db=db,
            object_type=object_type,
            object_id=object_id,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDObjectPermission(
            ObjectPermissionModel
        ).get_multi_type_id_auth(
            db=db,
            request=request,
            object_type=object_type,
            object_id=object_id,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Get permission with ID
@router.get(
    "/{id}",
    status_code=200,
    response_model=ObjectPermission,
    operation_id="object_permissions_read_one",
    responses=READ_RESPONSES,
    summary="Get ObjectPermission",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a single object permission by ID.",
        permission="object_permissions_read",
    ),
)
def get_permission(
    request: Request,
    id: UUID4,
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "object_permissions_read", request, db=db
    ).has_permission():
        return CRUDObjectPermission(ObjectPermissionModel).get(db, id)
    else:
        raise PermissionDenied()


# Delete ObjectPermissions with ID
@router.delete(
    "/{id}",
    status_code=200,
    operation_id="object_permissions_delete",
    responses=WRITE_RESPONSES,
    summary="Delete ObjectPermission",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Revokes an object-level permission by ID.",
        permission="object_permissions_delete",
    ),
)
def delete_permission(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "object_permissions_delete", request, db=db
    ).has_permission():
        return CRUDObjectPermission(ObjectPermissionModel).delete(
            db, id, request
        )
    else:
        raise PermissionDenied()
