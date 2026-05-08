"""Tests for core/mail_worker.py - SMTP email sending worker."""

import smtplib
import uuid
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from unittest.mock import MagicMock

import pytest

from models import Language, Mail, MailAction, MailTemplate, SubTask, Task
from pve.worker_utils import TaskException
from tests.helpers.mock_smtp import MockSMTP


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def sample_language(db_session, system_user):
    return db_session.query(Language).filter_by(key="de_DE").one()


@pytest.fixture()
def sample_mail_action(db_session, system_user):
    now = datetime.now(timezone.utc)
    action = MailAction(
        id=uuid.uuid4(),
        name="Test Action",
        description="Test action",
        slug="test_action",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(action)
    db_session.flush()
    return action


@pytest.fixture()
def sample_mail_template(db_session, system_user, sample_language, sample_mail_action):
    now = datetime.now(timezone.utc)
    tpl = MailTemplate(
        id=uuid.uuid4(),
        name="Test Template",
        subject="Test Subject",
        contentHTML="<p>Hello {{ user.name }}</p>",
        contentPlain="Hello {{ user.name }}",
        language=sample_language.id,
        mail_action=sample_mail_action.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(tpl)
    db_session.flush()
    return tpl


def _make_task(db, system_user, event_id=None):
    now = datetime.now(timezone.utc)
    task = Task(
        id=uuid.uuid4(),
        name="test-task",
        status="queued",
        event_id=event_id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(task)
    db.flush()
    return task


def _make_subtask(db, system_user, parent_task, action="mails_send", job_id=None):
    now = datetime.now(timezone.utc)
    subtask = SubTask(
        id=uuid.uuid4(),
        name="test-subtask",
        status="queued",
        object_type="Mail",
        object_id=str(uuid.uuid4()),
        action=action,
        attempt="0",
        parent_task=parent_task.id,
        job_id=job_id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(subtask)
    db.flush()
    return subtask


def _make_mail(
    db, system_user, template_id, send_status="queued", content_rendered=None
):
    now = datetime.now(timezone.utc)
    mail = Mail(
        id=uuid.uuid4(),
        subject="Test Subject",
        fromName="Sender",
        fromMail="sender@example.com",
        toMail="recipient@example.com",
        sendStatus=send_status,
        templateId=template_id,
        replyTo="sender@example.com",
        content_rendered=content_rendered,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db.add(mail)
    db.flush()
    return mail


def _patch_session_and_smtp(monkeypatch, db_session, smtp_method="PLAIN"):
    """Patch SessionLocal, mail_construct, and SMTP for mail_worker tests."""
    monkeypatch.setattr("core.mail_worker.SessionLocal", lambda: db_session)
    # Also patch SessionLocal in modules called by worker_process_success/fail
    import core.mariadb as m
    import controllers.sub_tasks as st
    import core.mail_automated as ma

    monkeypatch.setattr(m, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(st, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(ma, "SessionLocal", lambda: db_session)

    # Patch settings to use PLAIN SMTP (simplest path)
    mock_settings = MagicMock()
    mock_settings.smtp_method = smtp_method
    mock_settings.smtp_host = "localhost"
    mock_settings.smtp_port = 1025
    mock_settings.smtp_username = ""
    mock_settings.smtp_password = ""
    mock_settings.worker_max_retry = 5
    monkeypatch.setattr("core.mail_worker.settings", mock_settings)

    # Patch mail_construct to return a simple MIME message
    mock_msg = MIMEMultipart("alternative")
    mock_msg["From"] = "sender@example.com"
    mock_msg["To"] = "recipient@example.com"
    mock_msg["Subject"] = "Test"
    mock_msg.attach(MIMEText("plain body", "plain"))
    monkeypatch.setattr("core.mail_worker.mail_construct", lambda **kw: mock_msg)

    return mock_settings


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestMailWorkerSend:
    def test_sends_mail_successfully(
        self, db_session, system_user, monkeypatch, sample_mail_template
    ):
        """Happy path: mail is sent, status updated to 'sent'."""
        _patch_session_and_smtp(monkeypatch, db_session)
        monkeypatch.setattr(
            "core.mail_worker.smtplib.SMTP",
            lambda host, port: MockSMTP(),
        )

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(db_session, system_user, task)
        mail = _make_mail(db_session, system_user, sample_mail_template.id)

        from core.mail_worker import mail_worker_send

        result = mail_worker_send(kvs_task_object_id=subtask.id, kvs_mail_id=mail.id)

        assert result is True
        db_session.expire_all()
        refreshed_mail = db_session.get(Mail, mail.id)
        assert refreshed_mail.sendStatus == "sent"

    def test_mail_not_found(
        self, db_session, system_user, monkeypatch, sample_mail_template
    ):
        """TaskException raised when Mail ID doesn't exist."""
        _patch_session_and_smtp(monkeypatch, db_session)

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(db_session, system_user, task)

        from core.mail_worker import mail_worker_send

        with pytest.raises(TaskException, match="Mail object not found"):
            mail_worker_send(
                kvs_task_object_id=subtask.id,
                kvs_mail_id=uuid.uuid4(),
            )

    def test_template_not_found(
        self, db_session, system_user, monkeypatch, sample_mail_template
    ):
        """TaskException raised when MailTemplate ID doesn't exist."""
        _patch_session_and_smtp(monkeypatch, db_session)

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(db_session, system_user, task)
        mail = _make_mail(db_session, system_user, sample_mail_template.id)

        # Wrap db.get to return None for MailTemplate lookups (simulating missing template)
        original_get = db_session.get

        def patched_get(model, id, **kwargs):
            if model is MailTemplate:
                return None
            return original_get(model, id, **kwargs)

        monkeypatch.setattr(db_session, "get", patched_get)

        from core.mail_worker import mail_worker_send

        with pytest.raises(TaskException, match="MailTemplate object not found"):
            mail_worker_send(
                kvs_task_object_id=subtask.id,
                kvs_mail_id=mail.id,
            )

    def test_smtp_auth_error(
        self, db_session, system_user, monkeypatch, sample_mail_template
    ):
        """SMTPAuthenticationError handled with code 535."""
        mock_settings = _patch_session_and_smtp(
            monkeypatch, db_session, smtp_method="tls"
        )
        mock_settings.smtp_username = "user"
        mock_settings.smtp_password = "pass"

        class FailingSMTP(MockSMTP):
            def login(self, *args, **kwargs):
                raise smtplib.SMTPAuthenticationError(535, b"Auth failed")

        monkeypatch.setattr(
            "core.mail_worker.smtplib.SMTP",
            lambda host, port: FailingSMTP(),
        )

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(db_session, system_user, task)
        mail = _make_mail(db_session, system_user, sample_mail_template.id)

        from core.mail_worker import mail_worker_send

        with pytest.raises(TaskException, match="SMTP authentication error"):
            mail_worker_send(kvs_task_object_id=subtask.id, kvs_mail_id=mail.id)

    def test_smtp_server_disconnected(
        self, db_session, system_user, monkeypatch, sample_mail_template
    ):
        """SMTPServerDisconnected handled with code 421."""
        mock_settings = _patch_session_and_smtp(
            monkeypatch, db_session, smtp_method="tls"
        )
        mock_settings.smtp_username = "user"
        mock_settings.smtp_password = "pass"

        class DisconnectingSMTP(MockSMTP):
            def login(self, *args, **kwargs):
                raise smtplib.SMTPServerDisconnected("Disconnected")

        monkeypatch.setattr(
            "core.mail_worker.smtplib.SMTP",
            lambda host, port: DisconnectingSMTP(),
        )

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(db_session, system_user, task)
        mail = _make_mail(db_session, system_user, sample_mail_template.id)

        from core.mail_worker import mail_worker_send

        with pytest.raises(TaskException, match="SMTP server disconnected"):
            mail_worker_send(kvs_task_object_id=subtask.id, kvs_mail_id=mail.id)

    def test_smtp_connection_refused(
        self, db_session, system_user, monkeypatch, sample_mail_template
    ):
        """ConnectionRefusedError handled with code 111."""
        _patch_session_and_smtp(monkeypatch, db_session)

        class RefusingSMTP(MockSMTP):
            def __init__(self, *args, **kwargs):
                raise ConnectionRefusedError("Connection refused")

        monkeypatch.setattr(
            "core.mail_worker.smtplib.SMTP",
            lambda host, port: RefusingSMTP(),
        )

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(db_session, system_user, task)
        mail = _make_mail(db_session, system_user, sample_mail_template.id)

        from core.mail_worker import mail_worker_send

        with pytest.raises(TaskException, match="SMTP connection refused"):
            mail_worker_send(kvs_task_object_id=subtask.id, kvs_mail_id=mail.id)

    def test_unsupported_smtp_method(
        self, db_session, system_user, monkeypatch, sample_mail_template
    ):
        """Unknown SMTP method raises TaskException with code 422."""
        _patch_session_and_smtp(monkeypatch, db_session, smtp_method="unknown_method")

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(db_session, system_user, task)
        mail = _make_mail(db_session, system_user, sample_mail_template.id)

        from core.mail_worker import mail_worker_send

        with pytest.raises(TaskException, match="Unsupported SMTP method"):
            mail_worker_send(kvs_task_object_id=subtask.id, kvs_mail_id=mail.id)

    def test_uses_pre_rendered_content(
        self, db_session, system_user, monkeypatch, sample_mail_template
    ):
        """When mail_object.content_rendered is set, uses it directly instead of mail_construct."""
        _patch_session_and_smtp(monkeypatch, db_session)
        monkeypatch.setattr(
            "core.mail_worker.smtplib.SMTP",
            lambda host, port: MockSMTP(),
        )

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(db_session, system_user, task)
        pre_rendered = "Pre-rendered email content body"
        mail = _make_mail(
            db_session,
            system_user,
            sample_mail_template.id,
            content_rendered=pre_rendered,
        )

        # Replace mail_construct with a bomb to verify it's NOT called
        def bomb(**kw):
            raise AssertionError("mail_construct should not be called")

        monkeypatch.setattr("core.mail_worker.mail_construct", bomb)

        from core.mail_worker import mail_worker_send

        result = mail_worker_send(kvs_task_object_id=subtask.id, kvs_mail_id=mail.id)

        assert result is True

    def test_failed_send_response(
        self, db_session, system_user, monkeypatch, sample_mail_template
    ):
        """sendmail returns non-empty dict = failure, status should be 'error'."""
        _patch_session_and_smtp(monkeypatch, db_session)

        class FailSendSMTP(MockSMTP):
            def sendmail(self, from_addr, to_addr, msg):
                return {"recipient@example.com": (550, "Mailbox unavailable")}

        monkeypatch.setattr(
            "core.mail_worker.smtplib.SMTP",
            lambda host, port: FailSendSMTP(),
        )

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(db_session, system_user, task)
        mail = _make_mail(db_session, system_user, sample_mail_template.id)

        from core.mail_worker import mail_worker_send

        with pytest.raises(TaskException, match="Failed to send mail"):
            mail_worker_send(kvs_task_object_id=subtask.id, kvs_mail_id=mail.id)

        db_session.expire_all()
        refreshed_mail = db_session.get(Mail, mail.id)
        assert refreshed_mail.sendStatus == "error"

    def test_template_render_error(
        self, db_session, system_user, monkeypatch, sample_mail_template
    ):
        """mail_construct raising an exception results in graceful failure."""
        _patch_session_and_smtp(monkeypatch, db_session)

        def exploding_construct(**kw):
            raise Exception("Jinja2 template error")

        monkeypatch.setattr("core.mail_worker.mail_construct", exploding_construct)

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(db_session, system_user, task)
        mail = _make_mail(db_session, system_user, sample_mail_template.id)

        from core.mail_worker import mail_worker_send

        with pytest.raises(TaskException, match="Failed to render email template"):
            mail_worker_send(kvs_task_object_id=subtask.id, kvs_mail_id=mail.id)

    # -----------------------------------------------------------------------
    # Case-insensitive smtp_method
    # -----------------------------------------------------------------------
    @pytest.mark.parametrize("method", ["PLAIN", "Plain", "plain", "pLaIn"])
    def test_smtp_method_case_insensitive_plain(
        self, db_session, system_user, monkeypatch, sample_mail_template, method
    ):
        """smtp_method comparison is case-insensitive for PLAIN."""
        _patch_session_and_smtp(monkeypatch, db_session, smtp_method=method)
        monkeypatch.setattr(
            "core.mail_worker.smtplib.SMTP",
            lambda host, port: MockSMTP(),
        )

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(db_session, system_user, task)
        mail = _make_mail(db_session, system_user, sample_mail_template.id)

        from core.mail_worker import mail_worker_send

        result = mail_worker_send(kvs_task_object_id=subtask.id, kvs_mail_id=mail.id)
        assert result is True

    @pytest.mark.parametrize("method", ["SSL", "Ssl", "ssl"])
    def test_smtp_method_case_insensitive_ssl(
        self, db_session, system_user, monkeypatch, sample_mail_template, method
    ):
        """smtp_method comparison is case-insensitive for SSL."""
        mock_settings = _patch_session_and_smtp(
            monkeypatch, db_session, smtp_method=method
        )
        mock_settings.smtp_username = "user"
        mock_settings.smtp_password = "pass"
        monkeypatch.setattr(
            "core.mail_worker.smtplib.SMTP_SSL",
            lambda host, port, context: MockSMTP(),
        )

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(db_session, system_user, task)
        mail = _make_mail(db_session, system_user, sample_mail_template.id)

        from core.mail_worker import mail_worker_send

        result = mail_worker_send(kvs_task_object_id=subtask.id, kvs_mail_id=mail.id)
        assert result is True

    @pytest.mark.parametrize("method", ["TLS", "Tls", "tls"])
    def test_smtp_method_case_insensitive_tls(
        self, db_session, system_user, monkeypatch, sample_mail_template, method
    ):
        """smtp_method comparison is case-insensitive for TLS."""
        mock_settings = _patch_session_and_smtp(
            monkeypatch, db_session, smtp_method=method
        )
        mock_settings.smtp_username = "user"
        mock_settings.smtp_password = "pass"
        monkeypatch.setattr(
            "core.mail_worker.smtplib.SMTP",
            lambda host, port: MockSMTP(),
        )

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(db_session, system_user, task)
        mail = _make_mail(db_session, system_user, sample_mail_template.id)

        from core.mail_worker import mail_worker_send

        result = mail_worker_send(kvs_task_object_id=subtask.id, kvs_mail_id=mail.id)
        assert result is True

    # -----------------------------------------------------------------------
    # PLAIN with optional login
    # -----------------------------------------------------------------------
    def test_plain_with_username_calls_login(
        self, db_session, system_user, monkeypatch, sample_mail_template
    ):
        """PLAIN with smtp_username set should call login."""
        mock_settings = _patch_session_and_smtp(
            monkeypatch, db_session, smtp_method="plain"
        )
        mock_settings.smtp_username = "testuser"
        mock_settings.smtp_password = "testpass"

        login_called = {}

        class LoginTrackingSMTP(MockSMTP):
            def login(self, user, password):
                login_called["user"] = user
                login_called["password"] = password

        monkeypatch.setattr(
            "core.mail_worker.smtplib.SMTP",
            lambda host, port: LoginTrackingSMTP(),
        )

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(db_session, system_user, task)
        mail = _make_mail(db_session, system_user, sample_mail_template.id)

        from core.mail_worker import mail_worker_send

        result = mail_worker_send(kvs_task_object_id=subtask.id, kvs_mail_id=mail.id)
        assert result is True
        assert login_called["user"] == "testuser"
        assert login_called["password"] == "testpass"

    def test_plain_without_username_skips_login(
        self, db_session, system_user, monkeypatch, sample_mail_template
    ):
        """PLAIN without smtp_username should not call login."""
        mock_settings = _patch_session_and_smtp(
            monkeypatch, db_session, smtp_method="plain"
        )
        mock_settings.smtp_username = ""
        mock_settings.smtp_password = ""

        class LoginBombSMTP(MockSMTP):
            def login(self, *args, **kwargs):
                raise AssertionError("login should not be called")

        monkeypatch.setattr(
            "core.mail_worker.smtplib.SMTP",
            lambda host, port: LoginBombSMTP(),
        )

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(db_session, system_user, task)
        mail = _make_mail(db_session, system_user, sample_mail_template.id)

        from core.mail_worker import mail_worker_send

        result = mail_worker_send(kvs_task_object_id=subtask.id, kvs_mail_id=mail.id)
        assert result is True

    def test_plain_auth_error_with_username(
        self, db_session, system_user, monkeypatch, sample_mail_template
    ):
        """PLAIN with username: SMTPAuthenticationError is handled."""
        mock_settings = _patch_session_and_smtp(
            monkeypatch, db_session, smtp_method="plain"
        )
        mock_settings.smtp_username = "baduser"
        mock_settings.smtp_password = "badpass"

        class FailingSMTP(MockSMTP):
            def login(self, *args, **kwargs):
                raise smtplib.SMTPAuthenticationError(535, b"Auth failed")

        monkeypatch.setattr(
            "core.mail_worker.smtplib.SMTP",
            lambda host, port: FailingSMTP(),
        )

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(db_session, system_user, task)
        mail = _make_mail(db_session, system_user, sample_mail_template.id)

        from core.mail_worker import mail_worker_send

        with pytest.raises(TaskException, match="SMTP authentication error"):
            mail_worker_send(kvs_task_object_id=subtask.id, kvs_mail_id=mail.id)

    # -----------------------------------------------------------------------
    # Permanent SMTP failures — parent Task must be set to "failed"
    # -----------------------------------------------------------------------
    def test_smtp_recipients_refused_fails_parent_task(
        self, db_session, system_user, monkeypatch, sample_mail_template
    ):
        """SMTPRecipientsRefused is a permanent failure — parent Task status must be 'failed'."""
        _patch_session_and_smtp(monkeypatch, db_session)

        class RecipientRefusedSMTP(MockSMTP):
            def sendmail(self, from_addr, to_addr, msg):
                raise smtplib.SMTPRecipientsRefused(
                    {"recipient@example.com": (550, b"User unknown")}
                )

        monkeypatch.setattr(
            "core.mail_worker.smtplib.SMTP",
            lambda host, port: RecipientRefusedSMTP(),
        )
        # Prevent actual RQ job lookup
        monkeypatch.setattr("core.mail_worker.get_current_job", lambda: None)

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(db_session, system_user, task)
        mail = _make_mail(db_session, system_user, sample_mail_template.id)

        from core.mail_worker import mail_worker_send

        with pytest.raises(TaskException, match="SMTP recipient refused"):
            mail_worker_send(kvs_task_object_id=subtask.id, kvs_mail_id=mail.id)

        db_session.expire_all()
        refreshed_task = db_session.get(Task, task.id)
        assert refreshed_task.status == "failed"

        refreshed_mail = db_session.get(Mail, mail.id)
        assert refreshed_mail.sendStatus == "error"

    def test_smtp_sender_refused_fails_parent_task(
        self, db_session, system_user, monkeypatch, sample_mail_template
    ):
        """SMTPSenderRefused is a permanent failure — parent Task status must be 'failed'."""
        _patch_session_and_smtp(monkeypatch, db_session)

        class SenderRefusedSMTP(MockSMTP):
            def sendmail(self, from_addr, to_addr, msg):
                raise smtplib.SMTPSenderRefused(
                    550, b"Sender not allowed", "sender@example.com"
                )

        monkeypatch.setattr(
            "core.mail_worker.smtplib.SMTP",
            lambda host, port: SenderRefusedSMTP(),
        )
        # Prevent actual RQ job lookup
        monkeypatch.setattr("core.mail_worker.get_current_job", lambda: None)

        task = _make_task(db_session, system_user)
        subtask = _make_subtask(db_session, system_user, task)
        mail = _make_mail(db_session, system_user, sample_mail_template.id)

        from core.mail_worker import mail_worker_send

        with pytest.raises(TaskException, match="SMTP sender refused"):
            mail_worker_send(kvs_task_object_id=subtask.id, kvs_mail_id=mail.id)

        db_session.expire_all()
        refreshed_task = db_session.get(Task, task.id)
        assert refreshed_task.status == "failed"

        refreshed_mail = db_session.get(Mail, mail.id)
        assert refreshed_mail.sendStatus == "error"
