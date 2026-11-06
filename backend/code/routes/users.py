from fastapi import APIRouter, Depends

from controllers.guacamole import CRUDGuacamole
from controllers.users import *
from core import dependencies
from core.exceptions import (
    DuplicateFieldException,
    InvalidFieldValue,
    PermissionDenied,
    RequiredParameterMissingError,
    UserAlreadyRegisteredException,
)
from core.responses import (
    BASE_RESPONSES,
    CRUD_RESPONSES,
    READ_RESPONSES,
    WRITE_RESPONSES,
    build_description,
)
from models import Guacamole as GuacamoleModel, User
from schemas.events import UserInEventList
from schemas.guacamole import GuacamoleList
from schemas.users import *
from schemas.virtual_machines import VirtualMachineList

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses=BASE_RESPONSES,
)


# Create new user
@router.post(
    "/",
    status_code=201,
    response_model=User,
    operation_id="users_create",
    responses=CRUD_RESPONSES,
    summary="Create User",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Creates a new user account.",
        permission="users_create",
        notes=[
            "Returns 409 if the username or email address is already registered.",
        ],
    ),
)
def create_user(
    *,
    user_in: UserCreate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "users_create", request, db=db
    ).has_permission():
        # Check if username already exists
        db_username = CRUDUser(UserModel).get_by_username(
            db, username=user_in.username
        )
        if db_username:
            raise UserAlreadyRegisteredException()
        # Check if user e-mail already exists
        db_useremail = CRUDUser(UserModel).get_by_email(db, email=user_in.email)
        if db_useremail:
            raise UserAlreadyRegisteredException()
        return CRUDUser(UserModel).create(
            db=db, request=request, obj_in=user_in
        )
    else:
        raise PermissionDenied()


# Returns all users
@router.get(
    "/",
    status_code=200,
    response_model=UserList | UserSearchList,
    operation_id="users_read_all",
    summary="Get Users",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a paginated list of users.",
        permission=["users_read", "users_search"],
        notes=[
            "With `users_read`: returns the full `User` schema with no search restrictions.",
            "With `users_search` only: returns the limited `UserSearch` schema. Requires `search_field` and `search_value`. Results are capped at 25 and always return page 1 to prevent enumeration.",
        ],
    ),
)
def get_users(
    request: Request,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
):
    # Full access: return complete User schema
    if dependencies.PermissionChecker(
        "users_read", request, db=db
    ).has_permission():
        result = CRUDUser(UserModel).get_multi(
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return UserList(
            pageDetails=result["pageDetails"],
            items=[User.model_validate(u) for u in result["items"]],
        )
    # Limited access: object_search on User returns limited UserSearch schema
    elif dependencies.PermissionChecker(
        "users_search", request, db=db
    ).has_permission():
        SEARCH_VALID_FIELDS = ["email", "username", "name", "id"]
        SEARCH_MAX_LIMIT = 25
        # Require search_field and search_value to prevent user enumeration
        if not search_field:
            raise RequiredParameterMissingError("search_field")
        if not search_value:
            raise RequiredParameterMissingError("search_value")
        # Force page 1 to prevent enumeration via pagination
        page = 1
        if search_field not in SEARCH_VALID_FIELDS:
            raise InvalidFieldValue(
                field="search_field",
                value=search_field,
                supported_values=SEARCH_VALID_FIELDS,
            )
        if sort_by not in SEARCH_VALID_FIELDS:
            raise InvalidFieldValue(
                field="sort_by",
                value=sort_by,
                supported_values=SEARCH_VALID_FIELDS,
            )
        result = CRUDUser(UserModel).get_multi(
            db=db,
            limit=min(limit, SEARCH_MAX_LIMIT),
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return UserSearchList(
            pageDetails=result["pageDetails"],
            items=[UserSearch.model_validate(u) for u in result["items"]],
        )
    else:
        raise PermissionDenied()


# Get user with ID
@router.get(
    "/{id}",
    status_code=200,
    response_model=User,
    operation_id="users_read_one",
    responses=READ_RESPONSES,
    summary="Get User",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a single user by ID.",
        permission="users_read",
    ),
)
def get_user(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "users_read", request, db=db
    ).has_permission():
        return CRUDUser(UserModel).get(db, id)
    else:
        raise PermissionDenied()


# Update user
@router.put(
    "/{id}",
    status_code=200,
    response_model=User,
    operation_id="users_update",
    responses=CRUD_RESPONSES,
    summary="Update User",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Updates a user's profile.",
        permission="users_update",
        notes=[
            "Returns 409 if the new email address is already in use by a different user.",
        ],
    ),
)
def update_user(
    *,
    id: UUID4,
    user_in: UserUpdate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "users_update", request, db=db
    ).has_permission():
        # Check if a DIFFERENT user exists with the same email
        db_useremail = CRUDUser(UserModel).get_by_email(db, email=user_in.email)
        if db_useremail and db_useremail.id != id:
            raise DuplicateFieldException(field="email")
        updated_user = CRUDUser(UserModel).update(
            db=db, request=request, obj_in=user_in, id=id
        )
        return updated_user
    else:
        raise PermissionDenied()


# Delete user with ID
@router.delete(
    "/{id}",
    status_code=200,
    operation_id="users_delete",
    responses=WRITE_RESPONSES,
    summary="Delete User",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Deletes a user by ID.",
        permission="users_delete",
    ),
)
def delete_user(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "users_delete", request, db=db
    ).has_permission():
        return CRUDUser(UserModel).delete(db, id)
    else:
        raise PermissionDenied()


# Preview objects to be deleted along with User upon User deletion
@router.get(
    "/{id}/delete-preview",
    status_code=200,
    operation_id="users_delete_preview",
    responses=READ_RESPONSES,
    summary="Preview objects to be deleted along with User upon User deletion",
    response_model=UserDeletePreview,
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a preview of all objects that will be cascade-deleted when this user is deleted.",
        permission="users_delete",
    ),
)
def user_delete_preview(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "users_delete", request, db=db
    ).has_permission():
        return CRUDUser(UserModel).delete_preview(db, id)
    else:
        raise PermissionDenied()


# Set password
@router.post(
    "/{id}/password",
    status_code=201,
    operation_id="users_set_password",
    responses=WRITE_RESPONSES,
    summary="Set user password",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Sets a new password for a user.",
        permission="users_set_password",
    ),
)
def update_password(
    *,
    id: UUID4,
    user_in: UserSetPassword,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> User:
    if dependencies.PermissionChecker(
        "users_set_password", request, db=db
    ).has_permission():
        return CRUDUser(UserModel).set_password(
            db=db, request=request, user_id=id, obj_in=user_in
        )
    else:
        raise PermissionDenied()


# Set user roles
@router.put(
    "/{id}/roles",
    status_code=200,
    response_model=User,
    operation_id="users_roles_put",
    responses=WRITE_RESPONSES,
    summary="Set User Roles",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Replaces all role assignments for a user.",
        permission="users_update",
        notes=[
            "This overwrites all existing role assignments — use POST to append instead.",
        ],
    ),
)
def set_user_roles(
    *,
    id: UUID4,
    user_in: UserUpdateRoles,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "users_update", request, id, db=db
    ).has_permission():
        return CRUDUser(UserModel).set_roles(
            db=db, request=request, obj_in=user_in, id=id
        )
    else:
        raise PermissionDenied()


# Update user roles
@router.post(
    "/{id}/roles",
    status_code=200,
    response_model=User,
    operation_id="users_roles_update",
    responses=WRITE_RESPONSES,
    summary="Update User Roles",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Appends role assignments to a user without removing existing ones.",
        permission="users_update",
    ),
)
def update_user_roles(
    *,
    id: UUID4,
    user_in: UserUpdateRoles,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "users_update", request, id, db=db
    ).has_permission():
        return CRUDUser(UserModel).update_roles(
            db=db, request=request, obj_in=user_in, id=id
        )
    else:
        raise PermissionDenied()


# Get effective permission list for
@router.get(
    "/{id}/permissions",
    status_code=200,
    operation_id="users_permissions_read_all",
    responses=READ_RESPONSES,
    summary="Get User Permissions",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns the full effective permission set for a user.",
        permission="users_read",
    ),
)
def get_user_permissions(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "users_read", request, id, db=db
    ).has_permission():
        return CRUDUser(UserModel).get_effective_permissions_new(db=db, id=id)
    else:
        raise PermissionDenied()


# Get all Guacamole for User
@router.get(
    "/{id}/guacamole",
    status_code=200,
    response_model=GuacamoleList,
    operation_id="users_guacamole_read_all",
    responses=READ_RESPONSES,
    summary="Get all Guacamole associated with User",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns all Guacamole connection records associated with a user.",
        permission="users_read",
    ),
)
def get_user_guacamole(
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
        "users_read", request, id, db=db
    ).has_permission():
        return CRUDGuacamole(GuacamoleModel).get_multi_foreign_key(
            foreign_key_field="userId",
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
            foreign_key_field="userId",
            foreign_key_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Get all Events for User
@router.get(
    "/{id}/events",
    status_code=200,
    response_model=UserInEventList,
    operation_id="users_events_read_all",
    responses=READ_RESPONSES,
    summary="Get all Events associated with User",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns all events the user is enrolled in.",
        permission="users_read",
        notes=[
            "Also accessible by the user themselves without `users_read`.",
        ],
    ),
)
def get_user_events(
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
    if (
        dependencies.PermissionChecker(
            "users_read", request, id, db=db
        ).has_permission()
        or request.user.id == id
    ):
        return CRUDUser(UserModel).get_user_events(
            db=db,
            id=id,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        raise PermissionDenied()


# Get all VirtualMachines for User
@router.get(
    "/{id}/virtual-machines",
    status_code=200,
    response_model=VirtualMachineList,
    operation_id="users_vms_read_all",
    responses=READ_RESPONSES,
    summary="Get all VirtualMachines associated with User",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns all virtual machines assigned to a user.",
        permission="users_read",
        notes=[
            "Also accessible by the user themselves without `users_read`.",
        ],
    ),
)
def get_user_vms(
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
    if (
        dependencies.PermissionChecker(
            "users_read", request, id, db=db
        ).has_permission()
        or request.user.id == id
    ):
        return CRUDUser(UserModel).get_user_vms(
            db=db,
            id=id,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        raise PermissionDenied()
