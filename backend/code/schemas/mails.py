from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict, Field

from .base import DBBase, DBBaseCreate, PaginationPageDetails


# Base Mail class
class MailBase(DBBase):
    """Base schema for outgoing mail log objects."""

    subject: str | None = Field(None, description="Subject line of the email")
    fromName: str | None = Field(None, description="Sender display name")
    fromMail: str | None = Field(None, description="Sender email address")
    toMail: str | None = Field(None, description="Recipient email address")
    sendStatus: str | None = Field(
        None, description="Delivery status of the email, e.g. sent, failed"
    )
    templateId: UUID4 | None = Field(
        None, description="ID of the mail template used to render the email"
    )
    replyTo: str | None = Field(
        None, description="Reply-to email address, if different from the sender"
    )
    user_id: UUID4 | None = Field(
        None, description="ID of the user this email was sent to"
    )
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class MailCreate(DBBaseCreate):
    """Payload for creating a new outgoing mail entry."""

    subject: str = Field(..., description="Subject line of the email")
    fromName: str = Field(..., description="Sender display name")
    fromMail: str = Field(..., description="Sender email address")
    toMail: str = Field(..., description="Recipient email address")
    templateId: UUID4 = Field(
        ..., description="ID of the mail template used to render the email"
    )
    replyTo: str | None = Field(
        None, description="Reply-to email address, if different from the sender"
    )
    user_id: UUID4 = Field(
        ..., description="ID of the user this email is being sent to"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "subject": "Willkommen im OpenVLE-System",
                "fromName": "OpenVLE",
                "fromMail": "noreply@example.com",
                "toMail": "max.mustermann@example.com",
                "templateId": "00000000-0000-0000-0000-000000000001",
                "replyTo": None,
                "user_id": "00000000-0000-0000-0000-000000000002",
            }
        },
    )


# Properties to receive via API on creation of system triggered mails
class MailSystemCreate(DBBaseCreate):
    """Payload for triggering a system-initiated email via a mail action."""

    subject: str = Field(..., description="Subject line of the email")
    mail_action: UUID4 = Field(
        ..., description="ID of the mail action that triggers this email"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "subject": "Systembenachrichtigung",
                "mail_action": "00000000-0000-0000-0000-000000000001",
            }
        },
    )


class MailInDBBase(MailBase):
    """Internal mail schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class Mail(MailInDBBase):
    """Full mail response schema including rendered content and associated event."""

    content_rendered: str | None = Field(
        None, description="Fully rendered HTML content of the email"
    )
    event: UUID4 | None = Field(
        None,
        description="ID of the event this email is associated with, if any",
    )
    model_config = ConfigDict(from_attributes=True)


# List object of Mail
class MailList(BaseModel):
    """Paginated list of mail log objects."""

    pageDetails: PaginationPageDetails
    items: list[Mail]
