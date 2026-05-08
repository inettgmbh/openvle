from fastapi import APIRouter, Depends, Request
from pydantic import UUID4
from sqlalchemy.orm import Session

from controllers.sub_tasks import CRUDSubTask
from controllers.tasks import *
from core import dependencies
from core.exceptions import PermissionDenied
from models import SubTask as SubTaskModel, Task as TaskModel
from schemas.sub_tasks import SubTaskList
from schemas.tasks import Task, TaskList

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"detail": "Not found"}},
)


# Returns all Tasks
@router.get(
    "/",
    status_code=200,
    response_model=TaskList,
    operation_id="tasks_read_all",
    summary="Get Tasks",
    dependencies=[Depends(dependencies.PermissionChecker())],
)
def get_tasks(
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
        "tasks_read", request, db=db
    ).has_permission():
        return CRUDTask(TaskModel).get_multi(
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


# Get Task with ID
@router.get(
    "/{id}",
    status_code=200,
    response_model=Task,
    operation_id="tasks_read_one",
    summary="Get Task",
    dependencies=[Depends(dependencies.PermissionChecker())],
)
def get_task(
    id: UUID4, request: Request, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "tasks_read", request, db=db
    ).has_permission():
        return CRUDTask(TaskModel).get(db, id)
    else:
        raise PermissionDenied()


# Get SubTasks with Task.ID
@router.get(
    "/{id}/sub-tasks",
    status_code=200,
    response_model=SubTaskList,
    operation_id="tasks_sub_tasks_read_all",
    summary="Get SubTasks for Task",
    dependencies=[Depends(dependencies.PermissionChecker())],
)
def get_sub_tasks_for_task(
    id: UUID4,
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
        "tasks_read", request, db=db
    ).has_permission():
        return CRUDSubTask(SubTaskModel).get_multi_foreign_key(
            foreign_key_field="parent_task",
            foreign_key_value=id,
            db=db,
            limit=limit,
            page=page,
            search_value=search_value,
            search_field=search_field,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    else:
        raise PermissionDenied()
