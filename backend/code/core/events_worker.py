from collections import defaultdict
from typing import Any

from proxmoxer.core import ResourceException
from rq import Retry
from sqlalchemy.orm import Session

from controllers.base import CRUDBase
from controllers.changelog import CRUDChangelog
from controllers.mails import CRUDMail
from controllers.sub_tasks import CRUDSubTask
from controllers.tasks import CRUDTask
from controllers.virtual_machines import CRUDVirtualMachine
from core.exceptions import JobEnqueueError
from core.guacamole import guacamole_connect
from core.redis import (
    queue_core_periodic,
    queue_pve_vm_actions,
    queue_pve_vm_clone,
)
from models import (
    Changelog,
    Course,
    Event,
    EventStatus,
    EventsUser,
    Guacamole,
    GuacamoleConnectionProfile,
    Mail,
    Role as RoleModel,
    SubTask,
    Task,
    Template,
    User as UserModel,
    VirtualMachine,
)
from pve.cluster import ProxmoxCluster
from schemas.sub_tasks import SubTaskCreate
from schemas.tasks import TaskCreate
from schemas.virtual_machines import VirtualMachineEventCreate

from .mariadb import SessionLocal


def events_post_deployment(
    kvs_task_object_id: Any, kvs_event_id: Any, virtual_machines: list
):
    """
    param: kvs_task_object_id - ID of SubTask for events_post_deployment
    param: event_id - ID of Event to be updated
    param: virtual_machines - List of VirtualMachines ID's that were enqueued for creation
    Events post deployment process used to ensure that all VirtualMachines (and optionally Guacamole) objects were successfully
    deployed. If all tasks have been completed, the task then updates the Event with the Active status.
    """
    # Set db variable to MariaDB session
    try:
        db = SessionLocal()
    except:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id, 401, "Unable to establish connection to MariaDB"
        )

    # Step 1: Get and update Task object
    CRUDSubTask(SubTask).worker_process_start(db, kvs_task_object_id)

    # Check that Event exists
    event = db.get(Event, kvs_event_id)
    if not event:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            404,
            f"Event with ID {kvs_event_id} not found",
            db,
        )

    # Create list to store VirtualMachines that do not have an ipv4 (this means that an error occurred somewhere in the deployment process)
    vms_batch = (
        db.query(VirtualMachine)
        .filter(VirtualMachine.id.in_(virtual_machines))
        .all()
    )
    vms_by_id = {vm.id: vm for vm in vms_batch}
    failed_deployments = []
    for vm_id in virtual_machines:
        virtual_machine = vms_by_id.get(vm_id)
        if not virtual_machine or not virtual_machine.ipv4:
            failed_deployments.append(vm_id)

    # If there were any failed deployments, update SubTask with list of effected VirtualMachines
    if failed_deployments:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            400,
            f"The following VirtualMachines encountered errors during deployment: {failed_deployments}",
            db,
        )

    # If there were no failed deployments, update Event with Active status
    event_status_active = (
        db.query(EventStatus).filter(EventStatus.name == "Aktiv").first()
    )
    if not event_status_active:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            404,
            "EventStatus 'Aktiv' not found",
            db,
        )
    old_status = event.status
    event.status = event_status_active.id
    event = db.merge(event)
    db.add(event)
    db.commit()
    request_user_id = db.get(SubTask, kvs_task_object_id).createdById
    status_changelog = CRUDChangelog(Changelog)._create_for_changes(
        db=db,
        user_id=request_user_id,
        object_type="Event",
        object_id=event.id,
        changes=[
            {
                "field": "status",
                "value_old": old_status,
                "value_new": event.status,
            }
        ],
    )
    return CRUDSubTask(SubTask).worker_process_success(
        kvs_task_object_id,
        201,
        "Event deployment was successful and Event status has been updated",
        db,
    )


def events_post_decommission(
    kvs_task_object_id: Any,
    kvs_event_id: Any,
    virtual_machines: list,
    protected_vm_count: int = 0,
):
    """
    param: kvs_task_object_id - ID of SubTask for events_post_decommission
    param: event_id - ID of Event to be updated
    param: virtual_machines - List of VirtualMachines ID's that were enqueued for deletion
    Events post deployment process used to ensure that all VirtualMachines (and optionally Guacamole) objects were successfully
    deleted. If all tasks have been completed, the task then updates the Event with the Archived status.
    """
    # Set db variable to MariaDB session
    try:
        db = SessionLocal()
    except:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id, 401, "Unable to establish connection to MariaDB"
        )

    # Step 1: Get and update Task object
    CRUDSubTask(SubTask).worker_process_start(db, kvs_task_object_id)

    # Check that Event exists
    event = db.get(Event, kvs_event_id)
    if not event:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            404,
            f"Event with ID {kvs_event_id} not found",
            db,
        )

    # Create list to store VirtualMachines that still exist
    failed_deletions = []
    virtual_machines = db.query(VirtualMachine).filter(
        VirtualMachine.event == event.id
    )
    for vm in virtual_machines:
        failed_deletions.append(vm.id)

    # If there were any failed deployments, update SubTask with list of effected VirtualMachines
    if failed_deletions:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            400,
            f"The following VirtualMachines encountered errors during decommissioning and will need to be deleted manually before deleting the Event: {failed_deletions}",
            db,
        )

    # If there were no failed deployments, update Event with Archived status
    event_status_archived = (
        db.query(EventStatus).filter(EventStatus.name == "Archiviert").first()
    )
    if not event_status_archived:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            404,
            "EventStatus 'Archiviert' not found",
            db,
        )
    old_status = event.status
    event.status = event_status_archived.id
    event = db.merge(event)
    db.add(event)
    db.commit()
    request_user_id = db.get(SubTask, kvs_task_object_id).createdById
    status_changelog = CRUDChangelog(Changelog)._create_for_changes(
        db=db,
        user_id=request_user_id,
        object_type="Event",
        object_id=event.id,
        changes=[
            {
                "field": "status",
                "value_old": old_status,
                "value_new": event.status,
            }
        ],
    )
    # Check if there are any existing Guacamole folders and delete them
    if event.guacamole:
        try:
            guacamole = guacamole_connect()
            if not guacamole:
                return CRUDSubTask(SubTask).worker_process_fail(
                    kvs_task_object_id,
                    500,
                    "Connection to Guacamole server could not be made.",
                    db,
                )
            connection_groups = guacamole.list_connection_groups()
            parent_identifier = next(
                (
                    k
                    for k, v in connection_groups.items()
                    if v.get("name") == event.slug
                ),
                None,
            )
            if parent_identifier:
                conn_group_delete = guacamole.delete_connection_group(
                    identifier=parent_identifier
                )
                if "message" in conn_group_delete:
                    return CRUDSubTask(SubTask).worker_process_fail(
                        kvs_task_object_id,
                        400,
                        "There are still active VirtualMachines assigned to the Event. Please decommission them before deleting the Event.",
                        db,
                    )
        except:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id,
                400,
                "An unknown error has occurred while attempting to handle Event's Guacamole folders.",
                db,
            )
    success_message = (
        "Event decommissioning was successful and Event status has been updated"
    )
    if protected_vm_count:
        success_message += f". {protected_vm_count} VirtualMachine(s) were skipped as they are protected."
    return CRUDSubTask(SubTask).worker_process_success(
        kvs_task_object_id,
        201,
        success_message,
        db,
    )


def create_vm_for_event_user(
    db: Session,
    event: Event,
    template: Template,
    user_role: RoleModel,
    user: UserModel,
):
    new_vm_name = str(f"{event.slug}-{user.username}-t{template.proxmoxId}")
    # Check if VirtualMachine with that name already exists (VM already created in previous start attempt)
    vm_in_db = (
        db.query(VirtualMachine)
        .filter(VirtualMachine.name == new_vm_name)
        .first()
    )
    if vm_in_db:
        return {"VirtualMachine": vm_in_db, "worker_tasks": None}
    new_vm_schema = VirtualMachineEventCreate(
        name=new_vm_name,
        description=f"{template.description if template.description else ''}\n Created for Event: {event.name}",
        cpu=template.cpu,
        ram=template.ram,
        template=template.id,
        prevent_delete=False,
        event=event.id,
        user=user.id,
    )
    new_vm = CRUDVirtualMachine(VirtualMachine).create_from_template_event(
        db=db, request=None, obj_in=new_vm_schema
    )
    return new_vm


def task_event_post_deployment(
    db: Session,
    event: Event,
    vms_deploying: list,
    task_dependencies: list = None,
):
    # Create Task object - Event post deployment
    new_task_schema = TaskCreate(
        name="Event post deployment process", event_id=event.id
    )
    new_task = CRUDTask(Task).create(
        db=db, request=None, obj_in=new_task_schema
    )
    # Create SubTask objects and enqueue job (events_post_deployment)
    sub_task_pdp_schema = SubTaskCreate(
        name="Event post deployment process",
        object_type="Event",
        object_id=event.id,
        action="events_post_deployment",
        attempt=0,
        parent_task=new_task.id,
    )
    sub_task_pdp = CRUDSubTask(SubTask).create(
        db=db, request=None, obj_in=sub_task_pdp_schema
    )
    job_pdp = queue_core_periodic.enqueue(
        events_post_deployment,
        kvs_event_id=event.id,
        virtual_machines=vms_deploying,
        kvs_task_object_id=sub_task_pdp.id,
        depends_on=task_dependencies,
        retry=Retry(max=5, interval=[10, 30, 60]),
    )
    if not job_pdp:
        raise JobEnqueueError(job_key="events_post_deployment")


def task_event_post_decommission(
    db: Session,
    event: Event,
    vms_decommissioning: list,
    task_dependencies: list,
    protected_vm_count: int = 0,
):
    # Create Task object - Event post decommission
    new_task_schema = TaskCreate(
        name="Event post decommission process", event_id=event.id
    )
    new_task = CRUDTask(Task).create(
        db=db, request=None, obj_in=new_task_schema
    )
    # Create SubTask objects and enqueue job (events_post_decommission)
    sub_task_pdp_schema = SubTaskCreate(
        name="Event post deployment process",
        object_type="Event",
        object_id=event.id,
        action="events_post_decommission",
        attempt=0,
        parent_task=new_task.id,
    )
    sub_task_pdp = CRUDSubTask(SubTask).create(
        db=db, request=None, obj_in=sub_task_pdp_schema
    )
    job_pdp = queue_core_periodic.enqueue(
        events_post_decommission,
        kvs_event_id=event.id,
        virtual_machines=vms_decommissioning,
        kvs_task_object_id=sub_task_pdp.id,
        protected_vm_count=protected_vm_count,
        depends_on=task_dependencies,
        retry=Retry(max=5, interval=[10, 30, 60]),
    )
    if not job_pdp:
        raise JobEnqueueError(job_key="events_post_decommission")


def pre_start_mail(db: Session, event: Event, event_admin: list):
    """
    event_admin: list of User IDs
    """
    if not event_admin:
        return
    users = {
        u.id: u
        for u in db.query(UserModel).filter(UserModel.id.in_(event_admin)).all()
    }
    for user_id in event_admin:
        user = users.get(user_id)
        if not user:
            continue
        CRUDMail(Mail).create_system_mail(
            db=db,
            user=user,
            context_objects=[event],
            mail_action_slug="events_deployment_started",
            event_id=event.id,
        )


# Worker function to asynchronously enqueue VirtualMachine and Guacamole deployment jobs when an Event is started
def events_start_worker(
    kvs_task_object_id: Any,
    kvs_event_id: Any,
    moodle_job_id: str | None = None,
):
    db = SessionLocal()
    try:
        # Get and update Task object
        CRUDSubTask(SubTask).worker_process_start(db, kvs_task_object_id)
        event: Event = db.get(Event, kvs_event_id)
        if not event:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id, 404, f"Event {kvs_event_id} not found", db
            )

        role_teacher = (
            db.query(RoleModel).filter(RoleModel.key == "lehrende").first()
        )
        if not role_teacher:
            return CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id,
                404,
                "Role 'lehrende' not found",
                db,
            )
        event_users = (
            db.query(EventsUser).filter(EventsUser.event_id == event.id).all()
        )

        course_templates = (
            db.query(Template)
            .join(Template.courses)
            .filter(Course.id == event.course)
            .all()
        )
        event.templates = course_templates
        db.commit()

        # Batch-fetch all users and roles needed for VM creation
        all_user_ids = list({eu.user_id for eu in event_users})
        all_role_ids = list({eu.role_id for eu in event_users})
        users_by_id = {
            u.id: u
            for u in db.query(UserModel)
            .filter(UserModel.id.in_(all_user_ids))
            .all()
        }
        roles_by_id = {
            r.id: r
            for r in db.query(RoleModel)
            .filter(RoleModel.id.in_(all_role_ids))
            .all()
        }

        # Create VMs/Guac for each (template x user)
        vms_deploying = []
        post_deployment_dependencies = []

        for template in event.templates:
            for eu in event_users:
                try:
                    user_role = roles_by_id.get(eu.role_id)
                    user = users_by_id.get(eu.user_id)
                    if not user_role or not user:
                        continue

                    # Create VirtualMachine
                    new_vm = create_vm_for_event_user(
                        db=db,
                        event=event,
                        template=template,
                        user_role=user_role,
                        user=user,
                    )
                    if new_vm["worker_tasks"]:
                        post_deployment_dependencies.extend(
                            new_vm["worker_tasks"]
                        )
                    vms_deploying.append(new_vm["VirtualMachine"].id)
                except Exception as e:
                    CRUDSubTask(SubTask).worker_process_fail(
                        kvs_task_object_id,
                        500,
                        f"VM create failed for user {eu.user_id}: {e}",
                        db,
                    )

        # Include Moodle job as post-deployment dependency so the
        # event only transitions to "Aktiv" after Moodle is done.
        if moodle_job_id:
            post_deployment_dependencies.append(moodle_job_id)

        task_event_post_deployment(
            db=db,
            event=event,
            vms_deploying=vms_deploying,
            task_dependencies=post_deployment_dependencies,
        )

        # Pre-start mail (teachers)
        teachers = [
            eu.user_id for eu in event_users if eu.role_id == role_teacher.id
        ]
        pre_start_mail(db=db, event=event, event_admin=teachers)

        return CRUDSubTask(SubTask).worker_process_success(
            kvs_task_object_id,
            200,
            f"Event worker successfully enqueued {len(vms_deploying)} VirtualMachines for deployment",
            db,
        )
    except Exception as e:
        return CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            500,
            f"Event worker has encountered an unexpected error: {e}",
            db,
        )


# Worker function to asynchronously handle VirtualMachine and Guacamole decommissioning when an Event is ended
def events_end_worker(kvs_task_object_id: Any, kvs_event_id: Any):
    db = SessionLocal()
    try:
        # Get and update Task object
        CRUDSubTask(SubTask).worker_process_start(db, kvs_task_object_id)
        event: Event = db.get(Event, kvs_event_id)
        if not event:
            CRUDSubTask(SubTask).worker_process_fail(
                kvs_task_object_id, 404, f"Event {kvs_event_id} not found", db
            )
            return

        vms_decommissioning: list = []
        post_decommission_dependencies: list = []
        protected_vm_count: int = 0

        # All VMs assigned to this event
        event_vms = (
            db.query(VirtualMachine)
            .filter(VirtualMachine.event == event.id)
            .all()
        )

        # Batch-load all GCPs and Guacamoles for event VMs
        event_vm_ids = [v.id for v in event_vms]
        all_gcps = []
        all_guacs = []
        if event_vm_ids and event.guacamole:
            all_gcps = (
                db.query(GuacamoleConnectionProfile)
                .filter(
                    GuacamoleConnectionProfile.objectId.in_(event_vm_ids),
                    GuacamoleConnectionProfile.objectType == "VirtualMachine",
                )
                .all()
            )
            all_gcp_ids = [gcp.id for gcp in all_gcps]
            if all_gcp_ids:
                all_guacs = (
                    db.query(Guacamole)
                    .filter(Guacamole.connection_profile.in_(all_gcp_ids))
                    .all()
                )

        # Build lookup dicts: vm_id -> [gcps], gcp_id -> [guacs]
        gcps_by_vm = defaultdict(list)
        for gcp in all_gcps:
            gcps_by_vm[gcp.objectId].append(gcp)
        guacs_by_gcp = defaultdict(list)
        for guac in all_guacs:
            guacs_by_gcp[guac.connection_profile].append(guac)

        _proxmox = ProxmoxCluster()

        for vm in event_vms:
            # Check protection: DB field + Proxmox config
            is_protected = vm.prevent_delete
            if not is_protected and vm.proxmoxId:
                try:
                    pve_config = (
                        _proxmox.proxmox.nodes(
                            _proxmox.pve_get_node(vm.proxmoxId)
                        )
                        .qemu(vm.proxmoxId)
                        .config.get()
                    )
                    if pve_config.get("protection") == 1:
                        vm.prevent_delete = True
                        db.add(vm)
                        db.commit()
                        db.refresh(vm)
                        is_protected = True
                except ResourceException as e:
                    return CRUDSubTask(SubTask).worker_process_fail(
                        kvs_task_object_id,
                        502,
                        f"Failed to retrieve VirtualMachine protection status from Proxmox VE. ID: {vm.id}",
                        db,
                    )

            if is_protected:
                protected_vm_count += 1
                # Delete Event Guacamole connections for this VM before detaching
                if event.guacamole:
                    gcps = gcps_by_vm.get(vm.id, [])
                    if gcps:
                        new_task = CRUDTask(Task).create(
                            db=db,
                            request=None,
                            obj_in=TaskCreate(
                                name=f"Delete Guacamole for Protected VM: {vm.name}",
                                event_id=event.id,
                            ),
                        )
                        for gcp in gcps:
                            guacs = guacs_by_gcp.get(gcp.id, [])
                            for guac in guacs:
                                CRUDVirtualMachine(
                                    db=db, id=vm.id
                                )._subtask_vm_guac_delete(
                                    db=db,
                                    request=None,
                                    parent_task_id=new_task.id,
                                    queue=queue_pve_vm_actions,
                                    guacamole_id=guac.id,
                                )
                try:
                    vm.event = None
                    db.add(vm)
                    db.commit()
                except Exception:
                    CRUDSubTask(SubTask).worker_process_fail(
                        kvs_task_object_id,
                        423,
                        f"Protected VM detach failed. ID: {vm.id})",
                        db,
                    )
                continue

            vms_decommissioning.append(vm.id)

            new_task = CRUDTask(Task).create(
                db=db,
                request=None,
                obj_in=TaskCreate(
                    name=f"Delete VirtualMachine (ID={vm.proxmoxId}) for Event",
                    event_id=event.id,
                ),
            )

            # If guacamole, enqueue guac deletions first
            guac_deps = []
            if event.guacamole:
                gcps = gcps_by_vm.get(vm.id, [])

                for gcp in gcps:
                    guacs = guacs_by_gcp.get(gcp.id, [])
                    for guac in guacs:
                        job = CRUDVirtualMachine(
                            db=db, id=vm.id
                        )._subtask_vm_guac_delete(
                            db=db,
                            request=None,
                            parent_task_id=new_task.id,
                            queue=queue_pve_vm_actions,
                            guacamole_id=guac.id,
                        )
                        if job is not None:
                            guac_deps.append(job)

            job_ha_remove = CRUDVirtualMachine(
                db=db, id=vm.id
            )._subtask_ha_remove(
                db=db,
                request=None,
                parent_task_id=new_task.id,
                queue=queue_pve_vm_actions,
                task_dependencies=guac_deps if guac_deps else None,
            )

            # Stop VM (depends on HA remove)
            job_stop = CRUDVirtualMachine(
                db=db, id=vm.id
            )._subtask_actions_stop(
                db=db,
                request=None,
                parent_task_id=new_task.id,
                queue=queue_pve_vm_actions,
                task_dependencies=[job_ha_remove] if job_ha_remove else None,
            )

            # Delete VM (depends on HA remove + stop)
            deps = [j for j in [job_ha_remove, job_stop] if j is not None]
            job_delete = CRUDVirtualMachine(db=db, id=vm.id)._subtask_vm_delete(
                db=db,
                request=None,
                parent_task_id=new_task.id,
                queue=queue_pve_vm_clone,
                task_dependencies=deps if deps else None,
            )

            if job_delete is not None:
                post_decommission_dependencies.append(job_delete)

            vm.status = "deleting"
            vm = db.merge(vm)
            db.add(vm)
            db.commit()

        # Post-decommission task (depends on all VM deletes)
        task_event_post_decommission(
            db=db,
            event=event,
            vms_decommissioning=vms_decommissioning,
            task_dependencies=post_decommission_dependencies,
            protected_vm_count=protected_vm_count,
        )

        CRUDSubTask(SubTask).worker_process_success(
            kvs_task_object_id,
            200,
            f"Event worker successfully enqueued {len(vms_decommissioning)} VirtualMachines for deletion",
            db,
        )

    except Exception as e:
        db.close()
        CRUDSubTask(SubTask).worker_process_fail(
            kvs_task_object_id,
            500,
            f"Event worker has encountered an unexpected error: {e}",
            db,
        )
