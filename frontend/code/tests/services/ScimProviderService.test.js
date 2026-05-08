import { beforeEach, describe, expect, it, vi } from 'vitest'

// Unmock the service under test (global mock is in setupMocks.js)
vi.unmock('@/services/ScimProviderService.js')

import ScimProviderService from '@/services/ScimProviderService'

describe('ScimProviderService', () => {
  let service
  let mockHttp

  beforeEach(() => {
    mockHttp = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    }
    service = new ScimProviderService(mockHttp)
  })

  describe('Constructor', () => {
    it('sets http instance and path', () => {
      expect(service.http).toBe(mockHttp)
      expect(service.path).toBe('/scim-providers')
    })
  })

  describe('CRUD Operations', () => {
    describe('create', () => {
      it('creates a provider with all fields', async () => {
        const providerData = {
          name: 'Authentik',
          description: 'Authentik provider',
          enabled: true,
          default_user_status: 'Active',
        }
        const expectedResponse = {
          id: '123',
          ...providerData,
          bearer_token: 'generated-token',
        }
        mockHttp.post.mockResolvedValue({ data: expectedResponse })

        const result = await service.create(providerData)

        expect(mockHttp.post).toHaveBeenCalledWith('/scim-providers/', {
          name: 'Authentik',
          description: 'Authentik provider',
          enabled: true,
          default_user_status: 'Active',
        })
        expect(result).toEqual(expectedResponse)
      })
    })

    describe('get', () => {
      it('retrieves a provider by ID', async () => {
        const expectedProvider = { id: '123', name: 'Authentik' }
        mockHttp.get.mockResolvedValue({ data: expectedProvider })

        const result = await service.get('123')

        expect(mockHttp.get).toHaveBeenCalledWith('/scim-providers/123')
        expect(result).toEqual(expectedProvider)
      })

      it('returns false on error', async () => {
        mockHttp.get.mockRejectedValue(new Error('Not found'))

        const result = await service.get('999')

        expect(result).toBe(false)
      })
    })

    describe('list', () => {
      it('retrieves paginated providers with default params', async () => {
        const expectedResponse = {
          pageDetails: { page: 1, perPage: 10 },
          items: [{ id: '1' }, { id: '2' }],
        }
        mockHttp.get.mockResolvedValue({ data: expectedResponse })

        const result = await service.list()

        expect(mockHttp.get).toHaveBeenCalledWith('/scim-providers/', {
          params: {
            page: 1,
            limit: 10,
            search_field: '',
            search_value: '',
            sort_by: 'name',
            sort_order: 'asc',
          },
        })
        expect(result).toEqual(expectedResponse)
      })

      it('retrieves providers with custom params', async () => {
        mockHttp.get.mockResolvedValue({ data: {} })

        await service.list({
          page: 2,
          limit: 25,
          search_field: 'name',
          search_value: 'Authentik',
          sort_by: 'createdAt',
          sort_order: 'desc',
        })

        expect(mockHttp.get).toHaveBeenCalledWith('/scim-providers/', {
          params: {
            page: 2,
            limit: 25,
            search_field: 'name',
            search_value: 'Authentik',
            sort_by: 'createdAt',
            sort_order: 'desc',
          },
        })
      })
    })

    describe('update', () => {
      it('updates a provider', async () => {
        const updateData = { name: 'Updated Provider' }
        mockHttp.put.mockResolvedValue({
          data: { id: '123', ...updateData },
        })

        const result = await service.update('123', updateData)

        expect(mockHttp.put).toHaveBeenCalledWith(
          '/scim-providers/123',
          updateData,
        )
        expect(result).toEqual({ id: '123', ...updateData })
      })
    })

    describe('delete', () => {
      it('deletes a provider', async () => {
        mockHttp.delete.mockResolvedValue({ data: { message: 'Deleted' } })

        const result = await service.delete('123')

        expect(mockHttp.delete).toHaveBeenCalledWith('/scim-providers/123')
        expect(result).toEqual({ message: 'Deleted' })
      })
    })
  })

  describe('Helper Methods', () => {
    describe('getName', () => {
      it('returns provider name', async () => {
        mockHttp.get.mockResolvedValue({
          data: { id: '123', name: 'Authentik' },
        })

        const result = await service.getName('123')

        expect(result).toBe('Authentik')
      })
    })

    describe('dropdown', () => {
      it('returns formatted dropdown options', async () => {
        mockHttp.get.mockResolvedValue({
          data: {
            items: [
              { id: '1', name: 'Authentik' },
              { id: '2', name: 'Okta' },
            ],
          },
        })

        const result = await service.dropdown()

        expect(result).toEqual([
          { label: 'Authentik', value: '1' },
          { label: 'Okta', value: '2' },
        ])
      })
    })

    describe('search', () => {
      it('searches providers by name', async () => {
        mockHttp.get.mockResolvedValue({
          data: {
            pageDetails: { page: 1, perPage: 25 },
            items: [{ id: '1', name: 'Authentik' }],
          },
        })

        const result = await service.search('Authentik')

        expect(mockHttp.get).toHaveBeenCalledWith('/scim-providers/', {
          params: {
            page: 1,
            limit: 25,
            search_field: 'name',
            search_value: 'Authentik',
            sort_by: 'name',
            sort_order: 'asc',
          },
        })
        expect(result.items).toHaveLength(1)
        expect(result.items[0].name).toBe('Authentik')
      })
    })
  })

  describe('Token Management', () => {
    describe('rotateToken', () => {
      it('rotates the bearer token', async () => {
        const expectedResponse = {
          id: '123',
          name: 'Authentik',
          bearer_token: 'new-token-abc',
        }
        mockHttp.post.mockResolvedValue({ data: expectedResponse })

        const result = await service.rotateToken('123')

        expect(mockHttp.post).toHaveBeenCalledWith(
          '/scim-providers/123/rotate-token',
        )
        expect(result).toEqual(expectedResponse)
      })
    })
  })

  describe('Role Management', () => {
    describe('updateRoles', () => {
      it('replaces roles for a provider', async () => {
        const roles = [{ key: 'admin' }, { key: 'user' }]
        mockHttp.put.mockResolvedValue({ data: { message: 'Updated' } })

        await service.updateRoles('123', roles)

        expect(mockHttp.put).toHaveBeenCalledWith('/scim-providers/123/roles', {
          roles,
        })
      })
    })

    describe('addRoles', () => {
      it('adds roles to a provider', async () => {
        const roles = [{ key: 'editor' }]
        mockHttp.post.mockResolvedValue({ data: { message: 'Added' } })

        await service.addRoles('123', roles)

        expect(mockHttp.post).toHaveBeenCalledWith(
          '/scim-providers/123/roles',
          { roles },
        )
      })
    })
  })
})
