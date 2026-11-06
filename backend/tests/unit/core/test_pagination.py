"""Tests for core/pagination.py - Pagination helper function."""

import pytest
from core.exceptions import PaginationPageError
from core.pagination import paginate


class TestPaginate:
    def test_basic_pagination_structure(self):
        items = ["a", "b", "c"]
        result = paginate(items, object_query_count=3, current_page=1, limit=10)
        assert "pageDetails" in result
        assert "items" in result
        assert result["pageDetails"]["page"] == 1
        assert result["pageDetails"]["perPage"] == 10
        assert result["pageDetails"]["totalCount"] == 3

    def test_empty_list_returns_zero_count(self):
        result = paginate([], object_query_count=0, current_page=1, limit=10)
        assert result["pageDetails"]["totalCount"] == 0
        assert result["pageDetails"]["perPage"] == 0
        assert result["pageDetails"]["pageCount"] == 1
        assert result["items"] == []

    def test_none_list_returns_zero_count(self):
        result = paginate(None, object_query_count=0, current_page=1, limit=10)
        assert result["pageDetails"]["totalCount"] == 0
        assert result["items"] == []

    def test_page_count_calculation(self):
        items = list(range(5))
        result = paginate(items, object_query_count=5, current_page=1, limit=2)
        assert result["pageDetails"]["pageCount"] == 3  # ceil(5/2)

    def test_page_count_exact_division(self):
        items = list(range(4))
        result = paginate(items, object_query_count=4, current_page=1, limit=2)
        assert result["pageDetails"]["pageCount"] == 2  # 4/2

    def test_page_count_single_page(self):
        items = list(range(3))
        result = paginate(items, object_query_count=3, current_page=1, limit=10)
        assert result["pageDetails"]["pageCount"] == 1

    def test_page_out_of_range_raises(self):
        items = list(range(3))
        with pytest.raises(PaginationPageError):
            paginate(items, object_query_count=3, current_page=5, limit=2)

    def test_page_zero_raises(self):
        items = list(range(3))
        with pytest.raises(PaginationPageError):
            paginate(items, object_query_count=3, current_page=0, limit=2)

    def test_page_details_accuracy(self):
        items = list(range(10))
        result = paginate(
            items, object_query_count=25, current_page=2, limit=10
        )
        details = result["pageDetails"]
        assert details["page"] == 2
        assert details["perPage"] == 10
        assert details["pageCount"] == 3  # ceil(25/10)
        assert details["totalCount"] == 25
