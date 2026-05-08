import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick, ref } from 'vue'

import { useUnsavedChanges } from '@/composables/useUnsavedChanges'

describe('useUnsavedChanges', () => {
  let formData
  let onNavigateAway

  beforeEach(() => {
    formData = ref({ name: '', email: '' })
    onNavigateAway = vi.fn()
  })

  describe('Initialization', () => {
    it('initializes with hasChanges as false', () => {
      const { hasChanges } = useUnsavedChanges({ formData, onNavigateAway })
      expect(hasChanges.value).toBe(false)
    })

    it('initializes with showDiscardModal as false', () => {
      const { showDiscardModal } = useUnsavedChanges({
        formData,
        onNavigateAway,
      })
      expect(showDiscardModal.value).toBe(false)
    })
  })

  describe('setOriginal', () => {
    it('stores the original form state', () => {
      formData.value = { name: 'Test', email: 'test@example.com' }
      const { setOriginal, hasChanges } = useUnsavedChanges({
        formData,
        onNavigateAway,
      })

      setOriginal()

      // No changes yet
      expect(hasChanges.value).toBe(false)
    })

    it('detects changes after setOriginal is called', async () => {
      formData.value = { name: 'Test', email: 'test@example.com' }
      const { setOriginal, hasChanges } = useUnsavedChanges({
        formData,
        onNavigateAway,
      })

      setOriginal()

      formData.value.name = 'Modified'
      await nextTick()

      expect(hasChanges.value).toBe(true)
    })

    it('shows no changes when form is restored to original', async () => {
      formData.value = { name: 'Test', email: 'test@example.com' }
      const { setOriginal, hasChanges } = useUnsavedChanges({
        formData,
        onNavigateAway,
      })

      setOriginal()

      formData.value.name = 'Modified'
      await nextTick()
      expect(hasChanges.value).toBe(true)

      formData.value.name = 'Test'
      await nextTick()
      expect(hasChanges.value).toBe(false)
    })
  })

  describe('markAsSaved', () => {
    it('disables change detection after marking as saved', async () => {
      formData.value = { name: 'Test', email: 'test@example.com' }
      const { setOriginal, markAsSaved, hasChanges } = useUnsavedChanges({
        formData,
        onNavigateAway,
      })

      setOriginal()
      formData.value.name = 'Modified'
      await nextTick()

      expect(hasChanges.value).toBe(true)

      markAsSaved()
      await nextTick()

      expect(hasChanges.value).toBe(false)
    })
  })

  describe('handleCancel', () => {
    it('returns true when there are no changes', () => {
      const { handleCancel } = useUnsavedChanges({ formData, onNavigateAway })

      const result = handleCancel()

      expect(result).toBe(true)
    })

    it('returns false and shows modal when there are changes', async () => {
      formData.value = { name: 'Test', email: 'test@example.com' }
      const { setOriginal, handleCancel, showDiscardModal } = useUnsavedChanges(
        { formData, onNavigateAway },
      )

      setOriginal()
      formData.value.name = 'Modified'
      await nextTick()

      const result = handleCancel()

      expect(result).toBe(false)
      expect(showDiscardModal.value).toBe(true)
    })

    it('returns true after markAsSaved even with modifications', async () => {
      formData.value = { name: 'Test', email: 'test@example.com' }
      const { setOriginal, markAsSaved, handleCancel } = useUnsavedChanges({
        formData,
        onNavigateAway,
      })

      setOriginal()
      formData.value.name = 'Modified'
      await nextTick()

      markAsSaved()

      const result = handleCancel()

      expect(result).toBe(true)
    })
  })

  describe('confirmDiscard', () => {
    it('closes the modal', async () => {
      formData.value = { name: 'Test', email: 'test@example.com' }
      const { setOriginal, handleCancel, confirmDiscard, showDiscardModal } =
        useUnsavedChanges({ formData, onNavigateAway })

      setOriginal()
      formData.value.name = 'Modified'
      await nextTick()

      handleCancel()
      expect(showDiscardModal.value).toBe(true)

      confirmDiscard()
      expect(showDiscardModal.value).toBe(false)
    })

    it('calls onNavigateAway callback', async () => {
      formData.value = { name: 'Test', email: 'test@example.com' }
      const { setOriginal, handleCancel, confirmDiscard } = useUnsavedChanges({
        formData,
        onNavigateAway,
      })

      setOriginal()
      formData.value.name = 'Modified'
      await nextTick()

      handleCancel()
      confirmDiscard()

      expect(onNavigateAway).toHaveBeenCalledTimes(1)
    })

    it('marks as saved to prevent further warnings', async () => {
      formData.value = { name: 'Test', email: 'test@example.com' }
      const { setOriginal, handleCancel, confirmDiscard, hasChanges } =
        useUnsavedChanges({ formData, onNavigateAway })

      setOriginal()
      formData.value.name = 'Modified'
      await nextTick()

      expect(hasChanges.value).toBe(true)

      handleCancel()
      confirmDiscard()
      await nextTick()

      expect(hasChanges.value).toBe(false)
    })
  })

  describe('cancelDiscard', () => {
    it('closes the modal without navigating', async () => {
      formData.value = { name: 'Test', email: 'test@example.com' }
      const { setOriginal, handleCancel, cancelDiscard, showDiscardModal } =
        useUnsavedChanges({ formData, onNavigateAway })

      setOriginal()
      formData.value.name = 'Modified'
      await nextTick()

      handleCancel()
      expect(showDiscardModal.value).toBe(true)

      cancelDiscard()
      expect(showDiscardModal.value).toBe(false)
      expect(onNavigateAway).not.toHaveBeenCalled()
    })

    it('preserves hasChanges state', async () => {
      formData.value = { name: 'Test', email: 'test@example.com' }
      const { setOriginal, handleCancel, cancelDiscard, hasChanges } =
        useUnsavedChanges({ formData, onNavigateAway })

      setOriginal()
      formData.value.name = 'Modified'
      await nextTick()

      handleCancel()
      cancelDiscard()

      expect(hasChanges.value).toBe(true)
    })
  })

  describe('hasChanges computed', () => {
    it('returns false before setOriginal is called', async () => {
      formData.value = { name: 'Test' }
      const { hasChanges } = useUnsavedChanges({ formData, onNavigateAway })

      formData.value.name = 'Modified'
      await nextTick()

      expect(hasChanges.value).toBe(false)
    })

    it('detects nested object changes', async () => {
      formData.value = { user: { name: 'Test', email: 'test@example.com' } }
      const { setOriginal, hasChanges } = useUnsavedChanges({
        formData,
        onNavigateAway,
      })

      setOriginal()

      formData.value.user.name = 'Modified'
      await nextTick()

      expect(hasChanges.value).toBe(true)
    })

    it('detects array changes', async () => {
      formData.value = { items: ['a', 'b', 'c'] }
      const { setOriginal, hasChanges } = useUnsavedChanges({
        formData,
        onNavigateAway,
      })

      setOriginal()

      formData.value.items.push('d')
      await nextTick()

      expect(hasChanges.value).toBe(true)
    })

    it('detects property addition', async () => {
      formData.value = { name: 'Test' }
      const { setOriginal, hasChanges } = useUnsavedChanges({
        formData,
        onNavigateAway,
      })

      setOriginal()

      formData.value.email = 'test@example.com'
      await nextTick()

      expect(hasChanges.value).toBe(true)
    })

    it('detects property removal', async () => {
      formData.value = { name: 'Test', email: 'test@example.com' }
      const { setOriginal, hasChanges } = useUnsavedChanges({
        formData,
        onNavigateAway,
      })

      setOriginal()

      delete formData.value.email
      await nextTick()

      expect(hasChanges.value).toBe(true)
    })
  })

  describe('Edge cases', () => {
    it('handles null formData gracefully', () => {
      formData.value = null
      const { setOriginal, hasChanges } = useUnsavedChanges({
        formData,
        onNavigateAway,
      })

      setOriginal()

      expect(hasChanges.value).toBe(false)
    })

    it('handles empty object', () => {
      formData.value = {}
      const { setOriginal, hasChanges } = useUnsavedChanges({
        formData,
        onNavigateAway,
      })

      setOriginal()

      expect(hasChanges.value).toBe(false)
    })

    it('handles multiple setOriginal calls', async () => {
      formData.value = { name: 'First' }
      const { setOriginal, hasChanges } = useUnsavedChanges({
        formData,
        onNavigateAway,
      })

      setOriginal()

      formData.value.name = 'Second'
      setOriginal()

      formData.value.name = 'Second'
      await nextTick()

      expect(hasChanges.value).toBe(false)

      formData.value.name = 'Third'
      await nextTick()

      expect(hasChanges.value).toBe(true)
    })

    it('works without onNavigateAway callback', () => {
      const { confirmDiscard } = useUnsavedChanges({ formData })

      expect(() => confirmDiscard()).not.toThrow()
    })
  })
})
