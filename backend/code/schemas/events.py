import re
from datetime import date, datetime, time

from pydantic import UUID4, BaseModel, ConfigDict, field_validator

from core.exceptions import InvalidFieldValue

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails
from .templates import TemplateIdOnly, TemplateNested
from .virtual_machines import VirtualMachineIdOnly


# Events base
class EventBase(DBBase):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    dateStart: date | None = None
    dateEnd: date | None = None
    timeStart: time | None = None
    timeEnd: time | None = None
    guacamole: bool | None = False
    status: UUID4 | None = None
    course: UUID4 | None = None
    templates: list[TemplateNested] | None = None
    vms: list[VirtualMachineIdOnly] | None = None
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class EventCreate(DBBaseCreate):
    name: str
    slug: str
    description: str | None = None
    dateStart: date = datetime.now().date()
    dateEnd: date | None = datetime.now().date()
    timeStart: time = datetime.now().strftime("%H:%M:%S")
    timeEnd: time | None = datetime.now().strftime("%H:%M:%S")
    guacamole: bool = False
    status: UUID4
    course: UUID4

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
    name: str | None = None
    description: str | None = None
    dateStart: date | None = datetime.now().date()
    dateEnd: date | None = datetime.now().date()
    timeStart: time | None = datetime.now().strftime("%H:%M:%S")
    timeEnd: time | None = datetime.now().strftime("%H:%M:%S")
    course: UUID4 | None = None

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
    dateEnd: date = datetime.now().date()
    timeEnd: time = datetime.now().strftime("%H:%M:%S")

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
    templates: list[TemplateIdOnly]


# Properties to receive via API on updateTemplate
class EventUpdateVirtualMachine(DBBaseUpdate):
    vms: list[VirtualMachineIdOnly]


class EventInDBBase(EventBase):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Event(EventInDBBase):
    templates: list[TemplateIdOnly] | None = None
    vms: list[VirtualMachineIdOnly] | None = None
    moodleCourseId: int | None = None
    deployment_status: str | None = None
    model_config = ConfigDict(from_attributes=True)


# User's Event response model
class UserInEvent(DBBaseUpdate):
    id: UUID4
    name: str
    slug: str
    description: str | None = None
    status: UUID4
    course: UUID4
    role_ids: list

    model_config = ConfigDict(from_attributes=True)


# Class used for when Event is to appear as a nested model and will display key and name
class EventNested(DBBaseUpdate):
    name: str
    slug: str
    status: UUID4
    dateStart: datetime

    model_config = ConfigDict(from_attributes=True)


# VM bulk-action: Migrate
class EventVirtualMachinesMigrate(DBBaseUpdate):
    targetNode: str


# VM bulk-action: HA_Add
class EventVirtualMachinesHaAdd(DBBaseUpdate):
    ha_state: str = "started"
    ha_max_restart: int = 5
    ha_max_relocate: int = 5

    model_config = ConfigDict(from_attributes=True)


# List object of Event
class EventList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[Event]


# List object of UserInEvent
class UserInEventList(BaseModel):
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
