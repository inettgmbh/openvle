import { computed, nextTick, ref } from 'vue'

import {
  DATE_TIME_TYPES,
  DEFAULT_FIELD_ICON,
} from '@/components/Tables/searchFieldPresets'

/**
 * Generates a default value for date/time fields based on current time.
 *
 * @param {string} type - The field type ('date', 'time', or 'datetime')
 * @returns {string} - Formatted date/time string
 */
function getDefaultDateTimeValue(type) {
  const now = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  const date = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
  const time = `${pad(now.getHours())}:${pad(now.getMinutes())}`

  if (type === 'date') return date
  if (type === 'time') return time
  if (type === 'datetime') return `${date}T${time}`
  return ''
}

/**
 * Formats a date/time value for display in the filter chip.
 *
 * @param {string} value - The raw date/time value
 * @param {string} type - The field type ('date', 'time', or 'datetime')
 * @returns {string} - Human-readable formatted string
 */
function formatDateTimeDisplay(value, type) {
  if (!value) return ''
  try {
    if (type === 'date') {
      return new Date(value).toLocaleDateString('de-DE')
    }
    if (type === 'time') {
      return value // Already in HH:mm format
    }
    if (type === 'datetime') {
      const date = new Date(value)
      return `${date.toLocaleDateString('de-DE')} ${date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}`
    }
  } catch {
    return value
  }
  return value
}

/**
 * State machine composable for TableSearchBar.
 * Manages the search input phases: idle -> field -> operator -> value.
 *
 * @param {Object} options - Configuration options
 * @param {Function} options.getResolvedFields - Function returning resolved field definitions
 * @param {Ref<Array>} options.activeFilters - Ref to active filters array
 * @param {Ref<boolean>} options.canAddMore - Computed ref indicating if more filters can be added
 * @param {number} options.maxFilters - Maximum number of filters allowed
 * @param {Ref<HTMLElement>} options.inputEl - Ref to the input element
 * @param {Function} options.onFilterAdded - Callback when a filter is added
 * @param {Function} options.resetLookup - Function to reset lookup state
 * @returns {Object} - State and methods for search state management
 */
export function useSearchState(options) {
  const {
    getResolvedFields,
    activeFilters,
    canAddMore,
    maxFilters,
    inputEl,
    onFilterAdded,
    resetLookup,
  } = options

  // State
  const phase = ref('idle')
  const selectedField = ref(null)
  const selectedOperator = ref(null)
  const inputValue = ref('')
  const highlightedIndex = ref(-1)

  // Computed: whether current field is a date/time picker field
  const isDateTimeField = computed(() =>
    DATE_TIME_TYPES.includes(selectedField.value?.type),
  )

  // Computed: HTML input type for date/time fields
  const dateTimeInputType = computed(() => {
    const type = selectedField.value?.type
    if (type === 'datetime') return 'datetime-local'
    if (type === 'date' || type === 'time') return type
    return 'text'
  })

  /**
   * Resets all input state to idle.
   */
  function resetInput() {
    phase.value = 'idle'
    selectedField.value = null
    selectedOperator.value = null
    inputValue.value = ''
    highlightedIndex.value = -1
    resetLookup?.()
  }

  /**
   * Enters the field selection phase.
   */
  function enterFieldPhase() {
    phase.value = 'field'
    inputValue.value = ''
    highlightedIndex.value = -1
    nextTick(() => inputEl.value?.focus())
  }

  /**
   * Selects a field and transitions to operator or value phase.
   *
   * @param {Object} field - The selected field definition
   */
  function selectField(field) {
    selectedField.value = field
    inputValue.value = ''
    highlightedIndex.value = -1

    // Auto-skip operator if only one
    if (field.operators.length === 1) {
      selectedOperator.value = field.operators[0]
      phase.value = 'value'
    } else {
      phase.value = 'operator'
    }
    nextTick(() => inputEl.value?.focus())
  }

  /**
   * Selects an operator and transitions to value phase (or adds filter for empty/nempty).
   *
   * @param {Object} operator - The selected operator definition
   */
  function selectOperator(operator) {
    selectedOperator.value = operator
    inputValue.value = ''
    highlightedIndex.value = -1
    resetLookup?.()

    // Empty/nempty operators don't require a value - add filter immediately
    if (operator.key === 'empty' || operator.key === 'nempty') {
      addFilter('', '')
      return
    }

    // Pre-fill date/time fields with current date/time
    if (DATE_TIME_TYPES.includes(selectedField.value?.type)) {
      inputValue.value = getDefaultDateTimeValue(selectedField.value.type)
    }

    phase.value = 'value'
    nextTick(() => inputEl.value?.focus())
  }

  /**
   * Confirms a freetext value input and adds the filter.
   */
  function confirmFreetext() {
    const val = inputValue.value.trim()
    if (!val) return
    addFilter(val, val)
  }

  /**
   * Confirms a date/time picker value and adds the filter.
   */
  function confirmDateTime() {
    let val = inputValue.value
    if (!val) return

    // Append seconds for datetime if not present (datetime-local returns YYYY-MM-DDTHH:mm)
    if (selectedField.value.type === 'datetime' && val.length === 16) {
      val = `${val}:00`
    }

    const displayValue = formatDateTimeDisplay(val, selectedField.value.type)
    addFilter(val, displayValue)
  }

  /**
   * Adds a filter with the given value.
   *
   * @param {string} value - The filter value
   * @param {string} displayValue - The display value for the chip
   */
  function addFilter(value, displayValue) {
    // Freetext if field has no options, is not a lookup, and is not a date/time field
    const isFreetext =
      !selectedField.value.options &&
      selectedField.value.type !== 'lookup' &&
      !DATE_TIME_TYPES.includes(selectedField.value.type)

    const filter = {
      field: selectedField.value.key,
      fieldLabel: selectedField.value.label,
      fieldIcon: selectedField.value.icon || DEFAULT_FIELD_ICON,
      operator: selectedOperator.value.key,
      operatorLabel: selectedOperator.value.label,
      operatorIcon: selectedOperator.value.icon || null,
      value,
      displayValue,
      isFreetext,
      suffix: selectedField.value.suffix || null,
    }

    if (maxFilters === 1) {
      // Single filter mode: replace all
      activeFilters.value = [filter]
    } else {
      // Multi filter: replace existing for same field, or append
      const idx = activeFilters.value.findIndex((f) => f.field === filter.field)
      if (idx >= 0) {
        activeFilters.value.splice(idx, 1, filter)
      } else {
        activeFilters.value.push(filter)
      }
    }

    // Notify parent
    onFilterAdded?.()

    // Reset selection state, then re-enter field phase if more filters allowed
    selectedField.value = null
    selectedOperator.value = null
    inputValue.value = ''
    highlightedIndex.value = -1

    if (maxFilters !== 1 && canAddMore.value) {
      phase.value = 'field'
      nextTick(() => inputEl.value?.focus())
    } else {
      phase.value = 'idle'
    }
  }

  /**
   * Selects a value from dropdown (options or lookup).
   *
   * @param {string} value - The value to select
   * @param {string} displayValue - The display value for the chip
   */
  function selectValue(value, displayValue) {
    addFilter(value, displayValue)
  }

  /**
   * Goes back one phase (value -> operator -> field).
   * Called on Backspace when input is empty.
   */
  function goBackOnePhase() {
    if (phase.value === 'value') {
      // Step back to operator (or field if auto-skipped)
      if (selectedField.value?.operators.length === 1) {
        selectedOperator.value = null
        selectedField.value = null
        phase.value = 'field'
      } else {
        selectedOperator.value = null
        phase.value = 'operator'
      }
      highlightedIndex.value = -1
    } else if (phase.value === 'operator') {
      selectedField.value = null
      phase.value = 'field'
      highlightedIndex.value = -1
    }
  }

  return {
    // State
    phase,
    selectedField,
    selectedOperator,
    inputValue,
    highlightedIndex,

    // Computed
    isDateTimeField,
    dateTimeInputType,

    // Methods
    resetInput,
    enterFieldPhase,
    selectField,
    selectOperator,
    confirmFreetext,
    confirmDateTime,
    addFilter,
    selectValue,
    goBackOnePhase,
  }
}
