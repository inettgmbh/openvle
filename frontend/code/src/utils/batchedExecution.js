/**
 * Executes an array of async operations in batches with delay between batches.
 *
 * @param {Array<Function>} operations - Array of functions that return Promises
 * @param {Object} options - Configuration options
 * @param {number} [options.batchSize=3] - Number of operations per batch
 * @param {number} [options.delayMs=100] - Delay between batches in milliseconds
 * @param {Function} [options.onProgress] - Callback called after each batch: (completed, total) => void
 * @returns {Promise<{results: Array, errors: Array<{index: number, error: Error}>}>}
 */
export async function executeBatched(operations, options = {}) {
  const { batchSize = 3, delayMs = 100, onProgress } = options

  const results = []
  const errors = []
  let completed = 0

  for (let i = 0; i < operations.length; i += batchSize) {
    const batch = operations.slice(i, i + batchSize)

    const batchResults = await Promise.allSettled(batch.map((op) => op()))

    batchResults.forEach((result, batchIndex) => {
      const globalIndex = i + batchIndex
      if (result.status === 'fulfilled') {
        results[globalIndex] = result.value
      } else {
        errors.push({ index: globalIndex, error: result.reason })
        results[globalIndex] = null
      }
    })

    completed += batch.length
    if (onProgress) {
      onProgress(completed, operations.length)
    }

    // Delay before next batch (skip delay after last batch)
    if (i + batchSize < operations.length) {
      await delay(delayMs)
    }
  }

  return { results, errors }
}

/**
 * Helper to create a delay promise.
 *
 * @param {number} ms - Milliseconds to delay
 * @returns {Promise<void>}
 */
export function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
