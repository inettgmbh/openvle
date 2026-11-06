from fastapi import APIRouter, Depends, Request
from pydantic import UUID4
from sqlalchemy.orm import Session

from controllers.apps import *
from controllers.guacamole import *
from controllers.os import *
from core import dependencies
from core.exceptions import PermissionDenied
from core.responses import (
    BASE_RESPONSES,
    READ_RESPONSES,
    WRITE_RESPONSES,
    build_description,
)
from models.guacamole import Guacamole as GuacamoleModel
from schemas.guacamole import Guacamole, GuacamoleList

router = APIRouter(
    prefix="/guacamole",
    tags=["guacamole"],
    responses=BASE_RESPONSES,
)


# Create new Guacamole
@router.post(
    "/",
    status_code=201,
    response_model=Guacamole,
    operation_id="guacamoles_create",
    responses=WRITE_RESPONSES,
    summary="Create Guacamole",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Creates a Guacamole connection record and enqueues provisioning of the connection on the Guacamole server.",
        permission="guacamoles_create",
        is_async=True,
        notes=[
            "The referenced `GuacamoleConnectionProfile` must be linked to a VirtualMachine with a valid IPv4 address.",
            "The assigned user is automatically granted `object_full` permission on the new Guacamole connection.",
        ],
    ),
)
def create_guacamole(
    *,
    guacamole_in: GuacamoleCreate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "guacamoles_create", request, db=db
    ).has_permission():
        return CRUDGuacamole(GuacamoleModel).create(
            db=db, request=request, obj_in=guacamole_in
        )
    else:
        raise PermissionDenied()


# Returns all Guacamoles
@router.get(
    "/",
    status_code=200,
    response_model=GuacamoleList,
    operation_id="guacamoles_read_all",
    summary="Get Guacamoles",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a paginated list of all Guacamole connections visible to the requesting user.",
        permission="guacamoles_read",
    ),
)
def get_guacamoles(
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
        "guacamoles_read", request, db=db
    ).has_permission():
        return CRUDGuacamole(GuacamoleModel).get_multi(
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDGuacamole(GuacamoleModel).get_multi_auth(
            request=request,
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Get Guacamole with ID
@router.get(
    "/{id}",
    status_code=200,
    response_model=Guacamole,
    operation_id="guacamoles_read_one",
    responses=READ_RESPONSES,
    summary="Get Guacamole",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a single Guacamole connection by ID.",
        permission="guacamoles_read",
    ),
)
def get_guacamole(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "guacamoles_read", request, id, db=db
    ).has_permission():
        return CRUDGuacamole(GuacamoleModel).get(db, id)
    else:
        raise PermissionDenied()


# Delete Guacamole with ID
@router.delete(
    "/{id}",
    status_code=200,
    operation_id="guacamoles_delete",
    responses=WRITE_RESPONSES,
    summary="Delete Guacamole",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Deletes a Guacamole connection from both the database and the Guacamole server.",
        permission="guacamoles_delete",
        notes=[
            "Also removes associated changelogs, object permissions, and tags.",
        ],
    ),
)
def delete_guacamole(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "guacamoles_delete", request, id, db=db
    ).has_permission():
        return CRUDGuacamole(GuacamoleModel).delete(db, id)
    else:
        raise PermissionDenied()


# Manually provision Guacamole
@router.post(
    "/{id}/actions/provision",
    status_code=201,
    response_model=Guacamole,
    operation_id="guacamoles_provision",
    responses=WRITE_RESPONSES,
    summary="Provision Guacamole connection",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Manually provisions an unprovisioned Guacamole connection on the Guacamole server.",
        permission="guacamoles_create",
        notes=[
            "Only works on connections that have not yet been provisioned (no `identifier`).",
            "The linked virtual machine must have a valid IPv4 address.",
        ],
    ),
)
def provision_guacamole(
    *, id: UUID4, db: Session = Depends(dependencies.get_db), request: Request
):
    if dependencies.PermissionChecker(
        "guacamoles_create", request, id, db=db
    ).has_permission():
        return CRUDGuacamole(GuacamoleModel).provision(db=db, id=id)
    else:
        raise PermissionDenied()
