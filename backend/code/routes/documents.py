from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import UUID4
from sqlalchemy.orm import Session

from controllers.documents import *
from core import dependencies
from core.exceptions import DuplicateFieldException, PermissionDenied
from core.responses import CRUD_RESPONSES
from models import Document as DocumentModel
from schemas.documents import *

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses=CRUD_RESPONSES,
)


# Create new Document
@router.post(
    "/",
    status_code=201,
    response_model=Document,
    operation_id="documents_create",
    summary="Create Document",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `documents_create`",
)
def create_document(
    *,
    document_in: DocumentCreate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
):
    if dependencies.PermissionChecker(
        "documents_create", request, db=db
    ).has_permission():
        # Check if Document with the same name already exists
        db_name = CRUDDocument(DocumentModel).get_by_name(
            db, name=document_in.name
        )
        if db_name:
            raise DuplicateFieldException(field="name")
        return CRUDDocument(DocumentModel).create(
            db=db, request=request, obj_in=document_in
        )
    else:
        raise PermissionDenied()


# Upload file to Document
@router.post(
    "/{id}/upload",
    status_code=201,
    response_model=Document,
    operation_id="documents_upload",
    summary="Upload Document",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `documents_create`",
)
def upload_document(
    *,
    file: UploadFile = File(...),
    id: UUID4,
    db: Session = Depends(dependencies.get_db),
    request: Request,
):
    if dependencies.PermissionChecker(
        "documents_create", request, id, db=db
    ).has_permission():
        return CRUDDocument(DocumentModel).upload(
            db=db, request=request, id=id, file_in=file
        )
    else:
        raise PermissionDenied()


# Returns all Documents
@router.get(
    "/",
    status_code=200,
    response_model=DocumentList,
    operation_id="documents_read_all",
    summary="Get Documents",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `documents_read`",
)
def get_documents(
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
        "documents_read", request, db=db
    ).has_permission():
        return CRUDDocument(DocumentModel).get_multi(
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDDocument(DocumentModel).get_multi_auth(
            request=request,
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Get Document with ID
@router.get(
    "/{id}",
    status_code=200,
    response_model=Document,
    operation_id="documents_read_one",
    summary="Get Document",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `documents_read`",
)
def get_document(
    id: UUID4, request: Request, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "documents_read", request, id, db=db
    ).has_permission():
        return CRUDDocument(DocumentModel).get(db, id)
    else:
        raise PermissionDenied()


# Get file for Document with ID
@router.get(
    "/{id}/file",
    status_code=200,
    operation_id="documents_file_read_one",
    summary="Returns file for Document object",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `documents_read`",
)
def get_document_file(
    id: UUID4, request: Request, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "documents_read", request, id, db=db
    ).has_permission():
        document_object = CRUDDocument(DocumentModel).get(db, id)
        file_extension_start_index = document_object.path.rfind(".")
        file_extension = document_object.path[file_extension_start_index:]
        return FileResponse(
            document_object.path,
            media_type="application/octet-stream",
            filename=f"{document_object.name}{file_extension}",
        )
    else:
        raise PermissionDenied()


# Update Document
@router.put(
    "/{id}",
    status_code=200,
    response_model=Document,
    operation_id="documents_update",
    summary="Update Document",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `documents_update`",
)
def update_document(
    *,
    id: UUID4,
    document_in: DocumentUpdate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "documents_update", request, id, db=db
    ).has_permission():
        return CRUDDocument(DocumentModel).update(
            db=db, request=request, id=id, obj_in=document_in
        )
    else:
        raise PermissionDenied()


# Delete Document with ID
@router.delete(
    "/{id}",
    status_code=200,
    operation_id="documents_delete",
    summary="Delete Document",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `documents_delete`",
)
def delete_document(
    id: UUID4, request: Request, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "documents_delete", request, id, db=db
    ).has_permission():
        return CRUDDocument(DocumentModel).delete(db, id)
    else:
        raise PermissionDenied()


# Returns all Documents related to an object
@router.get(
    "/{object_type}/{object_id}",
    status_code=200,
    response_model=DocumentList,
    operation_id="documents_object_read_all",
    summary="Get all Documents for an object_id of an object_type",
    dependencies=[Depends(dependencies.get_current_user)],
    description="**Required permission:** `documents_read`",
)
def get_documents_for_object(
    object_type: str,
    object_id: UUID4,
    request: Request,
    limit: int = 100,
    page: int = 1,
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "documents_read", request, object_id, db=db
    ).has_permission():
        return CRUDDocument(DocumentModel).get_multi_for_object(
            db=db,
            limit=limit,
            page=page,
            sort_by=sort_by,
            sort_order=sort_order,
            object_type=object_type,
            object_id=object_id,
        )
    else:
        return CRUDDocument(DocumentModel).get_multi_for_object_auth(
            request=request,
            db=db,
            limit=limit,
            page=page,
            sort_by=sort_by,
            sort_order=sort_order,
            object_type=object_type,
            object_id=object_id,
        )
