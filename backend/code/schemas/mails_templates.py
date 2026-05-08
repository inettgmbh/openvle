import re

from pydantic import UUID4, BaseModel, ConfigDict, field_validator

from core.exceptions import InvalidFieldValue, MailSubjectTooLong

from .base import DBBase, DBBaseCreate, DBBaseUpdate, PaginationPageDetails

_SUBJECT_MAX_LENGTH = 75
_SUBJECT_PLACEHOLDER_BUDGET = (
    67  # max remaining chars when placeholder is present
)
# Matches {{event.slug}} with any amount of whitespace inside the braces
_SUBJECT_SLUG_PLACEHOLDER_RE = re.compile(r"\{\{\s*event\.slug\s*\}\}")


def _validate_mail_subject(value: str) -> str:
    if _SUBJECT_SLUG_PLACEHOLDER_RE.search(value):
        remaining = _SUBJECT_SLUG_PLACEHOLDER_RE.sub("", value)
        if len(remaining) > _SUBJECT_PLACEHOLDER_BUDGET:
            raise MailSubjectTooLong(
                max_length=_SUBJECT_PLACEHOLDER_BUDGET,
                actual_length=len(remaining),
            )
    elif len(value) > _SUBJECT_MAX_LENGTH:
        raise MailSubjectTooLong(
            max_length=_SUBJECT_MAX_LENGTH, actual_length=len(value)
        )
    return value


# Base MailTemplate class
class MailTemplateBase(DBBase):
    name: str | None = None
    subject: str | None = None
    description: str | None = None
    fromName: str | None = None
    fromMail: str | None = None
    contentHTML: str | None = None
    contentPlain: str | None = None
    language: UUID4 | None = None
    protected: bool | None = None
    replyTo: str | None = None
    mail_action: UUID4 | None = None
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class MailTemplateCreate(DBBaseCreate):
    name: str
    subject: str
    description: str | None = None
    fromName: str | None = None
    fromMail: str | None = None
    contentHTML: str
    contentPlain: str
    language: UUID4
    protected: bool
    replyTo: str | None = None
    mail_action: UUID4 | None = None

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, value):
        return _validate_mail_subject(value)


# Properties to receive via API on update
class MailTemplateUpdate(DBBaseUpdate):
    name: str | None = None
    subject: str | None = None
    description: str | None = None
    fromName: str | None = None
    fromMail: str | None = None
    contentHTML: str | None = None
    contentPlain: str | None = None
    language: UUID4 | None = None
    protected: bool | None = None
    replyTo: str | None = None
    mail_action: UUID4 | None = None

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, value):
        if value is None:
            return value
        return _validate_mail_subject(value)

    model_config = ConfigDict(from_attributes=True)


class MailTemplateInDBBase(MailTemplateBase):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class MailTemplate(MailTemplateInDBBase):
    model_config = ConfigDict(from_attributes=True)


# Class used for when MailTemplate is to appear as a nested model and will only display ID
class MailTemplateNested(DBBaseUpdate):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# List object of MailTemplate
class MailTemplateList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[MailTemplate]
