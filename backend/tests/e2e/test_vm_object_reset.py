"""
E2E tests for object_reset permission on VirtualMachines.

Verifies that object_reset implies read access so that users who can
reset/stop/start a VM can also see it in list and get endpoints.
Tests the fix for the bug where object_reset was a standalone permission
that did not grant visibility.
"""

import uuid
from datetime import datetime, timezone

from tests.e2e.conftest import API

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _create_vm(db_session, system_user, name="test-vm", ipv4="10.0.1.50"):
    """Create a VirtualMachine directly in DB."""
    from models import VirtualMachine

    now = datetime.now(timezone.utc)
    vm = VirtualMachine(
        id=uuid.uuid4(),
        name=f"{name}-{uuid.uuid4().hex[:6]}",
        description="VM for object_reset tests",
        cpu=2,
        ram=4096,
        disk=20,
        status="running",
        ipv4=ipv4,
        createdAt=now,
        updatedAt=now,
        createdById=system_user.id,
        updatedById=system_user.id,
    )
    db_session.add(vm)
    db_session.flush()
    return vm


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
# Scenario A: object_reset grants read visibility
# ------------------------------------------------------------------


class TestObjectResetGrantsReadVisibility:
    """object_reset on a VM should make it visible in list and get."""

    def test_vm_visible_in_list_with_object_reset(
        self,
        client,
        db_session,
        system_user,
        user_b,
        user_b_headers,
    ):
        """VM with object_reset appears in GET /virtual_machines/ list."""
        vm = _create_vm(db_session, system_user, ipv4="10.0.2.10")
        _create_object_permission(
            db_session,
            system_user,
            "VirtualMachine",
            vm.id,
            user_b.id,
            permission_key="object_reset",
        )

        resp = client.get(f"{API}/virtual_machines/", headers=user_b_headers)
        assert resp.status_code == 200
        items = resp.json()["items"]
        item_ids = [item["id"] for item in items]
        assert str(vm.id) in item_ids

    def test_vm_accessible_via_get_with_object_reset(
        self,
        client,
        db_session,
        system_user,
        user_b,
        user_b_headers,
    ):
        """VM with object_reset can be retrieved via GET /virtual_machines/{id}."""
        vm = _create_vm(db_session, system_user, ipv4="10.0.2.11")
        _create_object_permission(
            db_session,
            system_user,
            "VirtualMachine",
            vm.id,
            user_b.id,
            permission_key="object_reset",
        )

        resp = client.get(
            f"{API}/virtual_machines/{vm.id}", headers=user_b_headers
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == str(vm.id)

    def test_vm_not_visible_without_any_permission(
        self,
        client,
        db_session,
        system_user,
        user_b,
        user_b_headers,
    ):
        """VM without any permission is not visible (baseline)."""
        _create_vm(db_session, system_user, ipv4="10.0.2.12")

        resp = client.get(f"{API}/virtual_machines/", headers=user_b_headers)
        assert resp.status_code == 200
        assert resp.json()["items"] == []

    def test_get_vm_denied_without_any_permission(
        self,
        client,
        db_session,
        system_user,
        user_b,
        user_b_headers,
    ):
        """GET single VM without any permission returns 403 (baseline)."""
        vm = _create_vm(db_session, system_user, ipv4="10.0.2.13")

        resp = client.get(
            f"{API}/virtual_machines/{vm.id}", headers=user_b_headers
        )
        assert resp.status_code == 403


# ------------------------------------------------------------------
# Scenario B: object_reset filters correctly (no data leaks)
# ------------------------------------------------------------------


class TestObjectResetFiltering:
    """object_reset on VM-A must not leak VM-B."""

    def test_list_returns_only_permitted_vms(
        self,
        client,
        db_session,
        system_user,
        user_b,
        user_b_headers,
    ):
        """Only VMs with object_reset appear; others are hidden."""
        vm_visible = _create_vm(
            db_session, system_user, name="visible", ipv4="10.0.3.10"
        )
        vm_hidden = _create_vm(
            db_session, system_user, name="hidden", ipv4="10.0.3.11"
        )

        _create_object_permission(
            db_session,
            system_user,
            "VirtualMachine",
            vm_visible.id,
            user_b.id,
            permission_key="object_reset",
        )

        resp = client.get(f"{API}/virtual_machines/", headers=user_b_headers)
        assert resp.status_code == 200
        items = resp.json()["items"]
        item_ids = [item["id"] for item in items]
        assert str(vm_visible.id) in item_ids
        assert str(vm_hidden.id) not in item_ids

    def test_list_shows_vms_with_mixed_permissions(
        self,
        client,
        db_session,
        system_user,
        user_b,
        user_b_headers,
    ):
        """VMs with object_reset + VMs with object_read both appear."""
        vm_reset = _create_vm(
            db_session, system_user, name="reset-vm", ipv4="10.0.3.20"
        )
        vm_read = _create_vm(
            db_session, system_user, name="read-vm", ipv4="10.0.3.21"
        )
        vm_none = _create_vm(
            db_session, system_user, name="none-vm", ipv4="10.0.3.22"
        )

        _create_object_permission(
            db_session,
            system_user,
            "VirtualMachine",
            vm_reset.id,
            user_b.id,
            permission_key="object_reset",
        )
        _create_object_permission(
            db_session,
            system_user,
            "VirtualMachine",
            vm_read.id,
            user_b.id,
            permission_key="object_read",
        )

        resp = client.get(f"{API}/virtual_machines/", headers=user_b_headers)
        assert resp.status_code == 200
        item_ids = [item["id"] for item in resp.json()["items"]]
        assert str(vm_reset.id) in item_ids
        assert str(vm_read.id) in item_ids
        assert str(vm_none.id) not in item_ids


# ------------------------------------------------------------------
# Scenario C: object_reset does NOT grant update or delete
# ------------------------------------------------------------------


class TestObjectResetDoesNotGrantWriteAccess:
    """object_reset implies read but NOT update or delete."""

    def test_object_reset_denies_update(
        self,
        client,
        db_session,
        system_user,
        user_b,
        user_b_headers,
    ):
        """User with object_reset cannot PUT (update) the VM."""
        vm = _create_vm(db_session, system_user, ipv4="10.0.4.10")
        _create_object_permission(
            db_session,
            system_user,
            "VirtualMachine",
            vm.id,
            user_b.id,
            permission_key="object_reset",
        )

        resp = client.put(
            f"{API}/virtual_machines/{vm.id}",
            json={"name": "Updated Name"},
            headers=user_b_headers,
        )
        assert resp.status_code == 403

    def test_object_reset_denies_delete(
        self,
        client,
        db_session,
        system_user,
        user_b,
        user_b_headers,
    ):
        """User with object_reset cannot DELETE the VM."""
        vm = _create_vm(db_session, system_user, ipv4="10.0.4.11")
        _create_object_permission(
            db_session,
            system_user,
            "VirtualMachine",
            vm.id,
            user_b.id,
            permission_key="object_reset",
        )

        resp = client.delete(
            f"{API}/virtual_machines/{vm.id}",
            headers=user_b_headers,
        )
        assert resp.status_code == 403


# ------------------------------------------------------------------
# Scenario D: object_reset via role grants read visibility
# ------------------------------------------------------------------


class TestObjectResetViaRole:
    """object_reset assigned to a role grants read visibility to role members."""

    def test_role_object_reset_grants_vm_list_visibility(
        self,
        client,
        db_session,
        system_user,
        role_teacher,
        teacher_user,
        teacher_headers,
    ):
        """object_reset on a Role makes the VM visible in list for role members."""
        vm = _create_vm(db_session, system_user, ipv4="10.0.5.10")
        _create_object_permission(
            db_session,
            system_user,
            "VirtualMachine",
            vm.id,
            role_teacher.id,
            entity_type="Role",
            permission_key="object_reset",
        )

        resp = client.get(f"{API}/virtual_machines/", headers=teacher_headers)
        assert resp.status_code == 200
        item_ids = [item["id"] for item in resp.json()["items"]]
        assert str(vm.id) in item_ids

    def test_role_object_reset_grants_vm_get(
        self,
        client,
        db_session,
        system_user,
        role_teacher,
        teacher_user,
        teacher_headers,
    ):
        """object_reset on a Role allows GET /virtual_machines/{id}."""
        vm = _create_vm(db_session, system_user, ipv4="10.0.5.11")
        _create_object_permission(
            db_session,
            system_user,
            "VirtualMachine",
            vm.id,
            role_teacher.id,
            entity_type="Role",
            permission_key="object_reset",
        )

        resp = client.get(
            f"{API}/virtual_machines/{vm.id}", headers=teacher_headers
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == str(vm.id)


# ------------------------------------------------------------------
# Scenario E: global object_reset grants read on all VMs
# ------------------------------------------------------------------


class TestGlobalObjectReset:
    """Global object_reset (object_id=None) grants read on all VMs."""

    def test_global_object_reset_makes_all_vms_visible(
        self,
        client,
        db_session,
        system_user,
        user_b,
        user_b_headers,
    ):
        """Global object_reset lists all VMs of that type."""
        vm_a = _create_vm(
            db_session, system_user, name="global-a", ipv4="10.0.6.10"
        )
        vm_b = _create_vm(
            db_session, system_user, name="global-b", ipv4="10.0.6.11"
        )

        # Global permission (object_id=None)
        _create_object_permission(
            db_session,
            system_user,
            "VirtualMachine",
            None,
            user_b.id,
            permission_key="object_reset",
        )

        resp = client.get(f"{API}/virtual_machines/", headers=user_b_headers)
        assert resp.status_code == 200
        item_ids = [item["id"] for item in resp.json()["items"]]
        assert str(vm_a.id) in item_ids
        assert str(vm_b.id) in item_ids


# ------------------------------------------------------------------
# Scenario F: comparison with standard CRUD permissions
# ------------------------------------------------------------------


class TestObjectResetComparedToStandardPerms:
    """Verify object_reset behaves like other read-granting permissions
    for visibility, but does not escalate to update/delete."""

    def test_object_read_and_object_reset_both_grant_get(
        self,
        client,
        db_session,
        system_user,
        user_b,
        user_b_headers,
    ):
        """Both object_read and object_reset allow GET on a VM."""
        vm_read = _create_vm(
            db_session, system_user, name="cmp-read", ipv4="10.0.7.10"
        )
        vm_reset = _create_vm(
            db_session, system_user, name="cmp-reset", ipv4="10.0.7.11"
        )

        _create_object_permission(
            db_session,
            system_user,
            "VirtualMachine",
            vm_read.id,
            user_b.id,
            permission_key="object_read",
        )
        _create_object_permission(
            db_session,
            system_user,
            "VirtualMachine",
            vm_reset.id,
            user_b.id,
            permission_key="object_reset",
        )

        resp_read = client.get(
            f"{API}/virtual_machines/{vm_read.id}", headers=user_b_headers
        )
        resp_reset = client.get(
            f"{API}/virtual_machines/{vm_reset.id}", headers=user_b_headers
        )
        assert resp_read.status_code == 200
        assert resp_reset.status_code == 200

    def test_object_update_grants_more_than_object_reset(
        self,
        client,
        db_session,
        system_user,
        user_b,
        user_b_headers,
    ):
        """object_update allows PUT, object_reset does not."""
        vm_update = _create_vm(
            db_session, system_user, name="cmp-upd", ipv4="10.0.7.20"
        )
        vm_reset = _create_vm(
            db_session, system_user, name="cmp-rst", ipv4="10.0.7.21"
        )

        _create_object_permission(
            db_session,
            system_user,
            "VirtualMachine",
            vm_update.id,
            user_b.id,
            permission_key="object_update",
        )
        _create_object_permission(
            db_session,
            system_user,
            "VirtualMachine",
            vm_reset.id,
            user_b.id,
            permission_key="object_reset",
        )

        # Both can GET
        resp_upd_get = client.get(
            f"{API}/virtual_machines/{vm_update.id}", headers=user_b_headers
        )
        resp_rst_get = client.get(
            f"{API}/virtual_machines/{vm_reset.id}", headers=user_b_headers
        )
        assert resp_upd_get.status_code == 200
        assert resp_rst_get.status_code == 200

        # Only object_update can PUT
        resp_upd_put = client.put(
            f"{API}/virtual_machines/{vm_update.id}",
            json={"description": "Updated"},
            headers=user_b_headers,
        )
        resp_rst_put = client.put(
            f"{API}/virtual_machines/{vm_reset.id}",
            json={"description": "Should fail"},
            headers=user_b_headers,
        )
        assert resp_upd_put.status_code == 200
        assert resp_rst_put.status_code == 403
