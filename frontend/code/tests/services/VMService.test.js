import { beforeEach, describe, expect, it, vi } from 'vitest'

// Unmock the service under test (global mock is in setupMocks.js)
vi.unmock('@/services/VMService.js')

import VMService from '@/services/VMService'

describe('VMService', () => {
  let service
  let mockHttp

  beforeEach(() => {
    mockHttp = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    }
    service = new VMService(mockHttp)
  })

  describe('Constructor', () => {
    it('sets http instance and path', () => {
      expect(service.http).toBe(mockHttp)
      expect(service.path).toBe('/virtual_machines')
    })
  })

  describe('High Availability (HA)', () => {
    describe('getHa', () => {
      it('fetches the HA state of a VM', async () => {
        const haState = {
          type: 'vm',
          state: 'started',
          max_restart: 5,
          max_relocate: 5,
          digest: 'abc123',
        }
        mockHttp.get.mockResolvedValue({ data: haState })

        const result = await service.getHa('vm-1')

        expect(mockHttp.get).toHaveBeenCalledWith(
          '/virtual_machines/vm-1/actions/ha',
        )
        expect(result).toEqual(haState)
      })

      it('returns the synthesized state for a VM without HA', async () => {
        const haState = {
          type: 'vm',
          state: 'ignored',
          max_restart: 0,
          max_relocate: 0,
          digest: null,
        }
        mockHttp.get.mockResolvedValue({ data: haState })

        const result = await service.getHa('vm-1')

        expect(result.state).toBe('ignored')
        expect(result.digest).toBeNull()
      })
    })

    describe('setHa', () => {
      it('posts the backend defaults when no config is given', async () => {
        mockHttp.post.mockResolvedValue({ data: { id: 'vm-1' } })

        const result = await service.setHa('vm-1')

        expect(mockHttp.post).toHaveBeenCalledWith(
          '/virtual_machines/vm-1/actions/ha',
          {
            ha_state: 'started',
            ha_max_restart: 5,
            ha_max_relocate: 5,
          },
        )
        expect(result).toEqual({ id: 'vm-1' })
      })

      it('maps a custom config to the snake_cased request body', async () => {
        mockHttp.post.mockResolvedValue({ data: { id: 'vm-1' } })

        await service.setHa('vm-1', {
          haState: 'disabled',
          haMaxRestart: 2,
          haMaxRelocate: 0,
        })

        expect(mockHttp.post).toHaveBeenCalledWith(
          '/virtual_machines/vm-1/actions/ha',
          {
            ha_state: 'disabled',
            ha_max_restart: 2,
            ha_max_relocate: 0,
          },
        )
      })

      it('fills missing config fields with defaults', async () => {
        mockHttp.post.mockResolvedValue({ data: { id: 'vm-1' } })

        await service.setHa('vm-1', { haState: 'stopped' })

        expect(mockHttp.post).toHaveBeenCalledWith(
          '/virtual_machines/vm-1/actions/ha',
          {
            ha_state: 'stopped',
            ha_max_restart: 5,
            ha_max_relocate: 5,
          },
        )
      })
    })

    describe('removeHa', () => {
      it('deletes the HA configuration of a VM', async () => {
        mockHttp.delete.mockResolvedValue({ data: { id: 'vm-1' } })

        const result = await service.removeHa('vm-1')

        expect(mockHttp.delete).toHaveBeenCalledWith(
          '/virtual_machines/vm-1/actions/ha',
        )
        expect(result).toEqual({ id: 'vm-1' })
      })
    })
  })
})
