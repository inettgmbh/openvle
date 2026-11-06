from enum import Enum

from pydantic import BaseModel, Field, RootModel


# Proxmox rrd data consolidation functions
class ProxmoxRRDConsolidation(str, Enum):
    """Consolidation function to apply when fetching Proxmox RRD metrics."""

    AVERAGE = "AVERAGE"
    MAX = "MAX"


# Proxmox rrd data datasources
class ProxmoxRRDDataSource(str, Enum):
    """Available data sources for Proxmox RRD time-series queries."""

    ARCSIZE = "arcsize"
    CPU = "cpu"
    IOWAIT = "iowait"
    LOADAVG = "loadavg"
    MAXCPU = "maxcpu"
    MEMAVAILABLE = "memavailable"
    MEMUSED = "memused"
    NETIN = "netin"
    NETOUT = "netout"
    PRESSURE_CPU_SOME = "pressurecpusome"
    PRESSURE_IO_FULL = "pressureiofull"
    PRESSURE_IO_SOME = "pressureiosome"
    PRESSURE_MEMORY_FULL = "pressurememoryfull"
    PRESSURE_MEMORY_SOME = "pressurememorysome"
    ROOTTOTAL = "roottotal"
    ROOTUSED = "rootused"
    SWAPTOTAL = "swaptotal"
    SWAPUSED = "swapused"


# Proxmox rrd data timeframes
class ProxmoxRRDTimeframe(str, Enum):
    """Time window for Proxmox RRD metric queries."""

    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    DECADE = "decade"


# Proxmox base metrics
class ProxmoxBaseMetrics(BaseModel):
    """Common Proxmox metric fields shared by node and VM metric responses."""

    cpu: float | None = Field(
        None, description="CPU usage as a fraction of total CPU capacity"
    )
    maxcpu: int | None = Field(
        None, description="Total number of CPU cores available"
    )
    netin: float | None = Field(
        None, description="Incoming network traffic in bytes per second"
    )
    netout: float | None = Field(
        None, description="Outgoing network traffic in bytes per second"
    )
    pressurecpufull: float | None = Field(
        None, description="CPU full pressure stall information metric"
    )
    pressurecpusome: float | None = Field(
        None, description="CPU some pressure stall information metric"
    )
    pressureiofull: float | None = Field(
        None, description="I/O full pressure stall information metric"
    )
    pressureiosome: float | None = Field(
        None, description="I/O some pressure stall information metric"
    )
    pressurememoryfull: float | None = Field(
        None, description="Memory full pressure stall information metric"
    )
    pressurememorysome: float | None = Field(
        None, description="Memory some pressure stall information metric"
    )
    time: int | None = Field(
        None, description="Unix timestamp of the metric data point"
    )


# Proxmox node metrics
class ProxmoxNodeMetrics(ProxmoxBaseMetrics):
    """Metric data for a single Proxmox node at a point in time."""

    arcsize: float | None = Field(
        None, description="ZFS ARC cache size in bytes"
    )
    iowait: float | None = Field(
        None, description="I/O wait time as a fraction of CPU time"
    )
    loadavg: float | None = Field(None, description="System load average")
    memavailable: float | None = Field(
        None, description="Available memory in bytes"
    )
    memtotal: float | None = Field(
        None, description="Total installed memory in bytes"
    )
    memused: float | None = Field(None, description="Used memory in bytes")
    roottotal: float | None = Field(
        None, description="Total root filesystem size in bytes"
    )
    rootused: float | None = Field(
        None, description="Used root filesystem space in bytes"
    )
    swaptotal: float | None = Field(
        None, description="Total swap space in bytes"
    )
    swapused: float | None = Field(None, description="Used swap space in bytes")


# Proxmox vm metrics
class ProxmoxVMMetrics(ProxmoxBaseMetrics):
    """Metric data for a single Proxmox virtual machine at a point in time."""

    disk: float | None = Field(
        None, description="Disk I/O rate in bytes per second"
    )
    diskread: float | None = Field(
        None, description="Disk read throughput in bytes per second"
    )
    diskwrite: float | None = Field(
        None, description="Disk write throughput in bytes per second"
    )
    maxdisk: int | None = Field(
        None, description="Total disk size allocated to the VM in bytes"
    )
    maxmem: int | None = Field(
        None, description="Total memory allocated to the VM in bytes"
    )
    mem: float | None = Field(
        None, description="Memory used by the VM in bytes"
    )
    memhost: float | None = Field(
        None, description="Host memory consumed by the VM in bytes"
    )


# Response Models
class ProxmoxNodeMetricsList(RootModel[list[ProxmoxNodeMetrics]]):
    """List of Proxmox node metric data points for a time range."""

    pass


class ProxmoxVMMetricsList(RootModel[list[ProxmoxVMMetrics]]):
    """List of Proxmox VM metric data points for a time range."""

    pass
