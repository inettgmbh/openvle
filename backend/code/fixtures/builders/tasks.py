import logging

from sqlalchemy.orm import Session

from fixtures.constants import (
    STATUS_AKTIV_ID,
    STATUS_ARCHIVIERT_ID,
    fixture_timestamp,
    fixture_uuid,
    next_audit_user,
)
from fixtures.profiles import ProfileConfig
from models.sub_tasks import SubTask
from models.tasks import Task

log = logging.getLogger("fixtures")

# Task types that occur during event lifecycle
_DEPLOY_TASKS = [
    ("Create VirtualMachine from T{proxmox_id} for {user}", "template_clone"),
    ("Provision Guacamole connection for {user}", "guac_provision"),
    ("Update VirtualMachine tags", "vm_tags_update"),
]

_DECOMMISSION_TASKS = [
    ("Delete Guacamole connections", "guac_delete"),
    ("Stop VirtualMachine: {vm_name}", "vm_stop"),
    ("Delete VirtualMachine: {vm_name}", "vm_delete"),
]


def create_tasks(
    session: Session,
    config: ProfileConfig,
    context: dict,
) -> None:
    profile = config.name.value
    task_count = 0
    subtask_count = 0
    task_idx = 0
    sub_idx = 0

    events = context.get("events", [])
    vms = context.get("vms", [])
    students = context.get("students", [])
    templates_by_id = {t.id: t for t in context.get("templates", [])}

    vms_by_event = {}
    for vm in vms:
        vms_by_event.setdefault(vm.event, []).append(vm)

    for event in events:
        is_active = event.status == STATUS_AKTIV_ID
        is_archived = event.status == STATUS_ARCHIVIERT_ID
        if not is_active and not is_archived:
            continue

        event_vms = vms_by_event.get(event.id, [])

        # -- Deployment tasks (for active + archived events) --
        # Event post deployment task
        deploy_task_uid = fixture_uuid("task", profile, task_idx)
        if not session.get(Task, deploy_task_uid):
            author = next_audit_user(context)
            session.add(
                Task(
                    id=deploy_task_uid,
                    name="Event post deployment process",
                    status="success",
                    event_id=event.id,
                    description=f"Deployment fuer {event.name}",
                    createdAt=fixture_timestamp(
                        "task", profile, task_idx, event.createdAt
                    ),
                    updatedAt=fixture_timestamp(
                        "task_upd", profile, task_idx, event.createdAt
                    ),
                    createdById=author,
                    updatedById=author,
                )
            )
            task_count += 1
        session.flush()
        deploy_parent = deploy_task_uid
        task_idx += 1

        # Subtasks for each VM in the deployment
        for vm in event_vms:
            tpl = templates_by_id.get(vm.template)
            student = students[sub_idx % len(students)] if students else None

            for task_tpl, action in _DEPLOY_TASKS:
                sub_uid = fixture_uuid("subtask", profile, sub_idx)
                if not session.get(SubTask, sub_uid):
                    name = task_tpl.format(
                        proxmox_id=tpl.proxmoxId if tpl else "?",
                        user=student.username if student else "unknown",
                        vm_name=vm.name,
                    )
                    obj_type = (
                        "VirtualMachine"
                        if "VirtualMachine" in task_tpl
                        else "Guacamole"
                    )
                    author = next_audit_user(context)
                    ts = fixture_timestamp(
                        "subtask", profile, sub_idx, event.createdAt
                    )
                    session.add(
                        SubTask(
                            id=sub_uid,
                            name=name[:250],
                            status="success",
                            object_type=obj_type,
                            object_id=str(vm.id),
                            action=action,
                            attempt="1",
                            parent_task=deploy_parent,
                            response_code="201",
                            response_message=(
                                f"{obj_type} operation successful!"
                            ),
                            createdAt=ts,
                            updatedAt=ts,
                            createdById=author,
                            updatedById=author,
                        )
                    )
                    subtask_count += 1
                sub_idx += 1

        # -- Decommission tasks (only for archived events) --
        if is_archived:
            decom_task_uid = fixture_uuid("task", profile, task_idx)
            if not session.get(Task, decom_task_uid):
                author = next_audit_user(context)
                session.add(
                    Task(
                        id=decom_task_uid,
                        name="Event post decommission process",
                        status="success",
                        event_id=event.id,
                        description=(f"Dekommissionierung fuer {event.name}"),
                        createdAt=fixture_timestamp(
                            "task",
                            profile,
                            task_idx,
                            event.createdAt,
                        ),
                        updatedAt=fixture_timestamp(
                            "task_upd",
                            profile,
                            task_idx,
                            event.createdAt,
                        ),
                        createdById=author,
                        updatedById=author,
                    )
                )
                task_count += 1
            session.flush()
            decom_parent = decom_task_uid
            task_idx += 1

            # Decommission subtasks reference VMs by name
            # (VMs are deleted for archived events)
            for vi in range(min(3, config.vms_per_event_template)):
                vm_name = f"{event.slug}-vm{vi:02d}"
                for task_tpl, action in _DECOMMISSION_TASKS:
                    sub_uid = fixture_uuid("subtask", profile, sub_idx)
                    if not session.get(SubTask, sub_uid):
                        name = task_tpl.format(vm_name=vm_name, user="system")
                        author = next_audit_user(context)
                        ts = fixture_timestamp(
                            "subtask",
                            profile,
                            sub_idx,
                            event.createdAt,
                        )
                        session.add(
                            SubTask(
                                id=sub_uid,
                                name=name[:250],
                                status="success",
                                object_type="VirtualMachine",
                                object_id=None,
                                action=action,
                                attempt="1",
                                parent_task=decom_parent,
                                response_code="200",
                                response_message=(
                                    "Operation completed successfully!"
                                ),
                                createdAt=ts,
                                updatedAt=ts,
                                createdById=author,
                                updatedById=author,
                            )
                        )
                        subtask_count += 1
                    sub_idx += 1

        # -- Mail send tasks --
        mail_task_uid = fixture_uuid("task", profile, task_idx)
        if not session.get(Task, mail_task_uid):
            author = next_audit_user(context)
            session.add(
                Task(
                    id=mail_task_uid,
                    name=f"Send mail for Event {event.name}",
                    status="success",
                    event_id=event.id,
                    createdAt=fixture_timestamp(
                        "task", profile, task_idx, event.createdAt
                    ),
                    updatedAt=fixture_timestamp(
                        "task_upd", profile, task_idx, event.createdAt
                    ),
                    createdById=author,
                    updatedById=author,
                )
            )
            task_count += 1
        session.flush()
        mail_parent = mail_task_uid
        task_idx += 1

        # Mail subtasks
        for _mi in range(2):
            sub_uid = fixture_uuid("subtask", profile, sub_idx)
            if not session.get(SubTask, sub_uid):
                author = next_audit_user(context)
                ts = fixture_timestamp(
                    "subtask", profile, sub_idx, event.createdAt
                )
                session.add(
                    SubTask(
                        id=sub_uid,
                        name="Send mail",
                        status="success",
                        object_type="Mail",
                        object_id=None,
                        action="mails_send",
                        attempt="1",
                        parent_task=mail_parent,
                        response_code="201",
                        response_message="Mail sent successfully",
                        createdAt=ts,
                        updatedAt=ts,
                        createdById=author,
                        updatedById=author,
                    )
                )
                subtask_count += 1
            sub_idx += 1

    session.flush()
    context["_task_idx"] = task_idx
    context["_subtask_idx"] = sub_idx
    log.info("  %d tasks, %d subtasks", task_count, subtask_count)
