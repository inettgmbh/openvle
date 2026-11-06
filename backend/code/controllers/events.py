import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from proxmoxer.core import ResourceException
from pydantic import UUID4
from rq import Retry
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from core.config import Settings
from core.core_utils import request_user_validation
from core.events_worker import (
    events_end_worker,
    events_post_decommission,
    events_post_deployment,
    events_start_worker,
)
from core.exceptions import (
    BadRequestError,
    BulkActionRequirementMissing,
    DuplicateEventUserRoleError,
    GuacamoleConnectionError,
    InvalidStatusError,
    JobEnqueueError,
    ObjectDeleteIntegrityError,
    ObjectInUseError,
    ObjectNotFound,
    OperationDependencyMissing,
    ProtectedObjectError,
    ProxmoxRequestError,
    RequiredParameterMissingError,
)
from core.guacamole import guacamole_connect
from core.moodle import (
    ensure_moodle_user,
    moodle_connect,
    moodle_delete_course,
    moodle_deploy_course_worker,
    moodle_end_event_worker,
    moodle_enrol_user_worker,
    moodle_unenrol_user_worker,
)
from core.redis import (
    queue_core_periodic,
    queue_guacamole,
    queue_moodle,
    queue_pve_vm_actions,
    queue_pve_vm_clone,
)
from middlewares.i18n import _
from models import (
    Changelog,
    Course,
    Event,
    EventStatus,
    EventsUser,
    Guacamole,
    GuacamoleConnectionProfile,
    Mail,
    ObjectPermission,
    Tag,
    Template,
    VirtualMachine,
)
from models.roles import Role as RoleModel
from models.sub_tasks import SubTask as SubTaskModel
from models.tasks import Task as TaskModel
from models.users import User as UserModel
from pve.cluster import ProxmoxCluster
from schemas.events import (
    EventCreate,
    EventStatusReport,
    EventStatusReportConnectionStats,
    EventStatusReportSubTask,
    EventStatusReportTask,
    EventStatusReportTaskStats,
    EventStatusReportVmStats,
    EventUpdate,
    EventUpdateEndDateTime,
    EventUpdateTemplate,
    EventUpdateVirtualMachine,
    EventVirtualMachinesHaAdd,
)
from schemas.events_user import EventsUserCreate
from schemas.sub_tasks import SubTaskCreate
from schemas.tasks import TaskCreate
from schemas.virtual_machines import (
    VirtualMachineBulkHaAdd,
    VirtualMachineEventCreate,
    VirtualMachineIdList,
)

from .base import CRUDBase
from .changelog import CRUDChangelog
from .event_status import CRUDEventStatus
from .guacamole import CRUDGuacamole
from .mails import CRUDMail
from .object_permissions import CRUDObjectPermission
from .sub_tasks import CRUDSubTask
from .tasks import CRUDTask
from .virtual_machines import CRUDVirtualMachine

settings = Settings()


# Task.name values that identify Event lifecycle tasks created by actions_start / actions_stop
_TASK_NAME_LIFECYCLE_START = "Start Event"
_TASK_NAME_LIFECYCLE_END = "End Event"
_LIFECYCLE_TASK_NAMES = (_TASK_NAME_LIFECYCLE_START, _TASK_NAME_LIFECYCLE_END)

# Lifecycle status names that indicate the Event was triggered via actions_start
_START_TRIGGERED_STATUSES = frozenset(
    {"Deploying", "Aktiv", "Deployment Fehler"}
)
# Lifecycle status names that indicate the Event was triggered via actions_stop
_END_TRIGGERED_STATUSES = frozenset(
    {"Archiving", "Archiviert", "Archival Fehler", "Stopped"}
)


class CRUDEvent(CRUDBase[Event, EventCreate, EventUpdate]):
    # Get Event by name
    def get_by_name(self, db: Session, *, name: str) -> Event | None:
        event = db.query(Event).filter(Event.name == name).first()
        return event

    # Get Event by slug
    def get_by_slug(self, db: Session, *, slug: str) -> Event | None:
        event = db.query(Event).filter(Event.slug == slug).first()
        return event

    def get_status(self, db: Session, event_id: UUID4) -> EventStatusReport:
        event = self.get(db, event_id)

        event_status = db.get(EventStatus, event.status)
        current_status = event_status.name if event_status else "Unknown"

        # All VM stats in a single query, computed in Python
        event_vms = (
            db.query(VirtualMachine)
            .filter(VirtualMachine.event == event.id)
            .all()
        )
        vm_total = len(event_vms)
        protected_vm_count = sum(1 for vm in event_vms if vm.prevent_delete)
        vm_running = sum(1 for vm in event_vms if vm.status == "running")
        vm_stopped = sum(
            1
            for vm in event_vms
            if vm.status == "stopped" and vm.ipv4 is not None
        )
        vm_pending = sum(1 for vm in event_vms if vm.ipv4 is None)
        vm_stats = EventStatusReportVmStats(
            total=vm_total,
            running=vm_running,
            stopped=vm_stopped,
            pending=vm_pending,
            protected=protected_vm_count,
        )

        # Connection stats — Guacamole records linked to this event
        event_guacs = (
            db.query(Guacamole).filter(Guacamole.eventId == event.id).all()
        )
        guac_total = len(event_guacs)
        guac_deployed = sum(1 for g in event_guacs if g.identifier is not None)
        connection_stats = EventStatusReportConnectionStats(
            total=guac_total,
            deployed=guac_deployed,
            pending=guac_total - guac_deployed,
        )

        # Task stats — single GROUP BY query instead of 4 separate count queries
        event_task_ids = db.query(TaskModel.id).filter(
            TaskModel.event_id == event.id
        )
        subtask_counts = dict(
            db.query(SubTaskModel.status, func.count(SubTaskModel.id))
            .filter(SubTaskModel.parent_task.in_(event_task_ids))
            .group_by(SubTaskModel.status)
            .all()
        )
        task_stats = EventStatusReportTaskStats(
            total=sum(subtask_counts.values()),
            queued=subtask_counts.get("queued", 0),
            processing=subtask_counts.get("processing", 0),
            success=subtask_counts.get("success", 0),
            failed=subtask_counts.get("failed", 0),
        )

        # Determine who initiated the current status
        if current_status == "Geplant":
            status_initiator = event.createdById
        elif current_status in _START_TRIGGERED_STATUSES:
            start_task = (
                db.query(TaskModel)
                .filter(
                    TaskModel.event_id == event.id,
                    TaskModel.name == _TASK_NAME_LIFECYCLE_START,
                )
                .order_by(TaskModel.createdAt.desc())
                .first()
            )
            status_initiator = (
                start_task.createdById if start_task else event.updatedById
            )
        elif current_status in _END_TRIGGERED_STATUSES:
            end_task = (
                db.query(TaskModel)
                .filter(
                    TaskModel.event_id == event.id,
                    TaskModel.name == _TASK_NAME_LIFECYCLE_END,
                )
                .order_by(TaskModel.createdAt.desc())
                .first()
            )
            status_initiator = (
                end_task.createdById if end_task else event.updatedById
            )
        else:
            # Fallback for "Inaktiv", "Core Fehler", missing EventStatus ("Unknown"),
            # or any future status not in the lifecycle sets above.
            status_initiator = event.updatedById

        tasks = (
            db.query(TaskModel)
            .filter(
                TaskModel.event_id == event.id,
                TaskModel.name.in_(_LIFECYCLE_TASK_NAMES),
            )
            .order_by(TaskModel.createdAt.asc())
            .all()
        )

        # Bulk-fetch all subtasks for all tasks at once to avoid N+1
        task_ids = [t.id for t in tasks]
        all_subtasks = (
            db.query(SubTaskModel)
            .filter(SubTaskModel.parent_task.in_(task_ids))
            .order_by(SubTaskModel.createdAt.asc())
            .all()
            if task_ids
            else []
        )
        subtasks_by_task = defaultdict(list)
        for st in all_subtasks:
            subtasks_by_task[st.parent_task].append(st)

        event_tasks = [
            EventStatusReportTask(
                id=task.id,
                initiatedAt=task.createdAt,
                initiatedBy=task.createdById,
                subTasks=[
                    EventStatusReportSubTask(
                        id=st.id,
                        name=st.name,
                        status=st.status,
                        responseMsg=st.response_message,
                        attempt=st.attempt,
                    )
                    for st in subtasks_by_task[task.id]
                ],
            )
            for task in tasks
        ]

        return EventStatusReport(
            id=event.id,
            currentStatus=current_status,
            statusInitiator=status_initiator,
            vmStats=vm_stats,
            connectionStats=connection_stats,
            taskStats=task_stats,
            tasks=event_tasks,
        )

    def _create_vm_for_event_user(
        self,
        db: Session,
        request: Request,
        template: Template,
        user_role: RoleModel,
        user: UserModel,
    ):
        new_vm_name = str(
            f"{self.db_obj.slug}-{user.username}-t{template.proxmoxId}"
        )
        new_vm_schema = VirtualMachineEventCreate(
            name=new_vm_name,
            description=f"{template.description if template.description else ''}\n Created for Event: {self.db_obj.name}",
            cpu=template.cpu,
            ram=template.ram,
            disk=template.disk,
            template=template.id,
            prevent_delete=False,
            event=self.db_obj.id,
            user=user.id,
        )
        new_vm = CRUDVirtualMachine(VirtualMachine).create_from_template_event(
            db=db, request=request, obj_in=new_vm_schema
        )
        return new_vm

    def _task_event_post_deployment(
        self,
        db: Session,
        request: Request,
        vms_deploying: list,
        task_dependencies: list,
    ):
        # Create Task object - Event post deployment
        new_task_schema = TaskCreate(
            name="Event post deployment process", event_id=self.db_obj.id
        )
        new_task = CRUDTask(TaskModel).create(
            db=db, request=request, obj_in=new_task_schema
        )
        # Create SubTask objects and enqueue job (events_post_deployment)
        sub_task_pdp_schema = SubTaskCreate(
            name="Event post deployment process",
            object_type="Event",
            object_id=self.db_obj.id,
            action="events_post_deployment",
            attempt=0,
            parent_task=new_task.id,
        )
        sub_task_pdp = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_pdp_schema
        )
        job_pdp = queue_core_periodic.enqueue(
            events_post_deployment,
            kvs_event_id=self.db_obj.id,
            virtual_machines=vms_deploying,
            kvs_task_object_id=sub_task_pdp.id,
            depends_on=task_dependencies,
            retry=Retry(max=5, interval=[10, 30, 60]),
        )
        if not job_pdp:
            raise JobEnqueueError(job_key="events_post_deployment")

    def _task_event_post_decommission(
        self,
        db: Session,
        request: Request,
        vms_decommissioning: list,
        task_dependencies: list,
    ):
        # Create Task object - Event post decommission
        new_task_schema = TaskCreate(
            name="Event post decommission process", event_id=self.db_obj.id
        )
        new_task = CRUDTask(TaskModel).create(
            db=db, request=request, obj_in=new_task_schema
        )
        # Create SubTask objects and enqueue job (events_post_decommission)
        sub_task_pdp_schema = SubTaskCreate(
            name="Event post deployment process",
            object_type="Event",
            object_id=self.db_obj.id,
            action="events_post_decommission",
            attempt=0,
            parent_task=new_task.id,
        )
        sub_task_pdp = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_pdp_schema
        )
        job_pdp = queue_core_periodic.enqueue(
            events_post_decommission,
            kvs_event_id=self.db_obj.id,
            virtual_machines=vms_decommissioning,
            kvs_task_object_id=sub_task_pdp.id,
            depends_on=task_dependencies,
            retry=Retry(max=5, interval=[10, 30, 60]),
        )
        if not job_pdp:
            raise JobEnqueueError(job_key="events_post_decommission")

    def _pre_start_mail(self, db: Session, event_admin: list):
        """
        event_admin: list of User IDs
        """
        if not event_admin:
            return
        users = {
            u.id: u
            for u in db.query(UserModel)
            .filter(UserModel.id.in_(event_admin))
            .all()
        }
        for user_id in event_admin:
            user = users.get(user_id)
            if not user:
                continue
            CRUDMail(Mail).create_system_mail(
                db=db,
                user=user,
                context_objects=[self.db_obj],
                mail_action_slug="events_deployment_started",
                event_id=self.db_obj.id,
            )

    def _pre_end_mail(self, db: Session, event_admin: list):
        """
        event_admin: list of EventUser objects
        """
        if not event_admin:
            return
        user_ids = [eu.user_id for eu in event_admin]
        users = {
            u.id: u
            for u in db.query(UserModel)
            .filter(UserModel.id.in_(user_ids))
            .all()
        }
        for eu in event_admin:
            user = users.get(eu.user_id)
            if not user:
                continue
            CRUDMail(Mail).create_system_mail(
                db=db,
                user=user,
                context_objects=[self.db_obj],
                mail_action_slug="events_decommission_started",
                event_id=self.db_obj.id,
            )

    def _delete_mail(self, db: Session, event_admin: list):
        """
        event_admin: list of EventUser objects
        """
        if not event_admin:
            return
        user_ids = [eu.user_id for eu in event_admin]
        users = {
            u.id: u
            for u in db.query(UserModel)
            .filter(UserModel.id.in_(user_ids))
            .all()
        }
        for eu in event_admin:
            user = users.get(eu.user_id)
            if not user:
                continue
            CRUDMail(Mail).create_system_mail(
                db=db,
                user=user,
                context_objects=[self.db_obj],
                mail_action_slug="events_delete",
            )

    def get_event_admin(self, db: Session, id: Any):
        self.db_obj = self.get(db, id)
        role_teacher = (
            db.query(RoleModel).filter(RoleModel.key == "lehrende").first()
        )
        if not role_teacher:
            raise ObjectNotFound(model_name="Role", key="lehrende")
        event_admin = (
            db.query(EventsUser)
            .filter(
                EventsUser.event_id == self.db_obj.id,
                EventsUser.role_id == role_teacher.id,
            )
            .all()
        )
        return event_admin

    def get_event_students(self, db: Session, id: Any):
        self.db_obj = self.get(db, id)
        role_student = (
            db.query(RoleModel).filter(RoleModel.key == "studierende").first()
        )
        if not role_student:
            raise ObjectNotFound(model_name="Role", key="studierende")
        event_students = (
            db.query(EventsUser)
            .filter(
                EventsUser.event_id == self.db_obj.id,
                EventsUser.role_id == role_student.id,
            )
            .all()
        )
        return event_students

    # Create Event
    def create(
        self, db: Session, request: Request, *, obj_in: EventCreate
    ) -> Event:
        obj_in_data = jsonable_encoder(obj_in)
        self._initialize_object_fields(
            db=db, obj_data_in=obj_in_data, request=request
        )
        # Check if status exists
        db_obj_status = CRUDBase(EventStatus).get(db=db, id=obj_in.status)
        self.db_obj.status = db_obj_status.id
        # Check if course exists
        db_obj_course = CRUDBase(Course).get(db=db, id=obj_in.course)
        self.db_obj.course = db_obj_course.id
        db.add(self.db_obj)
        # Create object_full ObjectPermission for object creator
        db_obj_perm = self._create_obj_permission(db, self.db_obj, request)
        db.add(db_obj_perm)
        self._commit(db)
        db.refresh(self.db_obj)
        return self.db_obj

    # Update object with given ModelType/UpdateSchemaType
    def update(
        self, id: Any, db: Session, request: Request, *, obj_in: EventUpdate
    ) -> Event:
        self.db_obj = self.get(db, id)
        obj_data = jsonable_encoder(self.db_obj)
        update_data = self._merge_request_with_db_object(obj_in, obj_data)
        # Check if Event may be updated based on Event.status
        current_status = CRUDBase(EventStatus).get(db=db, id=self.db_obj.status)
        valid_status_list = ["Geplant", "Core Fehler", "Deployment Fehler"]
        if current_status.name not in valid_status_list:
            raise InvalidStatusError(
                current_status=current_status.name,
                action="event_update",
                valid_status_list=valid_status_list,
            )
        self._update_meta(request)
        # If current status is "Core Fehler", set status back to "Geplant" after update
        if current_status.name in ["Core Fehler", "Deployment Fehler"]:
            event_status_planned = CRUDEventStatus(EventStatus).get_by_name(
                db=db, name="Geplant"
            )
            self.db_obj.status = event_status_planned.id
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    # Update object with given ModelType/UpdateSchemaType
    def update_end_datetime(
        self,
        id: Any,
        db: Session,
        request: Request,
        *,
        obj_in: EventUpdateEndDateTime,
    ) -> Event:
        self.db_obj = self.get(db, id)
        obj_data = jsonable_encoder(self.db_obj)
        update_data = self._merge_request_with_db_object(obj_in, obj_data)
        # Check if Event may be updated based on Event.status
        current_status = CRUDBase(EventStatus).get(db=db, id=self.db_obj.status)
        valid_status_list = ["Geplant", "Core Fehler", "Aktiv"]
        if current_status.name not in valid_status_list:
            raise InvalidStatusError(
                current_status=current_status.name,
                action="event_enddate_update",
                valid_status_list=valid_status_list,
            )
        self._update_meta(request)
        # If current status is "Core Fehler", set status back to "Geplant" after update
        if current_status.name == "Core Fehler":
            event_status_planned = CRUDEventStatus(EventStatus).get_by_name(
                db=db, name="Geplant"
            )
            self.db_obj.status = event_status_planned.id
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    # Add User to event (create EventUser object)
    def add_user(
        self,
        id: Any,
        db: Session,
        request: Request,
        *,
        obj_in: EventsUserCreate,
    ) -> EventsUser:
        # Check if event exists
        self.db_obj = self.get(db, id)
        obj_in_data = jsonable_encoder(obj_in)
        event_user_new = EventsUser(**obj_in_data)
        event_user_new.id = uuid.uuid4()
        event_user_new.createdAt = datetime.now(timezone.utc)
        event_user_new.updatedAt = datetime.now(timezone.utc)
        event_user_new.createdById = request.user.id
        event_user_new.updatedById = request.user.id
        # Check if user exists
        db_user = CRUDBase(UserModel).get(db=db, id=obj_in.user_id)
        # Check if role exists
        db_role = CRUDBase(RoleModel).get(db=db, id=obj_in.role_id)

        # Moodle: ensure user exists in Moodle (sync, abort on failure)
        event_course = CRUDBase(Course).get(db=db, id=self.db_obj.course)
        if settings.moodle_enabled and event_course.moodleCourseId:
            moodle = moodle_connect(timeout=settings.moodle_sync_timeout)
            if not moodle:
                raise BadRequestError(message="Failed to connect to Moodle")
            try:
                ensure_moodle_user(moodle, db_user)
            except Exception as e:
                raise BadRequestError(
                    message=f"Failed to ensure Moodle user: {e}"
                )
            finally:
                moodle.close()

        event_user_new.user_id = db_user.id
        event_user_new.role_id = db_role.id
        event_user_new.event_id = self.db_obj.id
        try:
            db.add(event_user_new)
            db.commit()
            db.refresh(event_user_new)
        except IntegrityError:
            raise DuplicateEventUserRoleError()
        except:
            raise BadRequestError()

        # Check if Event is Active and deploy VirtualMachines/Guacamole for user if it is
        current_status = CRUDBase(EventStatus).get(db=db, id=self.db_obj.status)
        if current_status.name == "Aktiv":
            # Create Guacamole objects for all other Event VMs if new user is admin
            if db_role.key == "lehrende":
                try:
                    event_vms = (
                        db.query(VirtualMachine)
                        .filter(VirtualMachine.event == self.db_obj.id)
                        .all()
                    )
                    # Pre-fetch teacher IDs for ObjectPermission creation
                    event_teachers_rows = (
                        db.query(UserModel.id)
                        .join(
                            EventsUser,
                            EventsUser.user_id == UserModel.id,
                        )
                        .filter(
                            EventsUser.event_id == self.db_obj.id,
                            EventsUser.role_id == db_role.id,
                        )
                        .all()
                    )
                    event_teachers = [row[0] for row in event_teachers_rows]
                    # Batch-load all GCPs for event VMs
                    ev_vm_ids = [vm.id for vm in event_vms]
                    all_vm_interfaces = (
                        (
                            db.query(GuacamoleConnectionProfile)
                            .filter(
                                GuacamoleConnectionProfile.objectId.in_(
                                    ev_vm_ids
                                ),
                                GuacamoleConnectionProfile.objectType
                                == "VirtualMachine",
                            )
                            .all()
                        )
                        if ev_vm_ids
                        else []
                    )
                    interfaces_by_vm = defaultdict(list)
                    for iface in all_vm_interfaces:
                        interfaces_by_vm[iface.objectId].append(iface)

                    for vm in event_vms:
                        # Creates a Guacamole object (and relevant ObjectPermissions) for user
                        def create_and_enqueue_guacamole(
                            vm: VirtualMachine,
                            interface: GuacamoleConnectionProfile,
                            event: Event,
                            user: UserModel,
                            task_dependencies: list = None,
                        ):
                            def extract_vm_owner_name(vm_name: str) -> str:
                                parts = vm_name.rsplit("-", 1)[
                                    0
                                ]  # remove "-t<id>"
                                return parts.split("-", 1)[1]

                            vm_owner_username = extract_vm_owner_name(vm.name)
                            new_name = str(
                                f"{event.name}-{user.username}-PROV-{vm_owner_username}-{interface.protocol}"
                            )

                            # Create Guacamole for assigned user
                            try:
                                new_guac = Guacamole(
                                    id=uuid.uuid4(),
                                    name=new_name,
                                    guacd_hostname="",
                                    guacd_port=4822,
                                    guacd_encryption=True,
                                    connection_profile=interface.id,
                                    userId=user.id,
                                    eventId=event.id,
                                    createdAt=datetime.now(timezone.utc),
                                    updatedAt=datetime.now(timezone.utc),
                                    createdById=request_user_validation(
                                        db, request
                                    ),
                                    updatedById=request_user_validation(
                                        db, request
                                    ),
                                )
                                db.add(new_guac)
                                vm.guacamoles.append(new_guac)
                                db.add(vm)
                                self._commit(db)
                                db.refresh(vm)
                                db.refresh(new_guac)
                                # Create Task object
                                new_task_schema = TaskCreate(
                                    name=f"Provision Guacamole connection for {user.username}",
                                    event_id=event.id,
                                )
                                new_task = CRUDTask(TaskModel).create(
                                    db=db,
                                    request=request,
                                    obj_in=new_task_schema,
                                )
                                job_provision = CRUDGuacamole(
                                    Guacamole
                                )._subtask_guacamole_provision(
                                    db=db,
                                    request=request,
                                    parent_task_id=new_task.id,
                                    queue=queue_guacamole,
                                    user=user,
                                    connection_profile=interface,
                                    virtual_machine=vm,
                                    db_obj_id=new_guac.id,
                                    task_dependencies=task_dependencies,
                                )
                                # ObjectPermission creation - Guacamole
                                try:
                                    # Create ObjectPermission for object owner
                                    CRUDObjectPermission(
                                        ObjectPermission
                                    ).create_full(
                                        db,
                                        request,
                                        "Guacamole",
                                        new_guac.id,
                                        user.id,
                                    )
                                    # Create ObjectPermission for each teacher in event
                                    for teacher in event_teachers:
                                        # Skip self if object owner is teacher
                                        if user.id == teacher:
                                            continue
                                        try:
                                            CRUDObjectPermission(
                                                ObjectPermission
                                            ).create_full(
                                                db,
                                                request,
                                                "Guacamole",
                                                new_guac.id,
                                                teacher,
                                            )
                                        except Exception as e:
                                            print(
                                                f"UNABLE TO CREATE OBJECT PERMISSION: {e}"
                                            )
                                except Exception as e:
                                    print(e)
                                    ...
                            except Exception as e:
                                print(e)

                        # Get vm interfaces from pre-fetched dict
                        vm_interfaces = interfaces_by_vm.get(vm.id, [])
                        for interface in vm_interfaces:
                            create_and_enqueue_guacamole(
                                vm=vm,
                                interface=interface,
                                event=self.db_obj,
                                user=db_user,
                            )
                except Exception as e:
                    print(e)

            for template in self.db_obj.templates:
                try:
                    new_vm = self._create_vm_for_event_user(
                        db, request, template, db_role, db_user
                    )
                except:
                    # TODO: KVS-418
                    print(
                        f"PLACEHOLDER: Could not create VirtualMachine for user: {db_user.username}"
                    )

        # Moodle: async enrol user if event is active and has moodleCourseId
        if (
            current_status.name == "Aktiv"
            and self.db_obj.moodleCourseId
            and settings.moodle_enabled
        ):
            moodle_enrol_task = CRUDTask(TaskModel).create(
                db=db,
                request=request,
                obj_in=TaskCreate(
                    name=f"Moodle Enrol: {db_user.username}",
                    event_id=self.db_obj.id,
                ),
            )
            moodle_enrol_subtask = CRUDSubTask(SubTaskModel).create(
                db=db,
                request=request,
                obj_in=SubTaskCreate(
                    name=f"Enrol {db_user.username} in Moodle course",
                    object_type="Event",
                    object_id=self.db_obj.id,
                    action="moodle_enrol_user",
                    attempt=0,
                    parent_task=moodle_enrol_task.id,
                ),
            )
            job_moodle_enrol = queue_moodle.enqueue(
                moodle_enrol_user_worker,
                kvs_event_id=self.db_obj.id,
                kvs_user_id=db_user.id,
                kvs_role_key=db_role.key,
                kvs_task_object_id=moodle_enrol_subtask.id,
                retry=Retry(max=5, interval=[10, 30, 60]),
                result_ttl=86400,
                failure_ttl=86400,
            )
            moodle_enrol_subtask.job_id = job_moodle_enrol.id
            db.add(moodle_enrol_subtask)
            db.commit()

        # If current status is "Core Fehler", set status back to "Geplant" after update
        if current_status.name == "Core Fehler":
            event_status_planned = CRUDEventStatus.get_by_name(
                CRUDBase(EventStatus), db=db, name="Geplant"
            )
            self.db_obj.status = event_status_planned.id
            self.db_obj = self._commit(db, self.db_obj)

        return event_user_new

    # Update Course Template
    def add_templates(
        self,
        id: Any,
        db: Session,
        request: Request,
        *,
        obj_in: EventUpdateTemplate,
    ) -> Event:
        # TODO: KVS-417
        self.db_obj = self.get(db, id)
        obj_data = jsonable_encoder(self.db_obj)
        update_data = self._merge_request_with_db_object(obj_in, obj_data)
        # Only allow if Event.status is Geplant
        current_status = CRUDBase(EventStatus).get(db=db, id=self.db_obj.status)
        valid_status_list = ["Geplant", "Core Fehler", "Aktiv"]
        if current_status.name not in valid_status_list:
            raise InvalidStatusError(
                current_status=current_status.name,
                action="event_template_add",
                valid_status_list=valid_status_list,
            )
        # Handling of Course Template
        if "templates" not in update_data:
            raise RequiredParameterMissingError(parameter_name="templates")
        # Handling of Course Templates
        existing_templates = self.db_obj.templates
        template_ids = [t["id"] for t in update_data["templates"]]
        templates_by_id = {
            t.id: t
            for t in db.query(Template)
            .filter(Template.id.in_(template_ids))
            .all()
        }
        # Batch-check GCPs for all templates if guacamole is enabled
        if self.db_obj.guacamole and template_ids:
            gcp_template_ids = {
                row[0]
                for row in db.query(GuacamoleConnectionProfile.objectId)
                .filter(
                    GuacamoleConnectionProfile.objectId.in_(template_ids),
                    GuacamoleConnectionProfile.objectType == "Template",
                )
                .distinct()
                .all()
            }
        new_templates_list = []
        for template in update_data["templates"]:
            new_template = templates_by_id.get(template["id"])
            if not new_template:
                raise ObjectNotFound(
                    model_name=Template.__name__,
                    id=template["id"],
                )
            # Check if assigned template has valid proxmoxId
            if not new_template.proxmoxId:
                raise OperationDependencyMissing(
                    message=_(
                        "Template {template_name} has no proxmoxId"
                    ).format(template_name=new_template.name)
                )
            if self.db_obj.guacamole:
                if new_template.id not in gcp_template_ids:
                    raise OperationDependencyMissing(
                        message=f"Template: {new_template.name} has no assigned GuacamoleConnectionProfiles with which to create Guacamole connections."
                    )
            new_templates_list.append(new_template)
        if current_status.name == "Aktiv":
            # Batch-fetch event users, roles, and user objects before template loop
            event_users = (
                db.query(EventsUser).filter(EventsUser.event_id == id).all()
            )
            eu_user_ids = list({eu.user_id for eu in event_users})
            eu_role_ids = list({eu.role_id for eu in event_users})
            users_by_id = {
                u.id: u
                for u in db.query(UserModel)
                .filter(UserModel.id.in_(eu_user_ids))
                .all()
            }
            roles_by_id = {
                r.id: r
                for r in db.query(RoleModel)
                .filter(RoleModel.id.in_(eu_role_ids))
                .all()
            }
            for template in new_templates_list:
                for event_user in event_users:
                    try:
                        user_role = roles_by_id.get(event_user.role_id)
                        user = users_by_id.get(event_user.user_id)
                        new_vm = self._create_vm_for_event_user(
                            db, request, template, user_role, user
                        )
                    except Exception as e:
                        # TODO: KVS-418
                        continue

        self.db_obj.templates = existing_templates + new_templates_list
        # If current status is "Core Fehler", set status back to "Geplant" after update
        if current_status.name == "Core Fehler":
            event_status_planned = CRUDEventStatus.get_by_name(
                CRUDBase(EventStatus), db=db, name="Geplant"
            )
            self.db_obj.status = event_status_planned.id
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    # Update Event VirtualMachines
    def add_virtual_machines(
        self,
        id: Any,
        db: Session,
        request: Request,
        *,
        obj_in: EventUpdateVirtualMachine,
    ) -> Event:
        self.db_obj = self.get(db, id)
        obj_data = jsonable_encoder(self.db_obj)
        update_data = self._merge_request_with_db_object(obj_in, obj_data)
        # Handling of Course VirtualMachines
        if "vms" not in update_data:
            raise RequiredParameterMissingError(parameter_name="vms")
        # Handling of Course VirtualMachines
        for vm in update_data["vms"]:
            try:
                new_vm = CRUDBase(VirtualMachine).get(db, vm["id"])
                new_vm.event = id
                new_vm.updatedAt = datetime.now(timezone.utc)
                new_vm.updatedById = request.user.id
                db.add(new_vm)
            except:
                raise BadRequestError(
                    message=_(
                        "The VirtualMachine with ID: '{id}' could not be added to event."
                    ).format(id=vm["id"])
                )
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    # Remove VirtualMachines from event
    def delete_virtual_machine(
        self,
        id: Any,
        db: Session,
        request: Request,
        *,
        obj_in: EventUpdateVirtualMachine,
    ) -> Event:
        self.db_obj = self.get(db, id)
        obj_data = jsonable_encoder(self.db_obj)
        update_data = self._merge_request_with_db_object(obj_in, obj_data)
        # Handling of Course VirtualMachines
        if "vms" not in update_data:
            raise RequiredParameterMissingError(parameter_name="vms")
        # Handling of Event VirtualMachines
        existing_vms = db.query(VirtualMachine).filter(
            VirtualMachine.event == self.db_obj.id
        )
        for vm_to_be_removed in update_data["vms"]:
            vm = CRUDBase(VirtualMachine).get(db=db, id=vm_to_be_removed["id"])
            if vm in existing_vms:
                vm.event = None
                vm.updatedAt = datetime.now(timezone.utc)
                vm.updatedById = request.user.id
                db.add(vm)
            else:
                raise BadRequestError(
                    message="VirtualMachine with ID: '{id}' is not associated with this event.".format(
                        id=vm["id"]
                    )
                )
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    # Delete Event/User/Role from EventsUser
    def delete_event_user(
        self,
        db: Session,
        request: Request,
        event_id: Any,
        user_id: Any,
        role_id: Any,
    ) -> EventsUser:
        self.db_obj = self.get(db, event_id)
        # Only allow if Event.status is Geplant
        event_status = CRUDBase(EventStatus)._get(db=db, id=self.db_obj.status)
        event_user_role = (
            db.query(EventsUser)
            .filter(
                EventsUser.user_id == user_id,
                EventsUser.role_id == role_id,
                EventsUser.event_id == event_id,
            )
            .first()
        )
        if not event_user_role:
            raise BadRequestError(
                message=f"User '{user_id}' with Role '{role_id}' does not exist in Event '{event_id}'."
            )
        if event_status.name == "Aktiv":
            # Get User object and all Event VMs belonging to User
            user = CRUDBase(UserModel)._get(db=db, id=user_id)
            user_event_vms = (
                db.query(VirtualMachine)
                .join(VirtualMachine.users)
                .filter(
                    UserModel.id == user.id,
                    VirtualMachine.event == self.db_obj.id,
                )
                .all()
            )
            # Batch-load GCPs and Guacamoles for all user event VMs
            vm_ids = [vm.id for vm in user_event_vms]
            all_gcps = []
            all_guacs = []
            if vm_ids and self.db_obj.guacamole:
                all_gcps = (
                    db.query(GuacamoleConnectionProfile)
                    .filter(
                        GuacamoleConnectionProfile.objectId.in_(vm_ids),
                        GuacamoleConnectionProfile.objectType
                        == "VirtualMachine",
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
            gcps_by_vm = defaultdict(list)
            for gcp in all_gcps:
                gcps_by_vm[gcp.objectId].append(gcp)
            guacs_by_gcp = defaultdict(list)
            for guac in all_guacs:
                guacs_by_gcp[guac.connection_profile].append(guac)

            ids_to_exclude = []
            _proxmox = ProxmoxCluster()

            for vm in user_event_vms:
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
                    except ResourceException:
                        raise ProxmoxRequestError()

                if is_protected:
                    # Delete Event Guacamole connections for this VM before unlinking
                    event_vm_gcp = gcps_by_vm.get(vm.id, [])
                    if self.db_obj.guacamole and event_vm_gcp:
                        new_task_schema = TaskCreate(
                            name=f"Delete Guacamole for Protected VM: {vm.name}",
                            event_id=self.db_obj.id,
                        )
                        new_task = CRUDTask(TaskModel).create(
                            db=db, request=request, obj_in=new_task_schema
                        )
                        for gcp in event_vm_gcp:
                            event_vm_guac_all = guacs_by_gcp.get(gcp.id, [])
                            for event_vm_guac in event_vm_guac_all:
                                ids_to_exclude.append(event_vm_guac.id)
                                CRUDVirtualMachine(
                                    db=db, id=vm.id
                                )._subtask_vm_guac_delete(
                                    db=db,
                                    request=request,
                                    parent_task_id=new_task.id,
                                    queue=queue_guacamole,
                                    guacamole_id=event_vm_guac.id,
                                )
                    try:
                        vm.event = None
                        db.add(vm)
                        db.commit()
                    except:
                        raise ProtectedObjectError(
                            model_name=VirtualMachine.__name__,
                            operation="event_vm_remove",
                        )
                    continue
                # Decommission VirtualMachine
                event_vm_gcp = gcps_by_vm.get(vm.id, [])
                # Create Task object
                new_task_schema = TaskCreate(
                    name=f"Delete Event VirtualMachine: {vm.name}",
                    event_id=self.db_obj.id,
                )
                new_task = CRUDTask(TaskModel).create(
                    db=db, request=request, obj_in=new_task_schema
                )
                # Enqueue Guacamole deletion if Event.guacamole is True
                if self.db_obj.guacamole:
                    for gcp in event_vm_gcp:
                        # Get list of Guacamole objects from pre-fetched dict
                        event_vm_guac_all = guacs_by_gcp.get(gcp.id, [])
                        guacamole_delete_jobs = []
                        for event_vm_guac in event_vm_guac_all:
                            ids_to_exclude.append(event_vm_guac.id)
                            job_guac_delete = CRUDVirtualMachine(
                                db=db, id=vm.id
                            )._subtask_vm_guac_delete(
                                db=db,
                                request=request,
                                parent_task_id=new_task.id,
                                queue=queue_pve_vm_actions,
                                guacamole_id=event_vm_guac.id,
                            )
                            guacamole_delete_jobs.append(job_guac_delete)
                        job_ha_remove = CRUDVirtualMachine(
                            db=db, id=vm.id
                        )._subtask_ha_remove(
                            db=db,
                            request=request,
                            parent_task_id=new_task.id,
                            queue=queue_pve_vm_actions,
                            task_dependencies=guacamole_delete_jobs,
                        )
                else:
                    job_ha_remove = CRUDVirtualMachine(
                        db=db, id=vm.id
                    )._subtask_ha_remove(
                        db=db,
                        request=request,
                        parent_task_id=new_task.id,
                        queue=queue_pve_vm_actions,
                    )

                job_stop = CRUDVirtualMachine(
                    db=db, id=vm.id
                )._subtask_actions_stop(
                    db=db,
                    request=request,
                    parent_task_id=new_task.id,
                    queue=queue_pve_vm_actions,
                    task_dependencies=[job_ha_remove],
                )
                job_delete = CRUDVirtualMachine(
                    db=db, id=vm.id
                )._subtask_vm_delete(
                    db=db,
                    request=request,
                    parent_task_id=new_task.id,
                    queue=queue_pve_vm_clone,
                    task_dependencies=[job_ha_remove, job_stop],
                )
            # Also remove Guacamole objects for other Users' VMs if any exist
            guac_query = (
                db.query(Guacamole)
                .options(selectinload(Guacamole.vms))
                .filter(
                    Guacamole.userId == user.id,
                    Guacamole.eventId == self.db_obj.id,
                )
            )
            if ids_to_exclude:
                guac_query = guac_query.filter(
                    ~Guacamole.id.in_(ids_to_exclude),
                )
            user_event_guac = guac_query.all()
            if user_event_guac:
                new_guac_task_schema = TaskCreate(
                    name=f"Delete Event Guacamoles for: {user.username}",
                    event_id=self.db_obj.id,
                )
                new_guac_task = CRUDTask(TaskModel).create(
                    db=db, request=request, obj_in=new_guac_task_schema
                )
                for event_guac in user_event_guac:
                    vm_id = next((vm.id for vm in event_guac.vms), None)
                    job_guac_delete = CRUDVirtualMachine(
                        db=db, id=vm_id
                    )._subtask_vm_guac_delete(
                        db=db,
                        request=request,
                        parent_task_id=new_guac_task.id,
                        queue=queue_pve_vm_actions,
                        guacamole_id=event_guac.id,
                    )
        # Moodle: unenrol user if event is active and has moodleCourseId
        if (
            event_status.name == "Aktiv"
            and self.db_obj.moodleCourseId
            and settings.moodle_enabled
        ):
            moodle_unenrol_task = CRUDTask(TaskModel).create(
                db=db,
                request=request,
                obj_in=TaskCreate(
                    name=f"Moodle Unenrol: {user.username}",
                    event_id=self.db_obj.id,
                ),
            )
            moodle_unenrol_subtask = CRUDSubTask(SubTaskModel).create(
                db=db,
                request=request,
                obj_in=SubTaskCreate(
                    name=f"Unenrol {user.username} from Moodle course",
                    object_type="Event",
                    object_id=self.db_obj.id,
                    action="moodle_unenrol_user",
                    attempt=0,
                    parent_task=moodle_unenrol_task.id,
                ),
            )
            unenrol_role = CRUDBase(RoleModel)._get(db=db, id=role_id)
            job_moodle_unenrol = queue_moodle.enqueue(
                moodle_unenrol_user_worker,
                kvs_event_id=self.db_obj.id,
                kvs_user_id=user_id,
                kvs_role_key=unenrol_role.key,
                kvs_task_object_id=moodle_unenrol_subtask.id,
                retry=Retry(max=5, interval=[10, 30, 60]),
                result_ttl=86400,
                failure_ttl=86400,
            )
            moodle_unenrol_subtask.job_id = job_moodle_unenrol.id
            db.add(moodle_unenrol_subtask)
            db.commit()

        try:
            db.delete(event_user_role)
            db.query(Changelog).filter(
                Changelog.objectId == event_user_role.id
            ).delete(synchronize_session="fetch")
            db.query(Tag).filter(
                Tag.objectId == event_user_role.id,
                Tag.objectType == "EventsUser",
            ).delete(synchronize_session="fetch")
            self._commit(db)
            return {
                "detail": f"User '{user_id}' with Role '{role_id}' has been removed from event '{event_id}'."
            }
        except IntegrityError:
            raise BadRequestError(
                message=f"Could not remove User '{user_id}' with Role '{role_id}' from event '{event_id}'."
            )

    # Start Event
    def actions_start(
        self, id: Any, db: Session, request: Request = None
    ) -> Event:
        self.db_obj = self.get(db, id)
        # Check if Event may be started based on current Event.status
        event_status_current = CRUDBase(EventStatus).get(db, self.db_obj.status)
        valid_status_list = ["Geplant"]
        if event_status_current.name not in valid_status_list:
            raise InvalidStatusError(
                current_status=event_status_current.name,
                action="event_actions_start",
                valid_status_list=valid_status_list,
            )
        # Get list of users taking part in event
        event_users = (
            db.query(EventsUser).filter(EventsUser.event_id == id).all()
        )
        if not event_users:
            raise OperationDependencyMissing(
                message="Event has no participants"
            )

        # Get lists of different participant types
        role_teacher = (
            db.query(RoleModel).filter(RoleModel.key == "lehrende").first()
        )
        if not role_teacher:
            raise ObjectNotFound(model_name="Role", key="lehrende")
        role_student = (
            db.query(RoleModel).filter(RoleModel.key == "studierende").first()
        )
        if not role_student:
            raise ObjectNotFound(model_name="Role", key="studierende")

        event_users_teachers = (
            db.query(EventsUser)
            .filter(
                EventsUser.event_id == self.db_obj.id,
                EventsUser.role_id == role_teacher.id,
            )
            .count()
        )
        event_users_students = (
            db.query(EventsUser)
            .filter(
                EventsUser.event_id == self.db_obj.id,
                EventsUser.role_id == role_student.id,
            )
            .count()
        )

        # Participant requirement checks
        if event_users_teachers < 1:
            raise OperationDependencyMissing(
                message=_(
                    "Event must have at least 1 teacher before it can be started."
                )
            )
        if settings.events_start_require_students and event_users_students < 1:
            raise OperationDependencyMissing(
                message=_(
                    "Event must have at least 1 student before it can be started."
                )
            )

        # Create associations between Event and Course.templates
        event_course = CRUDBase(Course).get(db, self.db_obj.course)
        course_templates = (
            db.query(Template)
            .join(Template.courses)
            .filter(Course.id == event_course.id)
            .all()
        )
        if not course_templates:
            raise OperationDependencyMissing(
                message=_("Parent Course has no related Templates.")
            )
        new_templates: list = []
        for template in course_templates:
            # Check if template has valid proxmoxId
            if not template.proxmoxId:
                raise OperationDependencyMissing(
                    message=_(
                        "Template {template_name} has no proxmoxId"
                    ).format(template_name=template.name)
                )
            new_templates.append(template)
        try:
            self.db_obj.templates = new_templates
            self.db_obj = self._commit(db, self.db_obj)
        except:
            raise BadRequestError(
                message=_(
                    "Error creating relations between Event and Course templates."
                )
            )

        # Get list of templates for event
        event_templates = self.db_obj.templates
        if not event_templates:
            raise OperationDependencyMissing(
                message=_("Event has no related Templates.")
            )

        # Check if event templates have at least 1 GuacamoleConnectionProfiles assigned to each of them
        if self.db_obj.guacamole:
            for template in event_templates:
                template_gcp = (
                    db.query(GuacamoleConnectionProfile)
                    .filter(GuacamoleConnectionProfile.objectId == template.id)
                    .first()
                )
                if not template_gcp:
                    raise OperationDependencyMissing(
                        message=_(
                            "Template: {template_name} has no assigned GuacamoleConnectionProfiles with which to create Guacamole connections."
                        ).format(template_name=template.name)
                    )

        # Update Event status to "Deploying"
        status_deploying = (
            db.query(EventStatus)
            .filter(EventStatus.name == "Deploying")
            .first()
        )
        if not status_deploying:
            raise ObjectNotFound(model_name="EventStatus", key="Deploying")
        old_status = self.db_obj.status
        old_date = self.db_obj.dateStart
        self.db_obj.status = status_deploying.id
        self.db_obj.dateStart = datetime.now().date()
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        status_changelog = CRUDChangelog(Changelog)._create_for_changes(
            db=db,
            user_id=self.db_obj.updatedById,
            object_type="Event",
            object_id=self.db_obj.id,
            changes=[
                {
                    "field": "status",
                    "value_old": old_status,
                    "value_new": self.db_obj.status,
                },
                {
                    "field": "dateStart",
                    "value_old": old_date,
                    "value_new": self.db_obj.dateStart,
                },
            ],
        )
        # Create Task and SubTask to enqueue VirtualMachine deployment
        parent_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(
                name=_TASK_NAME_LIFECYCLE_START, event_id=self.db_obj.id
            ),
        )
        sub_task_event_start_schema = SubTaskCreate(
            name="Deploy VirtualMachines and Guacamoles for Event",
            object_type="Event",
            object_id=self.db_obj.id,
            action="events_actions_start",
            attempt=0,
            parent_task=parent_task.id,
        )
        sub_task_event_start = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_event_start_schema
        )

        # Moodle: enqueue course deploy before start worker so its
        # job ID can be passed as a post-deployment dependency.
        moodle_job_id = None
        event_course = CRUDBase(Course).get(db, self.db_obj.course)
        if settings.moodle_enabled and event_course.moodleCourseId:
            sub_task_moodle_schema = SubTaskCreate(
                name="Deploy Moodle course for Event",
                object_type="Event",
                object_id=self.db_obj.id,
                action="moodle_deploy_course",
                attempt=0,
                parent_task=parent_task.id,
            )
            sub_task_moodle = CRUDSubTask(SubTaskModel).create(
                db=db, request=request, obj_in=sub_task_moodle_schema
            )
            job_moodle = queue_moodle.enqueue(
                moodle_deploy_course_worker,
                kvs_event_id=self.db_obj.id,
                kvs_task_object_id=sub_task_moodle.id,
                retry=Retry(max=5, interval=[10, 30, 60]),
                result_ttl=86400,
                failure_ttl=86400,
            )
            sub_task_moodle.job_id = job_moodle.id
            moodle_job_id = job_moodle.id
            db.add(sub_task_moodle)
            db.commit()

        job_deploy = queue_pve_vm_actions.enqueue(
            events_start_worker,
            kvs_event_id=self.db_obj.id,
            kvs_task_object_id=sub_task_event_start.id,
            moodle_job_id=moodle_job_id,
            retry=Retry(max=5, interval=[10, 30, 60]),
            result_ttl=86400,
            failure_ttl=86400,
        )
        # Update SubTask with job id
        sub_task_event_start.job_id = job_deploy.id
        db.add(sub_task_event_start)
        db.commit()

        return self.db_obj

    # Stop Event
    def actions_stop(
        self, id: Any, db: Session, request: Request = None
    ) -> Event:
        self.db_obj = self.get(db, id)
        # Check if Event may be stopped based on current Event.status
        event_status_current = CRUDBase(EventStatus).get(db, self.db_obj.status)
        valid_status_list = ["Aktiv", "Archival Fehler"]
        if event_status_current.name not in valid_status_list:
            raise InvalidStatusError(
                current_status=event_status_current.name,
                action="event_actions_stop",
                valid_status_list=valid_status_list,
            )

        # If re-attempting archival after a previous failure, mark all stale
        # Tasks/SubTasks as failed so they don't hang in unprocessed status
        if event_status_current.name == "Archival Fehler":
            stale_tasks = (
                db.query(TaskModel)
                .filter(
                    TaskModel.event_id == self.db_obj.id,
                    TaskModel.status.notin_(["success", "failed"]),
                )
                .all()
            )
            for stale_task in stale_tasks:
                stale_subtasks = (
                    db.query(SubTaskModel)
                    .filter(
                        SubTaskModel.parent_task == stale_task.id,
                        SubTaskModel.status.notin_(["success", "failed"]),
                    )
                    .all()
                )
                for stale_subtask in stale_subtasks:
                    stale_subtask.status = "failed"
                    db.add(stale_subtask)
                stale_task.status = "failed"
                db.add(stale_task)
            db.commit()

        # Set Event.status to "Archiving"
        event_status_archiving = (
            db.query(EventStatus)
            .filter(EventStatus.name == "Archiving")
            .first()
        )
        if not event_status_archiving:
            raise ObjectNotFound(model_name="EventStatus", key="Archiving")
        old_status = self.db_obj.status
        old_date = self.db_obj.dateEnd
        self.db_obj.status = event_status_archiving.id
        self.db_obj.dateEnd = datetime.now().date()
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        status_changelog = CRUDChangelog(Changelog)._create_for_changes(
            db=db,
            user_id=self.db_obj.updatedById,
            object_type="Event",
            object_id=self.db_obj.id,
            changes=[
                {
                    "field": "status",
                    "value_old": old_status,
                    "value_new": self.db_obj.status,
                },
                {
                    "field": "dateEnd",
                    "value_old": old_date,
                    "value_new": self.db_obj.dateEnd,
                },
            ],
        )
        # Create Task and SubTask to enqueue VirtualMachine decommissions
        parent_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(
                name=_TASK_NAME_LIFECYCLE_END, event_id=self.db_obj.id
            ),
        )
        sub_task_event_end_schema = SubTaskCreate(
            name="Delete VirtualMachines and Guacamoles for Event",
            object_type="Event",
            object_id=self.db_obj.id,
            action="events_actions_stop",
            attempt=0,
            parent_task=parent_task.id,
        )
        sub_task_event_end = CRUDSubTask(SubTaskModel).create(
            db=db, request=request, obj_in=sub_task_event_end_schema
        )
        job_deploy = queue_pve_vm_actions.enqueue(
            events_end_worker,
            kvs_event_id=self.db_obj.id,
            kvs_task_object_id=sub_task_event_end.id,
            retry=Retry(max=5, interval=[10, 30, 60]),
            result_ttl=86400,
            failure_ttl=86400,
        )
        # Update SubTask with job id
        sub_task_event_end.job_id = job_deploy.id
        db.add(sub_task_event_end)
        db.commit()

        # Moodle: end event course (expire students, hide course)
        if settings.moodle_enabled and self.db_obj.moodleCourseId:
            sub_task_moodle_end_schema = SubTaskCreate(
                name="End Moodle course for Event",
                object_type="Event",
                object_id=self.db_obj.id,
                action="moodle_end_event",
                attempt=0,
                parent_task=parent_task.id,
            )
            sub_task_moodle_end = CRUDSubTask(SubTaskModel).create(
                db=db, request=request, obj_in=sub_task_moodle_end_schema
            )
            job_moodle_end = queue_moodle.enqueue(
                moodle_end_event_worker,
                kvs_event_id=self.db_obj.id,
                kvs_task_object_id=sub_task_moodle_end.id,
                retry=Retry(max=5, interval=[10, 30, 60]),
                result_ttl=86400,
                failure_ttl=86400,
            )
            sub_task_moodle_end.job_id = job_moodle_end.id
            db.add(sub_task_moodle_end)
            db.commit()

        return self.db_obj

    # Delete Event
    def delete(self, db: Session, id: Any) -> Event:
        self.db_obj = self.get(db, id)
        self._validate_event_status(
            db=db,
            valid_status_list=["Archiviert", "Geplant", "Core Fehler"],
            action="event_delete",
        )
        event_admin = self.get_event_admin(db=db, id=self.db_obj.id)

        # Moodle: delete event course if configured
        if (
            settings.moodle_enabled
            and self.db_obj.moodleCourseId
            and settings.moodle_delete_course_on_event_delete
        ):
            moodle_delete_course(self.db_obj.moodleCourseId)

        # Raise exception if there are still related VirtualMachines
        if (
            db.query(VirtualMachine)
            .filter(VirtualMachine.event == self.db_obj.id)
            .first()
        ):
            raise ObjectInUseError(
                model_name=Event.__name__,
                detail=_(
                    "There are still active VirtualMachines assigned to the Event. Please decommission them before deleting the Event."
                ),
            )

        try:
            event_users = (
                db.query(EventsUser).filter(EventsUser.event_id == id).all()
            )
            event_user_ids = [eu.id for eu in event_users]
            if event_user_ids:
                # Bulk delete Changelogs and Tags for all EventUsers
                db.query(Changelog).filter(
                    Changelog.objectId.in_(event_user_ids)
                ).delete(synchronize_session="fetch")
                db.query(Tag).filter(
                    Tag.objectId.in_(event_user_ids),
                    Tag.objectType == "EventsUser",
                ).delete(synchronize_session="fetch")
                # Delete all EventUsers
                db.query(EventsUser).filter(EventsUser.event_id == id).delete(
                    synchronize_session="fetch"
                )
            tasks = db.query(TaskModel).filter(TaskModel.event_id == id)
            for task in tasks:
                sub_tasks = db.query(SubTaskModel).filter(
                    SubTaskModel.parent_task == task.id
                )
                self._delete_child_list(db=db, obj_list=sub_tasks)
            self._delete_child_list(db=db, obj_list=tasks)
            # Delete all Mails associated with this Event
            event_mails = db.query(Mail).filter(Mail.event == id)
            self._delete_child_list(db=db, obj_list=event_mails)
            db.commit()
            self.db_obj.templates = []
            db.delete(self.db_obj)
            changelogs = db.query(Changelog).filter(
                Changelog.objectId == id, Changelog.object == "Event"
            )
            self._delete_child_list(db=db, obj_list=changelogs)
            object_permissions = db.query(ObjectPermission).filter(
                ObjectPermission.object_id == id,
                ObjectPermission.object_type == "Event",
            )
            self._delete_child_list(db=db, obj_list=object_permissions)
            tags = db.query(Tag).filter(
                Tag.objectId == id, Tag.objectType == "Event"
            )
            self._delete_child_list(db=db, obj_list=tags)
            self._commit(db)
            self._delete_mail(db=db, event_admin=event_admin)
            return {
                "detail": _("Event with ID {id} has been deleted.").format(
                    id=id
                )
            }
        except IntegrityError:
            raise ObjectDeleteIntegrityError(model_name=self.model.__name__)

    # VirtualMachine Bulk actions: start
    def virtual_machines_start(self, db: Session, id: Any, request: Request):
        self.db_obj = self.get(db=db, id=id)
        self._validate_event_status(
            db=db,
            valid_status_list=["Aktiv"],
            action=request.scope.get("route").operation_id,
        )
        event_vms = (
            db.query(VirtualMachine).filter(VirtualMachine.event == id).all()
        )
        event_vm_ids = [vm.id for vm in event_vms]
        vms_id_schema = VirtualMachineIdList(vms=event_vm_ids)
        return CRUDVirtualMachine(VirtualMachine).bulk_start(
            db=db, request=request, obj_in=vms_id_schema, event_id=id
        )

    def virtual_machines_stop(self, db: Session, id: Any, request: Request):
        self.db_obj = self.get(db=db, id=id)
        self._validate_event_status(
            db=db,
            valid_status_list=["Aktiv"],
            action=request.scope.get("route").operation_id,
        )
        event_vms = (
            db.query(VirtualMachine).filter(VirtualMachine.event == id).all()
        )
        event_vm_ids = [vm.id for vm in event_vms]
        vms_id_schema = VirtualMachineIdList(vms=event_vm_ids)
        return CRUDVirtualMachine(VirtualMachine).bulk_stop(
            db=db, request=request, obj_in=vms_id_schema, event_id=id
        )

    def virtual_machines_pause(self, db: Session, id: Any, request: Request):
        self.db_obj = self.get(db=db, id=id)
        self._validate_event_status(
            db=db,
            valid_status_list=["Aktiv"],
            action=request.scope.get("route").operation_id,
        )
        event_vms = (
            db.query(VirtualMachine).filter(VirtualMachine.event == id).all()
        )
        event_vm_ids = [vm.id for vm in event_vms]
        vms_id_schema = VirtualMachineIdList(vms=event_vm_ids)
        return CRUDVirtualMachine(VirtualMachine).bulk_pause(
            db=db, request=request, obj_in=vms_id_schema, event_id=id
        )

    def virtual_machines_reset(self, db: Session, id: Any, request: Request):
        self.db_obj = self.get(db=db, id=id)
        self._validate_event_status(
            db=db,
            valid_status_list=["Aktiv"],
            action=request.scope.get("route").operation_id,
        )
        event_vms = (
            db.query(VirtualMachine).filter(VirtualMachine.event == id).all()
        )
        event_vm_ids = [vm.id for vm in event_vms]
        vms_id_schema = VirtualMachineIdList(vms=event_vm_ids)
        return CRUDVirtualMachine(VirtualMachine).bulk_reset(
            db=db, request=request, obj_in=vms_id_schema, event_id=id
        )

    def virtual_machines_reboot(self, db: Session, id: Any, request: Request):
        self.db_obj = self.get(db=db, id=id)
        self._validate_event_status(
            db=db,
            valid_status_list=["Aktiv"],
            action=request.scope.get("route").operation_id,
        )
        event_vms = (
            db.query(VirtualMachine).filter(VirtualMachine.event == id).all()
        )
        event_vm_ids = [vm.id for vm in event_vms]
        vms_id_schema = VirtualMachineIdList(vms=event_vm_ids)
        return CRUDVirtualMachine(VirtualMachine).bulk_reboot(
            db=db, request=request, obj_in=vms_id_schema, event_id=id
        )

    def virtual_machines_shutdown(self, db: Session, id: Any, request: Request):
        self.db_obj = self.get(db=db, id=id)
        self._validate_event_status(
            db=db,
            valid_status_list=["Aktiv"],
            action=request.scope.get("route").operation_id,
        )
        event_vms = (
            db.query(VirtualMachine).filter(VirtualMachine.event == id).all()
        )
        event_vm_ids = [vm.id for vm in event_vms]
        vms_id_schema = VirtualMachineIdList(vms=event_vm_ids)
        return CRUDVirtualMachine(VirtualMachine).bulk_shutdown(
            db=db, request=request, obj_in=vms_id_schema, event_id=id
        )

    def virtual_machines_resume(self, db: Session, id: Any, request: Request):
        self.db_obj = self.get(db=db, id=id)
        self._validate_event_status(
            db=db,
            valid_status_list=["Aktiv"],
            action=request.scope.get("route").operation_id,
        )
        event_vms = (
            db.query(VirtualMachine).filter(VirtualMachine.event == id).all()
        )
        event_vm_ids = [vm.id for vm in event_vms]
        vms_id_schema = VirtualMachineIdList(vms=event_vm_ids)
        return CRUDVirtualMachine(VirtualMachine).bulk_resume(
            db=db, request=request, obj_in=vms_id_schema, event_id=id
        )

    def virtual_machines_hibernate(
        self, db: Session, id: Any, request: Request
    ):
        self.db_obj = self.get(db=db, id=id)
        self._validate_event_status(
            db=db,
            valid_status_list=["Aktiv"],
            action=request.scope.get("route").operation_id,
        )
        event_vms = (
            db.query(VirtualMachine).filter(VirtualMachine.event == id).all()
        )
        event_vm_ids = [vm.id for vm in event_vms]
        vms_id_schema = VirtualMachineIdList(vms=event_vm_ids)
        return CRUDVirtualMachine(VirtualMachine).bulk_hibernate(
            db=db, request=request, obj_in=vms_id_schema, event_id=id
        )

    def virtual_machines_migrate(
        self, db: Session, id: Any, request: Request, target_node: str
    ):
        self.db_obj = self.get(db=db, id=id)
        self._validate_event_status(
            db=db,
            valid_status_list=["Aktiv"],
            action=request.scope.get("route").operation_id,
        )
        event_vms = (
            db.query(VirtualMachine).filter(VirtualMachine.event == id).all()
        )
        event_vm_ids = [vm.id for vm in event_vms]
        vms_id_schema = VirtualMachineIdList(vms=event_vm_ids)
        return CRUDVirtualMachine(VirtualMachine).bulk_migrate(
            db=db,
            request=request,
            obj_in=vms_id_schema,
            target_node=target_node,
            event_id=id,
        )

    def virtual_machines_ha_add(
        self,
        db: Session,
        id: Any,
        request: Request,
        obj_in: EventVirtualMachinesHaAdd,
    ):
        self.db_obj = self.get(db=db, id=id)
        self._validate_event_status(
            db=db,
            valid_status_list=["Aktiv"],
            action=request.scope.get("route").operation_id,
        )
        event_vms = (
            db.query(VirtualMachine).filter(VirtualMachine.event == id).all()
        )
        event_vm_ids = [vm.id for vm in event_vms]
        vms_ha_add_schema = VirtualMachineBulkHaAdd(
            vms=event_vm_ids,
            ha_state=obj_in.ha_state,
            ha_max_restart=obj_in.ha_max_restart,
            ha_max_relocate=obj_in.ha_max_relocate,
        )
        return CRUDVirtualMachine(VirtualMachine).bulk_ha_add(
            db=db, request=request, obj_in=vms_ha_add_schema, event_id=id
        )

    def virtual_machines_ha_remove(
        self, db: Session, id: Any, request: Request
    ):
        self.db_obj = self.get(db=db, id=id)
        self._validate_event_status(
            db=db,
            valid_status_list=["Aktiv"],
            action=request.scope.get("route").operation_id,
        )
        event_vms = (
            db.query(VirtualMachine).filter(VirtualMachine.event == id).all()
        )
        event_vm_ids = [vm.id for vm in event_vms]
        vms_id_schema = VirtualMachineIdList(vms=event_vm_ids)
        return CRUDVirtualMachine(VirtualMachine).bulk_ha_remove(
            db=db, request=request, obj_in=vms_id_schema, event_id=id
        )

    def guacamoles_delete(self, db: Session, id: Any, request: Request):
        self.db_obj = self.get(db=db, id=id)
        self._validate_event_status(
            db=db,
            valid_status_list=["Aktiv"],
            action=request.scope.get("route").operation_id,
        )
        event_guac = db.query(Guacamole).filter(Guacamole.eventId == id).all()
        if not event_guac:
            raise BulkActionRequirementMissing(
                message="No Guacamoles are assigned to this event"
            )
        parent_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(
                name=f"Delete all Guacamoles connections for {self.db_obj.slug}",
                event_id=self.db_obj.id,
            ),
        )
        enqueued = 0
        for guac in event_guac:
            job_guac_delete = CRUDGuacamole(
                db=db, id=guac.id
            )._subtask_guacamole_delete(
                db=db,
                request=request,
                parent_task_id=parent_task.id,
                queue=queue_guacamole,
            )
            enqueued += 1
        if enqueued == 0:
            try:
                self._delete_empty_parents(db=db, parent_task_id=parent_task.id)
                raise BadRequestError(
                    message="Guacamoles connections assigned to this event could not be deleted"
                )
            except Exception as e:
                raise BadRequestError(
                    message=f"Failed to delete empty parent task: {parent_task.id}"
                )

        return {"task_id": parent_task.id, "enqueued": enqueued}

    def guacamoles_create(self, db: Session, id: Any, request: Request):
        self.db_obj = self.get(db=db, id=id)
        self._validate_event_status(
            db=db,
            valid_status_list=["Aktiv"],
            action=request.scope.get("route").operation_id,
        )
        parent_task = CRUDTask(TaskModel).create(
            db=db,
            request=request,
            obj_in=TaskCreate(
                name=f"Provision Guacamoles connections for {self.db_obj.slug}",
                event_id=id,
            ),
        )
        enqueued = 0
        event_vms = (
            db.query(VirtualMachine)
            .options(selectinload(VirtualMachine.users))
            .filter(VirtualMachine.event == id)
            .all()
        )
        # Batch-load event admin (teachers) and their User objects once
        event_admin = self.get_event_admin(db=db, id=id)
        teacher_user_ids = [t.user_id for t in event_admin]
        teachers_by_id = (
            {
                u.id: u
                for u in db.query(UserModel)
                .filter(UserModel.id.in_(teacher_user_ids))
                .all()
            }
            if teacher_user_ids
            else {}
        )
        # Batch-load all connection profiles for event VMs
        event_vm_ids = [vm.id for vm in event_vms]
        all_conn_profiles = (
            (
                db.query(GuacamoleConnectionProfile)
                .filter(
                    GuacamoleConnectionProfile.objectId.in_(event_vm_ids),
                    GuacamoleConnectionProfile.objectType == "VirtualMachine",
                )
                .all()
            )
            if event_vm_ids
            else []
        )
        conn_profiles_by_vm = defaultdict(list)
        for cp in all_conn_profiles:
            conn_profiles_by_vm[cp.objectId].append(cp)
        for vm in event_vms:
            connection_profiles = conn_profiles_by_vm.get(vm.id, [])
            for connection_profile in connection_profiles:
                new_guac = CRUDVirtualMachine(
                    db=db, id=vm.id
                )._create_and_enqueue_guacamole_event(
                    db=db,
                    request=request,
                    interface=connection_profile,
                    event=self.db_obj,
                    user=vm.users[0],
                    parent_task=parent_task.id,
                )
                if new_guac["created"]:
                    enqueued += 1
                for teacher_eu in event_admin:
                    # Skip self if object owner is teacher
                    if vm.users[0].id == teacher_eu.user_id:
                        continue
                    user = teachers_by_id.get(teacher_eu.user_id)
                    if not user:
                        continue
                    new_guac = CRUDVirtualMachine(
                        db=db, id=vm.id
                    )._create_and_enqueue_guacamole_event(
                        db=db,
                        request=request,
                        interface=connection_profile,
                        event=self.db_obj,
                        user=user,
                        is_teacher=True,
                        student_username=vm.users[0].username,
                        parent_task=parent_task.id,
                    )
                    if new_guac["created"]:
                        enqueued += 1

        if enqueued == 0:
            self._delete_empty_parents(db=db, parent_task_id=parent_task.id)
            raise BulkActionRequirementMissing(
                message="All Guacamole connections already exist"
            )

        return {"task_id": parent_task.id, "enqueued": enqueued}

    def _validate_event_status(
        self, db: Session, valid_status_list: list, action: str
    ):
        event_status_current = CRUDBase(EventStatus).get(db, self.db_obj.status)
        if event_status_current.name not in valid_status_list:
            raise InvalidStatusError(
                current_status=event_status_current.name,
                action=action,
                valid_status_list=valid_status_list,
            )

    def _delete_empty_parents(self, db: Session, parent_task_id: UUID4):
        try:
            parent_task = db.get(TaskModel, parent_task_id)
            db.delete(parent_task)
            db.commit()
        except Exception as e:
            db.rollback()
            raise BadRequestError(
                message=f"Failed to delete empty parent task {parent_task_id}: {e}"
            )


event = CRUDEvent(Event)
