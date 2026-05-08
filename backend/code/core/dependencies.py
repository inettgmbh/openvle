from collections.abc import Generator

from fastapi import Depends
from jose import JWTError, jwt
from pydantic import BaseModel

from controllers.users import *
from middlewares.i18n import _
from models import ObjectPermission, User

from .auth import oauth2_scheme
from .config import Settings
from .exceptions import (
    CredentialsNotValid,
    InvalidAuthToken,
    OutstandingPoliciesException,
    UserNotActiveError,
)
from .mariadb import SessionLocal

settings = Settings()


# Required jwt options
_JWT_OPTIONS = {
    "require_aud": True,
    "require_iat": True,
    "require_exp": True,
    "require_nbf": True,
    "require_iss": True,
    "require_sub": True,
}


# Get database session
def get_db() -> Generator:
    db = SessionLocal()
    db.current_user_id = None
    try:
        yield db
    finally:
        db.close()


class TokenData(BaseModel):
    user_id: str | None = None


def _decode_and_load_user(
    token: str,
    db: Session,
    *,
    allow_policy_required: bool,
    require_policy_required: bool = False,
    optional: bool,
) -> "User | bool":
    # Validate jwt
    if len(token.split(".")) != 3:
        if optional:
            return False
        raise InvalidAuthToken()

    # Decode jwt
    try:
        payload = jwt.decode(
            token,
            settings.auth_secret,
            algorithms=[settings.auth_algorithm],
            audience=settings.project_name,
            issuer=settings.project_name,
            options=_JWT_OPTIONS,
        )
    except JWTError:
        if optional:
            return False
        # TODO: KVS-391
        raise CredentialsNotValid()

    # Check token type
    token_type: str = payload.get("type")  # type: ignore
    if require_policy_required:
        # Only accept policy_required tokens
        if token_type != "policy_required":
            if optional:
                return False
            raise CredentialsNotValid()
    elif token_type == "policy_required" and not allow_policy_required:
        return False if optional else OutstandingPoliciesException()  # type: ignore

    # Fetch user uuid
    user_id: str | None = payload.get("sub")
    if not user_id:
        if optional:
            return False
        raise CredentialsNotValid()

    # Parse user uuid
    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        if optional:
            return False
        raise CredentialsNotValid()

    # Fetch user
    user = db.get(User, user_uuid)
    if user is None:
        if optional:
            return False
        raise CredentialsNotValid()

    # Check user status
    if getattr(user, "status", None) != "Active":
        if optional:
            return False
        raise UserNotActiveError()

    return user


# Get current user
async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User | Exception | bool:
    result = _decode_and_load_user(
        token, db, allow_policy_required=False, optional=False
    )
    if isinstance(result, Exception):
        raise result
    return result


# Get current user (optional)
async def get_current_user_optional(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> "User | bool":
    result = _decode_and_load_user(
        token, db, allow_policy_required=False, optional=True
    )

    return False if isinstance(result, Exception) else result


# Get current user, accept both bearer and policy_required tokens
async def get_current_user_allow_policy_required(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User | Exception | bool:
    result = _decode_and_load_user(
        token, db, allow_policy_required=True, optional=False
    )
    if isinstance(result, Exception):
        raise result
    return result


# Get current user for reauth (only policy_required tokens)
async def get_current_user_reauth(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User | Exception | bool:
    result = _decode_and_load_user(
        token,
        db,
        allow_policy_required=True,
        require_policy_required=True,
        optional=False,
    )
    if isinstance(result, Exception):
        raise result
    return result


# Permission checker Class
class PermissionChecker:
    def __init__(
        self,
        permissions_required: str | list[str] = None,
        request: Request = "",
        object_id: Any = None,
        db: Session = None,
    ) -> None:
        try:
            if request:
                self.user_id = request.user.id
        except:
            self.user_id = ""
        self.permissions_required = permissions_required
        if isinstance(permissions_required, str):
            self.permissions_required = [permissions_required]
        self.object_id = object_id
        self._db = db
        self.user: User

    def __call__(self, user: User = Depends(get_current_user)):
        self.user = user

    def has_permission(self) -> bool:
        """
        Determines whether the current user has permission for an action.
        Integrates Permissions, Role.Permissions, ObjectPermissions (via entity_id/entity_type)

        Permission hierarchy:
        - object_full grants all permissions
        - object_delete grants object_delete, object_update, object_read
        - object_update grants object_update, object_read
        - object_read grants object_read only
        """
        if not self.permissions_required:
            return True

        db = self._db

        # Load user's effective permissions
        effective_perms = CRUDUser(User).get_effective_permissions_new(
            db, self.user_id
        )
        perms_by_type = {}

        for entry in effective_perms:
            t = entry["type"]
            obj_path = entry["path"]  # "/" or "/<uuid>"
            obj_id = None if obj_path == "/" else obj_path.strip("/")

            if t not in perms_by_type:
                perms_by_type[t] = {}

            if obj_id not in perms_by_type[t]:
                perms_by_type[t][obj_id] = []

            for perm in entry["permissions"]:
                if perm not in perms_by_type[t][obj_id]:
                    perms_by_type[t][obj_id].append(perm)

        PERMISSION_TYPES = {
            "vms",
            "events",
            "users",
            "mails",
            "object_permissions",
            "sub_tasks",
            "guacamole_connection_profiles",
            "mail_templates",
            "status_events",
            "dashboards",
        }

        def parse_permission(required_perm: str) -> tuple[str, str]:
            # Try to match against known permission types first
            for perm_type in PERMISSION_TYPES:
                if required_perm.startswith(perm_type + "_"):
                    action = required_perm[len(perm_type) + 1 :]
                    return perm_type, action

            # Fall back to original logic
            parts = required_perm.split("_")

            # Pattern: <type>_actions_<action>
            if "actions" in parts:
                idx = parts.index("actions")
                perm_type = "_".join(parts[:idx])
                action = "actions_" + "_".join(parts[idx + 1 :])
                return perm_type, action

            # Pattern: <type>_<action>
            perm_type = parts[0]
            action = "_".join(parts[1:])
            return perm_type, action

        def map_required_to_obj_perm(action: str) -> str:
            """Convert needed action → object permission style key."""
            mapping = {
                "read": "object_read",
                "add": "object_update",
                "update": "object_update",
                "start": "object_update",
                "stop": "object_update",
                "pause": "object_update",
                "shutdown": "object_update",
                "reset": "object_update",
                "reboot": "object_update",
                "resume": "object_update",
                "hibernate": "object_update",
                "remove": "object_delete",
                "delete": "object_delete",
                "full": "object_full",
                "admins": "object_admins",
                "verwaltende": "object_verwaltende",
                "templates_update": "templates_update",
                "users_read": "users_read",
            }
            return mapping.get(action, f"object_{action}")

        def check_permission_hierarchy(
            needed_perm: str, user_perms: list
        ) -> bool:
            """
            Check if user has the needed permission considering hierarchy:
            - full grants everything (including special permissions)
            - delete grants delete, update, read
            - update grants update, read
            - read grants read only
            """
            # Always check for exact match and full permission
            if needed_perm in user_perms or "full" in user_perms:
                return True

            # Check hierarchical permissions
            if needed_perm == "object_read":
                # object_read is granted by update, delete, or reset
                return (
                    "update" in user_perms
                    or "delete" in user_perms
                    or "reset" in user_perms
                )
            elif needed_perm == "object_update":
                # object_update is granted by delete
                return "delete" in user_perms

            return False

        passed_any = False

        for required_perm in self.permissions_required:
            p_type, p_action = parse_permission(required_perm)

            if p_type not in perms_by_type:
                continue  # try next required permission

            needed_obj_perm = map_required_to_obj_perm(p_action)

            if self.object_id:
                obj_id = str(self.object_id)

                # Check object-specific permissions
                if obj_id in perms_by_type[p_type]:
                    obj_perms = perms_by_type[p_type][obj_id]

                    # Check using hierarchical permission logic
                    if check_permission_hierarchy(needed_obj_perm, obj_perms):
                        passed_any = True
                        break

                    # Also check for the original action (non-mapped)
                    if p_action in obj_perms:
                        passed_any = True
                        break

                # If no object-specific permission found, check for GLOBAL permissions as fallback
                if None in perms_by_type[p_type]:
                    global_obj_perms = perms_by_type[p_type][None]

                    # Check using hierarchical permission logic
                    if check_permission_hierarchy(
                        needed_obj_perm, global_obj_perms
                    ):
                        passed_any = True
                        break

                    # Also check for the original action (non-mapped)
                    if p_action in global_obj_perms:
                        passed_any = True
                        break

            # No object_id provided - check global permissions only
            else:
                needed_normal_perm = p_action
                if None in perms_by_type[p_type]:
                    global_obj_perms = perms_by_type[p_type][None]

                    # Check using hierarchical permission logic
                    if check_permission_hierarchy(
                        needed_obj_perm, global_obj_perms
                    ):
                        passed_any = True
                        break

                    # Also check for the original action (non-mapped)
                    if needed_normal_perm in global_obj_perms:
                        passed_any = True
                        break

            # Check next required_permission if multiple are provided
            continue

        return passed_any
