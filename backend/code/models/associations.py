from sqlalchemy import UUID, Column, ForeignKey, Table

from .base import Base

# Association between Users and Roles
user_role_association_table = Table(
    "sys_users_roles",
    Base.metadata,
    Column("user_id", UUID, ForeignKey("sys_users.id"), primary_key=True),
    Column("role_id", UUID, ForeignKey("sys_roles.id"), primary_key=True),
)


# Association between Templates and Application
template_app_association_table = Table(
    "kvs_templates_apps",
    Base.metadata,
    Column(
        "template_id", UUID, ForeignKey("kvs_templates.id"), primary_key=True
    ),
    Column("app_id", UUID, ForeignKey("kvs_apps.id"), primary_key=True),
)

# Association between VirtualMachines and Application
vm_app_association_table = Table(
    "kvs_vms_apps",
    Base.metadata,
    Column("vm_id", UUID, ForeignKey("kvs_vms.id"), primary_key=True),
    Column("app_id", UUID, ForeignKey("kvs_apps.id"), primary_key=True),
)

# Association between VirtualMachines and Guacamole
vm_guac_association_table = Table(
    "kvs_vms_guacamoles",
    Base.metadata,
    Column("vm_id", UUID, ForeignKey("kvs_vms.id"), primary_key=True),
    Column(
        "guacamole_id", UUID, ForeignKey("kvs_guacamole.id"), primary_key=True
    ),
)

# Association between Course and Templates
course_template_association_table = Table(
    "kvs_courses_templates",
    Base.metadata,
    Column("course_id", UUID, ForeignKey("kvs_courses.id"), primary_key=True),
    Column(
        "template_id", UUID, ForeignKey("kvs_templates.id"), primary_key=True
    ),
)

# Association between Events and Templates
template_event_association_table = Table(
    "kvs_events_templates",
    Base.metadata,
    Column("event_id", UUID, ForeignKey("kvs_events.id"), primary_key=True),
    Column(
        "template_id", UUID, ForeignKey("kvs_templates.id"), primary_key=True
    ),
)

# Association between Documents and Applications
documents_apps_association_table = Table(
    "kvs_documents_apps",
    Base.metadata,
    Column(
        "document_id", UUID, ForeignKey("kvs_documents.id"), primary_key=True
    ),
    Column("app_id", UUID, ForeignKey("kvs_apps.id"), primary_key=True),
)

# Association between Documents and OS
documents_os_association_table = Table(
    "kvs_documents_os",
    Base.metadata,
    Column(
        "document_id", UUID, ForeignKey("kvs_documents.id"), primary_key=True
    ),
    Column("os_id", UUID, ForeignKey("kvs_os.id"), primary_key=True),
)

# Association between Users and VirtualMachines
user_vm_association_table = Table(
    "kvs_users_vms",
    Base.metadata,
    Column("user_id", UUID, ForeignKey("sys_users.id"), primary_key=True),
    Column("vm_id", UUID, ForeignKey("kvs_vms.id"), primary_key=True),
)
