from enum import Enum
from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict

from .base import DBBase, DBBaseCreate, PaginationPageDetails
from .sub_tasks import SubTask


# Task.job_status list
class TaskStatus(Enum):
    queued = "queued"
    processing = "processing"
    failed = "failed"
    success = "success"


# Task base
class TaskBase(DBBase):
    name: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    event_id: UUID4 | None = None
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class TaskCreate(DBBaseCreate):
    name: str
    description: str | None = None
    status: str = "queued"
    event_id: UUID4 | None = None


class TaskInDBBase(TaskBase):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Task(TaskInDBBase):
    model_config = ConfigDict(from_attributes=True)


# List object of Tasks
class TaskList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[Task]
