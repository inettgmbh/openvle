"""Integration tests for /v{x}/virtual_machines/ endpoints."""

import uuid
from datetime import datetime, timezone

import pytest

from tests.integration.conftest import API


@pytest.fixture()
def sample_vm(db_session, system_user):
    """Create a VM in the test DB (no PVE interaction)."""
    from models import VirtualMachine

    now = datetime.now(timezone.utc)
    vm = VirtualMachine(
        id=uuid.uuid4(),
        name=f"test-vm-{uuid.uuid4().hex[:6]}",
        description="A test VM",
        cpu=2,
        ram=4096,
        disk=20,
        status="running",
        ipv4="10.0.1.50",
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vm)
    db_session.flush()
    return vm


# ------------------------------------------------------------------
# POST /virtual_machines/ -- create VM from template
# ------------------------------------------------------------------
class TestCreateVirtualMachine:
    """POST /virtual_machines/ -- create VM (contacts PVE)."""

    def test_create_unauthenticated_returns_401(self, client):
        payload = {
            "name": "unauth-vm",
            "cpu": 2,
            "ram": 4096,
            "template": str(uuid.uuid4()),
        }
        resp = client.post(f"{API}/virtual_machines/", json=payload)
        assert resp.status_code in (401, 403)

    def test_create_permission_denied_returns_403(self, client, auth_headers):
        """Without mock_permission_allow, vms_create is denied."""
        payload = {
            "name": "denied-vm",
            "cpu": 2,
            "ram": 4096,
            "template": str(uuid.uuid4()),
        }
        resp = client.post(
            f"{API}/virtual_machines/",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


# ------------------------------------------------------------------
# GET /virtual_machines/ -- list VMs
# ------------------------------------------------------------------
class TestGetVirtualMachines:
    """GET /virtual_machines/ -- list all VMs."""

    def test_returns_paginated_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_vm,
    ):
        resp = client.get(f"{API}/virtual_machines/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(f"{API}/virtual_machines/")
        assert resp.status_code in (401, 403)

    def test_without_permission_falls_through_to_auth(
        self, client, auth_headers, sample_vm
    ):
        """Without mock_permission_allow the list endpoint falls through
        to get_multi_auth which returns items filtered by object
        permissions (likely empty for the test user)."""
        resp = client.get(f"{API}/virtual_machines/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data


# ------------------------------------------------------------------
# GET /virtual_machines/{id} -- get single VM
# ------------------------------------------------------------------
class TestGetVirtualMachineById:
    """GET /virtual_machines/{id} -- get single VM."""

    def test_returns_vm(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_vm,
    ):
        resp = client.get(
            f"{API}/virtual_machines/{sample_vm.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_vm.id)
        assert data["name"] == sample_vm.name
        assert data["cpu"] == sample_vm.cpu
        assert data["ram"] == sample_vm.ram
        assert data["disk"] == sample_vm.disk

    def test_not_found_returns_404(self, client, auth_headers, mock_permission_allow):
        fake_id = uuid.uuid4()
        resp = client.get(
            f"{API}/virtual_machines/{fake_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/virtual_machines/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_permission_denied_returns_403(self, client, auth_headers, sample_vm):
        """Without mock_permission_allow, vms_read is denied."""
        resp = client.get(
            f"{API}/virtual_machines/{sample_vm.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 403


# ------------------------------------------------------------------
# PUT /virtual_machines/{id} -- update VM (contacts PVE for resize)
# ------------------------------------------------------------------
class TestUpdateVirtualMachine:
    """PUT /virtual_machines/{id} -- update VM."""

    def test_update_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        payload = {"name": "ghost-vm", "description": "Does not exist"}
        resp = client.put(
            f"{API}/virtual_machines/{fake_id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_update_unauthenticated_returns_401(self, client):
        """Use fake UUID so ChangelogMiddleware exits early."""
        fake_id = uuid.uuid4()
        payload = {"name": "no-auth-vm"}
        resp = client.put(f"{API}/virtual_machines/{fake_id}", json=payload)
        assert resp.status_code in (401, 403)

    def test_update_permission_denied_returns_403(
        self, client, auth_headers, sample_vm
    ):
        """Without mock_permission_allow, vms_update is denied."""
        payload = {"name": "denied-vm"}
        resp = client.put(
            f"{API}/virtual_machines/{sample_vm.id}",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


# ------------------------------------------------------------------
# DELETE /virtual_machines/{id} -- delete VM (contacts PVE)
# ------------------------------------------------------------------
class TestDeleteVirtualMachine:
    """DELETE /virtual_machines/{id} -- delete VM."""

    def test_delete_not_found_returns_404(
        self, client, auth_headers, mock_permission_allow
    ):
        fake_id = uuid.uuid4()
        resp = client.delete(
            f"{API}/virtual_machines/{fake_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_delete_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/virtual_machines/{fake_id}")
        assert resp.status_code in (401, 403)

    def test_delete_permission_denied_returns_403(
        self, client, auth_headers, sample_vm
    ):
        """Without mock_permission_allow, vms_delete is denied."""
        resp = client.delete(
            f"{API}/virtual_machines/{sample_vm.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 403


# ------------------------------------------------------------------
# GET /virtual_machines/{id}/applications -- get VM apps
# ------------------------------------------------------------------
class TestGetVirtualMachineApps:
    """GET /virtual_machines/{id}/applications -- list apps for a VM."""

    def test_returns_empty_apps_list(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_vm,
    ):
        resp = client.get(
            f"{API}/virtual_machines/{sample_vm.id}/applications",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pageDetails" in data
        assert "items" in data
        assert data["items"] == []

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/virtual_machines/{fake_id}/applications")
        assert resp.status_code in (401, 403)


# ------------------------------------------------------------------
# PUT /virtual_machines/{id}/applications -- update VM apps
# ------------------------------------------------------------------
class TestUpdateVirtualMachineApps:
    """PUT /virtual_machines/{id}/applications -- update VM apps."""

    def test_update_apps_unauthenticated_returns_401(self, client):
        """Use fake UUID so ChangelogMiddleware exits early."""
        fake_id = uuid.uuid4()
        payload = {"apps": []}
        resp = client.put(
            f"{API}/virtual_machines/{fake_id}/applications",
            json=payload,
        )
        assert resp.status_code in (401, 403)

    def test_update_apps_permission_denied_returns_403(
        self, client, auth_headers, sample_vm
    ):
        """Without mock_permission_allow, vms_update is denied."""
        payload = {"apps": []}
        resp = client.put(
            f"{API}/virtual_machines/{sample_vm.id}/applications",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


# ------------------------------------------------------------------
# GET /virtual_machines/{id}/guacamole -- get VM guacamole
# ------------------------------------------------------------------
class TestGetVirtualMachineGuacamole:
    """GET /virtual_machines/{id}/guacamole -- list guacamole for a VM."""

    def test_returns_422_vmid_field_not_on_model(
        self,
        client,
        auth_headers,
        mock_permission_allow,
        sample_vm,
    ):
        """The route uses foreign_key_field='vmId' but Guacamole has no
        vmId column (it's M2M via association table). This is a known
        production code issue that returns 422 (ModelFieldNotFound)."""
        resp = client.get(
            f"{API}/virtual_machines/{sample_vm.id}/guacamole",
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/virtual_machines/{fake_id}/guacamole")
        assert resp.status_code in (401, 403)


# ------------------------------------------------------------------
# GET /virtual_machines/{id}/ipv4 -- get IPv4 from PVE
# ------------------------------------------------------------------
class TestGetVirtualMachineIpv4:
    """GET /virtual_machines/{id}/ipv4 -- PVE-dependent."""

    def test_ipv4_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/virtual_machines/{fake_id}/ipv4")
        assert resp.status_code in (401, 403)

    def test_ipv4_permission_denied_returns_403(self, client, auth_headers, sample_vm):
        """Without mock_permission_allow, vms_read is denied."""
        resp = client.get(
            f"{API}/virtual_machines/{sample_vm.id}/ipv4",
            headers=auth_headers,
        )
        assert resp.status_code == 403


# ------------------------------------------------------------------
# VM Actions (individual) -- all PVE-dependent, test auth/permission
# ------------------------------------------------------------------
class TestVirtualMachineActionClone:
    """POST /virtual_machines/{id}/actions/clone -- clone VM."""

    def test_clone_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        payload = {
            "name": "clone-vm",
            "description": "cloned",
            "cpu": 2,
            "ram": 4096,
        }
        resp = client.post(
            f"{API}/virtual_machines/{fake_id}/actions/clone",
            json=payload,
        )
        assert resp.status_code in (401, 403)

    def test_clone_permission_denied_returns_403(self, client, auth_headers, sample_vm):
        payload = {
            "name": "clone-vm",
            "description": "cloned",
            "cpu": 2,
            "ram": 4096,
        }
        resp = client.post(
            f"{API}/virtual_machines/{sample_vm.id}/actions/clone",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestVirtualMachineActionMigrate:
    """POST /virtual_machines/{id}/actions/migrate -- migrate VM."""

    def test_migrate_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        payload = {"targetNode": "pve1"}
        resp = client.post(
            f"{API}/virtual_machines/{fake_id}/actions/migrate",
            json=payload,
        )
        assert resp.status_code in (401, 403)

    def test_migrate_permission_denied_returns_403(
        self, client, auth_headers, sample_vm
    ):
        payload = {"targetNode": "pve1"}
        resp = client.post(
            f"{API}/virtual_machines/{sample_vm.id}/actions/migrate",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestVirtualMachineActionHaGet:
    """GET /virtual_machines/{id}/actions/ha -- get HA state."""

    def test_ha_get_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/virtual_machines/{fake_id}/actions/ha")
        assert resp.status_code in (401, 403)

    def test_ha_get_permission_denied_returns_403(
        self, client, auth_headers, sample_vm
    ):
        resp = client.get(
            f"{API}/virtual_machines/{sample_vm.id}/actions/ha",
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestVirtualMachineActionHaSet:
    """POST /virtual_machines/{id}/actions/ha -- set HA parameters."""

    def test_ha_set_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        payload = {
            "ha_state": "started",
            "ha_max_restart": 5,
            "ha_max_relocate": 5,
        }
        resp = client.post(
            f"{API}/virtual_machines/{fake_id}/actions/ha",
            json=payload,
        )
        assert resp.status_code in (401, 403)

    def test_ha_set_permission_denied_returns_403(
        self, client, auth_headers, sample_vm
    ):
        payload = {
            "ha_state": "started",
            "ha_max_restart": 5,
            "ha_max_relocate": 5,
        }
        resp = client.post(
            f"{API}/virtual_machines/{sample_vm.id}/actions/ha",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestVirtualMachineActionHaRemove:
    """DELETE /virtual_machines/{id}/actions/ha -- remove from HA."""

    def test_ha_remove_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.delete(f"{API}/virtual_machines/{fake_id}/actions/ha")
        assert resp.status_code in (401, 403)

    def test_ha_remove_permission_denied_returns_403(
        self, client, auth_headers, sample_vm
    ):
        resp = client.delete(
            f"{API}/virtual_machines/{sample_vm.id}/actions/ha",
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestVirtualMachineActionStop:
    """POST /virtual_machines/{id}/actions/stop -- stop VM."""

    def test_stop_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.post(f"{API}/virtual_machines/{fake_id}/actions/stop")
        assert resp.status_code in (401, 403)

    def test_stop_permission_denied_returns_403(self, client, auth_headers, sample_vm):
        resp = client.post(
            f"{API}/virtual_machines/{sample_vm.id}/actions/stop",
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestVirtualMachineActionStart:
    """POST /virtual_machines/{id}/actions/start -- start VM."""

    def test_start_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.post(f"{API}/virtual_machines/{fake_id}/actions/start")
        assert resp.status_code in (401, 403)

    def test_start_permission_denied_returns_403(self, client, auth_headers, sample_vm):
        resp = client.post(
            f"{API}/virtual_machines/{sample_vm.id}/actions/start",
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestVirtualMachineActionReboot:
    """POST /virtual_machines/{id}/actions/reboot -- reboot VM."""

    def test_reboot_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.post(f"{API}/virtual_machines/{fake_id}/actions/reboot")
        assert resp.status_code in (401, 403)

    def test_reboot_permission_denied_returns_403(
        self, client, auth_headers, sample_vm
    ):
        resp = client.post(
            f"{API}/virtual_machines/{sample_vm.id}/actions/reboot",
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestVirtualMachineActionReset:
    """POST /virtual_machines/{id}/actions/reset -- reset VM."""

    def test_reset_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.post(f"{API}/virtual_machines/{fake_id}/actions/reset")
        assert resp.status_code in (401, 403)

    def test_reset_permission_denied_returns_403(self, client, auth_headers, sample_vm):
        resp = client.post(
            f"{API}/virtual_machines/{sample_vm.id}/actions/reset",
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestVirtualMachineActionPause:
    """POST /virtual_machines/{id}/actions/pause -- pause VM."""

    def test_pause_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.post(f"{API}/virtual_machines/{fake_id}/actions/pause")
        assert resp.status_code in (401, 403)

    def test_pause_permission_denied_returns_403(self, client, auth_headers, sample_vm):
        resp = client.post(
            f"{API}/virtual_machines/{sample_vm.id}/actions/pause",
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestVirtualMachineActionShutdown:
    """POST /virtual_machines/{id}/actions/shutdown -- shutdown VM."""

    def test_shutdown_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.post(f"{API}/virtual_machines/{fake_id}/actions/shutdown")
        assert resp.status_code in (401, 403)

    def test_shutdown_permission_denied_returns_403(
        self, client, auth_headers, sample_vm
    ):
        resp = client.post(
            f"{API}/virtual_machines/{sample_vm.id}/actions/shutdown",
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestVirtualMachineActionResume:
    """POST /virtual_machines/{id}/actions/resume -- resume VM."""

    def test_resume_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.post(f"{API}/virtual_machines/{fake_id}/actions/resume")
        assert resp.status_code in (401, 403)

    def test_resume_permission_denied_returns_403(
        self, client, auth_headers, sample_vm
    ):
        resp = client.post(
            f"{API}/virtual_machines/{sample_vm.id}/actions/resume",
            headers=auth_headers,
        )
        assert resp.status_code == 403


# ------------------------------------------------------------------
# GET /virtual_machines/{id}/rrddata -- RRD data (PVE-dependent)
# ------------------------------------------------------------------
class TestGetVirtualMachineRrddata:
    """GET /virtual_machines/{id}/rrddata -- PVE-dependent."""

    def test_rrddata_unauthenticated_returns_401(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"{API}/virtual_machines/{fake_id}/rrddata")
        assert resp.status_code in (401, 403)

    def test_rrddata_permission_denied_returns_403(
        self, client, auth_headers, sample_vm
    ):
        """Without mock_permission_allow, vms_read is denied."""
        resp = client.get(
            f"{API}/virtual_machines/{sample_vm.id}/rrddata",
            headers=auth_headers,
        )
        assert resp.status_code == 403


# ------------------------------------------------------------------
# Bulk Actions -- all PVE-dependent, test auth/permission only
# ------------------------------------------------------------------
class TestBulkActionStart:
    """POST /virtual_machines/bulk-actions/start -- bulk start."""

    def test_bulk_start_unauthenticated_returns_401(self, client):
        payload = {"vms": [str(uuid.uuid4())]}
        resp = client.post(
            f"{API}/virtual_machines/bulk-actions/start",
            json=payload,
        )
        assert resp.status_code in (401, 403)

    def test_bulk_start_permission_denied_returns_403(self, client, auth_headers):
        payload = {"vms": [str(uuid.uuid4())]}
        resp = client.post(
            f"{API}/virtual_machines/bulk-actions/start",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestBulkActionStop:
    """POST /virtual_machines/bulk-actions/stop -- bulk stop."""

    def test_bulk_stop_unauthenticated_returns_401(self, client):
        payload = {"vms": [str(uuid.uuid4())]}
        resp = client.post(
            f"{API}/virtual_machines/bulk-actions/stop",
            json=payload,
        )
        assert resp.status_code in (401, 403)

    def test_bulk_stop_permission_denied_returns_403(self, client, auth_headers):
        payload = {"vms": [str(uuid.uuid4())]}
        resp = client.post(
            f"{API}/virtual_machines/bulk-actions/stop",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestBulkActionPause:
    """POST /virtual_machines/bulk-actions/pause -- bulk pause."""

    def test_bulk_pause_unauthenticated_returns_401(self, client):
        payload = {"vms": [str(uuid.uuid4())]}
        resp = client.post(
            f"{API}/virtual_machines/bulk-actions/pause",
            json=payload,
        )
        assert resp.status_code in (401, 403)

    def test_bulk_pause_permission_denied_returns_403(self, client, auth_headers):
        payload = {"vms": [str(uuid.uuid4())]}
        resp = client.post(
            f"{API}/virtual_machines/bulk-actions/pause",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestBulkActionReset:
    """POST /virtual_machines/bulk-actions/reset -- bulk reset."""

    def test_bulk_reset_unauthenticated_returns_401(self, client):
        payload = {"vms": [str(uuid.uuid4())]}
        resp = client.post(
            f"{API}/virtual_machines/bulk-actions/reset",
            json=payload,
        )
        assert resp.status_code in (401, 403)

    def test_bulk_reset_permission_denied_returns_403(self, client, auth_headers):
        payload = {"vms": [str(uuid.uuid4())]}
        resp = client.post(
            f"{API}/virtual_machines/bulk-actions/reset",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestBulkActionReboot:
    """POST /virtual_machines/bulk-actions/reboot -- bulk reboot."""

    def test_bulk_reboot_unauthenticated_returns_401(self, client):
        payload = {"vms": [str(uuid.uuid4())]}
        resp = client.post(
            f"{API}/virtual_machines/bulk-actions/reboot",
            json=payload,
        )
        assert resp.status_code in (401, 403)

    def test_bulk_reboot_permission_denied_returns_403(self, client, auth_headers):
        payload = {"vms": [str(uuid.uuid4())]}
        resp = client.post(
            f"{API}/virtual_machines/bulk-actions/reboot",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestBulkActionShutdown:
    """POST /virtual_machines/bulk-actions/shutdown -- bulk shutdown."""

    def test_bulk_shutdown_unauthenticated_returns_401(self, client):
        payload = {"vms": [str(uuid.uuid4())]}
        resp = client.post(
            f"{API}/virtual_machines/bulk-actions/shutdown",
            json=payload,
        )
        assert resp.status_code in (401, 403)

    def test_bulk_shutdown_permission_denied_returns_403(self, client, auth_headers):
        payload = {"vms": [str(uuid.uuid4())]}
        resp = client.post(
            f"{API}/virtual_machines/bulk-actions/shutdown",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestBulkActionResume:
    """POST /virtual_machines/bulk-actions/resume -- bulk resume."""

    def test_bulk_resume_unauthenticated_returns_401(self, client):
        payload = {"vms": [str(uuid.uuid4())]}
        resp = client.post(
            f"{API}/virtual_machines/bulk-actions/resume",
            json=payload,
        )
        assert resp.status_code in (401, 403)

    def test_bulk_resume_permission_denied_returns_403(self, client, auth_headers):
        payload = {"vms": [str(uuid.uuid4())]}
        resp = client.post(
            f"{API}/virtual_machines/bulk-actions/resume",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestBulkActionHaAdd:
    """POST /virtual_machines/bulk-actions/ha -- bulk HA add."""

    def test_bulk_ha_add_unauthenticated_returns_401(self, client):
        payload = {
            "vms": [str(uuid.uuid4())],
            "ha_state": "started",
        }
        resp = client.post(
            f"{API}/virtual_machines/bulk-actions/ha",
            json=payload,
        )
        assert resp.status_code in (401, 403)

    def test_bulk_ha_add_permission_denied_returns_403(self, client, auth_headers):
        payload = {
            "vms": [str(uuid.uuid4())],
            "ha_state": "started",
        }
        resp = client.post(
            f"{API}/virtual_machines/bulk-actions/ha",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestBulkActionHaRemove:
    """DELETE /virtual_machines/bulk-actions/ha -- bulk HA remove."""

    def test_bulk_ha_remove_unauthenticated_returns_401(self, client):
        payload = {"vms": [str(uuid.uuid4())]}
        resp = client.delete(
            f"{API}/virtual_machines/bulk-actions/ha",
            json=payload,
        )
        assert resp.status_code in (401, 403)

    def test_bulk_ha_remove_permission_denied_returns_403(self, client, auth_headers):
        payload = {"vms": [str(uuid.uuid4())]}
        resp = client.delete(
            f"{API}/virtual_machines/bulk-actions/ha",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestBulkActionMigrate:
    """POST /virtual_machines/bulk-actions/migrate -- bulk migrate."""

    def test_bulk_migrate_unauthenticated_returns_401(self, client):
        payload = {
            "vms": [str(uuid.uuid4())],
            "targetNode": "pve1",
        }
        resp = client.post(
            f"{API}/virtual_machines/bulk-actions/migrate",
            json=payload,
        )
        assert resp.status_code in (401, 403)

    def test_bulk_migrate_permission_denied_returns_403(self, client, auth_headers):
        payload = {
            "vms": [str(uuid.uuid4())],
            "targetNode": "pve1",
        }
        resp = client.post(
            f"{API}/virtual_machines/bulk-actions/migrate",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 403
