from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict, Field

from .base import DBBase, PaginationPageDetails


# Base Language class
class LanguageBase(DBBase):
    """Base schema for language objects used for locale and mail template assignment."""

    nameEnglish: str | None = Field(
        None, description="Name of the language in English, e.g. German"
    )
    nameTranslated: str | None = Field(
        None,
        description="Name of the language in its own language, e.g. Deutsch",
    )
    key: str | None = Field(
        None, description="Locale key for the language, e.g. de_DE or en_US"
    )
    model_config = ConfigDict(from_attributes=True)


class LanguageInDBBase(LanguageBase):
    """Internal language schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Language(LanguageInDBBase):
    """Full language response schema."""

    nameEnglish: str
    nameTranslated: str
    key: str

    model_config = ConfigDict(from_attributes=True)


# List object of Language
class LanguageList(BaseModel):
    """Paginated list of language objects."""

    pageDetails: PaginationPageDetails
    items: list[Language]
