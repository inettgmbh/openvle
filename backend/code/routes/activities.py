import uuid

import pymongo
from bson import ObjectId
from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy.orm import Session

from core import dependencies
from core.config import Settings
from core.exceptions import (
    InvalidFieldValue,
    ObjectNotFound,
    PaginationLimitError,
    PaginationZeroPageError,
    PermissionDenied,
)
from core.mongodb import db
from core.pagination import paginate
from core.responses import BASE_RESPONSES, READ_RESPONSES, build_description
from schemas.activities import ActivitiesList, ActivitiesOwnList, Activity

settings = Settings()

router = APIRouter(
    prefix="/activities",
    tags=["activities"],
    responses=BASE_RESPONSES,
)

collection = db["sys_activities"]


@router.get(
    "/own",
    response_model=ActivitiesOwnList,
    operation_id="activities_read_own",
    summary="Get My Activities",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a paginated list of the currently authenticated user's own activity log.",
    ),
)
async def get_own(
    request: Request,
    limit: int = 10,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "timestamp",
    sort_order: str = "desc",
):
    if limit > settings.mariadb_query_result_limit:
        raise PaginationLimitError()
    if page < 1:
        raise PaginationZeroPageError()

    skip = page * limit - limit
    if sort_order == "asc":
        sort_order = pymongo.ASCENDING
    elif sort_order == "desc":
        sort_order = pymongo.DESCENDING
    else:
        raise InvalidFieldValue(
            field="sort_order",
            value=sort_order,
            supported_values=["asc", "desc"],
        )

    user_id = str(request.user.id)
    base_filter = {"requestUser.id": user_id}

    search_filter = {}
    if search_field:
        allowed_search_fields = [
            "timestamp",
            "requestClientIP",
            "requestMethod",
            "requestUrl",
            "responseCode",
        ]
        if search_field not in allowed_search_fields:
            raise InvalidFieldValue(
                field="search_field",
                value=search_field,
                supported_values=list(allowed_search_fields),
            )

        numeric_fields = {"responseCode"}
        if search_field in numeric_fields:
            try:
                code = int(search_value)
            except (TypeError, ValueError):
                raise InvalidFieldValue(
                    field="search_value",
                    value=search_value,
                    supported_values=["integer value for responseCode"],
                )
            search_filter = {search_field: code}
        else:
            search_filter = {
                search_field: {"$regex": str(search_value), "$options": "i"}
            }

    final_filter = (
        base_filter
        if not search_filter
        else {"$and": [base_filter, search_filter]}
    )

    model_query = list(
        collection.find(final_filter)
        .sort("timestamp", pymongo.DESCENDING)
        .limit(100)
    )

    model_query.sort(
        key=lambda x: x.get(sort_by, ""),
        reverse=sort_order != pymongo.ASCENDING,
    )

    start_idx = skip
    end_idx = skip + limit
    paginated_entries = model_query[start_idx:end_idx]

    for item in paginated_entries:
        item["id"] = str(item["_id"])

    model_query_count = min(collection.count_documents(final_filter), 100)

    return paginate(
        object_list=paginated_entries,
        object_query_count=model_query_count,
        current_page=page,
        limit=limit,
    )


@router.get(
    "/{id}",
    response_model=Activity,
    operation_id="activities_read_one",
    responses=READ_RESPONSES,
    summary="Get Activity",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a single activity log entry by MongoDB ObjectId.",
        permission="activities_read",
    ),
)
async def getOneById(
    request: Request,
    id: str = Path(..., pattern=r"^[0-9a-f]{24}$"),
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "activities_read", request, db=db
    ).has_permission():
        item = collection.find_one({"_id": ObjectId(id)}, {})
        if item is None:
            raise ObjectNotFound(model_name="Activity", id=id)
        item["id"] = str(item["_id"])
        return item
    else:
        raise PermissionDenied()


@router.get(
    "/",
    response_model=ActivitiesList,
    operation_id="activities_read_all",
    summary="Get Activities",
    dependencies=[Depends(dependencies.get_current_user)],
    description=build_description(
        description="Returns a paginated list of all activity log entries.",
        permission="activities_read",
    ),
)
async def getAll(
    request: Request,
    limit: int = 10,
    page: int = 1,
    search_field: str = "",
    search_value: str = "",
    sort_by: str = "timestamp",
    sort_order: str = "desc",
    db: Session = Depends(dependencies.get_db),
):
    if dependencies.PermissionChecker(
        "activities_read", request, db=db
    ).has_permission():
        if limit > settings.mariadb_query_result_limit:
            raise PaginationLimitError()
        if page < 1:
            raise PaginationZeroPageError()
        skip = page * limit - limit
        # Handle sorting
        if sort_order == "asc":
            sort_order = pymongo.ASCENDING
        elif sort_order == "desc":
            sort_order = pymongo.DESCENDING
        else:
            raise InvalidFieldValue(
                field="sort_order",
                value=sort_order,
                supported_values=["asc", "desc"],
            )

        if not search_field:
            # No search, just sort and paginate
            model_query = (
                collection.find()
                .sort(sort_by, sort_order)
                .skip(skip)
                .limit(limit)
            )
            model_query_count = collection.count_documents({})
        else:
            allowed_search_fields = [
                "timestamp",
                "requestClientIP",
                "requestUser",
                "requestMethod",
                "requestUrl",
                "requestParameter",
                "responseCode",
            ]
            if search_field not in allowed_search_fields:
                raise InvalidFieldValue(
                    field="search_field",
                    value=search_field,
                    supported_values=list(allowed_search_fields),
                )
            numeric_fields = {"responseCode"}

            # Build filter based on field type
            if search_field in numeric_fields:
                try:
                    code = int(search_value)
                except (TypeError, ValueError):
                    raise InvalidFieldValue(
                        field="search_value",
                        value=search_value,
                        supported_values=["integer value for responseCode"],
                    )
                search_filter = {search_field: code}
            elif search_field == "requestUser":

                def _as_uuid(val: str):
                    try:
                        return str(uuid.UUID(str(val)))
                    except (ValueError, TypeError):
                        return None

                uid = _as_uuid(search_value)
                username_regex = (
                    {"$regex": str(search_value), "$options": "i"}
                    if search_value
                    else {"$exists": True}
                )

                or_clauses = [{"requestUser.username": username_regex}]
                if uid:
                    or_clauses.insert(0, {"requestUser.id": uid})

                search_filter = {"$or": or_clauses}

            else:
                # case-insensitive partial match
                search_filter = {
                    search_field: {"$regex": str(search_value), "$options": "i"}
                }

            model_query = (
                collection.find(search_filter)
                .sort(sort_by, sort_order)
                .skip(skip)
                .limit(limit)
            )
            model_query_count = collection.count_documents(search_filter)

        # Handle setting of id
        model_query = list(model_query)
        for item in model_query:
            item["id"] = str(item["_id"])
        # return Paginated list of objects
        return paginate(
            object_list=model_query,
            object_query_count=model_query_count,
            current_page=page,
            limit=limit,
        )
    else:
        raise PermissionDenied()
