from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from core.config import Settings
from core.exceptions import RequiredParameterMissingError
from models import Application, Document, ObjectPermission, Vendor
from schemas.apps import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationUpdateDocuments,
)

from .base import CRUDBase
from .object_permissions import CRUDObjectPermission

settings = Settings()


class CRUDApplication(
    CRUDBase[Application, ApplicationCreate, ApplicationUpdate]
):
    # Get Application by key
    def get_by_key(self, db: Session, *, key: str) -> Application | None:
        app = db.query(Application).filter(Application.key == key).first()
        return app

    # Create Application
    def create(
        self, db: Session, request: Request, *, obj_in: ApplicationCreate
    ) -> Application | None:
        obj_in_data = jsonable_encoder(obj_in)
        self._initialize_object_fields(
            db=db, obj_data_in=obj_in_data, request=request
        )
        new_vendor = CRUDBase(Vendor).get(db, obj_in.vendor)
        self.db_obj.vendor = new_vendor.id
        self.db_obj = self._commit(db, self.db_obj)
        CRUDObjectPermission(ObjectPermission).create_full(
            db, request, "Application", self.db_obj.id, request.user.id
        )
        db.refresh(self.db_obj)
        return self.db_obj

    # Update Application
    def update(
        self,
        id: Any,
        db: Session,
        request: Request,
        *,
        obj_in: ApplicationUpdate,
    ) -> Application | None:
        # Check if object exists before attempting update
        self.db_obj = self.get(db, id)
        obj_data = jsonable_encoder(self.db_obj)
        update_data = self._merge_request_with_db_object(obj_in, obj_data)
        # Vendor handling
        if "vendor" in update_data:
            new_vendor = CRUDBase(Vendor).get(db=db, id=obj_in.vendor)
            self.db_obj.vendor = new_vendor.id
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    # Update Application documents
    def update_documents(
        self,
        id: Any,
        db: Session,
        request: Request,
        *,
        obj_in: ApplicationUpdateDocuments,
    ) -> Application:
        self.db_obj = self.get(db, id)
        obj_data = jsonable_encoder(self.db_obj)
        update_data = self._merge_request_with_db_object(obj_in, obj_data)
        # Handling of documents
        if "documents" not in update_data:
            raise RequiredParameterMissingError(parameter_name="documents")
        existing_documents = self.db_obj.documents
        documents_list = []
        for document in update_data["documents"]:
            new_document = CRUDBase(Document).get(db, document["id"])
            documents_list.append(new_document)
        self.db_obj.documents = existing_documents + documents_list
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    # Set Application documents
    def set_documents(
        self,
        id: Any,
        db: Session,
        request: Request,
        *,
        obj_in: ApplicationUpdateDocuments,
    ) -> Application:
        self.db_obj = self.get(db, id)
        obj_data = jsonable_encoder(self.db_obj)
        update_data = self._merge_request_with_db_object(obj_in, obj_data)
        # Handling of documents
        if "documents" not in update_data:
            raise RequiredParameterMissingError(parameter_name="documents")
        documents_list = []
        for document in update_data["documents"]:
            new_document = CRUDBase(Document).get(db=db, id=document["id"])
            documents_list.append(new_document)
        self.db_obj.documents = documents_list
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj


application = CRUDApplication(Application)
