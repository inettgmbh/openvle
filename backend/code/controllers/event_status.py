from typing import Optional

from sqlalchemy.orm import Session

from models.event_status import EventStatus
from schemas.event_status import EventStatusCreate, EventStatusUpdate

from .base import CRUDBase


class CRUDEventStatus(
    CRUDBase[EventStatus, EventStatusCreate, EventStatusUpdate]
):
    # Get EventStatus by name
    def get_by_name(self, db: Session, *, name: str) -> EventStatus | None:
        event_status = (
            db.query(EventStatus).filter(EventStatus.name == name).first()
        )
        return event_status


event_status = CRUDEventStatus(EventStatus)
