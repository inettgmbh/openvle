import uuid

import sentry_sdk
from fastapi import Request
from fastapi.responses import Response


async def request_id_middleware(request: Request, call_next) -> Response:
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Tag the current Sentry scope with the request ID (no-op if Sentry is not initialized)
    sentry_sdk.set_tag("request_id", request_id)

    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response
