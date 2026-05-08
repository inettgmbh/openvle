import { vi } from 'vitest'

export default {
  get: vi.fn().mockResolvedValue({
    id: '66e6d09d444a12cc50661aef',
    timestamp: '2024-09-15T12:18:37.237102+00:00',
    requestClientIP: '10.1.1.201',
    requestUser: '',
    requestPermission: 'api_version_read',
    requestMethod: 'HEAD',
    requestUrl: '/system/api/version',
    requestParameter: {},
    requestHeaders: {
      host: 'localhost',
      connection: 'close',
    },
    responseCode: 405,
    responseHeaders: {
      allow: 'GET',
      'content-length': '31',
      'content-type': 'application/json',
      'x-created-by': 'Test GmbH',
      'x-process-time': '0.0007627010345458984',
    },
  }),

  list: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 3 },
    items: [
      {
        id: '66e6d09d444a12cc50661aef',
        timestamp: '2024-09-15T12:18:37.237102+00:00',
        requestClientIP: '10.1.1.201',
        requestUser: '',
        requestPermission: 'api_version_read',
        requestMethod: 'HEAD',
        requestUrl: '/system/api/version',
        requestParameter: {},
        requestHeaders: { host: 'localhost', connection: 'close' },
        responseCode: 405,
        responseHeaders: {
          allow: 'GET',
          'content-length': '31',
          'content-type': 'application/json',
          'x-created-by': 'Test GmbH',
          'x-process-time': '0.0007627010345458984',
        },
      },
      {
        id: '66e6d09d444a12cc50461aef',
        timestamp: '2024-09-15T12:18:37.237102+00:00',
        requestClientIP: '10.1.1.201',
        requestUser: '',
        requestPermission: 'api_version_read',
        requestMethod: 'HEAD',
        requestUrl: '/system/api/version',
        requestParameter: {},
        requestHeaders: {
          host: 'localhost',
          connection: 'close',
        },
        responseCode: 405,
        responseHeaders: {
          allow: 'GET',
          'content-length': '31',
          'content-type': 'application/json',
          'x-created-by': 'Test GmbH',
          'x-process-time': '0.0007627010345458984',
        },
      },
      {
        id: '77f7d09d444a12cc50661aff',
        timestamp: '2024-09-16T08:45:12.123456+00:00',
        requestClientIP: '10.1.1.202',
        requestUser: 'e0f82710-27b6-4b57-9f6a-13c4d4f51f8d',
        requestPermission: 'api_data_read',
        requestMethod: 'GET',
        requestUrl: '/data/api/list',
        requestParameter: {},
        requestHeaders: {
          host: 'localhost',
          connection: 'keep-alive',
        },
        responseCode: 200,
        responseHeaders: {
          'content-length': '1024',
          'content-type': 'application/json',
          'x-created-by': 'Test GmbH',
          'x-process-time': '0.0012345678901234567',
        },
      },
    ],
  }),
}
