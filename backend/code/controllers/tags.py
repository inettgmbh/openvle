import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from pydantic import UUID4
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.config import Settings
from core.core_utils import get_system_user
from core.exceptions import (
    InvalidFieldValue,
    ModelNotFound,
    ObjectDeleteIntegrityError,
    ObjectNotFound,
)
from core.pagination import paginate
from core.redis import queue_pve_vm_actions
from middlewares.i18n import _
from models import Tag as TagModel, Task, object_type_map
from schemas.tags import Tag, TagCreate
from schemas.tasks import TaskCreate

from .base import CRUDBase, build_object_permission_filter

settings = Settings()


class CRUDTag(CRUDBase[Tag, TagCreate, TagCreate]):
    # Create Tag
    def create(
        self, db: Session, request: Request, *, obj_in: TagCreate
    ) -> Tag:
        obj_in_data = jsonable_encoder(obj_in)
        self._initialize_object_fields(
            db=db, obj_data_in=obj_in_data, request=request
        )
        self.db_obj.objectId = obj_in.objectId
        # Check if objectType is valid
        try:
            module = __import__(
                "models", fromlist=f"{obj_in_data['objectType']}"
            )
            object_model = getattr(module, obj_in_data["objectType"])
            # Check if object_model is a Model
            if object_model and not object_model.__tablename__:
                raise InvalidFieldValue(
                    field="objectType", value=obj_in_data["objectType"]
                )
        except AttributeError:
            raise ModelNotFound(model_name=obj_in_data["objectType"])
        # Check if object exists
        object = db.get(object_model, self.db_obj.objectId)
        if not object:
            raise ObjectNotFound(
                model_name=obj_in_data["objectType"], id=obj_in_data["objectId"]
            )
        self.db_obj = self._commit(db, self.db_obj)
        db.refresh(self.db_obj)
        if self.db_obj.objectType in ["VirtualMachine", "Template"]:
            from .tasks import CRUDTask

            # Update PVE with new tag
            try:
                # Create Task object
                new_task = CRUDTask(Task).create(
                    db=db,
                    request=request,
                    obj_in=TaskCreate(
                        name=f"Update {self.db_obj.objectType} tags"
                    ),
                )
                if self.db_obj.objectType == "VirtualMachine":
                    from .virtual_machines import CRUDVirtualMachine

                    job_update = CRUDVirtualMachine(
                        db=db, id=self.db_obj.objectId
                    )._subtask_tags_update(
                        db=db,
                        request=request,
                        parent_task_id=new_task.id,
                        queue=queue_pve_vm_actions,
                    )
                elif self.db_obj.objectType == "Template":
                    from .templates import CRUDTemplate

                    job_update = CRUDTemplate(
                        db=db, id=self.db_obj.objectId
                    )._subtask_tags_update(
                        db=db,
                        request=request,
                        parent_task_id=new_task.id,
                        queue=queue_pve_vm_actions,
                    )
            except Exception as e:
                print(e)

        return self.db_obj

    # Get all Tags that user is authorised to see
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
    ) -> list[TagModel] | None:
        self._get_multi_init(limit=limit, page=page, sort_by=sort_by)
        # Build filter for each object type the user can access
        object_filters = []

        for object_type, (object_model, perm_type) in object_type_map.items():
            # Skip if perm_type is None
            if perm_type is None:
                continue

            # If model is None, try to get it from the object_type key
            if object_model is None:
                try:
                    module = __import__("models", fromlist=[object_type])
                    object_model = getattr(module, object_type)
                except (AttributeError, ImportError):
                    continue

            perm_filter = build_object_permission_filter(
                db, object_model, request.user.id
            )
            accessible_ids = db.query(object_model.id).filter(perm_filter)

            object_filters.append(
                and_(
                    TagModel.objectType == object_type,
                    TagModel.objectId.in_(accessible_ids),
                )
            )

        if not object_filters:
            # User has no permissions, return empty result
            return paginate(
                object_list=[],
                object_query_count=0,
                current_page=page,
                limit=limit,
            )

        combined_filter = or_(*object_filters)
        model_query = db.query(TagModel).filter(combined_filter)

        model_query = self._model_query_search(
            model_query, search_field=search_field, search_value=search_value
        )
        model_query_sorted = self._model_query_sort(
            model_query, sort_by=sort_by, sort_order=sort_order, limit=limit
        )
        model_query_count = model_query.count()

        return paginate(
            object_list=list(model_query_sorted),
            object_query_count=model_query_count,
            current_page=page,
            limit=limit,
        )

    # Get all Tags for object with objectId and ObjectType that a user is authorised to view
    def get_tags_for_object_auth(
        self,
        request: Request,
        objectId: UUID4,
        objectType: str,
        db: Session,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
        search_field: str = "",
        search_value: str = "",
    ) -> list[TagModel] | None:
        from core.dependencies import PermissionChecker

        self._get_multi_init(limit=limit, page=page, sort_by=sort_by)
        # Check if objectType is valid and get permission type
        if objectType not in object_type_map:
            raise ModelNotFound(model_name=objectType)
        object_model, perm_type = object_type_map[objectType]

        # Skip permission check for types without permissions
        if perm_type is None:
            return paginate(
                object_list=[],
                object_query_count=0,
                current_page=page,
                limit=limit,
            )

        # If model is None, try to get it from the object_type key
        if object_model is None:
            try:
                module = __import__("models", fromlist=[objectType])
                object_model = getattr(module, objectType)
            except (AttributeError, ImportError):
                return paginate(
                    object_list=[],
                    object_query_count=0,
                    current_page=page,
                    limit=limit,
                )

        required_permission = f"{perm_type}_read"
        # Check if user can access this specific object
        if not PermissionChecker(
            required_permission, request, objectId, db=db
        ).has_permission():
            return paginate(
                object_list=[],
                object_query_count=0,
                current_page=page,
                limit=limit,
            )

        model_query = db.query(TagModel).filter(
            TagModel.objectId == objectId, TagModel.objectType == objectType
        )

        model_query = self._model_query_search(
            model_query, search_field=search_field, search_value=search_value
        )
        model_query_sorted = self._model_query_sort(
            model_query, sort_by=sort_by, sort_order=sort_order, limit=limit
        )
        model_query_count = model_query.count()
        return paginate(
            object_list=list(model_query_sorted),
            object_query_count=model_query_count,
            current_page=page,
            limit=limit,
        )

    # Get all Tags with Key and Value that a user is authorised to view
    def get_tags_key_value_auth(
        self,
        request: Request,
        key: str,
        value: str,
        db: Session,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
        search_field: str = "",
        search_value: str = "",
    ) -> list[TagModel] | None:
        self._get_multi_init(limit=limit, page=page, sort_by=sort_by)
        object_filters = []
        for object_type, (object_model, perm_type) in object_type_map.items():
            # Skip if perm_type is None
            if perm_type is None:
                continue

            # If model is None, try to get it from the object_type key
            if object_model is None:
                try:
                    module = __import__("models", fromlist=[object_type])
                    object_model = getattr(module, object_type)
                except (AttributeError, ImportError):
                    continue

            # Get all objects a User is authorised to see
            perm_filter = build_object_permission_filter(
                db, object_model, request.user.id
            )
            accessible_ids = db.query(object_model.id).filter(perm_filter)

            object_filters.append(
                and_(
                    TagModel.objectType == object_type,
                    TagModel.objectId.in_(accessible_ids),
                )
            )

        if not object_filters:
            return paginate(
                object_list=[],
                object_query_count=0,
                current_page=page,
                limit=limit,
            )

        combined_filter = or_(*object_filters)

        # Filter by key/value AND object permissions
        model_query = db.query(TagModel).filter(
            TagModel.key == key, TagModel.value == value, combined_filter
        )

        model_query = self._model_query_search(
            model_query, search_field=search_field, search_value=search_value
        )
        model_query_sorted = self._model_query_sort(
            model_query, sort_by=sort_by, sort_order=sort_order, limit=limit
        )
        model_query_count = model_query.count()
        return paginate(
            object_list=list(model_query_sorted),
            object_query_count=model_query_count,
            current_page=page,
            limit=limit,
        )

    # Get all Tags with Key that a user is authorised to view
    def get_tags_key_auth(
        self,
        request: Request,
        key: str,
        db: Session,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
        search_field: str = "",
        search_value: str = "",
    ) -> list[TagModel] | None:
        self._get_multi_init(limit=limit, page=page, sort_by=sort_by)
        object_filters = []
        for object_type, (object_model, perm_type) in object_type_map.items():
            # Skip if perm_type is None
            if perm_type is None:
                continue

            # If model is None, try to get it from the object_type key
            if object_model is None:
                try:
                    module = __import__("models", fromlist=[object_type])
                    object_model = getattr(module, object_type)
                except (AttributeError, ImportError):
                    continue

            # Get all objects a User is authorised to see
            perm_filter = build_object_permission_filter(
                db, object_model, request.user.id
            )
            accessible_ids = db.query(object_model.id).filter(perm_filter)

            object_filters.append(
                and_(
                    TagModel.objectType == object_type,
                    TagModel.objectId.in_(accessible_ids),
                )
            )

        if not object_filters:
            return paginate(
                object_list=[],
                object_query_count=0,
                current_page=page,
                limit=limit,
            )

        combined_filter = or_(*object_filters)

        # Filter by key AND object permissions
        model_query = db.query(TagModel).filter(
            TagModel.key == key, combined_filter
        )

        model_query = self._model_query_search(
            model_query, search_field=search_field, search_value=search_value
        )
        model_query_sorted = self._model_query_sort(
            model_query, sort_by=sort_by, sort_order=sort_order, limit=limit
        )
        model_query_count = model_query.count()
        return paginate(
            object_list=list(model_query_sorted),
            object_query_count=model_query_count,
            current_page=page,
            limit=limit,
        )

    # Get All Tags for object with objectId and ObjectType
    def _get_tags_for_object_internal(
        self, db: Session, objectId: UUID4, objectType: str
    ):
        try:
            object_tags = db.query(TagModel).filter(
                TagModel.objectId == objectId, TagModel.objectType == objectType
            )
        except:
            object_tags = None
        return object_tags

    def _convert_pve_to_kvs(self, pve_tags: str) -> list[dict[str, str]]:
        kvs_tags_list: list[dict[str, str]] = []
        if not pve_tags:
            return kvs_tags_list  # empty input returns empty list
        # Split string by comma and strip whitespace
        for raw_tag in pve_tags.split(","):
            tag = raw_tag.strip()
            if not tag:
                continue
            parts = tag.split("_", 1)  # split only on the first "_"
            if len(parts) != 2:
                continue  # Allow PVE Tags to have multiple "_" characters without breaking here but only use first 2
            key, value = parts
            kvs_tags_list.append({key: value})

        return kvs_tags_list

    def _convert_kvs_to_pve(
        self,
        db: Session,
        objectId: UUID4 = None,
        objectType: str = None,
        kvs_tags_list: list = None,
    ):
        pve_tags_list = []
        # Get Tags for object_id if kvs_tags_list not provided
        if not kvs_tags_list:
            kvs_tags_list = self._get_tags_for_object_internal(
                db=db, objectId=objectId, objectType=objectType
            )

        if not kvs_tags_list:
            return None

        for kvs_tag in kvs_tags_list:
            pve_tag = f"{kvs_tag.key}_{kvs_tag.value}"
            pve_tags_list.append(pve_tag)

        return pve_tags_list

    def _create_for_pve_tags_list(
        self,
        db: Session,
        objectId: UUID4,
        objectType: str,
        pve_tags: str = None,
        kvs_tags=None,
    ) -> list[Tag]:
        if not kvs_tags:
            kvs_tags = self._convert_pve_to_kvs(pve_tags=pve_tags)
        created_tags: list[Tag] = []
        for kvs_tag in kvs_tags:
            try:
                for key, value in kvs_tag.items():
                    new_tag = TagModel(
                        key=key,
                        value=value,
                        objectId=objectId,
                        objectType=objectType,
                        id=uuid.uuid4(),
                        createdAt=datetime.now(timezone.utc),
                        updatedAt=datetime.now(timezone.utc),
                        updatedById=get_system_user(db).id,
                        createdById=get_system_user(db).id,
                    )
                    db.add(new_tag)
                    created_tags.append(new_tag)
            except Exception as e:
                print(e)
                continue

        db.commit()
        for tag in created_tags:
            db.refresh(tag)

        return created_tags

    def delete(self, db: Session, id: Any, request: Request) -> dict:
        self.db_obj = self.get(db, id)
        try:
            db.delete(self.db_obj)
            self._commit(db)

            # If tag belongs to VM/Template, enqueue PVE update task
            if self.db_obj.objectType in ["VirtualMachine", "Template"]:
                from .tasks import CRUDTask

                new_task = CRUDTask(Task).create(
                    db=db,
                    request=request,
                    obj_in=TaskCreate(
                        name=f"Update {self.db_obj.objectType} tags"
                    ),
                )

                if self.db_obj.objectType == "VirtualMachine":
                    from .virtual_machines import CRUDVirtualMachine

                    CRUDVirtualMachine(
                        db=db, id=self.db_obj.objectId
                    )._subtask_tags_update(
                        db=db,
                        request=request,
                        parent_task_id=new_task.id,
                        queue=queue_pve_vm_actions,  # async worker queue
                        tag_to_remove=f"{self.db_obj.key}_{self.db_obj.value}",
                    )

                elif self.db_obj.objectType == "Template":
                    from .templates import CRUDTemplate

                    CRUDTemplate(
                        db=db, id=self.db_obj.objectId
                    )._subtask_tags_update(
                        db=db,
                        request=request,
                        parent_task_id=new_task.id,
                        queue=queue_pve_vm_actions,  # async worker queue
                        tag_to_remove=f"{self.db_obj.key}_{self.db_obj.value}",
                    )

            self.db_obj = None
            return {
                "detail": _("{model} with ID {id} has been deleted.").format(
                    model=self.model.__name__, id=id
                )
            }

        except IntegrityError:
            raise ObjectDeleteIntegrityError(model_name=self.model.__name__)

    def _inherit_tags(
        self,
        db: Session,
        source_object_id: UUID4,
        target_object_id: UUID4,
        source_object_type: str,
        target_object_type: str,
    ):
        source_tags = self._get_tags_for_object_internal(
            db=db, objectId=source_object_id, objectType=source_object_type
        )
        tag_list: list[dict[str, str]] = []
        for tag in source_tags:
            tag_list.append({tag.key: tag.value})
        new_tags = self._create_for_pve_tags_list(
            db=db,
            objectId=target_object_id,
            objectType=target_object_type,
            kvs_tags=tag_list,
        )
        return new_tags


changelog = CRUDTag(Tag)
