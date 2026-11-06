"""Integration tests for /v{x}/events/ endpoints."""

import uuid
from datetime import date, datetime, time, timezone
from typing import ClassVar

import pytest
from models.sub_tasks import SubTask
from models.tasks import Task

from tests.integration.conftest import API


@pytest.fixture()
def sample_event(db_session, system_user, event_statuses, sample_course):
    """Create an event in the test DB."""
    from models import Event

    now = datetime.now(timezone.utc)
    event = Event(
        id=uuid.uuid4(),
        name=f"Test Event {uuid.uuid4().hex[:6]}",
        slug=f"te-{uuid.uuid4().hex[:4]}",
        description="A test event",
        dateStart=date(2026, 6, 1),
        dateEnd=date(2026, 6, 30),
        timeStart=time(8, 0),
        timeEnd=time(18, 0),
        guacamole=False,
        status=event_statuses["Geplant"].id,
        course=sample_course.id,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(event)
    db_session.flush()
    return event


# ------------------------------------------------------------------
# CRUD endpoints
# ------------------------------------------------------------------


class TestCreateEvent:
    """POST /events/ -- create a new event."""

    def test_create_returns_201(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        event_statuses,
        sample_course,
    ):
        payload = {
            "name": "Brand New Event",
            "slug": "bne1",
            "description": "A brand new event",
            "dateStart": "2026-07-01",
            "dateEnd": "2026-07-31",
            "timeStart": "09:00:00",
            "timeEnd": "17:00:00",
            "guacamole": False,
            "status": str(event_statuses["Geplant"].id),
            "course": str(sample_course.id),
        }
        resp = client.post(f"{API}/events/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Brand New Event"
        assert data["slug"] == "bne1"
        assert data["description"] == "A brand new event"
        assert "id" in data

    def test_create_unauthenticated_returns_401(self, client):
        payload = {
            "name": "No Auth Event",
            "slug": "noau",
            "status": str(uuid.uuid4()),
            "course": str(uuid.uuid4()),
        }
        resp = client.post(f"{API}/events/", json=payload)
        assert resp.status_code in (401, 403)

    def test_create_permission_denied_returns_403(
        self, client, auth_headers, event_statuses, sample_course
    ):
        """Without mock_permission_allow, events_create is denied."""
        payload = {
            "name": "Denied Event",
            "slug": "deny",
            "status": str(event_statuses["Geplant"].id),
            "course": str(sample_course.id),
        }
        resp = client.post(f"{API}/events/", json=payload, headers=auth_headers)
        assert resp.status_code == 403


class TestGetEvents:
    """GET /events/ -- list all events."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_event,
    ):
        resp = client.get(f"{API}/events/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/events/")
        assert resp.status_code in (401, 403)

    def test_without_permission_falls_through_to_auth_filtered(
        self,
        client,
        auth_headers,
        sample_event,
    ):
        """Without events_read permission the route falls through to
        get_multi_auth which returns a (possibly empty) paginated list
        rather than raising 403."""
        resp = client.get(f"{API}/events/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data


class TestGetEventById:
    """GET /events/{id} -- get single event."""

    def test_returns_event(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_event,
    ):
        resp = client.get(
            f"{API}/events/{sample_event.id}", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_event.id)
        assert data["name"] == sample_event.name
        assert data["slug"] == sample_event.slug
        assert data["description"] == sample_event.description

    def test_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/events/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/events/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(
        self, client, auth_headers, sample_event
    ):
        """Without mock_permission_allow, events_read is denied."""
        resp = client.get(
            f"{API}/events/{sample_event.id}", headers=auth_headers
        )
        assert resp.status_code == 403


class TestUpdateEvent:
    """PUT /events/{id} -- update an event."""

    def test_update_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_event,
    ):
        payload = {
            "name": "Updated Event Name",
            "description": "Updated description",
        }
        resp = client.put(
            f"{API}/events/{sample_event.id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Event Name"
        assert data["description"] == "Updated description"

    def test_update_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        payload = {"name": "Ghost Event"}
        resp = client.put(
            f"{API}/events/{fake_id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_update_unauthenticated_returns_401(self, client):
        """Use non-existent ID so ChangelogMiddleware exits early."""
        fake_id = uuid.uuid4()
        payload = {"name": "No Auth Event"}
        resp = client.put(f"{API}/events/{fake_id}", json=payload)
        assert resp.status_code in (401, 403)

    def test_update_permission_denied_returns_403(
        self, client, auth_headers, sample_event
    ):
        """Without mock_permission_allow, events_update is denied."""
        payload = {"name": "Denied Update"}
        resp = client.put(
            f"{API}/events/{sample_event.id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestUpdateEventEndDate:
    """POST /events/{id}/end-date -- update event end date/time."""

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        payload = {
            "dateEnd": "2026-12-31",
            "timeEnd": "23:59:59",
        }
        resp = client.post(f"{API}/events/{fake_id}/end-date", json=payload)
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(
        self, client, auth_headers, sample_event
    ):
        """Without mock_permission_allow, events_update is denied."""
        payload = {
            "dateEnd": "2026-12-31",
            "timeEnd": "23:59:59",
        }
        resp = client.post(
            f"{API}/events/{sample_event.id}/end-date",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestDeleteEvent:
    """DELETE /events/{id} -- delete an event."""

    def test_delete_returns_200(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        role_teacher,
        sample_event,
    ):
        resp = client.delete(
            f"{API}/events/{sample_event.id}", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_delete_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/events/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/events/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_delete_permission_denied_returns_403(
        self, client, auth_headers, sample_event
    ):
        """Without mock_permission_allow, events_delete is denied."""
        resp = client.delete(
            f"{API}/events/{sample_event.id}", headers=auth_headers
        )
        assert resp.status_code == 403


# ------------------------------------------------------------------
# Event Users sub-resource
# ------------------------------------------------------------------


class TestAddEventUser:
    """POST /events/{id}/users -- add user to event."""

    def test_add_user_returns_201(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_event,
        active_user,
        role_teacher,
    ):
        payload = {
            "user_id": str(active_user.id),
            "role_id": str(role_teacher.id),
        }
        resp = client.post(
            f"{API}/events/{sample_event.id}/users",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["user_id"] == str(active_user.id)
        assert data["role_id"] == str(role_teacher.id)
        assert data["event_id"] == str(sample_event.id)

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        payload = {
            "user_id": str(uuid.uuid4()),
            "role_id": str(uuid.uuid4()),
        }
        resp = client.post(f"{API}/events/{fake_id}/users", json=payload)
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(
        self, client, auth_headers, sample_event
    ):
        """Without mock_permission_allow, events_update is denied."""
        payload = {
            "user_id": str(uuid.uuid4()),
            "role_id": str(uuid.uuid4()),
        }
        resp = client.post(
            f"{API}/events/{sample_event.id}/users",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestGetEventUsers:
    """GET /events/{id}/users -- list users for event."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_event,
    ):
        resp = client.get(
            f"{API}/events/{sample_event.id}/users",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/events/{fake_id}/users")
        assert resp.status_code in (401, 403)


class TestDeleteEventUser:
    """DELETE /events/{id}/users/{user_id}/roles/{role_id} -- remove user/role."""

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        fake_user_id = uuid.uuid4()
        fake_role_id = uuid.uuid4()
        resp = client.delete(
            f"{API}/events/{fake_id}/users/{fake_user_id}/roles/{fake_role_id}"
        )
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(
        self, client, auth_headers, sample_event
    ):
        """Without mock_permission_allow, events_update is denied."""
        fake_user_id = uuid.uuid4()
        fake_role_id = uuid.uuid4()
        resp = client.delete(
            f"{API}/events/{sample_event.id}/users/{fake_user_id}/roles/{fake_role_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 403


# ------------------------------------------------------------------
# Event Mails sub-resource
# ------------------------------------------------------------------


class TestGetEventMails:
    """GET /events/{id}/mails -- list mails for event."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_event,
    ):
        resp = client.get(
            f"{API}/events/{sample_event.id}/mails",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert data["items"] == []

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/events/{fake_id}/mails")
        assert resp.status_code in (401, 403)


# ------------------------------------------------------------------
# Event Templates sub-resource
# ------------------------------------------------------------------


class TestGetEventTemplates:
    """GET /events/{id}/templates -- list templates for event."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_event,
    ):
        resp = client.get(
            f"{API}/events/{sample_event.id}/templates",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert data["items"] == []

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/events/{fake_id}/templates")
        assert resp.status_code in (401, 403)


class TestAddEventTemplates:
    """POST /events/{id}/templates -- add templates to event."""

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        payload = {"templates": [{"id": str(uuid.uuid4())}]}
        resp = client.post(f"{API}/events/{fake_id}/templates", json=payload)
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(
        self, client, auth_headers, sample_event
    ):
        """Without mock_permission_allow, events_templates_update is denied."""
        payload = {"templates": [{"id": str(uuid.uuid4())}]}
        resp = client.post(
            f"{API}/events/{sample_event.id}/templates",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


# ------------------------------------------------------------------
# Event Virtual Machines sub-resource
# ------------------------------------------------------------------


class TestGetEventVirtualMachines:
    """GET /events/{id}/virtual-machines -- list VMs for event."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_event,
    ):
        resp = client.get(
            f"{API}/events/{sample_event.id}/virtual-machines",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert data["items"] == []

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/events/{fake_id}/virtual-machines")
        assert resp.status_code in (401, 403)


# ------------------------------------------------------------------
# Bulk VM actions (auth/permission patterns only -- PVE unavailable)
# ------------------------------------------------------------------


class TestEventBulkVMActions:
    """POST /events/{id}/virtual-machines/bulk-actions/{action}

    These endpoints require Proxmox, so we only test auth and
    permission gates here.
    """

    # Actions that take no request body
    SIMPLE_ACTIONS: ClassVar[list[str]] = [
        "start",
        "stop",
        "pause",
        "reset",
        "reboot",
        "shutdown",
        "resume",
        "hibernate",
    ]

    @pytest.mark.parametrize("action", SIMPLE_ACTIONS)
    def test_unauthenticated_returns_401(self, client, action):
        fake_id = uuid.uuid4()
        resp = client.post(
            f"{API}/events/{fake_id}/virtual-machines/bulk-actions/{action}"
        )
        assert resp.status_code in (401, 403)

    @pytest.mark.parametrize("action", SIMPLE_ACTIONS)
    def test_permission_denied_returns_403(
        self,
        client,
        auth_headers,
        sample_event,
        mock_redis_queues,
        action,
    ):
        """Without mock_permission_allow, events_update is denied."""
        resp = client.post(
            f"{API}/events/{sample_event.id}/virtual-machines/bulk-actions/{action}",
            headers=auth_headers,
        )
        assert resp.status_code == 403

    # Migrate (requires body with targetNode)
    def test_migrate_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        payload = {"targetNode": "pve1"}
        resp = client.post(
            f"{API}/events/{fake_id}/virtual-machines/bulk-actions/migrate",
            json=payload,
        )
        assert resp.status_code in (401, 403)

    def test_migrate_permission_denied_returns_403(
        self,
        client,
        auth_headers,
        sample_event,
        mock_redis_queues,
    ):
        """Without mock_permission_allow, events_update is denied."""
        payload = {"targetNode": "pve1"}
        resp = client.post(
            f"{API}/events/{sample_event.id}/virtual-machines/bulk-actions/migrate",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403

    # HA-Add (POST, requires body)
    def test_ha_add_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        payload = {"ha_state": "started"}
        resp = client.post(
            f"{API}/events/{fake_id}/virtual-machines/bulk-actions/ha",
            json=payload,
        )
        assert resp.status_code in (401, 403)

    def test_ha_add_permission_denied_returns_403(
        self,
        client,
        auth_headers,
        sample_event,
        mock_redis_queues,
    ):
        """Without mock_permission_allow, events_update is denied."""
        payload = {"ha_state": "started"}
        resp = client.post(
            f"{API}/events/{sample_event.id}/virtual-machines/bulk-actions/ha",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403

    # HA-Remove (DELETE)
    def test_ha_remove_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.delete(
            f"{API}/events/{fake_id}/virtual-machines/bulk-actions/ha"
        )
        assert resp.status_code in (401, 403)

    def test_ha_remove_permission_denied_returns_403(
        self,
        client,
        auth_headers,
        sample_event,
        mock_redis_queues,
    ):
        """Without mock_permission_allow, events_update is denied."""
        resp = client.delete(
            f"{API}/events/{sample_event.id}/virtual-machines/bulk-actions/ha",
            headers=auth_headers,
        )
        assert resp.status_code == 403


# ------------------------------------------------------------------
# Event Guacamole sub-resource
# ------------------------------------------------------------------


class TestGetEventGuacamole:
    """GET /events/{id}/guacamole -- list guacamole connections for event."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_event,
    ):
        resp = client.get(
            f"{API}/events/{sample_event.id}/guacamole",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert data["items"] == []

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/events/{fake_id}/guacamole")
        assert resp.status_code in (401, 403)


# ------------------------------------------------------------------
# Bulk Guacamole actions
# ------------------------------------------------------------------


class TestEventBulkGuacamoleActions:
    """Guacamole bulk create/delete -- auth gates only."""

    def test_create_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.post(
            f"{API}/events/{fake_id}/guacamoles/bulk-actions/create"
        )
        assert resp.status_code in (401, 403)

    def test_delete_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.post(
            f"{API}/events/{fake_id}/guacamoles/bulk-actions/delete"
        )
        assert resp.status_code in (401, 403)


# ------------------------------------------------------------------
# Event lifecycle actions (start / end)
# ------------------------------------------------------------------


class TestEventActions:
    """POST /events/{id}/actions/{start|end} -- lifecycle actions.

    These endpoints orchestrate PVE/Redis workers, so we only test
    auth gates here.
    """

    def test_start_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.post(f"{API}/events/{fake_id}/actions/start")
        assert resp.status_code in (401, 403)

    def test_end_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.post(f"{API}/events/{fake_id}/actions/stop")
        assert resp.status_code in (401, 403)


# ------------------------------------------------------------------
# GET /events/{id}/status
# ------------------------------------------------------------------


def _make_task(db, user, event, name="Start Event"):
    now = datetime.now(timezone.utc)
    task = Task(
        id=uuid.uuid4(),
        name=name,
        status="queued",
        event_id=event.id,
        createdAt=now,
        updatedAt=now,
        createdById=user.id,
        updatedById=user.id,
    )
    db.add(task)
    db.flush()
    return task


def _make_subtask(db, user, task, status="success"):
    now = datetime.now(timezone.utc)
    st = SubTask(
        id=uuid.uuid4(),
        name="Deploy VM",
        status=status,
        object_type="Event",
        object_id=str(task.event_id),
        action="events_actions_start",
        attempt="1",
        parent_task=task.id,
        createdAt=now,
        updatedAt=now,
        createdById=user.id,
        updatedById=user.id,
    )
    db.add(st)
    db.flush()
    return st


def _make_vm(
    db, user, event, vm_status="running", ipv4="10.0.0.1", prevent_delete=False
):
    from models import VirtualMachine

    now = datetime.now(timezone.utc)
    vm = VirtualMachine(
        id=uuid.uuid4(),
        name=f"vm-{uuid.uuid4().hex[:6]}",
        cpu=2,
        ram=4096,
        disk=50,
        status=vm_status,
        event=event.id,
        ipv4=ipv4,
        prevent_delete=prevent_delete,
        proxmoxId=100,
        proxmoxNode="pve-node-01",
        createdAt=now,
        updatedAt=now,
        createdById=user.id,
        updatedById=user.id,
    )
    db.add(vm)
    db.flush()
    return vm


class TestGetEventStatus:
    """GET /events/{id}/status -- event status report."""

    # ------------------------------------------------------------------
    # Auth / basic routing
    # ------------------------------------------------------------------

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/events/{uuid.uuid4()}/status")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(
        self, client, auth_headers, sample_event
    ):
        resp = client.get(
            f"{API}/events/{sample_event.id}/status", headers=auth_headers
        )
        assert resp.status_code == 403

    def test_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        resp = client.get(
            f"{API}/events/{uuid.uuid4()}/status", headers=auth_headers
        )
        assert resp.status_code == 404

    # ------------------------------------------------------------------
    # Response shape
    # ------------------------------------------------------------------

    def test_response_contains_required_fields(
        self, client, auth_headers, mock_permission_allow, sample_event
    ):
        resp = client.get(
            f"{API}/events/{sample_event.id}/status", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_event.id)
        assert "currentStatus" in data
        assert "statusInitiator" in data
        assert "vmStats" in data
        assert "connectionStats" in data
        assert "taskStats" in data
        assert "tasks" in data

    def test_vm_stats_fields_present(
        self, client, auth_headers, mock_permission_allow, sample_event
    ):
        resp = client.get(
            f"{API}/events/{sample_event.id}/status", headers=auth_headers
        )
        vm_stats = resp.json()["vmStats"]
        for field in ("total", "running", "stopped", "pending", "protected"):
            assert field in vm_stats, f"vmStats missing '{field}'"

    def test_connection_stats_fields_present(
        self, client, auth_headers, mock_permission_allow, sample_event
    ):
        resp = client.get(
            f"{API}/events/{sample_event.id}/status", headers=auth_headers
        )
        connection_stats = resp.json()["connectionStats"]
        for field in ("total", "deployed", "pending"):
            assert field in connection_stats, (
                f"connectionStats missing '{field}'"
            )
        # No Guacamole records on the bare sample_event → all zero
        assert connection_stats["total"] == 0
        assert connection_stats["deployed"] == 0
        assert connection_stats["pending"] == 0

    def test_task_stats_fields_present(
        self, client, auth_headers, mock_permission_allow, sample_event
    ):
        resp = client.get(
            f"{API}/events/{sample_event.id}/status", headers=auth_headers
        )
        task_stats = resp.json()["taskStats"]
        for field in ("total", "queued", "processing", "success", "failed"):
            assert field in task_stats, f"taskStats missing '{field}'"

    # ------------------------------------------------------------------
    # Geplant
    # ------------------------------------------------------------------

    def test_geplant_initiator_is_creator(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        db_session,
        system_user,
        event_statuses,
        sample_course,
    ):
        now = datetime.now(timezone.utc)
        from models import Event

        event = Event(
            id=uuid.uuid4(),
            name=f"GP-{uuid.uuid4().hex[:6]}",
            slug=f"gp{uuid.uuid4().hex[:4]}",
            dateStart=date(2026, 6, 1),
            dateEnd=date(2026, 6, 30),
            guacamole=False,
            status=event_statuses["Geplant"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=system_user.id,
            updatedById=system_user.id,
        )
        db_session.add(event)
        db_session.flush()

        resp = client.get(
            f"{API}/events/{event.id}/status", headers=auth_headers
        )
        data = resp.json()
        assert data["currentStatus"] == "Geplant"
        assert data["statusInitiator"] == str(system_user.id)
        assert data["vmStats"]["total"] == 0
        assert data["taskStats"]["queued"] == 0
        assert data["tasks"] == []

    # ------------------------------------------------------------------
    # Deploying — with tasks and VMs
    # ------------------------------------------------------------------

    def test_deploying_with_tasks_and_vms(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        db_session,
        system_user,
        active_user,
        event_statuses,
        sample_course,
    ):
        from models import Event

        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"DP-{uuid.uuid4().hex[:6]}",
            slug=f"dp{uuid.uuid4().hex[:4]}",
            dateStart=date(2026, 6, 1),
            dateEnd=date(2026, 6, 30),
            guacamole=False,
            status=event_statuses["Deploying"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        task = _make_task(db_session, system_user, event, name="Start Event")
        _make_subtask(db_session, active_user, task, status="processing")
        _make_subtask(db_session, active_user, task, status="queued")
        _make_vm(
            db_session, active_user, event, vm_status="running", ipv4="10.0.0.1"
        )
        _make_vm(
            db_session, active_user, event, vm_status="stopped", ipv4=None
        )  # pending

        resp = client.get(
            f"{API}/events/{event.id}/status", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["currentStatus"] == "Deploying"
        assert data["statusInitiator"] == str(system_user.id)
        assert data["vmStats"]["total"] == 2
        assert data["vmStats"]["running"] == 1
        assert data["vmStats"]["pending"] == 1
        assert data["taskStats"]["processing"] == 1
        assert data["taskStats"]["queued"] == 1
        assert len(data["tasks"]) == 1
        assert len(data["tasks"][0]["subTasks"]) == 2

    # ------------------------------------------------------------------
    # Aktiv
    # ------------------------------------------------------------------

    def test_aktiv_status(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        db_session,
        system_user,
        active_user,
        event_statuses,
        sample_course,
    ):
        from models import Event

        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"AK-{uuid.uuid4().hex[:6]}",
            slug=f"ak{uuid.uuid4().hex[:4]}",
            dateStart=date(2026, 6, 1),
            dateEnd=date(2026, 6, 30),
            guacamole=False,
            status=event_statuses["Aktiv"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        task = _make_task(db_session, system_user, event, name="Start Event")
        _make_subtask(db_session, active_user, task, status="success")
        _make_vm(
            db_session, active_user, event, vm_status="running", ipv4="10.0.0.1"
        )
        _make_vm(
            db_session, active_user, event, vm_status="running", ipv4="10.0.0.2"
        )
        _make_vm(
            db_session,
            active_user,
            event,
            vm_status="running",
            ipv4="10.0.0.3",
            prevent_delete=True,
        )

        resp = client.get(
            f"{API}/events/{event.id}/status", headers=auth_headers
        )
        data = resp.json()
        assert data["currentStatus"] == "Aktiv"
        assert data["statusInitiator"] == str(system_user.id)
        assert data["vmStats"]["total"] == 3
        assert data["vmStats"]["running"] == 3
        assert data["vmStats"]["protected"] == 1
        assert data["taskStats"]["success"] == 1

    # ------------------------------------------------------------------
    # Archiving / Archiviert
    # ------------------------------------------------------------------

    def test_archiving_initiator_is_end_task_creator(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        db_session,
        system_user,
        active_user,
        event_statuses,
        sample_course,
    ):
        from models import Event

        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"AR-{uuid.uuid4().hex[:6]}",
            slug=f"ar{uuid.uuid4().hex[:4]}",
            dateStart=date(2026, 6, 1),
            dateEnd=date(2026, 6, 30),
            guacamole=False,
            status=event_statuses["Archiving"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        task = _make_task(db_session, system_user, event, name="End Event")
        _make_subtask(db_session, active_user, task, status="processing")

        resp = client.get(
            f"{API}/events/{event.id}/status", headers=auth_headers
        )
        data = resp.json()
        assert data["currentStatus"] == "Archiving"
        assert data["statusInitiator"] == str(system_user.id)

    def test_archiviert_with_protected_vms_skipped(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        db_session,
        system_user,
        active_user,
        event_statuses,
        sample_course,
    ):
        from models import Event

        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"AV-{uuid.uuid4().hex[:6]}",
            slug=f"av{uuid.uuid4().hex[:4]}",
            dateStart=date(2026, 6, 1),
            dateEnd=date(2026, 6, 30),
            guacamole=False,
            status=event_statuses["Archiviert"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        task = _make_task(db_session, system_user, event, name="End Event")
        _make_subtask(db_session, active_user, task, status="success")
        # Protected VMs remain after archiving
        _make_vm(
            db_session, active_user, event, ipv4="10.0.0.1", prevent_delete=True
        )
        _make_vm(
            db_session, active_user, event, ipv4="10.0.0.2", prevent_delete=True
        )

        resp = client.get(
            f"{API}/events/{event.id}/status", headers=auth_headers
        )
        data = resp.json()
        assert data["currentStatus"] == "Archiviert"
        assert data["statusInitiator"] == str(system_user.id)
        assert data["vmStats"]["protected"] == 2
        assert data["taskStats"]["success"] == 1

    # ------------------------------------------------------------------
    # Error states
    # ------------------------------------------------------------------

    def test_deployment_fehler(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        db_session,
        system_user,
        active_user,
        event_statuses,
        sample_course,
    ):
        from models import Event

        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"DE-{uuid.uuid4().hex[:6]}",
            slug=f"de{uuid.uuid4().hex[:4]}",
            dateStart=date(2026, 6, 1),
            dateEnd=date(2026, 6, 30),
            guacamole=False,
            status=event_statuses["Deployment Fehler"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        task = _make_task(db_session, system_user, event, name="Start Event")
        _make_subtask(db_session, active_user, task, status="failed")
        # Some VMs deployed, some still pending
        _make_vm(
            db_session, active_user, event, vm_status="running", ipv4="10.0.0.1"
        )
        _make_vm(db_session, active_user, event, vm_status="stopped", ipv4=None)

        resp = client.get(
            f"{API}/events/{event.id}/status", headers=auth_headers
        )
        data = resp.json()
        assert data["currentStatus"] == "Deployment Fehler"
        assert data["statusInitiator"] == str(system_user.id)
        assert data["vmStats"]["total"] == 2
        assert data["vmStats"]["pending"] == 1
        assert data["taskStats"]["failed"] == 1

    def test_archival_fehler(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        db_session,
        system_user,
        active_user,
        event_statuses,
        sample_course,
    ):
        from models import Event

        now = datetime.now(timezone.utc)
        event = Event(
            id=uuid.uuid4(),
            name=f"AF-{uuid.uuid4().hex[:6]}",
            slug=f"af{uuid.uuid4().hex[:4]}",
            dateStart=date(2026, 6, 1),
            dateEnd=date(2026, 6, 30),
            guacamole=False,
            status=event_statuses["Archival Fehler"].id,
            course=sample_course.id,
            createdAt=now,
            updatedAt=now,
            createdById=active_user.id,
            updatedById=active_user.id,
        )
        db_session.add(event)
        db_session.flush()

        task = _make_task(db_session, system_user, event, name="End Event")
        _make_subtask(db_session, active_user, task, status="failed")
        _make_vm(
            db_session, active_user, event, ipv4="10.0.0.1"
        )  # VM still exists

        resp = client.get(
            f"{API}/events/{event.id}/status", headers=auth_headers
        )
        data = resp.json()
        assert data["currentStatus"] == "Archival Fehler"
        assert data["statusInitiator"] == str(system_user.id)
        assert data["vmStats"]["total"] == 1
        assert data["taskStats"]["failed"] == 1
