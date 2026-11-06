from fastapi import APIRouter, Depends, Request
from pydantic import UUID4
from sqlalchemy.orm import Session

from controllers.templates import *
from controllers.virtual_machines import CRUDVirtualMachine
from core import dependencies
from core.exceptions import DuplicateFieldException, PermissionDenied
from core.responses import (
    BASE_RESPONSES,
    CRUD_RESPONSES,
    DELETE_RESPONSES,
    READ_RESPONSES,
    WRITE_RESPONSES,
    build_description,
)
from models.apps import Application as ApplicationModel
from models.courses import Course as CourseModel
from models.templates import Template as TemplateModel
from models.virtual_machines import VirtualMachine as VirtualMachineModel
from schemas.apps import ApplicationList
from schemas.courses import CourseList
from schemas.templates import *
from schemas.virtual_machines import VirtualMachineList

router = APIRouter(
    prefix="/templates",
    tags=["templates"],
    responses=BASE_RESPONSES,
)


# Create new template
@router.post(
    "/",
    status_code=201,
    response_model=Template,
    operation_id="templates_create",
    responses=WRITE_RESPONSES,
    summary="Create Template",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Creates a new template record and enqueues cloning and conversion of the source virtual machine on Proxmox.",
        permission="templates_create",
        is_async=True,
        notes=[
            "The source VM must have a valid `proxmoxId` and be in `stopped` status.",
            "Creator is automatically granted `object_full` permission on the new template.",
            "`GuacamoleConnectionProfile`s linked to the source VM are automatically copied to the new template.",
            "Tags from the source VM are inherited by the new template.",
        ],
    ),
)
def create_template(
    *,
    template_in: TemplateCreate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "templates_create", request, db=db
    ).has_permission():
        return CRUDTemplate(TemplateModel).create(
            db=db, request=request, obj_in=template_in
        )
    else:
        raise PermissionDenied()


# Returns all templates
@router.get(
    "/",
    status_code=200,
    response_model=TemplateList,
    operation_id="templates_read_all",
    summary="Get Templates",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a paginated list of all templates visible to the requesting user.",
        permission="templates_read",
    ),
)
def get_templates(
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
        "templates_read", request, db=db
    ).has_permission():
        return CRUDTemplate(TemplateModel).get_multi(
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDTemplate(TemplateModel).get_multi_auth(
            request=request,
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Get template with ID
@router.get(
    "/{id}",
    status_code=200,
    response_model=Template,
    operation_id="templates_read_one",
    responses=READ_RESPONSES,
    summary="Get Template",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a single template by ID.",
        permission="templates_read",
    ),
)
def get_template(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "templates_read", request, id, db=db
    ).has_permission():
        return CRUDTemplate(TemplateModel).get(db, id)
    else:
        raise PermissionDenied()


# Update template
@router.put(
    "/{id}",
    status_code=200,
    response_model=Template,
    operation_id="templates_update",
    responses=CRUD_RESPONSES,
    summary="Update Template",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Updates template metadata and enqueues a template refresh on Proxmox.",
        permission="templates_update",
        is_async=True,
    ),
)
def update_template(
    *,
    id: UUID4,
    template_in: TemplateUpdate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "templates_update", request, id, db=db
    ).has_permission():
        # Check if template with the same name already exists
        db_name = CRUDTemplate(TemplateModel).get_by_name(
            db, name=template_in.name
        )
        if db_name and db_name.id != id:
            raise DuplicateFieldException(field="name")
        # Check if a DIFFERENT template with the same Key already exists
        updated_template = CRUDTemplate(TemplateModel).update(
            db=db, request=request, obj_in=template_in, id=id
        )
        return updated_template
    else:
        raise PermissionDenied()


# Update template's Apps
@router.put(
    "/{id}/applications",
    status_code=200,
    response_model=Template,
    operation_id="templates_apps_update",
    responses=WRITE_RESPONSES,
    summary="Update Template Apps",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Replaces the application list associated with a template.",
        permission="templates_update",
    ),
)
def update_template_apps(
    *,
    id: UUID4,
    template_in: TemplateUpdateApps,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "templates_update", request, id, db=db
    ).has_permission():
        return CRUDTemplate(TemplateModel).update_apps(
            db=db, request=request, obj_in=template_in, id=id
        )
    else:
        raise PermissionDenied()


# Delete template with ID
@router.delete(
    "/{id}",
    status_code=200,
    operation_id="templates_delete",
    responses=DELETE_RESPONSES,
    summary="Delete Template",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Deletes a template record and enqueues removal from Proxmox.",
        permission="templates_delete",
        is_async=True,
        notes=[
            "Blocked if the template has `prevent_delete` set or if PVE protection is enabled on the underlying VM.",
            "Blocked if the template is still linked to virtual machines, courses, or events.",
        ],
    ),
)
def delete_template(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "templates_delete", request, id, db=db
    ).has_permission():
        return CRUDTemplate(TemplateModel).delete(db, request, id)
    else:
        raise PermissionDenied()


# Returns all VMs with given template
@router.get(
    "/{id}/virtual-machines",
    response_model=VirtualMachineList,
    status_code=200,
    operation_id="templates_vms_read_all",
    responses=READ_RESPONSES,
    summary="Get all Virtual Machines with Template",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns all virtual machines created from this template.",
        permission="templates_read",
    ),
)
def get_template_vms(
    request: Request,
    id: UUID4,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "templates_read", request, id, db=db
    ).has_permission():
        return CRUDVirtualMachine(VirtualMachineModel).get_multi_foreign_key(
            foreign_key_field="template",
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
        return CRUDVirtualMachine(
            VirtualMachineModel
        ).get_multi_foreign_key_auth(
            request=request,
            foreign_key_field="template",
            foreign_key_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Returns a Template's apps
@router.get(
    "/{id}/applications",
    status_code=200,
    response_model=ApplicationList,
    operation_id="templates_application_read_all",
    responses=READ_RESPONSES,
    summary="Get Template's Applications",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns all applications associated with a template.",
        permission="templates_read",
    ),
)
def get_templates_apps(
    request: Request,
    id: UUID4,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "templates_read", request, id, db=db
    ).has_permission():
        return CRUDTemplate(TemplateModel).get_multi_association(
            parent_model=ApplicationModel,
            child_model=TemplateModel,
            parent_field_name="templates",
            child_field_name="id",
            field_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDTemplate(TemplateModel).get_multi_association_auth(
            request=request,
            parent_model=ApplicationModel,
            child_model=TemplateModel,
            parent_field_name="templates",
            child_field_name="id",
            field_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Returns a Template's courses
@router.get(
    "/{id}/courses",
    status_code=200,
    response_model=CourseList,
    operation_id="templates_courses_read_all",
    responses=READ_RESPONSES,
    summary="Get Template's Courses",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns all courses associated with a template.",
        permission="templates_read",
    ),
)
def get_templates_courses(
    request: Request,
    id: UUID4,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "templates_read", request, id, db=db
    ).has_permission():
        return CRUDTemplate(TemplateModel).get_multi_association(
            parent_model=CourseModel,
            child_model=TemplateModel,
            parent_field_name="templates",
            child_field_name="id",
            field_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=id,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDTemplate(TemplateModel).get_multi_association_auth(
            request=request,
            parent_model=CourseModel,
            child_model=TemplateModel,
            parent_field_name="templates",
            child_field_name="id",
            field_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )
