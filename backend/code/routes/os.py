from fastapi import APIRouter, Depends, Request
from pydantic import UUID4
from sqlalchemy.orm import Session

from controllers.os import *
from controllers.templates import *
from controllers.virtual_machines import *
from core import dependencies
from core.exceptions import DuplicateFieldException, PermissionDenied
from core.responses import CRUD_RESPONSES
from models.os import OS as OSModel
from models.templates import Template as TemplateModel
from models.virtual_machines import VirtualMachine as VirtualMachineModel
from schemas.os import *
from schemas.templates import TemplateList
from schemas.virtual_machines import VirtualMachineList

router = APIRouter(
    prefix="/os",
    tags=["os"],
    responses=CRUD_RESPONSES,
)


# Create new Operating System
@router.post(
    "/",
    status_code=201,
    response_model=OS,
    operation_id="os_create",
    summary="Create Operating System",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `os_create`",
)
def create_operating_system(
    *,
    os_in: OSCreate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "os_create", request, db=db
    ).has_permission():
        # Check if OS with the same name already exists
        db_name = CRUDOperatingSystem(OSModel).get_by_name(db, name=os_in.name)
        if db_name:
            raise DuplicateFieldException(field="name")
        # Check if OS with the same name already exists
        db_key = CRUDOperatingSystem(OSModel).get_by_key(db, key=os_in.key)
        if db_key:
            raise DuplicateFieldException(field="key")
        return CRUDOperatingSystem(OSModel).create(
            db=db, request=request, obj_in=os_in
        )
    else:
        raise PermissionDenied()


# Returns all Operating Systems
@router.get(
    "/",
    status_code=200,
    response_model=OSList,
    operation_id="os_read_all",
    summary="Get Operating Systems",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `os_read`",
)
def get_operating_systems(
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
        "os_read", request, db=db
    ).has_permission():
        return CRUDOperatingSystem(OSModel).get_multi(
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDOperatingSystem(OSModel).get_multi_auth(
            request=request,
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Get Operating System with ID
@router.get(
    "/{id}",
    status_code=200,
    response_model=OS,
    operation_id="os_read_one",
    summary="Get Operating System",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `os_read`",
)
def get_operating_system(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "os_read", request, id, db=db
    ).has_permission():
        return CRUDOperatingSystem(OSModel).get(db, id)
    else:
        raise PermissionDenied()


# Update Operating System
@router.put(
    "/{id}",
    status_code=200,
    response_model=OS,
    operation_id="os_update",
    summary="Update Operating System",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `os_update`",
)
def update_operating_system(
    *,
    id: UUID4,
    os_in: OSUpdate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "os_update", request, id, db=db
    ).has_permission():
        # Check if OS with the same name already exists
        db_name = CRUDOperatingSystem(OSModel).get_by_name(db, name=os_in.name)
        if db_name and db_name.id != id:
            raise DuplicateFieldException(field="name")
        # Check if a DIFFERENT permission with the same Key already exists
        return CRUDOperatingSystem(OSModel).update(
            db=db, request=request, obj_in=os_in, id=id
        )
    else:
        raise PermissionDenied()


# Delete OS with ID
@router.delete(
    "/{id}",
    status_code=200,
    operation_id="os_delete",
    summary="Delete Operating System",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `os_delete`",
)
def delete_operating_system(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "os_delete", request, id, db=db
    ).has_permission():
        return CRUDOperatingSystem(OSModel).delete(db, id)
    else:
        raise PermissionDenied()


# Returns all Templates with given OS
@router.get(
    "/{id}/templates",
    response_model=TemplateList,
    status_code=200,
    operation_id="os_templates_read_all",
    summary="Get all Templates with OS",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `os_read`",
)
def get_operating_system_template(
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
        "os_read", request, id, db=db
    ).has_permission():
        return CRUDBase(TemplateModel).get_multi_foreign_key(
            foreign_key_field="os",
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
        return CRUDBase(TemplateModel).get_multi_foreign_key_auth(
            request=request,
            foreign_key_field="os",
            foreign_key_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Returns all VMs with given OS
@router.get(
    "/{id}/virtual-machines",
    response_model=VirtualMachineList,
    status_code=200,
    operation_id="os_vms_read_all",
    summary="Get all Virtual Machines with OS",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `os_read`",
)
def get_operating_system_vms(
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
        "os_read", request, id, db=db
    ).has_permission():
        return CRUDBase(VirtualMachineModel).get_multi_foreign_key(
            foreign_key_field="os",
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
        return CRUDBase(VirtualMachineModel).get_multi_foreign_key_auth(
            request=request,
            foreign_key_field="os",
            foreign_key_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Update OS documents
@router.post(
    "/{id}/documents",
    status_code=200,
    response_model=OS,
    operation_id="os_documents_update",
    summary="Add documents to OS",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `os_update`",
)
def update_os_documents(
    *,
    id: UUID4,
    app_in: OSUpdateDocuments,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "os_update", request, id, db=db
    ).has_permission():
        return CRUDOperatingSystem(OSModel).update_documents(
            db=db, request=request, obj_in=app_in, id=id
        )
    else:
        raise PermissionDenied()


# Set documents for OS
@router.put(
    "/{id}/documents",
    status_code=200,
    response_model=OS,
    operation_id="os_documents_set",
    summary="Set documents for OS",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `os_update`",
)
def set_os_documents(
    *,
    id: UUID4,
    obj_in: OSUpdateDocuments,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "os_update", request, id, db=db
    ).has_permission():
        return CRUDOperatingSystem(OSModel).set_documents(
            db=db, request=request, obj_in=obj_in, id=id
        )
    else:
        raise PermissionDenied()
