import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.unmock('@/services/MeService.js')

import MeService from '@/services/MeService'

describe('MeService', () => {
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
    service = new MeService(mockHttp)
  })

  describe('Constructor', () => {
    it('sets http instance and path', () => {
      expect(service.http).toBe(mockHttp)
      expect(service.path).toBe('/me')
    })
  })

  describe('get', () => {
    it('retrieves the currently authenticated user from /me', async () => {
      const user = { id: '123', name: 'Current User' }
      mockHttp.get.mockResolvedValue({ data: user })

      const result = await service.get()

      expect(mockHttp.get).toHaveBeenCalledWith('/me')
      expect(result).toEqual(user)
    })
  })

  describe('getPermissions', () => {
    it('retrieves the current user permissions from /me/permissions', async () => {
      const permissions = [{ type: 'users', permissions: ['read'] }]
      mockHttp.get.mockResolvedValue({ data: permissions })

      const result = await service.getPermissions()

      expect(mockHttp.get).toHaveBeenCalledWith('/me/permissions')
      expect(result).toEqual(permissions)
    })
  })

  describe('updatePassword', () => {
    it('PUTs the password change to /me/password', async () => {
      mockHttp.put.mockResolvedValue({ data: { message: 'Updated' } })

      const result = await service.updatePassword('old123', 'new456', 'new456')

      expect(mockHttp.put).toHaveBeenCalledWith('/me/password', {
        password_old: 'old123',
        password_new: 'new456',
        password_new_repeat: 'new456',
      })
      expect(result).toEqual({ message: 'Updated' })
    })
  })
})
