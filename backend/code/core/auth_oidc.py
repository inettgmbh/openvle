from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode, urlparse

from authlib.integrations.starlette_client import OAuth
from fastapi import Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm.session import Session

from controllers.policies import CRUDPolicy
from core.auth import create_access_token, enrollment
from core.config import Settings
from core.core_utils import get_system_user
from core.exceptions import (
    BadRequestError,
    CSRFMismatch,
    IncorrectCredentials,
    InvalidRedirectURL,
    SystemUserLoginException,
    UserNotActiveError,
)
from models import Policy, User
from schemas.auth import TokenResponse

oauth = OAuth()
settings = Settings()

oauth.register(
    name="oidc00",
    client_id=settings.oidc_client_id,
    client_secret=settings.oidc_client_secret,
    server_metadata_url=settings.oidc_url_metadata,
    client_kwargs={"scope": settings.oidc_scopes},
)


# Authenticate user from oidc
def authenticate_oidc(*, user_in: object = None, db: Session) -> TokenResponse:
    from controllers.users import CRUDUser

    # Prevent login as system user outside development environments
    if (
        settings.app_env != "dev"
        and user_in[settings.oidc_attr_username] == "system"
    ):
        raise SystemUserLoginException()

    # Check if User exists in MariaDB
    user = CRUDUser(User).get_by_username(
        db, username=user_in[settings.oidc_attr_username]
    )

    # If User with username does not exist in MariaDB, create it, if oidc enrollment env is true
    if not user:
        if settings.oidc_enroll_users:
            user = enrollment(
                db,
                username=user_in[settings.oidc_attr_username],
                name=user_in[settings.oidc_attr_name],
                email=user_in[settings.oidc_attr_email],
            )
        else:
            # User does not exist and oidc enrollment is not allowed -> raise error
            raise IncorrectCredentials()
    # Check if our user data (name & email) is still in sync, update data if not
    elif (
        user_in[settings.oidc_attr_name] != user.name
        or user_in[settings.oidc_attr_email] != user.email
    ):
        user.name = user_in[settings.oidc_attr_name]
        user.email = user_in[settings.oidc_attr_email]
        user.updatedAt = datetime.now(timezone.utc)
        user.updatedById = get_system_user().id
        db.add(user)
        db.commit()
        db.refresh(user)

    # Check if user is active
    if user.status != "Active":  # type: ignore
        raise UserNotActiveError()

    # Check for outstanding and active policies
    outstanding_policies_list = CRUDPolicy(Policy).get_outstanding(
        db=db, user_id=user.id
    )

    # Generate response payload
    token_type = "policy_required" if outstanding_policies_list else "bearer"

    return {
        "access_token": create_access_token(user=user, type=token_type),
        "token_type": "bearer",
        "outstanding_policies": outstanding_policies_list or None,
    }


# Start oidc login flow
async def handle_oidc_login(request: Request) -> Any:
    redirect_target = request.query_params.get("redirect", None)

    # Check if provided redirect url is allowed
    # None is always allowed, as we just return the token
    # If env oidc_allowed_redirect_urls is set to '***' we allow any redirect url`
    if not (
        redirect_target is None
        or settings.oidc_allowed_redirect_urls == "***"
        or redirect_target in settings.oidc_allowed_redirect_urls
    ):
        if redirect_target is not None and all(
            [urlparse(redirect_target).scheme, urlparse(redirect_target).netloc]
        ):
            return RedirectResponse(
                f"{redirect_target}?error=redirect_invalid", status_code=302
            )
        raise InvalidRedirectURL(redirect_url=str(redirect_target))

    # Save frontend redirect url in session
    request.session["oidc00_post_auth_redirect"] = redirect_target

    # Generate OIDC callback url
    redirect_uri = request.url_for("oidc_callback")

    return await oauth.oidc00.authorize_redirect(  # type: ignore
        request,
        redirect_uri,
    )


# Process oidc callback from idp
async def handle_oidc_callback(
    request: Request, db: Session
) -> TokenResponse | RedirectResponse | Exception:
    # Fetch (and remove) frontend redirect url from session
    redirect_target = request.session.pop("oidc00_post_auth_redirect", None)

    # Check if provided redirect url is allowed
    if not (
        redirect_target is None
        or settings.oidc_allowed_redirect_urls == "***"
        or redirect_target in settings.oidc_allowed_redirect_urls
    ):
        if redirect_target is not None and all(
            [urlparse(redirect_target).scheme, urlparse(redirect_target).netloc]
        ):
            return RedirectResponse(
                f"{redirect_target}?error=redirect_invalid", status_code=302
            )
        raise InvalidRedirectURL(redirect_url=str(redirect_target))

    # Validate and decode OIDC response
    try:
        token = await oauth.oidc00.authorize_access_token(request)  # type: ignore
    except:
        if redirect_target is not None and all(
            [urlparse(redirect_target).scheme, urlparse(redirect_target).netloc]
        ):
            return RedirectResponse(
                f"{redirect_target}?error=csrf_mismatch", status_code=302
            )
        raise CSRFMismatch()

    try:
        # Authenticate user (check if user exists, (enrollment), active, update data)
        response_payload = authenticate_oidc(user_in=token["userinfo"], db=db)
    except IncorrectCredentials:
        if redirect_target is not None and all(
            [urlparse(redirect_target).scheme, urlparse(redirect_target).netloc]
        ):
            return RedirectResponse(
                f"{redirect_target}?error=incorrect_credentials",
                status_code=302,
            )
        raise IncorrectCredentials()
    except SystemUserLoginException:
        if redirect_target is not None and all(
            [urlparse(redirect_target).scheme, urlparse(redirect_target).netloc]
        ):
            return RedirectResponse(
                f"{redirect_target}?error=system_user", status_code=302
            )
        raise SystemUserLoginException()
    except UserNotActiveError:
        if redirect_target is not None and all(
            [urlparse(redirect_target).scheme, urlparse(redirect_target).netloc]
        ):
            return RedirectResponse(
                f"{redirect_target}?error=user_not_active", status_code=302
            )
        raise
    except:
        if redirect_target is not None and all(
            [urlparse(redirect_target).scheme, urlparse(redirect_target).netloc]
        ):
            return RedirectResponse(
                f"{redirect_target}?error=unknown_error", status_code=302
            )
        raise BadRequestError()

    # Redirect back to frontend with token in URL if redirect URL is provided
    if redirect_target is not None and all(
        [urlparse(redirect_target).scheme, urlparse(redirect_target).netloc]
    ):
        return RedirectResponse(
            f"{redirect_target}?{urlencode(response_payload, doseq=True)}",
            status_code=302,
        )

    # Return the payload if no redirect URL is provided
    return response_payload
