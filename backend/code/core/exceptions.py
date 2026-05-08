from typing import Any

from fastapi import HTTPException

from middlewares.i18n import _

from .config import Settings
from .messages import msg_user_not_active

settings = Settings()


# -------- Auth/User exceptions --------
# Exception: System User login not allowed in production environment
class SystemUserLoginException(HTTPException):
    error_code = "SYSTEM_USER_LOGIN"

    def __init__(self):
        self.status_code = 403
        self.detail = _(
            "Unable to login as system user in production environment"
        )


# Exception: User with Email/username already registered
class UserAlreadyRegisteredException(HTTPException):
    error_code = "USER_ALREADY_REGISTERED"

    def __init__(self):
        self.status_code = 409
        self.detail = _("Email/Username already registered")


# Exception: Invalid credentials
class CredentialsNotValid(HTTPException):
    error_code = "CREDENTIALS_NOT_VALID"

    def __init__(self):
        self.status_code = 401
        self.detail = _("Could not validate credentials")
        self.headers = {"WWW-Authenticate": "Bearer"}


# Exception: Invalid auth token
class InvalidAuthToken(HTTPException):
    error_code = "INVALID_AUTH_TOKEN"

    def __init__(self):
        self.status_code = 401
        self.detail = _("Invalid token")
        self.headers = {"WWW-Authenticate": "Bearer"}


# Exception: User has not agreed to all required policies
class OutstandingPoliciesException(HTTPException):
    error_code = "OUTSTANDING_POLICIES"

    def __init__(self):
        self.status_code = 403
        self.detail = _(
            "This account needs to agree to all outstanding policies before performing this action."
        )


# Exception: Invalid login credentials
class IncorrectCredentials(HTTPException):
    error_code = "INCORRECT_CREDENTIALS"

    def __init__(self):
        self.status_code = 401
        self.detail = _("Incorrect username or password")


# Exception: Insufficient permissions
class PermissionDenied(HTTPException):
    error_code = "PERMISSION_DENIED"

    def __init__(self):
        self.status_code = 403
        self.detail = _("You do not have permission to perform this action")


# Exception: User account is not active
class UserNotActiveError(HTTPException):
    error_code = "USER_NOT_ACTIVE"

    def __init__(self):
        self.status_code = 403
        self.detail = _(msg_user_not_active)


# -------- Database connection exceptions --------
class ServiceConnectionError(HTTPException):
    error_code = "SERVICE_CONNECTION_ERROR"

    def __init__(self):
        super().__init__(
            status_code=503,
            detail=_("Service temporarily unavailable."),
        )


# Exception: Error connecting to MariaDB
class MariaDBConnectionError(ServiceConnectionError):
    error_code = "MARIADB_CONNECTION_ERROR"

    def __init__(self):
        super().__init__()
        self.detail = _("Database temporarily unavailable.")


# Exception: Error connecting to MongoDB
class MongoDBConnectionError(ServiceConnectionError):
    error_code = "MONGODB_CONNECTION_ERROR"

    def __init__(self):
        super().__init__()
        self.detail = _("Database temporarily unavailable.")


# Exception: Error connecting to Redis
class RedisConnectionError(ServiceConnectionError):
    error_code = "REDIS_CONNECTION_ERROR"

    def __init__(self):
        super().__init__()
        self.detail = _("Cache temporarily unavailable.")


# -------- KVS core exceptions --------
# Exception: KVS object not found
class ObjectNotFound(HTTPException):
    error_code = "OBJECT_NOT_FOUND"

    def __init__(
        self, model_name: str, id: Any = None, slug: str = None, key: str = None
    ):
        self.status_code = 404
        if id:
            self.detail = _("{model_name} with ID: {id} not found.").format(
                model_name=model_name, id=id
            )
        elif slug:
            self.detail = _("{model_name} with slug: {slug} not found.").format(
                model_name=model_name, slug=slug
            )
        elif key:
            self.detail = _("{model_name} with key: {key} not found.").format(
                model_name=model_name, key=key
            )


# Exception: KVS bulk objects not found
class BulkObjectNotFound(HTTPException):
    error_code = "BULK_OBJECT_NOT_FOUND"

    def __init__(self, model_name: str, ids: list):
        self.status_code = 404
        self.detail = _(
            "The following {model_name}s ID's could not be found: {ids}"
        ).format(model_name=model_name, ids=ids)


# Exception: KVS bulk action requirement not met
class BulkActionRequirementMissing(HTTPException):
    error_code = "BULK_ACTION_REQUIREMENT_MISSING"

    def __init__(self, message: str):
        self.status_code = 422
        self.detail = _(
            "Requirement for bulk action not met: {message}"
        ).format(message=message)


# Exception: Mail generation failed (generic)
class MailGenerationError(HTTPException):
    error_code = "MAIL_GENERATION_ERROR"

    def __init__(self, message: str = "", status_code: int = 500):
        self.status_code = status_code
        self.detail = _("Mail generation failed. {message}").format(
            message=message
        )


# Exception: Mail subject exceeds the RFC maximum allowed length
class MailSubjectTooLong(HTTPException):
    error_code = "MAIL_SUBJECT_TOO_LONG"

    def __init__(self, max_length: int, actual_length: int):
        self.status_code = 422
        self.detail = _(
            "Mail subject exceeds the maximum allowed length of {max_length} characters (got {actual_length})."
        ).format(max_length=max_length, actual_length=actual_length)


# Exception: System mail subject event slug placeholder cannot be rendered
class MailSubjectSlugRenderError(HTTPException):
    error_code = "MAIL_SUBJECT_SLUG_RENDER_ERROR"

    def __init__(self):
        self.status_code = 500
        self.detail = _(
            "Mail subject contains '{event.slug}' placeholder but no event could be found to render it."
        )


# Exception: Field value exceeds the column's maximum allowed length
class FieldValueTooLong(HTTPException):
    error_code = "FIELD_VALUE_TOO_LONG"

    def __init__(self, field: str, max_length: int, actual_length: int):
        self.status_code = 422
        self.detail = _(
            "'{field}' exceeds the maximum length of {max_length} characters (got {actual_length})."
        ).format(
            field=field, max_length=max_length, actual_length=actual_length
        )


# Exception: Invalid field value in request
class InvalidFieldValue(HTTPException):
    error_code = "INVALID_FIELD_VALUE"

    def __init__(
        self,
        value: Any,
        field: str,
        supported_values: Any = None,
        format: str = None,
        message: str = None,
    ):
        self.status_code = 422
        if supported_values:
            self.detail = _(
                "Invalid {field} value: {value}. Supported values: {supported_values}"
            ).format(
                field=field, value=value, supported_values=supported_values
            )
        elif format:
            self.detail = _(
                "Field '{field}' with value '{value}' is invalid. {field} must follow the following format: {format}"
            ).format(field=field, value=value, format=format)
        elif message:
            self.detail = _(
                "Invalid {field} value: '{value}'. {message}"
            ).format(field=field, value=value, message=message)
        else:
            self.detail = _("Invalid {field} value: {value}.").format(
                field=field, value=value
            )


# Exception: Object initialisation error
class ObjectInitError(HTTPException):
    error_code = "OBJECT_INIT_ERROR"

    def __init__(self, message: str):
        self.status_code = 500
        self.detail = _(
            "An error occurred during object initialization: {message}"
        ).format(message=message)


# Exception: KVS commit error
class ObjectCommitError(HTTPException):
    error_code = "OBJECT_COMMIT_ERROR"

    def __init__(self, message: str, model_name: str):
        self.status_code = 500
        self.detail = _(
            "An error occurred while committing {model_name} object changes to MariaDB: {message}"
        ).format(model_name=model_name, message=message)


# Exception: Pagination limit error
class PaginationLimitError(HTTPException):
    error_code = "PAGINATION_LIMIT_ERROR"

    def __init__(self):
        self.status_code = 422
        self.detail = _(
            "The 'limit' parameter cannot be more than {limit}"
        ).format(limit=settings.mariadb_query_result_limit)


# Exception: Pagination page error - page=0
class PaginationZeroPageError(HTTPException):
    error_code = "PAGINATION_ZERO_PAGE_ERROR"

    def __init__(self):
        self.status_code = 422
        self.detail = _("The 'page' parameter cannot be less than 1.")


# Exception: Pagination page error
class PaginationPageError(HTTPException):
    error_code = "PAGINATION_PAGE_ERROR"

    def __init__(self):
        self.status_code = 422
        self.detail = _(
            "The page you are trying to access is out of range of the response."
        )


# Exception: Field not in model
class ModelFieldNotFound(HTTPException):
    error_code = "MODEL_FIELD_NOT_FOUND"

    def __init__(self, model_name: str, field_name: str):
        self.status_code = 422
        self.detail = _(
            "Field '{field_name}' could not be found for {model_name} model."
        ).format(field_name=field_name, model_name=model_name)


# Exception: Model doest not exist
class ModelNotFound(HTTPException):
    error_code = "MODEL_NOT_FOUND"

    def __init__(self, model_name: str):
        self.status_code = 422
        self.detail = _("Model with name: {model_name} does not exist.").format(
            model_name=model_name
        )


# Exception: MariaDB integrity error
class ObjectDeleteIntegrityError(HTTPException):
    error_code = "OBJECT_DELETE_INTEGRITY_ERROR"

    def __init__(self, model_name: str):
        self.status_code = 409
        self.detail = _(
            "Could not delete {model_name} object as it the subject of 1 or more relations."
        ).format(model_name=model_name)


# Exception: Required parameter not provided
class RequiredParameterMissingError(HTTPException):
    error_code = "REQUIRED_PARAMETER_MISSING"

    def __init__(self, parameter_name: str):
        self.status_code = 422
        self.detail = _(
            "Required parameter '{parameter_name}' not provided."
        ).format(parameter_name=parameter_name)


# Exception: Error with uploading file
class FileUploadError(HTTPException):
    error_code = "FILE_UPLOAD_ERROR"

    def __init__(self):
        self.status_code = 500
        self.detail = _("There was an error uploading the file.")


# Exception: Unsupported file type
class UnsupportedFileType(HTTPException):
    error_code = "UNSUPPORTED_FILE_TYPE"

    def __init__(self, content_type: str):
        self.status_code = 415
        self.detail = _("Unsupported file type: {content_type}").format(
            content_type=content_type
        )


# Exception: No association between given parent_model and child_model
class ModelAssociationNotFound(HTTPException):
    error_code = "MODEL_ASSOCIATION_NOT_FOUND"

    def __init__(self, parent_model: str, child_model: str):
        self.status_code = 422
        self.detail = _(
            "The '{parent_model}' model has no association with the {child_model} model."
        ).format(parent_model=parent_model, child_model=child_model)


# Exception: Failed to add job to queue
class JobEnqueueError(HTTPException):
    error_code = "JOB_ENQUEUE_ERROR"

    def __init__(self, job_key: str):
        self.status_code = 500
        self.detail = _("Unable to add {job_key} job to worker queue.").format(
            job_key=job_key
        )


# Exception: Object has invalid status for operation
class InvalidStatusError(HTTPException):
    error_code = "INVALID_STATUS"

    def __init__(
        self, current_status: str, action: str, valid_status_list: [str]
    ):
        self.status_code = 422
        valid_statuses = ", ".join(valid_status_list)
        self.detail = _(
            "Action {action} is only permitted when the event status is one of the following: {valid_statuses}. Current status: {current_status}."
        ).format(
            action=action,
            valid_statuses=valid_statuses,
            current_status=current_status,
        )


# Exception: Duplicate Entry for Event, User and Role
class DuplicateEventUserRoleError(HTTPException):
    error_code = "DUPLICATE_EVENT_USER_ROLE"

    def __init__(self):
        self.status_code = 409
        self.detail = _("This User is already assigned to this Event.")


# Exception: Duplicate Entry for ObjectPermission
class DuplicateObjectPermission(HTTPException):
    error_code = "DUPLICATE_OBJECT_PERMISSION"

    def __init__(self, message: str):
        self.status_code = 409
        self.detail = message


# Exception: Generic bad request error
class BadRequestError(HTTPException):
    error_code = "BAD_REQUEST"

    def __init__(self, message: str = None):
        self.status_code = 400
        if message:
            self.detail = message
        else:
            self.detail = _(
                "An unexpected error has occurred while processing your request."
            )


# Exception: Operation dependency not met
class OperationDependencyMissing(HTTPException):
    error_code = "OPERATION_DEPENDENCY_MISSING"

    def __init__(self, message: str):
        self.status_code = 409
        self.detail = _("Operation condition not met: ") + message


# Exception: Invalid object type for operation
class InvalidOperationForObject(HTTPException):
    error_code = "INVALID_OPERATION_FOR_OBJECT"

    def __init__(self, operation: str, object_type: str):
        self.status_code = 422
        self.detail = _(
            "The requested operation {operation} is not possible for object of type {object_type}."
        ).format(operation=operation, object_type=object_type)


# Exception: Relation between 2 objects not found
class RelationNotFound(HTTPException):
    error_code = "RELATION_NOT_FOUND"

    def __init__(
        self,
        model_name_1: str,
        obj_id_1: Any,
        model_name_2: str,
        obj_id_2: Any,
    ):
        self.status_code = 404
        self.detail = _(
            "Could not find relation between {model_name_1} '{obj_id_1}' and {model_name_2} '{obj_id_2}'."
        ).format(
            model_name_1=model_name_1,
            obj_id_1=obj_id_1,
            model_name_2=model_name_2,
            obj_id_2=obj_id_2,
        )


# Exception: Object is protected
class ProtectedObjectError(HTTPException):
    error_code = "PROTECTED_OBJECT"

    def __init__(
        self, model_name: str, operation: str, source: str | None = None
    ):
        self.status_code = 403
        if source:
            self.detail = _(
                "{operation} operation not possible as {model_name} is protected on {source}."
            ).format(operation=operation, model_name=model_name, source=source)
        else:
            self.detail = _(
                "{operation} operation not possible as {model_name} is protected."
            ).format(operation=operation, model_name=model_name)


# Exception: Unique field value already exists in DB
class DuplicateFieldException(HTTPException):
    error_code = "DUPLICATE_FIELD"

    def __init__(self, field: str):
        self.status_code = 409
        self.detail = _("{field} already exists").format(field=field)


# -------- Proxmox integration exceptions --------
# Exception: Error connecting to PVE
class ProxmoxConnectionError(HTTPException):
    error_code = "PROXMOX_CONNECTION_ERROR"

    def __init__(self):
        self.status_code = 500
        self.detail = _("Connection to PVE could not be made.")


# Exception: Proxmox resource not found
class ProxmoxResourceNotFound(HTTPException):
    error_code = "PROXMOX_RESOURCE_NOT_FOUND"

    def __init__(self, resource_type: str, field_value: Any, field_type: str):
        self.status_code = 404
        self.detail = _(
            "{resource_type} with {field_type} '{field_value}' on Proxmox resource could not be found."
        ).format(
            resource_type=resource_type,
            field_type=field_type,
            field_value=field_value,
        )


# Exception: PVE request failure
class ProxmoxRequestError(HTTPException):
    error_code = "PROXMOX_REQUEST_ERROR"

    def __init__(self):
        self.status_code = 500
        self.detail = _("Request to PVE failed.")


# -------- Guacamole integration exceptions --------
# Exception: Error connecting to Guacamole
class GuacamoleConnectionError(HTTPException):
    error_code = "GUACAMOLE_CONNECTION_ERROR"

    def __init__(self):
        self.status_code = 500
        self.detail = _("Connection to Guacamole server could not be made.")


# Exception: Guacamole request failure
class GuacamoleRequestError(HTTPException):
    error_code = "GUACAMOLE_REQUEST_ERROR"

    def __init__(self, message: str = None):
        self.status_code = 500
        if message:
            self.detail = message
        else:
            self.detail = _(
                "An unexpected error has occurred while processing your request."
            )


# -------- LDAP integration exceptions --------
# Exception: Error connecting to LDAP
class LdapConnectionError(HTTPException):
    error_code = "LDAP_CONNECTION_ERROR"

    def __init__(self):
        self.status_code = 500
        self.detail = _("Connection to LDAP server could not be made.")


# -------- OIDC integration exceptions --------
# Exception: Invalid redirect url
class InvalidRedirectURL(HTTPException):
    error_code = "INVALID_REDIRECT_URL"

    def __init__(self, redirect_url: str):
        self.status_code = 422
        self.detail = _("Redirect URL {redirect_url} not allowed.").format(
            redirect_url=redirect_url
        )


# Exception: Mismatching CSRF state in request and response
class CSRFMismatch(HTTPException):
    error_code = "CSRF_MISMATCH"

    def __init__(self):
        self.status_code = 403
        self.detail = _("Mismatching CSRF state in request and response.")


# -------- Moodle integration exceptions --------
# Exception: Error connecting to Moodle
class MoodleConnectionError(HTTPException):
    error_code = "MOODLE_CONNECTION_ERROR"

    def __init__(self):
        self.status_code = 500
        self.detail = _("Connection to Moodle could not be made.")


# Exception: Moodle request failure
class MoodleRequestError(HTTPException):
    error_code = "MOODLE_REQUEST_ERROR"

    def __init__(self, message: str = None):
        self.status_code = 500
        if message:
            self.detail = message
        else:
            self.detail = _(
                "An unexpected error has occurred while processing"
                " your Moodle request."
            )


# Exception: Moodle integration not enabled
class MoodleNotEnabledError(HTTPException):
    error_code = "MOODLE_NOT_ENABLED"

    def __init__(self):
        self.status_code = 422
        self.detail = _("Moodle integration is not enabled.")
