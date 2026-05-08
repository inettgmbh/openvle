from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from core.config import Settings
from models import Event, Task
from schemas.tasks import TaskCreate

from .base import CRUDBase

settings = Settings()


class CRUDTask(CRUDBase[Task, TaskCreate, TaskCreate]):
    # Create Task
    def create(
        self, db: Session, request: Request = None, *, obj_in: TaskCreate
    ) -> Task:
        obj_in_data = jsonable_encoder(obj_in)
        self._initialize_object_fields(
            db=db, obj_data_in=obj_in_data, request=request
        )
        # Check if Event id was provided and if Event exists
        if obj_in.event_id:
            event = CRUDBase(Event).get(db, obj_in.event_id)
            self.db_obj.event_id = event.id
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj


template = CRUDTask(Task)
