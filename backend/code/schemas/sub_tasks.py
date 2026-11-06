from enum import Enum
from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict, Field

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails


# SubTask.status list
class SubTaskStatus(Enum):
    """Enumeration of possible sub-task execution statuses."""

    queued = "queued"
    processing = "processing"
    failed = "failed"
    success = "success"


# SubTask base
class SubTaskBase(DBBase):
    """Base schema for sub-task objects that track individual operations within a task."""

    name: str | None = Field(None, description="Display name of the sub-task")
    description: str | None = Field(
        None, description="Optional description of the sub-task"
    )
    status: SubTaskStatus | None = Field(
        None,
        description="Current execution status. One of: queued, processing, failed, success",
    )
    object_type: str | None = Field(
        None,
        description="Type of the object this sub-task acts on, e.g. VirtualMachine",
    )
    object_id: UUID4 | None = Field(
        None, description="ID of the object this sub-task acts on"
    )
    action: str | None = Field(
        None,
        description="Action being performed by this sub-task, e.g. start, stop",
    )
    attempt: int | None = Field(
        None, description="Number of execution attempts made so far"
    )
    parent_task: UUID4 | None = Field(
        None, description="ID of the parent task this sub-task belongs to"
    )
    job_id: str | None = Field(
        None,
        description="External job/queue ID for tracking the underlying worker job",
    )
    response_code: int | None = Field(
        None,
        description="HTTP or system response code from the last execution attempt",
    )
    response_message: str | None = Field(
        None,
        description="Response message or error detail from the last execution attempt",
    )
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class SubTaskCreate(DBBaseCreate):
    """Payload for creating a new sub-task within a parent task."""

    name: str = Field(..., description="Display name of the sub-task")
    description: str | None = Field(
        None, description="Optional description of the sub-task"
    )
    object_type: str = Field(
        ...,
        description="Type of the object this sub-task acts on, e.g. VirtualMachine",
    )
    object_id: UUID4 | None = Field(
        None, description="ID of the object this sub-task acts on"
    )
    action: str = Field(
        ...,
        description="Action being performed by this sub-task, e.g. start, stop",
    )
    job_id: str | None = Field(
        None,
        description="External job/queue ID for tracking the underlying worker job",
    )
    status: str = Field(
        "queued",
        description="Initial execution status. One of: queued, processing, failed, success",
    )
    attempt: int = Field(0, description="Initial attempt count, normally 0")
    parent_task: UUID4 = Field(
        ..., description="ID of the parent task this sub-task belongs to"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "VM starten",
                "description": "Startet die VM nach dem Erstellen",
                "object_type": "VirtualMachine",
                "object_id": "00000000-0000-0000-0000-000000000001",
                "action": "start",
                "job_id": None,
                "status": "queued",
                "attempt": 0,
                "parent_task": "00000000-0000-0000-0000-000000000002",
            }
        }
    )


# SubTask base
class SubTaskUpdate(DBBaseUpdate):
    """Payload for updating an existing sub-task's status and result fields."""

    description: str | None = Field(
        None, description="Optional description of the sub-task"
    )
    status: SubTaskStatus | None = Field(
        None,
        description="Updated execution status. One of: queued, processing, failed, success",
    )
    object_type: str | None = Field(
        None, description="Type of the object this sub-task acts on"
    )
    object_id: UUID4 | None = Field(
        None, description="ID of the object this sub-task acts on"
    )
    action: str | None = Field(
        None, description="Action being performed by this sub-task"
    )
    attempt: int | None = Field(None, description="Updated attempt count")
    parent_task: UUID4 | None = Field(
        None, description="ID of the parent task this sub-task belongs to"
    )
    job_id: str | None = Field(
        None,
        description="External job/queue ID for tracking the underlying worker job",
    )
    response_code: int | None = Field(
        None,
        description="HTTP or system response code from the last execution attempt",
    )
    response_message: str | None = Field(
        None,
        description="Response message or error detail from the last execution attempt",
    )
    model_config = ConfigDict(from_attributes=True)


class SubTaskInDBBase(SubTaskBase):
    """Internal sub-task schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class SubTask(SubTaskInDBBase):
    """Full sub-task response schema."""

    model_config = ConfigDict(from_attributes=True)


# List object of SubTasks
class SubTaskList(BaseModel):
    """Paginated list of sub-task objects."""

    pageDetails: PaginationPageDetails
    items: list[SubTask]
