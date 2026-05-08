import { vi } from 'vitest'

// Mock role data
const mockRole = {
  id: 'b1a2c3d4-5678-4e9f-9bcb-2f3a4d5e6f7g',
  createdAt: '2024-09-15T14:00:03.800094',
  createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
  updatedAt: '2024-09-15T14:00:03.800118',
  updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
  name: 'Admin',
  key: 'admin',
  description: 'Administrator role with full access',
  protected: true,
  permissions: [
    { key: 'guacamoles_read', name: 'Guacamole lesen' },
    { key: 'users_delete', name: 'Benutzer löschen' },
    { key: 'roles_update', name: 'Rollen aktualisieren' },
  ],
}

const mockRolesList = {
  pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 4 },
  items: [
    {
      id: 'b1a2c3d4-5678-4e9f-9bcb-2f3a4d5e6f7g',
      createdAt: '2024-09-15T14:00:03.800094',
      createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      updatedAt: '2024-09-15T14:00:03.800118',
      updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      name: 'Admin',
      description: 'Administrator role with full access',
      key: 'admin',
      protected: true,
      permissions: [
        { key: 'guacamoles_read', name: 'Guacamole lesen' },
        { key: 'users_delete', name: 'Benutzer löschen' },
        { key: 'roles_update', name: 'Rollen aktualisieren' },
      ],
    },
    {
      id: 'e7f8g9h0-1234-4b2b-8e7a-1d9f8a5d2c3e',
      createdAt: '2024-09-15T14:00:03.800094',
      createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      updatedAt: '2024-09-15T14:00:03.800118',
      updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      name: 'User',
      description: 'Standard user role with limited access',
      key: 'user',
      protected: true,
      permissions: [
        { key: 'guacamoles_read', name: 'Guacamole lesen' },
        { key: 'users_read', name: 'Benutzer lesen' },
      ],
    },
    {
      id: '7ca9258a-2200-4367-b3ee-03c1644586c6',
      createdAt: '2024-09-14T14:00:03.800094',
      createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      updatedAt: '2024-09-14T14:00:03.800118',
      updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      name: 'Studierende',
      description: 'Alle Studierende',
      key: 'studierende',
      protected: true,
      permissions: [],
    },
    {
      id: '8327f069-6d2e-4b58-bd95-b78c94f64e52',
      createdAt: '2024-09-14T14:00:03.800094',
      createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      updatedAt: '2024-09-14T14:00:03.800118',
      updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      name: 'Lehrende',
      description: 'Alle Lehrende',
      key: 'lehrende',
      protected: true,
      permissions: [],
    },
  ],
}

export default {
  // ============================================================
  // Standard CRUD Methods (New API)
  // ============================================================
  create: vi.fn().mockResolvedValue({
    id: 'new-role-id',
    name: 'Mock Role 01',
    description: 'A mock role 01',
    protected: false,
    key: 'mock_role_01',
  }),

  get: vi.fn().mockResolvedValue(mockRole),

  list: vi.fn().mockResolvedValue(mockRolesList),

  update: vi.fn().mockResolvedValue({
    id: 'b1a2c3d4-5678-4e9f-9bcb-2f3a4d5e6f7g',
    name: 'Role Updated',
    description: 'Updated description for role',
  }),

  delete: vi.fn().mockResolvedValue({
    message: 'Role successfully deleted',
  }),

  // ============================================================
  // Helper Methods (New API)
  // ============================================================
  getName: vi.fn().mockResolvedValue('Admin'),

  dropdown: vi.fn().mockResolvedValue([
    { label: 'Admin', value: 'b1a2c3d4-5678-4e9f-9bcb-2f3a4d5e6f7g' },
    { label: 'User', value: 'e7f8g9h0-1234-4b2b-8e7a-1d9f8a5d2c3e' },
    { label: 'Studierende', value: '7ca9258a-2200-4367-b3ee-03c1644586c6' },
    { label: 'Lehrende', value: '8327f069-6d2e-4b58-bd95-b78c94f64e52' },
  ]),

  eventDropdown: vi.fn().mockResolvedValue([
    { label: 'Studierende', value: '7ca9258a-2200-4367-b3ee-03c1644586c6' },
    { label: 'Lehrende', value: '8327f069-6d2e-4b58-bd95-b78c94f64e52' },
  ]),

  // ============================================================
  // Search (New API)
  // ============================================================
  search: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 25, pageCount: 1, totalCount: 4 },
    items: [
      { id: 'b1a2c3d4-5678-4e9f-9bcb-2f3a4d5e6f7g', name: 'Admin' },
      { id: 'e7f8g9h0-1234-4b2b-8e7a-1d9f8a5d2c3e', name: 'User' },
      { id: '7ca9258a-2200-4367-b3ee-03c1644586c6', name: 'Studierende' },
      { id: '8327f069-6d2e-4b58-bd95-b78c94f64e52', name: 'Lehrende' },
    ],
  }),

  // ============================================================
  // Members Management (New API)
  // ============================================================
  getMembers: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 2 },
    items: [
      { id: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d', name: 'Mock User 01' },
      { id: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3', name: 'Mock User 02' },
    ],
  }),
}
