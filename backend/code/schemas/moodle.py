from pydantic import BaseModel

from .base import PaginationPageDetails


class MoodleCourseSearch(BaseModel):
    id: int
    fullname: str
    shortname: str
    categoryname: str
    startdate: int
    enddate: int
    visible: bool


class MoodleCourseSearchList(BaseModel):
    pageDetails: PaginationPageDetails
    items: list[MoodleCourseSearch]
