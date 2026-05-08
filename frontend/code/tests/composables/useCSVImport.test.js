import Papa from 'papaparse'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useCSVImport } from '@/composables/useCSVImport'
import { CSV_ROW_STATUS } from '@/utils/csvImportStatus'

// Mock PapaParse
vi.mock('papaparse', () => ({
  default: {
    parse: vi.fn(),
  },
}))

// Mock backend singleton (beginSilent/endSilent)
vi.mock('@/services', () => ({
  default: {
    beginSilent: vi.fn(),
    endSilent: vi.fn(),
  },
}))

// Helper: simulate PapaParse calling `complete` with given data
function simulateParse(data, fields, errors = []) {
  Papa.parse.mockImplementation((_file, opts) => {
    opts.complete({
      data,
      meta: { fields },
      errors,
    })
  })
}

// Helper: simulate PapaParse calling `error`
function simulateParseError(message) {
  Papa.parse.mockImplementation((_file, opts) => {
    opts.error({ message })
  })
}

function makeFile(name = 'test.csv', size = 100) {
  return { name, size }
}

const DEFAULT_MAPPINGS = [
  { key: 'email', label: 'E-Mail' },
  { key: 'name', label: 'Name' },
]

function createComposable(overrides = {}) {
  return useCSVImport({
    requiredMappings: DEFAULT_MAPPINGS,
    onImportConfirm: vi.fn().mockResolvedValue(true),
    onFinish: null,
    limit: null,
    ...overrides,
  })
}

describe('useCSVImport', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Initial state', () => {
    it('starts with no file and step 1', () => {
      const c = createComposable()
      expect(c.noFile.value).toBe(true)
      expect(c.rawRows.value).toEqual([])
      expect(c.csvHeaders.value).toEqual([])
      expect(c.currentStep.value).toBe(1)
      expect(c.isImporting.value).toBe(false)
      expect(c.hasImportStarted.value).toBe(false)
      expect(c.isImportFinished.value).toBe(false)
      expect(c.parseError.value).toBe('')
      expect(c.totalCount.value).toBe(0)
    })
  })

  describe('parseFile', () => {
    it('returns false for null file', async () => {
      const c = createComposable()
      const result = await c.parseFile(null)
      expect(result).toBe(false)
      expect(c.noFile.value).toBe(true)
    })

    it('rejects non-.csv extension', async () => {
      const c = createComposable()
      const result = await c.parseFile(makeFile('data.xlsx'))
      expect(result).toBe(false)
      expect(c.parseError.value).toContain('.csv')
    })

    it('rejects file exceeding 5 MB', async () => {
      const c = createComposable()
      const result = await c.parseFile(makeFile('big.csv', 6 * 1024 * 1024))
      expect(result).toBe(false)
      expect(c.parseError.value).toContain('zu groß')
    })

    it('parses a valid CSV and moves to step 2', async () => {
      const rows = [
        { email: 'a@b.com', name: 'Alice' },
        { email: 'c@d.com', name: 'Bob' },
      ]
      simulateParse(rows, ['email', 'name'])

      const c = createComposable()
      const result = await c.parseFile(makeFile())
      expect(result).toBe(true)
      expect(c.rawRows.value).toHaveLength(2)
      expect(c.csvHeaders.value).toEqual(['email', 'name'])
      expect(c.currentStep.value).toBe(2)
      expect(c.noFile.value).toBe(false)
    })

    it('detects limit exceeded', async () => {
      const rows = Array.from({ length: 5 }, (_, i) => ({
        email: `u${i}@x.com`,
      }))
      simulateParse(rows, ['email'])

      const c = createComposable({ limit: 3 })
      const result = await c.parseFile(makeFile())
      expect(result).toBe(false)
      expect(c.limitExceeded.value).toBe(true)
      expect(c.parsedRowCount.value).toBe(5)
      expect(c.rawRows.value).toEqual([])
    })

    it('sets parseError on PapaParse error callback', async () => {
      simulateParseError('Unexpected end of input')

      const c = createComposable()
      const result = await c.parseFile(makeFile())
      expect(result).toBe(false)
      expect(c.parseError.value).toContain('Unexpected end of input')
    })

    it('sets parseError on PapaParse result errors', async () => {
      Papa.parse.mockImplementation((_file, opts) => {
        opts.complete({
          data: [],
          meta: { fields: [] },
          errors: [{ message: 'Trailing comma' }],
        })
      })

      const c = createComposable()
      const result = await c.parseFile(makeFile())
      expect(result).toBe(false)
      expect(c.parseError.value).toContain('Trailing comma')
    })

    it('stores fileName and fileSize', async () => {
      simulateParse([{ email: 'a@b.com' }], ['email'])

      const c = createComposable()
      await c.parseFile(makeFile('users.csv', 4200))
      expect(c.fileName.value).toBe('users.csv')
      expect(c.fileSize.value).toBe(4200)
    })

    it('initialises header mapping with empty values', async () => {
      simulateParse([{ email: 'a@b.com' }], ['email'])

      const c = createComposable()
      await c.parseFile(makeFile())
      expect(c.headerMapping.value).toEqual({ email: '', name: '' })
    })

    it('initialises row status to PENDING', async () => {
      simulateParse([{ a: '1' }, { a: '2' }], ['a'])

      const c = createComposable()
      await c.parseFile(makeFile())
      expect(c.rowStatus.value).toEqual([
        CSV_ROW_STATUS.PENDING,
        CSV_ROW_STATUS.PENDING,
      ])
    })
  })

  describe('canConfirm', () => {
    it('is false when no mappings are set', async () => {
      simulateParse([{ email: 'a@b.com', name: 'A' }], ['email', 'name'])

      const c = createComposable()
      await c.parseFile(makeFile())
      expect(c.canConfirm.value).toBe(false)
    })

    it('is true when all mappings are set', async () => {
      simulateParse([{ email: 'a@b.com', name: 'A' }], ['email', 'name'])

      const c = createComposable()
      await c.parseFile(makeFile())
      c.headerMapping.value.email = 'email'
      c.headerMapping.value.name = 'name'
      expect(c.canConfirm.value).toBe(true)
    })

    it('is false when only some mappings are set', async () => {
      simulateParse([{ email: 'a@b.com', name: 'A' }], ['email', 'name'])

      const c = createComposable()
      await c.parseFile(makeFile())
      c.headerMapping.value.email = 'email'
      expect(c.canConfirm.value).toBe(false)
    })
  })

  describe('hasDuplicateMappings', () => {
    it('is false when mappings are unique', async () => {
      simulateParse([{ email: 'a@b.com', name: 'A' }], ['email', 'name'])

      const c = createComposable()
      await c.parseFile(makeFile())
      c.headerMapping.value.email = 'email'
      c.headerMapping.value.name = 'name'
      expect(c.hasDuplicateMappings.value).toBe(false)
    })

    it('is true when same CSV column is mapped twice', async () => {
      simulateParse([{ email: 'a@b.com', name: 'A' }], ['email', 'name'])

      const c = createComposable()
      await c.parseFile(makeFile())
      c.headerMapping.value.email = 'email'
      c.headerMapping.value.name = 'email'
      expect(c.hasDuplicateMappings.value).toBe(true)
    })

    it('ignores empty values', async () => {
      simulateParse([{ email: 'a@b.com', name: 'A' }], ['email', 'name'])

      const c = createComposable()
      await c.parseFile(makeFile())
      // Both empty => no duplicates
      expect(c.hasDuplicateMappings.value).toBe(false)
    })
  })

  describe('confirmImport', () => {
    async function setupForImport(c, count = 2) {
      const rows = Array.from({ length: count }, (_, i) => ({
        email: `u${i}@x.com`,
        name: `User${i}`,
      }))
      simulateParse(rows, ['email', 'name'])
      await c.parseFile(makeFile())
      c.headerMapping.value.email = 'email'
      c.headerMapping.value.name = 'name'
    }

    it('imports all rows successfully', async () => {
      const onImport = vi.fn().mockResolvedValue(true)
      const c = createComposable({ onImportConfirm: onImport })
      await setupForImport(c)

      await c.confirmImport()

      expect(onImport).toHaveBeenCalledTimes(2)
      expect(c.successCount.value).toBe(2)
      expect(c.failedCount.value).toBe(0)
      expect(c.isImportFinished.value).toBe(true)
      expect(c.currentStep.value).toBe(4)
    })

    it('records failed rows', async () => {
      const onImport = vi
        .fn()
        .mockResolvedValueOnce(true)
        .mockRejectedValueOnce(new Error('Duplicate'))
      const c = createComposable({ onImportConfirm: onImport })
      await setupForImport(c)

      await c.confirmImport()

      expect(c.successCount.value).toBe(1)
      expect(c.failedCount.value).toBe(1)
      expect(c.rowError.value[1]).toBe('Duplicate')
      expect(c.allowRetry.value).toBe(true)
    })

    it('extracts error message from response.data.message', async () => {
      const err = { response: { data: { message: 'API error' } } }
      const onImport = vi.fn().mockRejectedValue(err)
      const c = createComposable({ onImportConfirm: onImport })
      await setupForImport(c, 1)

      await c.confirmImport()

      expect(c.rowError.value[0]).toBe('API error')
    })

    it('extracts error message from response.data.detail', async () => {
      const err = { response: { data: { detail: 'Detail error' } } }
      const onImport = vi.fn().mockRejectedValue(err)
      const c = createComposable({ onImportConfirm: onImport })
      await setupForImport(c, 1)

      await c.confirmImport()

      expect(c.rowError.value[0]).toBe('Detail error')
    })

    it('falls back to "Unbekannter Fehler"', async () => {
      const onImport = vi.fn().mockRejectedValue({})
      const c = createComposable({ onImportConfirm: onImport })
      await setupForImport(c, 1)

      await c.confirmImport()

      expect(c.rowError.value[0]).toBe('Unbekannter Fehler')
    })

    it('calls onFinish when provided', async () => {
      const onFinish = vi.fn()
      const c = createComposable({ onFinish })
      await setupForImport(c)

      await c.confirmImport()

      expect(onFinish).toHaveBeenCalledTimes(1)
    })

    it('does not throw when onFinish is null', async () => {
      const c = createComposable({ onFinish: null })
      await setupForImport(c)

      await expect(c.confirmImport()).resolves.toBeUndefined()
    })
  })

  describe('retry (confirmImport with retryOnly=true)', () => {
    it('only retries failed rows', async () => {
      const onImport = vi
        .fn()
        .mockResolvedValueOnce(true)
        .mockRejectedValueOnce(new Error('fail'))
        // On retry, succeed:
        .mockResolvedValueOnce(true)

      const c = createComposable({ onImportConfirm: onImport })

      const rows = [
        { email: 'a@b.com', name: 'A' },
        { email: 'c@d.com', name: 'B' },
      ]
      simulateParse(rows, ['email', 'name'])
      await c.parseFile(makeFile())
      c.headerMapping.value.email = 'email'
      c.headerMapping.value.name = 'name'

      // First import
      await c.confirmImport()
      expect(c.failedCount.value).toBe(1)
      expect(c.successCount.value).toBe(1)

      // Retry only failed
      await c.confirmImport(true)
      expect(c.successCount.value).toBe(2)
      expect(c.failedCount.value).toBe(0)
      // 3 total calls: 2 initial + 1 retry
      expect(onImport).toHaveBeenCalledTimes(3)
    })
  })

  describe('progressPercent', () => {
    it('is 0 with no rows', () => {
      const c = createComposable()
      expect(c.progressPercent.value).toBe(0)
    })

    it('reflects completed fraction', async () => {
      const onImport = vi.fn().mockResolvedValue(true)
      const c = createComposable({ onImportConfirm: onImport })

      simulateParse(
        [
          { email: 'a@b.com', name: 'A' },
          { email: 'c@d.com', name: 'B' },
        ],
        ['email', 'name'],
      )
      await c.parseFile(makeFile())
      c.headerMapping.value.email = 'email'
      c.headerMapping.value.name = 'name'

      await c.confirmImport()
      expect(c.progressPercent.value).toBe(100)
    })
  })

  describe('reset', () => {
    it('resets all state to initial values', async () => {
      simulateParse([{ email: 'a@b.com' }], ['email'])
      const c = createComposable()
      await c.parseFile(makeFile('test.csv', 500))

      c.reset()

      expect(c.rawRows.value).toEqual([])
      expect(c.csvHeaders.value).toEqual([])
      expect(c.headerMapping.value).toEqual({})
      expect(c.rowStatus.value).toEqual([])
      expect(c.rowError.value).toEqual([])
      expect(c.hasImportStarted.value).toBe(false)
      expect(c.isImporting.value).toBe(false)
      expect(c.limitExceeded.value).toBe(false)
      expect(c.parsedRowCount.value).toBe(0)
      expect(c.parseError.value).toBe('')
      expect(c.fileName.value).toBe('')
      expect(c.fileSize.value).toBe(0)
      expect(c.noFile.value).toBe(true)
      expect(c.currentStep.value).toBe(1)
    })
  })
})
