import { vi } from 'vitest'

export default {
  create: vi.fn().mockResolvedValue({
    subject: 'Mock Mail Subject',
    fromName: 'Mock Sender',
    fromMail: 'from@mock.com',
    toMail: 'to@mock.com',
    templateId: 'f9f9c4a2-8d49-4e9a-bbaf-05b0ffdb93e6',
    replyTo: 'replyto@mock.com',
  }),

  get: vi.fn().mockResolvedValue({
    id: 'd290f1ee-6c54-4b01-90e6-d701748f0851',
    createdAt: '2024-09-15T14:00:03.800094',
    createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    updatedAt: '2024-09-15T14:00:03.800118',
    updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
    subject: 'Mock Mail Subject 01',
    fromName: 'Mock Sender',
    fromMail: 'from@mock.com',
    toMail: 'recipient01@mock.com',
    sendStatus: 'sent',
    templateId: 'f9f9c4a2-8d49-4e9a-bbaf-05b0ffdb93e6',
    replyTo: 'replyto@mock.com',
    content_rendered: 'Mock Content 01',
  }),

  list: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 3 },
    items: [
      {
        id: 'd290f1ee-6c54-4b01-90e6-d701748f0851',
        createdAt: '2024-09-15T14:00:03.800094',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '2024-09-15T14:00:03.800118',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        subject: 'Mock Mail Subject 01',
        fromName: 'Mock Sender',
        fromMail: 'from@mock.com',
        toMail: 'recipient01@mock.com',
        sendStatus: 'sent',
        templateId: 'f9f9c4a2-8d49-4e9a-bbaf-05b0ffdb93e6',
        replyTo: 'replyto@mock.com',
        content_rendered: 'Mock Content 01',
      },
      {
        id: 'b5b64d9e-5f1c-4f3e-ae74-60d68c7b9d8f',
        createdAt: '2024-09-10T14:00:03.800094',
        createdById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        updatedAt: '2024-09-10T14:00:03.800118',
        updatedById: 'd4f82710-19a4-4b29-8e9b-98b52af1d2d3',
        subject: 'Mock Mail Subject 02',
        fromName: 'Mock Sender',
        fromMail: 'from@mock.com',
        toMail: 'recipient02@mock.com',
        sendStatus: 'sent',
        templateId: 'c6224e1b-436f-41af-9559-3019911a81a5',
        replyTo: 'replyto@mock.com',
        content_rendered: 'Mock Content 02',
      },
      {
        id: '34385696-2cfb-4af5-84cf-4bfeed6f19d5',
        createdAt: '2024-09-11T14:00:03.800094',
        createdById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        updatedAt: '2024-09-11T14:00:03.800118',
        updatedById: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        subject: 'Mock Subject 03',
        fromName: 'Mock Sender',
        fromMail: 'from@mock.com',
        toMail: 'recipient03@mock.com',
        sendStatus: 'sent',
        templateId: '7f9ef0db-9f3a-42b5-9046-bcb131ebaae9',
        replyTo: 'replyto@mock.com',
        content_rendered: 'Mock Content 03',
      },
    ],
  }),

  delete: vi.fn().mockResolvedValue({
    message: 'Mail successfully deleted',
  }),

  listByUser: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 1 },
    items: [
      {
        id: 'a3b3e7d6-7c62-4cbb-b46a-1d6e1f66aec1',
        createdAt: '2024-09-15T13:15:58',
        sender: 'noreply@mock.com',
        subject: 'Mock Mail Subject',
        recipients: ['mockuser01@example.com'],
        status: 'delivered',
      },
    ],
  }),

  listByEvent: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 1 },
    items: [
      {
        id: 'a3b3e7d6-7c62-4cbb-b46a-1d6e1f66aec1',
        createdAt: '2024-09-15T13:15:58',
        sender: 'noreply@mock.com',
        subject: 'Event Notification',
        recipients: ['mockuser01@example.com'],
        status: 'delivered',
      },
    ],
  }),
}
