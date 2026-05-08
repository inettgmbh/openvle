from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from controllers.moodle import search_courses
from core import dependencies
from core.exceptions import PermissionDenied
from schemas.moodle import MoodleCourseSearchList

router = APIRouter(
    prefix="/moodle",
    tags=["moodle"],
    responses={404: {"detail": "Not found"}},
)


@router.get(
    "/courses",
    status_code=200,
    response_model=MoodleCourseSearchList,
    operation_id="moodle_courses_search",
    summary="Search Moodle Courses",
    dependencies=[Depends(dependencies.get_current_user)],
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
