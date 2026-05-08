import debounce from 'lodash/debounce'
import { computed, ref } from 'vue'

/**
 * Composable for handling autocomplete/lookup functionality in TableSearchBar.
 * Manages async data fetching with debouncing and minimum character requirements.
 *
 * @param {Object} options - Configuration options
 * @param {Ref<Object|null>} options.selectedField - Ref to currently selected field
 * @param {Ref<string>} options.inputValue - Ref to current input value
 * @param {Ref<string>} options.phase - Ref to current search phase
 * @returns {Object} - Lookup state and methods
 */
export function useSearchLookup(options) {
  const { selectedField, inputValue, phase } = options

  // State
  const lookupResults = ref([])
  const lookupLoading = ref(false)

  // Computed: minimum characters for current lookup field
  const lookupMinChars = computed(() => selectedField.value?.minChars ?? 3)

  // Computed: whether to show "min chars" hint for lookup
  const showLookupMinCharsHint = computed(() => {
    if (phase.value !== 'value') return false
    if (selectedField.value?.type !== 'lookup') return false
    return inputValue.value.length < lookupMinChars.value
  })

  // Computed: whether to show "no results" message for lookup
  const showLookupNoResults = computed(() => {
    if (phase.value !== 'value') return false
    if (selectedField.value?.type !== 'lookup') return false
    if (lookupLoading.value) return false
    if (lookupResults.value.length > 0) return false
    return inputValue.value.length >= lookupMinChars.value
  })

  /**
   * Performs lookup search with debouncing.
   * Fetches data from the field's fetchData function.
   */
  const performLookup = debounce(async (query) => {
    if (!selectedField.value?.fetchData) return

    const minChars = selectedField.value.minChars ?? 3
    if (query.length < minChars) {
      lookupResults.value = []
      lookupLoading.value = false
      return
    }

    lookupLoading.value = true
    try {
      const result = await selectedField.value.fetchData(query)
      const labelAttr = selectedField.value.labelAttribute ?? 'name'
      const returnAttr = selectedField.value.returnAttribute ?? 'id'

      lookupResults.value = (result.items || []).map((item) => ({
        key: item[returnAttr],
        label: item[labelAttr],
        raw: item,
      }))
    } catch (error) {
      console.error('[TableSearchBar] Lookup failed:', error)
      lookupResults.value = []
    } finally {
      lookupLoading.value = false
    }
  }, 300)

  /**
   * Resets lookup state.
   */
  function resetLookup() {
    lookupResults.value = []
    lookupLoading.value = false
  }

  return {
    // State
    lookupResults,
    lookupLoading,

    // Computed
    lookupMinChars,
    showLookupMinCharsHint,
    showLookupNoResults,

    // Methods
    performLookup,
    resetLookup,
  }
}
