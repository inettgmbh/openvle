import { vi } from 'vitest'

export default {
  create: vi.fn().mockResolvedValue({
    key: 'Nr. 10',
    value: 'MockTag',
    objectId: '2359089d-61bc-4296-901e-5ca17b3f6135',
    objectType: 'applications',
  }),

  getTagById: vi.fn().mockResolvedValue({
    id: 'f1e2d3c4-5678-4b9a-8e7c-1f2d3a4b5c6d',
    createdAt: '2024-06-25T20:35:51',
    createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    updatedAt: '2024-06-25T20:35:51',
    updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    key: 'category',
    value: 'important',
    objectId: 'a1b2c3d4-5678-4e9f-9bcb-2f3a4d5e6f7g',
    objectType: 'virtual_machines',
  }),

  list: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 5 },
    items: [
      {
        id: 'f1e2d3c4-5678-4b9a-8e7c-1f2d3a4b5c6d',
        createdAt: '2024-06-25T20:35:51',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '2024-06-25T20:35:51',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        key: 'category',
        value: 'important',
        objectId: 'a1b2c3d4-5678-4e9f-9bcb-2f3a4d5e6f7g',
        objectType: 'virtual_machines',
      },
      {
        id: '2c04811c-6b2f-462d-997a-1dd54637a347',
        createdAt: '2024-06-25T20:35:51',
        createdById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        updatedAt: '2024-06-25T20:35:51',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        key: 'type',
        value: 'issue',
        objectId: 'e518d4d9-d077-4ba4-b511-6d90a4e6f529',
        objectType: 'virtual_machines',
      },
      {
        id: 'b3d23334-3682-4b12-8ffa-e0b6b60358fb',
        createdAt: '2024-06-25T20:35:51',
        createdById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        updatedAt: '2024-06-25T20:35:51',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        key: 'manager',
        value: 'mmustermann',
        objectId: '2359089d-61bc-4296-901e-5ca17b3f6135',
        objectType: 'applications',
      },
      {
        id: 'af8332b4-76ca-44fe-8436-b15dba617ec0',
        createdAt: '2024-06-25T20:35:51',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '2024-06-25T20:35:51',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        key: 'supervisor',
        value: 'mockman',
        objectId: '17cc28e6-19c0-46b9-9082-feb09ad0bfcd',
        objectType: 'events',
      },
      {
        id: '506b843a-51be-40b1-80e0-2487bae24903',
        createdAt: '2024-06-25T20:35:51',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '2024-06-26T20:35:51',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        key: 'version',
        value: '2024',
        objectId: '6398feed-be84-4d86-a02e-ca526a7f55ed',
        objectType: 'courses',
      },
    ],
  }),

  delete: vi.fn().mockResolvedValue({
    message: 'Tag successfully deleted',
  }),

  getTagsByObject: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 1 },
    items: [
      {
        id: '506b843a-51be-40b1-80e0-2487bae24903',
        createdAt: '2024-06-25T20:35:51',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '2024-06-26T20:35:51',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        key: 'version',
        value: '2024',
        objectId: '6398feed-be84-4d86-a02e-ca526a7f55ed',
        objectType: 'courses',
      },
    ],
  }),

  listByKey: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 1 },
    items: [
      {
        id: 'af8332b4-76ca-44fe-8436-b15dba617ec0',
        createdAt: '2024-06-25T20:35:51',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '2024-06-25T20:35:51',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        key: 'supervisor',
        value: 'mockman',
        objectId: '17cc28e6-19c0-46b9-9082-feb09ad0bfcd',
        objectType: 'events',
      },
    ],
  }),

  listByKeyValue: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 1 },
    items: [
      {
        id: 'b3d23334-3682-4b12-8ffa-e0b6b60358fb',
        createdAt: '2024-06-25T20:35:51',
        createdById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        updatedAt: '2024-06-25T20:35:51',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        key: 'manager',
        value: 'mmustermann',
        objectId: '2359089d-61bc-4296-901e-5ca17b3f6135',
        objectType: 'applications',
      },
    ],
  }),
}
