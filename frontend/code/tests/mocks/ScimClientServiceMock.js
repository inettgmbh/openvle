import { vi } from 'vitest'

// Mock SCIM client data
const mockClient = {
  id: 'c3d4e5f6-7890-4a1b-bcde-3c4d5e6f7a8b',
  createdAt: '2025-06-10T10:00:00.000000',
  createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
  updatedAt: '2025-06-10T10:00:00.000000',
  updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
  name: 'External LMS Client',
  description: 'SCIM client for external LMS sync',
  enabled: true,
  endpoint_url: 'https://lms.example.com/scim/v2',
  sync_groups: true,
  roles: [{ key: 'user', name: 'User' }],
}

const mockClientsList = {
  pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 2 },
  items: [
    {
      id: 'c3d4e5f6-7890-4a1b-bcde-3c4d5e6f7a8b',
      createdAt: '2025-06-10T10:00:00.000000',
      createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      updatedAt: '2025-06-10T10:00:00.000000',
      updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      name: 'External LMS Client',
      description: 'SCIM client for external LMS sync',
      enabled: true,
      endpoint_url: 'https://lms.example.com/scim/v2',
      sync_groups: true,
      roles: [{ key: 'user', name: 'User' }],
    },
    {
      id: 'd4e5f6a7-8901-4b2c-cdef-4d5e6f7a8b9c',
      createdAt: '2025-06-11T12:00:00.000000',
      createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      updatedAt: '2025-06-11T12:00:00.000000',
      updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      name: 'HR System Client',
      description: 'SCIM client for HR system',
      enabled: false,
      endpoint_url: 'https://hr.example.com/scim/v2',
      sync_groups: false,
      roles: [],
    },
  ],
}

const mockUserMappings = {
  pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 2 },
  items: [
    {
      user_id: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      external_scim_id: 'ext-user-001',
      last_synced_at: '2025-06-12T08:30:00.000000',
    },
    {
      user_id: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
      external_scim_id: 'ext-user-002',
      last_synced_at: '2025-06-12T08:30:00.000000',
    },
  ],
}

export default {
  // ============================================================
  // Standard CRUD Methods
  // ============================================================
  create: vi.fn().mockResolvedValue({
    id: 'new-client-id',
    name: 'New SCIM Client',
    description: 'A new SCIM client',
    enabled: true,
    endpoint_url: 'https://new.example.com/scim/v2',
    sync_groups: false,
  }),

  get: vi.fn().mockResolvedValue(mockClient),

  list: vi.fn().mockResolvedValue(mockClientsList),

  update: vi.fn().mockResolvedValue({
    id: 'c3d4e5f6-7890-4a1b-bcde-3c4d5e6f7a8b',
    name: 'Client Updated',
    description: 'Updated description',
    enabled: true,
    endpoint_url: 'https://lms.example.com/scim/v2',
    sync_groups: true,
  }),

  delete: vi.fn().mockResolvedValue({
    message: 'SCIM client successfully deleted',
  }),

  // ============================================================
  // Helper Methods
  // ============================================================
  getName: vi.fn().mockResolvedValue('External LMS Client'),

  dropdown: vi.fn().mockResolvedValue([
    {
      label: 'External LMS Client',
      value: 'c3d4e5f6-7890-4a1b-bcde-3c4d5e6f7a8b',
    },
    {
      label: 'HR System Client',
      value: 'd4e5f6a7-8901-4b2c-cdef-4d5e6f7a8b9c',
    },
  ]),

  search: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 25, pageCount: 1, totalCount: 2 },
    items: [
      {
        id: 'c3d4e5f6-7890-4a1b-bcde-3c4d5e6f7a8b',
        name: 'External LMS Client',
      },
      { id: 'd4e5f6a7-8901-4b2c-cdef-4d5e6f7a8b9c', name: 'HR System Client' },
    ],
  }),

  // ============================================================
  // Role Management
  // ============================================================
  updateRoles: vi.fn().mockResolvedValue({
    message: 'Roles successfully updated',
  }),

  addRoles: vi.fn().mockResolvedValue({
    message: 'Roles successfully added',
  }),

  // ============================================================
  // User Mappings
  // ============================================================
  getUserMappings: vi.fn().mockResolvedValue(mockUserMappings),
}
