import { vi } from 'vitest'

export default {
  // ============================================================
  // Standard CRUD Methods (New API)
  // ============================================================
  create: vi.fn().mockResolvedValue({
    object_type: 'application',
    object_id: '2359089d-61bc-4296-901e-5ca17b3f6135',
    user_id: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    permission_key: 'object_full',
  }),

  get: vi.fn().mockResolvedValue({
    id: 'd1e2f8a3-3a7e-4c2b-bf8e-6f8b4a2d3e1f',
    createdAt: '2024-09-15T12:53:39',
    createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    updatedAt: '2024-09-15T12:53:39',
    updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    object_type: 'application',
    object_id: '2359089d-61bc-4296-901e-5ca17b3f6135',
    user_id: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    permission_key: 'object_full',
  }),

  list: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 6 },
    items: [
      {
        id: 'd1e2f8a3-3a7e-4c2b-bf8e-6f8b4a2d3e1f',
        createdAt: '2024-09-15T12:53:39',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '2024-09-15T12:53:39',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        object_type: 'application',
        object_id: '2359089d-61bc-4296-901e-5ca17b3f6135',
        user_id: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        permission_key: 'object_full',
      },
      {
        id: 'cfc415b8-eac9-460e-951b-96a161eacc51',
        createdAt: '2024-09-15T12:53:39',
        createdById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        updatedAt: '2024-09-15T12:53:39',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        object_type: 'application',
        object_id: '2359089d-61bc-4296-901e-5ca17b3f6135',
        user_id: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        permission_key: 'object_read',
      },
      {
        id: 'e3e1114f-4ecc-44b6-8d0f-044480a077fd',
        createdAt: '2024-09-15T12:53:39',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '2024-09-15T12:53:39',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        object_type: 'application',
        object_id: '2359089d-61bc-4296-901e-5ca17b3f6135',
        user_id: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        permission_key: 'object_update',
      },
      {
        id: '6571cff0-4cab-4083-b36c-5ce5aae1dd51',
        createdAt: '2024-09-15T12:53:39',
        createdById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        updatedAt: '2024-09-15T12:53:39',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        object_type: 'application',
        object_id: '2359089d-61bc-4296-901e-5ca17b3f6135',
        user_id: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        permission_key: 'object_delete',
      },
      {
        id: 'f7fb5c1f-8b80-45e2-886b-a867ff20b386',
        createdAt: '2024-09-15T12:53:39',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '2024-09-15T12:53:39',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        object_type: 'application',
        object_id: '2359089d-61bc-4296-901e-5ca17b3f6135',
        user_id: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        permission_key: 'object_read',
      },
      {
        id: '8aaa59e7-73d7-4a08-986f-4e604c1f6ce7',
        createdAt: '2024-09-15T12:53:39',
        createdById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        updatedAt: '2024-09-15T12:53:39',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        object_type: 'application',
        object_id: '2359089d-61bc-4296-901e-5ca17b3f6135',
        user_id: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        permission_key: 'object_full',
      },
    ],
  }),

  delete: vi.fn().mockResolvedValue({
    message: 'Object permission successfully deleted',
  }),
}
