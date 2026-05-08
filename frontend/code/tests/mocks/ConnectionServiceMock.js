import { vi } from 'vitest'

export default {
  add: vi.fn().mockResolvedValue({
    port: '3389',
    protocol: 'RDP',
    username: 'mockUser',
    password: 'mockPassword',
    objectId: '86d45a04-8c05-4281-9a56-383282730d19',
    objectType: 'VirtualMachine',
  }),

  get: vi.fn().mockResolvedValue({
    id: '82a14957-a561-4c54-b192-07f79fcf12a0',
    port: 3389,
    protocol: 'RDP',
    username: 'mockUser',
    objectId: 'c7982ce4-6bd9-4aa2-9a02-039cb131e0ee',
    objectType: 'VirtualMachine',
  }),

  list: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 2 },
    items: [
      {
        id: '82a14957-a561-4c54-b192-07f79fcf12a0',
        port: 3389,
        protocol: 'RDP',
        username: 'mockUser',
        objectId: 'c7982ce4-6bd9-4aa2-9a02-039cb131e0ee',
        objectType: 'VirtualMachine',
      },
      {
        id: '261aac33-3641-48bc-baa9-48159609f34b',
        port: 22,
        protocol: 'SSH',
        username: 'mockUser',
        objectId: '3fddcd5a-2ea0-4d22-8d41-ecf1f790e156',
        objectType: 'Template',
      },
    ],
  }),

  listByObject: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 1 },
    items: [
      {
        id: '82a14957-a561-4c54-b192-07f79fcf12a0',
        port: '3389',
        protocol: 'RDP',
        username: 'user1',
        objectId: 'c7982ce4-6bd9-4aa2-9a02-039cb131e0ee',
        objectType: 'VirtualMachine',
      },
    ],
  }),

  delete: vi.fn().mockResolvedValue({
    message: 'Connection profile successfully deleted',
  }),

  fetchConnectionsDropdown: vi.fn().mockResolvedValue([
    {
      label: 'Template: [RDP] + object-1 - Benutzer: user1',
      value: 'profile-1',
    },
    {
      label: 'VirtualMachine: [SSH] + object-2 - Benutzer: user2',
      value: 'profile-2',
    },
  ]),

  fetchTemplateConnectionsDropdown: vi.fn().mockResolvedValue([
    {
      label: 'Vorlage: [RDP] + object-1 - Benutzer: user1',
      value: 'profile-1',
    },
  ]),

  dropdownVMs: vi.fn().mockResolvedValue([
    {
      label: '[SSH] + object-2 - Benutzer: user2',
      protocol: 'SSH',
      username: 'user2',
      objectId: 'object-2',
      value: 'profile-2',
    },
  ]),

  getObjectId: vi.fn().mockResolvedValue('object-id'),

  addV2: vi.fn().mockResolvedValue({
    params: { port: 3389, username: 'mockUser', password: 'mockPassword' },
    protocol: 'RDP',
    objectId: '86d45a04-8c05-4281-9a56-383282730d19',
    objectType: 'VirtualMachine',
  }),

  clone: vi.fn().mockResolvedValue({
    id: 'cloned-profile-id',
    port: 3389,
    protocol: 'RDP',
    username: 'mockUser',
    objectId: 'new-object-id',
    objectType: 'VirtualMachine',
  }),

  preload: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 200, pageCount: 1, totalCount: 2 },
    items: [
      {
        id: '82a14957-a561-4c54-b192-07f79fcf12a0',
        port: 3389,
        protocol: 'RDP',
        username: 'mockUser',
        objectId: 'c7982ce4-6bd9-4aa2-9a02-039cb131e0ee',
        objectType: 'VirtualMachine',
      },
      {
        id: '261aac33-3641-48bc-baa9-48159609f34b',
        port: 22,
        protocol: 'SSH',
        username: 'mockUser',
        objectId: '3fddcd5a-2ea0-4d22-8d41-ecf1f790e156',
        objectType: 'Template',
      },
    ],
  }),

  getLabel: vi.fn().mockResolvedValue('[RDP] c7982ce4 - mockUser:3389'),

  search: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 25, pageCount: 1, totalCount: 1 },
    items: [
      {
        id: '82a14957-a561-4c54-b192-07f79fcf12a0',
        port: 3389,
        protocol: 'RDP',
        username: 'mockUser',
        objectId: 'c7982ce4-6bd9-4aa2-9a02-039cb131e0ee',
        objectType: 'VirtualMachine',
      },
    ],
  }),
}
