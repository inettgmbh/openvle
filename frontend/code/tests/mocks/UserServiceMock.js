import { vi } from 'vitest'

// Mock user data
const mockUser = {
  id: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
  createdAt: '2024-07-06T16:09:00',
  createdById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
  updatedAt: '2024-08-09T16:59:23',
  updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
  username: 'mockuser02',
  name: 'Mock User 02',
  email: 'mockuser02@example.com',
  status: 'Inactive',
  locale: 'fr_FR',
  roles: [{ key: 'lehrende', name: 'Lehrende' }],
  permissions: [{ key: 'applications_create', name: 'Anwendungen erstellen' }],
  user_type: 'ldap',
}

const mockUsersList = {
  pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 3 },
  items: [
    {
      id: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
      createdAt: '2024-09-07T16:09:00',
      createdById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
      updatedAt: '2024-09-10T16:59:23',
      updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
      username: 'mockuser01',
      name: 'Mock User 01',
      email: 'mockuser01@example.com',
      status: 'Active',
      locale: 'de_DE',
      roles: [{ key: 'studierende', name: 'Studierende' }],
      permissions: [
        { key: 'applications_create', name: 'Anwendungen erstellen' },
      ],
      user_type: 'internal',
    },
    {
      id: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
      createdAt: '2024-07-06T16:09:00',
      createdById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
      updatedAt: '2024-08-09T16:59:23',
      updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
      username: 'mockuser02',
      name: 'Mock User 02',
      email: 'mockuser02@example.com',
      status: 'Inactive',
      locale: 'fr_FR',
      roles: [{ key: 'lehrende', name: 'Lehrende' }],
      permissions: [
        { key: 'applications_create', name: 'Anwendungen erstellen' },
      ],
      user_type: 'ldap',
    },
    {
      id: '1db3d8ac-22d9-4116-976a-93ad6e4fb234',
      createdAt: '1970-01-01T00:00:00',
      createdById: '1db3d8ac-22d9-4116-976a-93ad6e4fb234',
      updatedAt: '1970-01-01T00:00:00',
      updatedById: '1db3d8ac-22d9-4116-976a-93ad6e4fb234',
      username: 'system',
      name: 'System Benutzer',
      email: 'system@system.system',
      status: 'Active',
      locale: 'en_US',
      roles: [{ key: 'admin_full', name: 'Administrator (Full)' }],
      permissions: [],
      user_type: 'ldap',
    },
  ],
}

export default {
  // ============================================================
  // Standard CRUD Methods (New API)
  // ============================================================
  create: vi.fn().mockResolvedValue({
    username: 'mockuser042',
    email: 'mockuser042@mock.com',
    name: 'Mock User 042',
    locale: 'de_DE',
    status: 'Active',
  }),

  get: vi.fn().mockResolvedValue(mockUser),

  list: vi.fn().mockResolvedValue(mockUsersList),

  update: vi.fn().mockResolvedValue({
    id: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    name: 'updateduser',
    email: 'updateduser@example.com',
    status: 'Inactive',
    locale: 'fr_FR',
  }),

  delete: vi.fn().mockResolvedValue({
    message: 'User successfully deleted',
  }),

  // ============================================================
  // Helper Methods (New API)
  // ============================================================
  getName: vi.fn().mockResolvedValue('mockuser01'),

  dropdown: vi.fn().mockResolvedValue([
    {
      label: 'Mock User 01 (mockuser01)',
      value: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    },
    {
      label: 'Mock User 02 (mockuser02)',
      value: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
    },
  ]),

  search: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 25, pageCount: 1, totalCount: 2 },
    items: [
      {
        id: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        name: 'Mock User 01 <mockuser01@example.com>',
      },
      {
        id: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        name: 'Mock User 02 <mockuser02@example.com>',
      },
    ],
  }),

  formatById: vi
    .fn()
    .mockResolvedValue('Mock User 01 <mockuser01@example.com>'),

  preload: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 200, pageCount: 1, totalCount: 3 },
    items: [
      { id: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d', name: 'mockuser01' },
      { id: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3', name: 'mockuser02' },
      { id: '1db3d8ac-22d9-4116-976a-93ad6e4fb234', name: 'system' },
    ],
  }),

  setPassword: vi.fn().mockResolvedValue({
    message: 'Password successfully set',
  }),

  // ============================================================
  // Role Management (New API)
  // ============================================================
  getRoles: vi.fn().mockResolvedValue([
    { key: 'admin', name: 'Administrator' },
    { key: 'user', name: 'User' },
  ]),

  addRole: vi.fn().mockResolvedValue({
    message: 'Role successfully added to user',
  }),

  updateRoles: vi.fn().mockResolvedValue({
    message: 'User roles successfully updated',
  }),

  deleteRole: vi.fn().mockResolvedValue({
    message: 'User role successfully deleted',
  }),

  // ============================================================
  // Related Resources (New API)
  // ============================================================
  getEvents: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 0 },
    items: [],
  }),

  getVMs: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 0 },
    items: [],
  }),

  getGuacamoles: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 1 },
    items: [
      {
        id: '647ca9b9-b011-4f3e-8036-c9183af53e14',
        createdAt: '2024-09-15T12:53:39',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '2024-09-15T12:53:39',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        name: 'Mock Guacamole 01',
        guacd_hostname: null,
        guacd_port: 4822,
        guacd_encryption: true,
        userId: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        eventId: '17cc28e6-19c0-46b9-9082-feb09ad0bfcd',
        identifier: 234,
        connection_profile: '82a14957-a561-4c54-b192-07f79fcf12a0',
      },
    ],
  }),

  // ============================================================
  // Status Management (New API)
  // ============================================================
  getStatuses: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 4 },
    items: [
      { id: '3ebec0c5-f0d8-4127-8747-496cb7efbf2e', name: 'Banned' },
      { id: '7bef5728-da30-48c9-a725-4facbabc0f0a', name: 'E-Mail-Pending' },
      { id: '9714d8de-4c77-450e-a452-61fb43e8a37e', name: 'Active' },
      { id: 'e8cd074b-be94-4c17-b0f5-853d0a979e49', name: 'Inactive' },
    ],
  }),

  addStatus: vi.fn().mockResolvedValue({
    message: 'Status successfully added',
  }),

  deleteStatus: vi.fn().mockResolvedValue({
    message: 'Status successfully deleted',
  }),

  // ============================================================
  // Delete Preview
  // ============================================================
  getDeletePreview: vi.fn().mockResolvedValue({
    stats: {
      virtual_machines: 0,
      connections: 0,
      mails: 0,
      changelogs: 0,
      object_permissions: 0,
      event_memberships: 0,
      policy_memberships: 0,
      tags: 0,
    },
    virtual_machines: { items: [], truncated: false },
    connections: { items: [], truncated: false },
    mails: { items: [], truncated: false },
    changelogs: { items: [], truncated: false },
    object_permissions: { items: [], truncated: false },
    tags: { items: [], truncated: false },
    event_memberships: { items: [], truncated: false },
  }),
}
