from fastapi import APIRouter, Depends, Request
from pydantic import UUID4
from sqlalchemy.orm import Session

from controllers.tags import *
from core import dependencies
from core.exceptions import PermissionDenied
from models import Tag as TagModel, object_type_map
from schemas.tags import Tag, TagCreate, TagList

router = APIRouter(
    prefix="/tags",
    tags=["tags"],
    responses={404: {"detail": "Not found"}},
)


# Create new Tag
@router.post(
    "/",
    status_code=201,
    response_model=Tag,
    operation_id="tags_create",
    summary="Create Tag",
    dependencies=[Depends(dependencies.get_current_user)],
)
def create_tag(
    *,
    tag_in: TagCreate,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> dict:
    if tag_in.objectType not in object_type_map:
        raise ModelNotFound(model_name=tag_in.objectType)
    _, perm_type = object_type_map[tag_in.objectType]

    if perm_type is None:
        raise PermissionDenied()

    required_permission = f"{perm_type}_update"

    if dependencies.PermissionChecker(
        required_permission, request, tag_in.objectId, db=db
    ).has_permission():
        return CRUDTag(TagModel).create(db=db, request=request, obj_in=tag_in)
    else:
        raise PermissionDenied()


# Returns all Tags (filtered by user's object permissions)
@router.get(
    "/",
    status_code=200,
    response_model=TagList,
    operation_id="tags_read_all",
    summary="Get Tags",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_tags(
    request: Request,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
):
    return CRUDTag(TagModel).get_multi_auth(
        request=request,
        db=db,
        limit=limit,
        page=page,
        search_field=search_field,
        search_value=search_value,
        sort_by=sort_by,
        sort_order=sort_order,
    )


# Get Tag with ID
@router.get(
    "/{id}",
    status_code=200,
    response_model=Tag,
    operation_id="tags_read_one",
    summary="Get Tag",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_tag(
    id: UUID4, request: Request, db: Session = Depends(dependencies.get_db)
):
    tag = CRUDTag(TagModel).get(db, id)
    # Get permission type from object type
    if tag.objectType not in object_type_map:
        raise ModelNotFound(model_name=tag.objectType)
    _, perm_type = object_type_map[tag.objectType]

    # Skip permission check for types without permissions
    if perm_type is None:
        raise PermissionDenied()
    required_permission = f"{perm_type}_read"
    # Check permission on the tagged object, not the Tag itself
    if dependencies.PermissionChecker(
        required_permission, request, tag.objectId, db=db
    ).has_permission():
        return tag
    else:
        raise PermissionDenied()


# Delete Tag with ID
@router.delete(
    "/{id}",
    status_code=200,
    operation_id="tags_delete",
    summary="Delete Tag",
    dependencies=[Depends(dependencies.get_current_user)],
)
def delete_tag(
    id: UUID4, request: Request, db: Session = Depends(dependencies.get_db)
):
    tag = CRUDTag(TagModel).get(db, id)

    if tag.objectType not in object_type_map:
        raise ModelNotFound(model_name=tag.objectType)
    _, perm_type = object_type_map[tag.objectType]

    if perm_type is None:
        raise PermissionDenied()

    required_permission = f"{perm_type}_update"

    if dependencies.PermissionChecker(
        required_permission, request, tag.objectId, db=db
    ).has_permission():
        return CRUDTag(TagModel).delete(db, id, request)
    else:
        raise PermissionDenied()


# Returns all Tags for ObjectId and objectType
@router.get(
    "/{objectType}/{objectId}",
    status_code=200,
    response_model=TagList,
    operation_id="tags_objects_read_all",
    summary="Get Tags by objectType and objectId",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_tags_for_object(
    objectId: UUID4,
    objectType: str,
    request: Request,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
):
    return CRUDTag(TagModel).get_tags_for_object_auth(
        request=request,
        db=db,
        objectId=objectId,
        objectType=objectType,
        limit=limit,
        page=page,
        search_field=search_field,
        search_value=search_value,
        sort_by=sort_by,
        sort_order=sort_order,
    )


# Returns all Tags for Key
@router.get(
    "/{key}/",
    status_code=200,
    response_model=TagList,
    operation_id="tags_key_read_all",
    summary="Get Tags by Key",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_tags_key(
    key: str,
    request: Request,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
):
    return CRUDTag(TagModel).get_tags_key_auth(
        request=request,
        db=db,
        key=key,
        limit=limit,
        page=page,
        search_field=search_field,
        search_value=search_value,
        sort_by=sort_by,
        sort_order=sort_order,
    )


# Returns all Tags for Key and Value
@router.get(
    "/{key}/{value}/",
    status_code=200,
    response_model=TagList,
    operation_id="tags_key_value_read_all",
    summary="Get Tags by Key-Value pair",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_tags_key_value(
    key: str,
    value: str,
    request: Request,
    limit: int = 100,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
):
    return CRUDTag(TagModel).get_tags_key_value_auth(
        request=request,
        db=db,
        key=key,
        value=value,
        limit=limit,
        search_field=search_field,
        search_value=search_value,
        page=page,
        sort_by=sort_by,
        sort_order=sort_order,
    )
