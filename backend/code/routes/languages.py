from fastapi import APIRouter, Depends, Request
from pydantic import UUID4
from sqlalchemy.orm import Session

from controllers.languages import *
from core import dependencies
from core.exceptions import PermissionDenied
from core.responses import CRUD_RESPONSES
from models.languages import Language as LanguageModel
from schemas.languages import Language, LanguageList

router = APIRouter(
    prefix="/languages",
    tags=["languages"],
    responses=CRUD_RESPONSES,
)


# Returns all Languages
@router.get(
    "/",
    status_code=200,
    response_model=LanguageList,
    operation_id="languages_read_all",
    summary="Get Languages",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_language(
    request: Request,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(None, request, db=db).has_permission():
        return CRUDLanguage(LanguageModel).get_multi(
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


# Get Language with ID
@router.get(
    "/{id}",
    status_code=200,
    response_model=Language,
    operation_id="languages_read_one",
    summary="Get Language",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_language(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(None, request, db=db).has_permission():
        return CRUDLanguage(LanguageModel).get(db, id)
    else:
        raise PermissionDenied()
