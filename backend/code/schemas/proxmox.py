from enum import Enum

from pydantic import BaseModel, RootModel


# Proxmox rrd data consolidation functions
class ProxmoxRRDConsolidation(str, Enum):
    AVERAGE = "AVERAGE"
    MAX = "MAX"


# Proxmox rrd data datasources
class ProxmoxRRDDataSource(str, Enum):
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
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    DECADE = "decade"


# Proxmox base metrics
class ProxmoxBaseMetrics(BaseModel):
    cpu: float | None = None
    maxcpu: int | None = None
    netin: float | None = None
    netout: float | None = None
    pressurecpufull: float | None = None
    pressurecpusome: float | None = None
    pressureiofull: float | None = None
    pressureiosome: float | None = None
    pressurememoryfull: float | None = None
    pressurememorysome: float | None = None
    time: int | None = None


# Proxmox node metrics
class ProxmoxNodeMetrics(ProxmoxBaseMetrics):
    arcsize: float | None = None
    iowait: float | None = None
    loadavg: float | None = None
    memavailable: float | None = None
    memtotal: float | None = None
    memused: float | None = None
    roottotal: float | None = None
    rootused: float | None = None
    swaptotal: float | None = None
    swapused: float | None = None


# Proxmox vm metrics
class ProxmoxVMMetrics(ProxmoxBaseMetrics):
    disk: float | None = None
    diskread: float | None = None
    diskwrite: float | None = None
    maxdisk: int | None = None
    maxmem: int | None = None
    mem: float | None = None
    memhost: float | None = None


# Response Models
class ProxmoxNodeMetricsList(RootModel[list[ProxmoxNodeMetrics]]):
    pass


class ProxmoxVMMetricsList(RootModel[list[ProxmoxVMMetrics]]):
    pass
