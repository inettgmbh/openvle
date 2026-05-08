from fastapi import APIRouter, Depends, Request
from pydantic import UUID4
from sqlalchemy.orm import Session

from controllers.event_status import *
from core import dependencies
from core.exceptions import PermissionDenied
from models.event_status import EventStatus as EventStatusModel
from schemas.event_status import *

router = APIRouter(
    prefix="/status/events",
    tags=["status/events"],
    responses={404: {"detail": "Not found"}},
)


# Returns all EventStatus
@router.get(
    "/",
    status_code=200,
    response_model=EventStatusList,
    operation_id="status_events_read_all",
    summary="Get Event Statuses",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_event_status(
    request: Request,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(None, request, db=db).has_permission():
        return CRUDEventStatus(EventStatusModel).get_multi(
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        raise PermissionDenied()


# Get EventStatus with ID
@router.get(
    "/{id}",
    status_code=200,
    response_model=EventStatus,
    operation_id="status_events_read_one",
    summary="Get Event Status",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_event_status(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        None, request, id, db=db
    ).has_permission():
        return CRUDEventStatus(EventStatusModel).get(db, id)
    else:
        raise PermissionDenied()
