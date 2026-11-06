from fastapi import APIRouter, Depends, Request
from pydantic import UUID4
from sqlalchemy.orm import Session

from controllers.apps import *
from controllers.os import *
from controllers.vendor import *
from core import dependencies
from core.exceptions import DuplicateFieldException, PermissionDenied
from core.responses import CRUD_RESPONSES
from models.apps import Application as ApplicationModel
from models.os import OS as OSModel
from models.vendor import Vendor as VendorModel
from schemas.apps import *
from schemas.os import *
from schemas.vendor import Vendor, VendorList

router = APIRouter(
    prefix="/vendors",
    tags=["vendors"],
    responses=CRUD_RESPONSES,
)


# Create new Vendor
@router.post(
    "/",
    status_code=201,
    response_model=Vendor,
    operation_id="vendors_create",
    summary="Create Vendor",
    dependencies=[Depends(dependencies.PermissionChecker())],
    description="**Required permission:** `vendors_create`",
)
def create_vendor(
    *,
    vendor_in: VendorCreate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "vendors_create", request, db=db
    ).has_permission():
        # Check if Vendor with the same name already exists
        db_name = CRUDVendor(VendorModel).get_by_name(db, name=vendor_in.name)
        if db_name:
            raise DuplicateFieldException(field="name")
        return CRUDVendor(VendorModel).create(
            db=db, request=request, obj_in=vendor_in
        )
    else:
        raise PermissionDenied()


# Returns all Vendors
@router.get(
    "/",
    status_code=200,
    response_model=VendorList,
    operation_id="vendors_read_all",
    summary="Get Vendors",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `vendors_read`",
)
def get_vendors(
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
        "vendors_read", request, db=db
    ).has_permission():
        return CRUDVendor(VendorModel).get_multi(
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDVendor(VendorModel).get_multi_auth(
            request=request,
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Get Vendor with ID
@router.get(
    "/{id}",
    status_code=200,
    response_model=Vendor,
    operation_id="vendors_read_one",
    summary="Get Vendor",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `vendors_read`",
)
def get_vendor(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "vendors_read", request, id, db=db
    ).has_permission():
        return CRUDVendor(VendorModel).get(db, id)
    else:
        raise PermissionDenied()


# Update Vendor
@router.put(
    "/{id}",
    status_code=200,
    response_model=Vendor,
    operation_id="vendors_update",
    summary="Update Vendor",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `vendors_update`",
)
def update_vendor(
    *,
    id: UUID4,
    vendor_in: VendorUpdate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "vendors_update", request, id, db=db
    ).has_permission():
        # Check if Vendor with the same name already exists
        db_name = CRUDVendor(VendorModel).get_by_name(db, name=vendor_in.name)
        if db_name and db_name.id != id:
            raise DuplicateFieldException(field="name")
        return CRUDVendor(VendorModel).update(
            db=db, request=request, id=id, obj_in=vendor_in
        )
    else:
        raise PermissionDenied()


# Delete Vendor with ID
@router.delete(
    "/{id}",
    status_code=200,
    operation_id="vendors_delete",
    summary="Delete Vendor",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `vendors_delete`",
)
def delete_vendor(
    id: UUID4, request: Request, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "vendors_delete", request, id, db=db
    ).has_permission():
        return CRUDVendor(VendorModel).delete(db, id)
    else:
        raise PermissionDenied()


# Returns all OS with given vendor
@router.get(
    "/{id}/operating-systems",
    response_model=OSList,
    status_code=200,
    operation_id="vendors_os_read_all",
    summary="Get all OS with Vendor",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `vendors_read`",
)
def get_vendor_os(
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
        "vendors_read", request, id, db=db
    ).has_permission():
        return CRUDOperatingSystem(OSModel).get_multi_foreign_key(
            foreign_key_field="vendor",
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
        return CRUDOperatingSystem(OSModel).get_multi_foreign_key_auth(
            request=request,
            foreign_key_field="vendor",
            foreign_key_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Returns all Apps with given vendor
@router.get(
    "/{id}/applications",
    response_model=ApplicationList,
    status_code=200,
    operation_id="vendors_apps_read_all",
    summary="Get all Applications with Vendor",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `vendors_read`",
)
def get_vendor_apps(
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
        "vendors_read", request, id, db=db
    ).has_permission():
        return CRUDApplication(ApplicationModel).get_multi_foreign_key(
            foreign_key_field="vendor",
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
        return CRUDApplication(ApplicationModel).get_multi_foreign_key_auth(
            request=request,
            foreign_key_field="vendor",
            foreign_key_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )
