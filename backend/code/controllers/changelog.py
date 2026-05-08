import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import Request
from pydantic import UUID4
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from core.core_utils import get_system_user, prepare_changelog_values
from core.exceptions import (
    InvalidFieldValue,
    ModelNotFound,
)
from core.pagination import paginate
from models import Changelog as ChangelogModel, object_type_map
from schemas.changelog import Changelog

from .base import CRUDBase, build_object_permission_filter


class CRUDChangelog(CRUDBase[ChangelogModel, Changelog, Changelog]):
    def _create_for_changes(
        self,
        db: Session,
        object_type: str,
        object_id: UUID4,
        changes: list[dict],
        user_id: UUID4 = None,
    ) -> Changelog:
        values_old = {}
        values_new = {}
        for change in changes:
            values_old[change["field"]] = change["value_old"]
            values_new[change["field"]] = change["value_new"]

        value_old, value_new = prepare_changelog_values(values_old, values_new)
        new_changelog = ChangelogModel(
            id=uuid.uuid4(),
            timestamp=datetime.now(timezone.utc),
            valueOld=value_old,
            valueNew=value_new,
            object=object_type,
            objectId=object_id,
            userId=user_id if user_id else get_system_user().id,
        )
        db.add(new_changelog)
        db.commit()
        db.refresh(new_changelog)
        return new_changelog

    # Get all Changelogs that a user is authorised to see
    def get_multi_auth(
        self,
        db: Session,
        request: Request,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
        search_field: str = "",
        search_value: str = "",
    ) -> list[ChangelogModel] | None:
        self._get_multi_init(limit=limit, page=page, sort_by=sort_by)
        object_filters = []
        for object_type, (object_model, perm_type) in object_type_map.items():
            # Skip types without permissions
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
                    ChangelogModel.object == object_type,
                    ChangelogModel.objectId.in_(accessible_ids),
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
        model_query = db.query(ChangelogModel).filter(combined_filter)

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

    # Get All Changelogs for object with objectId/objectType (auth filtered)
    def get_changelogs_object_auth(
        self,
        request: Request,
        objectId: UUID4,
        objectType: str,
        db: Session,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
        search_field: str = "",
        search_value: str = "",
    ) -> list[ChangelogModel] | None:
        from core.dependencies import PermissionChecker

        self._get_multi_init(limit=limit, page=page, sort_by=sort_by)
        # Check if objectType is valid and get permission type
        if objectType not in object_type_map:
            raise ModelNotFound(model_name=objectType)
        object_model, perm_type = object_type_map[objectType]

        # Validate that the model has a tablename
        if not hasattr(object_model, "__tablename__"):
            raise InvalidFieldValue(field="objectType", value=objectType)

        # Skip permission check for types without permissions
        if perm_type is None:
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

        model_query = db.query(ChangelogModel).filter(
            ChangelogModel.objectId == objectId,
            ChangelogModel.object == objectType,
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


changelog = CRUDChangelog(Changelog)
