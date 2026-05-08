from fastapi import APIRouter, Depends, Request
from pydantic import UUID4
from sqlalchemy.orm import Session

from controllers.mails_templates import *
from core import dependencies
from core.exceptions import (
    DuplicateFieldException,
    PermissionDenied,
    ProtectedObjectError,
)
from models.mails_templates import MailTemplate as MailTemplateModel
from schemas.mails_templates import MailTemplate, MailTemplateList

router = APIRouter(
    prefix="/mailtemplates",
    tags=["mailtemplates"],
    responses={404: {"detail": "Not found"}},
)


# Create new MailTemplate
@router.post(
    "/",
    status_code=201,
    response_model=MailTemplate,
    operation_id="mail_templates_create",
    summary="Create MailTemplate",
    dependencies=[Depends(dependencies.get_current_user)],
)
def create_mail_template(
    *,
    mail_template_in: MailTemplateCreate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "mail_templates_create", request, db=db
    ).has_permission():
        # Check if MailTemplate with the same name already exists
        db_name = CRUDMailTemplate(MailTemplateModel).get_by_name(
            db, name=mail_template_in.name
        )
        if db_name and db_name.id != mail_template_in.id:
            raise DuplicateFieldException(field="name")
        return CRUDMailTemplate(MailTemplateModel).create(
            db=db, request=request, obj_in=mail_template_in
        )
    else:
        raise PermissionDenied()


# Returns all MailTemplates
@router.get(
    "/",
    status_code=200,
    response_model=MailTemplateList,
    operation_id="mail_templates_read_all",
    summary="Get MailTemplates",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_mail_templates(
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
        return CRUDMailTemplate(MailTemplateModel).get_multi(
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDMailTemplate(MailTemplateModel).get_multi_auth(
            request=request,
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Get MailTemplate with ID
@router.get(
    "/{id}",
    status_code=200,
    response_model=MailTemplate,
    operation_id="mail_templates_read_one",
    summary="Get MailTemplate",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_mail_template(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "mail_templates_read", request, id, db=db
    ).has_permission():
        return CRUDMailTemplate(MailTemplateModel).get(db, id)
    else:
        raise PermissionDenied()


# Update MailTemplate
@router.put(
    "/{id}",
    status_code=200,
    response_model=MailTemplate,
    operation_id="mail_templates_update",
    summary="Update MailTemplate",
    dependencies=[Depends(dependencies.get_current_user)],
)
def update_mail_template(
    *,
    id: UUID4,
    mail_template_in: MailTemplateUpdate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "mail_templates_update", request, id, db=db
    ).has_permission():
        # Check if MailTemplate with the same name already exists
        db_name = CRUDMailTemplate(MailTemplateModel).get_by_name(
            db, name=mail_template_in.name
        )
        if db_name and db_name.id != id:
            raise DuplicateFieldException(field="name")
        return CRUDMailTemplate(MailTemplateModel).update(
            db=db, request=request, id=id, obj_in=mail_template_in
        )
    else:
        raise PermissionDenied()


# Delete MailTemplate with ID
@router.delete(
    "/{id}",
    status_code=200,
    operation_id="mail_templates_delete",
    summary="Delete MailTemplate",
    dependencies=[Depends(dependencies.get_current_user)],
)
def delete_mail_template(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "mail_templates_delete", request, id, db=db
    ).has_permission():
        mail_template = CRUDMailTemplate(MailTemplateModel).get(db, id)
        if mail_template.protected:
            raise ProtectedObjectError(
                model_name=MailTemplateModel.__name__,
                operation="mail_templates_delete",
            )
        return CRUDMailTemplate(MailTemplateModel).delete(db, id)
    else:
        raise PermissionDenied()
