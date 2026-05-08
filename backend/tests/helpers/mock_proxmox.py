"""Mock for Proxmox VE cluster."""

from unittest.mock import MagicMock


class MockProxmoxCluster:
    """Mock for ProxmoxCluster used in pve/ modules."""

    def __init__(self):
        self.nodes = MagicMock()
        self.proxmox = MagicMock()

    def pve_get_node(self, vm_id):
        return "pve-node-01"

    def next_vm_id(self, db=None):
        return 9999

    def get_free_node(self):
        return "pve-node-01"
