import { vi } from 'vitest'

export default {
  getDashboard: vi.fn().mockResolvedValue({
    vms: {
      own_total: 12,
      own_running: 10,
      all_total: 265,
      all_running: 234,
      all_error: 4,
    },
    courses: {
      own_total: 32,
    },
    events: {
      own_total: 54,
      own_running: 12,
      all_total: 231,
      all_running: 43,
    },
    connections: {
      own_total: 65,
      all_total: 603,
    },
    users: {
      all_total: 563,
      all_active: 523,
      all_locked: 32,
    },
    resources: {
      cpu: {
        usable: 1536,
        used: 9.245569716640901,
        allocated_max: 88,
        unit: 'cores',
      },
      ram: {
        usable: 26049.05096435547,
        used: 571.5412101745605,
        allocated_max: 262,
        unit: 'GB',
      },
      storage: {
        total: 5673.8714599609375,
        used: 62.230224609375,
        allocated_max: 278,
        unit: 'GB',
      },
      nodes: {
        total: 13,
        online: 13,
      },
    },
    nodes: {
      proxmox06: {
        hostname: 'proxmox06',
        fqdn: 'proxmox06.mock.intern',
        status: 'online',
        resources: {
          cpu: {
            usable: 32,
            used: 0.22332794830371552,
            allocated_max: null,
            unit: 'cores',
          },
          ram: {
            usable: 2003.7695579528809,
            used: 34.943084716796875,
            allocated_max: null,
            unit: 'GB',
          },
          storage: {
            total: 430.19287109375,
            used: 4.1676025390625,
            allocated_max: null,
            unit: 'GB',
          },
        },
      },
      proxmox11: {
        hostname: 'proxmox11',
        fqdn: 'proxmox11.mock.intern',
        status: 'online',
        resources: {
          cpu: {
            usable: 256,
            used: 0.20804509351780684,
            allocated_max: null,
            unit: 'cores',
          },
          ram: {
            usable: 2003.6766624450684,
            used: 38.09080123901367,
            allocated_max: null,
            unit: 'GB',
          },
          storage: {
            total: 430.1907958984375,
            used: 3.985595703125,
            allocated_max: null,
            unit: 'GB',
          },
        },
      },
      proxmox01: {
        hostname: 'proxmox01',
        fqdn: 'proxmox01.mock.intern',
        status: 'online',
        resources: {
          cpu: {
            usable: 256,
            used: 0.4658332565121024,
            allocated_max: null,
            unit: 'cores',
          },
          ram: {
            usable: 2003.8473892211914,
            used: 49.667083740234375,
            allocated_max: null,
            unit: 'GB',
          },
          storage: {
            total: 457.3138427734375,
            used: 6.05517578125,
            allocated_max: null,
            unit: 'GB',
          },
        },
      },
      proxmox04: {
        hostname: 'proxmox04',
        fqdn: 'proxmox04.mock.intern',
        status: 'online',
        resources: {
          cpu: {
            usable: 32,
            used: 0.7748134388111328,
            allocated_max: null,
            unit: 'cores',
          },
          ram: {
            usable: 2003.7680397033691,
            used: 102.51875305175781,
            allocated_max: null,
            unit: 'GB',
          },
          storage: {
            total: 430.1900634765625,
            used: 5.9287109375,
            allocated_max: null,
            unit: 'GB',
          },
        },
      },
      proxmox12: {
        hostname: 'proxmox12',
        fqdn: 'proxmox12.mock.intern',
        status: 'online',
        resources: {
          cpu: {
            usable: 32,
            used: 0.5890258867527616,
            allocated_max: null,
            unit: 'cores',
          },
          ram: {
            usable: 2003.7695617675781,
            used: 25.11,
            allocated_max: null,
            unit: 'GB',
          },
          storage: {
            total: 430.193359375,
            used: 3.980712890625,
            allocated_max: null,
            unit: 'GB',
          },
        },
      },
      proxmox09: {
        hostname: 'proxmox09',
        fqdn: 'proxmox09.mock.intern',
        status: 'online',
        resources: {
          cpu: {
            usable: 32,
            used: 0.22083198968074816,
            allocated_max: null,
            unit: 'cores',
          },
          ram: {
            usable: 2003.7695503234863,
            used: 34.14497756958008,
            allocated_max: null,
            unit: 'GB',
          },
          storage: {
            total: 430.193603515625,
            used: 3.996337890625,
            allocated_max: null,
            unit: 'GB',
          },
        },
      },
      proxmox02: {
        hostname: 'proxmox02',
        fqdn: 'proxmox02.mock.intern',
        status: 'online',
        resources: {
          cpu: {
            usable: 256,
            used: 0.7850900960569677,
            allocated_max: null,
            unit: 'cores',
          },
          ram: {
            usable: 2003.8498191833496,
            used: 51.401790618896484,
            allocated_max: null,
            unit: 'GB',
          },
          storage: {
            total: 457.3133544921875,
            used: 5.830078125,
            allocated_max: null,
            unit: 'GB',
          },
        },
      },
      proxmox13: {
        hostname: 'proxmox13',
        fqdn: 'proxmox13.mock.intern',
        status: 'online',
        resources: {
          cpu: {
            usable: 256,
            used: 0.3216376374934477,
            allocated_max: null,
            unit: 'cores',
          },
          ram: {
            usable: 2003.6766967773438,
            used: 36.85279846191406,
            allocated_max: null,
            unit: 'GB',
          },
          storage: {
            total: 430.19091796875,
            used: 3.9952392578125,
            allocated_max: null,
            unit: 'GB',
          },
        },
      },
      proxmox03: {
        hostname: 'proxmox03',
        fqdn: 'proxmox03.mock.intern',
        status: 'online',
        resources: {
          cpu: {
            usable: 256,
            used: 4.677356816877338,
            allocated_max: 8,
            unit: 'cores',
          },
          ram: {
            usable: 2003.849853515625,
            used: 52.2520866394043,
            allocated_max: 8192,
            unit: 'GB',
          },
          storage: {
            total: 457.3182373046875,
            used: 6.2393798828125,
            allocated_max: 50,
            unit: 'GB',
          },
        },
      },
      proxmox05: {
        hostname: 'proxmox05',
        fqdn: 'proxmox05.mock.intern',
        status: 'online',
        resources: {
          cpu: {
            usable: 32,
            used: 0.26386736454282306,
            allocated_max: 8,
            unit: 'cores',
          },
          ram: {
            usable: 2003.7695846557617,
            used: 34.88148498535156,
            allocated_max: 8192,
            unit: 'GB',
          },
          storage: {
            total: 430.1885986328125,
            used: 6.0291748046875,
            allocated_max: 50,
            unit: 'GB',
          },
        },
      },
      proxmox08: {
        hostname: 'proxmox08',
        fqdn: 'proxmox08.mock.intern',
        status: 'online',
        resources: {
          cpu: {
            usable: 32,
            used: 0.29288729897837507,
            allocated_max: null,
            unit: 'cores',
          },
          ram: {
            usable: 2003.7673530578613,
            used: 37.236412048339844,
            allocated_max: null,
            unit: 'GB',
          },
          storage: {
            total: 430.19482421875,
            used: 4.0206298828125,
            allocated_max: null,
            unit: 'GB',
          },
        },
      },
      proxmox07: {
        hostname: 'proxmox07',
        fqdn: 'proxmox07.mock.intern',
        status: 'online',
        resources: {
          cpu: {
            usable: 32,
            used: 0.2152974504249293,
            allocated_max: null,
            unit: 'cores',
          },
          ram: {
            usable: 2003.767349243164,
            used: 47.1025276184082,
            allocated_max: null,
            unit: 'GB',
          },
          storage: {
            total: 430.1925048828125,
            used: 4.0247802734375,
            allocated_max: null,
            unit: 'GB',
          },
        },
      },
      proxmox10: {
        hostname: 'proxmox10',
        fqdn: 'proxmox10.mock.intern',
        status: 'online',
        resources: {
          cpu: {
            usable: 32,
            used: 0.20755543868875456,
            allocated_max: null,
            unit: 'cores',
          },
          ram: {
            usable: 2003.769546508789,
            used: 27.33086395263672,
            allocated_max: null,
            unit: 'GB',
          },
          storage: {
            total: 430.198486328125,
            used: 3.976806640625,
            allocated_max: null,
            unit: 'GB',
          },
        },
      },
    },
  }),
}
