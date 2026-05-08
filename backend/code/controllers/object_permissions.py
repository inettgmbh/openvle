import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from pydantic import UUID4
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.config import Settings
from core.core_utils import get_system_user
from core.exceptions import (
    DuplicateObjectPermission,
    InvalidFieldValue,
    ModelNotFound,
    ObjectDeleteIntegrityError,
    ObjectNotFound,
    ProtectedObjectError,
)
from core.pagination import paginate
from middlewares.i18n import _
from models import Changelog, ObjectPermission, User
from schemas.object_permissions import (
    LEGACY_PERMISSION_CONSTRAINTS,
    ObjectPermissionCreate,
)

from .base import CRUDBase

settings = Settings()


class CRUDObjectPermission(
    CRUDBase[ObjectPermission, ObjectPermissionCreate, ObjectPermissionCreate]
):
    # fixme: merge into a central function

    # Create object_full ObjectPermission for User
    def create_full(
        self,
        db: Session,
        request: Request,
        object_type: str,
        object_id: Any,
        user_id: Any = None,
    ) -> ObjectPermission:
        user_id = user_id or get_system_user().id
        db_obj_perm_dict = {
            "object_id": object_id,
            "object_type": object_type,
            "entity_id": user_id,
            "entity_type": "User",
            "permission_key": "object_full",
        }
        db_obj_perm = ObjectPermission(**db_obj_perm_dict)
        db_obj_perm.id = uuid.uuid4()
        db_obj_perm.createdAt = datetime.now(timezone.utc)
        db_obj_perm.updatedAt = datetime.now(timezone.utc)
        if request:
            db_obj_perm.createdById = request.user.id
            db_obj_perm.updatedById = request.user.id
        else:
            db_obj_perm.createdById = get_system_user(db).id
            db_obj_perm.updatedById = get_system_user(db).id
        db_obj_perm = self._commit(db, db_obj_perm)
        return db_obj_perm

    # Create object_reset ObjectPermission for User
    def create_reset(
        self,
        db: Session,
        request: Request,
        object_type: str,
        object_id: Any,
        user_id: Any = None,
    ) -> ObjectPermission:
        db_obj_perm_dict = {
            "object_id": object_id,
            "object_type": object_type,
            "entity_id": request.user.id if user_id is None else user_id,
            "entity_type": "User",
            "permission_key": "object_reset",
        }
        db_obj_perm = ObjectPermission(**db_obj_perm_dict)
        db_obj_perm.id = uuid.uuid4()
        db_obj_perm.createdAt = datetime.now(timezone.utc)
        db_obj_perm.updatedAt = datetime.now(timezone.utc)
        if request:
            db_obj_perm.createdById = request.user.id
            db_obj_perm.updatedById = request.user.id
        else:
            db_obj_perm.createdById = get_system_user(db).id
            db_obj_perm.updatedById = get_system_user(db).id
        db_obj_perm = self._commit(db, db_obj_perm)
        return db_obj_perm

    # Create ObjectPermission
    def create(
        self, db: Session, request: Request, *, obj_in: ObjectPermissionCreate
    ) -> ObjectPermission:
        obj_in_data = jsonable_encoder(obj_in)
        self._initialize_object_fields(
            db=db,
            obj_data_in=obj_in_data,
            request=request,
            model_type=ObjectPermission,
        )
        # Validate entity_type
        if obj_in.entity_type not in ["User", "Role"]:
            raise InvalidFieldValue(
                field="entity_type", value=obj_in.entity_type
            )
        module = __import__("models", fromlist=f"{obj_in.object_type}")
        # Check if entity exists
        entity_model = getattr(module, obj_in.entity_type)
        entity = db.get(entity_model, obj_in.entity_id)
        if not entity:
            raise ObjectNotFound(
                id=obj_in.entity_id, model_name=obj_in.entity_type
            )
        # Prevent system roles from being assigned
        if entity_model.__name__ == "Role" and entity.protected:
            raise ProtectedObjectError(
                model_name=entity_model.__name__,
                operation="object_permission_create",
            )
        self.db_obj.entity_id = obj_in.entity_id

        # Check if object_type model exists and is valid
        NON_MODEL_OBJECT_TYPES = [
            "Activity",
            "Dashboard",
            "Moodle",
            "Proxmox",
            "System",
        ]

        if obj_in.object_type in NON_MODEL_OBJECT_TYPES:
            # object_types that are NOT SQL Alchemy models that are still valid
            pass
        else:
            # Standard model-based object_type
            try:
                object_model = getattr(module, obj_in.object_type)
                if object_model and not object_model.__tablename__:
                    raise InvalidFieldValue(
                        field="object_type", value=obj_in.object_type
                    )
            except AttributeError:
                raise ModelNotFound(model_name=obj_in.object_type)

            # Check if specific object exists (if object_id provided)
            if getattr(obj_in, "object_id", None) is not None:
                db_object = db.get(object_model, obj_in.object_id)
                if not db_object:
                    raise ObjectNotFound(
                        id=obj_in.object_id, model_name=obj_in.object_type
                    )
                self.db_obj.object_id = obj_in.object_id

        # Rule 1: Check for exact duplicate ObjectPermission
        existing_exact = (
            db.query(ObjectPermission)
            .filter(
                ObjectPermission.object_type == obj_in.object_type,
                ObjectPermission.object_id == obj_in.object_id,
                ObjectPermission.entity_type == obj_in.entity_type,
                ObjectPermission.entity_id == obj_in.entity_id,
                ObjectPermission.permission_key == obj_in.permission_key,
            )
            .first()
        )
        if existing_exact:
            raise DuplicateObjectPermission(
                message=_(
                    "An ObjectPermission with this exact combination"
                    " already exists."
                )
            )

        # Special permissions that can coexist with CRUD permissions
        SPECIAL_PERMISSIONS = list(LEGACY_PERMISSION_CONSTRAINTS.keys())

        # Basic CRUD permissions (excluding object_create which has special rules)
        BASIC_CRUD_PERMISSIONS = [
            "object_full",
            "object_read",
            "object_update",
            "object_delete",
        ]

        # Rule 2: Check existing permissions for the same object_type/object_id/entity combination
        existing_for_object = (
            db.query(ObjectPermission)
            .filter(
                ObjectPermission.object_type == obj_in.object_type,
                ObjectPermission.object_id == obj_in.object_id,
                ObjectPermission.entity_type == obj_in.entity_type,
                ObjectPermission.entity_id == obj_in.entity_id,
            )
            .all()
        )

        if existing_for_object:
            new_is_special = obj_in.permission_key in SPECIAL_PERMISSIONS
            new_is_create = obj_in.permission_key == "object_create"
            new_is_basic_crud = obj_in.permission_key in BASIC_CRUD_PERMISSIONS

            if new_is_special:
                # SPECIAL PERMISSIONS: Check for duplicate special permission only
                existing_special_keys = [
                    p.permission_key
                    for p in existing_for_object
                    if p.permission_key in SPECIAL_PERMISSIONS
                ]
                if obj_in.permission_key in existing_special_keys:
                    raise DuplicateObjectPermission(
                        message=_(
                            "The ObjectPermission"
                            " '{permission_key}' already"
                            " exists for this object."
                        ).format(permission_key=obj_in.permission_key)
                    )
                # Special permissions can always be added (unlimited) - allow creation

            elif new_is_create:
                # OBJECT_CREATE: Can only be added if no other object_create exists
                # object_create can coexist with one other BASIC CRUD permission
                existing_has_create = any(
                    p.permission_key == "object_create"
                    for p in existing_for_object
                )

                if existing_has_create:
                    raise DuplicateObjectPermission(
                        message=_(
                            "An 'object_create' permission"
                            " already exists for this object."
                        )
                    )

                # Check if there's already a basic CRUD permission (object_create can coexist with ONE)
                existing_basic_crud = [
                    p
                    for p in existing_for_object
                    if p.permission_key in BASIC_CRUD_PERMISSIONS
                ]
                if len(existing_basic_crud) > 1:
                    raise DuplicateObjectPermission(
                        message=_(
                            "Cannot add 'object_create' when"
                            " multiple CRUD permissions"
                            " already exist. Only one CRUD"
                            " permission can coexist with"
                            " object_create."
                        )
                    )

            elif new_is_basic_crud:
                # BASIC CRUD PERMISSIONS: Check constraints
                existing_has_create = any(
                    p.permission_key == "object_create"
                    for p in existing_for_object
                )
                existing_basic_crud = [
                    p
                    for p in existing_for_object
                    if p.permission_key in BASIC_CRUD_PERMISSIONS
                ]

                if existing_has_create:
                    # If object_create exists, can add ONE basic CRUD permission
                    if len(existing_basic_crud) >= 1:
                        raise DuplicateObjectPermission(
                            message=_(
                                "Cannot add another CRUD"
                                " permission. When"
                                " 'object_create' exists,"
                                " only one other CRUD"
                                " permission is allowed."
                            )
                        )
                    # Allow: adding first CRUD permission alongside object_create
                # If no object_create, can only have ONE basic CRUD permission total
                elif len(existing_basic_crud) >= 1:
                    entity_type_display = obj_in.entity_type
                    object_display = (
                        f"object_id={obj_in.object_id}"
                        if obj_in.object_id
                        else "global (object_id=null)"
                    )

                    raise DuplicateObjectPermission(
                        message=_(
                            "The {entity_type} already has"
                            " a CRUD permission for"
                            " {object_type}"
                            " ({object_display}). Only one"
                            " CRUD permission per object"
                            " is allowed, except when"
                            " combining object_create with"
                            " one other CRUD permission."
                        ).format(
                            entity_type=entity_type_display,
                            object_type=obj_in.object_type,
                            object_display=object_display,
                        )
                    )
        self.db_obj = self._commit(db, self.db_obj)
        # Create Changelog for assigned entity for new ObjectPermission
        perm_dict = {
            "object_type": self.db_obj.object_type,
            "object_id": str(self.db_obj.object_id)
            if obj_in.object_id
            else None,
            "permission_key": self.db_obj.permission_key,
        }
        value_new = json.dumps({"permissions": [perm_dict]})

        new_changelog = Changelog(
            id=uuid.uuid4(),
            timestamp=datetime.now(timezone.utc),
            valueOld=json.dumps({"permissions": []}),
            valueNew=value_new,
            object=self.db_obj.entity_type,
            objectId=self.db_obj.entity_id,
            userId=request.user.id,
        )
        db.add(new_changelog)
        self._commit(db)
        return self.db_obj

    # Get all ObjectPermission for object_type and object_id (including global permissions for that type)
    def get_multi_type_id(
        self,
        object_type: str,
        object_id: UUID4,
        db: Session,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
        search_field: str = "",
        search_value: str = "",
    ) -> list[ObjectPermission] | None:
        self._get_multi_init(limit=limit, page=page, sort_by=sort_by)
        # Build query to get both object-specific AND global permissions for this object_type
        model_query = db.query(ObjectPermission).filter(
            ObjectPermission.object_type == object_type,
            (
                (ObjectPermission.object_id == object_id)
                | (ObjectPermission.object_id.is_(None))
            ),
            ObjectPermission.permission_key != "object_create",
        )
        model_query = self._model_query_search(
            model_query, search_field=search_field, search_value=search_value
        )
        model_query_sorted = self._model_query_sort(
            model_query, sort_by=sort_by, sort_order=sort_order, limit=limit
        )
        model_query_count = model_query.count()
        # return Paginated list of objects
        return paginate(
            object_list=list(model_query_sorted),
            object_query_count=model_query_count,
            current_page=page,
            limit=limit,
        )

    # Get all ObjectPermission for object_type and object_id belonging to request User (including global permissions and Role permissions)
    def get_multi_type_id_auth(
        self,
        request: Request,
        object_type: str,
        object_id: UUID4,
        db: Session,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
        search_field: str = "",
        search_value: str = "",
    ) -> list[ObjectPermission] | None:
        self._get_multi_init(limit=limit, page=page, sort_by=sort_by)

        # Get user's roles
        user = db.get(User, request.user.id)
        user_role_ids = (
            [role.id for role in user.roles] if user and user.roles else []
        )

        # Build query
        model_query = db.query(ObjectPermission).filter(
            ObjectPermission.object_type == object_type,
            (
                (ObjectPermission.object_id == object_id)
                | (ObjectPermission.object_id.is_(None))
            ),
            ObjectPermission.permission_key != "object_create",
            (
                # User's own permissions
                (
                    (ObjectPermission.entity_type == "User")
                    & (ObjectPermission.entity_id == request.user.id)
                )
                |
                # Role permissions (if user has roles)
                (
                    (ObjectPermission.entity_type == "Role")
                    & (ObjectPermission.entity_id.in_(user_role_ids))
                )
                if user_role_ids
                else False
            ),
        )

        model_query = self._model_query_search(
            model_query, search_field=search_field, search_value=search_value
        )
        model_query_sorted = self._model_query_sort(
            model_query, sort_by=sort_by, sort_order=sort_order, limit=limit
        )
        model_query_count = model_query.count()
        # return Paginated list of objects
        return paginate(
            object_list=list(model_query_sorted),
            object_query_count=model_query_count,
            current_page=page,
            limit=limit,
        )

    # Delete ObjectPermission
    def delete(self, db: Session, id: Any, request: Request) -> dict:
        self.db_obj = self.get(db, id)

        # Store information needed for Changelog before deletion
        entity_type = self.db_obj.entity_type
        entity_id = self.db_obj.entity_id
        object_type = self.db_obj.object_type
        object_id = self.db_obj.object_id
        permission_key = self.db_obj.permission_key

        try:
            db.delete(self.db_obj)

            # Create Changelog for the entity that had the permission removed
            perm_dict = {
                "object_type": object_type,
                "object_id": str(object_id) if object_id else None,
                "permission_key": permission_key,
            }
            value_old = json.dumps({"permissions": [perm_dict]})

            new_changelog = Changelog(
                id=uuid.uuid4(),
                timestamp=datetime.now(timezone.utc),
                valueOld=value_old,
                valueNew=json.dumps({"permissions": []}),
                object=entity_type,
                objectId=entity_id,
                userId=request.user.id,
            )
            db.add(new_changelog)

            self._commit(db)
            self.db_obj = None

            return {
                "detail": _("{model} with ID {id} has been deleted.").format(
                    model=self.model.__name__, id=id
                )
            }
        except IntegrityError:
            raise ObjectDeleteIntegrityError(model_name=self.model.__name__)


permission = CRUDObjectPermission(ObjectPermission)
