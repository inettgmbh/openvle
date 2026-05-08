from fastapi import Request
from fastapi.encoders import jsonable_encoder
from pydantic import UUID4
from sqlalchemy import and_, asc, desc, exists, or_
from sqlalchemy.orm import Session

from core.config import Settings
from core.exceptions import (
    InvalidFieldValue,
    ModelFieldNotFound,
    ModelNotFound,
    ObjectNotFound,
    PaginationLimitError,
    PaginationZeroPageError,
)
from core.pagination import paginate
from models import GuacamoleConnectionProfile, ObjectPermission, Role
from models.associations import user_role_association_table
from schemas.guacamole_connection_profiles import (
    GuacamoleConnectionProfileClone,
    GuacamoleConnectionProfileCreate,
)

from .base import CRUDBase, build_object_permission_filter
from .object_permissions import CRUDObjectPermission

settings = Settings()


class CRUDGuacamoleConnectionProfile(
    CRUDBase[
        GuacamoleConnectionProfile,
        GuacamoleConnectionProfileCreate,
        GuacamoleConnectionProfileCreate,
    ]
):
    # Create GuacamoleConnectionProfile
    def create(
        self,
        db: Session,
        request: Request = None,
        *,
        obj_in: GuacamoleConnectionProfileCreate,
    ) -> GuacamoleConnectionProfile:
        obj_in_data = jsonable_encoder(obj_in)
        self._initialize_object_fields(
            db=db, obj_data_in=obj_in_data, request=request
        )
        # Check if objectType is valid
        try:
            module = __import__(
                "models", fromlist=f"{obj_in_data['objectType']}"
            )
            object_model = getattr(module, obj_in_data["objectType"])
            if object_model and not object_model.__tablename__:
                raise InvalidFieldValue(
                    field="objectType", value=obj_in_data["objectType"]
                )
        except AttributeError:
            raise ModelNotFound(model_name=obj_in_data["objectType"])
        # Check if VirtualMachine/Template object exists
        vm_temp_object = db.get(object_model, obj_in.objectId)
        if not vm_temp_object:
            raise ObjectNotFound(
                id=obj_in.objectId, model_name=object_model.__name__
            )
        self.db_obj.objectId = vm_temp_object.id
        self.db_obj = self._commit(db, self.db_obj)
        request_user_id = request.user.id if request else None
        CRUDObjectPermission(ObjectPermission).create_full(
            db,
            request,
            "GuacamoleConnectionProfile",
            self.db_obj.id,
            request_user_id,
        )
        db.refresh(self.db_obj)
        return self.db_obj

    # Clone GuacamoleConnectionProfile
    def clone(
        self,
        db: Session,
        id: UUID4,
        request: Request = None,
        *,
        obj_in: GuacamoleConnectionProfileClone,
    ) -> GuacamoleConnectionProfile:
        obj_in_data = jsonable_encoder(obj_in)
        source_gcp = CRUDBase(GuacamoleConnectionProfile)._get(db, id)
        if not source_gcp:
            ObjectNotFound(
                id=id, model_name=GuacamoleConnectionProfile.__name__
            )
        self._initialize_object_fields(
            db=db, obj_data_in=obj_in_data, request=request
        )
        # Check if objectType is valid
        try:
            module = __import__(
                "models", fromlist=f"{obj_in_data['objectType']}"
            )
            object_model = getattr(module, obj_in_data["objectType"])
            if object_model and not object_model.__tablename__:
                raise InvalidFieldValue(
                    field="objectType", value=obj_in_data["objectType"]
                )
        except AttributeError:
            raise ModelNotFound(model_name=obj_in_data["objectType"])
        # Check if VirtualMachine/Template object exists
        vm_temp_object = db.get(object_model, obj_in.objectId)
        if not vm_temp_object:
            raise ObjectNotFound(
                id=obj_in.objectId, model_name=object_model.__name__
            )
        self.db_obj.objectId = vm_temp_object.id
        if not self.db_obj.port:
            self.db_obj.port = source_gcp.port
        if not self.db_obj.protocol:
            self.db_obj.protocol = source_gcp.protocol
        if not self.db_obj.password:
            self.db_obj.password = source_gcp.password
        if not self.db_obj.username:
            self.db_obj.username = source_gcp.username
        self.db_obj = self._commit(db, self.db_obj)
        request_user_id = request.user.id if request else None
        CRUDObjectPermission(ObjectPermission).create_full(
            db,
            request,
            "GuacamoleConnectionProfile",
            self.db_obj.id,
            request_user_id,
        )
        db.refresh(self.db_obj)
        return self.db_obj

    # Get all GuacamoleConnectionProfiles for ObjectId and objectType
    def get_gcps_for_object(
        self,
        objectId: UUID4,
        objectType: str,
        db: Session,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
    ) -> list[GuacamoleConnectionProfile] | None:
        if limit > settings.mariadb_query_result_limit:
            raise PaginationLimitError()
        model_list = []
        if page < 1:
            raise PaginationZeroPageError()
        skip = page * limit - limit
        # Check if the provided sort_by attribute exists for the given model
        if not hasattr(GuacamoleConnectionProfile, sort_by):
            raise ModelFieldNotFound(
                field_name=sort_by,
                model_name=GuacamoleConnectionProfile.__name__,
            )
        # Build query
        model_query = db.query(GuacamoleConnectionProfile).filter(
            GuacamoleConnectionProfile.objectId == objectId,
            GuacamoleConnectionProfile.objectType == objectType,
        )
        if sort_order == "asc":
            model_query_sorted = (
                model_query.order_by(asc(sort_by)).offset(skip).limit(limit)
            )
        elif sort_order == "desc":
            model_query_sorted = (
                model_query.order_by(desc(sort_by)).offset(skip).limit(limit)
            )
        else:
            raise InvalidFieldValue(
                field="sort_order",
                value=sort_order,
                supported_values=["asc", "desc"],
            )
        model_query_count = model_query.count()

        # return Paginated list of objects
        return paginate(
            object_list=list(model_query_sorted),
            object_query_count=model_query_count,
            current_page=page,
            limit=limit,
        )

    # Get All GuacamoleConnectionProfiles for ObjectId and objectType that a user is authorised to view based on ObjectPermissions
    def get_gcps_for_object_auth(
        self,
        request: Request,
        objectId: UUID4,
        objectType: str,
        db: Session,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
    ) -> list[GuacamoleConnectionProfile] | None:
        if limit > settings.mariadb_query_result_limit:
            raise PaginationLimitError()
        if page < 1:
            raise PaginationZeroPageError()
        skip = page * limit - limit
        # Check if the provided sort_by attribute exists for the given model
        if not hasattr(GuacamoleConnectionProfile, sort_by):
            raise ModelFieldNotFound(
                field_name=sort_by,
                model_name=GuacamoleConnectionProfile.__name__,
            )

        perm_filter = build_object_permission_filter(
            db, GuacamoleConnectionProfile, request.user.id
        )

        model_query = (
            db.query(GuacamoleConnectionProfile)
            .filter(
                GuacamoleConnectionProfile.objectId == objectId,
                GuacamoleConnectionProfile.objectType == objectType,
            )
            .filter(perm_filter)
        )
        if sort_order == "asc":
            model_query_sorted = (
                model_query.order_by(asc(sort_by)).offset(skip).limit(limit)
            )
        elif sort_order == "desc":
            model_query_sorted = (
                model_query.order_by(desc(sort_by)).offset(skip).limit(limit)
            )
        else:
            raise InvalidFieldValue(
                field="sort_order",
                value=sort_order,
                supported_values=["asc", "desc"],
            )
        model_query_count = model_query.count()

        # return Paginated list of objects
        return paginate(
            object_list=list(model_query_sorted),
            object_query_count=model_query_count,
            current_page=page,
            limit=limit,
        )


guacamole_connection_profile = CRUDGuacamoleConnectionProfile(
    GuacamoleConnectionProfile
)
