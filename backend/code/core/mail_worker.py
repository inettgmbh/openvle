import smtplib
import ssl

from pydantic import UUID4
from rq import get_current_job

from controllers.sub_tasks import CRUDSubTask
from models import Mail, MailTemplate, SubTask

from .config import Settings
from .mail import mail_construct
from .mariadb import SessionLocal

settings = Settings()


def _cancel_job_retries():
    """Remove the current RQ job from the retry queue so it is not attempted again."""
    try:
        current_job = get_current_job()
        if current_job:
            current_job.retries_left = 0
            current_job.save()
    except Exception:
        pass


def _fail_mail(
    db, mail_object, kvs_task_object_id, code, message, force_fail: bool = False
):
    """Update Mail.sendStatus to 'error' (if available) then fail the SubTask."""
    if mail_object:
        mail_object.sendStatus = "error"
        db.add(mail_object)
        db.commit()
    return CRUDSubTask(SubTask).worker_process_fail(
        kvs_task_object_id, code, message, db, force_fail=force_fail
    )


def mail_worker_send(
    kvs_task_object_id: UUID4, kvs_mail_id: UUID4, context_objects: list = None
):
    """
    :param kvs_task_object_id: ID of related SubTask in DB
    :param kvs_mail_id: ID of related Mail object in DB
    :param context_objects: List of related objects used in generating the context with which to render the mail
    This function is used by the RQ Worker to SEND a mail based on a Mail object. Also updates the Mail.sendStatus
    and the corresponding Task object.
    """
    # Step 1: Get and update SubTask object
    db = SessionLocal()
    CRUDSubTask(SubTask).worker_process_start(db, kvs_task_object_id)
    sub_task = db.get(SubTask, kvs_task_object_id)

    # Step 2: get Mail and MailTemplate objects from database
    mail_object = db.get(Mail, kvs_mail_id)
    if not mail_object:
        return _fail_mail(
            db,
            None,
            kvs_task_object_id,
            404,
            "Mail object not found in database",
        )

    # If a previous attempt already recorded a permanent SMTP failure, do not retry
    if sub_task.response_code and sub_task.response_code == 550:
        return _fail_mail(
            db,
            mail_object,
            kvs_task_object_id,
            sub_task.response_code,
            sub_task.response_message,
        )

    mail_template_object = db.get(MailTemplate, mail_object.templateId)
    if not mail_template_object:
        return _fail_mail(
            db,
            mail_object,
            kvs_task_object_id,
            404,
            "MailTemplate object not found in database",
        )

    # Step 3: Construct mail
    try:
        if mail_object.content_rendered:
            mail_rendered = mail_object.content_rendered
            mail_body = str(mail_rendered)
        else:
            mail_rendered = mail_construct(
                to_mail=mail_object.toMail,
                subject=mail_object.subject,
                content_plain=mail_template_object.contentPlain,
                content_html=mail_template_object.contentHTML,
                from_name=mail_object.fromName,
                from_mail=mail_object.fromMail,
                reply_to=mail_object.replyTo,
                context_objects=context_objects,
            )
            mail_body = mail_rendered.as_string()
    except Exception as e:
        return _fail_mail(
            db,
            mail_object,
            kvs_task_object_id,
            400,
            f"Failed to render email template: {e}",
        )

    # Step 4: Initiate connection to SMTP server and send mail
    try:
        smtp_method = settings.smtp_method.lower()
        if smtp_method == "ssl":
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                host=settings.smtp_host,
                port=settings.smtp_port,
                context=context,
            ) as mail_server:
                mail_server.login(
                    settings.smtp_username, settings.smtp_password
                )
                mail_send_response = mail_server.sendmail(
                    mail_object.fromMail, mail_object.toMail, mail_body
                )
        elif smtp_method == "tls":
            context = ssl.create_default_context()
            with smtplib.SMTP(
                host=settings.smtp_host, port=settings.smtp_port
            ) as mail_server:
                mail_server.starttls(context=context)
                mail_server.login(
                    settings.smtp_username, settings.smtp_password
                )
                mail_send_response = mail_server.sendmail(
                    mail_object.fromMail, mail_object.toMail, mail_body
                )
        elif smtp_method == "plain":
            with smtplib.SMTP(
                host=settings.smtp_host, port=settings.smtp_port
            ) as mail_server:
                if settings.smtp_username:
                    mail_server.login(
                        settings.smtp_username, settings.smtp_password
                    )
                mail_send_response = mail_server.sendmail(
                    mail_object.fromMail, mail_object.toMail, mail_body
                )
        else:
            return _fail_mail(
                db,
                mail_object,
                kvs_task_object_id,
                422,
                f"Unsupported SMTP method '{settings.smtp_method}'",
            )
    except smtplib.SMTPAuthenticationError:
        return _fail_mail(
            db,
            mail_object,
            kvs_task_object_id,
            535,
            "SMTP authentication error",
        )
    except smtplib.SMTPServerDisconnected:
        return _fail_mail(
            db, mail_object, kvs_task_object_id, 421, "SMTP server disconnected"
        )
    except smtplib.SMTPConnectError as e:
        return _fail_mail(
            db,
            mail_object,
            kvs_task_object_id,
            421,
            f"SMTP server connection error: {e}",
        )
    except smtplib.SMTPHeloError:
        return _fail_mail(
            db, mail_object, kvs_task_object_id, 503, "SMTP helo error"
        )
    except smtplib.SMTPNotSupportedError:
        return _fail_mail(
            db, mail_object, kvs_task_object_id, 504, "SMTP not supported error"
        )
    except smtplib.SMTPRecipientsRefused as e:
        # Permanent failure — recipient does not exist, remove job from queue
        _cancel_job_retries()
        return _fail_mail(
            db,
            mail_object,
            kvs_task_object_id,
            550,
            f"SMTP recipient refused: {e}",
            force_fail=True,
        )
    except smtplib.SMTPSenderRefused as e:
        # Permanent failure — sender refused, remove job from queue
        _cancel_job_retries()
        return _fail_mail(
            db,
            mail_object,
            kvs_task_object_id,
            550,
            f"SMTP sender refused: {e}",
            force_fail=True,
        )
    except smtplib.SMTPDataError as e:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id, 550, f"SMTP data error: {e}", db
        )
    except ConnectionRefusedError:
        return _fail_mail(
            db, mail_object, kvs_task_object_id, 111, "SMTP connection refused"
        )
    except Exception as e:
        return _fail_mail(
            db,
            mail_object,
            kvs_task_object_id,
            502,
            f"Failed to connect to SMTP server: {e}",
        )

    # Step 5: Check that mail was sent successfully and update mail object
    if not mail_send_response:
        # Success
        mail_object.sendStatus = "sent"
        if not mail_object.content_rendered:
            mail_object.content_rendered = mail_rendered.as_string()
        db.add(mail_object)
        db.commit()
        return CRUDSubTask(SubTask).worker_process_success(
            kvs_task_object_id, 200, "Mail sent successfully", db
        )
    else:
        # Failed to send
        return _fail_mail(
            db,
            mail_object,
            kvs_task_object_id,
            554,
            f"Failed to send mail to {mail_send_response}",
        )
