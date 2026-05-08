import { vi } from 'vitest'

export default {
  // ============================================================
  // Standard CRUD Methods (New API)
  // ============================================================
  create: vi.fn().mockResolvedValue({
    name: 'Mock Test Permission',
    protected: false,
    key: 'mock_test01',
  }),

  get: vi.fn().mockResolvedValue({
    id: '2f7dd83c-5a8d-4218-a324-f7146048da19',
    createdAt: '2024-09-15T14:00:03.800094',
    createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    updatedA: '2024-09-15T14:00:03.800118',
    updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    name: 'Mock Permission 01',
    protected: false,
    key: 'mock_01',
  }),

  list: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 5 },
    items: [
      {
        id: '2f7dd83c-5a8d-4218-a324-f7146048da19',
        createdAt: '2024-09-15T14:00:03.800094',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedA: '2024-09-15T14:00:03.800118',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        name: 'Mock Permission 01',
        protected: false,
        key: 'mock_01',
      },
      {
        id: '9fbd67b4-b21a-427c-ac79-0593599fa142',
        createdAt: '2024-09-15T14:00:03.800094',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedA: '2024-09-15T14:00:03.800118',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        name: 'Mock Permission 02',
        protected: false,
        key: 'mock_02',
      },
      {
        id: 'cd1e0424-d83b-405e-accf-7a64a5561000',
        createdAt: '2024-09-15T14:00:03.800094',
        createdById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        updatedA: '2024-09-15T14:00:03.800118',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        name: 'Mock Permission 03',
        protected: true,
        key: 'mock_03',
      },
      {
        id: 'c186b116-634c-4a96-8abf-289d42f151a8',
        createdAt: '2024-09-15T14:00:03.800094',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedA: '2024-09-15T14:00:03.800118',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        name: 'Mock Permission 04',
        protected: true,
        key: 'mock_04',
      },
      {
        id: 'c9b06664-14c7-44d0-9704-b4041ef3d3f5',
        createdAt: '2024-09-15T14:00:03.800094',
        createdById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        updatedA: '2024-09-15T14:00:03.800118',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        name: 'Mock Permission 05',
        protected: false,
        key: 'mock_05',
      },
    ],
  }),

  update: vi.fn().mockResolvedValue({
    id: '2f7dd83c-5a8d-4218-a324-f7146048da19',
    name: 'Mock Permission Updated',
  }),

  delete: vi.fn().mockResolvedValue({
    message: 'Permission successfully deleted',
  }),

  // ============================================================
  // Helper Methods (New API)
  // ============================================================
  dropdown: vi.fn().mockResolvedValue([
    {
      label: 'Mock Permission 01',
      key: 'mock_01',
      value: [{ name: 'Mock Permission 01', key: 'mock_01' }],
    },
    {
      label: 'Mock Permission 02',
      key: 'mock_02',
      value: [{ name: 'Mock Permission 02', key: 'mock_02' }],
    },
    {
      label: 'Mock Permission 03',
      key: 'mock_03',
      value: [{ name: 'Mock Permission 03', key: 'mock_03' }],
    },
    {
      label: 'Mock Permission 04',
      key: 'mock_04',
      value: [{ name: 'Mock Permission 04', key: 'mock_04' }],
    },
    {
      label: 'Mock Permission 05',
      key: 'mock_05',
      value: [{ name: 'Mock Permission 05', key: 'mock_05' }],
    },
  ]),

  search: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 25, pageCount: 1, totalCount: 5 },
    items: [
      {
        id: '2f7dd83c-5a8d-4218-a324-f7146048da19',
        name: 'Mock Permission 01',
      },
      {
        id: '9fbd67b4-b21a-427c-ac79-0593599fa142',
        name: 'Mock Permission 02',
      },
      {
        id: 'cd1e0424-d83b-405e-accf-7a64a5561000',
        name: 'Mock Permission 03',
      },
      {
        id: 'c186b116-634c-4a96-8abf-289d42f151a8',
        name: 'Mock Permission 04',
      },
      {
        id: 'c9b06664-14c7-44d0-9704-b4041ef3d3f5',
        name: 'Mock Permission 05',
      },
    ],
  }),

  // ============================================================
  // Related Resources (New API)
  // ============================================================
  getRoles: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 0 },
    items: [],
  }),

  getUsers: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 0 },
    items: [],
  }),
}
