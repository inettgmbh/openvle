import { vi } from 'vitest'

// Mock SCIM provider data
const mockProvider = {
  id: 'a1b2c3d4-5678-4e9f-9bcb-1a2b3c4d5e6f',
  createdAt: '2025-06-10T10:00:00.000000',
  createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
  updatedAt: '2025-06-10T10:00:00.000000',
  updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
  name: 'Authentik Provider',
  description: 'SCIM provider for Authentik',
  enabled: true,
  default_user_status: 'Active',
  roles: [{ key: 'user', name: 'User' }],
}

const mockProvidersList = {
  pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 2 },
  items: [
    {
      id: 'a1b2c3d4-5678-4e9f-9bcb-1a2b3c4d5e6f',
      createdAt: '2025-06-10T10:00:00.000000',
      createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      updatedAt: '2025-06-10T10:00:00.000000',
      updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      name: 'Authentik Provider',
      description: 'SCIM provider for Authentik',
      enabled: true,
      default_user_status: 'Active',
      roles: [{ key: 'user', name: 'User' }],
    },
    {
      id: 'b2c3d4e5-6789-4f0a-abcd-2b3c4d5e6f7a',
      createdAt: '2025-06-11T12:00:00.000000',
      createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      updatedAt: '2025-06-11T12:00:00.000000',
      updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      name: 'Okta Provider',
      description: 'SCIM provider for Okta',
      enabled: false,
      default_user_status: 'Inactive',
      roles: [],
    },
  ],
}

export default {
  // ============================================================
  // Standard CRUD Methods
  // ============================================================
  create: vi.fn().mockResolvedValue({
    id: 'new-provider-id',
    name: 'New SCIM Provider',
    description: 'A new SCIM provider',
    enabled: true,
    default_user_status: 'Active',
    bearer_token: 'generated-token-abc123',
  }),

  get: vi.fn().mockResolvedValue(mockProvider),

  list: vi.fn().mockResolvedValue(mockProvidersList),

  update: vi.fn().mockResolvedValue({
    id: 'a1b2c3d4-5678-4e9f-9bcb-1a2b3c4d5e6f',
    name: 'Provider Updated',
    description: 'Updated description',
    enabled: true,
    default_user_status: 'Active',
  }),

  delete: vi.fn().mockResolvedValue({
    message: 'SCIM provider successfully deleted',
  }),

  // ============================================================
  // Helper Methods
  // ============================================================
  getName: vi.fn().mockResolvedValue('Authentik Provider'),

  dropdown: vi.fn().mockResolvedValue([
    {
      label: 'Authentik Provider',
      value: 'a1b2c3d4-5678-4e9f-9bcb-1a2b3c4d5e6f',
    },
    { label: 'Okta Provider', value: 'b2c3d4e5-6789-4f0a-abcd-2b3c4d5e6f7a' },
  ]),

  search: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 25, pageCount: 1, totalCount: 2 },
    items: [
      {
        id: 'a1b2c3d4-5678-4e9f-9bcb-1a2b3c4d5e6f',
        name: 'Authentik Provider',
      },
      { id: 'b2c3d4e5-6789-4f0a-abcd-2b3c4d5e6f7a', name: 'Okta Provider' },
    ],
  }),

  // ============================================================
  // Token Management
  // ============================================================
  rotateToken: vi.fn().mockResolvedValue({
    ...mockProvider,
    bearer_token: 'rotated-token-xyz789',
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
}
