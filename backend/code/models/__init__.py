from .apps import Application
from .changelog import Changelog
from .courses import Course
from .documents import Document
from .event_status import EventStatus
from .events import Event
from .events_user import EventsUser
from .guacamole import Guacamole
from .guacamole_connection_profiles import GuacamoleConnectionProfile
from .languages import Language
from .mails import Mail
from .mails_actions import MailAction
from .mails_templates import MailTemplate
from .object_permissions import ObjectPermission
from .os import OS
from .policies import Policy
from .policies_user import PoliciesUser
from .roles import Role
from .sub_tasks import SubTask
from .system import SystemSetting
from .tags import Tag
from .tasks import Task
from .templates import Template
from .users import User
from .vendor import Vendor
from .virtual_machines import VirtualMachine

# Dict {key = model_name, value = permission_prefix}
MODELS_PERMISSIONS = {
    Application.__name__: "applications",
    Changelog.__name__: "changelogs",
    Course.__name__: "courses",
    Document.__name__: "documents",
    EventStatus.__name__: "status_events",
    Event.__name__: "events",
    EventsUser.__name__: None,
    Guacamole.__name__: "guacamoles",
    GuacamoleConnectionProfile.__name__: "guacamole_connection_profiles",
    Language.__name__: "languages",
    Mail.__name__: "mails",
    MailAction.__name__: "mail_actions",
    MailTemplate.__name__: "mail_templates",
    ObjectPermission.__name__: "object_permissions",
    OS.__name__: "os",
    Policy.__name__: "policies",
    PoliciesUser.__name__: "policies_users",
    Role.__name__: "roles",
    SubTask.__name__: "sub_tasks",
    SystemSetting.__name__: "system",
    Tag.__name__: "tags",
    Task.__name__: "tasks",
    Template.__name__: "templates",
    User.__name__: "users",
    Vendor.__name__: "vendors",
    VirtualMachine.__name__: "vms",
}

# Map of object types to their models and permission prefix
object_type_map = {
    "Activity": (None, "activities"),
    "Application": (Application, "applications"),
    "Changelog": (Changelog, "changelogs"),
    "Course": (Course, "courses"),
    "Document": (Document, "documents"),
    "Dashboard": (None, "dashboards"),
    "Event": (Event, "events"),
    "EventStatus": (EventStatus, "status_events"),
    "Guacamole": (Guacamole, "guacamoles"),
    "GuacamoleConnectionProfile": (
        GuacamoleConnectionProfile,
        "guacamole_connection_profiles",
    ),
    "Language": (Language, "languages"),
    "Mail": (Mail, "mails"),
    "MailAction": (MailAction, "mail_actions"),
    "MailTemplate": (MailTemplate, "mail_templates"),
    "ObjectPermission": (ObjectPermission, "object_permissions"),
    "OS": (OS, "os"),
    "Policy": (Policy, "policies"),
    "PoliciesUser": (PoliciesUser, "policies_users"),
    "Proxmox": (None, "proxmox"),
    "Role": (Role, "roles"),
    "SubTask": (SubTask, "sub_tasks"),
    "SystemSetting": (SystemSetting, "system_settings"),
    "Tag": (Tag, "tags"),
    "Task": (Task, "tasks"),
    "Template": (Template, "templates"),
    "User": (User, "users"),
    "Vendor": (Vendor, "vendors"),
    "VirtualMachine": (VirtualMachine, "vms"),
}
