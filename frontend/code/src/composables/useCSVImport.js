import Papa from 'papaparse'
import { computed, ref } from 'vue'

import backend from '@/services'
import { CSV_ROW_STATUS } from '@/utils/csvImportStatus'

const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024 // 5 MB

/**
 * Composable that encapsulates CSV import logic.
 *
 * @param {Object} options
 * @param {Array<{key: string, label: string}>} options.requiredMappings
 * @param {Function} options.onImportConfirm  - Called per row, should return a promise.
 * @param {Function} [options.onFinish]       - Called once when the full import is done.
 * @param {number|null} [options.limit]       - Max allowed row count.
 * @returns {Object} Reactive state, computed properties, and methods.
 */
export function useCSVImport({
  requiredMappings,
  onImportConfirm,
  onFinish = null,
  limit = null,
} = {}) {
  // ── State ──────────────────────────────────────────────
  const allowRetry = ref(false)
  const csvHeaders = ref([])
  const fileName = ref('')
  const fileSize = ref(0)
  const hasImportStarted = ref(false)
  const headerMapping = ref({})
  const isImporting = ref(false)
  const limitExceeded = ref(false)
  const noFile = ref(true)
  const parseError = ref('')
  const parsedRowCount = ref(0)
  const rawRows = ref([])
  const rowError = ref([])
  const rowStatus = ref([])

  // ── Helpers ────────────────────────────────────────────
  function delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }

  // ── Computed ───────────────────────────────────────────
  const canConfirm = computed(() =>
    requiredMappings.every((m) => !!headerMapping.value[m.key]),
  )

  const hasDuplicateMappings = computed(() => {
    const assigned = Object.values(headerMapping.value).filter(Boolean)
    return new Set(assigned).size !== assigned.length
  })

  const successCount = computed(
    () => rowStatus.value.filter((s) => s === CSV_ROW_STATUS.SUCCESS).length,
  )

  const failedCount = computed(
    () => rowStatus.value.filter((s) => s === CSV_ROW_STATUS.FAILED).length,
  )

  const remainingCount = computed(
    () => rowStatus.value.filter((s) => s === CSV_ROW_STATUS.PENDING).length,
  )

  const importingCount = computed(
    () => rowStatus.value.filter((s) => s === CSV_ROW_STATUS.IMPORTING).length,
  )

  const totalCount = computed(() => rowStatus.value.length)

  const isImportFinished = computed(
    () =>
      totalCount.value > 0 &&
      successCount.value + failedCount.value === totalCount.value,
  )

  const progressPercent = computed(() => {
    if (totalCount.value === 0) return 0
    return Math.round(
      ((successCount.value + failedCount.value) / totalCount.value) * 100,
    )
  })

  /**
   * Derives the current wizard step from the state:
   *  1 = file upload
   *  2 = column mapping
   *  3 = preview & import
   *  4 = result
   */
  const currentStep = computed(() => {
    if (isImportFinished.value) return 4
    if (hasImportStarted.value) return 3
    if (rawRows.value.length > 0 && !limitExceeded.value) return 2
    return 1
  })

  // ── Methods ────────────────────────────────────────────

  /**
   * Validates and parses a CSV file.
   *
   * @param {File} file - The File object from a file input or drag-and-drop.
   * @returns {Promise<boolean>} Resolves to true on success, false on validation/parse failure.
   */
  function parseFile(file) {
    return new Promise((resolve) => {
      // Reset previous errors
      parseError.value = ''
      limitExceeded.value = false

      if (!file) {
        noFile.value = true
        resolve(false)
        return
      }

      // Validate extension
      if (!file.name.toLowerCase().endsWith('.csv')) {
        parseError.value =
          'Ungültiges Dateiformat. Bitte eine .csv-Datei auswählen.'
        resolve(false)
        return
      }

      // Validate size
      if (file.size > MAX_FILE_SIZE_BYTES) {
        parseError.value =
          `Die Datei ist zu groß (${(file.size / 1024 / 1024).toFixed(1)} MB). ` +
          `Maximal erlaubt sind 5 MB.`
        resolve(false)
        return
      }

      noFile.value = false
      fileName.value = file.name
      fileSize.value = file.size

      Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          if (results.errors && results.errors.length > 0) {
            parseError.value = `CSV-Parsing-Fehler: ${results.errors[0].message}`
            resolve(false)
            return
          }

          parsedRowCount.value = results.data.length
          limitExceeded.value = limit !== null && results.data.length > limit

          if (limitExceeded.value) {
            rawRows.value = []
            csvHeaders.value = []
            headerMapping.value = {}
            rowStatus.value = []
            rowError.value = []
            resolve(false)
            return
          }

          rawRows.value = results.data
          csvHeaders.value = results.meta.fields || []
          headerMapping.value = Object.fromEntries(
            requiredMappings.map((m) => [m.key, '']),
          )
          rowStatus.value = Array(results.data.length).fill(
            CSV_ROW_STATUS.PENDING,
          )
          rowError.value = Array(results.data.length).fill('')
          hasImportStarted.value = false
          allowRetry.value = false
          resolve(true)
        },
        error: (err) => {
          parseError.value = `CSV konnte nicht gelesen werden: ${err.message}`
          resolve(false)
        },
      })
    })
  }

  /**
   * Starts the import (or retries only failed rows).
   *
   * @param {boolean} [retryOnly=false] - When true, only re-imports failed rows.
   */
  async function confirmImport(retryOnly = false) {
    isImporting.value = true
    hasImportStarted.value = true
    allowRetry.value = false

    const mappedRows = rawRows.value.map((row, index) => {
      const mapped = {}
      for (const m of requiredMappings) {
        mapped[m.key] = row[headerMapping.value[m.key]]
      }
      return { mapped, index }
    })

    const targets = retryOnly
      ? mappedRows.filter(
          ({ index }) => rowStatus.value[index] === CSV_ROW_STATUS.FAILED,
        )
      : mappedRows

    if (retryOnly) {
      for (const { index } of targets) {
        rowStatus.value[index] = CSV_ROW_STATUS.PENDING
        rowError.value[index] = ''
      }
    }

    // Suppress per-row error toasts — errors are shown in the table instead
    backend.beginSilent()
    try {
      for (const { mapped, index } of targets) {
        rowStatus.value[index] = CSV_ROW_STATUS.IMPORTING
        rowError.value[index] = ''
        await delay(100)

        try {
          await onImportConfirm(mapped, index)
          rowStatus.value[index] = CSV_ROW_STATUS.SUCCESS
        } catch (e) {
          rowStatus.value[index] = CSV_ROW_STATUS.FAILED
          rowError.value[index] =
            e?.response?.data?.message ||
            e?.response?.data?.detail ||
            e?.message ||
            'Unbekannter Fehler'
        }

        await delay(500)
      }
    } finally {
      backend.endSilent()
    }

    isImporting.value = false

    if (failedCount.value > 0) {
      allowRetry.value = true
    }

    if (onFinish) {
      await onFinish()
    }
  }

  /**
   * Resets all state back to initial values.
   */
  function reset() {
    rawRows.value = []
    csvHeaders.value = []
    headerMapping.value = {}
    rowStatus.value = []
    rowError.value = []
    hasImportStarted.value = false
    allowRetry.value = false
    isImporting.value = false
    limitExceeded.value = false
    parsedRowCount.value = 0
    parseError.value = ''
    fileName.value = ''
    fileSize.value = 0
    noFile.value = true
  }

  return {
    // State
    allowRetry,
    csvHeaders,
    fileName,
    fileSize,
    hasImportStarted,
    headerMapping,
    isImporting,
    limitExceeded,
    noFile,
    parseError,
    parsedRowCount,
    rawRows,
    rowError,
    rowStatus,

    // Computed
    canConfirm,
    currentStep,
    failedCount,
    hasDuplicateMappings,
    importingCount,
    isImportFinished,
    progressPercent,
    remainingCount,
    successCount,
    totalCount,

    // Methods
    confirmImport,
    parseFile,
    reset,
  }
}
