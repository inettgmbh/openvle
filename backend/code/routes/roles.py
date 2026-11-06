from fastapi import APIRouter, Depends, Request
from pydantic import UUID4
from sqlalchemy.orm import Session

from controllers.roles import *
from core import dependencies
from core.exceptions import (
    DuplicateFieldException,
    PermissionDenied,
    ProtectedObjectError,
)
from core.responses import (
    BASE_RESPONSES,
    CRUD_RESPONSES,
    READ_RESPONSES,
    WRITE_RESPONSES,
    build_description,
)
from models.roles import Role as RoleModel
from schemas.roles import *
from schemas.users import UserList

router = APIRouter(
    prefix="/roles",
    tags=["roles"],
    responses=BASE_RESPONSES,
)


# Create new role
@router.post(
    "/",
    status_code=201,
    response_model=Role,
    operation_id="roles_create",
    responses=CRUD_RESPONSES,
    summary="Create Role",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Creates a new role.",
        permission="roles_create",
    ),
)
def create_role(
    *,
    role_in: RoleCreate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "roles_create", request, db=db
    ).has_permission():
        db_key = CRUDRole(RoleModel).get_by_key(db, key=role_in.key)
        if db_key:
            raise DuplicateFieldException(field="key")
        return CRUDRole(RoleModel).create(
            db=db, request=request, obj_in=role_in
        )
    else:
        raise PermissionDenied()


# Returns all roles
@router.get(
    "/",
    status_code=200,
    response_model=RoleList,
    operation_id="roles_read_all",
    summary="Get Roles",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a paginated list of all roles.",
        permission="roles_read",
    ),
)
def get_roles(
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
        "roles_read", request, db=db
    ).has_permission():
        return CRUDRole(RoleModel).get_multi(
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


# Get role with ID
@router.get(
    "/{id}",
    status_code=200,
    response_model=Role,
    operation_id="roles_read_one",
    responses=READ_RESPONSES,
    summary="Get Role",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a single role by ID.",
        permission="roles_read",
    ),
)
def get_role(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "roles_read", request, id, db=db
    ).has_permission():
        return CRUDRole(RoleModel).get(db, id)
    else:
        raise PermissionDenied()


# Update role
@router.put(
    "/{id}",
    status_code=200,
    response_model=Role,
    operation_id="roles_update",
    responses=WRITE_RESPONSES,
    summary="Update Role",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Updates a role's metadata.",
        permission="roles_update",
        notes=[
            "Protected roles cannot be updated.",
        ],
    ),
)
def update_role(
    *,
    id: UUID4,
    role_in: RoleUpdate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "roles_update", request, id, db=db
    ).has_permission():
        if CRUDRole(RoleModel).get(db, id).protected:
            raise ProtectedObjectError(
                model_name=RoleModel.__name__, operation="roles_update"
            )
        return CRUDRole(RoleModel).update(
            db=db, request=request, obj_in=role_in, id=id
        )
    else:
        raise PermissionDenied()


# Set role ObjectPermissions (overwrite)
@router.put(
    "/{id}/object-permissions",
    status_code=200,
    response_model=Role,
    operation_id="roles_object_permissions_put",
    responses=WRITE_RESPONSES,
    summary="Set Role ObjectPermissions",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Replaces all object-level permissions on a role.",
        permission="roles_update",
        notes=[
            "Protected roles cannot be modified.",
            "This overwrites all existing object permissions for the role — use POST to append instead.",
        ],
    ),
)
def set_role_object_permissions(
    *,
    id: UUID4,
    role_in: RoleUpdateObjectPermissions,
    db: Session = Depends(dependencies.get_db),
    request: Request,
):
    if dependencies.PermissionChecker(
        "roles_update", request, id, db=db
    ).has_permission():
        if CRUDRole(RoleModel).get(db, id).protected:
            raise ProtectedObjectError(
                model_name=RoleModel.__name__, operation="roles_update"
            )
        return CRUDRole(RoleModel).set_object_permissions(
            db=db, request=request, obj_in=role_in, id=id
        )
    else:
        raise PermissionDenied()


# Update role ObjectPermissions (append)
@router.post(
    "/{id}/object-permissions",
    status_code=200,
    response_model=Role,
    operation_id="roles_object_permissions_update",
    responses=WRITE_RESPONSES,
    summary="Update Role ObjectPermissions",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Appends object-level permissions to a role without removing existing ones.",
        permission="roles_update",
        notes=[
            "Protected roles cannot be modified.",
        ],
    ),
)
def update_role_object_permissions(
    *,
    id: UUID4,
    role_in: RoleUpdateObjectPermissions,
    db: Session = Depends(dependencies.get_db),
    request: Request,
):
    if dependencies.PermissionChecker(
        "roles_update", request, id, db=db
    ).has_permission():
        if CRUDRole(RoleModel).get(db, id).protected:
            raise ProtectedObjectError(
                model_name=RoleModel.__name__, operation="roles_update"
            )
        return CRUDRole(RoleModel).update_object_permissions(
            db=db, request=request, obj_in=role_in, id=id
        )
    else:
        raise PermissionDenied()


# Get users with given role
@router.get(
    "/{id}/members",
    status_code=200,
    response_model=UserList,
    operation_id="roles_members_read",
    responses=READ_RESPONSES,
    summary="Get Role members",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns all users assigned to a role.",
        permission="roles_read",
    ),
)
def get_role(
    request: Request,
    id: UUID4,
    limit: int = 200,
    page: int = 1,
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    search_field: str = "",
    search_value: str = "",
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "roles_read", request, id, db=db
    ).has_permission():
        return CRUDRole(RoleModel).get_members(
            db=db,
            id=id,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        raise PermissionDenied()


# Delete role with ID
@router.delete(
    "/{id}",
    status_code=200,
    operation_id="roles_delete",
    responses=WRITE_RESPONSES,
    summary="Delete Role",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Deletes a role by ID.",
        permission="roles_delete",
        notes=[
            "Protected roles cannot be deleted.",
        ],
    ),
)
def delete_role(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "roles_delete", request, id, db=db
    ).has_permission():
        if CRUDRole(RoleModel).get(db, id).protected:
            raise ProtectedObjectError(
                model_name=RoleModel.__name__, operation="roles_delete"
            )
        return CRUDRole(RoleModel).delete(db, id)
    else:
        raise PermissionDenied()
