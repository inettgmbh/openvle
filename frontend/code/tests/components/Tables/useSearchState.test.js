import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick, ref } from 'vue'

import { useSearchState } from '@/components/Tables/composables/useSearchState'
import { SearchOperators } from '@/components/Tables/searchOperators'

describe('useSearchState', () => {
  let options
  let state
  let inputEl

  const mockField = {
    key: 'name',
    label: 'Name',
    operators: SearchOperators.TEXT,
    icon: 'icon-path',
  }

  const mockDateField = {
    key: 'createdAt',
    label: 'Created',
    type: 'date',
    operators: SearchOperators.DATE,
    icon: 'date-icon',
  }

  const mockSingleOpField = {
    key: 'status',
    label: 'Status',
    operators: [SearchOperators.ALL.eq],
  }

  beforeEach(() => {
    inputEl = { value: { focus: vi.fn() } }

    options = {
      getResolvedFields: () => [mockField],
      activeFilters: ref([]),
      canAddMore: ref(true),
      maxFilters: 10,
      inputEl: inputEl,
      onFilterAdded: vi.fn(),
      resetLookup: vi.fn(),
    }

    state = useSearchState(options)
  })

  // ============================================================
  // Initial State
  // ============================================================

  describe('Initial State', () => {
    it('starts in idle phase', () => {
      expect(state.phase.value).toBe('idle')
    })

    it('has no selected field', () => {
      expect(state.selectedField.value).toBeNull()
    })

    it('has no selected operator', () => {
      expect(state.selectedOperator.value).toBeNull()
    })

    it('has empty input value', () => {
      expect(state.inputValue.value).toBe('')
    })

    it('has highlighted index at -1', () => {
      expect(state.highlightedIndex.value).toBe(-1)
    })
  })

  // ============================================================
  // Phase Transitions
  // ============================================================

  describe('Phase Transitions', () => {
    it('enters field phase', async () => {
      state.enterFieldPhase()
      await nextTick()

      expect(state.phase.value).toBe('field')
      expect(state.inputValue.value).toBe('')
      expect(state.highlightedIndex.value).toBe(-1)
      expect(inputEl.value.focus).toHaveBeenCalled()
    })

    it('selects field and transitions to operator phase', async () => {
      state.selectField(mockField)
      await nextTick()

      expect(state.selectedField.value).toStrictEqual(mockField)
      expect(state.phase.value).toBe('operator')
      expect(state.inputValue.value).toBe('')
      expect(inputEl.value.focus).toHaveBeenCalled()
    })

    it('auto-skips operator phase when only one operator', async () => {
      state.selectField(mockSingleOpField)
      await nextTick()

      expect(state.phase.value).toBe('value')
      expect(state.selectedOperator.value).toStrictEqual(
        mockSingleOpField.operators[0],
      )
    })

    it('selects operator and transitions to value phase', async () => {
      state.selectField(mockField)
      state.selectOperator(SearchOperators.ALL.eq)
      await nextTick()

      expect(state.selectedOperator.value).toStrictEqual(SearchOperators.ALL.eq)
      expect(state.phase.value).toBe('value')
      expect(options.resetLookup).toHaveBeenCalled()
    })

    it('adds filter immediately for empty operator', () => {
      state.selectField(mockField)
      state.selectOperator(SearchOperators.ALL.empty)

      expect(options.activeFilters.value.length).toBe(1)
      expect(options.activeFilters.value[0].operator).toBe('empty')
      expect(options.onFilterAdded).toHaveBeenCalled()
    })

    it('adds filter immediately for nempty operator', () => {
      state.selectField(mockField)
      state.selectOperator(SearchOperators.ALL.nempty)

      expect(options.activeFilters.value.length).toBe(1)
      expect(options.activeFilters.value[0].operator).toBe('nempty')
    })
  })

  // ============================================================
  // Date/Time Handling
  // ============================================================

  describe('Date/Time Handling', () => {
    it('detects date/time field correctly', () => {
      state.selectField(mockDateField)

      expect(state.isDateTimeField.value).toBe(true)
    })

    it('returns correct input type for date field', () => {
      state.selectField(mockDateField)

      expect(state.dateTimeInputType.value).toBe('date')
    })

    it('returns datetime-local for datetime field', () => {
      const datetimeField = { ...mockDateField, type: 'datetime' }
      state.selectField(datetimeField)

      expect(state.dateTimeInputType.value).toBe('datetime-local')
    })

    it('returns time for time field', () => {
      const timeField = { ...mockDateField, type: 'time' }
      state.selectField(timeField)

      expect(state.dateTimeInputType.value).toBe('time')
    })

    it('pre-fills date/time fields with current value', () => {
      state.selectField(mockDateField)
      state.selectOperator(SearchOperators.ALL.eq)

      // Should be pre-filled with today's date in YYYY-MM-DD format
      expect(state.inputValue.value).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    })

    it('confirms date/time value', () => {
      state.selectField(mockDateField)
      state.selectOperator(SearchOperators.ALL.eq)
      state.inputValue.value = '2025-01-15'

      state.confirmDateTime()

      expect(options.activeFilters.value.length).toBe(1)
      expect(options.activeFilters.value[0].value).toBe('2025-01-15')
    })

    it('appends seconds for datetime values', () => {
      const datetimeField = { ...mockDateField, type: 'datetime' }
      state.selectField(datetimeField)
      state.selectOperator(SearchOperators.ALL.eq)
      state.inputValue.value = '2025-01-15T10:30'

      state.confirmDateTime()

      expect(options.activeFilters.value[0].value).toBe('2025-01-15T10:30:00')
    })

    it('does not confirm empty datetime value', () => {
      state.selectField(mockDateField)
      state.selectOperator(SearchOperators.ALL.eq)
      state.inputValue.value = ''

      state.confirmDateTime()

      expect(options.activeFilters.value.length).toBe(0)
    })
  })

  // ============================================================
  // Freetext Value
  // ============================================================

  describe('Freetext Value', () => {
    it('confirms freetext value', () => {
      state.selectField(mockField)
      state.selectOperator(SearchOperators.ALL.eq)
      state.inputValue.value = 'test value'

      state.confirmFreetext()

      expect(options.activeFilters.value.length).toBe(1)
      expect(options.activeFilters.value[0].value).toBe('test value')
      expect(options.activeFilters.value[0].isFreetext).toBe(true)
    })

    it('trims whitespace from freetext value', () => {
      state.selectField(mockField)
      state.selectOperator(SearchOperators.ALL.eq)
      state.inputValue.value = '  trimmed  '

      state.confirmFreetext()

      expect(options.activeFilters.value[0].value).toBe('trimmed')
    })

    it('does not confirm empty freetext value', () => {
      state.selectField(mockField)
      state.selectOperator(SearchOperators.ALL.eq)
      state.inputValue.value = '   '

      state.confirmFreetext()

      expect(options.activeFilters.value.length).toBe(0)
    })
  })

  // ============================================================
  // Adding Filters
  // ============================================================

  describe('Adding Filters', () => {
    it('adds filter with correct structure', () => {
      state.selectField(mockField)
      state.selectOperator(SearchOperators.ALL.eq)
      state.inputValue.value = 'test'

      state.confirmFreetext()

      const filter = options.activeFilters.value[0]
      expect(filter.field).toBe('name')
      expect(filter.fieldLabel).toBe('Name')
      expect(filter.fieldIcon).toBe('icon-path')
      expect(filter.operator).toBe('eq')
      expect(filter.operatorLabel).toBe('ist gleich')
      expect(filter.value).toBe('test')
      expect(filter.displayValue).toBe('test')
    })

    it('replaces filter in single-filter mode', () => {
      options.maxFilters = 1
      state = useSearchState(options)

      // Add first filter
      state.selectField(mockField)
      state.selectOperator(SearchOperators.ALL.eq)
      state.inputValue.value = 'first'
      state.confirmFreetext()

      expect(options.activeFilters.value.length).toBe(1)

      // Add second filter (should replace)
      state.selectField(mockField)
      state.selectOperator(SearchOperators.ALL.eq)
      state.inputValue.value = 'second'
      state.confirmFreetext()

      expect(options.activeFilters.value.length).toBe(1)
      expect(options.activeFilters.value[0].value).toBe('second')
    })

    it('replaces existing filter for same field in multi-filter mode', () => {
      state.selectField(mockField)
      state.selectOperator(SearchOperators.ALL.eq)
      state.inputValue.value = 'first'
      state.confirmFreetext()

      // Add filter for same field (should replace)
      state.selectField(mockField)
      state.selectOperator(SearchOperators.ALL.neq)
      state.inputValue.value = 'second'
      state.confirmFreetext()

      expect(options.activeFilters.value.length).toBe(1)
      expect(options.activeFilters.value[0].operator).toBe('neq')
      expect(options.activeFilters.value[0].value).toBe('second')
    })

    it('re-enters field phase after adding filter when more allowed', async () => {
      options.canAddMore = ref(true)
      state = useSearchState(options)

      state.selectField(mockField)
      state.selectOperator(SearchOperators.ALL.eq)
      state.inputValue.value = 'test'
      state.confirmFreetext()

      await nextTick()

      expect(state.phase.value).toBe('field')
    })

    it('goes to idle after adding filter in single-filter mode', () => {
      options.maxFilters = 1
      state = useSearchState(options)

      state.selectField(mockField)
      state.selectOperator(SearchOperators.ALL.eq)
      state.inputValue.value = 'test'
      state.confirmFreetext()

      expect(state.phase.value).toBe('idle')
    })

    it('calls onFilterAdded callback', () => {
      state.selectField(mockField)
      state.selectOperator(SearchOperators.ALL.eq)
      state.inputValue.value = 'test'
      state.confirmFreetext()

      expect(options.onFilterAdded).toHaveBeenCalled()
    })
  })

  // ============================================================
  // Going Back
  // ============================================================

  describe('Going Back', () => {
    it('goes back from value to operator phase', () => {
      state.selectField(mockField)
      state.selectOperator(SearchOperators.ALL.eq)

      expect(state.phase.value).toBe('value')

      state.goBackOnePhase()

      expect(state.phase.value).toBe('operator')
      expect(state.selectedOperator.value).toBeNull()
    })

    it('goes back from value to field phase when operator was auto-skipped', () => {
      state.selectField(mockSingleOpField)

      expect(state.phase.value).toBe('value')

      state.goBackOnePhase()

      expect(state.phase.value).toBe('field')
      expect(state.selectedField.value).toBeNull()
      expect(state.selectedOperator.value).toBeNull()
    })

    it('goes back from operator to field phase', () => {
      state.selectField(mockField)

      expect(state.phase.value).toBe('operator')

      state.goBackOnePhase()

      expect(state.phase.value).toBe('field')
      expect(state.selectedField.value).toBeNull()
    })
  })

  // ============================================================
  // Reset
  // ============================================================

  describe('Reset', () => {
    it('resets all state to initial', () => {
      state.selectField(mockField)
      state.selectOperator(SearchOperators.ALL.eq)
      state.inputValue.value = 'test'
      state.highlightedIndex.value = 5

      state.resetInput()

      expect(state.phase.value).toBe('idle')
      expect(state.selectedField.value).toBeNull()
      expect(state.selectedOperator.value).toBeNull()
      expect(state.inputValue.value).toBe('')
      expect(state.highlightedIndex.value).toBe(-1)
    })

    it('calls resetLookup on reset', () => {
      state.resetInput()

      expect(options.resetLookup).toHaveBeenCalled()
    })
  })

  // ============================================================
  // Select Value
  // ============================================================

  describe('Select Value', () => {
    it('adds filter with value and display value', () => {
      state.selectField(mockField)
      state.selectOperator(SearchOperators.ALL.eq)

      state.selectValue('uuid-123', 'Display Name')

      expect(options.activeFilters.value.length).toBe(1)
      expect(options.activeFilters.value[0].value).toBe('uuid-123')
      expect(options.activeFilters.value[0].displayValue).toBe('Display Name')
    })
  })
})
