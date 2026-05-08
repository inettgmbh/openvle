import { beforeEach, describe, expect, it, vi } from 'vitest'

// Unmock the service under test (global mock is in setupMocks.js)
vi.unmock('@/services/MoodleService.js')

import MoodleService from '@/services/MoodleService'

describe('MoodleService', () => {
  let service
  let mockHttp

  beforeEach(() => {
    vi.clearAllMocks()

    mockHttp = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    }
    service = new MoodleService(mockHttp)
  })

  describe('Constructor', () => {
    it('sets http instance and path', () => {
      expect(service.http).toBe(mockHttp)
      expect(service.path).toBe('/moodle/courses')
    })
  })

  describe('search', () => {
    it('calls http.get with search query and returns data', async () => {
      const expectedData = {
        items: [{ id: 1, fullname: 'Intro to CS' }],
        pageDetails: { page: 1, perPage: 25 },
      }
      mockHttp.get.mockResolvedValue({ data: expectedData })

      const result = await service.search('Intro')

      expect(mockHttp.get).toHaveBeenCalledWith('/moodle/courses', {
        params: { search: 'Intro' },
      })
      expect(result).toEqual(expectedData)
    })

    it('calls http.get with empty string for fetchAll/preload', async () => {
      const expectedData = {
        items: [
          { id: 1, fullname: 'Intro to CS' },
          { id: 2, fullname: 'Advanced Math' },
        ],
        pageDetails: { page: 1, perPage: 25 },
      }
      mockHttp.get.mockResolvedValue({ data: expectedData })

      const result = await service.search('')

      expect(mockHttp.get).toHaveBeenCalledWith('/moodle/courses', {
        params: { search: '' },
      })
      expect(result).toEqual(expectedData)
    })
  })

  describe('getName', () => {
    it('returns fullname when course is found', async () => {
      mockHttp.get.mockResolvedValue({
        data: {
          items: [{ id: 42, fullname: 'Intro to CS' }],
        },
      })

      const result = await service.getName(42)

      expect(mockHttp.get).toHaveBeenCalledWith('/moodle/courses', {
        params: { id: 42 },
      })
      expect(result).toBe('Intro to CS')
    })

    it('returns fallback when items array is empty', async () => {
      mockHttp.get.mockResolvedValue({
        data: { items: [] },
      })

      const result = await service.getName(99)

      expect(result).toBe('Moodle #99')
    })

    it('returns fallback when items is undefined', async () => {
      mockHttp.get.mockResolvedValue({
        data: {},
      })

      const result = await service.getName(99)

      expect(result).toBe('Moodle #99')
    })
  })
})
