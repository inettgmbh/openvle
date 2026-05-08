import { beforeEach, describe, expect, it, vi } from 'vitest'

// Unmock the service under test (global mock is in setupMocks.js)
vi.unmock('@/services/RoleService.js')

import RoleService from '@/services/RoleService'

// Mock the store import
vi.mock('@/stores/main.js', () => ({
  useMainStore: vi.fn(() => ({
    settings: {
      roles: {
        students: 'student-role-id',
        teachers: 'teacher-role-id',
      },
    },
  })),
}))

describe('RoleService', () => {
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
    service = new RoleService(mockHttp)
  })

  describe('Constructor', () => {
    it('sets http instance and path', () => {
      expect(service.http).toBe(mockHttp)
      expect(service.path).toBe('/roles')
    })
  })

  describe('Lazy-loaded Properties', () => {
    it('mainStore getter returns store instance', () => {
      const store = service.mainStore
      expect(store).toBeDefined()
      expect(store.settings.roles.students).toBe('student-role-id')
    })

    it('mainStore caches the instance', () => {
      const store1 = service.mainStore
      const store2 = service.mainStore
      expect(store1).toBe(store2)
    })
  })

  describe('CRUD Operations', () => {
    describe('create', () => {
      it('creates a role with all fields', async () => {
        const roleData = {
          name: 'Admin',
          key: 'admin',
          description: 'Administrator role',
          protected: true,
        }
        const expectedResponse = { id: '123', ...roleData }
        mockHttp.post.mockResolvedValue({ data: expectedResponse })

        const result = await service.create(roleData)

        expect(mockHttp.post).toHaveBeenCalledWith('/roles/', {
          name: 'Admin',
          key: 'admin',
          description: 'Administrator role',
          protected: true,
        })
        expect(result).toEqual(expectedResponse)
      })
    })

    describe('get', () => {
      it('retrieves a role by ID', async () => {
        const expectedRole = { id: '123', name: 'Admin' }
        mockHttp.get.mockResolvedValue({ data: expectedRole })

        const result = await service.get('123')

        expect(mockHttp.get).toHaveBeenCalledWith('/roles/123')
        expect(result).toEqual(expectedRole)
      })

      it('returns false for student role', async () => {
        const result = await service.get('student-role-id')

        expect(mockHttp.get).not.toHaveBeenCalled()
        expect(result).toBe(false)
      })

      it('returns false for teacher role', async () => {
        const result = await service.get('teacher-role-id')

        expect(mockHttp.get).not.toHaveBeenCalled()
        expect(result).toBe(false)
      })

      it('returns false on error', async () => {
        mockHttp.get.mockRejectedValue(new Error('Not found'))

        const result = await service.get('nonexistent')

        expect(result).toBe(false)
      })
    })

    describe('list', () => {
      it('retrieves paginated roles with default params', async () => {
        const response = {
          pageDetails: { page: 1, perPage: 10 },
          items: [
            { id: '1', name: 'Admin' },
            { id: '2', name: 'User' },
          ],
        }
        mockHttp.get.mockResolvedValue({ data: response })

        const result = await service.list()

        expect(mockHttp.get).toHaveBeenCalledWith('/roles/', {
          params: {
            page: 1,
            limit: 10,
            search_field: '',
            search_value: '',
            sort_by: 'name',
            sort_order: 'asc',
          },
        })
        expect(result.items).toEqual(response.items)
      })

      it('filters out student and teacher roles', async () => {
        const response = {
          pageDetails: { page: 1, perPage: 10 },
          items: [
            { id: '1', name: 'Admin' },
            { id: 'student-role-id', name: 'Students' },
            { id: 'teacher-role-id', name: 'Teachers' },
            { id: '2', name: 'User' },
          ],
        }
        mockHttp.get.mockResolvedValue({ data: response })

        const result = await service.list()

        expect(result.items).toEqual([
          { id: '1', name: 'Admin' },
          { id: '2', name: 'User' },
        ])
      })

      it('supports custom params', async () => {
        mockHttp.get.mockResolvedValue({
          data: { pageDetails: {}, items: [] },
        })

        await service.list({
          page: 2,
          limit: 25,
          search_field: 'name',
          search_value: 'admin',
          sort_by: 'createdAt',
          sort_order: 'desc',
        })

        expect(mockHttp.get).toHaveBeenCalledWith('/roles/', {
          params: {
            page: 2,
            limit: 25,
            search_field: 'name',
            search_value: 'admin',
            sort_by: 'createdAt',
            sort_order: 'desc',
          },
        })
      })
    })

    describe('update', () => {
      it('updates a role', async () => {
        const updateData = { name: 'Updated Role', description: 'New desc' }
        mockHttp.put.mockResolvedValue({ data: { id: '123', ...updateData } })

        const result = await service.update('123', updateData)

        expect(mockHttp.put).toHaveBeenCalledWith('/roles/123', updateData)
        expect(result).toEqual({ id: '123', ...updateData })
      })
    })

    describe('delete', () => {
      it('deletes a role', async () => {
        mockHttp.delete.mockResolvedValue({ data: { message: 'Deleted' } })

        const result = await service.delete('123')

        expect(mockHttp.delete).toHaveBeenCalledWith('/roles/123')
        expect(result).toEqual({ message: 'Deleted' })
      })
    })
  })

  describe('Helper Methods', () => {
    describe('getName', () => {
      it('returns role name', async () => {
        mockHttp.get.mockResolvedValue({
          data: { id: '123', name: 'Admin' },
        })

        const result = await service.getName('123')

        expect(mockHttp.get).toHaveBeenCalledWith('/roles/123')
        expect(result).toBe('Admin')
      })
    })

    describe('dropdown', () => {
      it('returns formatted dropdown options', async () => {
        mockHttp.get.mockResolvedValue({
          data: {
            items: [
              { id: '1', name: 'Admin', key: 'admin' },
              { id: '2', name: 'User', key: 'user' },
            ],
          },
        })

        const result = await service.dropdown()

        expect(result).toEqual([
          { id: '1', label: 'Admin', value: 'admin' },
          { id: '2', label: 'User', value: 'user' },
        ])
      })
    })

    describe('eventRolesDropdown', () => {
      it('returns student and teacher role options', async () => {
        const result = await service.eventRolesDropdown()

        expect(result).toEqual([
          { label: 'Studierende', value: 'student-role-id' },
          { label: 'Lehrende', value: 'teacher-role-id' },
        ])
      })
    })

    describe('search', () => {
      it('searches roles by name', async () => {
        mockHttp.get.mockResolvedValue({
          data: {
            pageDetails: { page: 1, perPage: 25 },
            items: [{ id: '1', name: 'Admin' }],
          },
        })

        const result = await service.search('Admin')

        expect(mockHttp.get).toHaveBeenCalledWith('/roles/', {
          params: expect.objectContaining({
            search_field: 'name',
            search_value: 'Admin',
            limit: 25,
          }),
        })
        expect(result.items).toEqual([{ id: '1', name: 'Admin' }])
      })
    })
  })

  describe('Members Management', () => {
    describe('getMembers', () => {
      it('retrieves role members with default params', async () => {
        const response = {
          pageDetails: { page: 1, perPage: 10 },
          items: [{ id: 'user-1', name: 'User One' }],
        }
        mockHttp.get.mockResolvedValue({ data: response })

        const result = await service.getMembers('123')

        expect(mockHttp.get).toHaveBeenCalledWith('/roles/123/members', {
          params: {
            page: 1,
            limit: 10,
            search_field: '',
            search_value: '',
            sort_by: 'name',
            sort_order: 'asc',
          },
        })
        expect(result).toEqual(response)
      })

      it('supports custom params', async () => {
        mockHttp.get.mockResolvedValue({ data: { items: [] } })

        await service.getMembers('123', { page: 2, limit: 20 })

        expect(mockHttp.get).toHaveBeenCalledWith('/roles/123/members', {
          params: expect.objectContaining({ page: 2, limit: 20 }),
        })
      })
    })
  })
})
