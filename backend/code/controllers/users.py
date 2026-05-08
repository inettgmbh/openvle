import base64
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from core.auth import get_password_hash, verify_password
from core.config import Settings
from core.core_utils import get_system_user
from core.exceptions import (
    BadRequestError,
    GuacamoleConnectionError,
    InvalidFieldValue,
    ObjectDeleteIntegrityError,
    ObjectNotFound,
    ProtectedObjectError,
    RequiredParameterMissingError,
)
from core.guacamole import guacamole_connect
from core.messages import (
    msg_cannot_update_external_user_pass,
    msg_passwords_do_not_match,
)
from core.pagination import paginate
from core.redis import queue_pve_vm_actions, queue_pve_vm_clone
from middlewares.i18n import _
from models import (
    Changelog,
    Event,
    EventStatus,
    EventsUser,
    Guacamole,
    GuacamoleConnectionProfile,
    Mail,
    ObjectPermission,
    PoliciesUser,
    Role,
    Tag,
    Task,
    User,
    VirtualMachine,
)
from schemas.events import UserInEventList
from schemas.tasks import TaskCreate
from schemas.users import (
    TruncatedList,
    UserCreate,
    UserDeletePreview,
    UserDeletePreviewChangelog,
    UserDeletePreviewConnection,
    UserDeletePreviewEventMembership,
    UserDeletePreviewEventMembershipRole,
    UserDeletePreviewMail,
    UserDeletePreviewObjectPermission,
    UserDeletePreviewStats,
    UserDeletePreviewTag,
    UserDeletePreviewVirtualMachine,
    UserSetPassword,
    UserUpdate,
    UserUpdatePassword,
    UserUpdateRoles,
)

from .base import CRUDBase
from .tasks import CRUDTask
from .virtual_machines import CRUDVirtualMachine

settings = Settings()


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    # Get user by username
    def get_by_username(self, db: Session, *, username: str) -> User | None:
        user = db.query(User).filter(User.username == username).first()
        return user

    # Get user by e-mail
    def get_by_email(self, db: Session, *, email: str) -> User | None:
        user = db.query(User).filter(User.email == email).first()
        return user

    # Get list of effective permissions assigned to user (Permissions and ObjectPermissions)
    def get_effective_permissions_new(self, db: Session, id: Any):
        # Mapping of ObjectPermission object_type to normalized permission type
        OBJECT_TYPE_TO_PERM_TYPE = {
            "Activity": "activities",
            "Application": "applications",
            "Changelog": "changelogs",
            "Course": "courses",
            "Document": "documents",
            "Dashboard": "dashboards",
            "Event": "events",
            "Guacamole": "guacamoles",
            "GuacamoleConnectionProfile": "guacamole_connection_profiles",
            "MailTemplate": "mail_templates",
            "Mail": "mails",
            "ObjectPermission": "object_permissions",
            "OS": "os",
            "Policy": "policies",
            "Role": "roles",
            "SubTask": "sub_tasks",
            "SystemSetting": "system_settings",
            "Tag": "tags",
            "Task": "tasks",
            "Template": "templates",
            "User": "users",
            "Vendor": "vendors",
            "VirtualMachine": "vms",
        }

        obj = (
            db.query(User)
            .options(
                selectinload(User.roles),
            )
            .filter(User.id == id)
            .first()
        )
        if not obj:
            raise ObjectNotFound(model_name=User.__name__, id=id)

        # Final normalized permission map:
        # type_dict[type][object_id or None] = [permissions...]
        type_dict: dict[str, dict[str | None, list[str]]] = {}

        def add_obj_perm(op: ObjectPermission):
            # Use mapping to convert object_type to normalized permission type
            # Falls back to lowercase if not in mapping
            type_ = OBJECT_TYPE_TO_PERM_TYPE.get(
                op.object_type, op.object_type.lower()
            )

            if type_ not in type_dict:
                type_dict[type_] = {}

            object_id = str(op.object_id) if op.object_id else None

            # Extract permission from permission_key
            if op.permission_key.startswith("object_"):
                permission = op.permission_key[7:]  # Remove "object_" prefix
            else:
                permission = op.permission_key

            if object_id not in type_dict[type_]:
                type_dict[type_][object_id] = []

            if permission not in type_dict[type_][object_id]:
                type_dict[type_][object_id].append(permission)

        # Get user's role IDs
        user_role_ids = [role.id for role in obj.roles]

        # ObjectPermissions directly assigned to user (entity_type="User", entity_id=user_id)
        for op in db.query(ObjectPermission).filter(
            ObjectPermission.entity_type == "User",
            ObjectPermission.entity_id == id,
        ):
            add_obj_perm(op)

        # ObjectPermissions inherited from roles (entity_type="Role", entity_id in user's roles)
        if user_role_ids:
            for op in db.query(ObjectPermission).filter(
                ObjectPermission.entity_type == "Role",
                ObjectPermission.entity_id.in_(user_role_ids),
            ):
                add_obj_perm(op)

        # Build final result
        results = []
        for type_, id_map in type_dict.items():
            for object_id, perms in id_map.items():
                results.append(
                    {
                        "type": type_,
                        "path": "/" + object_id if object_id else "/",
                        "permissions": perms,
                    }
                )

        return results

    # Get multiple (all) objects with limit of 100
    def get_multi(
        self,
        db: Session,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
        search_field: str = "",
        search_value: str = "",
    ) -> list[User] | None:
        self._get_multi_init(limit=limit, page=page, sort_by=sort_by)
        system_user = get_system_user(db)
        # Build query
        model_query = db.query(User)
        model_query = self._model_query_search(
            model_query, search_field=search_field, search_value=search_value
        )
        # Remove system user from model_query
        model_query = model_query.filter(User.id != system_user.id)
        model_query = model_query.filter(~User.username.contains("deleted_"))
        model_query_sorted = self._model_query_sort(
            model_query, sort_by=sort_by, sort_order=sort_order, limit=limit
        )
        model_query_count = model_query.count()
        # return Paginated list of objects
        return paginate(
            object_list=list(model_query_sorted),
            object_query_count=model_query_count,
            current_page=page,
            limit=limit,
        )

    # Create user
    def create(
        self, db: Session, request: Request, *, obj_in: UserCreate
    ) -> User:
        USER_PASSWORD = None
        # Check if a password was provided in request body
        if obj_in.password and obj_in.password_repeat:
            if obj_in.password != obj_in.password_repeat:
                raise BadRequestError(message=_(msg_passwords_do_not_match))
            USER_PASSWORD = get_password_hash(obj_in.password)
        # TODO: Add check for empty password and not empty password_repeat
        elif obj_in.password and not obj_in.password_repeat:
            raise BadRequestError(message=_("Please repeat your password."))
        create_data = obj_in.model_dump()
        create_data.pop("password", None)
        create_data.pop("password_repeat", None)
        # Create User object
        self.db_obj = User(**create_data)
        self.db_obj.id = uuid.uuid4()
        if USER_PASSWORD:
            self.db_obj.hashed_password = USER_PASSWORD
        self.db_obj.createdAt = datetime.now(timezone.utc)
        self.db_obj.updatedAt = datetime.now(timezone.utc)
        self.db_obj.createdById = request.user.id
        self.db_obj.updatedById = request.user.id
        # If user status is 'E-Mail-Pending' we set mailValidateToken, and mail it to the user to verify its e-mail address
        if self.db_obj.status == "E-Mail-Pending":
            self.db_obj.mailValidateToken = uuid.uuid4()
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    # Set User Roles
    def set_roles(
        self, id: Any, db: Session, request: Request, *, obj_in: UserUpdateRoles
    ) -> User:
        self.db_obj = self.get(db, id)
        if self.db_obj.username == "system":
            raise ProtectedObjectError(
                model_name="System user", operation="user_update"
            )
        elif "deleted_" in self.db_obj.username:
            raise ProtectedObjectError(
                model_name="Deleted user", operation="user_delete"
            )
        obj_data = jsonable_encoder(self.db_obj)
        update_data = self._merge_request_with_db_object(obj_in, obj_data)
        # Handling of roles
        if "roles" not in update_data:
            raise RequiredParameterMissingError(parameter_name="roles")
        role_keys = [role["key"] for role in update_data["roles"]]
        roles_by_key = {
            r.key: r
            for r in db.query(Role).filter(Role.key.in_(role_keys)).all()
        }
        roles_list = []
        for role in update_data["roles"]:
            new_role = roles_by_key.get(role["key"])
            if not new_role:
                raise ObjectNotFound(model_name=Role.__name__, key=role["key"])
            roles_list.append(new_role)
        self.db_obj.roles = roles_list
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    # Update User Roles
    def update_roles(
        self, id: Any, db: Session, request: Request, *, obj_in: UserUpdateRoles
    ) -> User:
        self.db_obj = self.get(db, id)
        if self.db_obj.username == "system":
            raise ProtectedObjectError(
                model_name="System user", operation="user_update"
            )
        elif "deleted_" in self.db_obj.username:
            raise ProtectedObjectError(
                model_name="Deleted user", operation="user_delete"
            )
        obj_data = jsonable_encoder(self.db_obj)
        update_data = self._merge_request_with_db_object(obj_in, obj_data)
        # Handling of roles
        if "roles" not in update_data:
            raise RequiredParameterMissingError(parameter_name="roles")
        existing_roles = self.db_obj.roles
        role_keys = [role["key"] for role in update_data["roles"]]
        roles_by_key = {
            r.key: r
            for r in db.query(Role).filter(Role.key.in_(role_keys)).all()
        }
        roles_list = []
        for role in update_data["roles"]:
            new_role = roles_by_key.get(role["key"])
            if not new_role:
                raise ObjectNotFound(model_name=Role.__name__, key=role["key"])
            roles_list.append(new_role)
        self.db_obj.roles = existing_roles + roles_list
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    # Update (own) user password
    def update_password(
        self, db: Session, request: Request, *, obj_in: UserUpdatePassword
    ) -> User:
        self.db_obj = self.get(db, request.user.id)
        if self.db_obj.username == "system":
            raise ProtectedObjectError(
                model_name="System user", operation="user_update"
            )
        elif "deleted_" in self.db_obj.username:
            raise ProtectedObjectError(
                model_name="Deleted user", operation="user_delete"
            )
        obj_data = obj_in.model_dump()
        # Check if user's password is empty which signifies that the account is an external account
        if not self.db_obj.hashed_password:
            raise BadRequestError(
                message=_(msg_cannot_update_external_user_pass)
            )
        # Verify that password_old is the correct password
        if not verify_password(
            obj_data["password_old"], self.db_obj.hashed_password
        ):
            raise BadRequestError(
                message=_(
                    "The password you have entered is incorrect. Please try again."
                )
            )
        # Verify that password_new and password_new_repeat are the same
        if obj_data["password_new"] != obj_data["password_new_repeat"]:
            raise BadRequestError(message=_(msg_passwords_do_not_match))
        # Verify that password_new and password_old are NOT the same
        if obj_data["password_new"] == obj_data["password_old"]:
            raise BadRequestError(
                message=_(
                    "Your new password cannot be the same as your old password."
                )
            )
        self.db_obj.hashed_password = get_password_hash(
            obj_data["password_new"]
        )
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    # Set user password
    def set_password(
        self,
        db: Session,
        request: Request,
        *,
        obj_in: UserSetPassword,
        user_id: Any,
    ) -> User:
        obj_data = obj_in.model_dump()
        self.db_obj = self.get(db, user_id)
        if not self.db_obj:
            raise ObjectNotFound(id=user_id, model_name=self.model.__name__)
        if self.db_obj.username == "system":
            raise ProtectedObjectError(
                model_name="System user", operation="user_update"
            )
        elif "deleted_" in self.db_obj.username:
            raise ProtectedObjectError(
                model_name="Deleted user", operation="user_delete"
            )
        # Check if user's password is empty which signifies that the account is an external account
        if not self.db_obj.hashed_password:
            raise BadRequestError(
                message=_(msg_cannot_update_external_user_pass)
            )
        # Verify that password_new and password_new_repeat are the same
        if obj_data["password_new"] != obj_data["password_new_repeat"]:
            raise BadRequestError(message=_(msg_passwords_do_not_match))
        self.db_obj.hashed_password = get_password_hash(
            obj_data["password_new"]
        )
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    # Update User
    def update(
        self, id: Any, db: Session, request: Request, *, obj_in: UserUpdate
    ) -> User:
        self.db_obj = self.get(db, id)
        if self.db_obj.username == "system":
            raise ProtectedObjectError(
                model_name="System user", operation="user_update"
            )
        elif "deleted_" in self.db_obj.username:
            raise ProtectedObjectError(
                model_name="Deleted user", operation="user_delete"
            )
        old_status = self.db_obj.status
        obj_data = jsonable_encoder(self.db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        # Check if User
        if not self.db_obj.hashed_password:
            for field in ["name", "email"]:
                if field in update_data and update_data[field] != getattr(
                    self.db_obj, field
                ):
                    raise BadRequestError(
                        message=_(
                            "External Users may not update their {field}."
                        ).format(field=field)
                    )
        for field in obj_data:
            if field in update_data:
                setattr(self.db_obj, field, update_data[field])
        # If user was un-/banned, un-/lock user on Guacamole
        if old_status != self.db_obj.status:
            guacamole = guacamole_connect()
            if not guacamole:
                raise GuacamoleConnectionError()
            # User was banned
            if old_status != "Banned" and self.db_obj.status == "Banned":
                response = guacamole.detail_user(self.db_obj.username)
                if (
                    "username" in response
                    and response["username"] == self.db_obj.username
                ):
                    user_lock = guacamole.lock_user(self.db_obj.username)
            # User was unbanned
            if old_status == "Banned":
                response = guacamole.detail_user(self.db_obj.username)
                if (
                    "username" in response
                    and response["username"] == self.db_obj.username
                ):
                    user_unlock = guacamole.unlock_user(self.db_obj.username)
        self._update_meta(request)
        self.db_obj = self._commit(db, self.db_obj)
        return self.db_obj

    def _get_owned_vm_guac(self, db: Session):
        user_created_vms = (
            db.query(VirtualMachine)
            .options(selectinload(VirtualMachine.guacamoles))
            .filter(VirtualMachine.createdById == self.db_obj.id)
            .all()
        )
        all_vms = user_created_vms + self.db_obj.vms
        user_vms = list({vm.id: vm for vm in all_vms}.values())

        vm_guacs = []
        for vm in user_vms:
            for guac in getattr(vm, "guacamoles", []):
                if guac.userId == self.db_obj.id:
                    vm_guacs.append(guac)
        vm_guacs = list({guac.id: guac for guac in vm_guacs}.values())

        vm_guac_ids = {guac.id for guac in vm_guacs}
        user_created_guac = (
            db.query(Guacamole)
            .filter(
                Guacamole.createdById == self.db_obj.id,
                ~Guacamole.id.in_(vm_guac_ids),
            )
            .all()
        )

        all_guacs = vm_guacs + user_created_guac
        user_guacs = list({guac.id: guac for guac in all_guacs}.values())

        return {
            "user_vms_all": user_vms,
            "user_guacamoles_all": user_guacs,
            "user_created_guac": user_created_guac,
        }

    def delete_preview(self, db: Session, id: Any) -> UserDeletePreview:
        self.db_obj = self.get(db, id)
        owned = self._get_owned_vm_guac(db)
        vms = owned["user_vms_all"]
        connections = owned["user_guacamoles_all"]

        LIMIT = 100

        mails_q = db.query(Mail).filter(Mail.user_id == id)
        mails_count = mails_q.count()
        mails_items = mails_q.limit(LIMIT).all()

        changelogs_q = db.query(Changelog).filter(
            Changelog.objectId == id, Changelog.object == "User"
        )
        changelogs_count = changelogs_q.count()
        changelogs_items = changelogs_q.limit(LIMIT).all()

        object_permissions_q = db.query(ObjectPermission).filter(
            or_(
                (ObjectPermission.entity_id == id)
                & (ObjectPermission.entity_type == "User"),
                (ObjectPermission.object_id == id)
                & (ObjectPermission.object_type == "User"),
            )
        )
        object_permissions_count = object_permissions_q.count()
        object_permissions_items = object_permissions_q.limit(LIMIT).all()

        tags_q = db.query(Tag).filter(
            Tag.objectId == id, Tag.objectType == "User"
        )
        tags_count = tags_q.count()
        tags_items = tags_q.limit(LIMIT).all()

        # Count via simple query on EventsUser; the join is only needed for the items.
        event_memberships_count = (
            db.query(EventsUser).filter(EventsUser.user_id == id).count()
        )
        event_memberships_items = (
            db.query(EventsUser, Event, EventStatus, Role)
            .join(Event, Event.id == EventsUser.event_id)
            .join(EventStatus, EventStatus.id == Event.status)
            .join(Role, Role.id == EventsUser.role_id)
            .filter(EventsUser.user_id == id)
            .limit(LIMIT)
            .all()
        )

        policy_memberships_count = (
            db.query(PoliciesUser).filter(PoliciesUser.user_id == id).count()
        )

        stats = UserDeletePreviewStats(
            virtual_machines=len(vms),
            connections=len(connections),
            mails=mails_count,
            changelogs=changelogs_count,
            object_permissions=object_permissions_count,
            event_memberships=event_memberships_count,
            policy_memberships=policy_memberships_count,
            tags=tags_count,
        )

        return UserDeletePreview(
            stats=stats,
            virtual_machines=TruncatedList[UserDeletePreviewVirtualMachine](
                items=[
                    UserDeletePreviewVirtualMachine.model_validate(vm)
                    for vm in vms[:LIMIT]
                ],
                truncated=len(vms) > LIMIT,
            ),
            connections=TruncatedList[UserDeletePreviewConnection](
                items=[
                    UserDeletePreviewConnection.model_validate(c)
                    for c in connections[:LIMIT]
                ],
                truncated=len(connections) > LIMIT,
            ),
            mails=TruncatedList[UserDeletePreviewMail](
                items=[
                    UserDeletePreviewMail.model_validate(m) for m in mails_items
                ],
                truncated=mails_count > LIMIT,
            ),
            changelogs=TruncatedList[UserDeletePreviewChangelog](
                items=[
                    UserDeletePreviewChangelog.model_validate(c)
                    for c in changelogs_items
                ],
                truncated=changelogs_count > LIMIT,
            ),
            object_permissions=TruncatedList[UserDeletePreviewObjectPermission](
                items=[
                    UserDeletePreviewObjectPermission.model_validate(p)
                    for p in object_permissions_items
                ],
                truncated=object_permissions_count > LIMIT,
            ),
            tags=TruncatedList[UserDeletePreviewTag](
                items=[
                    UserDeletePreviewTag.model_validate(t) for t in tags_items
                ],
                truncated=tags_count > LIMIT,
            ),
            event_memberships=TruncatedList[UserDeletePreviewEventMembership](
                items=[
                    UserDeletePreviewEventMembership(
                        id=event.id,
                        name=event.name,
                        status=status.name,
                        role=UserDeletePreviewEventMembershipRole(
                            id=role.id,
                            name=role.name,
                        ),
                    )
                    for _, event, status, role in event_memberships_items
                ],
                truncated=event_memberships_count > LIMIT,
            ),
        )

    # Delete User
    def delete(self, db: Session, id: Any) -> User | None:
        self.db_obj = self.get(db, id)
        if self.db_obj.username == "system":
            raise ProtectedObjectError(
                model_name="System user", operation="user_delete"
            )
        elif "deleted_" in self.db_obj.username:
            raise ProtectedObjectError(
                model_name="Deleted user", operation="user_delete"
            )
        # Delete all VirtualMachines and their related objects
        owned_vms_guacs = self._get_owned_vm_guac(db)
        user_vms = owned_vms_guacs["user_vms_all"]

        # Batch-load all GCPs and Guacamoles for user's VMs
        vm_ids = [vm.id for vm in user_vms]
        all_gcps = []
        all_guacs = []
        if vm_ids:
            all_gcps = (
                db.query(GuacamoleConnectionProfile)
                .filter(
                    GuacamoleConnectionProfile.objectId.in_(vm_ids),
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
        gcps_by_vm = defaultdict(list)
        for gcp in all_gcps:
            gcps_by_vm[gcp.objectId].append(gcp)
        guacs_by_gcp = defaultdict(list)
        for guac in all_guacs:
            guacs_by_gcp[guac.connection_profile].append(guac)

        for vm in user_vms:
            new_task = CRUDTask(Task).create(
                db=db,
                request=None,
                obj_in=TaskCreate(
                    name="Delete VirtualMachine for deleted user"
                ),
            )

            crud_vm = CRUDVirtualMachine(db=db, id=vm.id)

            # If guacamole, enqueue guac deletions first
            guac_deps = []
            gcps = gcps_by_vm.get(vm.id, [])

            for gcp in gcps:
                guacs = guacs_by_gcp.get(gcp.id, [])
                for guac in guacs:
                    job = crud_vm._subtask_vm_guac_delete(
                        db=db,
                        request=None,
                        parent_task_id=new_task.id,
                        queue=queue_pve_vm_actions,
                        guacamole_id=guac.id,
                        guacamole_identifier=guac.identifier,
                    )
                    if job is not None:
                        guac_deps.append(job)

            job_ha_remove = crud_vm._subtask_ha_remove(
                db=db,
                request=None,
                parent_task_id=new_task.id,
                queue=queue_pve_vm_actions,
                task_dependencies=guac_deps if guac_deps else None,
            )

            # Stop VM (depends on HA remove)
            job_stop = crud_vm._subtask_actions_stop(
                db=db,
                request=None,
                parent_task_id=new_task.id,
                queue=queue_pve_vm_actions,
                task_dependencies=[job_ha_remove] if job_ha_remove else None,
            )

            # Delete VM (depends on HA remove + stop)
            deps = [j for j in [job_ha_remove, job_stop] if j is not None]
            job_delete = crud_vm._subtask_vm_delete(
                db=db,
                request=None,
                parent_task_id=new_task.id,
                queue=queue_pve_vm_clone,
                task_dependencies=deps if deps else None,
            )
        for guac in owned_vms_guacs["user_created_guac"]:
            job = CRUDVirtualMachine(db=db, id=vm.id)._subtask_vm_guac_delete(
                db=db,
                request=None,
                parent_task_id=new_task.id,
                queue=queue_pve_vm_actions,
                guacamole_id=guac.id,
                guacamole_identifier=guac.identifier,
            )
        # Randomise name, username and email
        new_name = (
            base64.b32encode(self.db_obj.id.bytes)
            .decode("utf-8")
            .rstrip("=")
            .lower()[:8]
        )
        self.db_obj.name = new_name
        self.db_obj.username = f"deleted_{new_name}"
        self.db_obj.email = f"{new_name}@mail.mail"
        self.db_obj.hashed_password = None
        self.db_obj.status = "deleted"
        try:
            db.query(Changelog).filter(
                Changelog.objectId == id,
                Changelog.object == self.model.__name__,
            ).delete(synchronize_session="fetch")
            # Delete ObjectPermissions where User is the entity (entity_type="User", entity_id=user_id)
            db.query(ObjectPermission).filter(
                ObjectPermission.entity_id == id,
                ObjectPermission.entity_type == "User",
            ).delete(synchronize_session="fetch")
            # Delete ObjectPermissions where User is the object (object_type="User", object_id=user_id)
            db.query(ObjectPermission).filter(
                ObjectPermission.object_id == id,
                ObjectPermission.object_type == "User",
            ).delete(synchronize_session="fetch")
            db.query(EventsUser).filter(
                EventsUser.user_id == id,
            ).delete(synchronize_session="fetch")
            db.query(PoliciesUser).filter(
                PoliciesUser.user_id == id,
            ).delete(synchronize_session="fetch")
            db.query(Tag).filter(
                Tag.objectId == id,
                Tag.objectType == self.model.__name__,
            ).delete(synchronize_session="fetch")
            db.query(Mail).filter(
                Mail.user_id == id,
            ).delete(synchronize_session="fetch")
            self._commit(db)
            return {
                "detail": _("{model} with ID {id} has been deleted.").format(
                    model=self.model.__name__, id=id
                )
            }
        except IntegrityError:
            raise ObjectDeleteIntegrityError(model_name=User.__name__)

    # Get all Event objects associated with an EventUser via User.id
    def get_user_events(
        self,
        db: Session,
        id: Any,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
        search_field: str = "",
        search_value: str = "",
    ) -> UserInEventList | None:
        self._get_multi_init(
            limit=limit, page=page, sort_by=sort_by, parent_model=Event
        )

        # Build and sort query based on provided parameters
        model_query = (
            db.query(Event)
            .join(EventsUser, EventsUser.event_id == Event.id)
            .filter(EventsUser.user_id == id)
            .distinct()
        )

        model_query = self._model_query_search(
            model_query,
            search_model=Event,
            search_field=search_field,
            search_value=search_value,
        )

        model_query_sorted = self._model_query_sort(
            model_query, sort_by=sort_by, sort_order=sort_order, limit=limit
        )

        model_query_count = model_query.count()

        # Fetch events after sorting
        events = list(model_query_sorted)

        # Get all role_ids for these events
        role_rows = (
            db.query(EventsUser.event_id, EventsUser.role_id)
            .filter(
                EventsUser.user_id == id,
                EventsUser.event_id.in_([e.id for e in events]),
            )
            .all()
        )

        # Build map: event_id → list of role_ids
        role_map = defaultdict(list)
        for event_id, role_id in role_rows:
            role_map[event_id].append(role_id)

        # Attach roles to events
        for event in events:
            event.role_ids = role_map.get(event.id, [])

        return paginate(
            object_list=events,
            object_query_count=model_query_count,
            current_page=page,
            limit=limit,
        )

    # Get all VirtualMachine objects associated with a User via User.vms
    def get_user_vms(
        self,
        db: Session,
        id: Any,
        limit: int = 200,
        page: int = 1,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
        search_field: str = "",
        search_value: str = "",
    ):
        self._get_multi_init(
            limit=limit, page=page, sort_by=sort_by, parent_model=VirtualMachine
        )

        # Build and sort query based on provided parameters
        model_query = (
            db.query(VirtualMachine)
            .outerjoin(User, VirtualMachine.users)
            .filter(or_(User.id == id, VirtualMachine.createdById == id))
            .distinct()
        )

        model_query = self._model_query_search(
            model_query,
            search_model=VirtualMachine,
            search_field=search_field,
            search_value=search_value,
        )

        model_query_sorted = self._model_query_sort(
            model_query, sort_by=sort_by, sort_order=sort_order, limit=limit
        )

        model_query_count = model_query.count()

        return paginate(
            object_list=list(model_query_sorted),
            object_query_count=model_query_count,
            current_page=page,
            limit=limit,
        )


user = CRUDUser(User)
