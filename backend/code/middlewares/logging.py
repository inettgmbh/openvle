import json
import time
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse, urlunparse

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from core.config import Settings
from core.mariadb import SessionLocal
from core.mongodb import db
from models import User

settings = Settings()

collection = db["sys_activities"]

SENSITIVE_REQUEST_HEADERS = {"authorization", "cookie"}
SENSITIVE_QUERY_PARAMS = {"code", "state", "id_token"}


# Middleware function
async def activityLogging(request: Request, call_next):
    body_bytes = await request.body()

    msgs = [
        {"type": "http.request", "body": body_bytes, "more_body": False},
        {"type": "http.request", "body": b"", "more_body": False},
    ]

    async def receive():
        return (
            msgs.pop(0)
            if msgs
            else {"type": "http.request", "body": b"", "more_body": False}
        )

    request = Request(request.scope, receive=receive)

    request_id = getattr(request.state, "request_id", None)

    start_time = time.time()
    try:
        response = await call_next(request)
    except HTTPException as exc:
        error_code = getattr(exc, "error_code", "UNKNOWN_ERROR")
        content = {"detail": exc.detail, "error_code": error_code}
        if request_id:
            content["request_id"] = request_id
        response = JSONResponse(content, status_code=exc.status_code)
        if request_id:
            response.headers["X-Request-Id"] = request_id
    except Exception:
        content = {
            "detail": "Internal Server Error",
            "error_code": "INTERNAL_SERVER_ERROR",
        }
        if request_id:
            content["request_id"] = request_id
        response = JSONResponse(content, status_code=500)
        if request_id:
            response.headers["X-Request-Id"] = request_id

    response.headers["X-Created-By"] = settings.contact_name
    response.headers["X-Process-Time"] = str(time.time() - start_time)
    # Skip logging of OPTIONS requests and healthcheck
    if request.method == "OPTIONS" or request.url.path == "/system/healthz":
        return response
    try:
        user_id = "" if not request.user else str(request.user.id)
    except AssertionError:
        # AuthenticationMiddleware is unavailable (e.g. MariaDB connection is down)
        # Continue logging the request with an empty user rather than breaking the response
        user_id = ""

    request_headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in SENSITIVE_REQUEST_HEADERS
    }
    request_params = {
        k: v
        for k, v in request.query_params.items()
        if k not in SENSITIVE_QUERY_PARAMS
    }
    response_headers = dict(response.headers)
    if request_id:
        response_headers["X-Request-Id"] = request_id
    # Strip query parameters from location header (may contain JWT in OIDC redirect)
    if "location" in response_headers:
        parsed = urlparse(response_headers["location"])
        response_headers["location"] = urlunparse(
            parsed._replace(query="", fragment="")
        )

    collectionData = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "requestId": request_id,
        "requestClientIP": request.client.host,
        "requestUser": {"id": user_id, "username": ""},
        "requestMethod": request.method,
        "requestUrl": request.url.path,
        "requestParameter": request_params,
        "requestHeaders": request_headers,
        "responseCode": response.status_code,
        "responseHeaders": response_headers,
    }
    if "login" in request.url.path:
        try:
            username = None
            ct = (request.headers.get("content-type") or "").lower()
            if "application/json" in ct:
                payload = json.loads((body_bytes or b"").decode() or "{}")
                if isinstance(payload, dict):
                    username = payload.get("username")
            elif "application/x-www-form-urlencoded" in ct:
                form = parse_qs((body_bytes or b"").decode())
                vals = form.get("username")
                if vals:
                    username = vals[0]
            if username:
                if response.status_code != 200:
                    collectionData["requestUser"]["username"] = username
                # Get user ID for successful login
                else:
                    mariadb = SessionLocal()
                    user = (
                        mariadb.query(User)
                        .filter(User.username == username)
                        .first()
                    )
                    collectionData["requestUser"]["id"] = str(user.id)
                    mariadb.close()
        except Exception:
            pass
    # Add operation_id from route information from the scope if it exists
    route_info = request.scope.get("route", None)
    if route_info and isinstance(route_info, APIRoute):
        collectionData["requestPermission"] = getattr(
            route_info, "unique_id", None
        ) or getattr(route_info, "operation_id", None)

    collection.insert_one(collectionData)

    return response
