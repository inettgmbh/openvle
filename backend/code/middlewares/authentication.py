import uuid
from typing import Any

from jose import JWTError, jwt
from starlette.authentication import AuthCredentials, AuthenticationBackend

from core.config import Settings
from core.dependencies import TokenData
from core.exceptions import CredentialsNotValid
from core.mariadb import SessionLocal
from models.users import User

settings = Settings()


class SimpleUser:
    def __init__(self, username: str, id: Any, locale: str = "en_US") -> None:
        try:
            self.id = uuid.UUID(id)
        except:
            self.id = id
        self.username = username
        self.locale = locale

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self.username


# Authentication Backend Class
class AuthBackend(AuthenticationBackend):
    async def authenticate(self, request):
        db = SessionLocal()
        try:
            if (
                str(request.url)[-14:]
                == f"/v{str(settings.project_version)[0]}/auth/login"
            ):
                return AuthCredentials(["unauthenticated"]), SimpleUser("", "")

            # Return unauthenticated None user if Auth headers are not provided or invalid
            if "Authorization" not in request.headers:
                return AuthCredentials(["unauthenticated"]), SimpleUser("", "")

            if (
                request.headers["Authorization"][:5] == "Basic"
            ):  # Occurs on user login
                return AuthCredentials(["unauthenticated"]), SimpleUser("", "")

            # Get token from Auth header
            token = request.headers["Authorization"][7:]
            try:
                payload = jwt.decode(
                    token,
                    settings.auth_secret,
                    algorithms=[settings.auth_algorithm],
                    audience=settings.project_name,
                    issuer=settings.project_name,
                    options={
                        "require_aud": True,
                        "require_iat": True,
                        "require_exp": True,
                        "require_nbf": True,
                        "require_iss": True,
                        "require_sub": True,
                    },
                )
                user_id: str = payload.get("sub")
                if user_id is None:
                    raise CredentialsNotValid()
                token_data = TokenData(user_id=user_id)
            except JWTError:
                return AuthCredentials(["unauthenticated"]), SimpleUser("", "")

            user = db.get(User, uuid.UUID(token_data.user_id))
            if user is None:
                return AuthCredentials(["unauthenticated"]), SimpleUser("", "")
            if user.status != "Active":
                return AuthCredentials(["unauthenticated"]), SimpleUser("", "")

            # Return simple version of user to be made available to Request.user object
            return AuthCredentials(["authenticated"]), SimpleUser(
                user.username, user.id, user.locale
            )
        finally:
            db.close()
