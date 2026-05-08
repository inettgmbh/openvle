import { vi } from 'vitest'

export default {
  search: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 25, pageCount: 1, totalCount: 2 },
    items: [
      {
        id: 101,
        fullname: 'Netzwerktechnik Labor WS25',
        shortname: 'NWT-WS25',
        categoryname: 'Informatik',
        startdate: 1727740800,
        enddate: 1735689600,
        visible: true,
      },
      {
        id: 102,
        fullname: 'Linux Grundlagen SS26',
        shortname: 'LIN-SS26',
        categoryname: 'Informatik',
        startdate: 1743465600,
        enddate: 1751328000,
        visible: false,
      },
    ],
  }),

  getName: vi.fn().mockResolvedValue('Netzwerktechnik Labor WS25'),
}
