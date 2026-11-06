from fastapi import APIRouter, Depends

from controllers.events import *
from core import dependencies
from core.exceptions import DuplicateFieldException, PermissionDenied
from core.responses import (
    BASE_RESPONSES,
    CRUD_RESPONSES,
    DELETE_RESPONSES,
    READ_RESPONSES,
    WRITE_RESPONSES,
    build_description,
)
from models import (
    Event as EventModel,
    EventsUser as EventsUserModel,
    Guacamole as GuacamoleModel,
    Mail as MailModel,
    Template as TemplateModel,
    VirtualMachine as VirtualMachineModel,
)
from schemas.events import *
from schemas.events_user import EventsUser, EventsUserCreate, EventsUserList
from schemas.guacamole import GuacamoleList
from schemas.mails import MailList
from schemas.templates import TemplateList
from schemas.virtual_machines import VirtualMachineList

router = APIRouter(
    prefix="/events",
    tags=["events"],
    responses=BASE_RESPONSES,
)


# Create new Event
@router.post(
    "/",
    status_code=201,
    response_model=Event,
    operation_id="events_create",
    responses=CRUD_RESPONSES,
    summary="Create Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Creates a new event in the planned state.",
        permission="events_create",
        notes=[
            "Creator is automatically granted `object_full` permission on the new event.",
            "Event is initialized with `Geplant` status — required before a start can be triggered.",
            "The referenced course must be fully configured for deployment to succeed when the event is started.",
        ],
    ),
)
def create_events(
    *,
    events_in: EventCreate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "events_create", request, db=db
    ).has_permission():
        # Check if Event with the same name already exists
        db_name = CRUDEvent(EventModel).get_by_name(db, name=events_in.name)
        if db_name:
            raise DuplicateFieldException(field="name")
        # Check if slug is unique
        if CRUDEvent(EventModel).get_by_slug(db, slug=events_in.slug):
            raise DuplicateFieldException(field="slug")
        return CRUDEvent(EventModel).create(
            db=db, request=request, obj_in=events_in
        )
    else:
        raise PermissionDenied()


# Returns all Event
@router.get(
    "/",
    status_code=200,
    response_model=EventList,
    operation_id="events_read_all",
    summary="Get Events",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a paginated list of all events visible to the requesting user.",
        permission="events_read",
    ),
)
def get_events(
    request: Request,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "events_read", request, db=db
    ).has_permission():
        return CRUDEvent(EventModel).get_multi(
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDEvent(EventModel).get_multi_auth(
            request=request,
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Get Event status report
@router.get(
    "/{id}/status",
    status_code=200,
    response_model=EventStatusReport,
    operation_id="events_read_status",
    responses=READ_RESPONSES,
    summary="Get Event Status Report",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a status report for an event including VM counts, Guacamole connection stats, and task progress.",
        permission="events_read",
    ),
)
def get_event_status(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "events_read", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).get_status(db, id)
    else:
        raise PermissionDenied()


# Get Event with ID
@router.get(
    "/{id}",
    status_code=200,
    response_model=Event,
    operation_id="events_read_one",
    responses=READ_RESPONSES,
    summary="Get Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a single event by ID.",
        permission="events_read",
    ),
)
def get_event(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "events_read", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).get(db, id)
    else:
        raise PermissionDenied()


# Update Event
@router.put(
    "/{id}",
    status_code=200,
    response_model=Event,
    operation_id="events_update",
    responses=CRUD_RESPONSES,
    summary="Update Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Updates event metadata.",
        permission="events_update",
        notes=[
            "Blocked if the event has been started — allowed only in `Geplant`, `Core Fehler`, or `Deployment Fehler` status.",
        ],
    ),
)
def update_event(
    *,
    id: UUID4,
    events_in: EventUpdate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "events_update", request, id, db=db
    ).has_permission():
        # Check if Event with the same name already exists
        db_name = CRUDEvent(EventModel).get_by_name(db, name=events_in.name)
        if db_name and db_name.id != id:
            raise DuplicateFieldException(field="name")
        return CRUDEvent(EventModel).update(
            db=db, request=request, id=id, obj_in=events_in
        )
    else:
        raise PermissionDenied()


# Update Event End date/time
@router.post(
    "/{id}/end-date",
    status_code=200,
    response_model=Event,
    operation_id="events_update_end",
    responses=WRITE_RESPONSES,
    summary="Update Event end date/time",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Updates the end date and time of an event.",
        permission="events_update",
        notes=[
            "Allowed in `Geplant`, `Core Fehler`, and `Aktiv` status — the only update permitted on a running event.",
        ],
    ),
)
def update_event_end(
    *,
    id: UUID4,
    events_in: EventUpdateEndDateTime,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "events_update", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).update_end_datetime(
            db=db, request=request, id=id, obj_in=events_in
        )
    else:
        raise PermissionDenied()


# Delete Event with ID
@router.delete(
    "/{id}",
    status_code=200,
    operation_id="events_delete",
    responses=DELETE_RESPONSES,
    summary="Delete Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Deletes an event by ID.",
        permission="events_delete",
    ),
)
def delete_events(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "events_delete", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).delete(db, id)
    else:
        raise PermissionDenied()


# Add user to event
@router.post(
    "/{id}/users",
    status_code=201,
    response_model=EventsUser,
    operation_id="events_users_add",
    responses=WRITE_RESPONSES,
    summary="Add User to Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Adds a user/role combination to an event.",
        permission="events_update",
    ),
)
def add_events_user(
    *,
    id: UUID4,
    events_user_in: EventsUserCreate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "events_update", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).add_user(
            db=db, request=request, obj_in=events_user_in, id=id
        )
    else:
        raise PermissionDenied()


# Get User/Role combinations for event
@router.get(
    "/{id}/users",
    status_code=200,
    response_model=EventsUserList,
    operation_id="events_users_read_all",
    responses=READ_RESPONSES,
    summary="Get all Users associated with Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns all user/role combinations associated with an event.",
        permission="events_read",
    ),
)
def get_events_users(
    request: Request,
    id: UUID4,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "events_read", request, id, db=db
    ).has_permission():
        return CRUDBase(EventsUserModel).get_multi_foreign_key(
            foreign_key_field="event_id",
            foreign_key_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDBase(EventsUserModel).get_multi_foreign_key_auth(
            request=request,
            foreign_key_field="event_id",
            foreign_key_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Remove user/role combo from event
@router.delete(
    "/{id}/users/{user_id}/roles/{role_id}",
    status_code=200,
    operation_id="events_user_delete",
    responses=WRITE_RESPONSES,
    summary="Remove User/Role combination from Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Removes a specific user/role combination from an event.",
        permission="events_update",
    ),
)
def delete_event_user(
    *,
    id: UUID4,
    user_id: UUID4,
    role_id: UUID4,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "events_update", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).delete_event_user(
            db=db,
            request=request,
            event_id=id,
            role_id=role_id,
            user_id=user_id,
        )
    else:
        raise PermissionDenied()


# Get all Mails for Event
@router.get(
    "/{id}/mails",
    status_code=200,
    response_model=MailList,
    operation_id="events_mails_read_all",
    responses=READ_RESPONSES,
    summary="Get all Mails associated with Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns all mail records associated with an event.",
        permission="events_read",
    ),
)
def get_events_mails(
    request: Request,
    id: UUID4,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
) -> dict:
    if dependencies.PermissionChecker(
        "events_read", request, id, db=db
    ).has_permission():
        return CRUDBase(MailModel).get_multi_foreign_key(
            foreign_key_field="event",
            foreign_key_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDBase(MailModel).get_multi_foreign_key_auth(
            request=request,
            foreign_key_field="event",
            foreign_key_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Get all Templates for Event
@router.get(
    "/{id}/templates",
    status_code=200,
    response_model=TemplateList,
    operation_id="events_templates_read_all",
    responses=READ_RESPONSES,
    summary="Get all Templates associated with Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns all templates linked to an event.",
        permission="events_read",
    ),
)
def get_events_templates(
    request: Request,
    id: UUID4,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
) -> dict:
    if dependencies.PermissionChecker(
        "events_read", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).get_multi_association(
            parent_model=TemplateModel,
            child_model=EventModel,
            parent_field_name="events",
            child_field_name="id",
            field_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDEvent(EventModel).get_multi_association_auth(
            request=request,
            parent_model=TemplateModel,
            child_model=EventModel,
            parent_field_name="events",
            child_field_name="id",
            field_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Add Templates to Event
@router.post(
    "/{id}/templates",
    status_code=200,
    response_model=Event,
    operation_id="events_templates_add",
    responses=WRITE_RESPONSES,
    summary="Add Templates to Event. If the Event is active, VirtualMachines are deployed for new Template.",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Links one or more templates to an event. If the event is currently active, virtual machines are asynchronously deployed for any newly added templates.",
        permission="events_templates_update",
        notes=[
            "Each added template must have a valid `proxmoxId` for VM deployment to succeed when the event is active.",
        ],
    ),
)
def add_events_templates(
    request: Request,
    id: UUID4,
    obj_in: EventUpdateTemplate,
    db: Session = Depends(dependencies.get_db),
) -> dict:
    if dependencies.PermissionChecker(
        "events_templates_update", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).add_templates(
            db=db, id=id, request=request, obj_in=obj_in
        )
    else:
        raise PermissionDenied()


# Get VMs for Event
@router.get(
    "/{id}/virtual-machines",
    status_code=200,
    response_model=VirtualMachineList,
    operation_id="events_virtual_machines_read_all",
    responses=READ_RESPONSES,
    summary="Get all VirtualMachine associated with Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns all virtual machines associated with an event.",
        permission="events_read",
    ),
)
def get_events_virtual_machines(
    request: Request,
    id: UUID4,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
) -> dict:
    if dependencies.PermissionChecker(
        "events_read", request, id, db=db
    ).has_permission():
        return CRUDBase(VirtualMachineModel).get_multi_foreign_key(
            foreign_key_field="event",
            foreign_key_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDBase(VirtualMachineModel).get_multi_foreign_key_auth(
            request=request,
            foreign_key_field="event",
            foreign_key_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Add VM to event
@router.post(
    "/{id}/virtual-machines",
    status_code=201,
    response_model=Event,
    operation_id="events_virtual_machines_add",
    responses=WRITE_RESPONSES,
    summary="Add VirtualMachine to Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Associates an existing virtual machine with an event.",
        permission="events_update",
    ),
)
def add_events_virtual_machines(
    *,
    id: UUID4,
    events_vms_in: EventUpdateVirtualMachine,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "events_update", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).add_virtual_machines(
            db=db, request=request, obj_in=events_vms_in, id=id
        )
    else:
        raise PermissionDenied()


# Delete Template from Event
@router.delete(
    "/{id}/virtual-machines",
    status_code=200,
    response_model=Event,
    operation_id="events_virtual_machines_delete",
    responses=WRITE_RESPONSES,
    summary="Delete VirtualMachine from Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Removes a virtual machine association from an event.",
        permission="events_update",
    ),
)
def delete_event_virtual_machines(
    *,
    id: UUID4,
    events_vms_in: EventUpdateVirtualMachine,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "events_update", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).delete_virtual_machine(
            db=db, request=request, id=id, obj_in=events_vms_in
        )
    else:
        raise PermissionDenied()


# Event VirtualMachines bulk actions: start
@router.post(
    "/{id}/virtual-machines/bulk-actions/start",
    status_code=200,
    operation_id="events_virtual_machines_bulk_actions_start",
    responses=WRITE_RESPONSES,
    summary="Start all VirtualMachines related to an Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Enqueues a start operation for all virtual machines associated with an event.",
        permission="events_update",
        is_async=True,
    ),
)
def events_virtual_machines_bulk_actions_start(
    request: Request,
    id: UUID4,
    db: Session = Depends(dependencies.get_db),
) -> dict:
    if dependencies.PermissionChecker(
        "events_update", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).virtual_machines_start(
            db=db, request=request, id=id
        )
    else:
        raise PermissionDenied()


# Event VirtualMachines bulk actions: stop
@router.post(
    "/{id}/virtual-machines/bulk-actions/stop",
    status_code=200,
    operation_id="events_virtual_machines_bulk_actions_stop",
    responses=WRITE_RESPONSES,
    summary="Stop all VirtualMachines related to an Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Enqueues a stop operation for all virtual machines associated with an event.",
        permission="events_update",
        is_async=True,
    ),
)
def events_virtual_machines_bulk_actions_stop(
    request: Request,
    id: UUID4,
    db: Session = Depends(dependencies.get_db),
) -> dict:
    if dependencies.PermissionChecker(
        "events_update", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).virtual_machines_stop(
            db=db, request=request, id=id
        )
    else:
        raise PermissionDenied()


# Event VirtualMachines bulk actions: pause
@router.post(
    "/{id}/virtual-machines/bulk-actions/pause",
    status_code=200,
    operation_id="events_virtual_machines_bulk_actions_pause",
    responses=WRITE_RESPONSES,
    summary="Pause all VirtualMachines related to an Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Enqueues a pause operation for all virtual machines associated with an event.",
        permission="events_update",
        is_async=True,
    ),
)
def events_virtual_machines_bulk_actions_pause(
    request: Request,
    id: UUID4,
    db: Session = Depends(dependencies.get_db),
) -> dict:
    if dependencies.PermissionChecker(
        "events_update", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).virtual_machines_pause(
            db=db, request=request, id=id
        )
    else:
        raise PermissionDenied()


# Event VirtualMachines bulk actions: reset
@router.post(
    "/{id}/virtual-machines/bulk-actions/reset",
    status_code=200,
    operation_id="events_virtual_machines_bulk_actions_reset",
    responses=WRITE_RESPONSES,
    summary="Reset all VirtualMachines related to an Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Enqueues a hard reset for all virtual machines associated with an event.",
        permission="events_update",
        is_async=True,
    ),
)
def events_virtual_machines_bulk_actions_reset(
    *,
    id: UUID4,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "events_update", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).virtual_machines_reset(
            db=db, request=request, id=id
        )
    else:
        raise PermissionDenied()


# Event VirtualMachines bulk actions: reboot
@router.post(
    "/{id}/virtual-machines/bulk-actions/reboot",
    status_code=200,
    operation_id="events_virtual_machines_bulk_actions_reboot",
    responses=WRITE_RESPONSES,
    summary="Reboot all VirtualMachines related to an Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Enqueues a graceful reboot for all virtual machines associated with an event.",
        permission="events_update",
        is_async=True,
    ),
)
def events_virtual_machines_bulk_actions_reboot(
    *,
    id: UUID4,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "events_update", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).virtual_machines_reboot(
            db=db, request=request, id=id
        )
    else:
        raise PermissionDenied()


# Event VirtualMachines bulk actions: shutdown
@router.post(
    "/{id}/virtual-machines/bulk-actions/shutdown",
    status_code=200,
    operation_id="events_virtual_machines_bulk_actions_shutdown",
    responses=WRITE_RESPONSES,
    summary="Shutdown all VirtualMachines related to an Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Enqueues a graceful shutdown for all virtual machines associated with an event.",
        permission="events_update",
        is_async=True,
    ),
)
def events_virtual_machines_bulk_actions_shutdown(
    *,
    id: UUID4,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "events_update", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).virtual_machines_shutdown(
            db=db, request=request, id=id
        )
    else:
        raise PermissionDenied()


# Event VirtualMachines bulk actions: resume
@router.post(
    "/{id}/virtual-machines/bulk-actions/resume",
    status_code=200,
    operation_id="events_virtual_machines_bulk_actions_resume",
    responses=WRITE_RESPONSES,
    summary="Resume all VirtualMachines related to an Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Enqueues a resume operation for all paused virtual machines associated with an event.",
        permission="events_update",
        is_async=True,
    ),
)
def events_virtual_machines_bulk_actions_resume(
    *,
    id: UUID4,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "events_update", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).virtual_machines_resume(
            db=db, request=request, id=id
        )
    else:
        raise PermissionDenied()


# Event VirtualMachines bulk actions: hibernate
@router.post(
    "/{id}/virtual-machines/bulk-actions/hibernate",
    status_code=200,
    operation_id="events_virtual_machines_bulk_actions_hibernate",
    responses=WRITE_RESPONSES,
    summary="Hibernate all VirtualMachines related to an Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Enqueues a hibernate operation for all virtual machines associated with an event.",
        permission="events_update",
        is_async=True,
    ),
)
def events_virtual_machines_bulk_actions_hibernate(
    *,
    id: UUID4,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "events_update", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).virtual_machines_hibernate(
            db=db, request=request, id=id
        )
    else:
        raise PermissionDenied()


# Event VirtualMachines bulk actions: Migrate
@router.post(
    "/{id}/virtual-machines/bulk-actions/migrate",
    status_code=200,
    operation_id="events_virtual_machines_bulk_actions_migrate",
    responses=WRITE_RESPONSES,
    summary="Migrate all VirtualMachines related to an Event to specified Proxmox node",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Enqueues a migration of all virtual machines associated with an event to the specified Proxmox node.",
        permission="events_update",
        is_async=True,
    ),
)
def events_virtual_machines_bulk_actions_migrate(
    *,
    id: UUID4,
    obj_in: EventVirtualMachinesMigrate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "events_update", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).virtual_machines_migrate(
            db=db, request=request, id=id, target_node=obj_in.targetNode
        )
    else:
        raise PermissionDenied()


# Event VirtualMachines bulk actions: HA-Add
@router.post(
    "/{id}/virtual-machines/bulk-actions/ha",
    status_code=200,
    operation_id="events_virtual_machines_bulk_actions_ha_add",
    responses=WRITE_RESPONSES,
    summary="Update all VirtualMachines related to an Event with new HA parameters",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Enqueues an HA configuration update for all virtual machines associated with an event.",
        permission="events_update",
        is_async=True,
    ),
)
def events_virtual_machines_bulk_actions_ha_add(
    *,
    id: UUID4,
    obj_in: EventVirtualMachinesHaAdd,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "events_update", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).virtual_machines_ha_add(
            db=db, request=request, id=id, obj_in=obj_in
        )
    else:
        raise PermissionDenied()


# Event VirtualMachines bulk actions: HA-remove
@router.delete(
    "/{id}/virtual-machines/bulk-actions/ha",
    status_code=200,
    operation_id="events_virtual_machines_bulk_actions_ha_remove",
    responses=WRITE_RESPONSES,
    summary="Remove all VirtualMachines related to an Event from Proxmox cluster HA",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Enqueues removal of all virtual machines associated with an event from Proxmox cluster HA.",
        permission="events_update",
        is_async=True,
    ),
)
def events_virtual_machines_bulk_actions_ha_remove(
    *,
    id: UUID4,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "events_update", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).virtual_machines_ha_remove(
            db=db, request=request, id=id
        )
    else:
        raise PermissionDenied()


# Get all Guacamole for Event
@router.get(
    "/{id}/guacamole",
    status_code=200,
    response_model=GuacamoleList,
    operation_id="events_guacamole_read_all",
    responses=READ_RESPONSES,
    summary="Get all Guacamole associated with Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns all Guacamole connection records associated with an event.",
        permission="events_read",
    ),
)
def get_events_guacamole(
    request: Request,
    id: UUID4,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
) -> dict:
    if dependencies.PermissionChecker(
        "events_read", request, id, db=db
    ).has_permission():
        return CRUDBase(GuacamoleModel).get_multi_foreign_key(
            foreign_key_field="eventId",
            foreign_key_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDBase(GuacamoleModel).get_multi_foreign_key_auth(
            request=request,
            foreign_key_field="eventId",
            foreign_key_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Event Guacamoles bulk actions: create
@router.post(
    "/{id}/guacamoles/bulk-actions/create",
    status_code=200,
    operation_id="events_guacamoles_bulk_actions_create",
    responses=WRITE_RESPONSES,
    summary="Create all Guacamole connections related to an Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Enqueues provisioning of all Guacamole connections associated with an event.",
        permission="events_update",
        is_async=True,
        notes=[
            "Each virtual machine must have a valid IPv4 address before its Guacamole connection can be provisioned.",
        ],
    ),
)
def events_guacamoles_bulk_actions_create(
    *,
    id: UUID4,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "events_update", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).guacamoles_create(
            db=db, request=request, id=id
        )
    else:
        raise PermissionDenied()


# Event Guacamoles bulk actions: delete
@router.post(
    "/{id}/guacamoles/bulk-actions/delete",
    status_code=200,
    operation_id="events_guacamoles_bulk_actions_delete",
    responses=WRITE_RESPONSES,
    summary="Delete all Guacamole connections related to an Event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Enqueues deletion of all Guacamole connections associated with an event.",
        permission="events_update",
        is_async=True,
    ),
)
def events_guacamoles_bulk_actions_delete(
    *,
    id: UUID4,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "events_update", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).guacamoles_delete(
            db=db, request=request, id=id
        )
    else:
        raise PermissionDenied()


# Events actions - START
@router.post(
    "/{id}/actions/start",
    status_code=200,
    response_model=Event,
    operation_id="events_actions_start",
    responses=WRITE_RESPONSES,
    summary="Start event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Triggers the event start lifecycle — deploys virtual machines, enrolls users in Moodle, and provisions Guacamole connections.",
        permission="events_actions_start",
        is_async=True,
        notes=[
            "Event must be in `Geplant` status.",
            "Each template linked to the event must have a valid `proxmoxId` before deployment can proceed.",
            "Moodle course enrollment is also enqueued if a course is linked to the event.",
        ],
    ),
)
def events_actions_start(
    *, id: UUID4, db: Session = Depends(dependencies.get_db), request: Request
) -> dict:
    if dependencies.PermissionChecker(
        "events_actions_start", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).actions_start(
            db=db, request=request, id=id
        )
    else:
        raise PermissionDenied()


# Events actions - STOP
@router.post(
    "/{id}/actions/stop",
    status_code=200,
    response_model=Event,
    operation_id="events_actions_stop",
    responses=WRITE_RESPONSES,
    summary="Stop event",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Triggers the event stop lifecycle — decommissions virtual machines, unenrolls users from Moodle, and removes Guacamole connections.",
        permission="events_actions_stop",
        is_async=True,
        notes=[
            "Event must be in an active status (`Aktiv`, `Deploying`, or `Deployment Fehler`) to be stopped.",
        ],
    ),
)
def events_actions_stop(
    *, id: UUID4, db: Session = Depends(dependencies.get_db), request: Request
) -> dict:
    if dependencies.PermissionChecker(
        "events_actions_stop", request, id, db=db
    ).has_permission():
        return CRUDEvent(EventModel).actions_stop(db=db, request=request, id=id)
    else:
        raise PermissionDenied()
