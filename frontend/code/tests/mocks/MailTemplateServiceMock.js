import { vi } from 'vitest'

export default {
  // ============================================================
  // Standard CRUD Methods (New API)
  // ============================================================
  create: vi.fn().mockResolvedValue({
    name: 'New Mock Mail Template',
    subject: 'New Mock Subject',
    description: 'This is a new mock mail template',
    fromName: 'Mock Sender',
    fromMail: 'from@mock.com',
    contentHTML: '<p>Mock HTML content</p>',
    contentPlain: 'Mock plain content',
    language: '08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0',
    protected: false,
    replyTo: 'replyto@mock.com',
  }),

  get: vi.fn().mockResolvedValue({
    id: 'f9f9c4a2-8d49-4e9a-bbaf-05b0ffdb93e6',
    name: 'Mock Mail Template 01',
    subject: 'Mock Subject 01',
    description: 'This is a mock mail template 01',
    fromName: 'Mock Sender',
    fromMail: 'from@mock.com',
    contentHTML: '<p>Mock HTML content</p>',
    contentPlain: 'Mock plain content',
    language: '08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0',
    protected: false,
    replyTo: 'replyto@mock.com',
  }),

  list: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 3 },
    items: [
      {
        id: 'f9f9c4a2-8d49-4e9a-bbaf-05b0ffdb93e6',
        name: 'Mock Mail Template 01',
        subject: 'Mock Subject 01',
        description: 'This is a mock mail template 01',
        fromName: 'Mock Sender',
        fromMail: 'from@mock.com',
        contentHTML: '<p>Mock HTML content</p>',
        contentPlain: 'Mock plain content',
        language: '08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0',
        protected: false,
        replyTo: 'replyto@mock.com',
      },
      {
        id: 'c6224e1b-436f-41af-9559-3019911a81a5',
        name: 'Mock Mail Template 02',
        subject: 'Mock Subject 02',
        description: 'This is a mock mail template 02',
        fromName: 'Mock Sender',
        fromMail: 'from@mock.com',
        contentHTML: '<p>Mock HTML content</p>',
        contentPlain: 'Mock plain content',
        language: '08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0',
        protected: true,
        replyTo: 'replyto@mock.com',
      },
      {
        id: '7f9ef0db-9f3a-42b5-9046-bcb131ebaae9',
        name: 'Mock Mail Template 03',
        subject: 'Mock Subject 03',
        description: 'This is a mock mail template 03',
        fromName: 'Mock Sender',
        fromMail: 'from@mock.com',
        contentHTML: '<p>Mock HTML content</p>',
        contentPlain: 'Mock plain content',
        language: '08cf9a2d-e8b6-4040-88bf-7b8a8c40e0e0',
        protected: false,
        replyTo: 'replyto@mock.com',
      },
    ],
  }),

  update: vi.fn().mockResolvedValue({
    id: 'f9f9c4a2-8d49-4e9a-bbaf-05b0ffdb93e6',
    name: 'Updated Mock Mail Template',
    subject: 'Updated Mock Subject',
    description: 'This is an updated mock mail template',
    fromName: 'Mock Sender',
    fromMail: 'from@mock.com',
    contentHTML: '<p>Updated Mock HTML content</p>',
    replyTo: 'replyto@mock.com',
  }),

  delete: vi.fn().mockResolvedValue({
    message: 'Mail Template successfully deleted',
  }),

  // ============================================================
  // Helper Methods (New API)
  // ============================================================
  getName: vi.fn().mockResolvedValue('Mock Mail Template 01'),

  search: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 25, pageCount: 1, totalCount: 1 },
    items: [
      {
        id: 'f9f9c4a2-8d49-4e9a-bbaf-05b0ffdb93e6',
        name: 'Mock Mail Template 01',
        key: 'mock_mail_template',
        description: 'A mock mail template',
        active: true,
      },
    ],
  }),

  dropdown: vi.fn().mockResolvedValue([
    {
      label: 'Mock Mail Template 01',
      value: 'f9f9c4a2-8d49-4e9a-bbaf-05b0ffdb93e6',
    },
    {
      label: 'Mock Mail Template 02',
      value: 'c6224e1b-436f-41af-9559-3019911a81a5',
    },
    {
      label: 'Mock Mail Template 03',
      value: '7f9ef0db-9f3a-42b5-9046-bcb131ebaae9',
    },
  ]),

  // ============================================================
  // Related Resources (New API)
  // ============================================================
  getMails: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 1 },
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
    ],
  }),

  // ============================================================
  // Protection Methods (New API)
  // ============================================================
  setProtection: vi.fn().mockResolvedValue({
    id: 'f9f9c4a2-8d49-4e9a-bbaf-05b0ffdb93e6',
    protected: true,
  }),

  // ============================================================
  // Mail Action Assignment (New API)
  // ============================================================
  unassignMailAction: vi.fn().mockResolvedValue({
    message: 'Mail template unassigned successfully',
  }),

  assignMailAction: vi.fn().mockResolvedValue({
    message: 'Mail template assigned successfully',
  }),
}
