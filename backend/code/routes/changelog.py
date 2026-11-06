from fastapi import APIRouter, Depends

from controllers.changelog import *
from core import dependencies
from core.exceptions import PermissionDenied
from core.responses import BASE_RESPONSES, READ_RESPONSES, build_description
from models import Changelog as ChangelogModel, object_type_map
from schemas.changelog import *

router = APIRouter(
    prefix="/changelogs",
    tags=["changelogs"],
    responses=BASE_RESPONSES,
)


# Returns all Changelogs (filtered by user's ObjectPermissions)
@router.get(
    "/",
    status_code=200,
    response_model=ChangelogList,
    operation_id="changelogs_read_all",
    summary="Get Changelogs",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a paginated list of changelog entries filtered to objects the requesting user has access to.",
        permission="changelogs_read",
    ),
)
def get_changelogs(
    request: Request,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "timestamp",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "changelogs_read", request, db=db
    ).has_permission():
        return CRUDChangelog(ChangelogModel).get_multi_auth(
            request=request,
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


# Get Changelog with ID
@router.get(
    "/{id}",
    status_code=200,
    response_model=Changelog,
    operation_id="changelogs_read_one",
    responses=READ_RESPONSES,
    summary="Get Changelog",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a single changelog entry by ID.",
        permission="changelogs_read",
        notes=[
            "Access is additionally gated by the requesting user's read permission on the referenced object.",
        ],
    ),
)
def get_changelog(
    request: Request, id: UUID4, db: Session = Depends(dependencies.get_db)
):
    if dependencies.PermissionChecker(
        "changelogs_read", request, db=db
    ).has_permission():
        changelog = CRUDChangelog(ChangelogModel).get(db, id)
        if changelog.object not in object_type_map:
            raise ModelNotFound(model_name=changelog.object)

        _, perm_type = object_type_map[changelog.object]
        # Skip permission check for types without permissions
        if perm_type is None:
            raise PermissionDenied()

        required_permission = f"{perm_type}_read"
        # Check permission on the object, not the changelog itself
        if dependencies.PermissionChecker(
            required_permission, request, changelog.objectId, db=db
        ).has_permission():
            return changelog
        else:
            raise PermissionDenied()
    else:
        raise PermissionDenied()


# Returns all Changelogs for an objectType/objectId combination
@router.get(
    "/{objectType}/{objectId}",
    status_code=200,
    response_model=ChangelogList,
    operation_id="changelog_object_read_all",
    responses=READ_RESPONSES,
    summary="Get Changelogs for objectId",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns all changelog entries for a specific object.",
        permission="changelogs_read",
    ),
)
def get_changelogs_for_objectId(
    request: Request,
    objectId: UUID4,
    objectType: str,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "timestamp",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "changelogs_read", request, db=db
    ).has_permission():
        return CRUDChangelog(ChangelogModel).get_changelogs_object_auth(
            request=request,
            objectId=objectId,
            objectType=objectType,
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
