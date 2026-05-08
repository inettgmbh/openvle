import { ref } from 'vue'

import { executeBatched } from '@/utils/batchedExecution'

/**
 * Composable for batch-adding multiple items via sequential API calls.
 *
 * @param {Object} options - Configuration options.
 * @param {Function} options.execute - Function called per item: (item) => Promise
 * @param {Function} [options.onComplete] - Called when batch finishes: ({ succeeded, failed, skipped, total }) => void
 * @param {Function} [options.isSkippable] - Predicate: (error) => boolean. Skippable errors count as "skipped", not "failed".
 * @param {Function} [options.beginSilent] - Called before batch starts to suppress toasts.
 * @param {Function} [options.endSilent] - Called after batch ends to re-enable toasts.
 * @param {string} [options.idKey='id'] - Key used to identify items for deduplication.
 * @param {number} [options.batchSize=3] - Number of parallel operations per batch.
 * @returns {Object} Reactive state and methods for batch selection and execution.
 */
export function useBatchAdd({
  execute,
  onComplete,
  isSkippable,
  beginSilent,
  endSilent,
  idKey = 'id',
  batchSize = 3,
}) {
  const selectedItems = ref([])
  const phase = ref('selecting')
  const progress = ref({ current: 0, total: 0, errors: [], skipped: 0 })

  function hasItem(id) {
    return selectedItems.value.some((item) => item[idKey] === id)
  }

  function addItem(item) {
    if (hasItem(item[idKey])) return false
    selectedItems.value.push(item)
    return true
  }

  function removeItem(id) {
    selectedItems.value = selectedItems.value.filter(
      (item) => item[idKey] !== id,
    )
  }

  function clearItems() {
    selectedItems.value = []
  }

  async function performSave() {
    const items = [...selectedItems.value]
    phase.value = 'saving'
    progress.value = { current: 0, total: items.length, errors: [], skipped: 0 }

    // Wrap each operation to handle skippable errors
    const operations = items.map((item) => async () => {
      try {
        return await execute(item)
      } catch (error) {
        if (isSkippable?.(error)) {
          return { _skipped: true }
        }
        throw error
      }
    })

    beginSilent?.()
    try {
      const { results, errors } = await executeBatched(operations, {
        batchSize,
        delayMs: 100,
        onProgress: (completed, total) => {
          progress.value.current = completed
          progress.value.total = total
        },
      })

      // Count skipped items from successful results
      const skipped = results.filter((r) => r?._skipped).length

      // Map real errors to include item display names
      progress.value.errors = errors.map(({ index, error }) => ({
        index,
        error,
        itemName: items[index]?._displayName || items[index]?.[idKey] || '',
      }))
      progress.value.skipped = skipped

      const failed = errors.length
      const succeeded = items.length - failed - skipped
      phase.value = failed > 0 ? 'error' : 'done'

      if (onComplete) {
        onComplete({ succeeded, failed, skipped, total: items.length })
      }
    } finally {
      endSilent?.()
    }
  }

  function reset() {
    selectedItems.value = []
    phase.value = 'selecting'
    progress.value = { current: 0, total: 0, errors: [], skipped: 0 }
  }

  return {
    selectedItems,
    phase,
    progress,
    addItem,
    removeItem,
    clearItems,
    hasItem,
    performSave,
    reset,
  }
}
