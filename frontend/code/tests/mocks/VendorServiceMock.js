import { vi } from 'vitest'

export default {
  create: vi.fn().mockResolvedValue({
    id: 'new-vendor-id-001',
    name: 'Mock Vendor 134',
    description: 'This is a mock vendor 134',
  }),

  get: vi.fn().mockResolvedValue({
    id: '1a7990c9-945f-4845-9753-8d2db9c42e51',
    description: 'This is a mock vendor 538',
    updatedAt: '1970-01-01T00:00:00',
    updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    name: 'Mock Vendor 538',
    createdAt: '1970-01-01T00:00:00',
    createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
  }),

  getApplications: vi.fn().mockResolvedValue({
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

  getName: vi.fn().mockResolvedValue('Mock Vendor'),

  getOS: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 1 },
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
    ],
  }),

  list: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 2 },
    items: [
      {
        id: '1a7990c9-945f-4845-9753-8d2db9c42e51',
        description: 'This is a mock vendor 538',
        updatedAt: '1970-01-01T00:00:00',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        name: 'Mock Vendor 538',
        createdAt: '1970-01-01T00:00:00',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      },
      {
        id: '43e1b4c6-eaf6-4836-8802-c089c47ff973',
        description: 'This is a mock vendor 821',
        updatedAt: '2020-01-01T00:10:00',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        name: 'Mock Vendor 821',
        createdAt: '2020-01-01T00:00:00',
        createdById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
      },
    ],
  }),

  update: vi.fn().mockResolvedValue({
    id: '1a7990c9-945f-4845-9753-8d2db9c42e51',
    name: 'Updated Mock Vendor',
    description: 'This is an updated mock vendor',
  }),

  delete: vi.fn().mockResolvedValue({
    message: 'Vendor successfully deleted',
  }),
}
