from fastapi import APIRouter, Depends, Request
from pydantic import UUID4
from sqlalchemy.orm import Session

from controllers.apps import *
from controllers.guacamole import *
from controllers.os import *
from core import dependencies
from core.exceptions import PermissionDenied
from models.guacamole import Guacamole as GuacamoleModel
from schemas.guacamole import Guacamole, GuacamoleList

router = APIRouter(
    prefix="/guacamole",
    tags=["guacamole"],
    responses={404: {"detail": "Not found"}},
)


# Create new Guacamole
@router.post(
    "/",
    status_code=201,
    response_model=Guacamole,
    operation_id="guacamoles_create",
    summary="Create Guacamole",
    dependencies=[Depends(dependencies.get_current_user)],
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
    summary="Get Guacamole",
    dependencies=[Depends(dependencies.get_current_user)],
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
    summary="Delete Guacamole",
    dependencies=[Depends(dependencies.get_current_user)],
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
    summary="Provision Guacamole connection",
    dependencies=[Depends(dependencies.get_current_user)],
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
