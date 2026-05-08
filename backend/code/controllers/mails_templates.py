from fastapi import Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from models import Language, MailTemplate, ObjectPermission
from schemas.mails_templates import MailTemplateCreate, MailTemplateUpdate

from .base import CRUDBase
from .object_permissions import CRUDObjectPermission


class CRUDMailTemplate(
    CRUDBase[MailTemplate, MailTemplateCreate, MailTemplateUpdate]
):
    # Get MailTemplate by name
    def get_by_name(self, db: Session, *, name: str) -> MailTemplate | None:
        mail_temp = (
            db.query(MailTemplate).filter(MailTemplate.name == name).first()
        )
        return mail_temp

    # Create MailTemplate
    def create(
        self, db: Session, request: Request, *, obj_in: MailTemplateCreate
    ) -> MailTemplate:
        obj_in_data = jsonable_encoder(obj_in)
        self._initialize_object_fields(
            db=db, obj_data_in=obj_in_data, request=request
        )
        self.db_obj.language = CRUDBase(Language).get(db, obj_in.language).id
        self.db_obj = self._commit(db, self.db_obj)
        CRUDObjectPermission(ObjectPermission).create_full(
            db, request, "MailTemplate", self.db_obj.id, request.user.id
        )
        db.refresh(self.db_obj)
        return self.db_obj


mail_template = CRUDMailTemplate(MailTemplate)
