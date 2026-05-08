from typing import Optional

from sqlalchemy.orm import Session

from models import MailAction
from schemas.mails_actions import MailActionCreate

from .base import CRUDBase


class CRUDMailAction(CRUDBase[MailAction, MailActionCreate, MailActionCreate]):
    # Get MailAction by slug
    def get_by_slug(self, db: Session, *, slug: str) -> MailAction | None:
        mail_action = (
            db.query(MailAction).filter(MailAction.slug == slug).first()
        )
        return mail_action


mail_action = CRUDMailAction(MailAction)
