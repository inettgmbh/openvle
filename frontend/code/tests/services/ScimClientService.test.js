import { beforeEach, describe, expect, it, vi } from 'vitest'

// Unmock the service under test (global mock is in setupMocks.js)
vi.unmock('@/services/ScimClientService.js')

import ScimClientService from '@/services/ScimClientService'

describe('ScimClientService', () => {
  let service
  let mockHttp

  beforeEach(() => {
    mockHttp = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    }
    service = new ScimClientService(mockHttp)
  })

  describe('Constructor', () => {
    it('sets http instance and path', () => {
      expect(service.http).toBe(mockHttp)
      expect(service.path).toBe('/scim-clients')
    })
  })

  describe('CRUD Operations', () => {
    describe('create', () => {
      it('creates a client with all fields', async () => {
        const clientData = {
          name: 'External LMS',
          description: 'LMS sync client',
          enabled: true,
          endpoint_url: 'https://lms.example.com/scim/v2',
          bearer_token: 'my-token',
          sync_groups: true,
        }
        const expectedResponse = {
          id: '123',
          ...clientData,
        }
        mockHttp.post.mockResolvedValue({ data: expectedResponse })

        const result = await service.create(clientData)

        expect(mockHttp.post).toHaveBeenCalledWith('/scim-clients/', {
          name: 'External LMS',
          description: 'LMS sync client',
          enabled: true,
          endpoint_url: 'https://lms.example.com/scim/v2',
          bearer_token: 'my-token',
          sync_groups: true,
        })
        expect(result).toEqual(expectedResponse)
      })
    })

    describe('get', () => {
      it('retrieves a client by ID', async () => {
        const expectedClient = { id: '123', name: 'External LMS' }
        mockHttp.get.mockResolvedValue({ data: expectedClient })

        const result = await service.get('123')

        expect(mockHttp.get).toHaveBeenCalledWith('/scim-clients/123')
        expect(result).toEqual(expectedClient)
      })

      it('returns false on error', async () => {
        mockHttp.get.mockRejectedValue(new Error('Not found'))

        const result = await service.get('999')

        expect(result).toBe(false)
      })
    })

    describe('list', () => {
      it('retrieves paginated clients with default params', async () => {
        const expectedResponse = {
          pageDetails: { page: 1, perPage: 10 },
          items: [{ id: '1' }, { id: '2' }],
        }
        mockHttp.get.mockResolvedValue({ data: expectedResponse })

        const result = await service.list()

        expect(mockHttp.get).toHaveBeenCalledWith('/scim-clients/', {
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

      it('retrieves clients with custom params', async () => {
        mockHttp.get.mockResolvedValue({ data: {} })

        await service.list({
          page: 2,
          limit: 25,
          search_field: 'name',
          search_value: 'LMS',
          sort_by: 'createdAt',
          sort_order: 'desc',
        })

        expect(mockHttp.get).toHaveBeenCalledWith('/scim-clients/', {
          params: {
            page: 2,
            limit: 25,
            search_field: 'name',
            search_value: 'LMS',
            sort_by: 'createdAt',
            sort_order: 'desc',
          },
        })
      })
    })

    describe('update', () => {
      it('updates a client', async () => {
        const updateData = { name: 'Updated Client' }
        mockHttp.put.mockResolvedValue({
          data: { id: '123', ...updateData },
        })

        const result = await service.update('123', updateData)

        expect(mockHttp.put).toHaveBeenCalledWith(
          '/scim-clients/123',
          updateData,
        )
        expect(result).toEqual({ id: '123', ...updateData })
      })
    })

    describe('delete', () => {
      it('deletes a client', async () => {
        mockHttp.delete.mockResolvedValue({ data: { message: 'Deleted' } })

        const result = await service.delete('123')

        expect(mockHttp.delete).toHaveBeenCalledWith('/scim-clients/123')
        expect(result).toEqual({ message: 'Deleted' })
      })
    })
  })

  describe('Helper Methods', () => {
    describe('getName', () => {
      it('returns client name', async () => {
        mockHttp.get.mockResolvedValue({
          data: { id: '123', name: 'External LMS' },
        })

        const result = await service.getName('123')

        expect(result).toBe('External LMS')
      })
    })

    describe('dropdown', () => {
      it('returns formatted dropdown options', async () => {
        mockHttp.get.mockResolvedValue({
          data: {
            items: [
              { id: '1', name: 'External LMS' },
              { id: '2', name: 'HR System' },
            ],
          },
        })

        const result = await service.dropdown()

        expect(result).toEqual([
          { label: 'External LMS', value: '1' },
          { label: 'HR System', value: '2' },
        ])
      })
    })

    describe('search', () => {
      it('searches clients by name', async () => {
        mockHttp.get.mockResolvedValue({
          data: {
            pageDetails: { page: 1, perPage: 25 },
            items: [{ id: '1', name: 'External LMS' }],
          },
        })

        const result = await service.search('LMS')

        expect(mockHttp.get).toHaveBeenCalledWith('/scim-clients/', {
          params: {
            page: 1,
            limit: 25,
            search_field: 'name',
            search_value: 'LMS',
            sort_by: 'name',
            sort_order: 'asc',
          },
        })
        expect(result.items).toHaveLength(1)
        expect(result.items[0].name).toBe('External LMS')
      })
    })
  })

  describe('Role Management', () => {
    describe('updateRoles', () => {
      it('replaces roles for a client', async () => {
        const roles = [{ key: 'admin' }, { key: 'user' }]
        mockHttp.put.mockResolvedValue({ data: { message: 'Updated' } })

        await service.updateRoles('123', roles)

        expect(mockHttp.put).toHaveBeenCalledWith('/scim-clients/123/roles', {
          roles,
        })
      })
    })

    describe('addRoles', () => {
      it('adds roles to a client', async () => {
        const roles = [{ key: 'editor' }]
        mockHttp.post.mockResolvedValue({ data: { message: 'Added' } })

        await service.addRoles('123', roles)

        expect(mockHttp.post).toHaveBeenCalledWith('/scim-clients/123/roles', {
          roles,
        })
      })
    })
  })

  describe('User Mappings', () => {
    describe('getUserMappings', () => {
      it('retrieves user mappings with default params', async () => {
        const expectedResponse = {
          pageDetails: { page: 1, perPage: 10 },
          items: [{ user_id: '1', external_scim_id: 'ext-1' }],
        }
        mockHttp.get.mockResolvedValue({ data: expectedResponse })

        const result = await service.getUserMappings('123')

        expect(mockHttp.get).toHaveBeenCalledWith(
          '/scim-clients/123/user-mappings',
          {
            params: {
              page: 1,
              limit: 10,
              sort_by: 'last_synced_at',
              sort_order: 'desc',
            },
          },
        )
        expect(result).toEqual(expectedResponse)
      })

      it('retrieves user mappings with custom params', async () => {
        mockHttp.get.mockResolvedValue({ data: {} })

        await service.getUserMappings('123', {
          page: 2,
          limit: 25,
          sort_by: 'user_id',
          sort_order: 'asc',
        })

        expect(mockHttp.get).toHaveBeenCalledWith(
          '/scim-clients/123/user-mappings',
          {
            params: {
              page: 2,
              limit: 25,
              sort_by: 'user_id',
              sort_order: 'asc',
            },
          },
        )
      })
    })
  })
})
