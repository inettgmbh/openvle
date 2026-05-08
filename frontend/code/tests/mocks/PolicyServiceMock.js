import { vi } from 'vitest'

export default {
  create: vi.fn().mockResolvedValue({
    name: 'Privacy Policy',
    description: 'This is a privacy policy.',
    content: 'Detailed policy content goes here.',
  }),

  get: vi.fn().mockResolvedValue({
    id: 'ab092aa5-eb2c-471b-8f54-5b8fc3249da8',
    createdAt: '2024-09-15T14:00:03.800094',
    createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    updatedAt: '2024-09-15T14:00:03.800118',
    updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    name: 'Mock Policy 01',
    description: 'This is a mock policy 01',
    content: 'Mock Content 01',
    active: false,
  }),

  list: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 2 },
    items: [
      {
        id: 'ab092aa5-eb2c-471b-8f54-5b8fc3249da8',
        createdAt: '2024-09-15T14:00:03.800094',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '2024-09-15T14:00:03.800118',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        name: 'Mock Policy 01',
        description: 'This is a mock policy 01',
        content: 'Mock Content 01',
        active: false,
      },
      {
        id: '5d9364ea-a71f-4aa3-b442-38263e60ae84',
        createdAt: '2024-09-11T14:00:03.800094',
        createdById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        updatedAt: '2024-09-11T14:00:03.800118',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        name: 'Mock Policy 02',
        description: 'This is a mock policy 02',
        content: 'Mock Content 02',
        active: true,
      },
    ],
  }),

  update: vi.fn().mockResolvedValue({
    id: 'ab092aa5-eb2c-471b-8f54-5b8fc3249da8',
    name: 'Privacy Policy Updated',
    description: 'This is an updated privacy policy.',
    content: 'Updated detailed policy content.',
    active: true,
  }),

  delete: vi.fn().mockResolvedValue({
    message: 'Policy successfully deleted',
  }),

  agree: vi.fn().mockResolvedValue({
    message: 'Policy agreement successfully recorded',
  }),

  getUsers: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 0, totalCount: 0 },
    items: [],
  }),

  getPoliciesByUserId: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 0, totalCount: 0 },
    items: [],
  }),

  checkUserAgreedToPolicy: vi.fn().mockResolvedValue({
    agreed: true,
  }),

  enable: vi.fn().mockResolvedValue({
    message: 'Policy successfully enabled',
  }),

  disable: vi.fn().mockResolvedValue({
    message: 'Policy successfully disabled',
  }),
}
