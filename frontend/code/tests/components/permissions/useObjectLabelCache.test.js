import { beforeEach, describe, expect, it, vi } from 'vitest'

// Create persistent mocks
const mockResolve = vi.fn()

// Mock lookup store
vi.mock('@/stores/lookup', () => ({
  useLookupStore: () => ({
    resolve: mockResolve,
  }),
}))

// Mock dataUtils
vi.mock('@/utils/dataUtils', () => ({
  resolveObjectTypeToFrontendURLs: {
    user: 'users',
    role: 'roles',
    virtualmachine: 'vms',
    guacamoleconnectionprofile: 'connections',
  },
  resolveObjectTypeToGerman: vi.fn((key, opts) => {
    const map = {
      user: 'Benutzer',
      role: 'Rollen',
      application: 'Anwendungen',
    }
    return map[key] || null
  }),
}))

// Mock objectModelPermissions
vi.mock('@/utils/objectModelPermissions', () => ({
  getObjectModelByBackendType: vi.fn(() => null),
}))

import { useObjectLabelCache } from '@/components/permissions/composables/useObjectLabelCache'
import { getObjectModelByBackendType } from '@/utils/objectModelPermissions'

describe('useObjectLabelCache', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockResolve.mockReset()
    mockResolve.mockResolvedValue('Resolved Label')

    // Default: no model found
    getObjectModelByBackendType.mockReturnValue(null)
  })

  function createCache(resolver = null) {
    return useObjectLabelCache(resolver)
  }

  describe('getObjectTypeLabel', () => {
    it('returns model label when available', () => {
      getObjectModelByBackendType.mockReturnValue({ label: 'Benutzer' })

      const { getObjectTypeLabel } = createCache()

      expect(getObjectTypeLabel('User')).toBe('Benutzer')
    })

    it('falls back to German translation', () => {
      const { getObjectTypeLabel } = createCache()

      expect(getObjectTypeLabel('user')).toBe('Benutzer')
    })

    it('returns original key when no translation found', () => {
      const { getObjectTypeLabel } = createCache()

      expect(getObjectTypeLabel('UnknownType')).toBe('UnknownType')
    })

    it('handles null/undefined gracefully', () => {
      const { getObjectTypeLabel } = createCache()

      expect(getObjectTypeLabel(null)).toBe('')
      expect(getObjectTypeLabel(undefined)).toBe('')
    })
  })

  describe('getObjectLabelSync', () => {
    it('returns placeholder when not cached', () => {
      const { getObjectLabelSync } = createCache()

      const label = getObjectLabelSync('User', 'user-123')
      expect(label).toContain('user-123')
      expect(label).toContain('…')
    })

    it('includes objectType label in placeholder', () => {
      getObjectModelByBackendType.mockReturnValue({ label: 'Benutzer' })

      const { getObjectLabelSync } = createCache()

      const label = getObjectLabelSync('User', 'user-12345678-abcd')
      expect(label).toContain('Benutzer')
      expect(label).toContain('user-123') // First 8 chars
    })

    it('converts objectType and objectId to strings', () => {
      const { getObjectLabelSync } = createCache()

      // Should not throw
      const label = getObjectLabelSync(123, 456)
      expect(typeof label).toBe('string')
    })
  })

  describe('prefetchObjectLabel', () => {
    it('uses objectLabelResolver when provided', async () => {
      const customResolver = vi.fn(() => Promise.resolve('Custom Label'))

      const { getObjectLabelSync, prefetchObjectLabel } =
        createCache(customResolver)

      await prefetchObjectLabel('User', 'user-123')

      expect(customResolver).toHaveBeenCalledWith('User', 'user-123')
      expect(getObjectLabelSync('User', 'user-123')).toBe('Custom Label')
    })

    it('sets placeholder immediately before async resolution', () => {
      const customResolver = vi.fn(
        () => new Promise((resolve) => setTimeout(() => resolve('Final'), 100)),
      )

      const { getObjectLabelSync, prefetchObjectLabel } =
        createCache(customResolver)

      // Start prefetch but don't await
      prefetchObjectLabel('User', 'user-123')

      // Should have placeholder immediately
      const label = getObjectLabelSync('User', 'user-123')
      expect(label).toContain('…')
    })

    it('does not call lookup store when no keyspace available', async () => {
      // No model, no keyspace mapping
      getObjectModelByBackendType.mockReturnValue({ keyspace: null })

      const { prefetchObjectLabel } = createCache()

      await prefetchObjectLabel('UnknownType', 'id-123')

      expect(mockResolve).not.toHaveBeenCalled()
    })

    it('uses custom resolver and updates cache', async () => {
      const customResolver = vi.fn(() => Promise.resolve('From Resolver'))

      const { getObjectLabelSync, prefetchObjectLabel } =
        createCache(customResolver)

      await prefetchObjectLabel('User', 'user-1')

      expect(getObjectLabelSync('User', 'user-1')).toBe('From Resolver')
    })

    it('does not refetch if already cached via resolver', async () => {
      const customResolver = vi.fn(() => Promise.resolve('Label'))

      const { prefetchObjectLabel } = createCache(customResolver)

      await prefetchObjectLabel('User', 'user-123')
      await prefetchObjectLabel('User', 'user-123')

      // Should only call once
      expect(customResolver).toHaveBeenCalledTimes(1)
    })

    it('deduplicates in-flight requests with resolver', async () => {
      let resolveCount = 0
      const customResolver = vi.fn(
        () =>
          new Promise((resolve) => {
            resolveCount++
            setTimeout(() => resolve('Label'), 10)
          }),
      )

      const { prefetchObjectLabel } = createCache(customResolver)

      // Start multiple requests simultaneously
      const p1 = prefetchObjectLabel('User', 'user-123')
      const p2 = prefetchObjectLabel('User', 'user-123')
      const p3 = prefetchObjectLabel('User', 'user-123')

      await Promise.all([p1, p2, p3])

      // Should only have one actual request
      expect(resolveCount).toBe(1)
    })

    it('maintains separate cache per objectType with resolver', async () => {
      const customResolver = vi.fn((ot, id) => Promise.resolve(`${ot}:${id}`))

      const { getObjectLabelSync, prefetchObjectLabel } =
        createCache(customResolver)

      await prefetchObjectLabel('User', 'id-1')
      await prefetchObjectLabel('Role', 'id-1')

      expect(getObjectLabelSync('User', 'id-1')).toBe('User:id-1')
      expect(getObjectLabelSync('Role', 'id-1')).toBe('Role:id-1')
    })

    it('maintains separate cache per objectId with resolver', async () => {
      const customResolver = vi.fn((ot, id) => Promise.resolve(`Label:${id}`))

      const { getObjectLabelSync, prefetchObjectLabel } =
        createCache(customResolver)

      await prefetchObjectLabel('User', 'id-1')
      await prefetchObjectLabel('User', 'id-2')

      expect(getObjectLabelSync('User', 'id-1')).toBe('Label:id-1')
      expect(getObjectLabelSync('User', 'id-2')).toBe('Label:id-2')
    })
  })

  describe('Lookup Store Integration', () => {
    it('uses model keyspace when available', async () => {
      getObjectModelByBackendType.mockReturnValue({
        keyspace: 'customKeyspace',
      })
      mockResolve.mockResolvedValue('From Custom Keyspace')

      const { getObjectLabelSync, prefetchObjectLabel } = createCache()

      await prefetchObjectLabel('User', 'user-123')

      expect(mockResolve).toHaveBeenCalledWith('customKeyspace', 'user-123')
      expect(getObjectLabelSync('User', 'user-123')).toBe(
        'From Custom Keyspace',
      )
    })

    it('populates cache from lookup store when model has keyspace', async () => {
      getObjectModelByBackendType.mockReturnValue({ keyspace: 'users' })
      mockResolve.mockResolvedValue('John Doe')

      const { getObjectLabelSync, prefetchObjectLabel } = createCache()

      await prefetchObjectLabel('User', 'user-123')

      expect(getObjectLabelSync('User', 'user-123')).toBe('John Doe')
    })

    it('falls back to lookup store when resolver returns null', async () => {
      getObjectModelByBackendType.mockReturnValue({ keyspace: 'users' })
      mockResolve.mockResolvedValue('From Lookup')
      const customResolver = vi.fn(() => Promise.resolve(null))

      const { getObjectLabelSync, prefetchObjectLabel } =
        createCache(customResolver)

      await prefetchObjectLabel('User', 'user-123')

      expect(customResolver).toHaveBeenCalled()
      expect(mockResolve).toHaveBeenCalled()
      expect(getObjectLabelSync('User', 'user-123')).toBe('From Lookup')
    })
  })

  describe('Type Coercion', () => {
    it('converts all inputs to strings', async () => {
      const customResolver = vi.fn(() => Promise.resolve('Label'))

      const { getObjectLabelSync, prefetchObjectLabel } =
        createCache(customResolver)

      // Numbers should be converted
      await prefetchObjectLabel(123, 456)

      const label = getObjectLabelSync(123, 456)
      expect(typeof label).toBe('string')
      expect(label).toBe('Label')
    })
  })
})
