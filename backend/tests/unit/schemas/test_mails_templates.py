"""Tests for schemas/mails_templates.py - MailTemplate schema validation."""

import re
import uuid

import pytest
from core.exceptions import MailSubjectTooLong
from pydantic import ValidationError
from schemas.mails_templates import MailTemplateCreate, MailTemplateUpdate


class TestMailTemplateCreate:
    def test_valid_create(self):
        mt = MailTemplateCreate(
            name="Welcome Template",
            subject="Welcome!",
            contentHTML="<h1>Hi</h1>",
            contentPlain="Hi",
            language=uuid.uuid4(),
            protected=False,
        )
        assert mt.name == "Welcome Template"
        assert mt.subject == "Welcome!"
        assert mt.protected is False

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError):
            MailTemplateCreate(name="Test")

    def test_optional_fields(self):
        mt = MailTemplateCreate(
            name="Test",
            subject="Test",
            contentHTML="<p>Test</p>",
            contentPlain="Test",
            language=uuid.uuid4(),
            protected=True,
        )
        assert mt.description is None
        assert mt.fromName is None
        assert mt.fromMail is None
        assert mt.replyTo is None
        assert mt.mail_action is None


class TestMailTemplateUpdate:
    def test_valid_update(self):
        u = MailTemplateUpdate(name="Updated Template")
        assert u.name == "Updated Template"

    def test_all_optional(self):
        u = MailTemplateUpdate()
        assert u.name is None
        assert u.subject is None
        assert u.contentHTML is None

    def test_subject_none_skips_validation(self):
        """None subject on update should not raise."""
        u = MailTemplateUpdate(subject=None)
        assert u.subject is None


class TestSubjectLengthValidation:
    """Tests for the RFC subject length rules."""

    def _make_create(self, subject: str) -> MailTemplateCreate:
        return MailTemplateCreate(
            name="T",
            subject=subject,
            contentHTML="<p>x</p>",
            contentPlain="x",
            language=uuid.uuid4(),
            protected=False,
        )

    # --- No placeholder ---

    def test_subject_at_max_length_is_valid(self):
        """75 chars without placeholder → valid."""
        subject = "A" * 75
        mt = self._make_create(subject)
        assert mt.subject == subject

    def test_subject_one_over_max_raises(self):
        """76 chars without placeholder → MailSubjectTooLong."""
        with pytest.raises(MailSubjectTooLong):
            self._make_create("A" * 76)

    def test_short_subject_is_valid(self):
        mt = self._make_create("Hello")
        assert mt.subject == "Hello"

    def test_empty_subject_is_valid(self):
        mt = self._make_create("")
        assert mt.subject == ""

    # --- With exact placeholder {{event.slug}} ---

    def test_subject_with_slug_at_budget_is_valid(self):
        """Remaining chars (without placeholder) == 67 → valid."""
        subject = "A" * 67 + "{{event.slug}}"
        mt = self._make_create(subject)
        assert mt.subject == subject

    def test_subject_with_slug_one_over_budget_raises(self):
        """Remaining chars == 68 → MailSubjectTooLong."""
        with pytest.raises(MailSubjectTooLong):
            self._make_create("A" * 68 + "{{event.slug}}")

    def test_subject_placeholder_only_is_valid(self):
        """Just the placeholder → 0 remaining chars → valid."""
        mt = self._make_create("{{event.slug}}")
        assert mt.subject == "{{event.slug}}"

    def test_subject_placeholder_with_surrounding_text(self):
        """Realistic subject with placeholder fits in budget."""
        subject = (
            "Deine Veranstaltung {{event.slug}} wurde erfolgreich ausgerollt."
        )
        remaining = re.sub(r"\{\{\s*event\.slug\s*\}\}", "", subject)
        assert len(remaining) <= 67
        mt = self._make_create(subject)
        assert mt.subject == subject

    # --- Whitespace variants of the placeholder ---

    def test_placeholder_with_inner_spaces_is_detected(self):
        """{{ event.slug }} counts as the slug placeholder."""
        subject = "A" * 10 + "{{ event.slug }}"
        mt = self._make_create(subject)
        assert mt.subject == subject

    def test_placeholder_with_tabs_is_detected(self):
        """{{\tevent.slug\t}} counts as the slug placeholder."""
        subject = "A" * 10 + "{{\tevent.slug\t}}"
        mt = self._make_create(subject)
        assert mt.subject == subject

    def test_placeholder_whitespace_variant_over_budget_raises(self):
        """68 remaining chars + whitespace-padded placeholder → MailSubjectTooLong."""
        with pytest.raises(MailSubjectTooLong):
            self._make_create("A" * 68 + "{{ event.slug }}")

    def test_placeholder_whitespace_variant_at_budget_is_valid(self):
        """67 remaining chars + whitespace-padded placeholder → valid."""
        subject = "A" * 67 + "{{ event.slug }}"
        mt = self._make_create(subject)
        assert mt.subject == subject

    def test_multiple_spaces_inside_braces(self):
        """Many spaces around event.slug still treated as placeholder."""
        subject = "A" * 10 + "{{   event.slug   }}"
        mt = self._make_create(subject)
        assert mt.subject == subject

    # --- Update validator mirrors create ---

    def test_update_subject_at_max_length_is_valid(self):
        u = MailTemplateUpdate(subject="B" * 75)
        assert len(u.subject) == 75

    def test_update_subject_one_over_max_raises(self):
        with pytest.raises(MailSubjectTooLong):
            MailTemplateUpdate(subject="B" * 76)

    def test_update_subject_with_slug_at_budget_is_valid(self):
        u = MailTemplateUpdate(subject="B" * 67 + "{{event.slug}}")
        assert u.subject is not None

    def test_update_subject_with_slug_over_budget_raises(self):
        with pytest.raises(MailSubjectTooLong):
            MailTemplateUpdate(subject="B" * 68 + "{{event.slug}}")

    def test_update_subject_whitespace_placeholder_at_budget_is_valid(self):
        u = MailTemplateUpdate(subject="B" * 67 + "{{ event.slug }}")
        assert u.subject is not None

    def test_update_subject_whitespace_placeholder_over_budget_raises(self):
        with pytest.raises(MailSubjectTooLong):
            MailTemplateUpdate(subject="B" * 68 + "{{ event.slug }}")
