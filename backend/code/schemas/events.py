import re
from datetime import date, datetime, time

from pydantic import UUID4, BaseModel, ConfigDict, Field, field_validator

from core.exceptions import InvalidFieldValue

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails
from .templates import TemplateIdOnly, TemplateNested
from .virtual_machines import VirtualMachineIdOnly


# Events base
class EventBase(DBBase):
    """Base schema for event objects with common scheduling and status fields."""

    name: str | None = Field(None, description="Display name of the event")
    slug: str | None = Field(
        None,
        description="Short unique slug (4-8 lowercase alphanumeric characters)",
    )
    description: str | None = Field(
        None, description="Optional description of the event"
    )
    dateStart: date | None = Field(
        None, description="Start date of the event in YYYY-MM-DD format"
    )
    dateEnd: date | None = Field(
        None, description="End date of the event in YYYY-MM-DD format"
    )
    timeStart: time | None = Field(
        None, description="Daily start time of the event"
    )
    timeEnd: time | None = Field(
        None, description="Daily end time of the event"
    )
    guacamole: bool | None = Field(
        False,
        description="Whether Guacamole remote access is enabled for the event",
    )
    status: UUID4 | None = Field(
        None, description="ID of the event status object"
    )
    course: UUID4 | None = Field(
        None, description="ID of the associated course"
    )
    templates: list[TemplateNested] | None = Field(
        None, description="Templates linked to the event"
    )
    vms: list[VirtualMachineIdOnly] | None = Field(
        None, description="Virtual machines linked to the event"
    )
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class EventCreate(DBBaseCreate):
    """Payload for creating a new event."""

    name: str = Field(..., description="Display name of the event")
    slug: str = Field(
        ...,
        description="Short unique slug (4-8 lowercase alphanumeric characters)",
    )
    description: str | None = Field(
        None, description="Optional description of the event"
    )
    dateStart: date = Field(
        datetime.now().date(),
        description="Start date of the event in YYYY-MM-DD format",
    )
    dateEnd: date | None = Field(
        datetime.now().date(),
        description="End date of the event in YYYY-MM-DD format",
    )
    timeStart: time = Field(
        datetime.now().strftime("%H:%M:%S"),
        description="Daily start time of the event",
    )
    timeEnd: time | None = Field(
        datetime.now().strftime("%H:%M:%S"),
        description="Daily end time of the event",
    )
    guacamole: bool = Field(
        False,
        description="Whether Guacamole remote access is enabled for the event",
    )
    status: UUID4 = Field(..., description="ID of the event status object")
    course: UUID4 = Field(..., description="ID of the associated course")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Linux Grundlagen WS24",
                "slug": "lin24",
                "description": "Veranstaltung zu den Grundlagen von Linux",
                "dateStart": "2025-04-01",
                "dateEnd": "2025-07-31",
                "timeStart": "08:00:00",
                "timeEnd": "18:00:00",
                "guacamole": True,
                "status": "53b6993a-57d6-40a6-8d42-e55bf08fac4c",
                "course": "00000000-0000-0000-0000-000000000001",
            }
        }
    )

    # Validate dateStart and dateEnd
    @field_validator("dateStart", "dateEnd", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            pattern = r"\d{4}-\d{2}-\d{2}"  # YYYY-MM-DD
            if re.match(pattern, v):
                return datetime.fromisoformat(v).date()
            else:
                raise InvalidFieldValue(
                    field=v.__name__, value=v, format="YYYY-MM-DD"
                )
        return v

    @field_validator("slug", mode="before")
    @classmethod
    def validate_slug(cls, v):
        # Check length 4-8
        if not (4 <= len(v) <= 8):
            raise InvalidFieldValue(
                field="slug",
                value=v,
                supported_values="Must be between 4 and 8 characters long",
            )

        # Check allowed characters: a-z, 0-9, -, _
        if not re.fullmatch(r"[a-z0-9\-_]+", v):
            raise InvalidFieldValue(
                field="slug",
                value=v,
                supported_values="Lowercase letters, numbers, '-' and '_'",
            )

        return v


# Properties to receive via API on update
class EventUpdate(DBBaseUpdate):
    """Payload for updating an existing event's details."""

    name: str | None = Field(None, description="Display name of the event")
    description: str | None = Field(
        None, description="Optional description of the event"
    )
    dateStart: date | None = Field(
        datetime.now().date(),
        description="Start date of the event in YYYY-MM-DD format",
    )
    dateEnd: date | None = Field(
        datetime.now().date(),
        description="End date of the event in YYYY-MM-DD format",
    )
    timeStart: time | None = Field(
        datetime.now().strftime("%H:%M:%S"),
        description="Daily start time of the event",
    )
    timeEnd: time | None = Field(
        datetime.now().strftime("%H:%M:%S"),
        description="Daily end time of the event",
    )
    course: UUID4 | None = Field(
        None, description="ID of the associated course"
    )

    # Validate dateStart and dateEnd
    @field_validator("dateStart", "dateEnd", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            pattern = r"\d{4}-\d{2}-\d{2}"  # YYYY-MM-DD
            if re.match(pattern, v):
                return datetime.fromisoformat(v).date()
            else:
                raise InvalidFieldValue(
                    field=v.__name__, value=v, format="YYYY-MM-DD"
                )
        return v


# Properties to receive via API on update
class EventUpdateEndDateTime(DBBaseUpdate):
    """Payload for updating only the end date and time of an event."""

    dateEnd: date = Field(
        datetime.now().date(),
        description="New end date of the event in YYYY-MM-DD format",
    )
    timeEnd: time = Field(
        datetime.now().strftime("%H:%M:%S"),
        description="New daily end time of the event",
    )

    # Validate dateEnd
    @field_validator("dateEnd", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            pattern = r"\d{4}-\d{2}-\d{2}"  # YYYY-MM-DD
            if re.match(pattern, v):
                return datetime.fromisoformat(v).date()
            else:
                raise InvalidFieldValue(
                    field=v.__name__, value=v, format="YYYY-MM-DD"
                )
        return v


# Properties to receive via API on updateTemplate
class EventUpdateTemplate(DBBaseUpdate):
    """Payload for replacing the templates assigned to an event."""

    templates: list[TemplateIdOnly] = Field(
        ..., description="List of template IDs to assign to the event"
    )


# Properties to receive via API on updateTemplate
class EventUpdateVirtualMachine(DBBaseUpdate):
    """Payload for replacing the virtual machines assigned to an event."""

    vms: list[VirtualMachineIdOnly] = Field(
        ..., description="List of virtual machine IDs to assign to the event"
    )


class EventInDBBase(EventBase):
    """Internal event schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Event(EventInDBBase):
    """Full event response schema including templates, VMs, and deployment status."""

    templates: list[TemplateIdOnly] | None = None
    vms: list[VirtualMachineIdOnly] | None = None
    moodleCourseId: int | None = Field(
        None, description="Associated Moodle course ID, if any"
    )
    deployment_status: str | None = Field(
        None, description="Current VM deployment status for the event"
    )
    model_config = ConfigDict(from_attributes=True)


# User's Event response model
class UserInEvent(DBBaseUpdate):
    """Event data as seen by an enrolled user, including their role IDs."""

    id: UUID4
    name: str = Field(..., description="Display name of the event")
    slug: str = Field(..., description="Short unique slug of the event")
    description: str | None = Field(
        None, description="Optional description of the event"
    )
    status: UUID4 = Field(..., description="ID of the event status object")
    course: UUID4 = Field(..., description="ID of the associated course")
    role_ids: list = Field(
        ..., description="List of role IDs assigned to the user in this event"
    )

    model_config = ConfigDict(from_attributes=True)


# Class used for when Event is to appear as a nested model and will display key and name
class EventNested(DBBaseUpdate):
    """Minimal event schema for nested references, shows name, slug, status, and start date."""

    name: str = Field(..., description="Display name of the event")
    slug: str = Field(..., description="Short unique slug of the event")
    status: UUID4 = Field(..., description="ID of the event status object")
    dateStart: datetime = Field(
        ..., description="Start date and time of the event"
    )

    model_config = ConfigDict(from_attributes=True)


# VM bulk-action: Migrate
class EventVirtualMachinesMigrate(DBBaseUpdate):
    """Payload for bulk-migrating all VMs in an event to a different Proxmox node."""

    targetNode: str = Field(
        ..., description="Name of the target Proxmox node to migrate VMs to"
    )


# VM bulk-action: HA_Add
class EventVirtualMachinesHaAdd(DBBaseUpdate):
    """Payload for adding all VMs in an event to Proxmox HA."""

    ha_state: str = Field(
        "started", description="Desired HA state for the VMs, e.g. started"
    )
    ha_max_restart: int = Field(
        5, description="Maximum number of HA restart attempts"
    )
    ha_max_relocate: int = Field(
        5, description="Maximum number of HA relocation attempts"
    )

    model_config = ConfigDict(from_attributes=True)


# List object of Event
class EventList(BaseModel):
    """Paginated list of event objects."""

    pageDetails: PaginationPageDetails
    items: list[Event]


# List object of UserInEvent
class UserInEventList(BaseModel):
    """Paginated list of events as seen by an enrolled user."""

    pageDetails: PaginationPageDetails
    items: list[UserInEvent]


# Event status report schemas
class EventStatusReportVmStats(BaseModel):
    total: int
    running: int
    stopped: int
    pending: int  # no ipv4 assigned yet
    protected: int  # prevent_delete = True

    model_config = ConfigDict(from_attributes=True)


class EventStatusReportConnectionStats(BaseModel):
    total: int
    deployed: int  # Guacamole.identifier IS NOT NULL
    pending: int  # Guacamole.identifier IS NULL

    model_config = ConfigDict(from_attributes=True)


class EventStatusReportTaskStats(BaseModel):
    total: int
    queued: int
    processing: int
    success: int
    failed: int

    model_config = ConfigDict(from_attributes=True)


class EventStatusReportSubTask(BaseModel):
    id: UUID4
    name: str
    status: str
    responseMsg: str | None = None
    attempt: str

    model_config = ConfigDict(from_attributes=True)


class EventStatusReportTask(BaseModel):
    id: UUID4
    initiatedAt: datetime
    initiatedBy: UUID4
    subTasks: list[EventStatusReportSubTask]

    model_config = ConfigDict(from_attributes=True)


class EventStatusReport(BaseModel):
    id: UUID4
    currentStatus: str
    statusInitiator: UUID4 | None = None
    vmStats: EventStatusReportVmStats
    connectionStats: EventStatusReportConnectionStats
    taskStats: EventStatusReportTaskStats
    tasks: list[EventStatusReportTask]

    model_config = ConfigDict(from_attributes=True)
