import { vi } from 'vitest'

export default {
  addVM: vi.fn().mockResolvedValue({
    name: 'Mock VM 123',
    description: 'A new mock virtual machine 123',
    cpu: 2,
    ram: 4096,
    template: 'ebcf3979-40be-46c4-a9ca-e335d106a7ef',
    prevent_delete: false,
    create_guacamole: true,
  }),

  addVMApplication: vi.fn().mockResolvedValue({
    id: 'a1b2c3d4-5678-4e9f-9bcb-2f3a4d5e6f7g',
    apps: [{ key: 'chrome' }, { key: 'firefox' }],
  }),

  getVM: vi.fn().mockResolvedValue({
    id: 'a1b2c3d4-5678-4e9f-9bcb-2f3a4d5e6f7g',
    createdAt: '2024-09-15T10:55:31.403387',
    createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    updatedAt: '2024-09-15T10:55:31.403412',
    updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    name: 'Mock VM 424',
    description: 'A new mock virtual machine 424',
    status: 'running',
    cpu: 4,
    ram: 2048,
    disk: 120,
    os: '85ed6d38-881c-454f-8950-307f64044d16',
    template: 'ebcf3979-40be-46c4-a9ca-e335d106a7ef',
    prevent_delete: true,
    applications: [
      {
        firefox: 'Firefox',
      },
    ],
    proxmoxNode: 'proxmox01',
    proxmoxId: 421,
    event: '17cc28e6-19c0-46b9-9082-feb09ad0bfcd',
    ipv4: '192.168.3.13',
  }),

  getName: vi.fn().mockResolvedValue('Mock VM'),

  getVMApps: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 1 },
    items: [
      {
        id: '2359089d-61bc-4296-901e-5ca17b3f6135',
        createdAt: '1970-01-01T00:00:00',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '2024-09-08T19:16:43',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        name: 'Chrome',
        patch_level: null,
        description: null,
        vendor: '1a7990c9-945f-4845-9753-8d2db9c42e51',
        key: 'chrome',
        documents: [],
      },
    ],
  }),

  getVMs: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 2 },
    items: [
      {
        id: 'a1b2c3d4-5678-4e9f-9bcb-2f3a4d5e6f7g',
        createdAt: '2024-09-15T10:55:31.403387',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '2024-09-15T10:55:31.403412',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        name: 'Mock VM 424',
        description: 'A new mock virtual machine 424',
        status: 'running',
        cpu: 4,
        ram: 2048,
        disk: 120,
        os: '85ed6d38-881c-454f-8950-307f64044d16',
        template: 'ebcf3979-40be-46c4-a9ca-e335d106a7ef',
        prevent_delete: true,
        applications: [
          {
            firefox: 'Firefox',
          },
        ],
        proxmoxNode: 'proxmox01',
        proxmoxId: 421,
        event: '17cc28e6-19c0-46b9-9082-feb09ad0bfcd',
        ipv4: '192.168.3.13',
      },
      {
        id: 'e518d4d9-d077-4ba4-b511-6d90a4e6f529',
        createdAt: '2024-09-10T10:55:31.403387',
        createdById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        updatedAt: '2024-09-10T10:55:31.403412',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        name: 'Mock VM 734',
        description: 'A new mock virtual machine 734',
        status: 'stopped',
        cpu: 24,
        ram: 8192,
        disk: 240,
        os: 'dd89af9d-8953-48c5-8083-3e8210219c3e',
        template: 'e4182dc3-85d1-408c-aa88-23cc1088011f',
        prevent_delete: true,
        applications: [
          {
            chrome: 'Chrome',
          },
        ],
        proxmoxNode: 'proxmox02',
        proxmoxId: 534,
        event: null,
        ipv4: '192.168.2.232',
      },
    ],
  }),

  updateVM: vi.fn().mockResolvedValue({
    id: 'a1b2c3d4-5678-4e9f-9bcb-2f3a4d5e6f7g',
    name: 'Mock VM Updated',
    description: 'Updated mock virtual machine',
    cpu: 4,
    ram: 8192,
    os: '85ed6d38-881c-454f-8950-307f64044d16',
    prevent_delete: true,
    restart_vm: false,
  }),

  changeProtection: vi.fn().mockResolvedValue({
    id: 'a1b2c3d4-5678-4e9f-9bcb-2f3a4d5e6f7g',
    prevent_delete: true,
  }),

  deleteVM: vi.fn().mockResolvedValue({
    message: 'Virtual machine successfully deleted',
  }),

  updateStatus: vi.fn().mockResolvedValue({
    id: 'a1b2c3d4-5678-4e9f-9bcb-2f3a4d5e6f7g',
    status: 'running',
  }),

  migrate: vi.fn().mockResolvedValue({
    id: 'a1b2c3d4-5678-4e9f-9bcb-2f3a4d5e6f7g',
    message: 'VM migrated successfully',
  }),

  fetchVMsDropdown: vi.fn().mockResolvedValue([
    {
      label: 'Mock VM 734',
      value: 'e518d4d9-d077-4ba4-b511-6d90a4e6f529',
    },
    {
      label: 'Mock VM 424',
      value: 'a1b2c3d4-5678-4e9f-9bcb-2f3a4d5e6f7g',
    },
  ]),

  getVMIPv4: vi.fn().mockResolvedValue({
    ipv4: '192.168.1.100',
  }),
}
