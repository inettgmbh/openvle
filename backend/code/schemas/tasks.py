from enum import Enum
from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict, Field

from .base import DBBase, DBBaseCreate, PaginationPageDetails
from .sub_tasks import SubTask


# Task.job_status list
class TaskStatus(Enum):
    """Enumeration of possible task execution statuses."""

    queued = "queued"
    processing = "processing"
    failed = "failed"
    success = "success"


# Task base
class TaskBase(DBBase):
    """Base schema for background task objects."""

    name: str | None = Field(None, description="Display name of the task")
    description: str | None = Field(
        None, description="Optional description of the task"
    )
    status: TaskStatus | None = Field(
        None,
        description="Current execution status. One of: queued, processing, failed, success",
    )
    event_id: UUID4 | None = Field(
        None, description="ID of the event this task is associated with, if any"
    )
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class TaskCreate(DBBaseCreate):
    """Payload for creating a new background task."""

    name: str = Field(..., description="Display name of the task")
    description: str | None = Field(
        None, description="Optional description of the task"
    )
    status: str = Field(
        "queued",
        description="Initial execution status. One of: queued, processing, failed, success",
    )
    event_id: UUID4 | None = Field(
        None, description="ID of the event this task is associated with, if any"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "VMs für Veranstaltung erstellen",
                "description": "Erstellt alle VMs für die Veranstaltung",
                "status": "queued",
                "event_id": "00000000-0000-0000-0000-000000000001",
            }
        }
    )


class TaskInDBBase(TaskBase):
    """Internal task schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Task(TaskInDBBase):
    """Full task response schema."""

    model_config = ConfigDict(from_attributes=True)


# List object of Tasks
class TaskList(BaseModel):
    """Paginated list of task objects."""

    pageDetails: PaginationPageDetails
    items: list[Task]
