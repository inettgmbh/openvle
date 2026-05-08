from core.config import Settings
from core.exceptions import (
    MoodleConnectionError,
    MoodleNotEnabledError,
    MoodleRequestError,
)
from core.moodle import moodle_connect
from core.moodlelib import MoodleAPIError
from schemas.base import PaginationPageDetails
from schemas.moodle import MoodleCourseSearch, MoodleCourseSearchList

settings = Settings()


def search_courses(
    search: str = "",
    id: int | None = None,
) -> MoodleCourseSearchList:
    if not settings.moodle_enabled:
        raise MoodleNotEnabledError()

    moodle = moodle_connect(timeout=settings.moodle_sync_timeout)
    if not moodle:
        raise MoodleConnectionError()

    try:
        if id is not None:
            courses = moodle.get_courses_by_field("id", str(id))
        elif search:
            courses = moodle.search_courses(search)
        else:
            courses = moodle.search_courses("")

        items = [
            MoodleCourseSearch(
                id=c.get("id", 0),
                fullname=c.get("fullname", ""),
                shortname=c.get("shortname", ""),
                categoryname=c.get("categoryname", ""),
                startdate=c.get("startdate", 0),
                enddate=c.get("enddate", 0),
                visible=bool(c.get("visible", 1)),
            )
            for c in courses
            if isinstance(c, dict) and "id" in c
        ]
        total = len(items)
        return MoodleCourseSearchList(
            pageDetails=PaginationPageDetails(
                page=1,
                perPage=total,
                pageCount=1,
                totalCount=total,
            ),
            items=items,
        )

    except MoodleAPIError as e:
        raise MoodleRequestError(message=str(e.message))
    except Exception as e:
        raise MoodleRequestError(message=f"Error searching Moodle courses: {e}")
    finally:
        moodle.close()
