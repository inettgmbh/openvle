import { vi } from 'vitest'

export default {
  create: vi.fn().mockResolvedValue({
    name: 'Mock OS 823',
    patch_level: '13',
    key: 'mock_os_823',
    description: 'A new mock OS 823',
    version: '823.0',
    vendor: '1a7990c9-945f-4845-9753-8d2db9c42e51',
  }),

  get: vi.fn().mockResolvedValue({
    id: 'dd89af9d-8953-48c5-8083-3e8210219c3e',
    createdAt: '2024-09-15T10:55:31.403387',
    createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    updatedAt: '2024-09-15T10:55:31.403412',
    updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    name: 'Mock OS 234',
    patch_level: '434',
    description: 'A new mock OS 434',
    vendor: '1a7990c9-945f-4845-9753-8d2db9c42e51',
    version: '434',
    key: 'mock_os_434',
    documents: [],
  }),

  getName: vi.fn().mockResolvedValue('Mock OS'),

  getTemplates: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 1 },
    items: [
      {
        id: 'ebcf3979-40be-46c4-a9ca-e335d106a7ef',
        createdAt: '2024-09-15T10:55:31.403387',
        createdById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        updatedAt: '2024-09-15T10:55:31.403412',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        name: 'A Mock Template',
        description: 'A template for a mock virtual machines',
        status: 'available',
        proxmoxNode: 'proxmox01',
        proxmoxId: 281,
        cpu: 2,
        ram: 4096,
        disk: 32,
        os: 'dd89af9d-8953-48c5-8083-3e8210219c3e',
        prevent_delete: true,
        applications: [
          {
            chrome: 'Chrome',
          },
        ],
      },
    ],
  }),

  getVMs: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 1 },
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
    ],
  }),

  list: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 2 },
    items: [
      {
        id: 'dd89af9d-8953-48c5-8083-3e8210219c3e',
        createdAt: '2024-09-15T10:55:31.403387',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '2024-09-15T10:55:31.403412',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        name: 'Mock OS 234',
        patch_level: '434',
        description: 'A new mock OS 434',
        vendor: '1a7990c9-945f-4845-9753-8d2db9c42e51',
        version: '434',
        key: 'mock_os_434',
        documents: [],
      },
      {
        id: '85ed6d38-881c-454f-8950-307f64044d16',
        createdAt: '2024-09-15T10:55:31.403387',
        createdById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        updatedAt: '2024-09-15T10:55:31.403412',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        name: 'Mock OS 678',
        patch_level: '678',
        description: 'A new mock OS 678',
        vendor: '43e1b4c6-eaf6-4836-8802-c089c47ff973',
        version: '678',
        key: 'mock_os_678',
        documents: [],
      },
    ],
  }),

  update: vi.fn().mockResolvedValue({
    id: '85ed6d38-881c-454f-8950-307f64044d16',
    name: 'Mock OS Updated',
    description: 'Updated Description',
    version: '987',
    vendor: '1a7990c9-945f-4845-9753-8d2db9c42e51',
  }),

  delete: vi.fn().mockResolvedValue({
    message: 'OS successfully deleted',
  }),
}
