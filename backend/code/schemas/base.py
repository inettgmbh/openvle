import re
from datetime import datetime, timezone
from typing import Annotated, Any, ClassVar

from pydantic import (
    UUID4,
    BaseModel,
    BeforeValidator,
    Field,
    model_validator,
)
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.types import String as SAString

from core.exceptions import FieldValueTooLong

_EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)


def _validate_lenient_email(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError("string required")
    value = value.strip()
    try:
        from email_validator import validate_email

        result = validate_email(value, check_deliverability=False)
        return result.normalized
    except Exception:
        pass
    if not _EMAIL_REGEX.match(value):
        raise ValueError("invalid email format")
    return value


LenientEmailStr = Annotated[str, BeforeValidator(_validate_lenient_email)]


def _get_column_max_length(model_class: Any, field_name: str) -> int | None:
    """Return the maximum String length for a model column, or None."""
    if model_class is None:
        return None
    try:
        for col in sa_inspect(model_class).columns:
            if col.key == field_name and isinstance(col.type, SAString):
                return col.type.length
    except Exception:
        pass
    return None


def _infer_model_class(schema_class_name: str) -> Any | None:
    """
    Infer the SQLAlchemy model from a schema class name by stripping the
    trailing 'Create' or 'Update' suffix (e.g. TemplateCreate → Template).
    Returns None if no matching model is found.
    """
    import models as models_module

    for suffix in ("Create", "Update"):
        if schema_class_name.endswith(suffix):
            model_name = schema_class_name[: -len(suffix)]
            model = getattr(models_module, model_name, None)
            if model is not None:
                return model
    return None


# Base DB class for all objects
class DBBase(BaseModel):
    """Base model for all database-backed objects, includes audit fields."""

    id: UUID4 | None = Field(
        None, description="Unique identifier of the object"
    )
    createdAt: datetime | None = Field(
        datetime.now(timezone.utc),
        description="Timestamp when the object was created",
    )
    createdById: UUID4 | None = Field(
        None, description="ID of the user who created the object"
    )
    updatedAt: datetime | None = Field(
        datetime.now(timezone.utc), description="Timestamp of the last update"
    )
    updatedById: UUID4 | None = Field(
        None, description="ID of the user who last updated the object"
    )

    @classmethod
    def create(cls, user_id: UUID4, **kwargs):
        # create a new instance of the model
        new_instance = cls(**kwargs)
        # Dynamically set the following fields upon object creation
        new_instance.createdById = user_id
        new_instance.updatedById = user_id
        new_instance.createdAt = datetime.now(timezone.utc)
        new_instance.updatedAt = datetime.now(timezone.utc)
        return new_instance

    def update(self, user_id: UUID4, **kwargs):
        # update the fields with the provided values
        for key, value in kwargs.items():
            setattr(self, key, value)
        # update the updatedAt and updatedBy fields
        self.updatedAt = datetime.now(timezone.utc)
        self.updatedById = user_id


# Base DB Update class for all objects
class DBBaseUpdate(BaseModel):
    """Base schema for update payloads with column-length enforcement."""

    model_class: ClassVar[Any] = None

    def update(self, user_id: UUID4, **kwargs):
        # update the fields with the provided values
        for key, value in kwargs.items():
            setattr(self, key, value)
        # update the updatedAt and updatedBy fields
        self.updatedAt = datetime.now(timezone.utc)
        self.updatedById = user_id

    @model_validator(mode="wrap")
    @classmethod
    def _enforce_column_lengths(cls, values, handler):
        instance = handler(values)
        model = cls.model_class or _infer_model_class(cls.__name__)
        if model is None:
            return instance
        for field_name, value in instance.model_dump(
            exclude_unset=True
        ).items():
            if isinstance(value, str):
                max_len = _get_column_max_length(model, field_name)
                if max_len is not None and len(value) > max_len:
                    raise FieldValueTooLong(
                        field=field_name,
                        max_length=max_len,
                        actual_length=len(value),
                    )
        return instance


# Base DB Create class for all objects
class DBBaseCreate(BaseModel):
    """Base schema for creation payloads with column-length enforcement."""

    model_class: ClassVar[Any] = None

    @classmethod
    def create(cls, user_id: UUID4, **kwargs):
        # create a new instance of the model
        new_instance = cls(**kwargs)
        return new_instance

    @model_validator(mode="wrap")
    @classmethod
    def _enforce_column_lengths(cls, values, handler):
        instance = handler(values)
        model = cls.model_class or _infer_model_class(cls.__name__)
        if model is None:
            return instance
        for field_name, value in instance.model_dump(
            exclude_unset=True
        ).items():
            if isinstance(value, str):
                max_len = _get_column_max_length(model, field_name)
                if max_len is not None and len(value) > max_len:
                    raise FieldValueTooLong(
                        field=field_name,
                        max_length=max_len,
                        actual_length=len(value),
                    )
        return instance


# Base DB Create class for all objects
class DBBaseId(BaseModel):
    """Minimal schema exposing only the object's UUID."""

    id: UUID4 | None = Field(
        None, description="Unique identifier of the object"
    )


# pageDetails class for pagination
class PaginationPageDetails(BaseModel):
    """Pagination metadata returned with list responses."""

    page: int = Field(..., description="Current page number (1-based)")
    perPage: int = Field(..., description="Number of items per page")
    pageCount: int = Field(..., description="Total number of pages")
    totalCount: int = Field(
        ..., description="Total number of items across all pages"
    )
