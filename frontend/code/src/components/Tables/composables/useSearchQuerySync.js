import { watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  DATE_TIME_TYPES,
  DEFAULT_FIELD_ICON,
} from '@/components/Tables/searchFieldPresets'

/**
 * Formats a date/time value for display in the filter chip.
 * Duplicated here to avoid circular dependencies.
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
      return value
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
 * Composable for synchronizing search filters with URL query parameters.
 * Handles bidirectional sync: filters -> URL and URL -> filters.
 *
 * @param {Object} options - Configuration options
 * @param {Ref<Array>} options.activeFilters - Ref to active filters array
 * @param {Function} options.getResolvedFields - Function returning resolved field definitions
 * @param {boolean} options.syncQuery - Whether to sync with URL query params
 * @param {string} options.queryKey - Query parameter key (default: 'filter')
 * @param {Array} options.initialFilters - Initial filters from props
 * @param {Function} options.onFiltersRestored - Callback when filters are restored from URL/props
 * @returns {Object} - Query sync methods
 */
export function useSearchQuerySync(options) {
  const {
    activeFilters,
    getResolvedFields,
    syncQuery,
    queryKey,
    initialFilters,
    onFiltersRestored,
  } = options

  const route = useRoute()
  const router = useRouter()

  // Generation counter to discard stale results from superseded initializeFilters calls
  let initGeneration = 0

  /**
   * Converts filters array to URL query string format.
   *
   * @param {Array} filters - Array of filter objects
   * @returns {string} - Semicolon-separated filter string
   */
  function filtersToQuery(filters) {
    return filters.map((f) => `${f.field}:${f.operator}:${f.value}`).join(';')
  }

  /**
   * Parses URL query string to filters array.
   *
   * @param {string} queryValue - The query string value
   * @returns {Array} - Array of partial filter objects
   */
  function queryToFilters(queryValue) {
    if (!queryValue) return []
    return queryValue.split(';').map((part) => {
      const [field, operator, ...valueParts] = part.split(':')
      return { field, operator, value: valueParts.join(':') }
    })
  }

  /**
   * Syncs current filters to URL query params.
   */
  async function syncFiltersToQuery() {
    if (!syncQuery) return

    const filterString = filtersToQuery(
      activeFilters.value.map((f) => ({
        field: f.field,
        operator: f.operator,
        value: f.value,
      })),
    )

    const newQuery = { ...route.query }
    if (filterString) {
      newQuery[queryKey] = filterString
    } else {
      delete newQuery[queryKey]
    }

    // Only update if changed
    if (route.query[queryKey] !== newQuery[queryKey]) {
      await router.replace({ query: newQuery })
    }
  }

  /**
   * Initializes filters from query params or initialFilters prop.
   * Query params take precedence over initialFilters.
   * Emits filtersChanged immediately, then fetches display names for lookup fields.
   */
  async function initializeFilters() {
    // Determine initial filters: query params take precedence over prop
    let initialData = initialFilters || []

    if (syncQuery && route.query[queryKey]) {
      initialData = queryToFilters(route.query[queryKey])
    }

    if (!initialData?.length) {
      // No filters to restore — let the view trigger the initial fetch directly
      return
    }

    const resolvedFields = getResolvedFields()
    const filters = []
    const lookupUpdates = [] // Track lookup fields that need async display name fetch

    for (const initial of initialData) {
      const field = resolvedFields.find((f) => f.key === initial.field)
      if (!field) continue

      const operatorDef = (field.operators || []).find(
        (op) => op.key === initial.operator,
      )
      if (!operatorDef) continue

      let displayValue = initial.value

      // For lookup fields, use value as initial displayValue and fetch name async later
      if (field.type === 'lookup' && initial.value && field.fetchSelected) {
        lookupUpdates.push({
          field,
          value: initial.value,
          filterIndex: filters.length,
        })
      } else if (field.options) {
        // For options fields, find the label
        const opt = field.options.find((o) => o.value === initial.value)
        if (opt) displayValue = opt.label
      } else if (DATE_TIME_TYPES.includes(field.type)) {
        // For date/time fields, format the display value
        displayValue = formatDateTimeDisplay(initial.value, field.type)
      }

      const isFreetext =
        !field.options &&
        field.type !== 'lookup' &&
        !DATE_TIME_TYPES.includes(field.type)

      filters.push({
        field: field.key,
        fieldLabel: field.label,
        fieldIcon: field.icon || DEFAULT_FIELD_ICON,
        operator: operatorDef.key,
        operatorLabel: operatorDef.label,
        operatorIcon: operatorDef.icon || null,
        value: initial.value,
        displayValue,
        isFreetext,
        suffix: field.suffix || null,
      })
    }

    if (filters.length) {
      const currentGeneration = ++initGeneration

      // Set filters and emit event immediately (synchronously)
      activeFilters.value = filters
      onFiltersRestored?.()

      // Fetch display names for lookup fields in parallel
      if (lookupUpdates.length) {
        const results = await Promise.allSettled(
          lookupUpdates.map((update) =>
            update.field.fetchSelected(update.value),
          ),
        )

        // Discard results if a newer initializeFilters call has started
        if (currentGeneration !== initGeneration) return

        results.forEach((result, i) => {
          const update = lookupUpdates[i]
          if (result.status === 'fulfilled') {
            if (activeFilters.value[update.filterIndex]) {
              activeFilters.value[update.filterIndex].displayValue =
                result.value
            }
          } else {
            console.error(
              `[TableSearchBar] Failed to fetch display value for ${update.field.key}:`,
              result.reason,
            )
          }
        })
      }
    }
  }

  /**
   * Sets up watcher for query param changes (browser back/forward).
   */
  function setupQueryWatcher() {
    watch(
      () => route.query[queryKey],
      (newValue, oldValue) => {
        if (!syncQuery) return
        if (newValue === oldValue) return

        // Avoid re-initializing if we just updated the query ourselves
        const currentFilterString = filtersToQuery(
          activeFilters.value.map((f) => ({
            field: f.field,
            operator: f.operator,
            value: f.value,
          })),
        )
        if ((newValue || '') === currentFilterString) return

        // Re-initialize from new query value
        initializeFilters()
      },
    )
  }

  return {
    filtersToQuery,
    queryToFilters,
    syncFiltersToQuery,
    initializeFilters,
    setupQueryWatcher,
  }
}
