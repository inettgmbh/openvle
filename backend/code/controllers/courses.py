from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.config import Settings
from core.exceptions import (
    BadRequestError,
    ObjectInUseError,
    RequiredParameterMissingError,
)
from models.courses import Course
from models.events import Event
from models.templates import Template
from schemas.courses import CourseCreate, CourseUpdate, CourseUpdateTemplate

from .base import CRUDBase

settings = Settings()


class CRUDCourse(CRUDBase[Course, CourseCreate, CourseUpdate]):
    # Get Course by name
    def get_by_name(self, db: Session, *, name: str) -> Course | None:
        course = db.query(Course).filter(Course.name == name).first()
        return course

    # Delete Course, blocking while Events still reference it
    def delete(self, db: Session, id: Any):
        # Resolve the object first so a missing Course yields 404, not 409
        self.get(db, id)
        event_count = (
            db.query(func.count(Event.id)).filter(Event.course == id).scalar()
        )
        if event_count:
            raise ObjectInUseError(
                model_name=Course.__name__,
                references={Event.__name__: event_count},
            )
        return super().delete(db, id)

    # Update Course Template
    def update_template(
        self,
        id: Any,
        db: Session,
        request: Request,
        *,
        obj_in: CourseUpdateTemplate,
    ) -> Course:
        self.db_obj = self.get(db, id)
        obj_data = jsonable_encoder(self.db_obj)
        update_data = self._merge_request_with_db_object(obj_in, obj_data)
        # Handling of Course Template
        if "templates" not in update_data:
            raise RequiredParameterMissingError(parameter_name="templates")
        # Handling of Course Templates
        existing_templates = self.db_obj.templates
        template_ids = [t["id"] for t in update_data["templates"]]
        templates_by_id = {
            t.id: t
            for t in db.query(Template)
            .filter(Template.id.in_(template_ids))
            .all()
        }
        templates_list = []
        for template in update_data["templates"]:
            new_template = templates_by_id.get(template["id"])
            if not new_template:
                from core.exceptions import ObjectNotFound

                raise ObjectNotFound(
                    model_name=Template.__name__, id=template["id"]
                )
            if new_template in existing_templates:
                raise BadRequestError(
                    message=f"Template {new_template.name} is already assigned to this course"
                )
            templates_list.append(new_template)
        self.db_obj.templates = existing_templates + templates_list
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    # Delete Template from course
    def delete_template(
        self,
        id: Any,
        db: Session,
        request: Request,
        *,
        obj_in: CourseUpdateTemplate,
    ) -> Course:
        self.db_obj = self.get(db, id)
        obj_data = jsonable_encoder(self.db_obj)
        update_data = self._merge_request_with_db_object(obj_in, obj_data)
        # Handling of Course Template
        if "templates" not in update_data:
            raise RequiredParameterMissingError(parameter_name="templates")
        # Handling of user Templates
        existing_templates: list = self.db_obj.templates
        del_template_ids = [t["id"] for t in update_data["templates"]]
        del_templates_by_id = {
            t.id: t
            for t in db.query(Template)
            .filter(Template.id.in_(del_template_ids))
            .all()
        }
        for template in update_data["templates"]:
            new_template = del_templates_by_id.get(template["id"])
            if not new_template:
                from core.exceptions import ObjectNotFound

                raise ObjectNotFound(
                    model_name=Template.__name__, id=template["id"]
                )
            existing_templates.remove(new_template)
        self.db_obj.templates = existing_templates
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj


course = CRUDCourse(Course)
