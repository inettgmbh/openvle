import { vi } from 'vitest'

export default {
  create: vi.fn().mockResolvedValue({
    name: 'A New Mock Course',
    description: 'This is a another new mock course',
    guacamole: true,
  }),

  get: vi.fn().mockResolvedValue({
    id: '6398feed-be84-4d86-a02e-ca526a7f55ed',
    createdAt: '2024-06-25T19:26:19',
    createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    updatedAt: '2024-06-25T20:02:22',
    updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    name: 'New Mock Course',
    description: 'This is a new mock course"',
    guacamole: true,
    templates: [{ name: 'A Mock Template 421' }, { name: 'A Mock Template' }],
  }),

  getName: vi.fn().mockResolvedValue('Mock Course'),

  getTemplates: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 1 },
    templates: [
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

  list: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 2 },
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
      {
        id: 'd83b3289-81f4-40f9-a0fd-b85ae887a996',
        createdAt: '2024-06-20T19:26:19',
        createdById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        updatedAt: '2024-06-20T20:02:22',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        name: 'Mock Course 2',
        description: 'This is second new mock course"',
        guacamole: false,
        templates: [{ name: 'A Mock Template' }],
      },
    ],
  }),

  update: vi.fn().mockResolvedValue({
    id: '6398feed-be84-4d86-a02e-ca526a7f55ed',
    name: 'Updated Mock Course',
    description: 'This is an updated mock course',
  }),

  delete: vi.fn().mockResolvedValue({
    message: 'Course successfully deleted',
  }),

  addTemplate: vi.fn().mockResolvedValue({
    message: 'Template successfully added to course',
  }),

  deleteTemplate: vi.fn().mockResolvedValue({
    message: 'Template successfully removed from course',
  }),

  fetchCoursesDropdown: vi.fn().mockResolvedValue([
    {
      label: 'New Mock Course',
      value: '6398feed-be84-4d86-a02e-ca526a7f55ed',
    },
    {
      label: 'Mock Course 2',
      value: 'd83b3289-81f4-40f9-a0fd-b85ae887a996',
    },
  ]),

  search: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 25, pageCount: 1, totalCount: 1 },
    items: [
      {
        id: '6398feed-be84-4d86-a02e-ca526a7f55ed',
        name: 'New Mock Course',
        description: 'This is a new mock course',
        guacamole: true,
      },
    ],
  }),
}
