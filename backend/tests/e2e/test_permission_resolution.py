"""
E2E workflow tests for permission resolution.

Tests object permissions, permission hierarchy, fallthrough pattern
(filtered lists), role-based permissions, and protected objects.
"""

import uuid
from datetime import date, datetime, time, timezone

from tests.e2e.conftest import API

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _create_event_via_db(db_session, system_user, event_statuses, course):
    """Create an event directly in DB."""
    from models import Event

    now = datetime.now(timezone.utc)
    event = Event(
        id=uuid.uuid4(),
        name=f"Perm Event {uuid.uuid4().hex[:6]}",
        slug=f"pe-{uuid.uuid4().hex[:4]}",
        description="Event for permission tests",
        dateStart=date(2026, 8, 1),
        dateEnd=date(2026, 8, 31),
        timeStart=time(8, 0),
        timeEnd=time(18, 0),
        guacamole=False,
        status=event_statuses["Geplant"].id,
        course=course.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(event)
    db_session.flush()
    return event


def _create_object_permission(
    db_session,
    system_user,
    object_type,
    object_id,
    entity_id,
    entity_type="User",
    permission_key="object_full",
):
    """Create ObjectPermission directly in DB."""
    from models import ObjectPermission

    now = datetime.now(timezone.utc)
    perm = ObjectPermission(
        id=uuid.uuid4(),
        object_type=object_type,
        object_id=object_id,
        entity_id=entity_id,
        entity_type=entity_type,
        permission_key=permission_key,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(perm)
    db_session.flush()
    return perm


# ------------------------------------------------------------------
# Scenario A: Object permission grant and access
# ------------------------------------------------------------------


class TestObjectPermissionAccess:
    """Test granting and checking object-level permissions."""

    def test_creator_gets_object_full_on_event(
        self,
        client,
        db_session,
        auth_headers,
        mock_permission_allow,
        event_statuses,
        workflow_course,
    ):
        """Creating an event grants object_full to the creator."""
        payload = {
            "name": f"Creator Event {uuid.uuid4().hex[:6]}",
            "slug": f"ce-{uuid.uuid4().hex[:4]}",
            "description": "Creator permission test",
            "dateStart": "2026-08-01",
            "dateEnd": "2026-08-31",
            "timeStart": "08:00:00",
            "timeEnd": "18:00:00",
            "guacamole": False,
            "status": str(event_statuses["Geplant"].id),
            "course": str(workflow_course.id),
        }
        resp = client.post(f"{API}/events/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        event_id = resp.json()["id"]

        # Check object permissions for this event
        resp = client.get(
            f"{API}/object-permissions/Event/{event_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        perm_keys = [p["permission_key"] for p in items]
        assert "object_full" in perm_keys

    def test_grant_object_read_allows_get(
        self,
        client,
        db_session,
        system_user,
        event_statuses,
        workflow_course,
        user_b,
        user_b_headers,
    ):
        """Granting object_read allows GET on the specific event."""
        event = _create_event_via_db(
            db_session, system_user, event_statuses, workflow_course
        )

        # User B has no permissions -> GET should fail
        resp = client.get(f"{API}/events/{event.id}", headers=user_b_headers)
        assert resp.status_code == 403

        # Grant object_read to user B
        _create_object_permission(
            db_session,
            system_user,
            "Event",
            event.id,
            user_b.id,
            permission_key="object_read",
        )

        # Now GET should succeed
        resp = client.get(f"{API}/events/{event.id}", headers=user_b_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == str(event.id)

    def test_object_read_denies_update(
        self,
        client,
        db_session,
        system_user,
        event_statuses,
        workflow_course,
        user_b,
        user_b_headers,
    ):
        """User with object_read cannot PUT (update) the event."""
        event = _create_event_via_db(
            db_session, system_user, event_statuses, workflow_course
        )
        _create_object_permission(
            db_session,
            system_user,
            "Event",
            event.id,
            user_b.id,
            permission_key="object_read",
        )

        resp = client.put(
            f"{API}/events/{event.id}",
            json={"name": "Updated Name"},
            headers=user_b_headers,
        )
        assert resp.status_code == 403

    def test_object_update_allows_read(
        self,
        client,
        db_session,
        system_user,
        event_statuses,
        workflow_course,
        user_b,
        user_b_headers,
    ):
        """User with object_update can also GET (hierarchy: update > read)."""
        event = _create_event_via_db(
            db_session, system_user, event_statuses, workflow_course
        )
        _create_object_permission(
            db_session,
            system_user,
            "Event",
            event.id,
            user_b.id,
            permission_key="object_update",
        )

        # Read should work (implied by update)
        resp = client.get(f"{API}/events/{event.id}", headers=user_b_headers)
        assert resp.status_code == 200

    def test_object_full_allows_delete(
        self,
        client,
        db_session,
        system_user,
        event_statuses,
        workflow_course,
        role_teacher,
        user_b,
        user_b_headers,
    ):
        """User with object_full can delete the event."""
        event = _create_event_via_db(
            db_session, system_user, event_statuses, workflow_course
        )
        _create_object_permission(
            db_session,
            system_user,
            "Event",
            event.id,
            user_b.id,
            permission_key="object_full",
        )

        resp = client.delete(f"{API}/events/{event.id}", headers=user_b_headers)
        assert resp.status_code == 200


# ------------------------------------------------------------------
# Scenario B: Fallthrough pattern (filtered lists)
# ------------------------------------------------------------------


class TestFallthroughPattern:
    """Test that list endpoints filter by object permissions."""

    def test_list_events_returns_only_permitted(
        self,
        client,
        db_session,
        system_user,
        event_statuses,
        workflow_course,
        user_b,
        user_b_headers,
    ):
        """User B sees only events they have object_read permission for."""
        event_a = _create_event_via_db(
            db_session, system_user, event_statuses, workflow_course
        )
        event_b = _create_event_via_db(
            db_session, system_user, event_statuses, workflow_course
        )

        # Grant object_read on event_b only
        _create_object_permission(
            db_session,
            system_user,
            "Event",
            event_b.id,
            user_b.id,
            permission_key="object_read",
        )

        resp = client.get(f"{API}/events/", headers=user_b_headers)
        assert resp.status_code == 200
        items = resp.json()["items"]
        item_ids = [item["id"] for item in items]
        assert str(event_b.id) in item_ids
        assert str(event_a.id) not in item_ids

    def test_list_events_without_any_permission_returns_empty(
        self,
        client,
        db_session,
        system_user,
        event_statuses,
        workflow_course,
        user_b,
        user_b_headers,
    ):
        """User without any event permissions gets empty list."""
        _create_event_via_db(
            db_session, system_user, event_statuses, workflow_course
        )

        resp = client.get(f"{API}/events/", headers=user_b_headers)
        assert resp.status_code == 200
        assert resp.json()["items"] == []


# ------------------------------------------------------------------
# Scenario C: Role-based permissions
# ------------------------------------------------------------------


class TestRoleBasedPermissions:
    """Test that role permissions and role object permissions work."""

    def test_role_object_permission_grants_access(
        self,
        client,
        db_session,
        system_user,
        event_statuses,
        workflow_course,
        role_teacher,
        teacher_user,
        teacher_headers,
    ):
        """ObjectPermission on a Role grants access to users with that role."""
        event = _create_event_via_db(
            db_session, system_user, event_statuses, workflow_course
        )

        # Grant object_read for the Role (not the User directly)
        _create_object_permission(
            db_session,
            system_user,
            "Event",
            event.id,
            role_teacher.id,
            entity_type="Role",
            permission_key="object_read",
        )

        resp = client.get(f"{API}/events/{event.id}", headers=teacher_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == str(event.id)


# ------------------------------------------------------------------
# Scenario D: Protected objects
# ------------------------------------------------------------------


class TestProtectedObjects:
    """Test that protected roles and permissions cannot be modified."""

    def test_cannot_delete_protected_role(
        self,
        client,
        db_session,
        role_admin,
        mock_permission_allow,
        auth_headers,
    ):
        """Deleting a protected role (admin_full) returns 403."""
        resp = client.delete(
            f"{API}/roles/{role_admin.id}", headers=auth_headers
        )
        assert resp.status_code == 403

    def test_duplicate_object_permission_returns_409(
        self,
        client,
        db_session,
        system_user,
        mock_permission_allow,
        auth_headers,
        event_statuses,
        workflow_course,
        user_b,
    ):
        """Creating the same ObjectPermission twice returns 409."""
        event = _create_event_via_db(
            db_session, system_user, event_statuses, workflow_course
        )
        payload = {
            "object_type": "Event",
            "object_id": str(event.id),
            "entity_id": str(user_b.id),
            "entity_type": "User",
            "permission_key": "object_read",
        }

        # First creation
        resp = client.post(
            f"{API}/object-permissions/",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 201

        # Duplicate
        resp = client.post(
            f"{API}/object-permissions/",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 409


# ------------------------------------------------------------------
# Scenario E: Permission hierarchy
# ------------------------------------------------------------------


class TestPermissionHierarchy:
    """Test object permission hierarchy: full > delete > update > read."""

    def test_object_full_grants_all_operations(
        self,
        client,
        db_session,
        system_user,
        event_statuses,
        workflow_course,
        role_teacher,
        user_b,
        user_b_headers,
    ):
        """object_full allows read, update, and delete."""
        event = _create_event_via_db(
            db_session, system_user, event_statuses, workflow_course
        )
        _create_object_permission(
            db_session,
            system_user,
            "Event",
            event.id,
            user_b.id,
            permission_key="object_full",
        )

        # Read
        resp = client.get(f"{API}/events/{event.id}", headers=user_b_headers)
        assert resp.status_code == 200

        # Update
        resp = client.put(
            f"{API}/events/{event.id}",
            json={"description": "Updated by full"},
            headers=user_b_headers,
        )
        assert resp.status_code == 200

        # Delete
        resp = client.delete(f"{API}/events/{event.id}", headers=user_b_headers)
        assert resp.status_code == 200

    def test_object_delete_grants_update_and_read(
        self,
        client,
        db_session,
        system_user,
        event_statuses,
        workflow_course,
        user_b,
        user_b_headers,
    ):
        """object_delete implies update and read."""
        event = _create_event_via_db(
            db_session, system_user, event_statuses, workflow_course
        )
        _create_object_permission(
            db_session,
            system_user,
            "Event",
            event.id,
            user_b.id,
            permission_key="object_delete",
        )

        # Read
        resp = client.get(f"{API}/events/{event.id}", headers=user_b_headers)
        assert resp.status_code == 200

        # Update
        resp = client.put(
            f"{API}/events/{event.id}",
            json={"description": "Updated by delete"},
            headers=user_b_headers,
        )
        assert resp.status_code == 200

    def test_object_update_grants_read_but_not_delete(
        self,
        client,
        db_session,
        system_user,
        event_statuses,
        workflow_course,
        user_b,
        user_b_headers,
    ):
        """object_update grants read but NOT delete."""
        event = _create_event_via_db(
            db_session, system_user, event_statuses, workflow_course
        )
        _create_object_permission(
            db_session,
            system_user,
            "Event",
            event.id,
            user_b.id,
            permission_key="object_update",
        )

        # Read - allowed
        resp = client.get(f"{API}/events/{event.id}", headers=user_b_headers)
        assert resp.status_code == 200

        # Delete - denied
        resp = client.delete(f"{API}/events/{event.id}", headers=user_b_headers)
        assert resp.status_code == 403

    def test_object_read_denies_update_and_delete(
        self,
        client,
        db_session,
        system_user,
        event_statuses,
        workflow_course,
        user_b,
        user_b_headers,
    ):
        """object_read only allows read, not update or delete."""
        event = _create_event_via_db(
            db_session, system_user, event_statuses, workflow_course
        )
        _create_object_permission(
            db_session,
            system_user,
            "Event",
            event.id,
            user_b.id,
            permission_key="object_read",
        )

        # Read - allowed
        resp = client.get(f"{API}/events/{event.id}", headers=user_b_headers)
        assert resp.status_code == 200

        # Update - denied
        resp = client.put(
            f"{API}/events/{event.id}",
            json={"description": "Should fail"},
            headers=user_b_headers,
        )
        assert resp.status_code == 403

        # Delete - denied
        resp = client.delete(f"{API}/events/{event.id}", headers=user_b_headers)
        assert resp.status_code == 403
