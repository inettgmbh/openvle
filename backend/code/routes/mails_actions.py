from fastapi import APIRouter, Depends, Request
from pydantic import UUID4
from sqlalchemy.orm import Session

from controllers.base import CRUDBase
from controllers.mails_templates import CRUDMailTemplate
from core import dependencies
from core.exceptions import PermissionDenied
from core.responses import CRUD_RESPONSES
from models import (
    MailAction as MailActionModel,
    MailTemplate as MailTemplateModel,
)
from schemas.mails_actions import MailAction, MailActionList
from schemas.mails_templates import MailTemplateList

router = APIRouter(
    prefix="/mailactions",
    tags=["mailactions"],
    responses=CRUD_RESPONSES,
)


# Returns all MailActions
@router.get(
    "/",
    status_code=200,
    response_model=MailActionList,
    operation_id="mail_actions_read_all",
    summary="Get MailActions",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `mail_templates_read`",
)
def get_mail_actions(
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
        "mail_templates_read", request, db=db
    ).has_permission():
        return CRUDBase(MailActionModel).get_multi(
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


# Get MailAction with ID
@router.get(
    "/{id}",
    status_code=200,
    response_model=MailAction,
    operation_id="mail_actions_read_one",
    summary="Get MailAction",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `mail_templates_read`",
)
def get_mail_action(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "mail_templates_read", request, id, db=db
    ).has_permission():
        return CRUDBase(MailActionModel).get(db, id)
    else:
        raise PermissionDenied()


# Get MailTemplates for MailAction with MailTemplate.ID
@router.get(
    "/{id}/mail-templates",
    status_code=200,
    response_model=MailTemplateList,
    operation_id="mail_action_templates_read_all",
    summary="Get MailTemplates assigned to MailAction",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `mail_templates_read`",
)
def get_mail_templates_for_mail_action(
    id: UUID4,
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
        "mail_templates_read", request, db=db
    ).has_permission():
        return CRUDMailTemplate(MailTemplateModel).get_multi_foreign_key(
            foreign_key_field="mail_action",
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
        raise PermissionDenied()
