from fastapi import APIRouter, Depends, Request
from pydantic import UUID4
from sqlalchemy.orm import Session

from controllers.courses import *
from controllers.templates import *
from core import dependencies
from core.exceptions import DuplicateFieldException, PermissionDenied
from core.responses import (
    BASE_RESPONSES,
    CRUD_RESPONSES,
    DELETE_RESPONSES,
    READ_RESPONSES,
    WRITE_RESPONSES,
    build_description,
)
from models.courses import Course as CourseModel
from models.templates import Template as TemplateModel
from schemas.courses import *
from schemas.templates import *

router = APIRouter(
    prefix="/courses",
    tags=["courses"],
    responses=BASE_RESPONSES,
)


# Create new Course
@router.post(
    "/",
    status_code=201,
    response_model=Course,
    operation_id="courses_create",
    responses=CRUD_RESPONSES,
    summary="Create Course",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Creates a new course.",
        permission="courses_create",
    ),
)
def create_course(
    *,
    course_in: CourseCreate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "courses_create", request, db=db
    ).has_permission():
        # Check if course with the same name already exists
        db_name = CRUDCourse(CourseModel).get_by_name(db, name=course_in.name)
        if db_name:
            raise DuplicateFieldException(field="name")
        return CRUDCourse(CourseModel).create(
            db=db, request=request, obj_in=course_in
        )
    else:
        raise PermissionDenied()


# Returns all Courses
@router.get(
    "/",
    status_code=200,
    response_model=CourseList,
    operation_id="courses_read_all",
    summary="Get Courses",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a paginated list of all courses visible to the requesting user.",
        permission="courses_read",
    ),
)
def get_courses(
    request: Request,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "courses_read", request, db=db
    ).has_permission():
        return CRUDCourse(CourseModel).get_multi(
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDCourse(CourseModel).get_multi_auth(
            request=request,
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )


# Get Course with ID
@router.get(
    "/{id}",
    status_code=200,
    response_model=Course,
    operation_id="courses_read_one",
    responses=READ_RESPONSES,
    summary="Get Course",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a single course by ID.",
        permission="courses_read",
    ),
)
def get_course(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "courses_read", request, id, db=db
    ).has_permission():
        return CRUDCourse(CourseModel).get(db, id)
    else:
        raise PermissionDenied()


# Update Course
@router.put(
    "/{id}",
    status_code=200,
    response_model=Course,
    operation_id="courses_update",
    responses=CRUD_RESPONSES,
    summary="Update Course",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Updates a course's metadata.",
        permission="courses_update",
    ),
)
def update_course(
    *,
    id: UUID4,
    course_in: CourseUpdate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "courses_update", request, id, db=db
    ).has_permission():
        # Check if course with the same name already exists
        db_name = CRUDCourse(CourseModel).get_by_name(db, name=course_in.name)
        if db_name and db_name.id != id:
            raise DuplicateFieldException(field="name")
        # Check if a DIFFERENT course with the same Key already exists
        return CRUDCourse(CourseModel).update(
            db=db, request=request, obj_in=course_in, id=id
        )
    else:
        raise PermissionDenied()


# Delete Course with ID
@router.delete(
    "/{id}",
    status_code=200,
    operation_id="courses_delete",
    responses=DELETE_RESPONSES,
    summary="Delete Course",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Deletes a course by ID.",
        permission="courses_delete",
    ),
)
def delete_course(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "courses_delete", request, id, db=db
    ).has_permission():
        return CRUDCourse(CourseModel).delete(db, id)
    else:
        raise PermissionDenied()


# Update Course's Template
@router.post(
    "/{id}/template",
    status_code=200,
    response_model=Course,
    operation_id="courses_template_update",
    responses=WRITE_RESPONSES,
    summary="Update Course Templates",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Adds a template association to a course.",
        permission="courses_update",
    ),
)
def update_course_template(
    *,
    id: UUID4,
    course_in: CourseUpdateTemplate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "courses_update", request, id, db=db
    ).has_permission():
        return CRUDCourse(CourseModel).update_template(
            db=db, request=request, obj_in=course_in, id=id
        )
    else:
        raise PermissionDenied()


# Delete Template from Course
@router.delete(
    "/{id}/template",
    status_code=200,
    response_model=Course,
    operation_id="courses_template_delete",
    responses=WRITE_RESPONSES,
    summary="Delete Template from Course",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Removes a template association from a course.",
        permission="courses_update",
    ),
)
def delete_course_template(
    *,
    id: UUID4,
    course_in: CourseUpdateTemplate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if dependencies.PermissionChecker(
        "courses_update", request, id, db=db
    ).has_permission():
        return CRUDCourse(CourseModel).delete_template(
            db=db, request=request, obj_in=course_in, id=id
        )
    else:
        raise PermissionDenied()


# Returns a Course's templates
@router.get(
    "/{id}/templates",
    status_code=200,
    response_model=TemplateList,
    operation_id="courses_templates_read_all",
    responses=READ_RESPONSES,
    summary="Get Course's Templates",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns all templates associated with a course.",
        permission="courses_read",
    ),
)
def get_courses_templates(
    request: Request,
    id: UUID4,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "courses_read", request, id, db=db
    ).has_permission():
        return CRUDCourse(CourseModel).get_multi_association(
            parent_model=TemplateModel,
            child_model=CourseModel,
            parent_field_name="courses",
            child_field_name="id",
            field_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        return CRUDCourse(CourseModel).get_multi_association_auth(
            request=request,
            parent_model=TemplateModel,
            child_model=CourseModel,
            parent_field_name="courses",
            child_field_name="id",
            field_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )
