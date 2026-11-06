import datetime

from pydantic import BaseModel, ConfigDict, Field

from .base import PaginationPageDetails


class RequestUser(BaseModel):
    """Minimal user representation embedded in activity log entries."""

    id: str | None = Field(
        None, description="ID of the user who made the request"
    )
    username: str | None = Field(
        None, description="Username of the user who made the request"
    )


# Base DB class for all objects
class Activity(BaseModel):
    """Full activity log entry capturing request and response details."""

    id: str = Field(
        ..., description="Unique identifier of the activity log entry"
    )
    timestamp: datetime.datetime = Field(
        ..., description="Timestamp when the request was received"
    )
    requestClientIP: str = Field(
        ..., description="IP address of the client that made the request"
    )
    requestUser: RequestUser = Field(
        ..., description="User who made the request"
    )
    requestPermission: str | None = Field(
        None, description="Permission key required for the requested endpoint"
    )
    requestMethod: str = Field(
        ..., description="HTTP method of the request, e.g. GET, POST"
    )
    requestUrl: str = Field(..., description="URL path of the request")
    requestParameter: object = Field(
        ..., description="Query parameters included in the request"
    )
    requestHeaders: object = Field(
        ..., description="HTTP headers sent with the request"
    )
    #  requestBody: str
    #  responseBody: str
    responseCode: int = Field(
        ..., description="HTTP status code returned by the server"
    )
    responseHeaders: object = Field(
        ..., description="HTTP headers included in the server response"
    )
    #  requestUserAction: str

    model_config = ConfigDict(from_attributes=True)


class ActivityOwn(BaseModel):
    """Reduced activity log entry for the authenticated user's own request history."""

    id: str = Field(
        ..., description="Unique identifier of the activity log entry"
    )
    timestamp: datetime.datetime = Field(
        ..., description="Timestamp when the request was received"
    )
    requestClientIP: str = Field(
        ..., description="IP address of the client that made the request"
    )
    requestMethod: str = Field(
        ..., description="HTTP method of the request, e.g. GET, POST"
    )
    requestUrl: str = Field(..., description="URL path of the request")
    responseCode: int = Field(
        ..., description="HTTP status code returned by the server"
    )

    model_config = ConfigDict(from_attributes=True)


# List object of Activities
class ActivitiesList(BaseModel):
    """Paginated list of full activity log entries."""

    pageDetails: PaginationPageDetails
    items: list[Activity]


# List object of Activities
class ActivitiesOwnList(BaseModel):
    """Paginated list of the authenticated user's own activity entries."""

    pageDetails: PaginationPageDetails
    items: list[ActivityOwn]
