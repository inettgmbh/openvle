import {
  mdiAlertCircle,
  mdiCheckCircle,
  mdiClockOutline,
  mdiLoading,
} from '@mdi/js'

/**
 * Row-level status values used during CSV import.
 */
export const CSV_ROW_STATUS = Object.freeze({
  PENDING: 'pending',
  IMPORTING: 'importing',
  SUCCESS: 'success',
  FAILED: 'failed',
})

/**
 * Human-readable labels for each status.
 */
export const CSV_ROW_STATUS_LABEL = Object.freeze({
  [CSV_ROW_STATUS.PENDING]: 'Ausstehend',
  [CSV_ROW_STATUS.IMPORTING]: 'Importieren…',
  [CSV_ROW_STATUS.SUCCESS]: 'Erfolgreich',
  [CSV_ROW_STATUS.FAILED]: 'Fehlgeschlagen',
})

/**
 * Design-system colour keys for each status.
 */
export const CSV_ROW_STATUS_COLOR = Object.freeze({
  [CSV_ROW_STATUS.PENDING]: 'info',
  [CSV_ROW_STATUS.IMPORTING]: 'warning',
  [CSV_ROW_STATUS.SUCCESS]: 'success',
  [CSV_ROW_STATUS.FAILED]: 'danger',
})

/**
 * MDI icon SVG paths for each status.
 */
export const CSV_ROW_STATUS_ICON = Object.freeze({
  [CSV_ROW_STATUS.PENDING]: mdiClockOutline,
  [CSV_ROW_STATUS.IMPORTING]: mdiLoading,
  [CSV_ROW_STATUS.SUCCESS]: mdiCheckCircle,
  [CSV_ROW_STATUS.FAILED]: mdiAlertCircle,
})
