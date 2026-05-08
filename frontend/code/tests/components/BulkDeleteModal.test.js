import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

// Mock executeBatched — we control its return value per test
const mockExecuteBatched = vi.fn()
vi.mock('@/utils/batchedExecution', () => ({
  executeBatched: (...args) => mockExecuteBatched(...args),
}))

vi.mock('@/stores/style.js', () => ({
  useStyleStore: () => ({ darkMode: false }),
}))

const stubs = {
  OverlayLayer: {
    template:
      '<div class="overlay" v-if="$attrs[\'onOverlayClick\']"><slot /></div>',
  },
  CardBox: {
    template: `
      <div class="card-box">
        <slot />
        <slot name="footer" />
      </div>
    `,
    props: ['isModal'],
  },
  CardBoxComponentTitle: {
    template: '<div class="card-title">{{ title }}<slot /></div>',
    props: ['title'],
  },
  BaseButton: {
    template:
      '<button class="base-button" :disabled="disabled" :data-label="label" :data-color="color" @click="$emit(\'click\')">{{ label }}</button>',
    props: [
      'label',
      'color',
      'disabled',
      'icon',
      'small',
      'roundedFull',
      'outline',
    ],
    emits: ['click'],
  },
  BaseButtons: {
    template: '<div class="base-buttons"><slot /></div>',
  },
  BaseIcon: {
    template: '<span class="base-icon"></span>',
    props: ['path', 'w', 'h', 'size'],
  },
}

import BulkDeleteModal from '@/components/BulkDeleteModal.vue'

describe('BulkDeleteModal', () => {
  let wrapper

  const makeItems = (count, labelKey = 'name') =>
    Array.from({ length: count }, (_, i) => ({
      id: `id-${i + 1}`,
      [labelKey]: `User ${i + 1}`,
      event_id: 'evt-1',
      user_id: `uid-${i + 1}`,
      role_id: 'role-1',
    }))

  const defaultProps = {
    modelValue: true,
    items: makeItems(3),
    execute: vi.fn().mockResolvedValue({}),
  }

  const createWrapper = (props = {}, slots = {}) => {
    wrapper = mount(BulkDeleteModal, {
      props: { ...defaultProps, ...props },
      global: { stubs },
      slots,
    })
    return wrapper
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockExecuteBatched.mockResolvedValue({ results: [], errors: [] })
  })

  afterEach(() => {
    if (wrapper) wrapper.unmount()
  })

  // ───────────────────────────────────────────
  // Rendering — Confirming Phase
  // ───────────────────────────────────────────
  describe('Rendering (confirming phase)', () => {
    it('renders modal with title containing item count', async () => {
      createWrapper({ modelValue: false })
      await wrapper.setProps({ modelValue: true })
      await nextTick()
      expect(wrapper.find('.card-title').text()).toContain(
        '3 Einträge entfernen',
      )
    })

    it('renders item names in the list', () => {
      createWrapper()
      expect(wrapper.text()).toContain('User 1')
      expect(wrapper.text()).toContain('User 2')
      expect(wrapper.text()).toContain('User 3')
    })

    it('uses labelKey prop for item display', () => {
      const items = [
        { id: '1', username: 'alice' },
        { id: '2', username: 'bob' },
      ]
      createWrapper({ items, labelKey: 'username' })
      expect(wrapper.text()).toContain('alice')
      expect(wrapper.text()).toContain('bob')
    })

    it('shows "Sind Sie sicher?" prompt', () => {
      createWrapper()
      expect(wrapper.text()).toContain('Sind Sie sicher?')
    })

    it('renders close button in confirming phase', () => {
      createWrapper()
      const titleButtons = wrapper.findAll('.card-title .base-button')
      expect(titleButtons.length).toBeGreaterThanOrEqual(1)
    })

    it('limits displayed items to 10 and shows remaining count', () => {
      createWrapper({ items: makeItems(15) })
      expect(wrapper.text()).toContain('User 10')
      expect(wrapper.text()).not.toContain('User 11')
      expect(wrapper.text()).toContain('und 5 weitere')
    })

    it('does not show remaining count when 10 or fewer items', () => {
      createWrapper({ items: makeItems(10) })
      expect(wrapper.text()).not.toContain('weitere')
    })

    it('does not show progress UI in confirming phase', () => {
      createWrapper()
      expect(wrapper.text()).not.toContain('Wird entfernt...')
      expect(wrapper.text()).not.toContain('Abgeschlossen')
    })
  })

  // ───────────────────────────────────────────
  // Slot Rendering
  // ───────────────────────────────────────────
  describe('Slot rendering', () => {
    it('renders warning slot content', () => {
      createWrapper(
        {},
        { warning: '<div class="test-warning">Aktive Veranstaltung!</div>' },
      )
      expect(wrapper.find('.test-warning').exists()).toBe(true)
      expect(wrapper.text()).toContain('Aktive Veranstaltung!')
    })

    it('renders description slot content', () => {
      createWrapper(
        {},
        {
          description:
            '<p class="test-desc">Teilnehmer werden aus Event X entfernt.</p>',
        },
      )
      expect(wrapper.find('.test-desc').exists()).toBe(true)
      expect(wrapper.text()).toContain(
        'Teilnehmer werden aus Event X entfernt.',
      )
    })

    it('renders both warning and description slots together', () => {
      createWrapper(
        {},
        {
          warning: '<div class="test-warning">Warnung</div>',
          description: '<div class="test-desc">Beschreibung</div>',
        },
      )
      expect(wrapper.find('.test-warning').exists()).toBe(true)
      expect(wrapper.find('.test-desc').exists()).toBe(true)
    })

    it('does not render slots during deleting phase', async () => {
      mockExecuteBatched.mockReturnValue(new Promise(() => {})) // never resolves
      createWrapper({}, { warning: '<div class="test-warning">Warnung</div>' })

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await nextTick()

      expect(wrapper.find('.test-warning').exists()).toBe(false)
    })
  })

  // ───────────────────────────────────────────
  // Footer Buttons
  // ───────────────────────────────────────────
  describe('Footer buttons', () => {
    it('shows Entfernen and Abbrechen in confirming phase', () => {
      createWrapper()
      const labels = wrapper
        .findAll('.base-buttons .base-button')
        .map((b) => b.attributes('data-label'))

      expect(labels).toContain('Entfernen')
      expect(labels).toContain('Abbrechen')
    })

    it('Entfernen button has danger color', () => {
      createWrapper()
      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')

      expect(deleteBtn.attributes('data-color')).toBe('danger')
    })

    it('emits update:modelValue false when Abbrechen is clicked', async () => {
      createWrapper()

      const cancelBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Abbrechen')
      await cancelBtn.trigger('click')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')[0]).toEqual([false])
    })

    it('shows no footer buttons during deleting phase', async () => {
      mockExecuteBatched.mockReturnValue(new Promise(() => {}))
      createWrapper()

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await nextTick()

      const buttons = wrapper.findAll('.base-buttons .base-button')
      expect(buttons).toHaveLength(0)
    })

    it('shows Fertig button with success color when done without errors', async () => {
      mockExecuteBatched.mockResolvedValue({
        results: [{}, {}, {}],
        errors: [],
      })
      createWrapper()

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      const labels = wrapper
        .findAll('.base-buttons .base-button')
        .map((b) => b.attributes('data-label'))

      expect(labels).toContain('Fertig')
      expect(labels).not.toContain('Entfernen')
      expect(labels).not.toContain('Abbrechen')

      const fertigBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Fertig')
      expect(fertigBtn.attributes('data-color')).toBe('success')
    })

    it('shows Schließen button with danger color when done with errors', async () => {
      mockExecuteBatched.mockResolvedValue({
        results: [null],
        errors: [{ index: 0, error: new Error('fail') }],
      })
      createWrapper({ items: makeItems(1) })

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      const closeBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Schließen')
      expect(closeBtn).toBeTruthy()
      expect(closeBtn.attributes('data-color')).toBe('danger')
    })

    it('emits update:modelValue false when Fertig is clicked', async () => {
      mockExecuteBatched.mockResolvedValue({ results: [], errors: [] })
      createWrapper()

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      const fertigBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Fertig')
      await fertigBtn.trigger('click')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      const emits = wrapper.emitted('update:modelValue')
      expect(emits[emits.length - 1]).toEqual([false])
    })
  })

  // ───────────────────────────────────────────
  // Delete Execution
  // ───────────────────────────────────────────
  describe('Delete execution', () => {
    it('calls executeBatched with one operation per item', async () => {
      const execute = vi.fn().mockResolvedValue({})
      createWrapper({ items: makeItems(3), execute })

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      expect(mockExecuteBatched).toHaveBeenCalledTimes(1)
      const [operations, options] = mockExecuteBatched.mock.calls[0]
      expect(operations).toHaveLength(3)
      expect(options.batchSize).toBe(3) // default
    })

    it('respects custom batchSize prop', async () => {
      createWrapper({ batchSize: 5 })

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      const [, options] = mockExecuteBatched.mock.calls[0]
      expect(options.batchSize).toBe(5)
    })

    it('calls execute prop for each item via operations', async () => {
      const execute = vi.fn().mockResolvedValue({})
      const items = makeItems(2)
      createWrapper({ items, execute })

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      // Call each operation to verify it invokes execute with the correct item
      const [operations] = mockExecuteBatched.mock.calls[0]
      await operations[0]()
      expect(execute).toHaveBeenCalledWith(items[0])
      await operations[1]()
      expect(execute).toHaveBeenCalledWith(items[1])
    })

    it('calls beginSilent before and endSilent after execution', async () => {
      const beginSilent = vi.fn()
      const endSilent = vi.fn()
      createWrapper({ beginSilent, endSilent })

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      expect(beginSilent).toHaveBeenCalledTimes(1)
      expect(endSilent).toHaveBeenCalledTimes(1)
    })

    it('does not call beginSilent/endSilent when not provided', async () => {
      createWrapper({ beginSilent: null, endSilent: null })

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      // Should not throw
      expect(mockExecuteBatched).toHaveBeenCalledTimes(1)
    })

    it('calls endSilent even when errors occur', async () => {
      const endSilent = vi.fn()
      mockExecuteBatched.mockResolvedValue({
        results: [null],
        errors: [{ index: 0, error: new Error('fail') }],
      })
      createWrapper({ items: makeItems(1), beginSilent: vi.fn(), endSilent })

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      expect(endSilent).toHaveBeenCalledTimes(1)
    })
  })

  // ───────────────────────────────────────────
  // Phase: Deleting
  // ───────────────────────────────────────────
  describe('Phase: Deleting', () => {
    it('shows "Wird entfernt..." label', async () => {
      mockExecuteBatched.mockReturnValue(new Promise(() => {}))
      createWrapper()

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await nextTick()

      expect(wrapper.text()).toContain('Wird entfernt...')
    })

    it('shows progress counter', async () => {
      mockExecuteBatched.mockReturnValue(new Promise(() => {}))
      createWrapper()

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await nextTick()

      expect(wrapper.text()).toContain('0 / 3')
    })

    it('hides confirming UI elements', async () => {
      mockExecuteBatched.mockReturnValue(new Promise(() => {}))
      createWrapper()

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await nextTick()

      expect(wrapper.text()).not.toContain('Sind Sie sicher?')
      expect(wrapper.text()).not.toContain('User 1')
    })
  })

  // ───────────────────────────────────────────
  // Phase: Done
  // ───────────────────────────────────────────
  describe('Phase: Done', () => {
    it('shows "Abgeschlossen" label', async () => {
      mockExecuteBatched.mockResolvedValue({
        results: [{}, {}, {}],
        errors: [],
      })
      createWrapper()

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('Abgeschlossen')
    })

    it('shows 100% progress', async () => {
      mockExecuteBatched.mockImplementation((ops, options) => {
        // Simulate onProgress being called with all items completed
        if (options?.onProgress) options.onProgress(ops.length)
        return Promise.resolve({ results: [{}, {}, {}], errors: [] })
      })
      createWrapper()

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('100%')
      expect(wrapper.text()).toContain('3 / 3')
    })

    it('emits completed with correct counts on full success', async () => {
      mockExecuteBatched.mockResolvedValue({
        results: [{}, {}, {}],
        errors: [],
      })
      createWrapper()

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      expect(wrapper.emitted('completed')).toBeTruthy()
      expect(wrapper.emitted('completed')[0]).toEqual([
        { succeeded: 3, failed: 0, total: 3 },
      ])
    })
  })

  // ───────────────────────────────────────────
  // Phase: Error
  // ───────────────────────────────────────────
  describe('Phase: Error', () => {
    it('shows "Fehler aufgetreten" label', async () => {
      mockExecuteBatched.mockResolvedValue({
        results: [null, {}],
        errors: [{ index: 0, error: new Error('fail') }],
      })
      createWrapper({ items: makeItems(2) })

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('Fehler aufgetreten')
    })

    it('shows error count', async () => {
      mockExecuteBatched.mockResolvedValue({
        results: [null, null, {}],
        errors: [
          { index: 0, error: new Error('a') },
          { index: 1, error: new Error('b') },
        ],
      })
      createWrapper()

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('2 Fehler aufgetreten')
    })

    it('renders item names in error summary using labelKey', async () => {
      mockExecuteBatched.mockResolvedValue({
        results: [null],
        errors: [{ index: 0, error: new Error('timeout') }],
      })
      createWrapper({ items: makeItems(1), labelKey: 'name' })

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('User 1')
      expect(wrapper.text()).toContain('timeout')
    })

    it('prefers response.data.detail for error message', async () => {
      mockExecuteBatched.mockResolvedValue({
        results: [null],
        errors: [
          {
            index: 0,
            error: {
              message: 'Generic',
              response: { data: { detail: 'Benutzer nicht gefunden' } },
            },
          },
        ],
      })
      createWrapper({ items: makeItems(1) })

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('Benutzer nicht gefunden')
      expect(wrapper.text()).not.toContain('Generic')
    })

    it('shows "Unbekannter Fehler" when error has no message', async () => {
      mockExecuteBatched.mockResolvedValue({
        results: [null],
        errors: [{ index: 0, error: {} }],
      })
      createWrapper({ items: makeItems(1) })

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('Unbekannter Fehler')
    })

    it('falls back to index-based name when labelKey missing on item', async () => {
      const items = [{ id: '1' }] // no 'name' field
      mockExecuteBatched.mockResolvedValue({
        results: [null],
        errors: [{ index: 0, error: new Error('fail') }],
      })
      createWrapper({ items })

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('#1')
    })

    it('emits completed with correct counts on partial failure', async () => {
      mockExecuteBatched.mockResolvedValue({
        results: [null, {}],
        errors: [{ index: 0, error: new Error('fail') }],
      })
      createWrapper({ items: makeItems(2) })

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      expect(wrapper.emitted('completed')[0]).toEqual([
        { succeeded: 1, failed: 1, total: 2 },
      ])
    })

    it('emits completed with all failed', async () => {
      mockExecuteBatched.mockResolvedValue({
        results: [null, null],
        errors: [
          { index: 0, error: new Error('a') },
          { index: 1, error: new Error('b') },
        ],
      })
      createWrapper({ items: makeItems(2) })

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      expect(wrapper.emitted('completed')[0]).toEqual([
        { succeeded: 0, failed: 2, total: 2 },
      ])
    })
  })

  // ───────────────────────────────────────────
  // Progress Percentage
  // ───────────────────────────────────────────
  describe('Progress percentage', () => {
    it('computes 0% when total is 0', async () => {
      mockExecuteBatched.mockReturnValue(new Promise(() => {}))
      createWrapper({ items: [] })

      // Manually trigger the delete (items is empty but we test 0/0)
      wrapper.vm.handleDelete()
      await nextTick()

      expect(wrapper.text()).toContain('0%')
    })
  })

  // ───────────────────────────────────────────
  // Close Handling
  // ───────────────────────────────────────────
  describe('Close handling', () => {
    it('does not close during deleting phase', async () => {
      mockExecuteBatched.mockReturnValue(new Promise(() => {}))
      createWrapper()

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await nextTick()

      wrapper.vm.handleClose()
      await nextTick()

      expect(wrapper.emitted('update:modelValue')).toBeFalsy()
    })

    it('closes in confirming phase', async () => {
      createWrapper()

      wrapper.vm.handleClose()
      await nextTick()

      expect(wrapper.emitted('update:modelValue')[0]).toEqual([false])
    })

    it('closes in done phase', async () => {
      mockExecuteBatched.mockResolvedValue({ results: [], errors: [] })
      createWrapper()

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      wrapper.vm.handleClose()
      await nextTick()

      const emits = wrapper.emitted('update:modelValue')
      expect(emits[emits.length - 1]).toEqual([false])
    })

    it('closes in error phase', async () => {
      mockExecuteBatched.mockResolvedValue({
        results: [null],
        errors: [{ index: 0, error: new Error('x') }],
      })
      createWrapper({ items: makeItems(1) })

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      wrapper.vm.handleClose()
      await nextTick()

      const emits = wrapper.emitted('update:modelValue')
      expect(emits[emits.length - 1]).toEqual([false])
    })
  })

  // ───────────────────────────────────────────
  // Escape Key Handling
  // ───────────────────────────────────────────
  describe('Escape key handling', () => {
    it('closes on Escape in confirming phase', async () => {
      createWrapper({ modelValue: false })
      await nextTick()
      await wrapper.setProps({ modelValue: true })
      await nextTick()

      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
      await nextTick()

      const emitted = wrapper.emitted('update:modelValue')
      expect(emitted).toBeTruthy()
      expect(emitted[emitted.length - 1]).toEqual([false])
    })

    it('does not close on Escape during deleting', async () => {
      mockExecuteBatched.mockReturnValue(new Promise(() => {}))
      createWrapper({ modelValue: false })
      await nextTick()
      await wrapper.setProps({ modelValue: true })
      await nextTick()

      // Start deleting
      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await nextTick()

      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
      await nextTick()

      const emitted = wrapper.emitted('update:modelValue') || []
      const hasCloseEmit = emitted.some((e) => e[0] === false)
      expect(hasCloseEmit).toBe(false)
    })

    it('closes on Escape in done phase', async () => {
      mockExecuteBatched.mockResolvedValue({ results: [], errors: [] })
      createWrapper({ modelValue: false })
      await nextTick()
      await wrapper.setProps({ modelValue: true })
      await nextTick()

      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
      await nextTick()

      const emitted = wrapper.emitted('update:modelValue')
      expect(emitted[emitted.length - 1]).toEqual([false])
    })
  })

  // ───────────────────────────────────────────
  // Modal Open/Close Lifecycle
  // ───────────────────────────────────────────
  describe('Modal open/close lifecycle', () => {
    it('resets state when modal opens', async () => {
      mockExecuteBatched.mockResolvedValue({
        results: [null],
        errors: [{ index: 0, error: new Error('x') }],
      })
      createWrapper({ items: makeItems(1) })

      // Run a delete to enter error phase
      const deleteBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Entfernen')
      await deleteBtn.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('Fehler aufgetreten')

      // Close and reopen
      await wrapper.setProps({ modelValue: false })
      await nextTick()
      await wrapper.setProps({ modelValue: true })
      await nextTick()

      // Should be back in confirming phase
      expect(wrapper.text()).toContain('Sind Sie sicher?')
      expect(wrapper.text()).not.toContain('Fehler aufgetreten')
    })

    it('removes keydown listener when modal closes', async () => {
      const removeSpy = vi.spyOn(window, 'removeEventListener')
      createWrapper({ modelValue: true })
      await nextTick()

      await wrapper.setProps({ modelValue: false })
      await nextTick()

      expect(removeSpy).toHaveBeenCalledWith('keydown', expect.any(Function))
      removeSpy.mockRestore()
    })

    it('adds keydown listener when modal opens', async () => {
      const addSpy = vi.spyOn(window, 'addEventListener')
      createWrapper({ modelValue: false })
      await nextTick()

      await wrapper.setProps({ modelValue: true })
      await nextTick()

      expect(addSpy).toHaveBeenCalledWith('keydown', expect.any(Function))
      addSpy.mockRestore()
    })
  })
})
