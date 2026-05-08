from fastapi import APIRouter, Depends

from core.config import Settings
from middlewares.changelog import ChangelogMiddleware

# Models
from models import (
    OS as OSModel,
    Application as ApplicationModel,
    Course as CourseModel,
    Document as DocumentModel,
    Event as EventModel,
    EventStatus as EventStatusModel,
    Guacamole as GuacamoleModel,
    MailTemplate as MailTemplateModel,
    Policy as PolicyModel,
    Role as RoleModel,
    Template as TemplateModel,
    User as UserModel,
    Vendor as VendorModel,
    VirtualMachine as VirtualMachineModel,
)

# Routes
from . import (
    activities,
    apps,
    auth,
    changelog,
    courses,
    documents,
    event_status,
    events,
    guacamole,
    guacamole_connection_profiles,
    languages,
    mails,
    mails_actions,
    mails_templates,
    me,
    moodle,
    object_permissions,
    os,
    policies,
    proxmox,
    roles,
    statistics,
    sub_tasks,
    system,
    tags,
    tasks,
    templates,
    users,
    vendor,
    virtual_machines,
)

settings = Settings()

app_router = APIRouter(prefix=f"/v{str(settings.project_version)[0]}")

# Routes - No Changelog tracking
app_router.include_router(activities.router)
app_router.include_router(auth.router)
app_router.include_router(changelog.router)
app_router.include_router(guacamole_connection_profiles.router)
app_router.include_router(languages.router)
app_router.include_router(mails_actions.router)
app_router.include_router(mails.router)
app_router.include_router(me.router)
app_router.include_router(moodle.router)
app_router.include_router(object_permissions.router)
app_router.include_router(proxmox.router)
app_router.include_router(statistics.router)
app_router.include_router(sub_tasks.router)
app_router.include_router(system.router)
app_router.include_router(tags.router)
app_router.include_router(tasks.router)

# Routes - With Changelog tracking
app_router.include_router(
    policies.router,
    dependencies=[Depends(ChangelogMiddleware(model=PolicyModel))],
)
app_router.include_router(
    documents.router,
    dependencies=[Depends(ChangelogMiddleware(model=DocumentModel))],
)
app_router.include_router(
    mails_templates.router,
    dependencies=[Depends(ChangelogMiddleware(model=MailTemplateModel))],
)
app_router.include_router(
    users.router, dependencies=[Depends(ChangelogMiddleware(model=UserModel))]
)
app_router.include_router(
    roles.router, dependencies=[Depends(ChangelogMiddleware(model=RoleModel))]
)
app_router.include_router(
    templates.router,
    dependencies=[Depends(ChangelogMiddleware(model=TemplateModel))],
)
app_router.include_router(
    os.router, dependencies=[Depends(ChangelogMiddleware(model=OSModel))]
)
app_router.include_router(
    apps.router,
    dependencies=[Depends(ChangelogMiddleware(model=ApplicationModel))],
)
app_router.include_router(
    event_status.router,
    dependencies=[Depends(ChangelogMiddleware(model=EventStatusModel))],
)
app_router.include_router(
    vendor.router,
    dependencies=[Depends(ChangelogMiddleware(model=VendorModel))],
)
app_router.include_router(
    virtual_machines.router,
    dependencies=[Depends(ChangelogMiddleware(model=VirtualMachineModel))],
)
app_router.include_router(
    courses.router,
    dependencies=[Depends(ChangelogMiddleware(model=CourseModel))],
)
app_router.include_router(
    events.router, dependencies=[Depends(ChangelogMiddleware(model=EventModel))]
)
app_router.include_router(
    guacamole.router,
    dependencies=[Depends(ChangelogMiddleware(model=GuacamoleModel))],
)
