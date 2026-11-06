from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from controllers.system import *
from core import dependencies
from core.exceptions import PermissionDenied
from core.responses import AUTH_ERROR_RESPONSES, build_description

router = APIRouter(
    prefix="/system",
    tags=["system"],
    responses=AUTH_ERROR_RESPONSES,
)


@router.get(
    "/healthz",
    status_code=200,
    include_in_schema=False,
)
def get_healthz(request: Request):
    if request.client.host not in ("127.0.0.1", "::1"):
        raise PermissionDenied()
    return {"status": "ok"}


def get_services_status():
    API_SERVICES_STATUS = {
        "MariaDB": {"status": ""},
        "MongoDB": {"status": ""},
        "Redis": {"status": ""},
        "Proxmox": {"status": ""},
        "Guacamole": {"status": ""},
        "LDAP": {"status": ""},
    }
    # Check status of MariaDB
    try:
        from core.mariadb import SessionLocal

        db: Session = SessionLocal()
        if db:
            API_SERVICES_STATUS["MariaDB"]["status"] = "OK"
            db.close()
        else:
            API_SERVICES_STATUS["MariaDB"]["status"] = "ERROR"
    except:
        API_SERVICES_STATUS["MariaDB"]["status"] = "ERROR"
    # Check status of MongoDB
    try:
        from core.mongodb import db as mongo_db

        if mongo_db["sys_activities"].find().limit(1):
            API_SERVICES_STATUS["MongoDB"]["status"] = "OK"
        else:
            API_SERVICES_STATUS["MongoDB"]["status"] = "ERROR"
    except:
        API_SERVICES_STATUS["MongoDB"]["status"] = "ERROR"
    # Check status of Redis
    try:
        from core.redis import redis_connection

        if redis_connection.ping():
            API_SERVICES_STATUS["Redis"]["status"] = "OK"
        else:
            API_SERVICES_STATUS["Redis"]["status"] = "ERROR"
    except:
        API_SERVICES_STATUS["Redis"]["status"] = "ERROR"
    # Check status of Proxmox
    try:
        from pve.cluster import ProxmoxCluster

        proxmox = ProxmoxCluster().proxmox
        if proxmox.cluster.resources.get():
            API_SERVICES_STATUS["Proxmox"]["status"] = "OK"
        else:
            API_SERVICES_STATUS["Proxmox"]["status"] = "ERROR"
    except:
        API_SERVICES_STATUS["Proxmox"]["status"] = "ERROR"
    # Check status of Guacamole
    try:
        from core.guacamole import guacamole_connect

        guacamole = guacamole_connect()
        if guacamole:
            API_SERVICES_STATUS["Guacamole"]["status"] = "OK"
        else:
            API_SERVICES_STATUS["Guacamole"]["status"] = "ERROR"
    except:
        API_SERVICES_STATUS["Guacamole"]["status"] = "ERROR"
    # TODO: Add LDAP
    return API_SERVICES_STATUS


# Get API version
@router.get(
    "/api/version",
    status_code=200,
    operation_id="api_version_read",
    summary="Get current version of API",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns the current API version string.",
        permission="system_read",
    ),
)
def get_api_version(
    request: Request, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "system_read", request, db=db
    ).has_permission():
        from core.config import Settings

        settings = Settings()
        return {"api_version": settings.project_version}
    else:
        raise PermissionDenied()


# TODO: KVS-388


# Get health status of API as authenticated User
@router.get(
    "/health/authenticated",
    status_code=200,
    operation_id="system_health_auth",
    summary="Get health status of API - Requires user authentication",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns the health status of all dependent services. Requires an authenticated session.",
        permission="system_read",
    ),
)
def get_health_auth(
    request: Request, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "system_read", request, db=db
    ).has_permission():
        return get_services_status()
    else:
        raise PermissionDenied()


# Get health status of API with API token
@router.get(
    "/health/token",
    status_code=200,
    operation_id="system_health_token",
    summary="Get health status of API - Requires HEALTH_API_TOKEN",
    description=build_description(
        description="Returns the health status of all dependent services. Requires a static `HEALTH_API_TOKEN` header instead of a user session.",
    ),
)
def get_health_token(request: Request):
    from core.config import Settings

    settings = Settings()
    # Check if API token provided in request headers is valid
    token = request.headers.get("token")
    if token == settings.api_health_token:
        return get_services_status()
    else:
        raise PermissionDenied()
