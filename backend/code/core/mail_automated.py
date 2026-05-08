from pydantic import UUID4
from sqlalchemy import and_

from controllers.base import CRUDBase
from core.config import Settings
from models import Event, Mail, ObjectPermission, SubTask, User, VirtualMachine

from .mariadb import SessionLocal

settings = Settings()


def get_object_owners(db, object_id, object_type):
    object_owners = (
        db.query(User)
        .join(
            ObjectPermission,
            and_(
                ObjectPermission.entity_type == "User",
                ObjectPermission.entity_id == User.id,
            ),
        )
        .filter(
            ObjectPermission.object_id == object_id,
            ObjectPermission.object_type == object_type,
        )
        .distinct()
    )
    return object_owners


# Handles the sending of system triggered Mail creation based on provided SubTask
def system_triggered_mail_handler(kvs_subtask_object_id: UUID4):
    db = SessionLocal()
    kvs_task = db.get(SubTask, kvs_subtask_object_id)
    from controllers.mails import CRUDMail

    match kvs_task.object_type:
        case "VirtualMachine":
            kvs_vm = CRUDBase(VirtualMachine)._get(db, kvs_task.object_id)
            if not kvs_vm:
                pass
            context_objects = [kvs_vm]
            if kvs_vm.event:
                kvs_vm_event = db.get(Event, kvs_vm.event)
                context_objects.append(kvs_vm_event)
            match kvs_task.action:
                case action_type if action_type in [
                    "vm_clone",
                    "template_clone",
                ]:
                    if kvs_task.status == "success":
                        # Send success mail to VirtualMachine owner
                        target_users = (
                            kvs_vm.users
                            if kvs_vm.users
                            else [kvs_vm.createdById]
                        )
                        for user in target_users:
                            new_mail = CRUDMail(Mail).create_system_mail(
                                db=db,
                                mail_action_slug="vm_create_success",
                                user=user,
                                context_objects=context_objects,
                                event_id=kvs_vm.event,
                            )
                    elif kvs_task.status == "failed":
                        # Send failed mail to VirtualMachine owner
                        target_users = (
                            kvs_vm.users
                            if kvs_vm.users
                            else [kvs_vm.createdById]
                        )
                        for user in target_users:
                            new_mail = CRUDMail(Mail).create_system_mail(
                                db=db,
                                mail_action_slug="vm_create_failed",
                                user=user,
                                context_objects=context_objects,
                                event_id=kvs_vm.event,
                            )
                case "vm_delete":
                    if kvs_task.status == "failed":
                        # Send failed mail to VirtualMachine owner
                        target_users = get_object_owners(
                            db, kvs_vm.id, "VirtualMachine"
                        )
                        for user in target_users:
                            new_mail = CRUDMail(Mail).create_system_mail(
                                db=db,
                                mail_action_slug="vm_delete_failed",
                                user=user,
                                context_objects=context_objects,
                                event_id=kvs_vm.event,
                            )
        case "Event":
            from controllers.events import CRUDEvent

            event = CRUDBase(Event).get(db, kvs_task.object_id)
            event_admin = CRUDEvent(Event).get_event_admin(db=db, id=event.id)
            match kvs_task.action:
                case "events_post_deployment":
                    if kvs_task.status == "success":
                        # Send success mail to all Event administrators
                        user = CRUDBase(User).get(db, event.createdById)
                        new_mail = CRUDMail(Mail).create_system_mail(
                            db=db,
                            user=user,
                            context_objects=[event, kvs_task],
                            mail_action_slug="events_post_deployment_success",
                            event_id=event.id,
                        )
                    elif kvs_task.status == "failed":
                        # Send failed mail to all Event administrators
                        user = CRUDBase(User).get(db, event.createdById)
                        new_mail = CRUDMail(Mail).create_system_mail(
                            db=db,
                            user=user,
                            context_objects=[event, kvs_task],
                            mail_action_slug="events_post_deployment_failed",
                            event_id=event.id,
                        )
                case "events_post_decommission":
                    if kvs_task.status == "success":
                        user = CRUDBase(User).get(db, event.createdById)
                        new_mail = CRUDMail(Mail).create_system_mail(
                            db=db,
                            user=user,
                            context_objects=[event, kvs_task],
                            mail_action_slug="events_post_decommission_success",
                            event_id=event.id,
                        )
                    elif kvs_task.status == "failed":
                        user = CRUDBase(User).get(db, event.createdById)
                        new_mail = CRUDMail(Mail).create_system_mail(
                            db=db,
                            user=user,
                            context_objects=[event, kvs_task],
                            mail_action_slug="events_post_decommission_failed",
                            event_id=event.id,
                        )
    db.close()
