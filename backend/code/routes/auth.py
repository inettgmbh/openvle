from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from controllers.policies import CRUDPolicy
from controllers.users import *
from core import dependencies
from core.auth import authenticate, create_access_token
from core.auth_oidc import handle_oidc_callback, handle_oidc_login
from core.config import Settings
from core.exceptions import SystemUserLoginException
from core.responses import AUTH_ERROR_RESPONSES, build_description
from models import Policy
from schemas.auth import TokenResponse
from schemas.users import *

settings = Settings()

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses=AUTH_ERROR_RESPONSES,
)


def _build_token_response(db: Session, user) -> dict:
    """Check outstanding policies and return the appropriate token."""
    outstanding_policies_list = CRUDPolicy(Policy).get_outstanding(
        db=db, user_id=user.id
    )
    if outstanding_policies_list:
        return {
            "access_token": create_access_token(
                user=user, type="policy_required"
            ),
            "token_type": "bearer",
            "outstanding_policies": outstanding_policies_list,
        }
    return {
        "access_token": create_access_token(user=user, type="bearer"),
        "token_type": "bearer",
        "outstanding_policies": None,
    }


# User login
@router.post(
    "/login",
    response_model=TokenResponse,
    operation_id="auth_login",
    summary="User login",
    description=build_description(
        description="Authenticates a user with username and password and returns a JWT bearer token.",
        notes=[
            "If the user has outstanding policy acceptances, a `policy_required` token is returned instead of a standard bearer token.",
            "The `system` user cannot log in outside of `dev` environments.",
        ],
    ),
)
def login(
    user_in: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(dependencies.get_db),
) -> Any:
    if settings.app_env != "dev" and user_in.username == "system":
        raise SystemUserLoginException()
    user = authenticate(
        username=user_in.username, password=user_in.password, db=db
    )
    return _build_token_response(db, user)


# Reauthenticate user (only accepts policy_required tokens)
@router.post(
    "/reauthenticate",
    response_model=TokenResponse,
    operation_id="auth_reauthenticate",
    summary="Reauthenticate after policy acceptance",
    description=build_description(
        description="Exchanges a `policy_required` token for a standard bearer token after the user has accepted all outstanding policies.",
        notes=[
            "Only `policy_required` tokens are accepted — standard bearer tokens will be rejected.",
        ],
    ),
)
def reauthenticate(
    user=Depends(dependencies.get_current_user_reauth),
    db: Session = Depends(dependencies.get_db),
) -> Any:
    return _build_token_response(db, user)


# Login / Auth via OIDC, if enabled
if settings.oidc_enabled:

    @router.get(
        "/oidc/login",
        response_class=RedirectResponse,
        status_code=302,
        operation_id="auth_oidc_login",
        summary="OIDC login start",
        description=build_description(
            description="Initiates the OIDC authorization code flow by redirecting the user to the configured identity provider.",
        ),
    )
    async def oidc_login(request: Request):
        return await handle_oidc_login(request=request)

    @router.get(
        "/oidc/callback",
        response_model=TokenResponse,
        operation_id="auth_oidc_callback",
        summary="OIDC login callback",
        description=build_description(
            description="Handles the OIDC provider callback and returns a JWT bearer token, or redirects with token/error query parameters.",
        ),
        responses={
            302: {
                "description": (
                    "Redirect to the URL provided during `/oidc/login` "
                    "with token data or error as query parameters. "
                    "Query params on success: `token_type`, "
                    "`access_token`, `outstanding_policies`. "
                    "Query params on error: `error` "
                    "(e.g. `csrf_mismatch`, `incorrect_credentials`, "
                    "`user_not_active`, `system_user`)."
                ),
            },
        },
    )
    async def oidc_callback(
        request: Request, db: Session = Depends(dependencies.get_db)
    ) -> Any:
        return await handle_oidc_callback(request=request, db=db)
