from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from controllers.moodle import search_courses
from core import dependencies
from core.exceptions import PermissionDenied
from core.responses import BASE_RESPONSES, build_description
from schemas.moodle import MoodleCourseSearchList

router = APIRouter(
    prefix="/moodle",
    tags=["moodle"],
    responses=BASE_RESPONSES,
)


@router.get(
    "/courses",
    status_code=200,
    response_model=MoodleCourseSearchList,
    operation_id="moodle_courses_search",
    summary="Search Moodle Courses",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Searches for courses in the configured Moodle instance by name or ID.",
        permission="moodle_read",
    ),
)
def search_moodle_courses(
    request: Request,
    search: str = "",
    id: int | None = None,
    db: Session = Depends(dependencies.get_db),
):
    if not dependencies.PermissionChecker(
        "moodle_read", request, db=db
    ).has_permission():
        raise PermissionDenied()

    return search_courses(search=search, id=id)
