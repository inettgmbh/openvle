import { vi } from 'vitest'

export default {
  get: vi.fn().mockResolvedValue({
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
  }),

  getPermissions: vi.fn().mockResolvedValue([
    {
      path: '/',
      permissions: ['read', 'create', 'update', 'delete'],
      type: 'guacamoles',
    },
    {
      path: '/',
      permissions: ['read', 'create', 'update', 'delete'],
      type: 'users',
    },
    {
      path: '/',
      permissions: ['read', 'create', 'update', 'delete'],
      type: 'roles',
    },
  ]),

  updatePassword: vi.fn().mockResolvedValue({
    message: 'Password successfully updated',
  }),
}
