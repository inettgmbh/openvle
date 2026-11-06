import re

from pydantic import UUID4, BaseModel, ConfigDict, Field, field_validator

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
    """Base schema for email template objects used to render outgoing emails."""

    name: str | None = Field(
        None, description="Display name of the mail template"
    )
    subject: str | None = Field(
        None,
        description="Email subject line (max 75 chars, supports {{event.slug}} placeholder)",
    )
    description: str | None = Field(
        None, description="Optional description of the mail template"
    )
    fromName: str | None = Field(
        None,
        description="Sender display name used when sending emails with this template",
    )
    fromMail: str | None = Field(
        None,
        description="Sender email address used when sending emails with this template",
    )
    contentHTML: str | None = Field(
        None, description="HTML content of the email template"
    )
    contentPlain: str | None = Field(
        None, description="Plain-text content of the email template"
    )
    language: UUID4 | None = Field(
        None, description="ID of the language this template is written in"
    )
    protected: bool | None = Field(
        None, description="If true, the template cannot be deleted"
    )
    replyTo: str | None = Field(
        None,
        description="Reply-to email address for emails sent with this template",
    )
    mail_action: UUID4 | None = Field(
        None, description="ID of the mail action that uses this template"
    )
    model_config = ConfigDict(from_attributes=True)


# Properties to receive via API on creation
class MailTemplateCreate(DBBaseCreate):
    """Payload for creating a new email template."""

    name: str = Field(..., description="Display name of the mail template")
    subject: str = Field(
        ...,
        description="Email subject line (max 75 chars, supports {{event.slug}} placeholder)",
    )
    description: str | None = Field(
        None, description="Optional description of the mail template"
    )
    fromName: str | None = Field(
        None,
        description="Sender display name used when sending emails with this template",
    )
    fromMail: str | None = Field(
        None,
        description="Sender email address used when sending emails with this template",
    )
    contentHTML: str = Field(
        ..., description="HTML content of the email template"
    )
    contentPlain: str = Field(
        ..., description="Plain-text content of the email template"
    )
    language: UUID4 = Field(
        ..., description="ID of the language this template is written in"
    )
    protected: bool = Field(
        ..., description="If true, the template cannot be deleted"
    )
    replyTo: str | None = Field(
        None,
        description="Reply-to email address for emails sent with this template",
    )
    mail_action: UUID4 | None = Field(
        None, description="ID of the mail action that uses this template"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Willkommens-E-Mail",
                "subject": "Willkommen im OpenVLE-System",
                "description": "Vorlage für die Begrüßungs-E-Mail neuer Benutzer",
                "fromName": "OpenVLE",
                "fromMail": "noreply@example.com",
                "contentHTML": "<p>Willkommen im System, {{ user.name }}!</p>",
                "contentPlain": "Willkommen im System, {{ user.name }}!",
                "language": "00000000-0000-0000-0000-000000000001",
                "protected": False,
                "replyTo": None,
                "mail_action": None,
            }
        }
    )

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, value):
        return _validate_mail_subject(value)


# Properties to receive via API on update
class MailTemplateUpdate(DBBaseUpdate):
    """Payload for updating an existing email template."""

    name: str | None = Field(
        None, description="Display name of the mail template"
    )
    subject: str | None = Field(
        None,
        description="Email subject line (max 75 chars, supports {{event.slug}} placeholder)",
    )
    description: str | None = Field(
        None, description="Optional description of the mail template"
    )
    fromName: str | None = Field(
        None,
        description="Sender display name used when sending emails with this template",
    )
    fromMail: str | None = Field(
        None,
        description="Sender email address used when sending emails with this template",
    )
    contentHTML: str | None = Field(
        None, description="HTML content of the email template"
    )
    contentPlain: str | None = Field(
        None, description="Plain-text content of the email template"
    )
    language: UUID4 | None = Field(
        None, description="ID of the language this template is written in"
    )
    protected: bool | None = Field(
        None, description="If true, the template cannot be deleted"
    )
    replyTo: str | None = Field(
        None,
        description="Reply-to email address for emails sent with this template",
    )
    mail_action: UUID4 | None = Field(
        None, description="ID of the mail action that uses this template"
    )

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, value):
        if value is None:
            return value
        return _validate_mail_subject(value)

    model_config = ConfigDict(from_attributes=True)


class MailTemplateInDBBase(MailTemplateBase):
    """Internal mail template schema with required ID field."""

    id: UUID4

    model_config = ConfigDict(from_attributes=True)


# Main class used as response model
class MailTemplate(MailTemplateInDBBase):
    """Full mail template response schema."""

    model_config = ConfigDict(from_attributes=True)


# Class used for when MailTemplate is to appear as a nested model and will only display ID
class MailTemplateNested(DBBaseUpdate):
    """Minimal mail template schema for nested references, shows ID only."""

    id: UUID4 = Field(..., description="Unique identifier of the mail template")

    model_config = ConfigDict(from_attributes=True)


# List object of MailTemplate
class MailTemplateList(BaseModel):
    """Paginated list of mail template objects."""

    pageDetails: PaginationPageDetails
    items: list[MailTemplate]
