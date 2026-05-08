from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_pagination import add_pagination
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware

from core.config import Settings
from core.docs import docsTags, swaggerConfig
from core.exception_handler import (
    http_exception_handler,
    sqlalchemy_exception_handler,
)

# Periodic tasks import
from core.periodic_tasks import tasks_enqueue
from middlewares.authentication import AuthBackend
from middlewares.language import LanguageMiddleware
from middlewares.logging import activityLogging
from middlewares.request_id import request_id_middleware

# Routes
from routes import app_router, misc

settings = Settings()

BASE_PATH = Path(__file__).resolve().parent
STATIC_PATH = BASE_PATH / "static"

# Initialize FastAPI
app = FastAPI(
    title=settings.project_title,
    description=settings.project_description,
    version=str(settings.project_version),
    contact={
        "name": settings.contact_name,
        "url": settings.contact_url,
        "email": settings.contact_mail,
    },
    license_info={
        "name": "License: AGPL-3.0",
        "url": "https://www.gnu.org/licenses/agpl-3.0",
    },
    openapi_tags=docsTags,
    swagger_ui_parameters=swaggerConfig,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
)

# Register central exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

# Add Sentry (backend) if it is enabled
if settings.sentry_backend_enabled:
    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.sentry_backend_dsn,
        traces_sample_rate=settings.sentry_backend_traces_sample_rate,
        profiles_sample_rate=settings.sentry_backend_profiles_sample_rate,
        enable_tracing=settings.sentry_backend_enable_tracing,
        environment=settings.sentry_env,
        release=settings.sentry_release or None,
    )

# Add fastapi Pagination
add_pagination(app)

# Middleware: Language
app.add_middleware(LanguageMiddleware)

# Middleware: CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
    expose_headers=settings.cors_expose_headers,
)

# Middleware: Authentication
app.add_middleware(AuthenticationMiddleware, backend=AuthBackend())

# Middleware: Logging
app.middleware("http")(activityLogging)

# Middleware: Sessions
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_token)

# Middleware: Request ID
app.middleware("http")(request_id_middleware)

# Load static files
app.mount("/static", StaticFiles(directory=str(STATIC_PATH)), name="static")

# Include imported routes
app.include_router(
    app_router
)  # All contained routers have the API version prefix
app.include_router(misc.router)  # Without version prefix

# Queue daily tasks
tasks_enqueue()
