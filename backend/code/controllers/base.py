import uuid
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import (
    UUID,
    Boolean,
    String,
    and_,
    asc,
    desc,
    exists,
    inspect,
    or_,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.config import Settings
from core.core_utils import get_system_user
from core.exceptions import (
    BadRequestError,
    InvalidFieldValue,
    ModelFieldNotFound,
    ObjectCommitError,
    ObjectDeleteIntegrityError,
    ObjectInitError,
    ObjectNotFound,
    PaginationLimitError,
    PaginationZeroPageError,
)
from core.pagination import paginate
from middlewares.i18n import _
from models import ObjectPermission, Tag
from models.associations import user_role_association_table
from models.base import DBBaseModel
from models.changelog import Changelog

settings = Settings()

ModelType = TypeVar("ModelType", bound=DBBaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

# List of models that have no ObjectPermissions
MODELS_NO_OBJ_PERM = [
    "ObjectPermission",
    "Changelog",
    "CourseStatus",
    "EventStatus",
    "EventsUser",
    "Language",
    "Mail",
    "PoliciesUser",
    "Role",
    "SubTask",
    "Tag",
    "Task",
    "UserStatus",
    "User",
]


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**
        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model
        self.db_obj = None

    # Get single object by ID (No response validation)
    def _get(self, db: Session, id: Any) -> ModelType | None:
        if isinstance(id, str):
            try:
                id = uuid.UUID(id)
            except:
                raise InvalidFieldValue(field="id", value=id)
        db_obj = db.get(self.model, id)
        return db_obj

    def _get_by_name(self, db: Session, name: str) -> ModelType | None:
        if not getattr(self.model, "name", None):
            return None
        db_obj = db.query(self.model).filter(self.model.name == name).first()
        return db_obj

    # Get single object by ID
    def get(self, db: Session, id: Any) -> ModelType | None:
        if id is None:
            raise InvalidFieldValue(field="id", value=id)
        if isinstance(id, str):
            try:
                id = uuid.UUID(id)
            except:
                raise InvalidFieldValue(field="id", value=id)
        self.db_obj = db.get(self.model, id)
        if not self.db_obj:
            raise ObjectNotFound(id=id, model_name=self.model.__name__)
        return self.db_obj

    # Initialise base object fields for ModelType based on obj_data_in
    def _initialize_object_fields(
        self,
        db: Session,
        obj_data_in: dict[str, Any],
        request: Request = None,
        model_type: ModelType = None,
    ):
        try:
            if model_type:
                db_obj = model_type(**obj_data_in)
            else:
                db_obj = self.model(**obj_data_in)
            db_obj.id = uuid.uuid4()
            db_obj.createdAt = datetime.now(timezone.utc)
            db_obj.updatedAt = datetime.now(timezone.utc)
            if request and hasattr(request, "user") and request.user:
                db_obj.createdById = request.user.id
                db_obj.updatedById = request.user.id
            else:
                db_obj.createdById = get_system_user(db).id
                db_obj.updatedById = get_system_user(db).id
            # Set foreign key fields to provided values if object(s) exist
            mapper = inspect(model_type or self.model)
            for rel in mapper.relationships:
                foreign_model_class = rel.mapper.class_
                fk_field = rel.key
                if fk_field in obj_data_in:
                    # Check if object exists for provided ID
                    foreign_obj = db.get(
                        foreign_model_class, obj_data_in[rel.key]
                    )
                    if not foreign_obj:
                        raise ObjectNotFound(
                            id=obj_data_in[rel.key],
                            model_name=foreign_model_class,
                        )
                    else:
                        setattr(db_obj, fk_field, foreign_obj.id)
        except Exception as e:
            raise ObjectInitError(message=str(e))
        self.db_obj = db_obj

    def _merge_request_with_db_object(self, obj_in: Any, obj_data: Any):
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        # Build set of NOT NULL column names for this model
        mapper = inspect(self.model)
        not_null_fields = {
            col.key
            for col in mapper.columns
            if not col.nullable and col.key not in ("id",)
        }
        for field in obj_data:
            if field in update_data:
                if update_data[field] is None and field in not_null_fields:
                    raise InvalidFieldValue(field=field, value=None)
                setattr(self.db_obj, field, update_data[field])
        return update_data

    # Create object_full ObjectPermission based on given db_obj
    def _create_obj_permission(
        self, db: Session, db_obj: ModelType, request: Request
    ):
        db_obj_perm_dict = {
            "object_id": db_obj.id,
            "object_type": self.model.__name__,
            "entity_id": request.user.id,
            "entity_type": "User",
            "permission_key": "object_full",
        }
        db_obj_perm = ObjectPermission(**db_obj_perm_dict)
        db_obj_perm.id = uuid.uuid4()
        db_obj_perm.id = uuid.uuid4()
        db_obj_perm.createdAt = datetime.now(timezone.utc)
        db_obj_perm.updatedAt = datetime.now(timezone.utc)
        if request:
            db_obj_perm.createdById = request.user.id
            db_obj_perm.updatedById = request.user.id
        else:
            db_obj_perm.createdById = get_system_user(db).id
            db_obj_perm.updatedById = get_system_user(db).id
        return db_obj_perm

    # Update updatedById and updatedById fields
    def _update_meta(self, request: Request = None):
        self.db_obj.updatedAt = datetime.now(timezone.utc)
        if request:
            self.db_obj.updatedById = request.user.id
        # If no request object is provided (internal system action)
        else:
            self.db_obj.updatedById = get_system_user().id

    # Commit changes made in db session
    def _commit(self, db: Session, db_obj: ModelType = None):
        # If db_obj is provided, merge into session (merge returns the
        # session-attached instance — no separate add() needed)
        if db_obj:
            db_obj = db.merge(db_obj)
        try:
            db.commit()
            # If db_obj is provided, refresh object and return it
            if db_obj:
                self.db_obj = db_obj
                db.refresh(self.db_obj)
                return self.db_obj
        except IntegrityError:
            raise ObjectDeleteIntegrityError(model_name=self.model.__name__)
        except Exception as e:
            raise ObjectCommitError(
                model_name=self.model.__name__, message=str(e)
            )

    # Delete all objects in a list of child from DB (without committing)
    def _delete_child_list(self, db: Session, obj_list: list):
        for obj in obj_list:
            db.refresh(obj)
            db.delete(obj)

    # Start process for get_multi methods
    def _get_multi_init(
        self,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "createdAt",
        parent_model: ModelType = None,
    ):
        if limit > settings.mariadb_query_result_limit:
            raise PaginationLimitError()
        if page < 1:
            raise PaginationZeroPageError()
        self.skip = page * limit - limit

        if parent_model:
            # Check if the provided sort_by attribute exists for the given model
            if not hasattr(parent_model, sort_by):
                raise ModelFieldNotFound(
                    field_name=sort_by, model_name=parent_model.__name__
                )
        # Check if the provided sort_by attribute exists for the given model
        elif not hasattr(self.model, sort_by):
            raise ModelFieldNotFound(
                field_name=sort_by, model_name=self.model.__name__
            )

    # Handles model_query searches for get_multi methods
    def _model_query_search(
        self,
        model_query,
        search_model=None,
        search_field: str = "",
        search_value: str = "",
    ):
        search_model = self.model if search_model is None else search_model
        if search_field and search_value:
            # Check if the provided search_field attribute exists for the given model
            if not hasattr(search_model, search_field):
                raise ModelFieldNotFound(
                    field_name=search_field, model_name=search_model.__name__
                )
            col_type = getattr(search_model, search_field).prop.columns[0].type
            # check if attribute is a string
            if isinstance(col_type, String):
                # for string fields use ilike for search
                model_query = model_query.filter(
                    getattr(search_model, search_field).ilike(
                        f"%{search_value}%"
                    )
                )
            # check if attribute is a UUID
            elif isinstance(col_type, UUID):
                # Try to convert the search_value to UUID
                try:
                    search_value = uuid.UUID(search_value)
                except ValueError:
                    raise BadRequestError(
                        message=_(
                            "The provided search_value '{value}' is not valid for the search_field '{field}'."
                        ).format(field=search_field, value=search_value)
                    )
                model_query = model_query.filter(
                    getattr(search_model, search_field) == search_value
                )
            # check if attribute is a boolean
            elif isinstance(col_type, Boolean):
                if str(search_value).lower() in ("true", "1"):
                    bool_value = True
                elif str(search_value).lower() in ("false", "0"):
                    bool_value = False
                else:
                    raise InvalidFieldValue(
                        field=search_field,
                        value=search_value,
                        supported_values=["true", "false", "1", "0"],
                    )
                model_query = model_query.filter(
                    getattr(search_model, search_field) == bool_value
                )
            else:
                # for non-string fields, use exact value
                model_query = model_query.filter(
                    getattr(search_model, search_field) == search_value
                )
        return model_query

    # Sorts model_query search results for get_multi methods
    def _model_query_sort(
        self,
        model_query,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
        limit: int = 200,
    ):
        if sort_order == "asc":
            model_query_sorted = (
                model_query.order_by(asc(sort_by))
                .offset(self.skip)
                .limit(limit)
            )
        elif sort_order == "desc":
            model_query_sorted = (
                model_query.order_by(desc(sort_by))
                .offset(self.skip)
                .limit(limit)
            )
        else:
            raise InvalidFieldValue(
                field="sort_order",
                value=sort_order,
                supported_values=["asc", "desc"],
            )
        return model_query_sorted

    # Get multiple (all) objects with limit of 100
    def get_multi(
        self,
        db: Session,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
        search_field: str = "",
        search_value: str = "",
    ) -> list[ModelType] | None:
        # Initialise get_multi method
        self._get_multi_init(limit=limit, page=page, sort_by=sort_by)
        # Build and sort query based on provided parameters
        model_query = db.query(self.model)
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

    # Get multiple (all) objects with limit of 100 that a user is authorised to view based on ObjectPermissions
    def get_multi_auth(
        self,
        db: Session,
        request: Request,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
        search_field: str = "",
        search_value: str = "",
    ) -> list[ModelType] | None:
        # Initialise get_multi method
        self._get_multi_init(limit=limit, page=page, sort_by=sort_by)
        # Build filter for authorised objects
        perm_filter = build_object_permission_filter(
            db, self.model, request.user.id
        )
        model_query = db.query(self.model).filter(perm_filter)
        # Build and sort query based on provided parameters
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

    # Get multiple (all) objects with limit of 100 that are associated to a parent object (Foreign key relation)
    def get_multi_foreign_key(
        self,
        db: Session,
        foreign_key_field: str,
        foreign_key_value: str,
        parent_model: ModelType = None,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
        search_field: str = "",
        search_value: str = "",
    ) -> list[ModelType] | None:
        # Initialise get_multi methods
        if not parent_model:
            parent_model = self.model
        self._get_multi_init(
            limit=limit, page=page, sort_by=sort_by, parent_model=parent_model
        )
        # Check if the provided foreign_key_field attribute exists for the given model
        if not hasattr(parent_model, foreign_key_field):
            raise ModelFieldNotFound(
                field_name=foreign_key_field, model_name=parent_model.__name__
            )

        # Build and sort query based on provided parameters
        model_query = db.query(parent_model).filter(
            getattr(parent_model, foreign_key_field) == foreign_key_value
        )
        model_query = self._model_query_search(
            model_query,
            search_model=parent_model,
            search_field=search_field,
            search_value=search_value,
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

    # Get multiple (all) objects with limit of 100 that are associated to a parent object (Foreign key relation)
    # that a user is authorised to view based on ObjectPermissions
    def get_multi_foreign_key_auth(
        self,
        db: Session,
        request: Request,
        foreign_key_field: str,
        foreign_key_value: str,
        parent_model: ModelType = None,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
        search_field: str = "",
        search_value: str = "",
    ) -> list[ModelType] | None:
        # Initialise get_multi method
        if not parent_model:
            parent_model = self.model
        self._get_multi_init(
            limit=limit, page=page, sort_by=sort_by, parent_model=parent_model
        )
        # Check if the provided foreign_key_field attribute exists for the given model
        if not hasattr(parent_model, foreign_key_field):
            raise ModelFieldNotFound(
                field_name=foreign_key_field, model_name=parent_model.__name__
            )

        perm_filter = build_object_permission_filter(
            db, parent_model, request.user.id
        )
        model_query = (
            db.query(parent_model)
            .filter(
                getattr(parent_model, foreign_key_field) == foreign_key_value
            )
            .filter(perm_filter)
        )
        model_query = self._model_query_search(
            model_query,
            search_model=parent_model,
            search_field=search_field,
            search_value=search_value,
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

    # Get multiple (all) objects with limit of 100 that are associated to a parent object (Association table)
    def get_multi_association(
        self,
        db: Session,
        child_model: ModelType,
        parent_field_name: str,
        child_field_name: str,
        field_value: Any,
        parent_model: ModelType = None,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
        search_field: str = "",
        search_value: str = "",
    ) -> list[ModelType] | None:
        # Initialise get_multi method
        if not parent_model:
            parent_model = self.model
        self._get_multi_init(
            limit=limit, page=page, sort_by=sort_by, parent_model=parent_model
        )

        # Check if the provided foreign_key_field attribute exists for the given model
        if not hasattr(parent_model, parent_field_name):
            raise ModelFieldNotFound(
                field_name=parent_field_name, model_name=parent_model.__name__
            )
        # Build and sort query based on provided parameters
        model_query = (
            db.query(parent_model)
            .join(getattr(parent_model, parent_field_name))
            .filter(getattr(child_model, child_field_name) == field_value)
        )
        model_query = self._model_query_search(
            model_query,
            search_model=parent_model,
            search_field=search_field,
            search_value=search_value,
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

    # Get multiple (all) objects with limit of 100 that are associated to a parent object (Association table)
    def get_multi_association_auth(
        self,
        db: Session,
        request: Request,
        child_model: ModelType,
        parent_field_name: str,
        child_field_name: str,
        field_value: Any,
        parent_model: ModelType = None,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
        search_field: str = "",
        search_value: str = "",
    ) -> list[ModelType] | None:
        # Initialise get_multi method
        if not parent_model:
            parent_model = self.model
        self._get_multi_init(
            limit=limit, page=page, sort_by=sort_by, parent_model=parent_model
        )
        # Check if the provided foreign_key_field attribute exists for the given model
        if not hasattr(parent_model, parent_field_name):
            raise ModelFieldNotFound(
                field_name=parent_field_name, model_name=parent_model.__name__
            )
        perm_filter = build_object_permission_filter(
            db, parent_model, request.user.id
        )
        model_query = (
            db.query(parent_model)
            .join(getattr(parent_model, parent_field_name))
            .filter(getattr(child_model, child_field_name) == field_value)
            .filter(perm_filter)
        )
        model_query = self._model_query_search(
            model_query,
            search_model=parent_model,
            search_field=search_field,
            search_value=search_value,
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

    # Create single object with given ModelType/CreateSchemaType
    def create(
        self, db: Session, request: Request, *, obj_in: CreateSchemaType
    ) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        self._initialize_object_fields(
            db=db, obj_data_in=obj_in_data, request=request
        )
        db.add(self.db_obj)
        if (
            self.model.__name__ not in MODELS_NO_OBJ_PERM
        ):  # Only create ObjectPermission for relevant Models
            # Create object_full ObjectPermission for object creator
            db_obj_perm = self._create_obj_permission(db, self.db_obj, request)
            db.add(db_obj_perm)
        self._commit(db)
        return self.db_obj

    # Update object with given ModelType/UpdateSchemaType
    def update(
        self,
        id: Any,
        db: Session,
        request: Request,
        *,
        obj_in: UpdateSchemaType | dict[str, Any],
    ) -> ModelType:
        # Check if object exists before attempting update
        self.db_obj = self.get(db, id)
        obj_data = jsonable_encoder(self.db_obj)
        update_data = self._merge_request_with_db_object(obj_in, obj_data)
        self._update_meta(request)
        return self._commit(db, self.db_obj)

    # Delete object with ID
    def delete(self, db: Session, id: int) -> ModelType:
        self.db_obj = self.get(db, id)
        try:
            db.delete(self.db_obj)
            if self.model.__name__ != "Changelog":
                db.query(Changelog).filter(
                    Changelog.objectId == id,
                    Changelog.object == self.model.__name__,
                ).delete(synchronize_session="fetch")
            if (
                self.model.__name__ not in MODELS_NO_OBJ_PERM
            ):  # Only delete ObjectPermissions for relevant Models
                db.query(ObjectPermission).filter(
                    ObjectPermission.object_id == id,
                    ObjectPermission.object_type == self.model.__name__,
                ).delete(synchronize_session="fetch")
            db.query(Tag).filter(
                Tag.objectId == id, Tag.objectType == self.model.__name__
            ).delete(synchronize_session="fetch")
            self._commit(db)
            self.db_obj = None
            return {
                "detail": _("{model} with ID {id} has been deleted.").format(
                    model=self.model.__name__, id=id
                )
            }
        except IntegrityError:
            raise ObjectDeleteIntegrityError(model_name=self.model.__name__)


def build_object_permission_filter(db, model, user_id):
    """
    Returns a SQLAlchemy filter that restricts query results to objects the user
    can see based on ObjectPermissions.

    Only permissions that imply read access are considered:
    - object_read: grants read only
    - object_update: grants read (hierarchy)
    - object_delete: grants read (hierarchy)
    - object_full: grants all permissions
    """

    model_name = model.__name__

    # Permission keys that grant read access
    READ_PERMISSION_KEYS = [
        "object_read",
        "object_update",
        "object_delete",
        "object_full",
        "object_reset",
    ]

    # Get user's role IDs
    user_role_ids = db.query(user_role_association_table.c.role_id).filter(
        user_role_association_table.c.user_id == user_id
    )

    # Direct user object permissions (entity_type="User", entity_id=user_id)
    # Only consider permissions that grant read access
    direct_perms = db.query(ObjectPermission.object_id).filter(
        ObjectPermission.object_type == model_name,
        ObjectPermission.entity_type == "User",
        ObjectPermission.entity_id == user_id,
        ObjectPermission.permission_key.in_(READ_PERMISSION_KEYS),
    )

    # Role object permissions (entity_type="Role", entity_id in user's roles)
    # Only consider permissions that grant read access
    role_perms = db.query(ObjectPermission.object_id).filter(
        ObjectPermission.object_type == model_name,
        ObjectPermission.entity_type == "Role",
        ObjectPermission.entity_id.in_(user_role_ids),
        ObjectPermission.permission_key.in_(READ_PERMISSION_KEYS),
    )

    # Global ObjectPermissions (object_id is NULL)
    # Check if user has global permission either directly or via roles
    # Only consider permissions that grant read access
    global_perm_exists = (
        exists()
        .where(
            and_(
                ObjectPermission.object_type == model_name,
                ObjectPermission.object_id.is_(None),
                ObjectPermission.permission_key.in_(READ_PERMISSION_KEYS),
                or_(
                    # Direct user global permission
                    and_(
                        ObjectPermission.entity_type == "User",
                        ObjectPermission.entity_id == user_id,
                    ),
                    # Role global permission
                    and_(
                        ObjectPermission.entity_type == "Role",
                        ObjectPermission.entity_id.in_(user_role_ids),
                    ),
                ),
            )
        )
        .select_from(ObjectPermission)
    )

    return or_(
        model.id.in_(direct_perms),
        model.id.in_(role_perms),
        global_perm_exists,
    )
