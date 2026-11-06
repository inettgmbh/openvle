import string
import uuid
from collections.abc import MutableMapping
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from sqlalchemy.orm.session import Session

from core.exceptions import BadRequestError, IncorrectCredentials
from core.messages import msg_user_not_active
from middlewares.i18n import _
from models import User

from .auth_ldap import ldap_connect
from .config import Settings
from .core_utils import get_system_user
from .exceptions import BadRequestError, IncorrectCredentials

settings = Settings()

JWTPayloadMapping = MutableMapping[
    str, datetime | bool | str | list[str] | list[int]
]

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"/v{str(settings.project_version)[0]}/auth/login"
)


# Verify user entered password with hashed password stored in DB
def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False


# Password hashing
def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )


# Validate password against configurable rules stored in sys_settings
def validate_password(password: str, db: Session) -> None:
    from models import SystemSetting

    _keys = [
        "passwords.min",
        "passwords.max",
        "passwords.lowercase.min",
        "passwords.uppercase.min",
        "passwords.numbers.min",
        "passwords.special.min",
    ]
    rows = db.query(SystemSetting).filter(SystemSetting.key.in_(_keys)).all()
    cfg = {row.key: int(row.value) for row in rows}

    length = len(password)
    min_len = cfg.get("passwords.min", 0)
    max_len = cfg.get("passwords.max", 9999)
    min_lower = cfg.get("passwords.lowercase.min", 0)
    min_upper = cfg.get("passwords.uppercase.min", 0)
    min_digits = cfg.get("passwords.numbers.min", 0)
    min_special = cfg.get("passwords.special.min", 0)

    if length < min_len:
        raise BadRequestError(
            message=_("Password must be at least {n} characters long.").format(
                n=min_len
            )
        )
    if length > max_len:
        raise BadRequestError(
            message=_("Password must not exceed {n} characters.").format(
                n=max_len
            )
        )
    if sum(1 for c in password if c.islower()) < min_lower:
        raise BadRequestError(
            message=_(
                "Password must contain at least {n} lowercase letter(s)."
            ).format(n=min_lower)
        )
    if sum(1 for c in password if c.isupper()) < min_upper:
        raise BadRequestError(
            message=_(
                "Password must contain at least {n} uppercase letter(s)."
            ).format(n=min_upper)
        )
    if sum(1 for c in password if c.isdigit()) < min_digits:
        raise BadRequestError(
            message=_("Password must contain at least {n} digit(s).").format(
                n=min_digits
            )
        )
    if sum(1 for c in password if c in string.punctuation) < min_special:
        raise BadRequestError(
            message=_(
                "Password must contain at least {n} special character(s)."
            ).format(n=min_special)
        )


# Authenticate username/email and password combo
def authenticate(
    *,
    username: str = None,
    password: str,
    db: Session,
) -> User | None:
    # Check if User exists in MariaDB
    from controllers.users import CRUDUser

    user = CRUDUser(User).get_by_username(db, username=username)
    # If User with username does not exist in MariaDB
    if not user:
        if not settings.ldap_enabled:
            raise IncorrectCredentials()
        # Check if user exists in LDAP
        ldap_connection = ldap_connect(username=username, password=password)
        if ldap_connection:
            ldap_user = ldap_connection.search(
                search_base=settings.ldap_dn_people,
                search_filter=f"({settings.ldap_attr_user}={username})",
                attributes=["cn", settings.ldap_attr_mail],
            )
            if ldap_user and ldap_connection.entries:
                ldap_user = ldap_connection.entries[0]
                # Create new User in MariaDB based on LDAP User details
                user = enrollment(
                    db,
                    username=username,
                    name=ldap_user.cn.value,
                    email=getattr(ldap_user, settings.ldap_attr_mail).value,
                )
                return user
        else:
            raise IncorrectCredentials()
    # Check if User has a password in MariaDB
    if not user.hashed_password:
        if not settings.ldap_enabled:
            raise IncorrectCredentials()
        # Check if user exists in LDAP
        ldap_connection = ldap_connect(username=username, password=password)
        if ldap_connection:
            return user
    # If the User exists in the MariaDB, verify password against MariaDB
    if user and not verify_password(password, user.hashed_password):
        raise IncorrectCredentials()
    # Check if user is active
    if user.status != "Active":  # type: ignore
        raise BadRequestError(message=_(msg_user_not_active))
    # TODO: Check for 2FA KVS-340
    return user


# Create access token for user
def create_access_token(*, user: User, type: str) -> str:
    return _create_token(
        token_type=type,
        lifetime=timedelta(minutes=settings.auth_access_token_expire_minutes),
        user=user,
    )


# Enroll new user from ldap/oidc/external
def enrollment(db: Session, username: str, name: str, email: str) -> User:
    system_user = get_system_user(db)
    # Create new User in MariaDB based on provided user (e.g. LDAP/OIDC/...)
    try:
        new_user = User(
            id=uuid.uuid4(),
            username=username,
            email=email,
            name=name,
            status="Active",
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc),
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except:
        raise BadRequestError(
            message="An error occurred during user enrollment"
        )
    return new_user


# Internal helper for creating tokens
def _create_token(token_type: str, lifetime: timedelta, user: User) -> str:
    payload = {}
    now = datetime.now(timezone.utc)
    payload["type"] = token_type
    payload["exp"] = now + lifetime
    payload["iat"] = now
    payload["nbf"] = now - timedelta(seconds=5)
    payload["sub"] = str(user.id)
    payload["aud"] = settings.project_name
    payload["iss"] = settings.project_name
    payload["user"] = {
        "username": user.username,
        "email": user.email,
        "name": user.name,
    }
    return jwt.encode(
        payload, settings.auth_secret, algorithm=settings.auth_algorithm
    )
