from fastapi import APIRouter, Depends, Request
from pydantic import UUID4
from sqlalchemy.orm import Session

from controllers.policies import *
from core import dependencies
from core.exceptions import DuplicateFieldException, PermissionDenied
from core.responses import CRUD_RESPONSES
from models import PoliciesUser as PolicyUserModel, Policy as PolicyModel
from schemas.policies import (
    Policy,
    PolicyCreate,
    PolicyList,
    PolicyUpdate,
    PolicyUser,
    PolicyUserAgree,
    PolicyUserList,
)

router = APIRouter(
    prefix="/policies",
    tags=["policies"],
    responses=CRUD_RESPONSES,
)


# Create new Policy
@router.post(
    "/",
    status_code=201,
    response_model=Policy,
    operation_id="policies_create",
    summary="Create Policy",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `policies_create`",
)
def create_policy(
    *,
    policy_in: PolicyCreate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "policies_create", request, db=db
    ).has_permission():
        # Check if Policy with the same name already exists
        db_name = CRUDPolicy(PolicyModel).get_by_name(db, name=policy_in.name)
        if db_name:
            raise DuplicateFieldException(field="name")
        return CRUDPolicy(PolicyModel).create(
            db=db, request=request, obj_in=policy_in
        )
    else:
        raise PermissionDenied()


# Returns all Policies
@router.get(
    "/",
    status_code=200,
    response_model=PolicyList,
    operation_id="policies_read_all",
    summary="Get Policies",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `policies_read`",
)
def get_policies(
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
        "policies_read", request, db=db
    ).has_permission():
        return CRUDPolicy(PolicyModel).get_multi(
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


# Get Policy with ID
@router.get(
    "/{id}",
    status_code=200,
    response_model=Policy,
    operation_id="policies_read_one",
    summary="Get Policy",
    dependencies=[Depends(dependencies.get_current_user_allow_policy_required)],
)
def get_policy(
    id: UUID4, request: Request, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(None, request, db=db).has_permission():
        return CRUDPolicy(PolicyModel).get(db, id)
    else:
        raise PermissionDenied()


# Update Policy
@router.put(
    "/{id}",
    status_code=200,
    response_model=Policy,
    operation_id="policies_update",
    summary="Update Policy",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `policies_update`",
)
def update_policy(
    *,
    id: UUID4,
    policy_in: PolicyUpdate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "policies_update", request, id, db=db
    ).has_permission():
        # Check if Policy with the same name already exists
        db_name = CRUDPolicy(PolicyModel).get_by_name(db, name=policy_in.name)
        if db_name and db_name.id != id:
            raise DuplicateFieldException(field="name")
        return CRUDPolicy(PolicyModel).update(
            db=db, request=request, id=id, obj_in=policy_in
        )
    else:
        raise PermissionDenied()


# Delete Policy with ID
@router.delete(
    "/{id}",
    status_code=200,
    operation_id="policies_delete",
    summary="Delete Policy",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `policies_delete`",
)
def delete_policy(
    id: UUID4, request: Request, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "policies_delete", request, id, db=db
    ).has_permission():
        return CRUDPolicy(PolicyModel).delete(db, id)
    else:
        raise PermissionDenied()


# Endpoint to allow user to agree to a policy with a given policy_id
@router.post(
    "/{id}/actions",
    status_code=201,
    operation_id="policies_actions",
    summary="Allows user to agree to policy with given policy_id",
    dependencies=[Depends(dependencies.get_current_user_allow_policy_required)],
)
def actions_policy(
    *,
    id: UUID4,
    policy_in: PolicyUserAgree,
    db: Session = Depends(dependencies.get_db),
    request: Request,
):
    if dependencies.PermissionChecker(None, request, db=db).has_permission():
        # Check if user has agreed. If not, do nothing
        if not policy_in.agree:
            return
        return CRUDPolicy(PolicyModel).agree_to_policy(
            db=db, request=request, obj_in=policy_in, id=id
        )
    else:
        raise PermissionDenied()


# Returns all Policy - User associations
@router.get(
    "/users/",
    status_code=200,
    response_model=PolicyUserList,
    operation_id="policies_users_read_all",
    summary="Get all User - Policy associations",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `policies_users_read`",
)
def get_policies_users(
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
        "policies_users_read", request, db=db
    ).has_permission():
        return CRUDBase(PolicyUserModel).get_multi(
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


# Returns Policy - User object if user has agreed to policy
@router.get(
    "/{id}/users/{user_id}",
    status_code=200,
    response_model=PolicyUser,
    operation_id="policies_user_read_one",
    summary="Returns Policy - User object if user has agreed to policy",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `policies_user_read`",
)
def get_policy_user(
    id: UUID4,
    request: Request,
    user_id: UUID4,
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "policies_user_read", request, db=db
    ).has_permission():
        return CRUDPolicy(PolicyModel).get_policy_user(db, id, user_id)
    else:
        raise PermissionDenied()
