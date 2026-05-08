import { vi } from 'vitest'

export default {
  addTemplate: vi.fn().mockResolvedValue({
    name: 'A new Mock Template',
    description: 'A new mock template for virtual machines',
    cpu: 2,
    ram: 4096,
    disk: 48,
    prevent_delete: true,
    source_vm: 'a1b2c3d4-5678-4e9f-9bcb-2f3a4d5e6f7g',
  }),

  addTemplateApplication: vi.fn().mockResolvedValue({
    id: 'ebcf3979-40be-46c4-a9ca-e335d106a7ef',
    apps: [{ key: 'chrome' }, { key: 'firefox' }],
  }),

  getTemplate: vi.fn().mockResolvedValue({
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
  }),

  deleteTemplateApplication: vi.fn().mockResolvedValue({
    id: 'ebcf3979-40be-46c4-a9ca-e335d106a7ef',
    apps: [],
  }),

  getTemplateApplications: vi.fn().mockResolvedValue({
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

  getTemplateCourses: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 1 },
    items: [
      {
        id: '6398feed-be84-4d86-a02e-ca526a7f55ed',
        createdAt: '2024-06-25T19:26:19',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '2024-06-25T20:02:22',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        name: 'New Mock Course',
        description: 'This is a new mock course"',
        guacamole: true,
        templates: [
          { name: 'A Mock Template 421' },
          { name: 'A Mock Template' },
        ],
      },
    ],
  }),

  getTemplateVMs: vi.fn().mockResolvedValue({
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

  getTemplates: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 2 },
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
      {
        id: 'e4182dc3-85d1-408c-aa88-23cc1088011f',
        createdAt: '2024-09-01T10:55:31.403387',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '2024-09-01T10:55:31.403412',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        name: 'A Mock Template 421',
        description: 'A mock template 421 for virtual machines',
        status: 'available',
        proxmoxNode: 'proxmox02',
        proxmoxId: 289,
        cpu: 4,
        ram: 1024,
        disk: 32,
        os: '85ed6d38-881c-454f-8950-307f64044d16',
        prevent_delete: false,
        applications: [
          {
            firefox: 'Firefox',
          },
        ],
      },
    ],
  }),

  updateTemplate: vi.fn().mockResolvedValue({
    id: 'ebcf3979-40be-46c4-a9ca-e335d106a7ef',
    name: 'Mock Template Updated',
    description: 'Updated mock template for virtual machines',
    cpu: 4,
    ram: 8192,
    prevent_delete: false,
  }),

  changeProtection: vi.fn().mockResolvedValue({
    id: 'ebcf3979-40be-46c4-a9ca-e335d106a7ef',
    prevent_delete: true,
  }),

  deleteTemplate: vi.fn().mockResolvedValue({
    message: 'Template successfully deleted',
  }),

  fetchTemplatesDropdown: vi.fn().mockResolvedValue([
    {
      label: 'A Mock Template ',
      value: 'ebcf3979-40be-46c4-a9ca-e335d106a7ef',
    },
    {
      label: 'A Mock Template 421',
      value: 'e4182dc3-85d1-408c-aa88-23cc1088011f',
    },
  ]),

  getName: vi.fn().mockResolvedValue('A Mock Template 421'),
}
