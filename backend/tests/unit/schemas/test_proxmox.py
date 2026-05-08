"""Tests for schemas/proxmox.py - Proxmox enums and metrics schemas."""

from schemas.proxmox import (
    ProxmoxBaseMetrics,
    ProxmoxNodeMetrics,
    ProxmoxRRDConsolidation,
    ProxmoxRRDDataSource,
    ProxmoxRRDTimeframe,
    ProxmoxVMMetrics,
)


class TestProxmoxEnums:
    def test_consolidation_values(self):
        assert ProxmoxRRDConsolidation.AVERAGE.value == "AVERAGE"
        assert ProxmoxRRDConsolidation.MAX.value == "MAX"
        assert len(ProxmoxRRDConsolidation) == 2

    def test_datasource_count(self):
        assert len(ProxmoxRRDDataSource) == 18

    def test_datasource_contains_expected(self):
        values = {d.value for d in ProxmoxRRDDataSource}
        assert "cpu" in values
        assert "memused" in values
        assert "netin" in values
        assert "netout" in values

    def test_timeframe_values(self):
        expected = {"hour", "day", "week", "month", "year", "decade"}
        assert {t.value for t in ProxmoxRRDTimeframe} == expected


class TestProxmoxBaseMetrics:
    def test_all_defaults_none(self):
        m = ProxmoxBaseMetrics()
        assert m.cpu is None
        assert m.maxcpu is None
        assert m.netin is None
        assert m.netout is None
        assert m.time is None

    def test_with_values(self):
        m = ProxmoxBaseMetrics(cpu=0.75, maxcpu=4, time=1700000000)
        assert m.cpu == 0.75
        assert m.maxcpu == 4


class TestProxmoxNodeMetrics:
    def test_inherits_base_fields(self):
        m = ProxmoxNodeMetrics(cpu=0.5, loadavg=1.5, memused=4096.0)
        assert m.cpu == 0.5
        assert m.loadavg == 1.5
        assert m.memused == 4096.0

    def test_node_specific_fields_default_none(self):
        m = ProxmoxNodeMetrics()
        assert m.arcsize is None
        assert m.iowait is None
        assert m.roottotal is None
        assert m.swapused is None


class TestProxmoxVMMetrics:
    def test_vm_specific_fields(self):
        m = ProxmoxVMMetrics(disk=10.0, maxmem=8192, mem=4096.0)
        assert m.disk == 10.0
        assert m.maxmem == 8192
        assert m.mem == 4096.0

    def test_vm_defaults_none(self):
        m = ProxmoxVMMetrics()
        assert m.diskread is None
        assert m.diskwrite is None
        assert m.maxdisk is None
        assert m.memhost is None
