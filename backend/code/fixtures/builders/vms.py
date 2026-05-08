import logging

from sqlalchemy.orm import Session

from core.core_utils import convert_to_slug
from fixtures.constants import (
    PROXMOX_MANUAL_VM_BASE_ID,
    PROXMOX_NODE,
    PROXMOX_VM_BASE_ID,
    STATUS_AKTIV_ID,
    ensure_association,
    fixture_timestamp,
    fixture_uuid,
    next_audit_user,
)
from fixtures.profiles import ProfileConfig
from models.associations import (
    template_app_association_table,
    template_event_association_table,
    user_vm_association_table,
    vm_app_association_table,
)
from models.virtual_machines import VirtualMachine

log = logging.getLogger("fixtures")


def _copy_template_apps(session, template_id, vm_id) -> None:
    """Copy app associations from a template to a VM."""
    rows = session.execute(
        template_app_association_table.select().where(
            template_app_association_table.c.template_id == template_id
        )
    ).fetchall()
    for row in rows:
        ensure_association(
            session,
            vm_app_association_table,
            vm_id=vm_id,
            app_id=row.app_id,
        )


def create_virtual_machines(
    session: Session,
    config: ProfileConfig,
    context: dict,
) -> None:
    profile = config.name.value
    vms: list[VirtualMachine] = []
    idx = 0

    students = context["students"]
    templates_by_id = {t.id: t for t in context["templates"]}

    for event in context["events"]:
        if event.status != STATUS_AKTIV_ID:
            continue

        rows = session.execute(
            template_event_association_table.select().where(
                template_event_association_table.c.event_id == event.id,
            )
        ).fetchall()
        event_template_ids = [r.template_id for r in rows]

        for tpl_id in event_template_ids:
            tpl = templates_by_id.get(tpl_id)
            if not tpl:
                continue

            for v in range(config.vms_per_event_template):
                uid = fixture_uuid("vm", profile, idx)
                existing = session.get(VirtualMachine, uid)
                if existing:
                    vms.append(existing)
                    idx += 1
                    continue

                student = students[idx % len(students)] if students else None
                slug_event = convert_to_slug(event.slug, max_length=8)
                slug_user = (
                    convert_to_slug(student.username, max_length=10)
                    if student
                    else f"vm{v:02d}"
                )
                vm_name = (
                    f"{slug_event}-temp{tpl.proxmoxId}-{slug_user}-studierende"
                )[:100]

                vm = VirtualMachine(
                    id=uid,
                    name=vm_name,
                    description=(f"Bereitgestellte VM fuer {event.name}"),
                    status="running",
                    proxmoxId=PROXMOX_VM_BASE_ID + idx,
                    proxmoxNode=PROXMOX_NODE,
                    cpu=tpl.cpu,
                    ram=tpl.ram,
                    disk=tpl.disk,
                    os=tpl.os,
                    template=tpl.id,
                    event=event.id,
                    prevent_delete=False,
                    ipv4=(f"172.20.{(idx // 254) + 1}.{(idx % 254) + 1}"),
                    createdAt=fixture_timestamp(
                        "vm", profile, idx, event.createdAt
                    ),
                    updatedAt=fixture_timestamp(
                        "vm_upd", profile, idx, event.createdAt
                    ),
                    createdById=next_audit_user(context),
                    updatedById=next_audit_user(context),
                )
                session.add(vm)
                session.flush()

                _copy_template_apps(session, tpl.id, uid)

                if students:
                    student = students[idx % len(students)]
                    ensure_association(
                        session,
                        user_vm_association_table,
                        user_id=student.id,
                        vm_id=uid,
                    )

                vms.append(vm)
                idx += 1

    # -- Manual VMs (no event, created by teachers) --
    teachers = context.get("teachers", [])
    templates = context.get("templates", [])
    manual_statuses = ["running", "stopped", "stopped", "running"]
    manual_names = [
        "Test-VM-{teacher}",
        "Dev-Server-{teacher}",
        "Playground-{teacher}",
        "Sandbox-{teacher}",
        "Prototyp-{teacher}",
    ]
    n_manual = min(config.vms_per_event_template, len(teachers))

    for mi in range(n_manual):
        uid = fixture_uuid("manual_vm", profile, mi)
        existing = session.get(VirtualMachine, uid)
        if existing:
            vms.append(existing)
            continue

        teacher = teachers[mi % len(teachers)]
        tpl = templates[mi % len(templates)] if templates else None
        slug_teacher = convert_to_slug(teacher.username, max_length=10)
        vm_name = manual_names[mi % len(manual_names)].format(
            teacher=slug_teacher
        )

        vm = VirtualMachine(
            id=uid,
            name=vm_name,
            description=(f"Manuell erstellte VM von {teacher.name}"),
            status=manual_statuses[mi % len(manual_statuses)],
            proxmoxId=PROXMOX_MANUAL_VM_BASE_ID + mi,
            proxmoxNode=PROXMOX_NODE,
            cpu=tpl.cpu if tpl else 2,
            ram=tpl.ram if tpl else 4096,
            disk=tpl.disk if tpl else 32,
            os=tpl.os if tpl else None,
            template=tpl.id if tpl else None,
            event=None,
            prevent_delete=False,
            ipv4=f"172.21.0.{mi + 1}",
            createdAt=fixture_timestamp(
                "manual_vm", profile, mi, teacher.createdAt
            ),
            updatedAt=fixture_timestamp(
                "manual_vm_upd", profile, mi, teacher.createdAt
            ),
            createdById=teacher.id,
            updatedById=teacher.id,
        )
        session.add(vm)
        session.flush()

        if tpl:
            _copy_template_apps(session, tpl.id, uid)

        ensure_association(
            session,
            user_vm_association_table,
            user_id=teacher.id,
            vm_id=uid,
        )

        vms.append(vm)

    session.flush()
    context["vms"] = vms
    log.info("  %d virtual machines (%d manual)", len(vms), n_manual)
