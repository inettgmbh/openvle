import { vi } from 'vitest'

export default {
  // ============================================================
  // Standard CRUD Methods (New API)
  // ============================================================
  get: vi.fn().mockResolvedValue({
    id: 'action-123',
    name: 'Mock Mail Action',
    description: 'A mock mail action for testing',
    slug: 'events_test_action',
    createdAt: '2024-01-15T10:00:00.000Z',
    updatedAt: '2024-01-15T10:00:00.000Z',
  }),

  list: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 2 },
    items: [
      {
        id: 'action-123',
        name: 'Events Test Action',
        description: 'Action for events',
        slug: 'events_test_action',
      },
      {
        id: 'action-456',
        name: 'VM Test Action',
        description: 'Action for VMs',
        slug: 'vm_test_action',
      },
    ],
  }),

  // ============================================================
  // Helper Methods (New API)
  // ============================================================
  getName: vi.fn().mockResolvedValue('Mock Mail Action'),

  dropdown: vi.fn().mockResolvedValue([
    {
      label: 'Events Test Action',
      value: 'action-123',
      slug: 'events_test_action',
    },
    {
      label: 'VM Test Action',
      value: 'action-456',
      slug: 'vm_test_action',
    },
    {
      label: 'Generic Action',
      value: 'action-789',
      slug: 'generic_action',
    },
  ]),
}
