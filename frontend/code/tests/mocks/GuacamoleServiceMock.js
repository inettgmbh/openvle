import { vi } from 'vitest'

export default {
  create: vi.fn().mockResolvedValue({
    name: 'New Mock Guacamole',
    guacd_hostname: null,
    guacd_port: 4822,
    guacd_encryption: true,
    connection_profile: '82a14957-a561-4c54-b192-07f79fcf12a0',
    userId: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    eventId: null,
  }),

  get: vi.fn().mockResolvedValue({
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
  }),

  list: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 2 },
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
      {
        id: '69125db5-ef66-4ebc-b07f-1d98f64df180',
        createdAt: '2024-09-10T12:53:39',
        createdById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        updatedAt: '2024-09-10T12:53:39',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        name: 'Mock Guacamole 02',
        guacd_hostname: null,
        guacd_port: 4822,
        guacd_encryption: true,
        userId: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        eventId: null,
        identifier: 250,
        connection_profile: '261aac33-3641-48bc-baa9-48159609f34b',
      },
    ],
  }),

  getAllByEventId: vi.fn().mockResolvedValue({
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

  getAllByUserId: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 1 },
    items: [
      {
        id: '69125db5-ef66-4ebc-b07f-1d98f64df180',
        createdAt: '2024-09-10T12:53:39',
        createdById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        updatedAt: '2024-09-10T12:53:39',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        name: 'Mock Guacamole 02',
        guacd_hostname: null,
        guacd_port: 4822,
        guacd_encryption: true,
        userId: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        eventId: null,
        identifier: 250,
        connection_profile: '261aac33-3641-48bc-baa9-48159609f34b',
      },
    ],
  }),

  getAllByConnectionProfileId: vi.fn().mockResolvedValue({
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

  delete: vi.fn().mockResolvedValue({
    message: 'Guacamole successfully deleted',
  }),

  provision: vi.fn().mockResolvedValue({
    message: 'Guacamole successfully provisioned',
  }),

  getGuacamoleUrl: vi.fn().mockResolvedValue('http://localhost:8080/guacamole'),

  getName: vi.fn().mockResolvedValue('Mock Guacamole 01'),

  getAllByVMId: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 1 },
    items: [
      {
        id: '647ca9b9-b011-4f3e-8036-c9183af53e14',
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

  search: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 25, pageCount: 1, totalCount: 1 },
    items: [
      {
        id: '647ca9b9-b011-4f3e-8036-c9183af53e14',
        name: 'Mock Guacamole 01',
        guacd_port: 4822,
        guacd_encryption: true,
        userId: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        eventId: '17cc28e6-19c0-46b9-9082-feb09ad0bfcd',
      },
    ],
  }),
}
