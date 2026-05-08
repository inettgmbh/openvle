"""Tests for schemas/base.py - Base schema classes."""

import uuid
from datetime import datetime

from schemas.base import DBBase, PaginationPageDetails


class TestDBBase:
    def test_create_classmethod_sets_audit_fields(self):
        user_id = uuid.uuid4()
        obj = DBBase.create(user_id=user_id)
        assert obj.createdById == user_id
        assert obj.updatedById == user_id
        assert isinstance(obj.createdAt, datetime)
        assert isinstance(obj.updatedAt, datetime)

    def test_update_method_sets_updated_fields(self):
        user_id = uuid.uuid4()
        obj = DBBase.create(user_id=user_id)
        new_user_id = uuid.uuid4()
        obj.update(user_id=new_user_id)
        assert obj.updatedById == new_user_id


class TestPaginationPageDetails:
    def test_valid_page_details(self):
        details = PaginationPageDetails(page=1, perPage=10, pageCount=5, totalCount=50)
        assert details.page == 1
        assert details.perPage == 10
        assert details.pageCount == 5
        assert details.totalCount == 50
