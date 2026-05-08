import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'

import { usePaginationChild } from '@/utils/pagination'

describe('usePaginationChild', () => {
  let fetchUsers
  let fetchVMs

  beforeEach(() => {
    fetchUsers = vi.fn()
    fetchVMs = vi.fn()
  })

  function createChild(overrides = {}) {
    return usePaginationChild({
      children: [
        {
          name: 'users',
          perPage: 10,
          currentPage: 1,
          sortColumnKey: 'name',
          sortDirection: 'asc',
          fetchData: fetchUsers,
        },
        {
          name: 'vms',
          perPage: 10,
          currentPage: 1,
          sortColumnKey: 'name',
          sortDirection: 'asc',
          fetchData: fetchVMs,
        },
      ],
      fetchArgs: () => ['entity-123'],
      ...overrides,
    })
  }

  describe('refreshActiveTab', () => {
    it('does nothing when no tab has been activated', () => {
      const { refreshActiveTab } = createChild()

      refreshActiveTab()

      expect(fetchUsers).not.toHaveBeenCalled()
      expect(fetchVMs).not.toHaveBeenCalled()
    })

    it('refreshes the active tab after it has been loaded', async () => {
      const { handleTabChanged, refreshActiveTab } = createChild()

      await handleTabChanged('users')
      fetchUsers.mockClear()

      refreshActiveTab()

      expect(fetchUsers).toHaveBeenCalledWith('entity-123')
      expect(fetchVMs).not.toHaveBeenCalled()
    })

    it('refreshes the correct tab after switching tabs', async () => {
      const { handleTabChanged, refreshActiveTab } = createChild()

      await handleTabChanged('users')
      await handleTabChanged('vms')
      fetchUsers.mockClear()
      fetchVMs.mockClear()

      refreshActiveTab()

      expect(fetchVMs).toHaveBeenCalledWith('entity-123')
      expect(fetchUsers).not.toHaveBeenCalled()
    })

    it('does not refresh a tab that has not been loaded yet', async () => {
      const { handleTabChanged, refreshActiveTab, loadedTabs } = createChild()

      // Manually set activeTab by calling handleTabChanged for 'users'
      await handleTabChanged('users')
      fetchUsers.mockClear()

      // Simulate switching to a tab without fetchData (won't be in loadedTabs via normal flow)
      // But activeTab is tracked internally, so switch to 'vms'
      await handleTabChanged('vms')
      fetchVMs.mockClear()

      // Remove 'vms' from loadedTabs to simulate unloaded state
      loadedTabs.delete('vms')

      refreshActiveTab()

      expect(fetchVMs).not.toHaveBeenCalled()
    })

    it('does nothing for a tab without fetchData', async () => {
      const { handleTabChanged, refreshActiveTab } = usePaginationChild({
        children: [
          { name: 'overview' },
          { name: 'users', fetchData: fetchUsers },
        ],
        fetchArgs: () => [],
      })

      // Switch to tab without fetchData
      await handleTabChanged('overview')

      refreshActiveTab()

      expect(fetchUsers).not.toHaveBeenCalled()
    })
  })

  describe('handleTabChanged', () => {
    it('tracks active tab on first visit', async () => {
      const { handleTabChanged, loadedTabs } = createChild()

      await handleTabChanged('users')

      expect(fetchUsers).toHaveBeenCalledWith('entity-123')
      expect(loadedTabs.has('users')).toBe(true)
    })

    it('does not re-fetch on revisit', async () => {
      const { handleTabChanged } = createChild()

      await handleTabChanged('users')
      fetchUsers.mockClear()

      await handleTabChanged('users')

      expect(fetchUsers).not.toHaveBeenCalled()
    })

    it('skips initial fetch when URL has filter for tab with search', async () => {
      const { handleTabChanged } = usePaginationChild({
        children: [
          {
            name: 'users',
            perPage: 10,
            currentPage: 1,
            sortColumnKey: 'name',
            sortDirection: 'asc',
            searchField: null,
            searchValue: null,
            fetchData: fetchUsers,
          },
        ],
        fetchArgs: () => ['entity-123'],
        route: { query: { 'filter-users': 'name:contains:test' } },
      })

      await handleTabChanged('users')

      expect(fetchUsers).not.toHaveBeenCalled()
    })

    it('fetches normally when URL has no filter for tab with search', async () => {
      const { handleTabChanged } = usePaginationChild({
        children: [
          {
            name: 'users',
            perPage: 10,
            currentPage: 1,
            sortColumnKey: 'name',
            sortDirection: 'asc',
            searchField: null,
            searchValue: null,
            fetchData: fetchUsers,
          },
        ],
        fetchArgs: () => ['entity-123'],
        route: { query: {} },
      })

      await handleTabChanged('users')

      expect(fetchUsers).toHaveBeenCalledWith('entity-123')
    })

    it('fetches normally when tab has no searchField property', async () => {
      const { handleTabChanged } = usePaginationChild({
        children: [
          {
            name: 'users',
            perPage: 10,
            currentPage: 1,
            sortColumnKey: 'name',
            sortDirection: 'asc',
            fetchData: fetchUsers,
          },
        ],
        fetchArgs: () => ['entity-123'],
        route: { query: { 'filter-users': 'name:contains:test' } },
      })

      await handleTabChanged('users')

      expect(fetchUsers).toHaveBeenCalledWith('entity-123')
    })

    it('fetches normally when no route is provided', async () => {
      const { handleTabChanged } = usePaginationChild({
        children: [
          {
            name: 'users',
            perPage: 10,
            currentPage: 1,
            sortColumnKey: 'name',
            sortDirection: 'asc',
            searchField: null,
            searchValue: null,
            fetchData: fetchUsers,
          },
        ],
        fetchArgs: () => ['entity-123'],
      })

      await handleTabChanged('users')

      expect(fetchUsers).toHaveBeenCalledWith('entity-123')
    })

    it('uses custom searchBarQueryKey when provided', async () => {
      const { handleTabChanged } = usePaginationChild({
        children: [
          {
            name: 'users',
            perPage: 10,
            currentPage: 1,
            sortColumnKey: 'name',
            sortDirection: 'asc',
            searchField: null,
            searchValue: null,
            searchBarQueryKey: 'custom-key',
            fetchData: fetchUsers,
          },
        ],
        fetchArgs: () => ['entity-123'],
        route: { query: { 'custom-key': 'name:eq:test' } },
      })

      await handleTabChanged('users')

      expect(fetchUsers).not.toHaveBeenCalled()
    })

    it('skips fetch only for tab with matching URL filter', async () => {
      const { handleTabChanged } = usePaginationChild({
        children: [
          {
            name: 'users',
            perPage: 10,
            currentPage: 1,
            sortColumnKey: 'name',
            sortDirection: 'asc',
            searchField: null,
            searchValue: null,
            fetchData: fetchUsers,
          },
          {
            name: 'vms',
            perPage: 10,
            currentPage: 1,
            sortColumnKey: 'name',
            sortDirection: 'asc',
            searchField: null,
            searchValue: null,
            fetchData: fetchVMs,
          },
        ],
        fetchArgs: () => ['entity-123'],
        route: { query: { 'filter-users': 'name:contains:test' } },
      })

      await handleTabChanged('users')
      await handleTabChanged('vms')

      expect(fetchUsers).not.toHaveBeenCalled()
      expect(fetchVMs).toHaveBeenCalledWith('entity-123')
    })
  })

  describe('handleSearch', () => {
    it('updates searchField and searchValue on child component', () => {
      const { handleSearch, childComponents } = usePaginationChild({
        children: [
          {
            name: 'users',
            perPage: 10,
            currentPage: 1,
            sortColumnKey: 'name',
            sortDirection: 'asc',
            searchField: null,
            searchValue: null,
            fetchData: fetchUsers,
          },
        ],
        fetchArgs: () => ['entity-123'],
      })

      handleSearch({ field: 'name', value: 'test', objectModel: 'users' })

      const usersChild = childComponents.value.find((c) => c.name === 'users')
      expect(usersChild.searchField).toBe('name')
      expect(usersChild.searchValue).toBe('test')
    })

    it('resets currentPage to 1 on search', () => {
      const { handleSearch, childComponents } = usePaginationChild({
        children: [
          {
            name: 'users',
            perPage: 10,
            currentPage: 3,
            sortColumnKey: 'name',
            sortDirection: 'asc',
            searchField: null,
            searchValue: null,
            fetchData: fetchUsers,
          },
        ],
        fetchArgs: () => ['entity-123'],
      })

      handleSearch({ field: 'name', value: 'test', objectModel: 'users' })

      const usersChild = childComponents.value.find((c) => c.name === 'users')
      expect(usersChild.currentPage).toBe(1)
    })

    it('triggers fetch after updating search state', () => {
      const { handleSearch } = usePaginationChild({
        children: [
          {
            name: 'users',
            perPage: 10,
            currentPage: 1,
            sortColumnKey: 'name',
            sortDirection: 'asc',
            searchField: null,
            searchValue: null,
            fetchData: fetchUsers,
          },
        ],
        fetchArgs: () => ['entity-123'],
      })

      handleSearch({ field: 'name', value: 'test', objectModel: 'users' })

      expect(fetchUsers).toHaveBeenCalledWith('entity-123')
    })

    it('uses objectModel to identify the correct child', () => {
      const { handleSearch, childComponents } = usePaginationChild({
        children: [
          {
            name: 'users',
            perPage: 10,
            currentPage: 1,
            sortColumnKey: 'name',
            sortDirection: 'asc',
            searchField: null,
            searchValue: null,
            fetchData: fetchUsers,
          },
          {
            name: 'vms',
            perPage: 10,
            currentPage: 1,
            sortColumnKey: 'name',
            sortDirection: 'asc',
            searchField: null,
            searchValue: null,
            fetchData: fetchVMs,
          },
        ],
        fetchArgs: () => ['entity-123'],
      })

      handleSearch({ field: 'status', value: 'running', objectModel: 'vms' })

      const usersChild = childComponents.value.find((c) => c.name === 'users')
      const vmsChild = childComponents.value.find((c) => c.name === 'vms')

      expect(usersChild.searchField).toBeNull()
      expect(vmsChild.searchField).toBe('status')
      expect(vmsChild.searchValue).toBe('running')
      expect(fetchVMs).toHaveBeenCalledWith('entity-123')
      expect(fetchUsers).not.toHaveBeenCalled()
    })

    it('clears search when empty field and value', () => {
      const { handleSearch, childComponents } = usePaginationChild({
        children: [
          {
            name: 'users',
            perPage: 10,
            currentPage: 2,
            sortColumnKey: 'name',
            sortDirection: 'asc',
            searchField: 'name',
            searchValue: 'test',
            fetchData: fetchUsers,
          },
        ],
        fetchArgs: () => ['entity-123'],
      })

      handleSearch({ field: '', value: '', objectModel: 'users' })

      const usersChild = childComponents.value.find((c) => c.name === 'users')
      expect(usersChild.searchField).toBe('')
      expect(usersChild.searchValue).toBe('')
      expect(usersChild.currentPage).toBe(1)
      expect(fetchUsers).toHaveBeenCalled()
    })

    it('does not crash for unknown objectModel', () => {
      const { handleSearch } = createChild()

      expect(() => {
        handleSearch({
          field: 'name',
          value: 'test',
          objectModel: 'unknown',
        })
      }).not.toThrow()
    })
  })

  describe('handlePaginationChanged', () => {
    it('updates page and perPage for the correct child', () => {
      const { handlePaginationChanged, childComponents } = createChild()

      // Same perPage (10) — page should update to 2
      handlePaginationChanged(2, 10, 'users')

      const usersChild = childComponents.value.find((c) => c.name === 'users')
      expect(usersChild.currentPage).toBe(2)
      expect(usersChild.perPage).toBe(10)
      expect(fetchUsers).toHaveBeenCalledWith('entity-123')
    })

    it('resets to page 1 when perPage changes', () => {
      const { handlePaginationChanged, childComponents } = createChild()

      handlePaginationChanged(3, 10, 'users')
      handlePaginationChanged(3, 25, 'users')

      const usersChild = childComponents.value.find((c) => c.name === 'users')
      expect(usersChild.currentPage).toBe(1)
    })

    it('does not affect other children', () => {
      const { handlePaginationChanged, childComponents } = createChild()

      handlePaginationChanged(5, 50, 'users')

      const vmsChild = childComponents.value.find((c) => c.name === 'vms')
      expect(vmsChild.currentPage).toBe(1)
      expect(vmsChild.perPage).toBe(10)
    })
  })

  describe('handleSortOrderChanged', () => {
    it('updates sort column and direction for the correct child', () => {
      const { handleSortOrderChanged, childComponents } = createChild()

      handleSortOrderChanged('desc', 'email', 'users')

      const usersChild = childComponents.value.find((c) => c.name === 'users')
      expect(usersChild.sortColumnKey).toBe('email')
      expect(usersChild.sortDirection).toBe('desc')
      expect(fetchUsers).toHaveBeenCalledWith('entity-123')
    })

    it('does not affect other children', () => {
      const { handleSortOrderChanged, childComponents } = createChild()

      handleSortOrderChanged('desc', 'email', 'users')

      const vmsChild = childComponents.value.find((c) => c.name === 'vms')
      expect(vmsChild.sortColumnKey).toBe('name')
      expect(vmsChild.sortDirection).toBe('asc')
    })
  })

  describe('handleDeleteObject', () => {
    it('stores object and opens the correct modal', () => {
      const objToRemove = ref({})
      const modals = { deleteUsers: ref(false) }

      const { handleDeleteObject } = usePaginationChild({
        children: [{ name: 'users', fetchData: fetchUsers }],
        modals,
        objToRemove,
      })

      const obj = { id: '123', name: 'Test User' }
      handleDeleteObject(obj, 'users')

      expect(objToRemove.value).toEqual(obj)
      expect(modals.deleteUsers.value).toBe(true)
    })

    it('does not crash when modal does not exist', () => {
      const objToRemove = ref({})
      const modals = {}

      const { handleDeleteObject } = usePaginationChild({
        children: [{ name: 'users', fetchData: fetchUsers }],
        modals,
        objToRemove,
      })

      expect(() => {
        handleDeleteObject({ id: '123' }, 'unknown')
      }).not.toThrow()
    })
  })
})
