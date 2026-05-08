import { vi } from 'vitest'

export default {
  getClusterLog: vi.fn().mockResolvedValue([
    {
      id: 'log-1',
      user: 'root@pam',
      time: '2024-09-15T12:00:00Z',
      msg: 'Cluster log entry 1',
    },
    {
      id: 'log-2',
      user: 'admin@pam',
      time: '2024-09-15T12:05:00Z',
      msg: 'Cluster log entry 2',
    },
  ]),

  getClusterResources: vi.fn().mockResolvedValue([
    {
      id: 'resource-1',
      type: 'node',
      status: 'online',
      name: 'node1',
      cpu: 0.05,
      mem: 0.1,
      maxmem: 16777216,
      disk: 0.2,
      maxdisk: 83886080,
    },
    {
      id: 'resource-2',
      type: 'node',
      status: 'offline',
      name: 'node2',
      cpu: 0.0,
      mem: 0.0,
      maxmem: 16777216,
      disk: 0.0,
      maxdisk: 83886080,
    },
  ]),

  getClusterStatus: vi.fn().mockResolvedValue([
    {
      id: 'status-1',
      node: 'node1',
      online: true,
      local: true,
      type: 'quorum',
    },
    {
      id: 'status-2',
      node: 'node2',
      online: false,
      local: false,
      type: 'corosync',
    },
  ]),

  getClusterTasks: vi.fn().mockResolvedValue([
    {
      id: 'task-1',
      node: 'node1',
      type: 'backup',
      status: 'running',
      starttime: '2024-09-15T12:10:00Z',
    },
    {
      id: 'task-2',
      node: 'node2',
      type: 'restore',
      status: 'stopped',
      starttime: '2024-09-15T12:15:00Z',
    },
  ]),

  getClusterCounts: vi.fn().mockResolvedValue({
    nodes: 2,
    containers: 3,
    vms: 5,
    storages: 4,
  }),

  getNodes: vi.fn().mockResolvedValue([
    {
      id: 'node-1',
      name: 'node1',
      status: 'online',
      cpu: 0.05,
      mem: 0.1,
      maxmem: 16777216,
      disk: 0.2,
      maxdisk: 83886080,
    },
    {
      id: 'node-2',
      name: 'node2',
      status: 'offline',
      cpu: 0.0,
      mem: 0.0,
      maxmem: 16777216,
      disk: 0.0,
      maxdisk: 83886080,
    },
  ]),

  getNodesStats: vi.fn().mockResolvedValue([
    {
      id: 'node-1',
      name: 'node1',
      cpu: 0.05,
      mem: 0.1,
      maxmem: 16777216,
      disk: 0.2,
      maxdisk: 83886080,
    },
    {
      id: 'node-2',
      name: 'node2',
      cpu: 0.0,
      mem: 0.0,
      maxmem: 16777216,
      disk: 0.0,
      maxdisk: 83886080,
    },
  ]),

  getNodeRRD: vi.fn().mockResolvedValue([
    {
      time: '2024-09-15T12:00:00Z',
      cpu: 0.05,
      mem: 0.1,
      disk: 0.2,
    },
    {
      time: '2024-09-15T12:05:00Z',
      cpu: 0.06,
      mem: 0.12,
      disk: 0.25,
    },
  ]),
}
