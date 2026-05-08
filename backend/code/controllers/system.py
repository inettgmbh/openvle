import json
from collections.abc import Iterable, Sequence
from typing import Any, List, Optional, Tuple, Union

from fastapi import Request
from sqlalchemy.orm import Session

from core.config import Settings
from core.exceptions import (
    InvalidFieldValue,
    ModelFieldNotFound,
    ProtectedObjectError,
)
from core.pagination import paginate
from models import SystemSetting as SystemSettingModel
from schemas.system import (
    SystemSetting,
    SystemSettingCreate,
    SystemSettingList,
    SystemSettingUpdate,
    SystemSettingValueType,
    SystemSettingVisibility,
    SystemSettingWithoutAudit,
    SystemSettingWithoutAuditList,
)
from schemas.users import User

from .base import CRUDBase

settings = Settings()


class CRUDSystemSetting(
    CRUDBase[SystemSetting, SystemSettingCreate, SystemSettingUpdate]
):  # type: ignore
    def _normalize_result(self, result) -> tuple[object, Sequence]:
        if isinstance(result, dict):
            page_details = result.get("pageDetails")
            rows = result.get("items") or []
        else:
            page_details = getattr(result, "pageDetails", None)
            rows = getattr(result, "items", []) or []
        return page_details, rows

    def _to_public_item(self, item) -> SystemSettingWithoutAudit:
        return SystemSettingWithoutAudit(
            key=item.key,
            value=getattr(item, "value", None),
            type=item.type,
        )

    def _filter_by_visibility(
        self, rows: Iterable, allowed: set[SystemSettingVisibility]
    ) -> list[SystemSettingWithoutAudit]:
        return [
            self._to_public_item(item)
            for item in rows
            if item.visibility in allowed
        ]

    def _json_type(self, value) -> SystemSettingValueType:
        """Return the JSON type of the value field."""
        try:
            parsed = json.loads(value)  # type: ignore
        except (ValueError, TypeError):
            parsed = value

        if parsed is None:
            return SystemSettingValueType.null
        if isinstance(parsed, bool):
            return SystemSettingValueType.boolean
        if isinstance(parsed, int) and not isinstance(parsed, bool):
            return SystemSettingValueType.integer
        if isinstance(parsed, float):
            return SystemSettingValueType.float
        if isinstance(parsed, dict):
            return SystemSettingValueType.object
        if isinstance(parsed, list):
            return SystemSettingValueType.array
        return SystemSettingValueType.string

    def _trim_value(self, value):
        if isinstance(value, str):
            return value.strip()
        elif isinstance(value, list):
            return [self._trim_value(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._trim_value(v) for k, v in value.items()}
        return value

    def _pretty_format(self, value, value_type: SystemSettingValueType):
        value = self._trim_value(value)

        if value_type in {
            SystemSettingValueType.array,
            SystemSettingValueType.object,
        }:
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                    value = self._trim_value(value)
                except (ValueError, TypeError):
                    return value
            try:
                return json.dumps(value, indent=2, ensure_ascii=False)
            except (TypeError, ValueError):
                return value

        return value

    def update(
        self,
        id: Any,
        db: Session,
        request: Request,
        *,
        obj_in: SystemSettingUpdate,
    ) -> SystemSetting:  # type: ignore
        db_obj = self.get(db=db, id=id)
        if not db_obj:
            raise ModelFieldNotFound(
                field_name=id, model_name=self.model.__name__
            )

        if db_obj.visibility == SystemSettingVisibility.internal:
            raise ProtectedObjectError(
                model_name=self.model.__name__, operation="system_update"
            )

        existing_type = SystemSettingValueType(db_obj.type)
        if (
            obj_in.value is None
            and existing_type != SystemSettingValueType.null
        ):
            pass

        if "value" in obj_in.model_fields_set:
            new_type = self._json_type(obj_in.value)
            if existing_type not in (new_type, SystemSettingValueType.null):
                raise InvalidFieldValue(field="'value'", value=obj_in.value)

            obj_in.value = self._pretty_format(obj_in.value, new_type)

        return super().update(id=id, db=db, request=request, obj_in=obj_in)

    def get_multi_visibility(
        self,
        db: Session,
        allowed: set[SystemSettingVisibility],
        *,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
        search_field: str = "",
        search_value: str = "",
    ):
        self._get_multi_init(limit=limit, page=page, sort_by=sort_by)

        allowed_values = [
            v.value if isinstance(v, SystemSettingVisibility) else str(v)
            for v in allowed
        ]
        model_query = db.query(SystemSettingModel).filter(
            SystemSettingModel.visibility.in_(allowed_values)
        )

        model_query = self._model_query_search(
            model_query,
            search_model=SystemSetting,
            search_field=search_field,
            search_value=search_value,
        )

        model_query_count = model_query.count()

        model_query_sorted = self._model_query_sort(
            model_query, sort_by=sort_by, sort_order=sort_order, limit=limit
        )

        return paginate(
            object_list=list(model_query_sorted),
            object_query_count=model_query_count,
            current_page=page,
            limit=limit,
        )

    def get_filtered(
        self,
        db: Session,
        current_user: User | bool,
        permissionSet: bool = False,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
        search_field: str = "",
        search_value: str = "",
    ) -> list[SystemSettingWithoutAuditList] | None:
        # Not logged in → only show public visible data
        if not current_user:
            result = self.get_multi_visibility(
                db,
                allowed={SystemSettingVisibility.public},
                limit=limit,
                page=page,
                sort_by=sort_by,
                sort_order=sort_order,
                search_field=search_field,
                search_value=search_value,
            )
            page_details, rows = self._normalize_result(result)
            filtered = [self._to_public_item(item) for item in rows]
            return SystemSettingWithoutAuditList(
                pageDetails=page_details, items=filtered
            )  # type: ignore

        # Admin → return unmasked, complete list of system settings
        if permissionSet:
            result = super().get_multi(
                db=db,
                limit=limit,
                page=page,
                search_field=search_field,
                search_value=search_value,
                sort_by=sort_by,
                sort_order=sort_order,
            )
            page_details, rows = self._normalize_result(result)
            return SystemSettingList(pageDetails=page_details, items=list(rows))  # type: ignore

        # Logged in, but no full access → public + authenticated
        result = self.get_multi_visibility(
            db,
            allowed={
                SystemSettingVisibility.public,
                SystemSettingVisibility.authenticated,
            },
            limit=limit,
            page=page,
            sort_by=sort_by,
            sort_order=sort_order,
            search_field=search_field,
            search_value=search_value,
        )
        page_details, rows = self._normalize_result(result)
        filtered = [self._to_public_item(item) for item in rows]
        return SystemSettingWithoutAuditList(
            pageDetails=page_details, items=filtered
        )  # type: ignore
