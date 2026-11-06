"""Tests for controllers/base.py - CRUDBase generic CRUD operations.

Uses Course as a concrete model since it's simple (name, description, guacamole).
Uses Event for foreign-key tests (Event.course -> Course.id).
Uses Course <-> Template association for many-to-many tests.
"""

import uuid
from datetime import date, datetime, timezone

import pytest
from controllers.base import CRUDBase, build_object_permission_filter
from core.exceptions import (
    InvalidFieldValue,
    ModelFieldNotFound,
    ObjectNotFound,
    PaginationLimitError,
    PaginationZeroPageError,
)
from models import Course, Event, ObjectPermission, Template
from models.associations import (
    course_template_association_table,
    user_role_association_table,
)
from schemas.courses import CourseCreate, CourseUpdate

from tests.helpers.mock_request import create_mock_request


class TestCRUDBaseGet:
    def setup_method(self):
        self.crud = CRUDBase(Course)

    def test_get_existing_object_returns_model(
        self, db_session, system_user, sample_course
    ):
        result = self.crud.get(db_session, id=sample_course.id)
        assert result is not None
        assert result.id == sample_course.id
        assert result.name == sample_course.name

    def test_get_nonexistent_id_raises_object_not_found(
        self, db_session, system_user
    ):
        fake_id = uuid.uuid4()
        with pytest.raises(ObjectNotFound):
            self.crud.get(db_session, id=fake_id)

    def test_get_sets_db_obj_attribute(
        self, db_session, system_user, sample_course
    ):
        self.crud.get(db_session, id=sample_course.id)
        assert self.crud.db_obj is not None
        assert self.crud.db_obj.id == sample_course.id


class TestCRUDBaseGetMulti:
    def setup_method(self):
        self.crud = CRUDBase(Course)

    def _create_courses(self, db_session, system_user, count):
        now = datetime.now(timezone.utc)
        courses = []
        for i in range(count):
            c = Course(
                id=uuid.uuid4(),
                name=f"Course {i:03d}",
                description=f"Desc {i}",
                guacamole=True,
                createdAt=now,
                updatedAt=now,
                createdById=system_user.id,
                updatedById=system_user.id,
            )
            db_session.add(c)
            courses.append(c)
        db_session.flush()
        return courses

    def test_get_multi_returns_paginated_structure(
        self, db_session, system_user
    ):
        self._create_courses(db_session, system_user, 3)
        result = self.crud.get_multi(db_session, limit=10, page=1)
        assert "pageDetails" in result
        assert "items" in result
        assert result["pageDetails"]["totalCount"] == 3

    def test_get_multi_pagination_limits_results(self, db_session, system_user):
        self._create_courses(db_session, system_user, 5)
        result = self.crud.get_multi(db_session, limit=2, page=1)
        assert len(result["items"]) == 2

    def test_get_multi_page_count_calculation(self, db_session, system_user):
        self._create_courses(db_session, system_user, 5)
        result = self.crud.get_multi(db_session, limit=2, page=1)
        assert result["pageDetails"]["pageCount"] == 3  # ceil(5/2)

    def test_get_multi_sort_desc(self, db_session, system_user):
        self._create_courses(db_session, system_user, 3)
        result = self.crud.get_multi(
            db_session, limit=10, page=1, sort_by="name", sort_order="desc"
        )
        names = [item.name for item in result["items"]]
        assert names == sorted(names, reverse=True)

    def test_get_multi_sort_asc(self, db_session, system_user):
        self._create_courses(db_session, system_user, 3)
        result = self.crud.get_multi(
            db_session, limit=10, page=1, sort_by="name", sort_order="asc"
        )
        names = [item.name for item in result["items"]]
        assert names == sorted(names)

    def test_get_multi_search_string_field(self, db_session, system_user):
        self._create_courses(db_session, system_user, 5)
        # Search for "Course 003"
        result = self.crud.get_multi(
            db_session,
            limit=10,
            page=1,
            search_field="name",
            search_value="Course 003",
        )
        assert result["pageDetails"]["totalCount"] == 1
        assert result["items"][0].name == "Course 003"

    def test_get_multi_search_boolean_true(self, db_session, system_user):
        now = datetime.now(timezone.utc)
        for name, guac in [("GuacOn", True), ("GuacOff", False)]:
            db_session.add(
                Course(
                    id=uuid.uuid4(),
                    name=name,
                    guacamole=guac,
                    createdAt=now,
                    updatedAt=now,
                    createdById=system_user.id,
                    updatedById=system_user.id,
                )
            )
        db_session.flush()

        result = self.crud.get_multi(
            db_session,
            limit=10,
            page=1,
            search_field="guacamole",
            search_value="true",
        )
        assert result["pageDetails"]["totalCount"] == 1
        assert result["items"][0].name == "GuacOn"

    def test_get_multi_search_boolean_false(self, db_session, system_user):
        now = datetime.now(timezone.utc)
        for name, guac in [("GuacOn", True), ("GuacOff", False)]:
            db_session.add(
                Course(
                    id=uuid.uuid4(),
                    name=name,
                    guacamole=guac,
                    createdAt=now,
                    updatedAt=now,
                    createdById=system_user.id,
                    updatedById=system_user.id,
                )
            )
        db_session.flush()

        result = self.crud.get_multi(
            db_session,
            limit=10,
            page=1,
            search_field="guacamole",
            search_value="false",
        )
        assert result["pageDetails"]["totalCount"] == 1
        assert result["items"][0].name == "GuacOff"

    def test_get_multi_search_boolean_invalid_raises(
        self, db_session, system_user
    ):
        self._create_courses(db_session, system_user, 1)
        with pytest.raises(InvalidFieldValue):
            self.crud.get_multi(
                db_session,
                limit=10,
                page=1,
                search_field="guacamole",
                search_value="notabool",
            )

    def test_get_multi_empty_result(self, db_session, system_user):
        result = self.crud.get_multi(db_session, limit=10, page=1)
        assert result["pageDetails"]["totalCount"] == 0
        assert result["items"] == []

    def test_get_multi_page_zero_raises(self, db_session, system_user):
        self._create_courses(db_session, system_user, 3)
        with pytest.raises(PaginationZeroPageError):
            self.crud.get_multi(db_session, limit=10, page=0)

    def test_get_multi_limit_exceeds_max_raises(self, db_session, system_user):
        with pytest.raises(PaginationLimitError):
            self.crud.get_multi(db_session, limit=10000, page=1)


class TestCRUDBaseCreate:
    def setup_method(self):
        self.crud = CRUDBase(Course)

    def test_create_assigns_uuid_id(self, db_session, active_user):
        request = create_mock_request(active_user)
        obj_in = CourseCreate(
            name="New Course", description="Desc", guacamole=True
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)
        assert result.id is not None
        assert isinstance(result.id, uuid.UUID)

    def test_create_sets_timestamps(self, db_session, active_user):
        request = create_mock_request(active_user)
        obj_in = CourseCreate(
            name="New Course 2", description="Desc", guacamole=True
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)
        assert result.createdAt is not None
        assert result.updatedAt is not None

    def test_create_sets_audit_user(self, db_session, active_user):
        request = create_mock_request(active_user)
        obj_in = CourseCreate(
            name="Audit Course", description="Desc", guacamole=False
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)
        assert result.createdById == active_user.id
        assert result.updatedById == active_user.id

    def test_create_object_permission_for_standard_model(
        self, db_session, active_user
    ):
        request = create_mock_request(active_user)
        obj_in = CourseCreate(
            name="Perm Course", description="Desc", guacamole=True
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)
        # Course is not in MODELS_NO_OBJ_PERM, so ObjectPermission should be created
        obj_perm = (
            db_session.query(ObjectPermission)
            .filter(
                ObjectPermission.object_id == result.id,
                ObjectPermission.entity_id == active_user.id,
            )
            .first()
        )
        assert obj_perm is not None
        assert obj_perm.permission_key == "object_full"


class TestCRUDBaseUpdate:
    def setup_method(self):
        self.crud = CRUDBase(Course)

    def test_update_modifies_specified_fields(
        self, db_session, active_user, sample_course
    ):
        request = create_mock_request(active_user)
        obj_in = CourseUpdate(name="Updated Course Name")
        result = self.crud.update(
            sample_course.id, db_session, request, obj_in=obj_in
        )
        assert result.name == "Updated Course Name"

    def test_update_nonexistent_id_raises_not_found(
        self, db_session, active_user
    ):
        request = create_mock_request(active_user)
        fake_id = uuid.uuid4()
        obj_in = CourseUpdate(name="X")
        with pytest.raises(ObjectNotFound):
            self.crud.update(fake_id, db_session, request, obj_in=obj_in)

    def test_update_sets_updated_meta(
        self, db_session, active_user, sample_course
    ):
        request = create_mock_request(active_user)
        obj_in = CourseUpdate(name="Meta Updated")
        result = self.crud.update(
            sample_course.id, db_session, request, obj_in=obj_in
        )
        assert result.updatedById == active_user.id
        # updatedAt should be set (may differ in tz-awareness from fixture)
        assert result.updatedAt is not None

    def test_update_preserves_unmodified_fields(
        self, db_session, active_user, sample_course
    ):
        request = create_mock_request(active_user)
        original_description = sample_course.description
        # Only update name, leave description as None (should not change it)
        obj_in = {"name": "Only Name Changed"}
        result = self.crud.update(
            sample_course.id, db_session, request, obj_in=obj_in
        )
        assert result.description == original_description

    def test_update_null_on_not_null_field_raises_422(
        self, db_session, active_user, sample_course
    ):
        """Setting a NOT NULL field to None must raise InvalidFieldValue (422)."""
        request = create_mock_request(active_user)
        obj_in = {"name": None}
        with pytest.raises(InvalidFieldValue):
            self.crud.update(
                sample_course.id, db_session, request, obj_in=obj_in
            )

    def test_update_null_on_not_null_bool_field_raises_422(
        self, db_session, active_user, sample_course
    ):
        """Course.guacamole is NOT NULL — setting to None must fail."""
        request = create_mock_request(active_user)
        obj_in = {"guacamole": None}
        with pytest.raises(InvalidFieldValue):
            self.crud.update(
                sample_course.id, db_session, request, obj_in=obj_in
            )

    def test_update_null_on_nullable_field_succeeds(
        self, db_session, active_user, sample_course
    ):
        """Course.description is nullable — setting to None is allowed."""
        request = create_mock_request(active_user)
        obj_in = {"description": None}
        result = self.crud.update(
            sample_course.id, db_session, request, obj_in=obj_in
        )
        assert result.description is None


class TestCRUDBaseDelete:
    def setup_method(self):
        self.crud = CRUDBase(Course)

    def test_delete_removes_object_from_db(
        self, db_session, system_user, sample_course
    ):
        course_id = sample_course.id
        self.crud.delete(db_session, id=course_id)
        result = db_session.get(Course, course_id)
        assert result is None

    def test_delete_nonexistent_raises_not_found(self, db_session, system_user):
        fake_id = uuid.uuid4()
        with pytest.raises(ObjectNotFound):
            self.crud.delete(db_session, id=fake_id)

    def test_delete_removes_associated_object_permissions(
        self, db_session, active_user, system_user
    ):
        # Create a course with object permission
        request = create_mock_request(active_user)
        obj_in = CourseCreate(
            name="Delete Test", description="D", guacamole=True
        )
        course = self.crud.create(db_session, request, obj_in=obj_in)
        course_id = course.id

        # Verify object permission exists
        perms_before = (
            db_session.query(ObjectPermission)
            .filter(ObjectPermission.object_id == course_id)
            .count()
        )
        assert perms_before > 0

        # Delete the course
        self.crud.delete(db_session, id=course_id)

        # ObjectPermissions should be cleaned up
        perms_after = (
            db_session.query(ObjectPermission)
            .filter(ObjectPermission.object_id == course_id)
            .count()
        )
        assert perms_after == 0


class TestBuildObjectPermissionFilter:
    def test_filter_includes_user_direct_permissions(
        self, db_session, active_user, system_user, sample_course
    ):
        now = datetime.now(timezone.utc)
        # Create direct user ObjectPermission for sample_course
        op = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Course",
            object_id=sample_course.id,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_read",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(op)
        db_session.flush()

        # Build filter and query
        perm_filter = build_object_permission_filter(
            db_session, Course, active_user.id
        )
        result = db_session.query(Course).filter(perm_filter).all()
        assert any(c.id == sample_course.id for c in result)

    def test_filter_includes_role_permissions(
        self, db_session, active_user, system_user, sample_course, role_admin
    ):
        now = datetime.now(timezone.utc)

        # Assign user to role
        db_session.execute(
            user_role_association_table.insert().values(
                user_id=active_user.id, role_id=role_admin.id
            )
        )
        db_session.flush()

        # Create role ObjectPermission
        op = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Course",
            object_id=sample_course.id,
            entity_id=role_admin.id,
            entity_type="Role",
            permission_key="object_full",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(op)
        db_session.flush()

        perm_filter = build_object_permission_filter(
            db_session, Course, active_user.id
        )
        result = db_session.query(Course).filter(perm_filter).all()
        assert any(c.id == sample_course.id for c in result)

    def test_filter_excludes_objects_without_read(
        self, db_session, active_user, system_user
    ):
        # Create a course but no ObjectPermission for user
        now = datetime.now(timezone.utc)
        course = Course(
            id=uuid.uuid4(),
            name="Hidden Course",
            description="No perms",
            guacamole=False,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(course)
        db_session.flush()

        perm_filter = build_object_permission_filter(
            db_session, Course, active_user.id
        )
        result = db_session.query(Course).filter(perm_filter).all()
        assert not any(c.id == course.id for c in result)

    def test_filter_includes_object_reset_permission(
        self, db_session, active_user, system_user
    ):
        """object_reset grants read visibility in the permission filter."""
        from models import VirtualMachine

        now = datetime.now(timezone.utc)
        vm = VirtualMachine(
            id=uuid.uuid4(),
            name="Reset VM",
            description="VM with object_reset",
            cpu=2,
            ram=4096,
            disk=20,
            status="running",
            ipv4="10.0.1.99",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(vm)
        db_session.flush()

        # Grant object_reset (not object_read)
        op = ObjectPermission(
            id=uuid.uuid4(),
            object_type="VirtualMachine",
            object_id=vm.id,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_reset",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(op)
        db_session.flush()

        perm_filter = build_object_permission_filter(
            db_session, VirtualMachine, active_user.id
        )
        result = db_session.query(VirtualMachine).filter(perm_filter).all()
        assert any(v.id == vm.id for v in result)

    def test_filter_object_reset_does_not_leak_other_vms(
        self, db_session, active_user, system_user
    ):
        """object_reset on VM-A does not make VM-B visible."""
        from models import VirtualMachine

        now = datetime.now(timezone.utc)
        vm_a = VirtualMachine(
            id=uuid.uuid4(),
            name="Reset VM A",
            cpu=2,
            ram=4096,
            disk=20,
            status="running",
            ipv4="10.0.1.80",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        vm_b = VirtualMachine(
            id=uuid.uuid4(),
            name="Hidden VM B",
            cpu=2,
            ram=4096,
            disk=20,
            status="running",
            ipv4="10.0.1.81",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add_all([vm_a, vm_b])
        db_session.flush()

        # Grant object_reset only on vm_a
        op = ObjectPermission(
            id=uuid.uuid4(),
            object_type="VirtualMachine",
            object_id=vm_a.id,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_reset",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(op)
        db_session.flush()

        perm_filter = build_object_permission_filter(
            db_session, VirtualMachine, active_user.id
        )
        result = db_session.query(VirtualMachine).filter(perm_filter).all()
        result_ids = {v.id for v in result}
        assert vm_a.id in result_ids
        assert vm_b.id not in result_ids


class TestCRUDBaseGetMultiAuth:
    """Tests for get_multi_auth() - paginated listing filtered by ObjectPermissions."""

    def setup_method(self):
        self.crud = CRUDBase(Course)

    def _create_course(self, db_session, system_user, name):
        now = datetime.now(timezone.utc)
        course = Course(
            id=uuid.uuid4(),
            name=name,
            description=f"Desc for {name}",
            guacamole=True,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(course)
        db_session.flush()
        return course

    def _grant_user_permission(
        self, db_session, system_user, user, course, perm_key="object_read"
    ):
        now = datetime.now(timezone.utc)
        op = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Course",
            object_id=course.id,
            entity_id=user.id,
            entity_type="User",
            permission_key=perm_key,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(op)
        db_session.flush()
        return op

    def test_returns_only_permitted_courses(
        self, db_session, active_user, system_user
    ):
        visible = self._create_course(db_session, system_user, "Visible Course")
        self._create_course(db_session, system_user, "Hidden Course")
        self._grant_user_permission(
            db_session, system_user, active_user, visible
        )

        request = create_mock_request(active_user)
        result = self.crud.get_multi_auth(db_session, request, limit=10, page=1)
        assert result["pageDetails"]["totalCount"] == 1
        assert result["items"][0].id == visible.id

    def test_returns_empty_when_no_permissions(
        self, db_session, active_user, system_user
    ):
        self._create_course(db_session, system_user, "No Access")
        request = create_mock_request(active_user)
        result = self.crud.get_multi_auth(db_session, request, limit=10, page=1)
        assert result["pageDetails"]["totalCount"] == 0
        assert result["items"] == []

    def test_includes_courses_with_role_permission(
        self, db_session, active_user, system_user, role_admin
    ):
        course = self._create_course(db_session, system_user, "Role-Visible")
        # Assign user to role
        db_session.execute(
            user_role_association_table.insert().values(
                user_id=active_user.id, role_id=role_admin.id
            )
        )
        # Grant role permission on course
        now = datetime.now(timezone.utc)
        op = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Course",
            object_id=course.id,
            entity_id=role_admin.id,
            entity_type="Role",
            permission_key="object_full",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(op)
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_multi_auth(db_session, request, limit=10, page=1)
        assert result["pageDetails"]["totalCount"] == 1
        assert result["items"][0].id == course.id

    def test_respects_pagination(self, db_session, active_user, system_user):
        courses = []
        for i in range(5):
            c = self._create_course(
                db_session, system_user, f"Auth Course {i:03d}"
            )
            self._grant_user_permission(db_session, system_user, active_user, c)
            courses.append(c)

        request = create_mock_request(active_user)
        result = self.crud.get_multi_auth(db_session, request, limit=2, page=1)
        assert len(result["items"]) == 2
        assert result["pageDetails"]["totalCount"] == 5
        assert result["pageDetails"]["pageCount"] == 3

    def test_search_field_filters_within_permitted(
        self, db_session, active_user, system_user
    ):
        c1 = self._create_course(db_session, system_user, "Alpha Course")
        c2 = self._create_course(db_session, system_user, "Beta Course")
        self._grant_user_permission(db_session, system_user, active_user, c1)
        self._grant_user_permission(db_session, system_user, active_user, c2)

        request = create_mock_request(active_user)
        result = self.crud.get_multi_auth(
            db_session,
            request,
            limit=10,
            page=1,
            search_field="name",
            search_value="Alpha",
        )
        assert result["pageDetails"]["totalCount"] == 1
        assert result["items"][0].name == "Alpha Course"

    def test_limit_exceeds_max_raises(
        self, db_session, active_user, system_user
    ):
        request = create_mock_request(active_user)
        with pytest.raises(PaginationLimitError):
            self.crud.get_multi_auth(db_session, request, limit=10000, page=1)

    def test_page_zero_raises(self, db_session, active_user, system_user):
        request = create_mock_request(active_user)
        with pytest.raises(PaginationZeroPageError):
            self.crud.get_multi_auth(db_session, request, limit=10, page=0)

    def test_all_read_permission_keys_grant_access(
        self, db_session, active_user, system_user
    ):
        """object_read, object_update, object_delete, object_full all grant read."""
        for perm_key in [
            "object_read",
            "object_update",
            "object_delete",
            "object_full",
        ]:
            c = self._create_course(db_session, system_user, f"Perm-{perm_key}")
            self._grant_user_permission(
                db_session, system_user, active_user, c, perm_key=perm_key
            )

        request = create_mock_request(active_user)
        result = self.crud.get_multi_auth(db_session, request, limit=10, page=1)
        assert result["pageDetails"]["totalCount"] == 4

    def test_object_reset_grants_read_in_get_multi_auth(
        self, db_session, active_user, system_user
    ):
        """object_reset implies read access, so VMs appear in get_multi_auth."""
        from models import VirtualMachine

        crud_vm = CRUDBase(VirtualMachine)
        now = datetime.now(timezone.utc)
        vm = VirtualMachine(
            id=uuid.uuid4(),
            name="Reset-Auth VM",
            cpu=2,
            ram=4096,
            disk=20,
            status="running",
            ipv4="10.0.1.70",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(vm)
        db_session.flush()

        # Grant object_reset on the VM
        op = ObjectPermission(
            id=uuid.uuid4(),
            object_type="VirtualMachine",
            object_id=vm.id,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_reset",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(op)
        db_session.flush()

        request = create_mock_request(active_user)
        result = crud_vm.get_multi_auth(db_session, request, limit=10, page=1)
        assert result["pageDetails"]["totalCount"] == 1
        assert result["items"][0].id == vm.id

    def test_object_reset_mixed_with_other_perms(
        self, db_session, active_user, system_user
    ):
        """VMs with object_reset + VMs with object_read both appear."""
        from models import VirtualMachine

        crud_vm = CRUDBase(VirtualMachine)
        now = datetime.now(timezone.utc)

        vm_reset = VirtualMachine(
            id=uuid.uuid4(),
            name="VM Reset Perm",
            cpu=2,
            ram=4096,
            disk=20,
            status="running",
            ipv4="10.0.1.60",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        vm_read = VirtualMachine(
            id=uuid.uuid4(),
            name="VM Read Perm",
            cpu=2,
            ram=4096,
            disk=20,
            status="running",
            ipv4="10.0.1.61",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        vm_none = VirtualMachine(
            id=uuid.uuid4(),
            name="VM No Perm",
            cpu=2,
            ram=4096,
            disk=20,
            status="running",
            ipv4="10.0.1.62",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add_all([vm_reset, vm_read, vm_none])
        db_session.flush()

        for vm, perm_key in [
            (vm_reset, "object_reset"),
            (vm_read, "object_read"),
        ]:
            op = ObjectPermission(
                id=uuid.uuid4(),
                object_type="VirtualMachine",
                object_id=vm.id,
                entity_id=active_user.id,
                entity_type="User",
                permission_key=perm_key,
                createdAt=now,
                updatedAt=now,
                createdById=system_user.id,
                updatedById=system_user.id,
            )
            db_session.add(op)
        db_session.flush()

        request = create_mock_request(active_user)
        result = crud_vm.get_multi_auth(db_session, request, limit=10, page=1)
        result_ids = {item.id for item in result["items"]}
        assert vm_reset.id in result_ids
        assert vm_read.id in result_ids
        assert vm_none.id not in result_ids
        assert result["pageDetails"]["totalCount"] == 2


class TestCRUDBaseGetMultiForeignKey:
    """Tests for get_multi_foreign_key() - listing filtered by a FK field."""

    def setup_method(self):
        self.crud = CRUDBase(Event)

    def _create_event(
        self, db_session, system_user, name, course_id, status_id
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=name,
            slug=name[:8],
            description=f"Desc {name}",
            dateStart=date(2026, 3, 1),
            dateEnd=date(2026, 3, 31),
            guacamole=True,
            status=status_id,
            course=course_id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(event)
        db_session.flush()
        return event

    def test_returns_events_for_given_course(
        self, db_session, system_user, sample_course, event_statuses
    ):
        status_id = event_statuses["Geplant"].id
        e1 = self._create_event(
            db_session, system_user, "FK-E1", sample_course.id, status_id
        )
        e2 = self._create_event(
            db_session, system_user, "FK-E2", sample_course.id, status_id
        )

        result = self.crud.get_multi_foreign_key(
            db_session,
            foreign_key_field="course",
            foreign_key_value=sample_course.id,
            limit=10,
            page=1,
        )
        assert result["pageDetails"]["totalCount"] == 2
        result_ids = {item.id for item in result["items"]}
        assert e1.id in result_ids
        assert e2.id in result_ids

    def test_excludes_events_from_other_course(
        self, db_session, system_user, sample_course, event_statuses
    ):
        now = datetime.now(timezone.utc)
        other_course = Course(
            id=uuid.uuid4(),
            name="Other Course",
            description="Other",
            guacamole=False,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(other_course)
        db_session.flush()

        status_id = event_statuses["Geplant"].id
        self._create_event(
            db_session, system_user, "FK-Mine", sample_course.id, status_id
        )
        self._create_event(
            db_session, system_user, "FK-Other", other_course.id, status_id
        )

        result = self.crud.get_multi_foreign_key(
            db_session,
            foreign_key_field="course",
            foreign_key_value=sample_course.id,
            limit=10,
            page=1,
        )
        assert result["pageDetails"]["totalCount"] == 1
        assert result["items"][0].name == "FK-Mine"

    def test_invalid_foreign_key_field_raises(self, db_session, system_user):
        with pytest.raises(ModelFieldNotFound):
            self.crud.get_multi_foreign_key(
                db_session,
                foreign_key_field="nonexistent_field",
                foreign_key_value=uuid.uuid4(),
                limit=10,
                page=1,
            )

    def test_respects_pagination(
        self, db_session, system_user, sample_course, event_statuses
    ):
        status_id = event_statuses["Geplant"].id
        for i in range(5):
            self._create_event(
                db_session,
                system_user,
                f"FKPag{i:02d}",
                sample_course.id,
                status_id,
            )

        result = self.crud.get_multi_foreign_key(
            db_session,
            foreign_key_field="course",
            foreign_key_value=sample_course.id,
            limit=2,
            page=1,
        )
        assert len(result["items"]) == 2
        assert result["pageDetails"]["totalCount"] == 5
        assert result["pageDetails"]["pageCount"] == 3

    def test_search_within_fk_filter(
        self, db_session, system_user, sample_course, event_statuses
    ):
        status_id = event_statuses["Geplant"].id
        self._create_event(
            db_session, system_user, "FK-Alph", sample_course.id, status_id
        )
        self._create_event(
            db_session, system_user, "FK-Beta", sample_course.id, status_id
        )

        result = self.crud.get_multi_foreign_key(
            db_session,
            foreign_key_field="course",
            foreign_key_value=sample_course.id,
            limit=10,
            page=1,
            search_field="name",
            search_value="Alph",
        )
        assert result["pageDetails"]["totalCount"] == 1
        assert result["items"][0].name == "FK-Alph"

    def test_empty_result_when_no_matching_fk(
        self, db_session, system_user, sample_course, event_statuses
    ):
        result = self.crud.get_multi_foreign_key(
            db_session,
            foreign_key_field="course",
            foreign_key_value=uuid.uuid4(),
            limit=10,
            page=1,
        )
        assert result["pageDetails"]["totalCount"] == 0
        assert result["items"] == []

    def test_with_parent_model_override(
        self, db_session, system_user, sample_course, event_statuses
    ):
        """Passing parent_model explicitly should behave same as default."""
        status_id = event_statuses["Geplant"].id
        self._create_event(
            db_session, system_user, "FK-PM01", sample_course.id, status_id
        )

        result = self.crud.get_multi_foreign_key(
            db_session,
            foreign_key_field="course",
            foreign_key_value=sample_course.id,
            parent_model=Event,
            limit=10,
            page=1,
        )
        assert result["pageDetails"]["totalCount"] == 1


class TestCRUDBaseGetMultiForeignKeyAuth:
    """Tests for get_multi_foreign_key_auth() - FK filter + ObjectPermission."""

    def setup_method(self):
        self.crud = CRUDBase(Event)

    def _create_event(
        self, db_session, system_user, name, course_id, status_id
    ):
        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=name,
            slug=name[:8],
            description=f"Desc {name}",
            dateStart=date(2026, 3, 1),
            dateEnd=date(2026, 3, 31),
            guacamole=True,
            status=status_id,
            course=course_id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(event)
        db_session.flush()
        return event

    def _grant_event_permission(
        self, db_session, system_user, user, event, perm_key="object_read"
    ):
        now = datetime.now(timezone.utc)
        op = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Event",
            object_id=event.id,
            entity_id=user.id,
            entity_type="User",
            permission_key=perm_key,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(op)
        db_session.flush()
        return op

    def test_returns_only_permitted_events_for_course(
        self,
        db_session,
        active_user,
        system_user,
        sample_course,
        event_statuses,
    ):
        status_id = event_statuses["Geplant"].id
        visible = self._create_event(
            db_session, system_user, "FKA-Vis", sample_course.id, status_id
        )
        self._create_event(
            db_session, system_user, "FKA-Hid", sample_course.id, status_id
        )
        self._grant_event_permission(
            db_session, system_user, active_user, visible
        )

        request = create_mock_request(active_user)
        result = self.crud.get_multi_foreign_key_auth(
            db_session,
            request,
            foreign_key_field="course",
            foreign_key_value=sample_course.id,
            limit=10,
            page=1,
        )
        assert result["pageDetails"]["totalCount"] == 1
        assert result["items"][0].id == visible.id

    def test_empty_when_no_permissions(
        self,
        db_session,
        active_user,
        system_user,
        sample_course,
        event_statuses,
    ):
        status_id = event_statuses["Geplant"].id
        self._create_event(
            db_session, system_user, "FKA-NoP", sample_course.id, status_id
        )

        request = create_mock_request(active_user)
        result = self.crud.get_multi_foreign_key_auth(
            db_session,
            request,
            foreign_key_field="course",
            foreign_key_value=sample_course.id,
            limit=10,
            page=1,
        )
        assert result["pageDetails"]["totalCount"] == 0

    def test_invalid_fk_field_raises(
        self, db_session, active_user, system_user
    ):
        request = create_mock_request(active_user)
        with pytest.raises(ModelFieldNotFound):
            self.crud.get_multi_foreign_key_auth(
                db_session,
                request,
                foreign_key_field="nonexistent",
                foreign_key_value=uuid.uuid4(),
                limit=10,
                page=1,
            )

    def test_respects_pagination(
        self,
        db_session,
        active_user,
        system_user,
        sample_course,
        event_statuses,
    ):
        status_id = event_statuses["Geplant"].id
        for i in range(5):
            e = self._create_event(
                db_session,
                system_user,
                f"FKAP{i:03d}",
                sample_course.id,
                status_id,
            )
            self._grant_event_permission(
                db_session, system_user, active_user, e
            )

        request = create_mock_request(active_user)
        result = self.crud.get_multi_foreign_key_auth(
            db_session,
            request,
            foreign_key_field="course",
            foreign_key_value=sample_course.id,
            limit=2,
            page=1,
        )
        assert len(result["items"]) == 2
        assert result["pageDetails"]["totalCount"] == 5

    def test_search_within_fk_auth_filter(
        self,
        db_session,
        active_user,
        system_user,
        sample_course,
        event_statuses,
    ):
        status_id = event_statuses["Geplant"].id
        e1 = self._create_event(
            db_session, system_user, "FKAS-Al", sample_course.id, status_id
        )
        e2 = self._create_event(
            db_session, system_user, "FKAS-Be", sample_course.id, status_id
        )
        self._grant_event_permission(db_session, system_user, active_user, e1)
        self._grant_event_permission(db_session, system_user, active_user, e2)

        request = create_mock_request(active_user)
        result = self.crud.get_multi_foreign_key_auth(
            db_session,
            request,
            foreign_key_field="course",
            foreign_key_value=sample_course.id,
            limit=10,
            page=1,
            search_field="name",
            search_value="FKAS-Al",
        )
        assert result["pageDetails"]["totalCount"] == 1
        assert result["items"][0].name == "FKAS-Al"


class TestCRUDBaseGetMultiAssociation:
    """Tests for get_multi_association() - listing through a M2M association table.

    Uses Course <-> Template via course_template_association_table.
    The CRUDBase is initialised with Course, and we query courses that are
    associated to a specific Template through the 'templates' relationship.
    """

    def setup_method(self):
        self.crud = CRUDBase(Course)

    def _create_template(self, db_session, system_user, name):
        now = datetime.now(timezone.utc)
        tpl = Template(
            id=uuid.uuid4(),
            name=name,
            description=f"Desc {name}",
            cpu=2,
            ram=2048,
            disk=20,
            prevent_delete=False,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(tpl)
        db_session.flush()
        return tpl

    def _create_course(self, db_session, system_user, name):
        now = datetime.now(timezone.utc)
        course = Course(
            id=uuid.uuid4(),
            name=name,
            description=f"Desc {name}",
            guacamole=True,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(course)
        db_session.flush()
        return course

    def _link_course_template(self, db_session, course, template):
        db_session.execute(
            course_template_association_table.insert().values(
                course_id=course.id, template_id=template.id
            )
        )
        db_session.flush()

    def test_returns_courses_associated_with_template(
        self, db_session, system_user
    ):
        tpl = self._create_template(db_session, system_user, "Assoc Tpl")
        c1 = self._create_course(db_session, system_user, "Assoc C1")
        c2 = self._create_course(db_session, system_user, "Assoc C2")
        self._link_course_template(db_session, c1, tpl)
        self._link_course_template(db_session, c2, tpl)

        result = self.crud.get_multi_association(
            db_session,
            child_model=Template,
            parent_field_name="templates",
            child_field_name="id",
            field_value=tpl.id,
            limit=10,
            page=1,
        )
        assert result["pageDetails"]["totalCount"] == 2
        result_ids = {item.id for item in result["items"]}
        assert c1.id in result_ids
        assert c2.id in result_ids

    def test_excludes_courses_not_linked_to_template(
        self, db_session, system_user
    ):
        tpl = self._create_template(db_session, system_user, "Assoc Tpl2")
        linked = self._create_course(db_session, system_user, "Assoc Linked")
        self._create_course(db_session, system_user, "Assoc Unlinked")
        self._link_course_template(db_session, linked, tpl)

        result = self.crud.get_multi_association(
            db_session,
            child_model=Template,
            parent_field_name="templates",
            child_field_name="id",
            field_value=tpl.id,
            limit=10,
            page=1,
        )
        assert result["pageDetails"]["totalCount"] == 1
        assert result["items"][0].id == linked.id

    def test_invalid_parent_field_raises(self, db_session, system_user):
        with pytest.raises(ModelFieldNotFound):
            self.crud.get_multi_association(
                db_session,
                child_model=Template,
                parent_field_name="nonexistent_relation",
                child_field_name="id",
                field_value=uuid.uuid4(),
                limit=10,
                page=1,
            )

    def test_empty_result_when_no_associations(self, db_session, system_user):
        tpl = self._create_template(db_session, system_user, "Assoc Empty")
        result = self.crud.get_multi_association(
            db_session,
            child_model=Template,
            parent_field_name="templates",
            child_field_name="id",
            field_value=tpl.id,
            limit=10,
            page=1,
        )
        assert result["pageDetails"]["totalCount"] == 0
        assert result["items"] == []

    def test_respects_pagination(self, db_session, system_user):
        tpl = self._create_template(db_session, system_user, "Assoc PagTpl")
        for i in range(5):
            c = self._create_course(db_session, system_user, f"AssocPag{i:03d}")
            self._link_course_template(db_session, c, tpl)

        result = self.crud.get_multi_association(
            db_session,
            child_model=Template,
            parent_field_name="templates",
            child_field_name="id",
            field_value=tpl.id,
            limit=2,
            page=1,
        )
        assert len(result["items"]) == 2
        assert result["pageDetails"]["totalCount"] == 5
        assert result["pageDetails"]["pageCount"] == 3

    def test_search_within_association(self, db_session, system_user):
        tpl = self._create_template(db_session, system_user, "Assoc SearchTpl")
        c1 = self._create_course(db_session, system_user, "AssocSrch Alpha")
        c2 = self._create_course(db_session, system_user, "AssocSrch Beta")
        self._link_course_template(db_session, c1, tpl)
        self._link_course_template(db_session, c2, tpl)

        result = self.crud.get_multi_association(
            db_session,
            child_model=Template,
            parent_field_name="templates",
            child_field_name="id",
            field_value=tpl.id,
            limit=10,
            page=1,
            search_field="name",
            search_value="Alpha",
        )
        assert result["pageDetails"]["totalCount"] == 1
        assert result["items"][0].name == "AssocSrch Alpha"


class TestCRUDBaseGetMultiAssociationAuth:
    """Tests for get_multi_association_auth() - M2M + ObjectPermission filter.

    Same setup as TestCRUDBaseGetMultiAssociation but also requires
    ObjectPermission for the user to see the course.
    """

    def setup_method(self):
        self.crud = CRUDBase(Course)

    def _create_template(self, db_session, system_user, name):
        now = datetime.now(timezone.utc)
        tpl = Template(
            id=uuid.uuid4(),
            name=name,
            description=f"Desc {name}",
            cpu=2,
            ram=2048,
            disk=20,
            prevent_delete=False,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(tpl)
        db_session.flush()
        return tpl

    def _create_course(self, db_session, system_user, name):
        now = datetime.now(timezone.utc)
        course = Course(
            id=uuid.uuid4(),
            name=name,
            description=f"Desc {name}",
            guacamole=True,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(course)
        db_session.flush()
        return course

    def _link_course_template(self, db_session, course, template):
        db_session.execute(
            course_template_association_table.insert().values(
                course_id=course.id, template_id=template.id
            )
        )
        db_session.flush()

    def _grant_course_permission(
        self, db_session, system_user, user, course, perm_key="object_read"
    ):
        now = datetime.now(timezone.utc)
        op = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Course",
            object_id=course.id,
            entity_id=user.id,
            entity_type="User",
            permission_key=perm_key,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(op)
        db_session.flush()
        return op

    def test_returns_only_permitted_associated_courses(
        self, db_session, active_user, system_user
    ):
        tpl = self._create_template(db_session, system_user, "AssocAuth Tpl")
        visible = self._create_course(db_session, system_user, "AssocAuth Vis")
        hidden = self._create_course(db_session, system_user, "AssocAuth Hid")
        self._link_course_template(db_session, visible, tpl)
        self._link_course_template(db_session, hidden, tpl)
        self._grant_course_permission(
            db_session, system_user, active_user, visible
        )

        request = create_mock_request(active_user)
        result = self.crud.get_multi_association_auth(
            db_session,
            request,
            child_model=Template,
            parent_field_name="templates",
            child_field_name="id",
            field_value=tpl.id,
            limit=10,
            page=1,
        )
        assert result["pageDetails"]["totalCount"] == 1
        assert result["items"][0].id == visible.id

    def test_empty_when_associated_but_no_permission(
        self, db_session, active_user, system_user
    ):
        tpl = self._create_template(db_session, system_user, "AssocAuth NoPerm")
        c = self._create_course(db_session, system_user, "AssocAuth NoPCourse")
        self._link_course_template(db_session, c, tpl)

        request = create_mock_request(active_user)
        result = self.crud.get_multi_association_auth(
            db_session,
            request,
            child_model=Template,
            parent_field_name="templates",
            child_field_name="id",
            field_value=tpl.id,
            limit=10,
            page=1,
        )
        assert result["pageDetails"]["totalCount"] == 0

    def test_invalid_parent_field_raises(
        self, db_session, active_user, system_user
    ):
        request = create_mock_request(active_user)
        with pytest.raises(ModelFieldNotFound):
            self.crud.get_multi_association_auth(
                db_session,
                request,
                child_model=Template,
                parent_field_name="nonexistent",
                child_field_name="id",
                field_value=uuid.uuid4(),
                limit=10,
                page=1,
            )

    def test_respects_pagination(self, db_session, active_user, system_user):
        tpl = self._create_template(db_session, system_user, "AAP Tpl")
        for i in range(5):
            c = self._create_course(db_session, system_user, f"AAP C{i:03d}")
            self._link_course_template(db_session, c, tpl)
            self._grant_course_permission(
                db_session, system_user, active_user, c
            )

        request = create_mock_request(active_user)
        result = self.crud.get_multi_association_auth(
            db_session,
            request,
            child_model=Template,
            parent_field_name="templates",
            child_field_name="id",
            field_value=tpl.id,
            limit=2,
            page=1,
        )
        assert len(result["items"]) == 2
        assert result["pageDetails"]["totalCount"] == 5

    def test_search_within_association_auth(
        self, db_session, active_user, system_user
    ):
        tpl = self._create_template(db_session, system_user, "AAS Tpl")
        c1 = self._create_course(db_session, system_user, "AAS Alpha")
        c2 = self._create_course(db_session, system_user, "AAS Beta")
        self._link_course_template(db_session, c1, tpl)
        self._link_course_template(db_session, c2, tpl)
        self._grant_course_permission(db_session, system_user, active_user, c1)
        self._grant_course_permission(db_session, system_user, active_user, c2)

        request = create_mock_request(active_user)
        result = self.crud.get_multi_association_auth(
            db_session,
            request,
            child_model=Template,
            parent_field_name="templates",
            child_field_name="id",
            field_value=tpl.id,
            limit=10,
            page=1,
            search_field="name",
            search_value="Alpha",
        )
        assert result["pageDetails"]["totalCount"] == 1
        assert result["items"][0].name == "AAS Alpha"

    def test_role_permission_grants_access(
        self, db_session, active_user, system_user, role_admin
    ):
        tpl = self._create_template(db_session, system_user, "AAR Tpl")
        c = self._create_course(db_session, system_user, "AAR RoleCourse")
        self._link_course_template(db_session, c, tpl)

        # Assign user to role
        db_session.execute(
            user_role_association_table.insert().values(
                user_id=active_user.id, role_id=role_admin.id
            )
        )
        # Grant role permission on course
        now = datetime.now(timezone.utc)
        op = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Course",
            object_id=c.id,
            entity_id=role_admin.id,
            entity_type="Role",
            permission_key="object_full",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(op)
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_multi_association_auth(
            db_session,
            request,
            child_model=Template,
            parent_field_name="templates",
            child_field_name="id",
            field_value=tpl.id,
            limit=10,
            page=1,
        )
        assert result["pageDetails"]["totalCount"] == 1
        assert result["items"][0].id == c.id


class TestCRUDBaseDeleteChildList:
    """Tests for _delete_child_list() - deletes a list of child objects from the DB."""

    def setup_method(self):
        self.crud = CRUDBase(Course)

    def _create_course(self, db_session, system_user, name):
        now = datetime.now(timezone.utc)
        course = Course(
            id=uuid.uuid4(),
            name=name,
            description=f"Desc {name}",
            guacamole=True,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(course)
        db_session.flush()
        return course

    def test_deletes_all_objects_in_list(self, db_session, system_user):
        c1 = self._create_course(db_session, system_user, "DelChild 1")
        c2 = self._create_course(db_session, system_user, "DelChild 2")
        c3 = self._create_course(db_session, system_user, "DelChild 3")

        self.crud._delete_child_list(db_session, [c1, c2, c3])
        db_session.flush()

        assert db_session.get(Course, c1.id) is None
        assert db_session.get(Course, c2.id) is None
        assert db_session.get(Course, c3.id) is None

    def test_empty_list_does_nothing(self, db_session, system_user):
        c = self._create_course(db_session, system_user, "DelChild Keep")
        self.crud._delete_child_list(db_session, [])
        db_session.flush()
        assert db_session.get(Course, c.id) is not None

    def test_preserves_objects_not_in_list(self, db_session, system_user):
        to_delete = self._create_course(db_session, system_user, "DelChild Del")
        to_keep = self._create_course(db_session, system_user, "DelChild Keep2")

        self.crud._delete_child_list(db_session, [to_delete])
        db_session.flush()

        assert db_session.get(Course, to_delete.id) is None
        assert db_session.get(Course, to_keep.id) is not None

    def test_single_item_list(self, db_session, system_user):
        c = self._create_course(db_session, system_user, "DelChild Single")
        self.crud._delete_child_list(db_session, [c])
        db_session.flush()
        assert db_session.get(Course, c.id) is None
