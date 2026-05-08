from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict

from .base import DBBase, DBBaseCreate, PaginationPageDetails


# Base Mail class
class MailBase(DBBase):
    subject: str | None = None
    fromName: str | None = None
    fromMail: str | None = None
    toMail: str | None = None
    sendStatus: str | None = None
    templateId: UUID4 | None = None
    replyTo: str | None = None
    user_id: UUID4 | None = None
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class MailCreate(DBBaseCreate):
    subject: str
    fromName: str
    fromMail: str
    toMail: str
    templateId: UUID4
    replyTo: str | None = None
    user_id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation of system triggered mails
class MailSystemCreate(DBBaseCreate):
    subject: str
    mail_action: UUID4

    model_config = ConfigDict(from_attributes=True)


class MailInDBBase(MailBase):
    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Mail(MailInDBBase):
    content_rendered: str | None = None
    event: UUID4 | None = None
    model_config = ConfigDict(from_attributes=True)


# List object of Mail
class MailList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[Mail]
