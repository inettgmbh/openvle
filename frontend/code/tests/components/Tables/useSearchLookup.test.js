import { flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'

import { useSearchLookup } from '@/components/Tables/composables/useSearchLookup'

// Mock lodash debounce to execute immediately
vi.mock('lodash/debounce', () => ({
  default: (fn) => fn,
}))

describe('useSearchLookup', () => {
  let options
  let lookup

  const mockLookupField = {
    type: 'lookup',
    fetchData: vi.fn(),
    labelAttribute: 'name',
    returnAttribute: 'id',
    minChars: 3,
  }

  beforeEach(() => {
    vi.clearAllMocks()

    options = {
      selectedField: ref(null),
      inputValue: ref(''),
      phase: ref('idle'),
    }

    lookup = useSearchLookup(options)
  })

  // ============================================================
  // Initial State
  // ============================================================

  describe('Initial State', () => {
    it('starts with empty lookup results', () => {
      expect(lookup.lookupResults.value).toEqual([])
    })

    it('starts with loading false', () => {
      expect(lookup.lookupLoading.value).toBe(false)
    })

    it('has default minChars of 3', () => {
      expect(lookup.lookupMinChars.value).toBe(3)
    })
  })

  // ============================================================
  // Min Chars Hint
  // ============================================================

  describe('Min Chars Hint', () => {
    it('shows hint when in value phase with lookup field and too few chars', () => {
      options.phase.value = 'value'
      options.selectedField.value = mockLookupField
      options.inputValue.value = 'ab'

      expect(lookup.showLookupMinCharsHint.value).toBe(true)
    })

    it('hides hint when enough chars', () => {
      options.phase.value = 'value'
      options.selectedField.value = mockLookupField
      options.inputValue.value = 'abc'

      expect(lookup.showLookupMinCharsHint.value).toBe(false)
    })

    it('hides hint when not in value phase', () => {
      options.phase.value = 'field'
      options.selectedField.value = mockLookupField
      options.inputValue.value = 'ab'

      expect(lookup.showLookupMinCharsHint.value).toBe(false)
    })

    it('hides hint when not a lookup field', () => {
      options.phase.value = 'value'
      options.selectedField.value = { type: 'text' }
      options.inputValue.value = 'ab'

      expect(lookup.showLookupMinCharsHint.value).toBe(false)
    })

    it('respects custom minChars from field', () => {
      options.selectedField.value = { ...mockLookupField, minChars: 5 }

      expect(lookup.lookupMinChars.value).toBe(5)
    })
  })

  // ============================================================
  // No Results State
  // ============================================================

  describe('No Results State', () => {
    it('shows no results when lookup returns empty', async () => {
      options.phase.value = 'value'
      options.selectedField.value = mockLookupField
      options.inputValue.value = 'xyz'
      mockLookupField.fetchData.mockResolvedValue({ items: [] })

      await lookup.performLookup('xyz')
      await flushPromises()

      expect(lookup.showLookupNoResults.value).toBe(true)
    })

    it('hides no results when loading', async () => {
      options.phase.value = 'value'
      options.selectedField.value = mockLookupField
      options.inputValue.value = 'xyz'

      // Simulate loading state
      lookup.lookupLoading.value = true

      expect(lookup.showLookupNoResults.value).toBe(false)
    })

    it('hides no results when there are results', async () => {
      options.phase.value = 'value'
      options.selectedField.value = mockLookupField
      options.inputValue.value = 'xyz'
      mockLookupField.fetchData.mockResolvedValue({
        items: [{ id: '1', name: 'Test' }],
      })

      await lookup.performLookup('xyz')
      await flushPromises()

      expect(lookup.showLookupNoResults.value).toBe(false)
    })

    it('hides no results when input is too short', () => {
      options.phase.value = 'value'
      options.selectedField.value = mockLookupField
      options.inputValue.value = 'xy'

      expect(lookup.showLookupNoResults.value).toBe(false)
    })
  })

  // ============================================================
  // Perform Lookup
  // ============================================================

  describe('Perform Lookup', () => {
    it('does not perform lookup if no fetchData', async () => {
      options.selectedField.value = { type: 'lookup' }

      await lookup.performLookup('test')

      expect(lookup.lookupResults.value).toEqual([])
    })

    it('does not perform lookup if query too short', async () => {
      options.selectedField.value = mockLookupField

      await lookup.performLookup('ab')

      expect(mockLookupField.fetchData).not.toHaveBeenCalled()
    })

    it('performs lookup and transforms results', async () => {
      options.selectedField.value = mockLookupField
      mockLookupField.fetchData.mockResolvedValue({
        items: [
          { id: 'uuid-1', name: 'Test User 1' },
          { id: 'uuid-2', name: 'Test User 2' },
        ],
      })

      await lookup.performLookup('test')
      await flushPromises()

      expect(mockLookupField.fetchData).toHaveBeenCalledWith('test')
      expect(lookup.lookupResults.value).toEqual([
        {
          key: 'uuid-1',
          label: 'Test User 1',
          raw: { id: 'uuid-1', name: 'Test User 1' },
        },
        {
          key: 'uuid-2',
          label: 'Test User 2',
          raw: { id: 'uuid-2', name: 'Test User 2' },
        },
      ])
    })

    it('uses custom label and return attributes', async () => {
      options.selectedField.value = {
        ...mockLookupField,
        labelAttribute: 'displayName',
        returnAttribute: 'code',
      }
      mockLookupField.fetchData.mockResolvedValue({
        items: [{ code: 'ABC', displayName: 'Item ABC' }],
      })

      await lookup.performLookup('test')
      await flushPromises()

      expect(lookup.lookupResults.value[0].key).toBe('ABC')
      expect(lookup.lookupResults.value[0].label).toBe('Item ABC')
    })

    it('handles lookup errors gracefully', async () => {
      options.selectedField.value = mockLookupField
      mockLookupField.fetchData.mockRejectedValue(new Error('Network error'))
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      await lookup.performLookup('test')
      await flushPromises()

      expect(lookup.lookupResults.value).toEqual([])
      expect(consoleSpy).toHaveBeenCalled()
      consoleSpy.mockRestore()
    })

    it('handles empty items array', async () => {
      options.selectedField.value = mockLookupField
      mockLookupField.fetchData.mockResolvedValue({ items: [] })

      await lookup.performLookup('test')
      await flushPromises()

      expect(lookup.lookupResults.value).toEqual([])
    })

    it('handles missing items property', async () => {
      options.selectedField.value = mockLookupField
      mockLookupField.fetchData.mockResolvedValue({})

      await lookup.performLookup('test')
      await flushPromises()

      expect(lookup.lookupResults.value).toEqual([])
    })
  })

  // ============================================================
  // Reset
  // ============================================================

  describe('Reset', () => {
    it('resets lookup state', async () => {
      options.selectedField.value = mockLookupField
      mockLookupField.fetchData.mockResolvedValue({
        items: [{ id: '1', name: 'Test' }],
      })

      await lookup.performLookup('test')
      await flushPromises()

      expect(lookup.lookupResults.value.length).toBe(1)

      lookup.resetLookup()

      expect(lookup.lookupResults.value).toEqual([])
      expect(lookup.lookupLoading.value).toBe(false)
    })
  })
})
