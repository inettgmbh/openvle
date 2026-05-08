import os
from typing import Any, List, Optional

from fastapi import Request, UploadFile
from pydantic import UUID4
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.exceptions import (
    BadRequestError,
    FileUploadError,
    InvalidFieldValue,
    ModelAssociationNotFound,
    ModelFieldNotFound,
    ModelNotFound,
    ObjectDeleteIntegrityError,
    ObjectNotFound,
    PaginationLimitError,
    PaginationZeroPageError,
    UnsupportedFileType,
)
from core.pagination import paginate
from middlewares.i18n import _
from models import OS, Application, Changelog, Document, ObjectPermission, Tag
from schemas.documents import DocumentCreate, allowed_mime_types

from .base import CRUDBase, build_object_permission_filter


class CRUDDocument(CRUDBase[Document, DocumentCreate, DocumentCreate]):
    # Get Document by name
    def get_by_name(self, db: Session, *, name: str) -> Document | None:
        return db.query(Document).filter(Document.name == name).first()

    # Upload document
    # TODO: Controller and endpoint soon to be deprecated KVS-484
    def upload(
        self, id: Any, db: Session, request: Request, *, file_in: UploadFile
    ) -> Document | None:
        self.db_obj = self.get(db, id)
        if request.user.id != self.db_obj.createdById:
            raise BadRequestError(
                message=_(
                    "Only the creator of the document object may upload the associated file."
                )
            )
        # Check if file already exists for document object
        if self.db_obj.path:
            raise BadRequestError(
                message=_("A file is already assigned to document object.")
            )
        # Check if MIME/Media type is supported/allowed
        if file_in.content_type not in allowed_mime_types:
            raise UnsupportedFileType(content_type=file_in.content_type)
        # File handling
        try:
            contents = file_in.file.read()
            file_extension_start_index = file_in.filename.rfind(".")
            file_extension = file_in.filename[file_extension_start_index:]
            file_path = f"./tmp/f{self.db_obj.id!s}{file_extension}"
            with open(file_path, "wb") as f:
                f.write(contents)
        except Exception:
            raise FileUploadError()
        finally:
            file_in.file.close()
        self.db_obj.path = file_path
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    # Delete object with ID
    def delete(self, db: Session, id: Any) -> Document | None:
        self.db_obj = self.get(db, id)
        try:
            db.delete(self.db_obj)
            # Delete associated file if one exists
            if os.path.exists(self.db_obj.path):
                os.remove(self.db_obj.path)
            # Delete existing changelogs
            changelogs = db.query(Changelog).filter(
                Changelog.objectId == id,
                Changelog.object == self.model.__name__,
            )
            for changelog in changelogs:
                db.delete(changelog)
            object_permissions = db.query(ObjectPermission).filter(
                ObjectPermission.object_id == id,
                ObjectPermission.object_type == self.model.__name__,
            )
            if object_permissions:
                for perm in object_permissions:
                    db.delete(perm)
            tags = db.query(Tag).filter(
                Tag.objectId == id, Tag.objectType == self.model.__name__
            )
            for tag in tags:
                db.delete(tag)
            self._commit(db)
            self.db_obj = None
            return {
                "detail": f"{self.model.__name__} with ID {id} has been deleted."
            }
        except IntegrityError:
            raise ObjectDeleteIntegrityError(model_name=self.model.__name__)

    # Get multiple all documents for object_id and object_type
    def get_multi_for_object(
        self,
        object_type: str,
        object_id: UUID4,
        db: Session,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
    ) -> list[Document] | None:
        self._get_multi_init(limit=limit, page=page, sort_by=sort_by)
        # Get model for object_type
        try:
            module = __import__("models", fromlist=f"{object_type}")
            object_model = getattr(module, object_type)
            if object_model and not object_model.__tablename__:
                raise InvalidFieldValue(field="object_type", value=object_type)
        except AttributeError:
            raise ModelNotFound(model_name=object_type)
        # Build query according to object_type
        if object_type == "Application":
            app_obj = db.get(Application, object_id)
            if not app_obj:
                raise ObjectNotFound(
                    id=object_id, model_name=Application.__name__
                )
            query_prefix = db.query(Document).join(Document.apps)
        elif object_type == "OS":
            os_obj = db.get(OS, object_id)
            if not os_obj:
                raise ObjectNotFound(id=object_id, model_name=OS.__name__)
            query_prefix = (
                db.query(Document)
                .join(Document.os)
                .filter(object_model.id == object_id)
            )
        else:
            raise ModelAssociationNotFound(
                parent_model=Document.__name__, child_model=object_type
            )
        model_query_sorted = self._model_query_sort(
            query_prefix, sort_by=sort_by, sort_order=sort_order, limit=limit
        )
        model_query_count = query_prefix.count()

        # return Paginated list of objects
        return paginate(
            object_list=list(model_query_sorted),
            object_query_count=model_query_count,
            current_page=page,
            limit=limit,
        )

    # Get multiple all documents for object_id and object_type that a user is authorised to view based on ObjectPermissions
    def get_multi_for_object_auth(
        self,
        request: Request,
        object_type: str,
        object_id: UUID4,
        db: Session,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
    ) -> list[Document] | None:
        self._get_multi_init(limit=limit, page=page, sort_by=sort_by)
        # Get model for object_type
        try:
            module = __import__("models", fromlist=f"{object_type}")
            object_model = getattr(module, object_type)
            if object_model and not object_model.__tablename__:
                raise InvalidFieldValue(field="object_type", value=object_type)
        except AttributeError:
            raise ModelNotFound(model_name=object_type)
        perm_filter = build_object_permission_filter(
            db, Document, request.user.id
        )
        if object_type == "Application":
            app_obj = db.get(Application, object_id)
            if not app_obj:
                raise ObjectNotFound(
                    id=object_id, model_name=Application.__name__
                )
            query_prefix = (
                db.query(Document)
                .join(Document.apps)
                .filter(object_model.id == object_id)
                .filter(perm_filter)
            )
        elif object_type == "OS":
            os_obj = db.get(OS, object_id)
            if not os_obj:
                raise ObjectNotFound(id=object_id, model_name=OS.__name__)
            query_prefix = (
                db.query(Document)
                .join(Document.os)
                .filter(object_model.id == object_id)
                .filter(perm_filter)
            )
        else:
            raise ModelAssociationNotFound(
                parent_model=Document.__name__, child_model=object_type
            )
        model_query_sorted = self._model_query_sort(
            query_prefix, sort_by=sort_by, sort_order=sort_order, limit=limit
        )
        model_query_count = query_prefix.count()

        # return Paginated list of objects
        return paginate(
            object_list=list(model_query_sorted),
            object_query_count=model_query_count,
            current_page=page,
            limit=limit,
        )


document = CRUDDocument(Document)
