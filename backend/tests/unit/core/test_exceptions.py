"""Tests for core/exceptions.py - Exception hierarchy and status codes."""

import inspect

import core.exceptions as exceptions_module
import pytest
from core.exceptions import (
    BadRequestError,
    BulkActionRequirementMissing,
    BulkObjectNotFound,
    CredentialsNotValid,
    CSRFMismatch,
    DuplicateEventUserRoleError,
    DuplicateFieldException,
    DuplicateObjectPermission,
    FileUploadError,
    GuacamoleConnectionError,
    GuacamoleRequestError,
    IncorrectCredentials,
    InvalidAuthToken,
    InvalidFieldValue,
    InvalidOperationForObject,
    InvalidRedirectURL,
    InvalidStatusError,
    JobEnqueueError,
    LdapConnectionError,
    MailGenerationError,
    MariaDBConnectionError,
    ModelAssociationNotFound,
    ModelFieldNotFound,
    ModelNotFound,
    MongoDBConnectionError,
    ObjectCommitError,
    ObjectDeleteIntegrityError,
    ObjectInitError,
    ObjectInUseError,
    ObjectNotFound,
    OperationDependencyMissing,
    OutstandingPoliciesException,
    PaginationLimitError,
    PaginationPageError,
    PaginationZeroPageError,
    PermissionDenied,
    ProtectedObjectError,
    ProxmoxConnectionError,
    ProxmoxRequestError,
    ProxmoxResourceNotFound,
    RedisConnectionError,
    RelationNotFound,
    RequiredParameterMissingError,
    ServiceConnectionError,
    SystemUserLoginException,
    UnsupportedFileType,
    UserAlreadyRegisteredException,
    UserNotActiveError,
)
from fastapi import HTTPException


class TestExceptionStatusCodes:
    """Verify HTTP status codes for all exception classes."""

    @pytest.mark.parametrize(
        "exc_factory,expected_status",
        [
            (CredentialsNotValid, 401),
            (InvalidAuthToken, 401),
            (IncorrectCredentials, 401),
            (PermissionDenied, 403),
            (SystemUserLoginException, 403),
            (OutstandingPoliciesException, 403),
            (CSRFMismatch, 403),
            (lambda: ObjectNotFound("User", id="abc"), 404),
            (lambda: BulkObjectNotFound("User", ["a", "b"]), 404),
            (UserAlreadyRegisteredException, 409),
            (lambda: ObjectDeleteIntegrityError("User"), 409),
            (lambda: ObjectInUseError("Course", {"Event": 2}), 409),
            (
                lambda: ObjectInUseError(
                    "Template", {"VirtualMachine": 2, "Event": 1}
                ),
                409,
            ),
            (DuplicateEventUserRoleError, 409),
            (lambda: DuplicateObjectPermission("dup"), 409),
            (lambda: DuplicateFieldException("email"), 409),
            (lambda: OperationDependencyMissing("dep"), 409),
            (PaginationLimitError, 422),
            (PaginationZeroPageError, 422),
            (PaginationPageError, 422),
            (lambda: InvalidFieldValue("val", "field"), 422),
            (lambda: InvalidStatusError("Aktiv", "start", ["Geplant"]), 422),
            (lambda: ModelFieldNotFound("User", "xyz"), 422),
            (lambda: ModelNotFound("Foo"), 422),
            (lambda: BulkActionRequirementMissing("msg"), 422),
            (lambda: RequiredParameterMissingError("param"), 422),
            (lambda: ModelAssociationNotFound("A", "B"), 422),
            (lambda: InvalidOperationForObject("op", "type"), 422),
            (lambda: InvalidRedirectURL("http://evil"), 422),
            (BadRequestError, 400),
            (lambda: BadRequestError("custom"), 400),
            (lambda: UnsupportedFileType("text/plain"), 415),
            (lambda: RelationNotFound("A", "1", "B", "2"), 404),
            (lambda: ProxmoxResourceNotFound("VM", 100, "id"), 404),
            (lambda: ProtectedObjectError("User", "delete"), 403),
            (lambda: ObjectCommitError("err", "User"), 500),
            (lambda: ObjectInitError("err"), 500),
            (FileUploadError, 500),
            (lambda: JobEnqueueError("test_job"), 500),
            (lambda: MailGenerationError("err"), 500),
            (ProxmoxConnectionError, 500),
            (ProxmoxRequestError, 500),
            (GuacamoleConnectionError, 500),
            (GuacamoleRequestError, 500),
            (LdapConnectionError, 500),
            (MariaDBConnectionError, 503),
            (MongoDBConnectionError, 503),
            (RedisConnectionError, 503),
        ],
    )
    def test_status_code(self, exc_factory, expected_status):
        exc = exc_factory()
        assert exc.status_code == expected_status


class TestObjectNotFoundMessages:
    def test_includes_id_in_detail(self):
        exc = ObjectNotFound("User", id="abc-123")
        assert "abc-123" in exc.detail
        assert "User" in exc.detail

    def test_includes_slug_in_detail(self):
        exc = ObjectNotFound("Event", slug="evt001")
        assert "evt001" in exc.detail
        assert "Event" in exc.detail

    def test_includes_key_in_detail(self):
        exc = ObjectNotFound("Permission", key="users_read")
        assert "users_read" in exc.detail
        assert "Permission" in exc.detail


class TestInvalidFieldValueMessages:
    def test_with_supported_values(self):
        exc = InvalidFieldValue("bad", "status", supported_values=["a", "b"])
        assert "bad" in exc.detail
        assert "status" in exc.detail
        assert "Supported values" in exc.detail

    def test_with_format(self):
        exc = InvalidFieldValue("bad", "date", format="YYYY-MM-DD")
        assert "bad" in exc.detail
        assert "YYYY-MM-DD" in exc.detail

    def test_basic(self):
        exc = InvalidFieldValue("bad", "field")
        assert "bad" in exc.detail
        assert "field" in exc.detail


class TestInvalidStatusErrorMessage:
    def test_includes_all_info(self):
        exc = InvalidStatusError(
            current_status="Aktiv",
            action="start",
            valid_status_list=["Geplant", "Core Fehler"],
        )
        assert "Aktiv" in exc.detail
        assert "start" in exc.detail
        assert "Geplant" in exc.detail
        assert "Core Fehler" in exc.detail


class TestBadRequestError:
    def test_with_custom_message(self):
        exc = BadRequestError("Something went wrong")
        assert exc.detail == "Something went wrong"

    def test_without_message_uses_default(self):
        exc = BadRequestError()
        assert (
            "error" in exc.detail.lower() or "unexpected" in exc.detail.lower()
        )


class TestCredentialsNotValid:
    def test_has_www_authenticate_header(self):
        exc = CredentialsNotValid()
        assert exc.headers == {"WWW-Authenticate": "Bearer"}


class TestPaginationLimitError:
    def test_includes_configured_limit(self):
        exc = PaginationLimitError()
        assert "500" in exc.detail  # from test env mariadb_query_result_limit


class TestErrorCodes:
    """Verify error_code class attributes on all exception classes."""

    @pytest.mark.parametrize(
        "exc_factory,expected_code",
        [
            (SystemUserLoginException, "SYSTEM_USER_LOGIN"),
            (
                UserAlreadyRegisteredException,
                "USER_ALREADY_REGISTERED",
            ),
            (CredentialsNotValid, "CREDENTIALS_NOT_VALID"),
            (InvalidAuthToken, "INVALID_AUTH_TOKEN"),
            (
                OutstandingPoliciesException,
                "OUTSTANDING_POLICIES",
            ),
            (IncorrectCredentials, "INCORRECT_CREDENTIALS"),
            (PermissionDenied, "PERMISSION_DENIED"),
            (UserNotActiveError, "USER_NOT_ACTIVE"),
            (ServiceConnectionError, "SERVICE_CONNECTION_ERROR"),
            (MariaDBConnectionError, "MARIADB_CONNECTION_ERROR"),
            (MongoDBConnectionError, "MONGODB_CONNECTION_ERROR"),
            (RedisConnectionError, "REDIS_CONNECTION_ERROR"),
            (lambda: ObjectNotFound("User", id="x"), "OBJECT_NOT_FOUND"),
            (
                lambda: BulkObjectNotFound("User", ["a"]),
                "BULK_OBJECT_NOT_FOUND",
            ),
            (
                lambda: BulkActionRequirementMissing("m"),
                "BULK_ACTION_REQUIREMENT_MISSING",
            ),
            (MailGenerationError, "MAIL_GENERATION_ERROR"),
            (lambda: InvalidFieldValue("v", "f"), "INVALID_FIELD_VALUE"),
            (lambda: ObjectInitError("e"), "OBJECT_INIT_ERROR"),
            (
                lambda: ObjectCommitError("e", "M"),
                "OBJECT_COMMIT_ERROR",
            ),
            (PaginationLimitError, "PAGINATION_LIMIT_ERROR"),
            (
                PaginationZeroPageError,
                "PAGINATION_ZERO_PAGE_ERROR",
            ),
            (PaginationPageError, "PAGINATION_PAGE_ERROR"),
            (
                lambda: ModelFieldNotFound("User", "x"),
                "MODEL_FIELD_NOT_FOUND",
            ),
            (lambda: ModelNotFound("Foo"), "MODEL_NOT_FOUND"),
            (
                lambda: ObjectDeleteIntegrityError("User"),
                "OBJECT_DELETE_INTEGRITY_ERROR",
            ),
            (
                lambda: ObjectInUseError("Course", {"Event": 2}),
                "OBJECT_IN_USE",
            ),
            (
                lambda: ObjectInUseError("Event", detail="custom detail"),
                "OBJECT_IN_USE",
            ),
            (
                lambda: RequiredParameterMissingError("p"),
                "REQUIRED_PARAMETER_MISSING",
            ),
            (FileUploadError, "FILE_UPLOAD_ERROR"),
            (
                lambda: UnsupportedFileType("text/plain"),
                "UNSUPPORTED_FILE_TYPE",
            ),
            (
                lambda: ModelAssociationNotFound("A", "B"),
                "MODEL_ASSOCIATION_NOT_FOUND",
            ),
            (lambda: JobEnqueueError("j"), "JOB_ENQUEUE_ERROR"),
            (
                lambda: InvalidStatusError("A", "start", ["B"]),
                "INVALID_STATUS",
            ),
            (
                DuplicateEventUserRoleError,
                "DUPLICATE_EVENT_USER_ROLE",
            ),
            (
                lambda: DuplicateObjectPermission("dup"),
                "DUPLICATE_OBJECT_PERMISSION",
            ),
            (BadRequestError, "BAD_REQUEST"),
            (
                lambda: OperationDependencyMissing("d"),
                "OPERATION_DEPENDENCY_MISSING",
            ),
            (
                lambda: InvalidOperationForObject("o", "t"),
                "INVALID_OPERATION_FOR_OBJECT",
            ),
            (
                lambda: RelationNotFound("A", "1", "B", "2"),
                "RELATION_NOT_FOUND",
            ),
            (
                lambda: ProtectedObjectError("User", "delete"),
                "PROTECTED_OBJECT",
            ),
            (lambda: DuplicateFieldException("email"), "DUPLICATE_FIELD"),
            (
                ProxmoxConnectionError,
                "PROXMOX_CONNECTION_ERROR",
            ),
            (
                lambda: ProxmoxResourceNotFound("VM", 100, "id"),
                "PROXMOX_RESOURCE_NOT_FOUND",
            ),
            (ProxmoxRequestError, "PROXMOX_REQUEST_ERROR"),
            (
                GuacamoleConnectionError,
                "GUACAMOLE_CONNECTION_ERROR",
            ),
            (
                GuacamoleRequestError,
                "GUACAMOLE_REQUEST_ERROR",
            ),
            (LdapConnectionError, "LDAP_CONNECTION_ERROR"),
            (
                lambda: InvalidRedirectURL("http://evil"),
                "INVALID_REDIRECT_URL",
            ),
            (CSRFMismatch, "CSRF_MISMATCH"),
        ],
    )
    def test_error_code(self, exc_factory, expected_code):
        exc = exc_factory()
        assert exc.error_code == expected_code

    def test_error_codes_are_unique(self):
        """No two exception classes share the same error_code."""
        exc_classes = [
            cls
            for _, cls in inspect.getmembers(exceptions_module, inspect.isclass)
            if issubclass(cls, HTTPException) and cls is not HTTPException
        ]
        codes = [cls.error_code for cls in exc_classes]
        duplicates = [c for c in codes if codes.count(c) > 1]
        assert not duplicates, f"Duplicate error_code values: {set(duplicates)}"
