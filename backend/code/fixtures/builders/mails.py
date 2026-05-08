import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from fixtures.constants import (
    STATUS_AKTIV_ID,
    SYSTEM_USER_ID,
    fixture_timestamp,
    fixture_uuid,
)
from fixtures.profiles import ProfileConfig
from models.mails import Mail
from models.mails_templates import MailTemplate

log = logging.getLogger("fixtures")

# Mail template names from seed data → we look them up by name
_VM_SUCCESS_TPL = "Virtuelle Maschine erfolgreich bereitgestellt"
_VM_SUCCESS_TPL_FALLBACK = "Virtuelle Maschine wurde erfolgreich bereitgestellt"
_EVENT_DEPLOYED_TPL = "Veranstaltung erfolgreich bereitgestellt"
_EVENT_PRE_END_TPL = "Veranstaltung endet bald - Lehrende"


def create_mails(
    session: Session,
    config: ProfileConfig,
    context: dict,
) -> None:
    profile = config.name.value
    count = 0
    idx = 0

    # Look up mail template IDs
    vm_tpl = _find_template(session, _VM_SUCCESS_TPL)
    if not vm_tpl:
        vm_tpl = _find_template(session, _VM_SUCCESS_TPL_FALLBACK)
    event_tpl = _find_template(session, _EVENT_DEPLOYED_TPL)
    pre_end_tpl = _find_template(session, _EVENT_PRE_END_TPL)

    # Fall back to any template if specific ones don't exist
    fallback_tpl = session.execute(
        select(MailTemplate).limit(1)
    ).scalar_one_or_none()
    if not vm_tpl:
        vm_tpl = fallback_tpl
    if not event_tpl:
        event_tpl = fallback_tpl or vm_tpl
    if not pre_end_tpl:
        pre_end_tpl = event_tpl

    if not vm_tpl:
        log.warning("  No mail templates found, skipping mails")
        return

    events = context.get("events", [])
    students = context.get("students", [])
    teachers = context.get("teachers", [])
    app_name = "OpenVLE Demo"

    for event in events:
        if event.status != STATUS_AKTIV_ID:
            continue

        # -- VM deployment mails to students --
        n_students = min(
            len(students),
            config.vms_per_event_template,
        )
        for si in range(n_students):
            student = students[si % len(students)]
            uid = fixture_uuid("mail", profile, idx)
            if not session.get(Mail, uid):
                ts = fixture_timestamp("mail", profile, idx, event.createdAt)
                session.add(
                    Mail(
                        id=uid,
                        subject=(
                            "Virtuelle Maschine erfolgreich bereitgestellt"
                        ),
                        fromName=app_name,
                        fromMail=f"noreply@{profile}.openvle.de",
                        toMail=student.email,
                        sendStatus="sent",
                        templateId=vm_tpl.id,
                        replyTo=f"noreply@{profile}.openvle.de",
                        content_rendered=None,
                        event=event.id,
                        user_id=student.id,
                        createdAt=ts,
                        updatedAt=ts,
                        createdById=SYSTEM_USER_ID,
                        updatedById=SYSTEM_USER_ID,
                    )
                )
                count += 1
            idx += 1

        # -- Event deployment success mail to teachers --
        for teacher in teachers[:2]:
            uid = fixture_uuid("mail", profile, idx)
            if not session.get(Mail, uid):
                ts = fixture_timestamp("mail", profile, idx, event.createdAt)
                session.add(
                    Mail(
                        id=uid,
                        subject=(
                            f"Veranstaltung {event.slug} "
                            f"erfolgreich bereitgestellt"
                        )[:150],
                        fromName=app_name,
                        fromMail=f"noreply@{profile}.openvle.de",
                        toMail=teacher.email,
                        sendStatus="sent",
                        templateId=event_tpl.id,
                        replyTo=f"noreply@{profile}.openvle.de",
                        content_rendered=None,
                        event=event.id,
                        user_id=teacher.id,
                        createdAt=ts,
                        updatedAt=ts,
                        createdById=SYSTEM_USER_ID,
                        updatedById=SYSTEM_USER_ID,
                    )
                )
                count += 1
            idx += 1

        # -- Pre-end reminder mail to teachers --
        for teacher in teachers[:2]:
            uid = fixture_uuid("mail", profile, idx)
            if not session.get(Mail, uid):
                ts = fixture_timestamp("mail", profile, idx, event.createdAt)
                session.add(
                    Mail(
                        id=uid,
                        subject=(f"Veranstaltung {event.name} endet bald")[
                            :150
                        ],
                        fromName=app_name,
                        fromMail=f"noreply@{profile}.openvle.de",
                        toMail=teacher.email,
                        sendStatus="sent",
                        templateId=pre_end_tpl.id,
                        replyTo=f"noreply@{profile}.openvle.de",
                        content_rendered=None,
                        event=event.id,
                        user_id=teacher.id,
                        createdAt=ts,
                        updatedAt=ts,
                        createdById=SYSTEM_USER_ID,
                        updatedById=SYSTEM_USER_ID,
                    )
                )
                count += 1
            idx += 1

    session.flush()
    context["_mail_idx"] = idx
    log.info("  %d mails", count)


def _find_template(session: Session, name: str) -> MailTemplate | None:
    return session.execute(
        select(MailTemplate).where(MailTemplate.name == name)
    ).scalar_one_or_none()
