from enum import Enum
from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails


# SubTask.status list
class SubTaskStatus(Enum):
    queued = "queued"
    processing = "processing"
    failed = "failed"
    success = "success"


# SubTask base
class SubTaskBase(DBBase):
    name: str | None = None
    description: str | None = None
    status: SubTaskStatus | None = None
    object_type: str | None = None
    object_id: UUID4 | None = None
    action: str | None = None
    attempt: int | None = None
    parent_task: UUID4 | None = None
    job_id: str | None = None
    response_code: int | None = None
    response_message: str | None = None
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class SubTaskCreate(DBBaseCreate):
    name: str
    description: str | None = None
    object_type: str
    object_id: UUID4 | None = None
    action: str
    job_id: str | None = None
    status: str = "queued"
    attempt: int = 0
    parent_task: UUID4


# SubTask base
class SubTaskUpdate(DBBaseUpdate):
    description: str | None = None
    status: SubTaskStatus | None = None
    object_type: str | None = None
    object_id: UUID4 | None = None
    action: str | None = None
    attempt: int | None = None
    parent_task: UUID4 | None = None
    job_id: str | None = None
    response_code: int | None = None
    response_message: str | None = None
    model_config = ConfigDict(from_attributes=True)


class SubTaskInDBBase(SubTaskBase):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class SubTask(SubTaskInDBBase):
    model_config = ConfigDict(from_attributes=True)


# List object of SubTasks
class SubTaskList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[SubTask]
