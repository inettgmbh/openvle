from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.config import Settings
from core.core_utils import get_system_user
from core.exceptions import (
    ObjectDeleteIntegrityError,
    ObjectNotFound,
    ProtectedObjectError,
    RequiredParameterMissingError,
)
from core.pagination import paginate
from middlewares.i18n import _
from models import Changelog, ObjectPermission, Role, Tag, User
from models.associations import user_role_association_table
from schemas.roles import (
    RoleCreate,
    RoleUpdate,
    RoleUpdateObjectPermissions,
)

from .base import CRUDBase

settings = Settings()


class CRUDRole(CRUDBase[Role, RoleCreate, RoleUpdate]):
    # Get role by name
    def get_by_name(self, db: Session, *, name: str) -> Role | None:
        role = db.query(Role).filter(Role.name == name).first()
        return role

    # Get role by key
    def get_by_key(self, db: Session, *, key: str) -> Role | None:
        role = db.query(Role).filter(Role.key == key).first()
        return role

    def set_object_permissions(
        self,
        id: Any,
        db: Session,
        request: Request,
        *,
        obj_in: RoleUpdateObjectPermissions,
    ) -> Role:
        self.db_obj = self.get(db, id)

        if not obj_in.object_permissions:
            raise RequiredParameterMissingError(
                parameter_name="object_permissions"
            )

        # Batch-fetch all ObjectPermissions by ID
        perms_by_id = {
            op.id: op
            for op in db.query(ObjectPermission)
            .filter(ObjectPermission.id.in_(obj_in.object_permissions))
            .all()
        }
        new_permissions = []
        for op_id in obj_in.object_permissions:
            obj_perm = perms_by_id.get(op_id)
            if not obj_perm:
                raise ObjectNotFound(
                    model_name=ObjectPermission.__name__, id=op_id
                )
            new_permissions.append(obj_perm)

        self.db_obj.object_permissions = new_permissions
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    def update_object_permissions(
        self,
        id: Any,
        db: Session,
        request: Request,
        *,
        obj_in: RoleUpdateObjectPermissions,
    ) -> Role:
        self.db_obj = self.get(db, id)

        if not obj_in.object_permissions:
            raise RequiredParameterMissingError(
                parameter_name="object_permissions"
            )

        existing = self.db_obj.object_permissions
        # Batch-fetch all ObjectPermissions by ID
        perms_by_id = {
            op.id: op
            for op in db.query(ObjectPermission)
            .filter(ObjectPermission.id.in_(obj_in.object_permissions))
            .all()
        }
        new_permissions = []

        for op_id in obj_in.object_permissions:
            obj_perm = perms_by_id.get(op_id)
            if not obj_perm:
                raise ObjectNotFound(
                    model_name=ObjectPermission.__name__, id=op_id
                )
            new_permissions.append(obj_perm)

        # Avoid duplicates
        combined = existing + [p for p in new_permissions if p not in existing]

        self.db_obj.object_permissions = combined
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    # Get list of Users that have a given role
    def get_members(
        self,
        db: Session,
        id: Any,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
        search_field: str = "",
        search_value: str = "",
    ) -> list[User] | None:
        self._get_multi_init(
            limit=limit, page=page, sort_by=sort_by, parent_model=User
        )
        system_user = get_system_user(db)
        # Build query
        model_query = (
            db.query(User)
            .join(user_role_association_table)
            .filter(user_role_association_table.c.role_id == id)
        )
        model_query = self._model_query_search(
            model_query,
            search_field=search_field,
            search_value=search_value,
            search_model=User,
        )
        # Remove system user from model_query
        model_query = model_query.filter(User.id != system_user.id)
        model_query = model_query.filter(~User.username.contains("deleted_"))
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

    # Delete Role
    def delete(self, db: Session, id: Any) -> Role | None:
        self.db_obj = self.get(db, id)

        # Check if role is protected (system role)
        if self.db_obj.protected:
            raise ProtectedObjectError(
                model_name=Role.__name__, operation="role_delete"
            )

        try:
            # Delete Changelogs for this Role
            changelogs = db.query(Changelog).filter(
                Changelog.objectId == id,
                Changelog.object == self.model.__name__,
            )
            for changelog in changelogs:
                db.delete(changelog)

            # Delete ObjectPermissions where Role is the entity (entity_type="Role", entity_id=role_id)
            role_entity_perms = db.query(ObjectPermission).filter(
                ObjectPermission.entity_id == id,
                ObjectPermission.entity_type == "Role",
            )
            for obj_perm in role_entity_perms:
                db.delete(obj_perm)

            # Delete ObjectPermissions where Role is the object (object_type="Role", object_id=role_id)
            role_object_perms = db.query(ObjectPermission).filter(
                ObjectPermission.object_id == id,
                ObjectPermission.object_type == "Role",
            )
            for obj_perm in role_object_perms:
                db.delete(obj_perm)

            # Delete Tags for this Role
            tags = db.query(Tag).filter(
                Tag.objectId == id, Tag.objectType == self.model.__name__
            )
            for tag in tags:
                db.delete(tag)

            # Delete the Role itself
            db.delete(self.db_obj)
            self._commit(db)

            return {
                "detail": _("{model} with ID {id} has been deleted.").format(
                    model=self.model.__name__, id=id
                )
            }
        except IntegrityError:
            raise ObjectDeleteIntegrityError(model_name=Role.__name__)


role = CRUDRole(Role)
