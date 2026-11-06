"""
Reusable FastAPI response dicts and description builder for route decorators.

Router-level preset (use on every APIRouter):
    BASE_RESPONSES  — 401/403/422/503; no 400/404/409

Per-route preset selection:
    READ_RESPONSES  — 401/403/404/422/503  (GET by ID)
    WRITE_RESPONSES — 400/401/403/404/422/503  (POST/PUT/DELETE without uniqueness)
    CRUD_RESPONSES  — 400/401/403/404/409/422/503  (create/update with DuplicateFieldException)

Usage:
    router = APIRouter(responses=BASE_RESPONSES)

    @router.get("/{id}", responses=READ_RESPONSES, ...)
    @router.post("/", responses=WRITE_RESPONSES, ...)
    @router.post("/", responses=CRUD_RESPONSES, ...)  # when 409 is possible

    @router.get("/", description=build_description(
        description="Returns all resources.",
        permission="resource_read",
    ))
"""


def build_description(
    description: str,
    permission: str | list[str] | None = None,
    is_async: bool = False,
    side_effects: list[str] | None = None,
    notes: list[str] | None = None,
    deprecated: str | None = None,
) -> str:
    parts = [description]

    if permission is not None:
        if isinstance(permission, list):
            perm_str = " or ".join(f"`{p}`" for p in permission)
        else:
            perm_str = f"`{permission}`"
        parts.append(f"\n**Required permission:** {perm_str}")

    execution = (
        "Asynchronous — queued and performed by a background worker."
        if is_async
        else "Synchronous — performed immediately."
    )
    parts.append(f"\n**Execution:** {execution}")

    if side_effects:
        parts.append("\n**Side effects:** " + "; ".join(side_effects) + ".")

    if notes:
        notes_md = "\n".join(f"- {n}" for n in notes)
        parts.append(f"\n**Notes:**\n{notes_md}")

    if deprecated:
        parts.append(f"\n> **Deprecated** — use `{deprecated}` instead.")

    return "\n".join(parts)


# ── Individual response dicts ──────────────────────────────────────────────

HTTP_400: dict = {
    400: {
        "description": "Bad Request",
        "content": {
            "application/json": {
                "example": {
                    "detail": "An unexpected error has occurred while processing your request."
                }
            }
        },
    }
}

HTTP_401: dict = {
    401: {
        "description": "Unauthorized — invalid or missing authentication token",
        "content": {
            "application/json": {
                "example": {"detail": "Could not validate credentials"}
            }
        },
    }
}

HTTP_403: dict = {
    403: {
        "description": "Forbidden — insufficient permissions",
        "content": {
            "application/json": {
                "example": {
                    "detail": "You do not have permission to perform this action"
                }
            }
        },
    }
}

HTTP_404: dict = {
    404: {
        "description": "Not Found",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Object with ID: 00000000-0000-0000-0000-000000000001 not found."
                }
            }
        },
    }
}

HTTP_409: dict = {
    409: {
        "description": "Conflict — duplicate entry or unresolved dependency",
        "content": {
            "application/json": {"example": {"detail": "name already exists"}}
        },
    }
}

HTTP_422: dict = {
    422: {
        "description": "Unprocessable Entity — validation or invalid field value",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid field value: example."}
            }
        },
    }
}

HTTP_503: dict = {
    503: {
        "description": "Service Unavailable — database or external service temporarily down",
        "content": {
            "application/json": {
                "example": {"detail": "Database temporarily unavailable."}
            }
        },
    }
}

# ── Combined presets ───────────────────────────────────────────────────────

# Router-level baseline: universal errors on every route
BASE_RESPONSES: dict = {
    **HTTP_401,
    **HTTP_403,
    **HTTP_422,
    **HTTP_503,
}

# GET by-ID or sub-resource: adds 404 on top of BASE
READ_RESPONSES: dict = {
    **HTTP_401,
    **HTTP_403,
    **HTTP_404,
    **HTTP_422,
    **HTTP_503,
}

# Mutation without uniqueness conflict: POST/PUT/DELETE that can 400 or 404
WRITE_RESPONSES: dict = {
    **HTTP_400,
    **HTTP_401,
    **HTTP_403,
    **HTTP_404,
    **HTTP_422,
    **HTTP_503,
}

# Mutation with uniqueness conflict: create/update that can raise DuplicateFieldException
CRUD_RESPONSES: dict = {
    **HTTP_400,
    **HTTP_401,
    **HTTP_403,
    **HTTP_404,
    **HTTP_409,
    **HTTP_422,
    **HTTP_503,
}

# DELETE that can conflict with referential integrity (object still in use)
DELETE_RESPONSES: dict = {
    **WRITE_RESPONSES,
    **HTTP_409,
}

# Auth router: no 404/409, but still covers bad-request, credentials, and service errors
AUTH_ERROR_RESPONSES: dict = {
    **HTTP_400,
    **HTTP_401,
    **HTTP_403,
    **HTTP_422,
    **HTTP_503,
}
