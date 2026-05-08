import datetime

from pydantic import BaseModel, ConfigDict

from .base import PaginationPageDetails


class RequestUser(BaseModel):
    id: str | None = None
    username: str | None = None


# Base DB class for all objects
class Activity(BaseModel):
    id: str
    timestamp: datetime.datetime
    requestClientIP: str
    requestUser: RequestUser
    requestPermission: str | None = None
    requestMethod: str
    requestUrl: str
    requestParameter: object
    requestHeaders: object
    #  requestBody: str
    #  responseBody: str
    responseCode: int
    responseHeaders: object
    #  requestUserAction: str

    model_config = ConfigDict(from_attributes=True)


class ActivityOwn(BaseModel):
    id: str
    timestamp: datetime.datetime
    requestClientIP: str
    requestMethod: str
    requestUrl: str
    responseCode: int

    model_config = ConfigDict(from_attributes=True)


# List object of Activities
class ActivitiesList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[Activity]


# List object of Activities
class ActivitiesOwnList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[ActivityOwn]
