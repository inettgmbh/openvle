import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useBatchAdd } from '@/composables/useBatchAdd'

function makeItem(id, name) {
  return { id, name, _displayName: name }
}

function createComposable(overrides = {}) {
  return useBatchAdd({
    execute: vi.fn().mockResolvedValue({ ok: true }),
    idKey: 'id',
    batchSize: 3,
    ...overrides,
  })
}

describe('useBatchAdd', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Initial state', () => {
    it('starts with empty selection and selecting phase', () => {
      const { selectedItems, phase, progress } = createComposable()

      expect(selectedItems.value).toEqual([])
      expect(phase.value).toBe('selecting')
      expect(progress.value).toEqual({
        current: 0,
        total: 0,
        errors: [],
        skipped: 0,
      })
    })
  })

  describe('addItem', () => {
    it('adds an item to the selection', () => {
      const { addItem, selectedItems } = createComposable()
      const item = makeItem('1', 'Alice')

      const result = addItem(item)

      expect(result).toBe(true)
      expect(selectedItems.value).toHaveLength(1)
      expect(selectedItems.value[0]).toEqual(item)
    })

    it('adds multiple items', () => {
      const { addItem, selectedItems } = createComposable()

      addItem(makeItem('1', 'Alice'))
      addItem(makeItem('2', 'Bob'))
      addItem(makeItem('3', 'Charlie'))

      expect(selectedItems.value).toHaveLength(3)
    })

    it('rejects duplicate items and returns false', () => {
      const { addItem, selectedItems } = createComposable()

      addItem(makeItem('1', 'Alice'))
      const result = addItem(makeItem('1', 'Alice Copy'))

      expect(result).toBe(false)
      expect(selectedItems.value).toHaveLength(1)
      expect(selectedItems.value[0].name).toBe('Alice')
    })

    it('uses custom idKey for duplicate detection', () => {
      const { addItem, selectedItems } = createComposable({
        idKey: 'email',
      })

      addItem({ email: 'a@b.com', name: 'Alice' })
      const result = addItem({ email: 'a@b.com', name: 'Alice 2' })

      expect(result).toBe(false)
      expect(selectedItems.value).toHaveLength(1)
    })
  })

  describe('hasItem', () => {
    it('returns true for existing item', () => {
      const { addItem, hasItem } = createComposable()

      addItem(makeItem('1', 'Alice'))

      expect(hasItem('1')).toBe(true)
    })

    it('returns false for non-existing item', () => {
      const { addItem, hasItem } = createComposable()

      addItem(makeItem('1', 'Alice'))

      expect(hasItem('2')).toBe(false)
    })

    it('returns false on empty selection', () => {
      const { hasItem } = createComposable()

      expect(hasItem('1')).toBe(false)
    })
  })

  describe('removeItem', () => {
    it('removes an item by id', () => {
      const { addItem, removeItem, selectedItems } = createComposable()

      addItem(makeItem('1', 'Alice'))
      addItem(makeItem('2', 'Bob'))
      removeItem('1')

      expect(selectedItems.value).toHaveLength(1)
      expect(selectedItems.value[0].id).toBe('2')
    })

    it('does nothing for non-existing id', () => {
      const { addItem, removeItem, selectedItems } = createComposable()

      addItem(makeItem('1', 'Alice'))
      removeItem('99')

      expect(selectedItems.value).toHaveLength(1)
    })

    it('allows re-adding a removed item', () => {
      const { addItem, removeItem, selectedItems } = createComposable()

      addItem(makeItem('1', 'Alice'))
      removeItem('1')
      const result = addItem(makeItem('1', 'Alice Re-added'))

      expect(result).toBe(true)
      expect(selectedItems.value).toHaveLength(1)
    })
  })

  describe('clearItems', () => {
    it('removes all items', () => {
      const { addItem, clearItems, selectedItems } = createComposable()

      addItem(makeItem('1', 'Alice'))
      addItem(makeItem('2', 'Bob'))
      clearItems()

      expect(selectedItems.value).toEqual([])
    })
  })

  describe('performSave', () => {
    it('executes all items and sets phase to done', async () => {
      const execute = vi.fn().mockResolvedValue({ ok: true })
      const { addItem, performSave, phase, progress } = createComposable({
        execute,
      })

      addItem(makeItem('1', 'Alice'))
      addItem(makeItem('2', 'Bob'))
      await performSave()

      expect(execute).toHaveBeenCalledTimes(2)
      expect(execute).toHaveBeenCalledWith(expect.objectContaining({ id: '1' }))
      expect(execute).toHaveBeenCalledWith(expect.objectContaining({ id: '2' }))
      expect(phase.value).toBe('done')
      expect(progress.value.errors).toEqual([])
      expect(progress.value.skipped).toBe(0)
    })

    it('sets phase to saving during execution', async () => {
      let phaseDuringExecution
      const execute = vi.fn().mockImplementation(function () {
        phaseDuringExecution = phase.value
        return Promise.resolve()
      })
      const { addItem, performSave, phase } = createComposable({ execute })

      addItem(makeItem('1', 'Alice'))
      await performSave()

      expect(phaseDuringExecution).toBe('saving')
    })

    it('calls onComplete with correct counts on full success', async () => {
      const onComplete = vi.fn()
      const { addItem, performSave } = createComposable({
        execute: vi.fn().mockResolvedValue({}),
        onComplete,
      })

      addItem(makeItem('1', 'Alice'))
      addItem(makeItem('2', 'Bob'))
      await performSave()

      expect(onComplete).toHaveBeenCalledWith({
        succeeded: 2,
        failed: 0,
        skipped: 0,
        total: 2,
      })
    })

    it('tracks progress during execution', async () => {
      const progressValues = []
      const execute = vi.fn().mockImplementation(async () => {
        progressValues.push({ ...vi.mocked })
        return { ok: true }
      })
      const { addItem, performSave, progress } = createComposable({
        execute,
        batchSize: 1,
      })

      addItem(makeItem('1', 'Alice'))
      addItem(makeItem('2', 'Bob'))
      await performSave()

      expect(progress.value.current).toBe(2)
      expect(progress.value.total).toBe(2)
    })

    it('handles empty selection gracefully', async () => {
      const onComplete = vi.fn()
      const { performSave, phase } = createComposable({ onComplete })

      await performSave()

      expect(phase.value).toBe('done')
      expect(onComplete).toHaveBeenCalledWith({
        succeeded: 0,
        failed: 0,
        skipped: 0,
        total: 0,
      })
    })

    describe('Error handling', () => {
      it('sets phase to error when operations fail', async () => {
        const execute = vi
          .fn()
          .mockResolvedValueOnce({})
          .mockRejectedValueOnce(new Error('Network error'))
        const { addItem, performSave, phase, progress } = createComposable({
          execute,
        })

        addItem(makeItem('1', 'Alice'))
        addItem(makeItem('2', 'Bob'))
        await performSave()

        expect(phase.value).toBe('error')
        expect(progress.value.errors).toHaveLength(1)
      })

      it('includes item display name in error details', async () => {
        const execute = vi.fn().mockRejectedValue(new Error('API error'))
        const { addItem, performSave, progress } = createComposable({
          execute,
        })

        addItem(makeItem('1', 'Alice'))
        await performSave()

        expect(progress.value.errors[0].itemName).toBe('Alice')
      })

      it('falls back to idKey when _displayName is missing', async () => {
        const execute = vi.fn().mockRejectedValue(new Error('API error'))
        const { addItem, performSave, progress } = createComposable({
          execute,
        })

        addItem({ id: 'uuid-123', name: 'NoDisplay' })
        await performSave()

        expect(progress.value.errors[0].itemName).toBe('uuid-123')
      })

      it('calls onComplete with failed count', async () => {
        const onComplete = vi.fn()
        const execute = vi
          .fn()
          .mockResolvedValueOnce({})
          .mockRejectedValueOnce(new Error('fail'))
          .mockResolvedValueOnce({})
        const { addItem, performSave } = createComposable({
          execute,
          onComplete,
        })

        addItem(makeItem('1', 'Alice'))
        addItem(makeItem('2', 'Bob'))
        addItem(makeItem('3', 'Charlie'))
        await performSave()

        expect(onComplete).toHaveBeenCalledWith({
          succeeded: 2,
          failed: 1,
          skipped: 0,
          total: 3,
        })
      })

      it('collects multiple errors', async () => {
        const execute = vi
          .fn()
          .mockRejectedValueOnce(new Error('err1'))
          .mockRejectedValueOnce(new Error('err2'))
        const { addItem, performSave, progress } = createComposable({
          execute,
        })

        addItem(makeItem('1', 'Alice'))
        addItem(makeItem('2', 'Bob'))
        await performSave()

        expect(progress.value.errors).toHaveLength(2)
      })
    })

    describe('Skippable errors', () => {
      function makeDuplicateError() {
        const err = new Error('Duplicate')
        err.response = {
          data: { error_code: 'DUPLICATE_EVENT_USER_ROLE' },
        }
        return err
      }

      const isSkippable = (err) =>
        err?.response?.data?.error_code === 'DUPLICATE_EVENT_USER_ROLE'

      it('counts skippable errors as skipped, not failed', async () => {
        const execute = vi
          .fn()
          .mockResolvedValueOnce({})
          .mockRejectedValueOnce(makeDuplicateError())
        const onComplete = vi.fn()
        const { addItem, performSave, phase, progress } = createComposable({
          execute,
          isSkippable,
          onComplete,
        })

        addItem(makeItem('1', 'Alice'))
        addItem(makeItem('2', 'Bob'))
        await performSave()

        expect(phase.value).toBe('done')
        expect(progress.value.skipped).toBe(1)
        expect(progress.value.errors).toHaveLength(0)
        expect(onComplete).toHaveBeenCalledWith({
          succeeded: 1,
          failed: 0,
          skipped: 1,
          total: 2,
        })
      })

      it('does not skip non-matching errors', async () => {
        const execute = vi.fn().mockRejectedValue(new Error('Real error'))
        const { addItem, performSave, phase, progress } = createComposable({
          execute,
          isSkippable,
        })

        addItem(makeItem('1', 'Alice'))
        await performSave()

        expect(phase.value).toBe('error')
        expect(progress.value.errors).toHaveLength(1)
        expect(progress.value.skipped).toBe(0)
      })

      it('handles mix of success, skipped, and failed', async () => {
        const execute = vi
          .fn()
          .mockResolvedValueOnce({})
          .mockRejectedValueOnce(makeDuplicateError())
          .mockRejectedValueOnce(new Error('Server error'))
        const onComplete = vi.fn()
        const { addItem, performSave, phase, progress } = createComposable({
          execute,
          isSkippable,
          onComplete,
        })

        addItem(makeItem('1', 'Alice'))
        addItem(makeItem('2', 'Bob'))
        addItem(makeItem('3', 'Charlie'))
        await performSave()

        expect(phase.value).toBe('error')
        expect(progress.value.skipped).toBe(1)
        expect(progress.value.errors).toHaveLength(1)
        expect(onComplete).toHaveBeenCalledWith({
          succeeded: 1,
          failed: 1,
          skipped: 1,
          total: 3,
        })
      })

      it('all skipped results in done phase, not error', async () => {
        const execute = vi.fn().mockRejectedValue(makeDuplicateError())
        const { addItem, performSave, phase, progress } = createComposable({
          execute,
          isSkippable,
        })

        addItem(makeItem('1', 'Alice'))
        addItem(makeItem('2', 'Bob'))
        await performSave()

        expect(phase.value).toBe('done')
        expect(progress.value.skipped).toBe(2)
        expect(progress.value.errors).toHaveLength(0)
      })

      it('works without isSkippable (all errors are real)', async () => {
        const execute = vi.fn().mockRejectedValue(makeDuplicateError())
        const { addItem, performSave, phase, progress } = createComposable({
          execute,
          // no isSkippable provided
        })

        addItem(makeItem('1', 'Alice'))
        await performSave()

        expect(phase.value).toBe('error')
        expect(progress.value.errors).toHaveLength(1)
        expect(progress.value.skipped).toBe(0)
      })
    })

    describe('Silent mode (toast suppression)', () => {
      it('calls beginSilent before execution and endSilent after', async () => {
        const beginSilent = vi.fn()
        const endSilent = vi.fn()
        const callOrder = []

        beginSilent.mockImplementation(() => callOrder.push('begin'))
        endSilent.mockImplementation(() => callOrder.push('end'))

        const execute = vi.fn().mockImplementation(async () => {
          callOrder.push('execute')
          return {}
        })

        const { addItem, performSave } = createComposable({
          execute,
          beginSilent,
          endSilent,
        })

        addItem(makeItem('1', 'Alice'))
        await performSave()

        expect(beginSilent).toHaveBeenCalledTimes(1)
        expect(endSilent).toHaveBeenCalledTimes(1)
        expect(callOrder[0]).toBe('begin')
        expect(callOrder[callOrder.length - 1]).toBe('end')
      })

      it('calls endSilent even when errors occur', async () => {
        const endSilent = vi.fn()
        const execute = vi.fn().mockRejectedValue(new Error('fail'))

        const { addItem, performSave } = createComposable({
          execute,
          beginSilent: vi.fn(),
          endSilent,
        })

        addItem(makeItem('1', 'Alice'))
        await performSave()

        expect(endSilent).toHaveBeenCalledTimes(1)
      })

      it('works without beginSilent/endSilent', async () => {
        const { addItem, performSave, phase } = createComposable({
          execute: vi.fn().mockResolvedValue({}),
          // no beginSilent/endSilent
        })

        addItem(makeItem('1', 'Alice'))
        await expect(performSave()).resolves.toBeUndefined()
        expect(phase.value).toBe('done')
      })
    })
  })

  describe('reset', () => {
    it('resets all state to initial values', async () => {
      const { addItem, performSave, reset, selectedItems, phase, progress } =
        createComposable({
          execute: vi.fn().mockResolvedValue({}),
        })

      addItem(makeItem('1', 'Alice'))
      addItem(makeItem('2', 'Bob'))
      await performSave()

      expect(phase.value).toBe('done')
      expect(selectedItems.value).toHaveLength(2)

      reset()

      expect(selectedItems.value).toEqual([])
      expect(phase.value).toBe('selecting')
      expect(progress.value).toEqual({
        current: 0,
        total: 0,
        errors: [],
        skipped: 0,
      })
    })

    it('allows re-adding items after reset', () => {
      const { addItem, reset, selectedItems } = createComposable()

      addItem(makeItem('1', 'Alice'))
      reset()
      const result = addItem(makeItem('1', 'Alice'))

      expect(result).toBe(true)
      expect(selectedItems.value).toHaveLength(1)
    })
  })

  describe('Custom idKey', () => {
    it('uses custom key for all operations', () => {
      const { addItem, removeItem, hasItem, selectedItems } = createComposable({
        idKey: 'uuid',
      })

      addItem({ uuid: 'abc', name: 'Alice' })

      expect(hasItem('abc')).toBe(true)
      expect(hasItem('xyz')).toBe(false)

      removeItem('abc')
      expect(selectedItems.value).toEqual([])
    })

    it('uses custom key in error item names', async () => {
      const execute = vi.fn().mockRejectedValue(new Error('fail'))
      const { addItem, performSave, progress } = createComposable({
        execute,
        idKey: 'email',
      })

      addItem({ email: 'alice@test.com', name: 'Alice' })
      await performSave()

      // Falls back to idKey value when no _displayName
      expect(progress.value.errors[0].itemName).toBe('alice@test.com')
    })
  })
})
