from fastapi import APIRouter, Depends, Request
from pydantic import UUID4
from sqlalchemy.orm import Session

from controllers.mails import *
from core import dependencies
from core.exceptions import PermissionDenied
from core.responses import (
    BASE_RESPONSES,
    READ_RESPONSES,
    WRITE_RESPONSES,
    build_description,
)
from models.mails import Mail as MailModel
from schemas.mails import Mail, MailList

router = APIRouter(
    prefix="/mails",
    tags=["mails"],
    responses=BASE_RESPONSES,
)


# Create new Mail
@router.post(
    "/",
    status_code=201,
    response_model=Mail,
    operation_id="mails_send",
    responses=WRITE_RESPONSES,
    summary="Create Mail",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Sends a new mail message.",
        permission="mails_send",
    ),
)
def create_mail(
    *,
    mail_in: MailCreate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "mails_send", request, db=db
    ).has_permission():
        return CRUDMail(MailModel).create(
            db=db, request=request, obj_in=mail_in
        )
    else:
        raise PermissionDenied()


# Returns all Mails
@router.get(
    "/",
    status_code=200,
    response_model=MailList,
    operation_id="mails_read_all",
    summary="Get Mails",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a paginated list of all mail messages.",
        permission="mails_read",
    ),
)
def get_mails(
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
        "mails_read", request, db=db
    ).has_permission():
        return CRUDMail(MailModel).get_multi(
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDMail(MailModel).get_multi_auth(
            request=request,
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Get Mail with ID
@router.get(
    "/{id}",
    status_code=200,
    response_model=Mail,
    operation_id="mails_read_one",
    responses=READ_RESPONSES,
    summary="Get Mail",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a single mail message by ID.",
        permission="mails_read",
    ),
)
def get_mail(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "mails_read", request, id, db=db
    ).has_permission():
        return CRUDMail(MailModel).get(db, id)
    else:
        raise PermissionDenied()
