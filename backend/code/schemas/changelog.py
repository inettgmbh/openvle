from datetime import datetime
from typing import List

from pydantic import UUID4, BaseModel, ConfigDict

from .base import PaginationPageDetails


# Base DB class for all objects
class Changelog(BaseModel):
    id: UUID4
    timestamp: datetime
    valueOld: str
    valueNew: str
    object: str
    objectId: UUID4
    userId: UUID4

    model_config = ConfigDict(from_attributes=True)


# List object of Event
class ChangelogList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[Changelog]
