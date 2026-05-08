import { beforeEach, describe, expect, it, vi } from 'vitest'

// Unmock the service under test (global mock is in setupMocks.js)
vi.unmock('@/services/UserService.js')

import UserService from '@/services/UserService'

describe('UserService', () => {
  let service
  let mockHttp

  beforeEach(() => {
    mockHttp = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    }
    service = new UserService(mockHttp)
  })

  describe('Constructor', () => {
    it('sets http instance and path', () => {
      expect(service.http).toBe(mockHttp)
      expect(service.path).toBe('/users')
    })
  })

  describe('CRUD Operations', () => {
    describe('create', () => {
      it('creates a user with all fields', async () => {
        const userData = {
          username: 'testuser',
          email: 'test@example.com',
          name: 'Test User',
          status: 'Active',
          locale: 'en_US',
          password: 'secret123',
          password_repeat: 'secret123',
        }
        const expectedResponse = { id: '123', ...userData }
        mockHttp.post.mockResolvedValue({ data: expectedResponse })

        const result = await service.create(userData)

        expect(mockHttp.post).toHaveBeenCalledWith('/users/', {
          username: 'testuser',
          email: 'test@example.com',
          name: 'Test User',
          status: 'Active',
          locale: 'en_US',
          password: 'secret123',
          password_repeat: 'secret123',
        })
        expect(result).toEqual(expectedResponse)
      })

      it('passes locale as undefined when not provided', async () => {
        const userData = {
          username: 'testuser',
          email: 'test@example.com',
          name: 'Test User',
          status: 'Active',
        }
        mockHttp.post.mockResolvedValue({ data: {} })

        await service.create(userData)

        expect(mockHttp.post).toHaveBeenCalledWith('/users/', {
          username: 'testuser',
          email: 'test@example.com',
          name: 'Test User',
          status: 'Active',
          locale: undefined,
          password: '',
          password_repeat: '',
        })
      })
    })

    describe('get', () => {
      it('retrieves a user by ID', async () => {
        const expectedUser = { id: '123', name: 'Test User' }
        mockHttp.get.mockResolvedValue({ data: expectedUser })

        const result = await service.get('123')

        expect(mockHttp.get).toHaveBeenCalledWith('/users/123')
        expect(result).toEqual(expectedUser)
      })
    })

    describe('list', () => {
      it('retrieves paginated users with default params', async () => {
        const expectedResponse = {
          pageDetails: { page: 1, perPage: 10 },
          items: [{ id: '1' }, { id: '2' }],
        }
        mockHttp.get.mockResolvedValue({ data: expectedResponse })

        const result = await service.list()

        expect(mockHttp.get).toHaveBeenCalledWith('/users/', {
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

      it('retrieves users with custom params', async () => {
        mockHttp.get.mockResolvedValue({ data: {} })

        await service.list({
          page: 2,
          limit: 25,
          search_field: 'email',
          search_value: '@example.com',
          sort_by: 'createdAt',
          sort_order: 'desc',
        })

        expect(mockHttp.get).toHaveBeenCalledWith('/users/', {
          params: {
            page: 2,
            limit: 25,
            search_field: 'email',
            search_value: '@example.com',
            sort_by: 'createdAt',
            sort_order: 'desc',
          },
        })
      })
    })

    describe('update', () => {
      it('updates a user', async () => {
        const updateData = {
          name: 'Updated Name',
          email: 'updated@example.com',
        }
        mockHttp.put.mockResolvedValue({ data: { id: '123', ...updateData } })

        const result = await service.update('123', updateData)

        expect(mockHttp.put).toHaveBeenCalledWith('/users/123', updateData)
        expect(result).toEqual({ id: '123', ...updateData })
      })
    })

    describe('delete', () => {
      it('deletes a user', async () => {
        mockHttp.delete.mockResolvedValue({ data: { message: 'Deleted' } })

        const result = await service.delete('123')

        expect(mockHttp.delete).toHaveBeenCalledWith('/users/123')
        expect(result).toEqual({ message: 'Deleted' })
      })
    })
  })

  describe('Helper Methods', () => {
    describe('getName', () => {
      it('returns username from user', async () => {
        mockHttp.get.mockResolvedValue({
          data: { id: '123', username: 'testuser' },
        })

        const result = await service.getName('123')

        expect(result).toBe('testuser')
      })

      it('returns empty string when user has no username', async () => {
        mockHttp.get.mockResolvedValue({ data: { id: '123' } })

        const result = await service.getName('123')

        expect(result).toBe('')
      })
    })

    describe('dropdown', () => {
      it('returns formatted dropdown options', async () => {
        mockHttp.get.mockResolvedValue({
          data: {
            items: [
              { id: '1', name: 'User One', username: 'user1' },
              { id: '2', name: 'User Two', username: 'user2' },
            ],
          },
        })

        const result = await service.dropdown()

        expect(result).toEqual([
          { label: 'User One (user1)', value: '1' },
          { label: 'User Two (user2)', value: '2' },
        ])
      })
    })

    describe('search', () => {
      it('searches users by name and formats results', async () => {
        mockHttp.get.mockResolvedValue({
          data: {
            pageDetails: { page: 1, perPage: 25 },
            items: [{ id: '1', name: 'Test User', email: 'test@example.com' }],
          },
        })

        const result = await service.search('Test')

        expect(mockHttp.get).toHaveBeenCalledWith('/users/', {
          params: {
            page: 1,
            limit: 25,
            search_field: 'name',
            search_value: 'Test',
            sort_by: 'name',
            sort_order: 'asc',
          },
        })
        expect(result.items[0].name).toBe('Test User <test@example.com>')
      })
    })

    describe('formatById', () => {
      it('returns formatted name and email', async () => {
        mockHttp.get.mockResolvedValue({
          data: { name: 'Test User', email: 'test@example.com' },
        })

        const result = await service.formatById('123')

        expect(result).toBe('Test User <test@example.com>')
      })
    })

    describe('preload', () => {
      it('returns cleaned user list for lookup', async () => {
        mockHttp.get.mockResolvedValue({
          data: {
            pageDetails: { page: 1, perPage: 200 },
            items: [
              { id: '1', username: 'user1', name: 'User One' },
              { id: '2', name: 'User Two' },
            ],
          },
        })

        const result = await service.preload()

        expect(result.items).toEqual([
          { id: '1', name: 'user1' },
          { id: '2', name: '2' }, // Falls back to ID when no username
        ])
      })
    })
  })

  describe('setPassword', () => {
    it('sets password for another user', async () => {
      mockHttp.post.mockResolvedValue({ data: { message: 'Set' } })

      await service.setPassword('user-123', 'newpass', 'newpass')

      expect(mockHttp.post).toHaveBeenCalledWith('/users/user-123/password', {
        password_new: 'newpass',
        password_new_repeat: 'newpass',
      })
    })
  })

  describe('Role Management', () => {
    describe('getRoles', () => {
      it('retrieves user roles', async () => {
        const roles = [{ key: 'admin', name: 'Admin' }]
        mockHttp.get.mockResolvedValue({ data: roles })

        const result = await service.getRoles('123')

        expect(mockHttp.get).toHaveBeenCalledWith('/users/123/roles')
        expect(result).toEqual(roles)
      })
    })

    describe('addRole', () => {
      it('assigns a role to user', async () => {
        mockHttp.post.mockResolvedValue({ data: { message: 'Added' } })

        await service.addRole('123', 'admin')

        expect(mockHttp.post).toHaveBeenCalledWith('/users/123/roles', {
          roles: [{ key: 'admin' }],
        })
      })
    })

    describe('updateRoles', () => {
      it('updates all user roles', async () => {
        const roles = [{ key: 'admin' }, { key: 'user' }]
        mockHttp.put.mockResolvedValue({ data: { message: 'Updated' } })

        await service.updateRoles('123', roles)

        expect(mockHttp.put).toHaveBeenCalledWith('/users/123/roles', { roles })
      })
    })

    describe('deleteRole', () => {
      it('removes a role from user', async () => {
        mockHttp.get.mockResolvedValue({
          data: { roles: [{ key: 'admin' }, { key: 'user' }] },
        })
        mockHttp.put.mockResolvedValue({ data: { message: 'Updated' } })

        await service.deleteRole('123', 'admin')

        expect(mockHttp.put).toHaveBeenCalledWith('/users/123/roles', {
          roles: [{ key: 'user' }],
        })
      })
    })
  })

  describe('Related Resources', () => {
    describe('getEvents', () => {
      it('retrieves user events with params', async () => {
        mockHttp.get.mockResolvedValue({ data: { items: [] } })

        await service.getEvents('123', { page: 2, limit: 20 })

        expect(mockHttp.get).toHaveBeenCalledWith('/users/123/events', {
          params: {
            page: 2,
            limit: 20,
            search_field: '',
            search_value: '',
            sort_by: 'createdAt',
            sort_order: 'desc',
          },
        })
      })
    })

    describe('getVMs', () => {
      it('retrieves user VMs', async () => {
        mockHttp.get.mockResolvedValue({ data: { items: [] } })

        await service.getVMs('123')

        expect(mockHttp.get).toHaveBeenCalledWith(
          '/users/123/virtual-machines',
          {
            params: expect.objectContaining({ page: 1, limit: 10 }),
          },
        )
      })
    })

    describe('getGuacamoles', () => {
      it('retrieves user guacamole connections', async () => {
        mockHttp.get.mockResolvedValue({ data: { items: [] } })

        await service.getGuacamoles('123')

        expect(mockHttp.get).toHaveBeenCalledWith('/users/123/guacamole', {
          params: expect.objectContaining({ page: 1, limit: 10 }),
        })
      })
    })
  })

  describe('Status Management', () => {
    describe('getStatuses', () => {
      it('retrieves all user statuses', async () => {
        const statuses = [{ name: 'Active' }, { name: 'Inactive' }]
        mockHttp.get.mockResolvedValue({ data: statuses })

        const result = await service.getStatuses()

        expect(mockHttp.get).toHaveBeenCalledWith('/status/user')
        expect(result).toEqual(statuses)
      })
    })

    describe('addStatus', () => {
      it('adds a new status', async () => {
        mockHttp.post.mockResolvedValue({ data: { message: 'Added' } })

        await service.addStatus('Pending')

        expect(mockHttp.post).toHaveBeenCalledWith('/status/user', {
          status: 'Pending',
        })
      })
    })

    describe('deleteStatus', () => {
      it('deletes a status', async () => {
        mockHttp.delete.mockResolvedValue({ data: { message: 'Deleted' } })

        await service.deleteStatus('Pending')

        expect(mockHttp.delete).toHaveBeenCalledWith('/status/user/Pending')
      })
    })
  })

  describe('Delete Preview', () => {
    describe('getDeletePreview', () => {
      it('retrieves delete preview for user', async () => {
        const preview = { guacamoles: [], vms: [] }
        mockHttp.get.mockResolvedValue({ data: preview })

        const result = await service.getDeletePreview('123')

        expect(mockHttp.get).toHaveBeenCalledWith('/users/123/delete-preview')
        expect(result).toEqual(preview)
      })
    })
  })
})
