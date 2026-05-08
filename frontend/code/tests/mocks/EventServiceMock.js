import { vi } from 'vitest'

export default {
  create: vi.fn().mockResolvedValue({
    name: 'New Mock Event',
    description: 'This is a new mock event',
    dateStart: '2024-05-01T00:00:00Z',
    dateEnd: '2024-05-02T00:00:00Z',
    timeStart: '14:00:04',
    timeEnd: '14:00:04',
    guacamole: true,
    status: '53b6993a-57d6-40a6-8d42-e55bf08fac4c',
    course: '6398feed-be84-4d86-a02e-ca526a7f55ed',
  }),

  get: vi.fn().mockResolvedValue({
    id: '17cc28e6-19c0-46b9-9082-feb09ad0bfcd',
    createdAt: '2024-09-15T10:55:31.403387',
    createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    updatedAt: '2024-09-15T10:55:31.403412',
    updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    name: 'Mock Event 01',
    slug: 'mock_event_01',
    description: 'This is a mock event 01',
    dateStart: '2024-05-01T00:00:00Z',
    dateEnd: '2024-05-02T00:00:00Z',
    timeStart: '17:32:01',
    timeEnd: '17:32:01',
    guacamole: true,
    status: 'f481fb68-4e6b-4027-bf67-ae431bd8b6d1',
    course: '6398feed-be84-4d86-a02e-ca526a7f55ed',
    templates: [
      {
        id: 'ebcf3979-40be-46c4-a9ca-e335d106a7ef',
      },
    ],
    vms: [
      {
        id: 'a1b2c3d4-5678-4e9f-9bcb-2f3a4d5e6f7g',
      },
    ],
    deployment_status: null,
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

  getTemplates: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 1 },
    templates: [
      {
        id: 'ebcf3979-40be-46c4-a9ca-e335d106a7ef',
        createdAt: '2024-09-15T10:55:31.403387',
        createdById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        updatedAt: '2024-09-15T10:55:31.403412',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        name: 'A Mock Template',
        description: 'A template for a mock virtual machines',
        status: 'available',
        proxmoxNode: 'proxmox01',
        proxmoxId: 281,
        cpu: 2,
        ram: 4096,
        disk: 32,
        os: 'dd89af9d-8953-48c5-8083-3e8210219c3e',
        prevent_delete: true,
        applications: [
          {
            chrome: 'Chrome',
          },
        ],
      },
    ],
  }),

  getUsers: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 2 },
    users: [
      {
        id: '448ba2ae-d0f6-42ca-a2a8-abfa13782ab2',
        createdAt: '2024-09-10T17:36:32',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '2024-09-10T17:36:32',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        user_id: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        role_id: '7ca9258a-2200-4367-b3ee-03c1644586c6',
        event_id: '17cc28e6-19c0-46b9-9082-feb09ad0bfcd',
      },
      {
        id: 'a9913bcc-20a3-4f83-a6bb-65a931c467dc',
        createdAt: '2024-09-10T17:36:32',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '2024-09-10T17:36:32',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        user_id: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        role_id: '8327f069-6d2e-4b58-bd95-b78c94f64e52',
        event_id: '17cc28e6-19c0-46b9-9082-feb09ad0bfcd',
      },
    ],
  }),

  getVMs: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 1 },
    virtualMachines: [
      {
        id: 'a1b2c3d4-5678-4e9f-9bcb-2f3a4d5e6f7g',
        createdAt: '2024-09-15T10:55:31.403387',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '2024-09-15T10:55:31.403412',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        name: 'Mock VM 424',
        description: 'A new mock virtual machine 424',
        status: 'running',
        cpu: 4,
        ram: 2048,
        disk: 120,
        os: '85ed6d38-881c-454f-8950-307f64044d16',
        template: 'ebcf3979-40be-46c4-a9ca-e335d106a7ef',
        prevent_delete: true,
        applications: [
          {
            firefox: 'Firefox',
          },
        ],
        proxmoxNode: 'proxmox01',
        proxmoxId: 421,
        event: '17cc28e6-19c0-46b9-9082-feb09ad0bfcd',
        ipv4: '192.168.3.13',
      },
    ],
  }),

  list: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 2 },
    items: [
      {
        id: '17cc28e6-19c0-46b9-9082-feb09ad0bfcd',
        createdAt: '2024-09-15T10:55:31.403387',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '2024-09-15T10:55:31.403412',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        name: 'Mock Event 01',
        slug: 'mock_event_01',
        description: 'This is a mock event 01',
        dateStart: '2024-05-01T00:00:00Z',
        dateEnd: '2024-05-02T00:00:00Z',
        timeStart: '17:32:01',
        timeEnd: '17:32:01',
        guacamole: true,
        status: 'f481fb68-4e6b-4027-bf67-ae431bd8b6d1',
        course: '6398feed-be84-4d86-a02e-ca526a7f55ed',
        templates: [
          {
            id: 'ebcf3979-40be-46c4-a9ca-e335d106a7ef',
          },
        ],
        vms: [
          {
            id: 'a1b2c3d4-5678-4e9f-9bcb-2f3a4d5e6f7g',
          },
        ],
        deployment_status: null,
      },
      {
        id: 'a93fb0a9-50aa-49b9-b066-e3113393d7ac',
        createdAt: '2024-03-15T10:55:31.403387',
        createdById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        updatedAt: '2024-03-15T10:55:31.403412',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        name: 'Mock Event 02',
        slug: 'mock_event_02',
        description: 'This is a mock event 02',
        dateStart: '2024-04-13T00:00:00Z',
        dateEnd: '2024-02-13T00:00:00Z',
        timeStart: '23:21:32',
        timeEnd: '12:02:34',
        guacamole: false,
        status: '1fc851bf-5f4e-4937-bae9-c6d3fd0e5846',
        course: '6398feed-be84-4d86-a02e-ca526a7f55ed',
        templates: [
          {
            id: 'e4182dc3-85d1-408c-aa88-23cc1088011f',
          },
        ],
        vms: null,
        deployment_status: null,
      },
    ],
  }),

  listStatus: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 8 },
    items: [
      {
        id: 'bfbee14d-6f04-4ba1-a39c-0f5764f0563d',
        createdAt: '1970-01-01T00:00:00',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '1970-01-01T00:00:00',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        name: 'Archiviert',
      },
      {
        id: 'f63a9362-eb67-4769-ba93-62eb67b76939',
        createdAt: '1970-01-01T00:00:00',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '1970-01-01T00:00:00',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        name: 'Fehler',
      },
      {
        id: '4d99fe64-3c3c-4a2f-99fe-643c3c1a2f23',
        createdAt: '1970-01-01T00:00:00',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '1970-01-01T00:00:00',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        name: 'Archiving',
      },
      {
        id: 'f13303bf-b25f-4869-9717-698a4db13ada',
        createdAt: '1970-01-01T00:00:00',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '1970-01-01T00:00:00',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        name: 'Deploying',
      },
      {
        id: 'f481fb68-4e6b-4027-bf67-ae431bd8b6d1',
        createdAt: '1970-01-01T00:00:00',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '1970-01-01T00:00:00',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        name: 'Aktiv',
      },
      {
        id: '1fc851bf-5f4e-4937-bae9-c6d3fd0e5846',
        createdAt: '1970-01-01T00:00:00',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '1970-01-01T00:00:00',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        name: 'Stopped',
      },
      {
        id: '53b6993a-57d6-40a6-8d42-e55bf08fac4c',
        createdAt: '1970-01-01T00:00:00',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '1970-01-01T00:00:00',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        name: 'Geplant',
      },
      {
        id: 'cbc20092-629b-483f-babc-ef26202d685e',
        createdAt: '1970-01-01T00:00:00',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '1970-01-01T00:00:00',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        name: 'Inaktiv',
      },
    ],
  }),

  getStatus: vi.fn().mockResolvedValue({
    id: '1fc851bf-5f4e-4937-bae9-c6d3fd0e5846',
    name: 'Stopped',
  }),

  getStatusName: vi.fn().mockResolvedValue('Aktiv'),

  update: vi.fn().mockResolvedValue({
    id: '17cc28e6-19c0-46b9-9082-feb09ad0bfcd',
    name: 'Updated Mock Event',
    description: 'This is an updated mock event',
    dateStart: '2024-05-03T00:00:00Z',
    dateEnd: '2024-05-04T00:00:00Z',
    status: 'f481fb68-4e6b-4027-bf67-ae431bd8b6d1',
  }),

  delete: vi.fn().mockResolvedValue({
    message: 'Event successfully deleted',
  }),

  addUser: vi.fn().mockResolvedValue({
    message: 'User successfully added to event',
  }),

  deleteUser: vi.fn().mockResolvedValue({
    message: 'User successfully removed from event',
  }),

  dropdownStatus: vi.fn().mockResolvedValue([
    {
      value: 'bfbee14d-6f04-4ba1-a39c-0f5764f0563d',
      label: 'Archiviert',
    },
    {
      value: 'f63a9362-eb67-4769-ba93-62eb67b76939',
      label: 'Fehler',
    },
    {
      value: '4d99fe64-3c3c-4a2f-99fe-643c3c1a2f23',
      label: 'Archiving',
    },
    {
      value: 'f13303bf-b25f-4869-9717-698a4db13ada',
      label: 'Deploying',
    },
    {
      value: 'f481fb68-4e6b-4027-bf67-ae431bd8b6d1',
      label: 'Aktiv',
    },
    {
      value: '1fc851bf-5f4e-4937-bae9-c6d3fd0e5846',
      label: 'Stopped',
    },
    {
      value: '53b6993a-57d6-40a6-8d42-e55bf08fac4c',
      label: 'Geplant',
    },
    {
      value: 'cbc20092-629b-483f-babc-ef26202d685e',
      label: 'Inaktiv',
    },
  ]),

  start: vi.fn().mockResolvedValue({
    message: 'Event successfully started',
  }),

  end: vi.fn().mockResolvedValue({
    message: 'Event successfully ended',
  }),

  dropdown: vi.fn().mockResolvedValue([
    {
      label: 'Mock Event 01',
      value: '17cc28e6-19c0-46b9-9082-feb09ad0bfcd',
    },
    {
      label: 'Mock Event 02',
      value: 'a93fb0a9-50aa-49b9-b066-e3113393d7ac',
    },
  ]),

  getName: vi.fn().mockResolvedValue('Mock Event 01'),

  search: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 25, pageCount: 1, totalCount: 1 },
    items: [
      {
        id: '17cc28e6-19c0-46b9-9082-feb09ad0bfcd',
        name: 'Mock Event 01',
        description: 'This is a mock event 01',
        type: 'manual',
        status: 'created',
      },
    ],
  }),

  addTemplate: vi.fn().mockResolvedValue({
    id: '17cc28e6-19c0-46b9-9082-feb09ad0bfcd',
    templates: [
      { id: 'ebcf3979-40be-46c4-a9ca-e335d106a7ef', name: 'A Mock Template' },
    ],
  }),

  extend: vi.fn().mockResolvedValue({
    id: '17cc28e6-19c0-46b9-9082-feb09ad0bfcd',
    endDate: '2025-12-31T23:59:59',
  }),

  bulkAction: vi.fn().mockResolvedValue({
    message: 'Bulk action completed',
  }),

  rerollout: vi.fn().mockResolvedValue({
    id: '17cc28e6-19c0-46b9-9082-feb09ad0bfcd',
    message: 'Event re-rollout initiated',
  }),
}
