from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import UUID4
from sqlalchemy.orm import Session

from controllers.sub_tasks import *
from core import dependencies
from core.exceptions import PermissionDenied
from models.sub_tasks import SubTask as SubTaskModel
from schemas.sub_tasks import SubTask, SubTaskList

router = APIRouter(
    prefix="/sub-tasks",
    tags=["tasks"],
    responses={404: {"detail": "Not found"}},
)


# Returns all SubTasks
@router.get(
    "/",
    status_code=200,
    response_model=SubTaskList,
    operation_id="sub_tasks_read_all",
    summary="Get SubTasks",
    dependencies=[Depends(dependencies.PermissionChecker())],
)
def get_sub_tasks(
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
        "sub_tasks_read", request, db=db
    ).has_permission():
        return CRUDSubTask(SubTaskModel).get_multi(
            db=db,
            limit=limit,
            page=page,
            search_field=search_field,
            search_value=search_value,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        raise PermissionDenied()


# Get SubTask with ID
@router.get(
    "/{id}",
    status_code=200,
    response_model=SubTask,
    operation_id="sub_tasks_read_one",
    summary="Get SubTask",
    dependencies=[Depends(dependencies.PermissionChecker())],
)
def get_sub_task(
    id: UUID4, request: Request, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "sub_tasks_read", request, db=db
    ).has_permission():
        return CRUDSubTask(SubTaskModel).get(db, id)
    else:
        raise PermissionDenied()


# Retry a SubTask with ID
@router.get(
    "/{id}/retry",
    status_code=200,
    response_model=SubTask,
    operation_id="sub_tasks_retry",
    summary="Retry a failed SubTask",
    dependencies=[Depends(dependencies.PermissionChecker())],
)
def retry_sub_task(
    id: UUID4, request: Request, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "sub_tasks_read", request, db=db
    ).has_permission():
        subtask = CRUDSubTask(SubTaskModel).get(db, id)
        if subtask.status != "failed" and not subtask.action.startswith(
            "periodic"
        ):
            raise HTTPException(
                status_code=403,
                detail="Only failed and periodic SubTasks can be retried",
            )
        return CRUDSubTask(SubTaskModel).retry(db, request, id)
    else:
        raise PermissionDenied()
