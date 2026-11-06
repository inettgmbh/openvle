"""Tests for controllers/tags.py - CRUDTag operations."""

import uuid
from datetime import datetime, timezone

import pytest
from controllers.tags import CRUDTag
from core.exceptions import ModelNotFound, ObjectNotFound
from models import (
    Application,
    ObjectPermission,
    Tag as TagModel,
    Template,
    Vendor,
    VirtualMachine,
)
from schemas.tags import TagCreate

from tests.helpers.mock_request import create_mock_request


@pytest.fixture()
def sample_vendor_tag(db_session, system_user):
    now = datetime.now(timezone.utc)
    vendor = Vendor(
        id=uuid.uuid4(),
        name="Tag Vendor",
        description="Vendor for tag tests",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vendor)
    db_session.flush()
    return vendor


@pytest.fixture()
def sample_app_tag(db_session, system_user, sample_vendor_tag):
    now = datetime.now(timezone.utc)
    app = Application(
        id=uuid.uuid4(),
        key="tag-app",
        name="Tag App",
        vendor=sample_vendor_tag.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(app)
    db_session.flush()
    return app


class TestCRUDTagCreate:
    def setup_method(self):
        self.crud = CRUDTag(TagModel)

    def test_create_tag(self, db_session, active_user, sample_app_tag):
        request = create_mock_request(active_user)
        obj_in = TagCreate(
            key="env",
            value="production",
            objectId=str(sample_app_tag.id),
            objectType="Application",
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)
        assert result.key == "env"
        assert result.value == "production"
        assert result.objectType == "Application"

    def test_create_invalid_object_type_raises(self, db_session, active_user):
        request = create_mock_request(active_user)
        obj_in = TagCreate(
            key="env",
            value="test",
            objectId=str(uuid.uuid4()),
            objectType="FakeModel",
        )
        with pytest.raises(ModelNotFound):
            self.crud.create(db_session, request, obj_in=obj_in)

    def test_create_nonexistent_object_raises(self, db_session, active_user):
        request = create_mock_request(active_user)
        obj_in = TagCreate(
            key="env",
            value="test",
            objectId=str(uuid.uuid4()),
            objectType="Application",
        )
        with pytest.raises(ObjectNotFound):
            self.crud.create(db_session, request, obj_in=obj_in)


class TestCRUDTagGetMultiAuth:
    def setup_method(self):
        self.crud = CRUDTag(TagModel)

    def test_returns_authorized_tags(
        self, db_session, active_user, sample_app_tag
    ):
        """Tags are visible when user has ObjectPermission on the tagged object."""
        now = datetime.now(timezone.utc)
        # Create tag
        tag = TagModel(
            id=uuid.uuid4(),
            key="env",
            value="staging",
            objectId=sample_app_tag.id,
            objectType="Application",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(tag)

        # Grant permission
        perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Application",
            object_id=sample_app_tag.id,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_full",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(perm)
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_multi_auth(db_session, request)
        tag_ids = [t.id for t in result["items"]]
        assert tag.id in tag_ids

    def test_returns_empty_without_permissions(
        self, db_session, active_user, sample_app_tag
    ):
        now = datetime.now(timezone.utc)
        tag = TagModel(
            id=uuid.uuid4(),
            key="env",
            value="hidden",
            objectId=sample_app_tag.id,
            objectType="Application",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(tag)
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_multi_auth(db_session, request)
        assert len(result["items"]) == 0


class TestCRUDTagDelete:
    def setup_method(self):
        self.crud = CRUDTag(TagModel)

    def test_delete_tag(self, db_session, active_user, sample_app_tag):
        request = create_mock_request(active_user)
        # Create tag first
        obj_in = TagCreate(
            key="delete-me",
            value="yes",
            objectId=str(sample_app_tag.id),
            objectType="Application",
        )
        tag = self.crud.create(db_session, request, obj_in=obj_in)

        result = self.crud.delete(db_session, id=tag.id, request=request)
        assert "deleted" in result["detail"]


class TestConversions:
    def setup_method(self):
        self.crud = CRUDTag(TagModel)

    def test_convert_pve_to_kvs(self):
        pve_tags = "env_production, os_linux, role_web"
        result = self.crud._convert_pve_to_kvs(pve_tags)
        assert len(result) == 3
        assert {"env": "production"} in result
        assert {"os": "linux"} in result
        assert {"role": "web"} in result

    def test_convert_pve_to_kvs_empty(self):
        result = self.crud._convert_pve_to_kvs("")
        assert result == []

    def test_convert_pve_to_kvs_none(self):
        result = self.crud._convert_pve_to_kvs(None)
        assert result == []

    def test_convert_pve_to_kvs_invalid_format(self):
        """Tags without underscore are skipped."""
        pve_tags = "notag, env_prod"
        result = self.crud._convert_pve_to_kvs(pve_tags)
        assert len(result) == 1
        assert {"env": "prod"} in result

    def test_convert_pve_to_kvs_multiple_underscores(self):
        """Only split on first underscore."""
        pve_tags = "env_prod_us_east"
        result = self.crud._convert_pve_to_kvs(pve_tags)
        assert len(result) == 1
        assert {"env": "prod_us_east"} in result

    def test_convert_kvs_to_pve(self, db_session, system_user, sample_app_tag):
        now = datetime.now(timezone.utc)
        tag = TagModel(
            id=uuid.uuid4(),
            key="env",
            value="production",
            objectId=sample_app_tag.id,
            objectType="Application",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(tag)
        db_session.flush()

        result = self.crud._convert_kvs_to_pve(
            db_session,
            objectId=sample_app_tag.id,
            objectType="Application",
        )
        assert "env_production" in result

    def test_convert_kvs_to_pve_empty(self, db_session, system_user):
        result = self.crud._convert_kvs_to_pve(
            db_session,
            objectId=uuid.uuid4(),
            objectType="Application",
        )
        assert result is None or result == []


class TestCRUDTagGetTagsForObjectAuth:
    """Tests for get_tags_for_object_auth() - retrieve tags for a specific
    object filtered by the requesting user's permissions."""

    def setup_method(self):
        self.crud = CRUDTag(TagModel)

    def test_returns_tags_when_user_has_permission(
        self, db_session, active_user, sample_app_tag, mock_permission_allow
    ):
        """User with permission on the object sees its tags."""
        now = datetime.now(timezone.utc)
        tag = TagModel(
            id=uuid.uuid4(),
            key="env",
            value="staging",
            objectId=sample_app_tag.id,
            objectType="Application",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(tag)
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_tags_for_object_auth(
            request=request,
            objectId=sample_app_tag.id,
            objectType="Application",
            db=db_session,
        )
        tag_ids = [t.id for t in result["items"]]
        assert tag.id in tag_ids

    def test_returns_empty_when_user_lacks_permission(
        self, db_session, active_user, sample_app_tag
    ):
        """User without permission on the object sees no tags."""
        now = datetime.now(timezone.utc)
        tag = TagModel(
            id=uuid.uuid4(),
            key="env",
            value="secret",
            objectId=sample_app_tag.id,
            objectType="Application",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(tag)
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_tags_for_object_auth(
            request=request,
            objectId=sample_app_tag.id,
            objectType="Application",
            db=db_session,
        )
        assert len(result["items"]) == 0

    def test_invalid_object_type_raises(self, db_session, active_user):
        """Requesting tags for an unknown objectType raises ModelNotFound."""
        request = create_mock_request(active_user)
        with pytest.raises(ModelNotFound):
            self.crud.get_tags_for_object_auth(
                request=request,
                objectId=uuid.uuid4(),
                objectType="NonExistentModel",
                db=db_session,
            )

    def test_returns_only_tags_for_requested_object(
        self, db_session, active_user, sample_app_tag, mock_permission_allow
    ):
        """Only tags matching the requested objectId/objectType are returned."""
        now = datetime.now(timezone.utc)
        # Tag on the target object
        tag_target = TagModel(
            id=uuid.uuid4(),
            key="env",
            value="target",
            objectId=sample_app_tag.id,
            objectType="Application",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        # Tag on a different object (different objectId)
        other_app_id = uuid.uuid4()
        tag_other = TagModel(
            id=uuid.uuid4(),
            key="env",
            value="other",
            objectId=other_app_id,
            objectType="Application",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add_all([tag_target, tag_other])
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_tags_for_object_auth(
            request=request,
            objectId=sample_app_tag.id,
            objectType="Application",
            db=db_session,
        )
        tag_ids = [t.id for t in result["items"]]
        assert tag_target.id in tag_ids
        assert tag_other.id not in tag_ids

    def test_pagination_metadata(
        self, db_session, active_user, sample_app_tag, mock_permission_allow
    ):
        """Result includes pagination metadata."""
        now = datetime.now(timezone.utc)
        for i in range(3):
            tag = TagModel(
                id=uuid.uuid4(),
                key=f"key{i}",
                value=f"val{i}",
                objectId=sample_app_tag.id,
                objectType="Application",
                createdAt=now,
                updatedAt=now,
                createdById=active_user.id,
                updatedById=active_user.id,
            )
            db_session.add(tag)
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_tags_for_object_auth(
            request=request,
            objectId=sample_app_tag.id,
            objectType="Application",
            db=db_session,
            limit=2,
            page=1,
        )
        assert result["pageDetails"]["totalCount"] == 3
        assert len(result["items"]) == 2


class TestCRUDTagGetTagsKeyValueAuth:
    """Tests for get_tags_key_value_auth() - retrieve tags filtered by
    key+value with object permission filtering."""

    def setup_method(self):
        self.crud = CRUDTag(TagModel)

    def test_returns_matching_tags_when_authorized(
        self, db_session, active_user, sample_app_tag
    ):
        """Tags with matching key+value are returned when user has permission."""
        now = datetime.now(timezone.utc)
        tag = TagModel(
            id=uuid.uuid4(),
            key="env",
            value="production",
            objectId=sample_app_tag.id,
            objectType="Application",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(tag)

        perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Application",
            object_id=sample_app_tag.id,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_full",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(perm)
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_tags_key_value_auth(
            request=request,
            key="env",
            value="production",
            db=db_session,
        )
        tag_ids = [t.id for t in result["items"]]
        assert tag.id in tag_ids

    def test_excludes_tags_with_different_value(
        self, db_session, active_user, sample_app_tag
    ):
        """Tags with the same key but different value are excluded."""
        now = datetime.now(timezone.utc)
        tag_prod = TagModel(
            id=uuid.uuid4(),
            key="env",
            value="production",
            objectId=sample_app_tag.id,
            objectType="Application",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        tag_staging = TagModel(
            id=uuid.uuid4(),
            key="env",
            value="staging",
            objectId=sample_app_tag.id,
            objectType="Application",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Application",
            object_id=sample_app_tag.id,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_read",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add_all([tag_prod, tag_staging, perm])
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_tags_key_value_auth(
            request=request,
            key="env",
            value="production",
            db=db_session,
        )
        tag_ids = [t.id for t in result["items"]]
        assert tag_prod.id in tag_ids
        assert tag_staging.id not in tag_ids

    def test_returns_empty_without_permissions(
        self, db_session, active_user, sample_app_tag
    ):
        """Tags are hidden when the user has no ObjectPermission."""
        now = datetime.now(timezone.utc)
        tag = TagModel(
            id=uuid.uuid4(),
            key="env",
            value="production",
            objectId=sample_app_tag.id,
            objectType="Application",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(tag)
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_tags_key_value_auth(
            request=request,
            key="env",
            value="production",
            db=db_session,
        )
        assert len(result["items"]) == 0

    def test_returns_empty_when_no_tags_match_key_value(
        self, db_session, active_user, sample_app_tag
    ):
        """Empty result when no tags match the requested key+value."""
        now = datetime.now(timezone.utc)
        tag = TagModel(
            id=uuid.uuid4(),
            key="region",
            value="eu-west",
            objectId=sample_app_tag.id,
            objectType="Application",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Application",
            object_id=sample_app_tag.id,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_full",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add_all([tag, perm])
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_tags_key_value_auth(
            request=request,
            key="env",
            value="production",
            db=db_session,
        )
        assert len(result["items"]) == 0


class TestCRUDTagGetTagsKeyAuth:
    """Tests for get_tags_key_auth() - retrieve tags filtered by key
    with object permission filtering."""

    def setup_method(self):
        self.crud = CRUDTag(TagModel)

    def test_returns_all_values_for_key_when_authorized(
        self, db_session, active_user, sample_app_tag
    ):
        """All tags with the given key are returned when user is authorized."""
        now = datetime.now(timezone.utc)
        tag_prod = TagModel(
            id=uuid.uuid4(),
            key="env",
            value="production",
            objectId=sample_app_tag.id,
            objectType="Application",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        tag_staging = TagModel(
            id=uuid.uuid4(),
            key="env",
            value="staging",
            objectId=sample_app_tag.id,
            objectType="Application",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Application",
            object_id=sample_app_tag.id,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_full",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add_all([tag_prod, tag_staging, perm])
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_tags_key_auth(
            request=request,
            key="env",
            db=db_session,
        )
        tag_ids = [t.id for t in result["items"]]
        assert tag_prod.id in tag_ids
        assert tag_staging.id in tag_ids

    def test_excludes_tags_with_different_key(
        self, db_session, active_user, sample_app_tag
    ):
        """Tags with a different key are excluded from results."""
        now = datetime.now(timezone.utc)
        tag_env = TagModel(
            id=uuid.uuid4(),
            key="env",
            value="production",
            objectId=sample_app_tag.id,
            objectType="Application",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        tag_region = TagModel(
            id=uuid.uuid4(),
            key="region",
            value="eu-west",
            objectId=sample_app_tag.id,
            objectType="Application",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Application",
            object_id=sample_app_tag.id,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_full",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add_all([tag_env, tag_region, perm])
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_tags_key_auth(
            request=request,
            key="env",
            db=db_session,
        )
        tag_ids = [t.id for t in result["items"]]
        assert tag_env.id in tag_ids
        assert tag_region.id not in tag_ids

    def test_returns_empty_without_permissions(
        self, db_session, active_user, sample_app_tag
    ):
        """Tags are hidden when user has no ObjectPermission."""
        now = datetime.now(timezone.utc)
        tag = TagModel(
            id=uuid.uuid4(),
            key="env",
            value="production",
            objectId=sample_app_tag.id,
            objectType="Application",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(tag)
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_tags_key_auth(
            request=request,
            key="env",
            db=db_session,
        )
        assert len(result["items"]) == 0

    def test_returns_empty_when_no_tags_match_key(
        self, db_session, active_user, sample_app_tag
    ):
        """Empty result when no tags have the requested key."""
        now = datetime.now(timezone.utc)
        tag = TagModel(
            id=uuid.uuid4(),
            key="region",
            value="eu-west",
            objectId=sample_app_tag.id,
            objectType="Application",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        perm = ObjectPermission(
            id=uuid.uuid4(),
            object_type="Application",
            object_id=sample_app_tag.id,
            entity_id=active_user.id,
            entity_type="User",
            permission_key="object_full",
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add_all([tag, perm])
        db_session.flush()

        request = create_mock_request(active_user)
        result = self.crud.get_tags_key_auth(
            request=request,
            key="env",
            db=db_session,
        )
        assert len(result["items"]) == 0


class TestCRUDTagCreateForPveTagsList:
    """Tests for _create_for_pve_tags_list() - create Tag records from
    a Proxmox-style tags string or pre-converted kvs_tags list."""

    def setup_method(self):
        self.crud = CRUDTag(TagModel)

    def test_creates_tags_from_pve_string(
        self, db_session, system_user, sample_app_tag
    ):
        """Tags are created in DB from a comma-separated PVE tags string."""
        result = self.crud._create_for_pve_tags_list(
            db=db_session,
            objectId=sample_app_tag.id,
            objectType="Application",
            pve_tags="env_production, role_web",
        )
        assert len(result) == 2
        keys = {t.key for t in result}
        values = {t.value for t in result}
        assert "env" in keys
        assert "role" in keys
        assert "production" in values
        assert "web" in values
        # Verify they are persisted
        for tag in result:
            assert tag.id is not None
            assert tag.objectId == sample_app_tag.id
            assert tag.objectType == "Application"

    def test_creates_tags_from_kvs_tags_list(
        self, db_session, system_user, sample_app_tag
    ):
        """Tags are created when a pre-converted kvs_tags list is provided."""
        kvs_tags = [{"env": "staging"}, {"tier": "frontend"}]
        result = self.crud._create_for_pve_tags_list(
            db=db_session,
            objectId=sample_app_tag.id,
            objectType="Application",
            kvs_tags=kvs_tags,
        )
        assert len(result) == 2
        key_value_pairs = {(t.key, t.value) for t in result}
        assert ("env", "staging") in key_value_pairs
        assert ("tier", "frontend") in key_value_pairs

    def test_returns_empty_list_for_empty_pve_string(
        self, db_session, system_user, sample_app_tag
    ):
        """An empty PVE tags string produces no tags."""
        result = self.crud._create_for_pve_tags_list(
            db=db_session,
            objectId=sample_app_tag.id,
            objectType="Application",
            pve_tags="",
        )
        assert result == []

    def test_returns_empty_list_for_none_pve_string(
        self, db_session, system_user, sample_app_tag
    ):
        """None PVE tags string produces no tags."""
        result = self.crud._create_for_pve_tags_list(
            db=db_session,
            objectId=sample_app_tag.id,
            objectType="Application",
            pve_tags=None,
        )
        assert result == []

    def test_tags_assigned_to_system_user(
        self, db_session, system_user, sample_app_tag
    ):
        """Created tags are attributed to the system user."""
        result = self.crud._create_for_pve_tags_list(
            db=db_session,
            objectId=sample_app_tag.id,
            objectType="Application",
            pve_tags="env_dev",
        )
        assert len(result) == 1
        assert result[0].createdById == system_user.id
        assert result[0].updatedById == system_user.id

    def test_skips_invalid_pve_tags(
        self, db_session, system_user, sample_app_tag
    ):
        """PVE tags without underscore are skipped; valid ones are created."""
        result = self.crud._create_for_pve_tags_list(
            db=db_session,
            objectId=sample_app_tag.id,
            objectType="Application",
            pve_tags="notag, env_prod",
        )
        assert len(result) == 1
        assert result[0].key == "env"
        assert result[0].value == "prod"

    def test_multiple_underscores_split_on_first(
        self, db_session, system_user, sample_app_tag
    ):
        """PVE tags with multiple underscores split only on the first one."""
        result = self.crud._create_for_pve_tags_list(
            db=db_session,
            objectId=sample_app_tag.id,
            objectType="Application",
            pve_tags="env_prod_us_east",
        )
        assert len(result) == 1
        assert result[0].key == "env"
        assert result[0].value == "prod_us_east"


class TestCRUDTagInheritTags:
    """Tests for _inherit_tags() - copy tags from a source object
    (e.g. Template) to a target object (e.g. VirtualMachine)."""

    def setup_method(self):
        self.crud = CRUDTag(TagModel)

    @pytest.fixture()
    def source_template(self, db_session, system_user):
        """Create a Template as the source object for tag inheritance."""
        now = datetime.now(timezone.utc)
        tpl = Template(
            id=uuid.uuid4(),
            name="source-tpl",
            status="available",
            proxmoxId=100,
            proxmoxNode="pve-node-1",
            cpu=2,
            ram=2048,
            disk=32,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(tpl)
        db_session.flush()
        return tpl

    @pytest.fixture()
    def target_vm(self, db_session, system_user, source_template):
        """Create a VirtualMachine as the target for tag inheritance."""
        now = datetime.now(timezone.utc)
        vm = VirtualMachine(
            id=uuid.uuid4(),
            name="target-vm",
            status="stopped",
            proxmoxId=200,
            proxmoxNode="pve-node-1",
            cpu=2,
            ram=2048,
            disk=32,
            template=source_template.id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(vm)
        db_session.flush()
        return vm

    def test_inherits_all_tags_from_source(
        self, db_session, system_user, source_template, target_vm
    ):
        """All tags from the source object are copied to the target."""
        now = datetime.now(timezone.utc)
        tag1 = TagModel(
            id=uuid.uuid4(),
            key="env",
            value="production",
            objectId=source_template.id,
            objectType="Template",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        tag2 = TagModel(
            id=uuid.uuid4(),
            key="role",
            value="web",
            objectId=source_template.id,
            objectType="Template",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add_all([tag1, tag2])
        db_session.flush()

        result = self.crud._inherit_tags(
            db=db_session,
            source_object_id=source_template.id,
            target_object_id=target_vm.id,
            source_object_type="Template",
            target_object_type="VirtualMachine",
        )
        assert len(result) == 2
        key_value_pairs = {(t.key, t.value) for t in result}
        assert ("env", "production") in key_value_pairs
        assert ("role", "web") in key_value_pairs
        # Verify tags are assigned to the target object
        for tag in result:
            assert tag.objectId == target_vm.id
            assert tag.objectType == "VirtualMachine"

    def test_inherited_tags_have_new_ids(
        self, db_session, system_user, source_template, target_vm
    ):
        """Inherited tags get new UUIDs, not the source tag IDs."""
        now = datetime.now(timezone.utc)
        source_tag = TagModel(
            id=uuid.uuid4(),
            key="env",
            value="dev",
            objectId=source_template.id,
            objectType="Template",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(source_tag)
        db_session.flush()

        result = self.crud._inherit_tags(
            db=db_session,
            source_object_id=source_template.id,
            target_object_id=target_vm.id,
            source_object_type="Template",
            target_object_type="VirtualMachine",
        )
        assert len(result) == 1
        assert result[0].id != source_tag.id

    def test_returns_empty_when_source_has_no_tags(
        self, db_session, system_user, source_template, target_vm
    ):
        """No tags are created when the source object has no tags."""
        result = self.crud._inherit_tags(
            db=db_session,
            source_object_id=source_template.id,
            target_object_id=target_vm.id,
            source_object_type="Template",
            target_object_type="VirtualMachine",
        )
        assert result == []

    def test_source_tags_remain_unchanged(
        self, db_session, system_user, source_template, target_vm
    ):
        """Inheriting tags does not modify or delete the source tags."""
        now = datetime.now(timezone.utc)
        source_tag = TagModel(
            id=uuid.uuid4(),
            key="env",
            value="production",
            objectId=source_template.id,
            objectType="Template",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(source_tag)
        db_session.flush()

        self.crud._inherit_tags(
            db=db_session,
            source_object_id=source_template.id,
            target_object_id=target_vm.id,
            source_object_type="Template",
            target_object_type="VirtualMachine",
        )

        # Verify source tag still exists
        original = db_session.get(TagModel, source_tag.id)
        assert original is not None
        assert original.key == "env"
        assert original.value == "production"
        assert original.objectId == source_template.id

    def test_inherit_preserves_key_value_pairs(
        self, db_session, system_user, source_template, target_vm
    ):
        """Key-value pairs are faithfully copied from source to target."""
        now = datetime.now(timezone.utc)
        tags_data = [
            ("os", "linux"),
            ("tier", "backend"),
            ("region", "eu_central_1"),
        ]
        for key, value in tags_data:
            tag = TagModel(
                id=uuid.uuid4(),
                key=key,
                value=value,
                objectId=source_template.id,
                objectType="Template",
                createdAt=now,
                updatedAt=now,
                createdById=system_user.id,
                updatedById=system_user.id,
            )
            db_session.add(tag)
        db_session.flush()

        result = self.crud._inherit_tags(
            db=db_session,
            source_object_id=source_template.id,
            target_object_id=target_vm.id,
            source_object_type="Template",
            target_object_type="VirtualMachine",
        )
        assert len(result) == 3
        result_pairs = {(t.key, t.value) for t in result}
        for key, value in tags_data:
            assert (key, value) in result_pairs
