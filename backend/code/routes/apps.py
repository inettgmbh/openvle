from fastapi import APIRouter, Depends, Request
from pydantic import UUID4
from sqlalchemy.orm import Session

from controllers.apps import *
from core import dependencies
from core.exceptions import DuplicateFieldException, PermissionDenied
from models import (
    Application as ApplicationModel,
    Template as TemplateModel,
    VirtualMachine as VirtualMachineModel,
)
from schemas.apps import *
from schemas.templates import TemplateList
from schemas.virtual_machines import VirtualMachineList

router = APIRouter(
    prefix="/applications",
    tags=["applications"],
    responses={404: {"detail": "Not found"}},
)


# Create new application
@router.post(
    "/",
    status_code=201,
    response_model=Application,
    operation_id="applications_create",
    summary="Create Application",
    dependencies=[Depends(dependencies.get_current_user)],
)
def create_application(
    *,
    application_in: ApplicationCreate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "applications_create", request, db=db
    ).has_permission():
        # Check if application with the same Key already exists
        db_key = CRUDApplication(ApplicationModel).get_by_key(
            db, key=application_in.key
        )
        if db_key:
            raise DuplicateFieldException(field="key")
        return CRUDApplication(ApplicationModel).create(
            db=db, request=request, obj_in=application_in
        )
    else:
        raise PermissionDenied()


# Returns all applications
@router.get(
    "/",
    status_code=200,
    response_model=ApplicationList,
    operation_id="applications_read_all",
    summary="Get Applications",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_applications(
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
        "applications_read", request, db=db
    ).has_permission():
        return CRUDApplication(ApplicationModel).get_multi(
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDApplication(ApplicationModel).get_multi_auth(
            request=request,
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Get application with ID
@router.get(
    "/{id}",
    status_code=200,
    response_model=Application,
    operation_id="applications_read_one",
    summary="Get Application",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_application(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "applications_read", request, id, db=db
    ).has_permission():
        return CRUDApplication(ApplicationModel).get(db, id)
    else:
        raise PermissionDenied()


# Update application
@router.put(
    "/{id}",
    status_code=200,
    response_model=Application,
    operation_id="applications_update",
    summary="Update Application",
    dependencies=[Depends(dependencies.get_current_user)],
)
def update_application(
    *,
    id: UUID4,
    application_in: ApplicationUpdate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "applications_update", request, id, db=db
    ).has_permission():
        return CRUDApplication(ApplicationModel).update(
            db=db, request=request, obj_in=application_in, id=id
        )
    else:
        raise PermissionDenied()


# Delete application with ID
@router.delete(
    "/{id}",
    status_code=200,
    operation_id="applications_delete",
    summary="Delete Application",
    dependencies=[Depends(dependencies.get_current_user)],
)
def delete_application(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "applications_delete", request, id, db=db
    ).has_permission():
        return CRUDApplication(ApplicationModel).delete(db, id)
    else:
        raise PermissionDenied()


# Returns Templates associated with Application
@router.get(
    "/{id}/templates",
    status_code=200,
    response_model=TemplateList,
    operation_id="application_templates_read_all",
    summary="Get Application's Templates ",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_apps_templates(
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
        "applications_read", request, id, db=db
    ).has_permission():
        return CRUDApplication(ApplicationModel).get_multi_association(
            parent_model=TemplateModel,
            child_model=ApplicationModel,
            parent_field_name="apps",
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
        return CRUDApplication(ApplicationModel).get_multi_association_auth(
            request=request,
            parent_model=TemplateModel,
            child_model=ApplicationModel,
            parent_field_name="apps",
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


# Returns VirtualMachines associated with Application
@router.get(
    "/{id}/virtual-machines",
    status_code=200,
    response_model=VirtualMachineList,
    operation_id="application_virtual_machines_read_all",
    summary="Get Application's VirtualMachines",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_apps_vms(
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
        "applications_read", request, id, db=db
    ).has_permission():
        return CRUDApplication(ApplicationModel).get_multi_association(
            parent_model=VirtualMachineModel,
            child_model=ApplicationModel,
            parent_field_name="apps",
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
        return CRUDApplication(ApplicationModel).get_multi_association_auth(
            request=request,
            parent_model=VirtualMachineModel,
            child_model=ApplicationModel,
            parent_field_name="apps",
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


# Update Application documents
@router.post(
    "/{id}/documents",
    status_code=200,
    response_model=Application,
    operation_id="applications_documents_update",
    summary="Add documents to application",
    dependencies=[Depends(dependencies.get_current_user)],
)
def update_app_documents(
    *,
    id: UUID4,
    app_in: ApplicationUpdateDocuments,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "applications_update", request, id, db=db
    ).has_permission():
        return CRUDApplication(ApplicationModel).update_documents(
            db=db, request=request, obj_in=app_in, id=id
        )
    else:
        raise PermissionDenied()


# Set Application documents
@router.put(
    "/{id}/documents",
    status_code=200,
    response_model=Application,
    operation_id="applications_documents_set",
    summary="Set documents for application",
    dependencies=[Depends(dependencies.get_current_user)],
)
def set_app_documents(
    *,
    id: UUID4,
    obj_in: ApplicationUpdateDocuments,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "applications_update", request, id, db=db
    ).has_permission():
        return CRUDApplication(ApplicationModel).set_documents(
            db=db, request=request, obj_in=obj_in, id=id
        )
    else:
        raise PermissionDenied()
