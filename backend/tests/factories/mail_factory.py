"""Factories for Mail, MailTemplate, and MailAction models."""

import uuid

import factory
from models import Mail, MailAction, MailTemplate

from .base import BaseFactory


class MailActionFactory(BaseFactory):
    class Meta:
        model = MailAction

    name = factory.Sequence(lambda n: f"Mail Action {n}")
    description = factory.Faker("sentence")
    slug = factory.Sequence(lambda n: f"mail_action_{n}")


class MailTemplateFactory(BaseFactory):
    class Meta:
        model = MailTemplate

    name = factory.Sequence(lambda n: f"Mail Template {n}")
    subject = factory.Sequence(lambda n: f"Subject {n}")
    description = factory.Faker("sentence")
    fromName = "Test KVS"
    fromMail = "test@example.com"
    contentHTML = "<p>Hello {{ user.name }}</p>"
    contentPlain = "Hello {{ user.name }}"
    language = factory.LazyFunction(
        uuid.uuid4
    )  # Must be set to actual Language.id
    protected = False
    replyTo = None
    mail_action = None


class MailFactory(BaseFactory):
    class Meta:
        model = Mail

    subject = factory.Sequence(lambda n: f"Test Mail {n}")
    fromName = "Test KVS"
    fromMail = "test@example.com"
    toMail = factory.Sequence(lambda n: f"recipient{n}@example.com")
    sendStatus = "queued"
    templateId = factory.LazyFunction(
        uuid.uuid4
    )  # Must be set to actual MailTemplate.id
    replyTo = "noreply@example.com"
    content_rendered = None
    event = None
    user_id = None
