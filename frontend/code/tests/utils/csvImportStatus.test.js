import { describe, expect, it } from 'vitest'

import {
  CSV_ROW_STATUS,
  CSV_ROW_STATUS_COLOR,
  CSV_ROW_STATUS_ICON,
  CSV_ROW_STATUS_LABEL,
} from '@/utils/csvImportStatus'

const VALID_DESIGN_COLORS = [
  'info',
  'success',
  'danger',
  'warning',
  'white',
  'light',
  'contrast',
]

const ALL_STATUS_VALUES = Object.values(CSV_ROW_STATUS)

describe('csvImportStatus', () => {
  describe('CSV_ROW_STATUS', () => {
    it('contains exactly four statuses', () => {
      expect(ALL_STATUS_VALUES).toHaveLength(4)
    })

    it('has the expected keys', () => {
      expect(CSV_ROW_STATUS).toHaveProperty('PENDING')
      expect(CSV_ROW_STATUS).toHaveProperty('IMPORTING')
      expect(CSV_ROW_STATUS).toHaveProperty('SUCCESS')
      expect(CSV_ROW_STATUS).toHaveProperty('FAILED')
    })

    it('values are unique strings', () => {
      const unique = new Set(ALL_STATUS_VALUES)
      expect(unique.size).toBe(ALL_STATUS_VALUES.length)
      ALL_STATUS_VALUES.forEach((v) => expect(typeof v).toBe('string'))
    })

    it('is frozen (immutable)', () => {
      expect(Object.isFrozen(CSV_ROW_STATUS)).toBe(true)
    })
  })

  describe('CSV_ROW_STATUS_LABEL', () => {
    it('has a label for every status', () => {
      ALL_STATUS_VALUES.forEach((status) => {
        expect(CSV_ROW_STATUS_LABEL[status]).toBeDefined()
        expect(typeof CSV_ROW_STATUS_LABEL[status]).toBe('string')
        expect(CSV_ROW_STATUS_LABEL[status].length).toBeGreaterThan(0)
      })
    })

    it('is frozen', () => {
      expect(Object.isFrozen(CSV_ROW_STATUS_LABEL)).toBe(true)
    })
  })

  describe('CSV_ROW_STATUS_COLOR', () => {
    it('has a color for every status', () => {
      ALL_STATUS_VALUES.forEach((status) => {
        expect(CSV_ROW_STATUS_COLOR[status]).toBeDefined()
      })
    })

    it('only uses valid design-system colors', () => {
      ALL_STATUS_VALUES.forEach((status) => {
        expect(VALID_DESIGN_COLORS).toContain(CSV_ROW_STATUS_COLOR[status])
      })
    })

    it('is frozen', () => {
      expect(Object.isFrozen(CSV_ROW_STATUS_COLOR)).toBe(true)
    })
  })

  describe('CSV_ROW_STATUS_ICON', () => {
    it('has an icon path for every status', () => {
      ALL_STATUS_VALUES.forEach((status) => {
        expect(CSV_ROW_STATUS_ICON[status]).toBeDefined()
        expect(typeof CSV_ROW_STATUS_ICON[status]).toBe('string')
        expect(CSV_ROW_STATUS_ICON[status].length).toBeGreaterThan(0)
      })
    })

    it('is frozen', () => {
      expect(Object.isFrozen(CSV_ROW_STATUS_ICON)).toBe(true)
    })
  })
})
