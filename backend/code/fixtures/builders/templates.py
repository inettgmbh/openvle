import logging
from collections import defaultdict

from sqlalchemy.orm import Session

from fixtures.builders.apps import TEMPLATE_APP_MAPPING
from fixtures.constants import (
    APP_CHROME_ID,
    APP_FIREFOX_ID,
    APP_VSCODE_ID,
    APP_WORD_2022_ID,
    OS_DEBIAN_12_ID,
    OS_UBUNTU_2204_ID,
    OS_WINDOWS_11_ID,
    PROXMOX_NODE,
    PROXMOX_TEMPLATE_BASE_ID,
    ensure_association,
    fixture_timestamp,
    fixture_uuid,
    next_audit_user,
)
from fixtures.profiles import ProfileConfig
from models.associations import (
    course_template_association_table,
    template_app_association_table,
)
from models.guacamole_connection_profiles import (
    GuacamoleConnectionProfile,
)
from models.templates import Template

log = logging.getLogger("fixtures")

# Template definitions cycled through per course
TEMPLATE_DEFS = [
    {
        "name": "Debian-12-Lab",
        "os": OS_DEBIAN_12_ID,
        "cpu": 2,
        "ram": 4096,
        "disk": 32,
        "apps": [APP_VSCODE_ID, APP_FIREFOX_ID],
        "protocol": "ssh",
        "port": 22,
    },
    {
        "name": "Windows-11-Desktop",
        "os": OS_WINDOWS_11_ID,
        "cpu": 4,
        "ram": 8192,
        "disk": 64,
        "apps": [APP_CHROME_ID, APP_WORD_2022_ID],
        "protocol": "rdp",
        "port": 3389,
    },
    {
        "name": "Ubuntu-Dev-Environment",
        "os": OS_UBUNTU_2204_ID,
        "cpu": 2,
        "ram": 4096,
        "disk": 40,
        "apps": [APP_VSCODE_ID, APP_CHROME_ID],
        "protocol": "ssh",
        "port": 22,
    },
]


def create_templates(
    session: Session,
    config: ProfileConfig,
    context: dict,
) -> None:
    profile = config.name.value
    not_before = context.get("earliest_course")
    templates: list[Template] = []
    templates_by_course: dict[str, list] = defaultdict(list)
    idx = 0

    for course in context["courses"]:
        for _t in range(config.templates_per_course):
            tpl_def = TEMPLATE_DEFS[idx % len(TEMPLATE_DEFS)]
            uid = fixture_uuid("template", profile, idx)
            existing = session.get(Template, uid)
            if existing:
                templates.append(existing)
                templates_by_course[course.id].append(existing)
                idx += 1
                continue

            proxmox_id = PROXMOX_TEMPLATE_BASE_ID + idx
            template = Template(
                id=uid,
                name=f"{tpl_def['name']}-T{proxmox_id}",
                description=(
                    f"VM-Vorlage {tpl_def['name']} fuer den Kurs {course.name}"
                ),
                status="available",
                proxmoxId=proxmox_id,
                proxmoxNode=PROXMOX_NODE,
                cpu=tpl_def["cpu"],
                ram=tpl_def["ram"],
                disk=tpl_def["disk"],
                os=tpl_def["os"],
                prevent_delete=False,
                createdAt=fixture_timestamp(
                    "template", profile, idx, not_before
                ),
                updatedAt=fixture_timestamp(
                    "template_upd", profile, idx, not_before
                ),
                createdById=next_audit_user(context),
                updatedById=next_audit_user(context),
            )
            session.add(template)
            session.flush()

            # App associations
            all_app_ids = list(tpl_def["apps"])
            apps_by_key = context.get("apps_by_key", {})
            for prefix, app_keys in TEMPLATE_APP_MAPPING.items():
                if tpl_def["name"].startswith(prefix):
                    for ak in app_keys:
                        app = apps_by_key.get(ak)
                        if app and app.id not in all_app_ids:
                            all_app_ids.append(app.id)

            for app_id in all_app_ids:
                ensure_association(
                    session,
                    template_app_association_table,
                    template_id=uid,
                    app_id=app_id,
                )

            # Connection profile for template
            gcp_uid = fixture_uuid("tpl_gcp", profile, idx)
            if not session.get(GuacamoleConnectionProfile, gcp_uid):
                gcp_ts = fixture_timestamp(
                    "tpl_gcp", profile, idx, template.createdAt
                )
                gcp_author = next_audit_user(context)
                session.add(
                    GuacamoleConnectionProfile(
                        id=gcp_uid,
                        port=tpl_def["port"],
                        protocol=tpl_def["protocol"],
                        username="admin",
                        password="fixture",
                        objectId=uid,
                        objectType="Template",
                        createdAt=gcp_ts,
                        updatedAt=gcp_ts,
                        createdById=gcp_author,
                        updatedById=gcp_author,
                    )
                )
                session.flush()

            # Course-template association
            ensure_association(
                session,
                course_template_association_table,
                course_id=course.id,
                template_id=uid,
            )

            templates.append(template)
            templates_by_course[course.id].append(template)
            idx += 1

    session.flush()
    if templates:
        context["earliest_template"] = min(t.createdAt for t in templates)
    context["templates"] = templates
    context["templates_by_course"] = dict(templates_by_course)
    log.info("  %d templates", len(templates))
