from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict

from .base import DBBase, PaginationPageDetails


# Base Language class
class LanguageBase(DBBase):
    nameEnglish: str | None = None
    nameTranslated: str | None = None
    key: str | None = None
    model_config = ConfigDict(from_attributes=True)


class LanguageInDBBase(LanguageBase):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Language(LanguageInDBBase):
    nameEnglish: str
    nameTranslated: str
    key: str

    model_config = ConfigDict(from_attributes=True)


# List object of Language
class LanguageList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[Language]
