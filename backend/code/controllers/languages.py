from typing import Optional

from sqlalchemy.orm import Session

from models.languages import Language as LanguageModel
from schemas.languages import Language

from .base import CRUDBase


class CRUDLanguage(CRUDBase[LanguageModel, Language, Language]):
    # Get Language by key
    def get_by_key(self, db: Session, *, key: str) -> Language | None:
        lang = db.query(LanguageModel).filter(LanguageModel.key == key).first()
        return lang


language = CRUDLanguage(LanguageModel)
