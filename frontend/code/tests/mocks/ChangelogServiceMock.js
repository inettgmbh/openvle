import { vi } from 'vitest'

export default {
  // ============================================================
  // Standard CRUD Methods (New API)
  // ============================================================
  get: vi.fn().mockResolvedValue({
    id: '2b4c102c-1af1-4f0e-ab95-a0f9bcfdd472',
    valueOld: "{'status': 'Banned'}",
    valueNew: "{'status': 'Active'}",
    timestamp: '2024-01-01T00:00:00.000Z',
    object: 'User',
    objectId: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
    userId: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
  }),

  list: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 3 },
    items: [
      {
        id: 'a9a8c127-4c04-40c8-8c5c-ccdad4a0c2bd',
        valueOld: "{'status': 'Active'}",
        valueNew: "{'status': 'Banned'}",
        timestamp: '2023-12-31T00:00:00.000Z',
        object: 'User',
        objectId: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        userId: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      },
      {
        id: '2b4c102c-1af1-4f0e-ab95-a0f9bcfdd472',
        valueOld: "{'status': 'Banned'}",
        valueNew: "{'status': 'Active'}",
        timestamp: '2024-01-01T00:00:00.000Z',
        object: 'User',
        objectId: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        userId: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      },
      {
        id: '325660bf-17be-4de1-9e2d-bcd99c45edff',
        valueOld: "{'status': 'Inactive'}",
        valueNew: "{'status': 'Active'}",
        timestamp: '2024-02-01T00:00:00.000Z',
        object: 'User',
        objectId: 'e0a4a23c-121a-45dd-bfb8-e480afa69b0d',
        userId: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
      },
    ],
  }),

  // ============================================================
  // Query Methods (New API)
  // ============================================================
  listByObject: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 2 },
    items: [
      {
        id: '2b4c102c-1af1-4f0e-ab95-a0f9bcfdd472',
        valueOld: "{'status': 'Banned'}",
        valueNew: "{'status': 'Active'}",
        timestamp: '2024-01-01T00:00:00.000Z',
        object: 'User',
        objectId: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        userId: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      },
      {
        id: 'a9a8c127-4c04-40c8-8c5c-ccdad4a0c2bd',
        valueOld: "{'status': 'Active'}",
        valueNew: "{'status': 'Banned'}",
        timestamp: '2023-12-31T00:00:00.000Z',
        object: 'User',
        objectId: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        userId: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      },
    ],
  }),

  listByUser: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 2 },
    items: [
      {
        id: 'a9a8c127-4c04-40c8-8c5c-ccdad4a0c2bd',
        valueOld: "{'status': 'Active'}",
        valueNew: "{'status': 'Banned'}",
        timestamp: '2023-12-31T00:00:00.000Z',
        object: 'User',
        objectId: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        userId: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      },
      {
        id: '2b4c102c-1af1-4f0e-ab95-a0f9bcfdd472',
        valueOld: "{'status': 'Banned'}",
        valueNew: "{'status': 'Active'}",
        timestamp: '2024-01-01T00:00:00.000Z',
        object: 'User',
        objectId: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        userId: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      },
    ],
  }),
}
