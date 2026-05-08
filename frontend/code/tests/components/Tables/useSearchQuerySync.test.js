import { flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'

import { useSearchQuerySync } from '@/components/Tables/composables/useSearchQuerySync'
import { SearchOperators } from '@/components/Tables/searchOperators'

// Mock vue-router
const mockRoute = { query: {} }
const mockRouter = { replace: vi.fn() }

vi.mock('vue-router', () => ({
  useRoute: () => mockRoute,
  useRouter: () => mockRouter,
}))

describe('useSearchQuerySync', () => {
  let options
  let querySync

  const mockFields = [
    {
      key: 'name',
      label: 'Name',
      operators: SearchOperators.TEXT,
      icon: 'name-icon',
    },
    {
      key: 'status',
      label: 'Status',
      operators: SearchOperators.EQUALS_ONLY,
      options: [
        { value: 'active', label: 'Aktiv' },
        { value: 'inactive', label: 'Inaktiv' },
      ],
    },
    {
      key: 'createdAt',
      label: 'Created',
      type: 'date',
      operators: SearchOperators.DATE,
      icon: 'date-icon',
    },
    {
      key: 'userId',
      label: 'User',
      type: 'lookup',
      operators: SearchOperators.EQUALS_ONLY,
      fetchSelected: vi.fn(),
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    mockRoute.query = {}

    options = {
      activeFilters: ref([]),
      getResolvedFields: () => mockFields,
      syncQuery: true,
      queryKey: 'filter',
      initialFilters: [],
      onFiltersRestored: vi.fn(),
    }

    querySync = useSearchQuerySync(options)
  })

  // ============================================================
  // filtersToQuery
  // ============================================================

  describe('filtersToQuery', () => {
    it('converts single filter to query string', () => {
      const filters = [{ field: 'name', operator: 'eq', value: 'test' }]

      const result = querySync.filtersToQuery(filters)

      expect(result).toBe('name:eq:test')
    })

    it('converts multiple filters to query string', () => {
      const filters = [
        { field: 'name', operator: 'eq', value: 'test' },
        { field: 'status', operator: 'eq', value: 'active' },
      ]

      const result = querySync.filtersToQuery(filters)

      expect(result).toBe('name:eq:test;status:eq:active')
    })

    it('handles empty filters array', () => {
      const result = querySync.filtersToQuery([])

      expect(result).toBe('')
    })

    it('handles value containing colons', () => {
      const filters = [{ field: 'time', operator: 'eq', value: '10:30:00' }]

      const result = querySync.filtersToQuery(filters)

      expect(result).toBe('time:eq:10:30:00')
    })
  })

  // ============================================================
  // queryToFilters
  // ============================================================

  describe('queryToFilters', () => {
    it('parses single filter from query string', () => {
      const result = querySync.queryToFilters('name:eq:test')

      expect(result).toEqual([{ field: 'name', operator: 'eq', value: 'test' }])
    })

    it('parses multiple filters from query string', () => {
      const result = querySync.queryToFilters('name:eq:test;status:eq:active')

      expect(result).toEqual([
        { field: 'name', operator: 'eq', value: 'test' },
        { field: 'status', operator: 'eq', value: 'active' },
      ])
    })

    it('returns empty array for null/undefined', () => {
      expect(querySync.queryToFilters(null)).toEqual([])
      expect(querySync.queryToFilters(undefined)).toEqual([])
      expect(querySync.queryToFilters('')).toEqual([])
    })

    it('handles value containing colons', () => {
      const result = querySync.queryToFilters('time:eq:10:30:00')

      expect(result).toEqual([
        { field: 'time', operator: 'eq', value: '10:30:00' },
      ])
    })
  })

  // ============================================================
  // syncFiltersToQuery
  // ============================================================

  describe('syncFiltersToQuery', () => {
    it('updates URL query when filters change', async () => {
      options.activeFilters.value = [
        {
          field: 'name',
          operator: 'eq',
          value: 'test',
        },
      ]

      await querySync.syncFiltersToQuery()

      expect(mockRouter.replace).toHaveBeenCalledWith({
        query: { filter: 'name:eq:test' },
      })
    })

    it('removes query key when no filters', async () => {
      mockRoute.query = { filter: 'name:eq:old' }
      options.activeFilters.value = []

      await querySync.syncFiltersToQuery()

      expect(mockRouter.replace).toHaveBeenCalledWith({ query: {} })
    })

    it('does not update when syncQuery is false', async () => {
      options.syncQuery = false
      querySync = useSearchQuerySync(options)
      options.activeFilters.value = [
        { field: 'name', operator: 'eq', value: 'test' },
      ]

      await querySync.syncFiltersToQuery()

      expect(mockRouter.replace).not.toHaveBeenCalled()
    })

    it('does not update when query is unchanged', async () => {
      mockRoute.query = { filter: 'name:eq:test' }
      options.activeFilters.value = [
        { field: 'name', operator: 'eq', value: 'test' },
      ]

      await querySync.syncFiltersToQuery()

      expect(mockRouter.replace).not.toHaveBeenCalled()
    })

    it('uses custom queryKey', async () => {
      options.queryKey = 'search'
      querySync = useSearchQuerySync(options)
      options.activeFilters.value = [
        { field: 'name', operator: 'eq', value: 'test' },
      ]

      await querySync.syncFiltersToQuery()

      expect(mockRouter.replace).toHaveBeenCalledWith({
        query: { search: 'name:eq:test' },
      })
    })

    it('preserves existing query params', async () => {
      mockRoute.query = { page: '2', other: 'param' }
      options.activeFilters.value = [
        { field: 'name', operator: 'eq', value: 'test' },
      ]

      await querySync.syncFiltersToQuery()

      expect(mockRouter.replace).toHaveBeenCalledWith({
        query: { page: '2', other: 'param', filter: 'name:eq:test' },
      })
    })
  })

  // ============================================================
  // initializeFilters
  // ============================================================

  describe('initializeFilters', () => {
    it('initializes from query params', async () => {
      mockRoute.query = { filter: 'name:eq:test' }

      await querySync.initializeFilters()

      expect(options.activeFilters.value.length).toBe(1)
      expect(options.activeFilters.value[0].field).toBe('name')
      expect(options.activeFilters.value[0].value).toBe('test')
      expect(options.activeFilters.value[0].fieldLabel).toBe('Name')
      expect(options.onFiltersRestored).toHaveBeenCalled()
    })

    it('initializes from initialFilters prop when no query params', async () => {
      options.initialFilters = [
        { field: 'name', operator: 'eq', value: 'from-prop' },
      ]
      querySync = useSearchQuerySync(options)

      await querySync.initializeFilters()

      expect(options.activeFilters.value.length).toBe(1)
      expect(options.activeFilters.value[0].value).toBe('from-prop')
    })

    it('query params take precedence over initialFilters', async () => {
      mockRoute.query = { filter: 'name:eq:from-query' }
      options.initialFilters = [
        { field: 'name', operator: 'eq', value: 'from-prop' },
      ]
      querySync = useSearchQuerySync(options)

      await querySync.initializeFilters()

      expect(options.activeFilters.value[0].value).toBe('from-query')
    })

    it('skips invalid field keys', async () => {
      mockRoute.query = { filter: 'invalid:eq:test' }

      await querySync.initializeFilters()

      expect(options.activeFilters.value.length).toBe(0)
    })

    it('skips invalid operator keys', async () => {
      mockRoute.query = { filter: 'name:invalid:test' }

      await querySync.initializeFilters()

      expect(options.activeFilters.value.length).toBe(0)
    })

    it('resolves display value for options fields', async () => {
      mockRoute.query = { filter: 'status:eq:active' }

      await querySync.initializeFilters()

      expect(options.activeFilters.value[0].displayValue).toBe('Aktiv')
    })

    it('formats date display value', async () => {
      mockRoute.query = { filter: 'createdAt:eq:2025-01-15' }

      await querySync.initializeFilters()

      // German date format
      expect(options.activeFilters.value[0].displayValue).toContain('15')
      expect(options.activeFilters.value[0].displayValue).toContain('2025')
    })

    it('fetches display value for lookup fields', async () => {
      mockRoute.query = { filter: 'userId:eq:uuid-123' }
      mockFields[3].fetchSelected.mockResolvedValue('Max Mustermann')

      await querySync.initializeFilters()
      await flushPromises()

      expect(mockFields[3].fetchSelected).toHaveBeenCalledWith('uuid-123')
      expect(options.activeFilters.value[0].displayValue).toBe('Max Mustermann')
    })

    it('handles lookup fetch errors gracefully', async () => {
      mockRoute.query = { filter: 'userId:eq:uuid-123' }
      mockFields[3].fetchSelected.mockRejectedValue(new Error('Network error'))
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      await querySync.initializeFilters()
      await flushPromises()

      // Should still create filter with original value as displayValue
      expect(options.activeFilters.value[0].displayValue).toBe('uuid-123')
      expect(consoleSpy).toHaveBeenCalled()
      consoleSpy.mockRestore()
    })

    it('does not emit event when no initial data', async () => {
      await querySync.initializeFilters()

      expect(options.activeFilters.value.length).toBe(0)
      // No emit when no filters — views call initialFetch() directly instead
      expect(options.onFiltersRestored).not.toHaveBeenCalled()
    })

    it('sets isFreetext correctly', async () => {
      mockRoute.query = { filter: 'name:eq:test' }

      await querySync.initializeFilters()

      // Text field without options should be freetext
      expect(options.activeFilters.value[0].isFreetext).toBe(true)
    })

    it('sets isFreetext false for options fields', async () => {
      mockRoute.query = { filter: 'status:eq:active' }

      await querySync.initializeFilters()

      expect(options.activeFilters.value[0].isFreetext).toBe(false)
    })
  })

  // ============================================================
  // Query Watcher
  // ============================================================

  describe('Query Watcher', () => {
    it('sets up watcher that can be called', () => {
      // Just verify the function exists and can be called
      expect(() => querySync.setupQueryWatcher()).not.toThrow()
    })
  })
})
