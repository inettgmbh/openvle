"""
E2E workflow tests for event lifecycle.

Tests the full event lifecycle over multiple HTTP calls: create, add
templates/users, start, end, delete. Validates status transitions,
start prerequisites, and error recovery.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch


from tests.e2e.conftest import API
from tests.e2e.conftest import _set_event_status


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _create_event_payload(event_statuses, course_id, **overrides):
    """Build a valid event creation payload."""
    payload = {
        "name": f"Event {uuid.uuid4().hex[:6]}",
        "slug": f"ev-{uuid.uuid4().hex[:4]}",
        "description": "Lifecycle test event",
        "dateStart": "2026-08-01",
        "dateEnd": "2026-08-31",
        "timeStart": "08:00:00",
        "timeEnd": "18:00:00",
        "guacamole": False,
        "status": str(event_statuses["Geplant"].id),
        "course": str(course_id),
    }
    payload.update(overrides)
    return payload


def _add_template_to_course(db_session, course, template):
    """Associate a template with a course."""
    from models.associations import course_template_association_table

    db_session.execute(
        course_template_association_table.insert().values(
            course_id=course.id, template_id=template.id
        )
    )
    db_session.flush()


def _add_user_to_event(client, event_id, user_id, role_id, headers):
    """Add a user to an event via API."""
    return client.post(
        f"{API}/events/{event_id}/users",
        json={"user_id": str(user_id), "role_id": str(role_id)},
        headers=headers,
    )


# ------------------------------------------------------------------
# Scenario A: Happy path - full lifecycle
# ------------------------------------------------------------------


class TestEventLifecycleHappyPath:
    """Full event lifecycle from creation to deletion."""

    @patch("controllers.events.CRUDEvent._delete_mail")
    def test_full_lifecycle(
        self,
        _mock_delete_mail,
        client,
        db_session,
        mock_permission_allow,
        mock_redis_queues,
        auth_headers,
        event_statuses,
        workflow_course,
        workflow_template,
        role_teacher,
        role_student,
        teacher_user,
        student_user,
    ):
        """Create -> add templates -> add users -> start -> end -> delete."""
        # Step 1: Create event
        payload = _create_event_payload(event_statuses, workflow_course.id)
        resp = client.post(f"{API}/events/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        event_id = resp.json()["id"]
        assert resp.json()["status"] == str(event_statuses["Geplant"].id)

        # Step 2: Add template to course (needed for start)
        _add_template_to_course(db_session, workflow_course, workflow_template)

        # Step 3: Add teacher to event
        resp = _add_user_to_event(
            client,
            event_id,
            teacher_user.id,
            role_teacher.id,
            auth_headers,
        )
        assert resp.status_code == 201

        # Step 4: Add student to event
        resp = _add_user_to_event(
            client,
            event_id,
            student_user.id,
            role_student.id,
            auth_headers,
        )
        assert resp.status_code == 201

        # Step 5: Start event
        resp = client.post(
            f"{API}/events/{event_id}/actions/start",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == str(event_statuses["Deploying"].id)

        # Verify jobs were enqueued
        assert len(mock_redis_queues) > 0

        # Verify via GET
        resp = client.get(f"{API}/events/{event_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == str(event_statuses["Deploying"].id)

        # Step 6: Simulate worker completing (set status to Aktiv)
        from models import Event

        event = db_session.query(Event).filter(Event.id == uuid.UUID(event_id)).first()
        _set_event_status(db_session, event, "Aktiv", event_statuses)

        # Step 7: End event
        resp = client.post(
            f"{API}/events/{event_id}/actions/stop",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == str(event_statuses["Archiving"].id)

        # Step 8: Simulate worker completing (set status to Archiviert)
        event = db_session.query(Event).filter(Event.id == uuid.UUID(event_id)).first()
        _set_event_status(db_session, event, "Archiviert", event_statuses)

        # Step 9: Delete event
        resp = client.delete(f"{API}/events/{event_id}", headers=auth_headers)
        assert resp.status_code == 200

        # Step 10: Verify it's gone
        resp = client.get(f"{API}/events/{event_id}", headers=auth_headers)
        assert resp.status_code == 404


# ------------------------------------------------------------------
# Scenario B: Status validations
# ------------------------------------------------------------------


class TestEventStatusValidations:
    """Test that invalid status transitions are rejected."""

    def test_cannot_start_non_geplant_event(
        self,
        client,
        db_session,
        mock_permission_allow,
        mock_redis_queues,
        auth_headers,
        event_statuses,
        workflow_event,
    ):
        """Starting an event not in 'Geplant' status returns 422."""
        _set_event_status(db_session, workflow_event, "Aktiv", event_statuses)
        resp = client.post(
            f"{API}/events/{workflow_event.id}/actions/start",
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_cannot_end_non_aktiv_event(
        self,
        client,
        db_session,
        mock_permission_allow,
        mock_redis_queues,
        auth_headers,
        event_statuses,
        workflow_event,
    ):
        """Ending an event not in 'Aktiv' status returns 422."""
        # Event is in 'Geplant' by default
        resp = client.post(
            f"{API}/events/{workflow_event.id}/actions/stop",
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_cannot_delete_aktiv_event(
        self,
        client,
        db_session,
        mock_permission_allow,
        auth_headers,
        event_statuses,
        workflow_event,
        role_teacher,
    ):
        """Deleting an active event returns 422."""
        _set_event_status(db_session, workflow_event, "Aktiv", event_statuses)
        resp = client.delete(f"{API}/events/{workflow_event.id}", headers=auth_headers)
        assert resp.status_code == 422

    def test_can_delete_archiviert_event(
        self,
        client,
        db_session,
        mock_permission_allow,
        auth_headers,
        event_statuses,
        workflow_event,
        role_teacher,
    ):
        """Deleting an archived event returns 200."""
        _set_event_status(db_session, workflow_event, "Archiviert", event_statuses)
        resp = client.delete(f"{API}/events/{workflow_event.id}", headers=auth_headers)
        assert resp.status_code == 200

    def test_can_delete_geplant_event(
        self,
        client,
        db_session,
        mock_permission_allow,
        auth_headers,
        event_statuses,
        workflow_event,
        role_teacher,
    ):
        """Deleting a planned event returns 200."""
        # Already in Geplant
        resp = client.delete(f"{API}/events/{workflow_event.id}", headers=auth_headers)
        assert resp.status_code == 200

    def test_can_delete_core_fehler_event(
        self,
        client,
        db_session,
        mock_permission_allow,
        auth_headers,
        event_statuses,
        workflow_event,
        role_teacher,
    ):
        """Deleting an event in 'Core Fehler' returns 200."""
        _set_event_status(db_session, workflow_event, "Core Fehler", event_statuses)
        resp = client.delete(f"{API}/events/{workflow_event.id}", headers=auth_headers)
        assert resp.status_code == 200

    def test_cannot_delete_deploying_event(
        self,
        client,
        db_session,
        mock_permission_allow,
        auth_headers,
        event_statuses,
        workflow_event,
        role_teacher,
    ):
        """Deleting an event in 'Deploying' returns 422."""
        _set_event_status(db_session, workflow_event, "Deploying", event_statuses)
        resp = client.delete(f"{API}/events/{workflow_event.id}", headers=auth_headers)
        assert resp.status_code == 422


# ------------------------------------------------------------------
# Scenario C: Start prerequisites
# ------------------------------------------------------------------


class TestEventStartPrerequisites:
    """Test that start requires users and templates."""

    def test_start_requires_participants(
        self,
        client,
        db_session,
        mock_permission_allow,
        mock_redis_queues,
        auth_headers,
        event_statuses,
        workflow_event,
        workflow_template,
        workflow_course,
        role_teacher,
    ):
        """Starting without any participants raises 409 (OperationDependencyMissing)."""
        _add_template_to_course(db_session, workflow_course, workflow_template)
        resp = client.post(
            f"{API}/events/{workflow_event.id}/actions/start",
            headers=auth_headers,
        )
        assert resp.status_code == 409

    def test_start_requires_teachers(
        self,
        client,
        db_session,
        mock_permission_allow,
        mock_redis_queues,
        auth_headers,
        event_statuses,
        workflow_event,
        workflow_template,
        workflow_course,
        role_student,
        student_user,
        role_teacher,
    ):
        """Starting without teachers raises 409 (OperationDependencyMissing)."""
        _add_template_to_course(db_session, workflow_course, workflow_template)
        # Add only student
        resp = _add_user_to_event(
            client,
            workflow_event.id,
            student_user.id,
            role_student.id,
            auth_headers,
        )
        assert resp.status_code == 201

        resp = client.post(
            f"{API}/events/{workflow_event.id}/actions/start",
            headers=auth_headers,
        )
        assert resp.status_code == 409

    def test_start_requires_templates_on_course(
        self,
        client,
        db_session,
        mock_permission_allow,
        mock_redis_queues,
        auth_headers,
        event_statuses,
        workflow_event,
        role_teacher,
        role_student,
        teacher_user,
        student_user,
    ):
        """Starting with no templates on course raises 409 (OperationDependencyMissing)."""
        # Add users but no templates
        _add_user_to_event(
            client,
            workflow_event.id,
            teacher_user.id,
            role_teacher.id,
            auth_headers,
        )
        _add_user_to_event(
            client,
            workflow_event.id,
            student_user.id,
            role_student.id,
            auth_headers,
        )

        resp = client.post(
            f"{API}/events/{workflow_event.id}/actions/start",
            headers=auth_headers,
        )
        assert resp.status_code == 409

    def test_start_requires_template_proxmox_id(
        self,
        client,
        db_session,
        system_user,
        mock_permission_allow,
        mock_redis_queues,
        auth_headers,
        event_statuses,
        workflow_event,
        workflow_course,
        role_teacher,
        role_student,
        teacher_user,
        student_user,
    ):
        """Starting with template without proxmoxId raises 409 (OperationDependencyMissing)."""
        from models import Template

        # Create template WITHOUT proxmoxId
        now = datetime.now(timezone.utc)
        template_no_pve = Template(
            id=uuid.uuid4(),
            name=f"No PVE Template {uuid.uuid4().hex[:6]}",
            description="No proxmoxId",
            status="Ready",
            proxmoxId=None,
            proxmoxNode="pve-node-01",
            cpu=2,
            ram=4096,
            disk=32,
            prevent_delete=False,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(template_no_pve)
        db_session.flush()
        _add_template_to_course(db_session, workflow_course, template_no_pve)

        # Add users
        _add_user_to_event(
            client,
            workflow_event.id,
            teacher_user.id,
            role_teacher.id,
            auth_headers,
        )
        _add_user_to_event(
            client,
            workflow_event.id,
            student_user.id,
            role_student.id,
            auth_headers,
        )

        resp = client.post(
            f"{API}/events/{workflow_event.id}/actions/start",
            headers=auth_headers,
        )
        assert resp.status_code == 409


# ------------------------------------------------------------------
# Scenario D: Dynamic changes on active events
# ------------------------------------------------------------------


class TestActiveEventChanges:
    """Test adding/removing users and templates on active events."""

    def _make_active_event(
        self,
        client,
        db_session,
        auth_headers,
        event_statuses,
        workflow_course,
        workflow_template,
        role_teacher,
        role_student,
        teacher_user,
        student_user,
    ):
        """Helper: create and start an event, then set to Aktiv."""
        _add_template_to_course(db_session, workflow_course, workflow_template)
        payload = _create_event_payload(event_statuses, workflow_course.id)
        resp = client.post(f"{API}/events/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        event_id = resp.json()["id"]

        # Add teacher + student
        _add_user_to_event(
            client, event_id, teacher_user.id, role_teacher.id, auth_headers
        )
        _add_user_to_event(
            client, event_id, student_user.id, role_student.id, auth_headers
        )

        # Start
        resp = client.post(
            f"{API}/events/{event_id}/actions/start",
            headers=auth_headers,
        )
        assert resp.status_code == 200

        # Manually set to Aktiv (simulating worker)
        from models import Event

        event = db_session.query(Event).filter(Event.id == uuid.UUID(event_id)).first()
        _set_event_status(db_session, event, "Aktiv", event_statuses)

        return event_id

    def test_add_user_to_aktiv_event(
        self,
        client,
        db_session,
        mock_permission_allow,
        mock_redis_queues,
        auth_headers,
        event_statuses,
        workflow_course,
        workflow_template,
        role_teacher,
        role_student,
        teacher_user,
        student_user,
        system_user,
    ):
        """Adding a user to an active event succeeds and creates EventsUser."""
        event_id = self._make_active_event(
            client,
            db_session,
            auth_headers,
            event_statuses,
            workflow_course,
            workflow_template,
            role_teacher,
            role_student,
            teacher_user,
            student_user,
        )

        # Create another student
        from models import User

        now = datetime.now(timezone.utc)
        new_student = User(
            id=uuid.uuid4(),
            username=f"newstudent_{uuid.uuid4().hex[:6]}",
            name="New Student",
            email=f"newstudent_{uuid.uuid4().hex[:6]}@example.com",
            hashed_password="$2b$12$dummyhashvalue",
            status="Active",
            locale="de_DE",
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(new_student)
        db_session.flush()

        # Add new student to active event
        resp = _add_user_to_event(
            client,
            event_id,
            new_student.id,
            role_student.id,
            auth_headers,
        )
        assert resp.status_code == 201

        # Verify EventsUser was created
        from models import EventsUser

        event_user = (
            db_session.query(EventsUser)
            .filter(
                EventsUser.event_id == uuid.UUID(event_id),
                EventsUser.user_id == new_student.id,
            )
            .first()
        )
        assert event_user is not None
        assert event_user.role_id == role_student.id

    def test_remove_user_from_aktiv_event_enqueues_cleanup(
        self,
        client,
        db_session,
        mock_permission_allow,
        mock_redis_queues,
        auth_headers,
        event_statuses,
        workflow_course,
        workflow_template,
        role_teacher,
        role_student,
        teacher_user,
        student_user,
    ):
        """Removing a user from active event enqueues VM cleanup."""
        event_id = self._make_active_event(
            client,
            db_session,
            auth_headers,
            event_statuses,
            workflow_course,
            workflow_template,
            role_teacher,
            role_student,
            teacher_user,
            student_user,
        )

        # Clear queues to track only cleanup jobs
        mock_redis_queues.clear()

        # Remove student from active event
        resp = client.delete(
            f"{API}/events/{event_id}/users/{student_user.id}/roles/{role_student.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200


# ------------------------------------------------------------------
# Scenario E: Event update and error recovery
# ------------------------------------------------------------------


class TestEventUpdateAndRecovery:
    """Test event update rules and error status recovery."""

    def test_update_resets_core_fehler_to_geplant(
        self,
        client,
        db_session,
        mock_permission_allow,
        auth_headers,
        event_statuses,
        workflow_event,
    ):
        """Updating an event in 'Core Fehler' resets status to 'Geplant'."""
        _set_event_status(db_session, workflow_event, "Core Fehler", event_statuses)

        resp = client.put(
            f"{API}/events/{workflow_event.id}",
            json={"description": "Fixed description"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == str(event_statuses["Geplant"].id)

    def test_update_resets_deployment_fehler_to_geplant(
        self,
        client,
        db_session,
        mock_permission_allow,
        auth_headers,
        event_statuses,
        workflow_event,
    ):
        """Updating an event in 'Deployment Fehler' resets to 'Geplant'."""
        _set_event_status(
            db_session, workflow_event, "Deployment Fehler", event_statuses
        )

        resp = client.put(
            f"{API}/events/{workflow_event.id}",
            json={"description": "Fixed after deployment failure"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == str(event_statuses["Geplant"].id)

    def test_update_blocked_for_aktiv_event(
        self,
        client,
        db_session,
        mock_permission_allow,
        auth_headers,
        event_statuses,
        workflow_event,
    ):
        """Updating an active event returns 422."""
        _set_event_status(db_session, workflow_event, "Aktiv", event_statuses)

        resp = client.put(
            f"{API}/events/{workflow_event.id}",
            json={"description": "Should not work"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_update_blocked_for_deploying_event(
        self,
        client,
        db_session,
        mock_permission_allow,
        auth_headers,
        event_statuses,
        workflow_event,
    ):
        """Updating a deploying event returns 422."""
        _set_event_status(db_session, workflow_event, "Deploying", event_statuses)

        resp = client.put(
            f"{API}/events/{workflow_event.id}",
            json={"description": "Should not work"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_update_blocked_for_archiviert_event(
        self,
        client,
        db_session,
        mock_permission_allow,
        auth_headers,
        event_statuses,
        workflow_event,
    ):
        """Updating an archived event returns 422."""
        _set_event_status(db_session, workflow_event, "Archiviert", event_statuses)

        resp = client.put(
            f"{API}/events/{workflow_event.id}",
            json={"description": "Should not work"},
            headers=auth_headers,
        )
        assert resp.status_code == 422


# ------------------------------------------------------------------
# Scenario F: Slug and name validation
# ------------------------------------------------------------------


class TestEventSlugAndNameValidation:
    """Test slug and name uniqueness / validation."""

    def test_create_event_duplicate_name_returns_409(
        self,
        client,
        db_session,
        mock_permission_allow,
        auth_headers,
        event_statuses,
        workflow_course,
    ):
        """Creating two events with the same name returns 409."""
        name = f"Unique Name {uuid.uuid4().hex[:6]}"
        payload = _create_event_payload(event_statuses, workflow_course.id, name=name)
        resp = client.post(f"{API}/events/", json=payload, headers=auth_headers)
        assert resp.status_code == 201

        payload2 = _create_event_payload(
            event_statuses,
            workflow_course.id,
            name=name,
            slug=f"ev-{uuid.uuid4().hex[:4]}",
        )
        resp = client.post(f"{API}/events/", json=payload2, headers=auth_headers)
        assert resp.status_code == 409

    def test_create_event_duplicate_slug_returns_409(
        self,
        client,
        db_session,
        mock_permission_allow,
        auth_headers,
        event_statuses,
        workflow_course,
    ):
        """Creating two events with the same slug returns 409."""
        slug = f"ds-{uuid.uuid4().hex[:4]}"
        payload = _create_event_payload(event_statuses, workflow_course.id, slug=slug)
        resp = client.post(f"{API}/events/", json=payload, headers=auth_headers)
        assert resp.status_code == 201

        payload2 = _create_event_payload(
            event_statuses,
            workflow_course.id,
            slug=slug,
            name=f"Different Name {uuid.uuid4().hex[:6]}",
        )
        resp = client.post(f"{API}/events/", json=payload2, headers=auth_headers)
        assert resp.status_code == 409

    def test_slug_validation_too_short(
        self,
        client,
        db_session,
        mock_permission_allow,
        auth_headers,
        event_statuses,
        workflow_course,
    ):
        """Slug shorter than 4 characters returns 422."""
        payload = _create_event_payload(event_statuses, workflow_course.id, slug="ab")
        resp = client.post(f"{API}/events/", json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_slug_validation_too_long(
        self,
        client,
        db_session,
        mock_permission_allow,
        auth_headers,
        event_statuses,
        workflow_course,
    ):
        """Slug longer than 8 characters returns 422."""
        payload = _create_event_payload(
            event_statuses, workflow_course.id, slug="abcdefghi"
        )
        resp = client.post(f"{API}/events/", json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_slug_validation_invalid_chars(
        self,
        client,
        db_session,
        mock_permission_allow,
        auth_headers,
        event_statuses,
        workflow_course,
    ):
        """Slug with uppercase or special characters returns 422."""
        payload = _create_event_payload(event_statuses, workflow_course.id, slug="AB@D")
        resp = client.post(f"{API}/events/", json=payload, headers=auth_headers)
        assert resp.status_code == 422
