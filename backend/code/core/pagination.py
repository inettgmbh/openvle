import math
from typing import Any, Optional

from fastapi_pagination.api import apply_items_transformer
from fastapi_pagination.types import ItemsTransformer

from .exceptions import PaginationPageError


# Custom Pagination
def paginate(
    object_list: Any,
    object_query_count: int,
    current_page: int,
    limit: int = 100,
    *,
    transformer: ItemsTransformer | None = None,
) -> Any:
    items_all = object_list  # List of records returned by query

    total_count = (
        object_query_count  # Total amount of records returned by query
    )
    per_page = limit
    page_count = math.ceil(total_count / per_page)

    if not items_all:
        t_items = []
        total_count = 0  # Total amount of records returned by query
        per_page = 0
        page_count = 1
    else:
        # Check if the page the user is trying to access is within range of the total pages.
        if current_page > page_count or current_page < 1:
            raise PaginationPageError()

        t_items = apply_items_transformer(
            items_all, transformer
        )  # Transformed items

    response = {
        "pageDetails": {
            "page": current_page,
            "perPage": per_page,
            "pageCount": page_count,
            "totalCount": total_count,
        },
        "items": t_items,
    }

    return response
