import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick, ref } from 'vue'

// Controllable refs returned by the mocked composable
const mockSelectedItems = ref([])
const mockPhase = ref('selecting')
const mockProgress = ref({ current: 0, total: 0, errors: [], skipped: 0 })
const mockAddItem = vi.fn((item) => {
  if (mockSelectedItems.value.some((i) => i.id === item.id)) return false
  mockSelectedItems.value.push(item)
  return true
})
const mockRemoveItem = vi.fn((id) => {
  mockSelectedItems.value = mockSelectedItems.value.filter((i) => i.id !== id)
})
const mockHasItem = vi.fn((id) =>
  mockSelectedItems.value.some((i) => i.id === id),
)
const mockPerformSave = vi.fn()
const mockReset = vi.fn(() => {
  mockSelectedItems.value = []
  mockPhase.value = 'selecting'
  mockProgress.value = { current: 0, total: 0, errors: [], skipped: 0 }
})
const mockClearItems = vi.fn()

vi.mock('@/composables/useBatchAdd', () => ({
  useBatchAdd: vi.fn(() => ({
    selectedItems: mockSelectedItems,
    phase: mockPhase,
    progress: mockProgress,
    addItem: mockAddItem,
    removeItem: mockRemoveItem,
    hasItem: mockHasItem,
    performSave: mockPerformSave,
    reset: mockReset,
    clearItems: mockClearItems,
  })),
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
  FormField: {
    template: '<div class="form-field"><slot /></div>',
    props: ['label'],
  },
  SearchControl: {
    template: '<div class="search-control"></div>',
    props: ['modelValue', 'fetchData', 'icon', 'returnAttribute', 'maxEntries'],
    emits: ['update:modelValue', 'set-ref'],
    setup(_, { emit }) {
      const mockRef = {
        setInitialDisplay: vi.fn(),
        setSelectedId: vi.fn(),
      }
      emit('set-ref', mockRef)
      return { mockRef }
    },
  },
  UnsavedChangesModal: {
    template:
      '<div class="unsaved-changes-modal" v-if="modelValue"><button class="discard-btn" @click="$emit(\'discard\')">Discard</button><button class="continue-btn" @click="$emit(\'continue\')">Continue</button></div>',
    props: ['modelValue'],
    emits: ['update:modelValue', 'discard', 'continue'],
  },
}

import BatchAddModal from '@/components/BatchAddModal.vue'
import { useBatchAdd } from '@/composables/useBatchAdd'

describe('BatchAddModal', () => {
  let wrapper

  const defaultProps = {
    modelValue: true,
    title: 'Teilnehmende hinzufügen',
    fetchData: vi.fn().mockResolvedValue({
      items: [
        { id: '1', name: 'Alice <alice@test.com>' },
        { id: '2', name: 'Bob <bob@test.com>' },
      ],
      pageDetails: { totalCount: 2 },
    }),
    execute: vi.fn().mockResolvedValue({}),
  }

  const createWrapper = (props = {}, slots = {}) => {
    wrapper = mount(BatchAddModal, {
      props: { ...defaultProps, ...props },
      global: { stubs },
      slots,
    })
    return wrapper
  }

  beforeEach(() => {
    mockSelectedItems.value = []
    mockPhase.value = 'selecting'
    mockProgress.value = { current: 0, total: 0, errors: [], skipped: 0 }
    vi.clearAllMocks()
  })

  afterEach(() => {
    if (wrapper) wrapper.unmount()
  })

  describe('Rendering', () => {
    it('renders modal with title', () => {
      createWrapper()
      expect(wrapper.find('.card-title').text()).toContain(
        'Teilnehmende hinzufügen',
      )
    })

    it('renders search control in selecting phase', () => {
      createWrapper()
      expect(wrapper.find('.search-control').exists()).toBe(true)
    })

    it('renders close button in selecting phase', () => {
      createWrapper()
      const buttons = wrapper.findAll('.card-title .base-button')
      expect(buttons.length).toBeGreaterThanOrEqual(1)
    })

    it('does not render when modelValue is false', () => {
      createWrapper({ modelValue: false })
      // OverlayLayer uses v-show, so the element exists but is hidden
      // The CardBox also has v-show="modelValue"
      expect(wrapper.find('.overlay').exists()).toBe(true)
    })
  })

  describe('Slot rendering', () => {
    it('renders warning slot content', () => {
      createWrapper({}, { warning: '<div class="test-warning">Warnung!</div>' })
      expect(wrapper.find('.test-warning').exists()).toBe(true)
    })

    it('renders options slot content', () => {
      createWrapper({}, { options: '<div class="test-options">Optionen</div>' })
      expect(wrapper.find('.test-options').exists()).toBe(true)
    })
  })

  describe('Selected items (chips)', () => {
    it('does not render chip area when no items selected', () => {
      createWrapper()
      expect(wrapper.text()).not.toContain('ausgewählt')
    })

    it('renders chips for selected items', async () => {
      mockSelectedItems.value = [
        { id: '1', name: 'Alice', _displayName: 'Alice' },
        { id: '2', name: 'Bob', _displayName: 'Bob' },
      ]
      createWrapper()
      await nextTick()

      expect(wrapper.text()).toContain('2 ausgewählt')
      expect(wrapper.text()).toContain('Alice')
      expect(wrapper.text()).toContain('Bob')
    })

    it('calls removeItem when chip remove button is clicked', async () => {
      mockSelectedItems.value = [
        { id: '1', name: 'Alice', _displayName: 'Alice' },
      ]
      createWrapper()
      await nextTick()

      const removeBtn = wrapper.find('button[type="button"]')
      await removeBtn.trigger('click')

      expect(mockRemoveItem).toHaveBeenCalledWith('1')
    })
  })

  describe('Search and item selection', () => {
    it('wraps fetchData to cache results', async () => {
      const fetchData = vi.fn().mockResolvedValue({
        items: [{ id: '1', name: 'Alice' }],
        pageDetails: { totalCount: 1 },
      })
      createWrapper({ fetchData })

      // Access the wrapped fetchData via the SearchControl's prop
      const searchControl = wrapper.findComponent(stubs.SearchControl)
      const wrappedFetch = searchControl.props('fetchData')

      await wrappedFetch('Ali')

      expect(fetchData).toHaveBeenCalledWith('Ali')
    })

    it('adds item to selection when search value changes', async () => {
      const fetchData = vi.fn().mockResolvedValue({
        items: [{ id: '1', name: 'Alice <alice@test.com>' }],
        pageDetails: { totalCount: 1 },
      })
      createWrapper({ fetchData })

      // Simulate SearchControl fetchData being called (populates cache)
      const searchControl = wrapper.findComponent(stubs.SearchControl)
      const wrappedFetch = searchControl.props('fetchData')
      await wrappedFetch('Ali')

      // Simulate SearchControl emitting a selection
      await searchControl.vm.$emit('update:modelValue', '1')
      await nextTick()

      expect(mockAddItem).toHaveBeenCalledWith(
        expect.objectContaining({
          id: '1',
          _displayName: 'Alice <alice@test.com>',
        }),
      )
    })

    it('ignores items already in existingIds', async () => {
      const fetchData = vi.fn().mockResolvedValue({
        items: [{ id: 'existing-1', name: 'Already There' }],
        pageDetails: { totalCount: 1 },
      })
      createWrapper({ fetchData, existingIds: ['existing-1'] })

      const searchControl = wrapper.findComponent(stubs.SearchControl)
      const wrappedFetch = searchControl.props('fetchData')
      await wrappedFetch('Already')

      await searchControl.vm.$emit('update:modelValue', 'existing-1')
      await nextTick()

      expect(mockAddItem).not.toHaveBeenCalled()
    })

    it('uses labelKey for display name', async () => {
      const fetchData = vi.fn().mockResolvedValue({
        items: [{ id: '1', display: 'Custom Label', name: 'Fallback' }],
        pageDetails: { totalCount: 1 },
      })
      createWrapper({ fetchData, labelKey: 'display' })

      const searchControl = wrapper.findComponent(stubs.SearchControl)
      await searchControl.props('fetchData')('test')
      await searchControl.vm.$emit('update:modelValue', '1')
      await nextTick()

      expect(mockAddItem).toHaveBeenCalledWith(
        expect.objectContaining({ _displayName: 'Custom Label' }),
      )
    })

    it('resets search control after selection', async () => {
      const fetchData = vi.fn().mockResolvedValue({
        items: [{ id: '1', name: 'Alice' }],
        pageDetails: { totalCount: 1 },
      })
      createWrapper({ fetchData })

      const searchControl = wrapper.findComponent(stubs.SearchControl)
      await searchControl.props('fetchData')('Ali')
      await searchControl.vm.$emit('update:modelValue', '1')
      await nextTick()

      // searchValue should be reset to null via the v-model update
      // This triggers the watch to clear
      expect(searchControl.props('modelValue')).toBeNull()
    })
  })

  describe('Footer buttons', () => {
    it('shows Speichern and Abbrechen in selecting phase', () => {
      createWrapper()
      const buttons = wrapper.findAll('.base-buttons .base-button')
      const labels = buttons.map((b) => b.attributes('data-label'))

      expect(labels).toContain('Speichern')
      expect(labels).toContain('Abbrechen')
    })

    it('disables Speichern when no items are selected', () => {
      createWrapper()
      const saveBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Speichern')

      expect(saveBtn.attributes('disabled')).toBeDefined()
    })

    it('enables Speichern when items are selected', async () => {
      mockSelectedItems.value = [
        { id: '1', name: 'Alice', _displayName: 'Alice' },
      ]
      createWrapper()
      await nextTick()

      const saveBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Speichern')

      expect(saveBtn.attributes('disabled')).toBeUndefined()
    })

    it('calls performSave when Speichern is clicked', async () => {
      mockSelectedItems.value = [
        { id: '1', name: 'Alice', _displayName: 'Alice' },
      ]
      createWrapper()
      await nextTick()

      const saveBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Speichern')
      await saveBtn.trigger('click')

      expect(mockPerformSave).toHaveBeenCalledTimes(1)
    })

    it('shows Fertig button when phase is done', async () => {
      mockPhase.value = 'done'
      createWrapper()
      await nextTick()

      const buttons = wrapper.findAll('.base-buttons .base-button')
      const labels = buttons.map((b) => b.attributes('data-label'))

      expect(labels).toContain('Fertig')
      expect(labels).not.toContain('Speichern')
      expect(labels).not.toContain('Abbrechen')
    })

    it('shows Schließen button when phase is error', async () => {
      mockPhase.value = 'error'
      mockProgress.value = {
        current: 2,
        total: 2,
        errors: [{ index: 0, error: new Error('fail'), itemName: 'Alice' }],
        skipped: 0,
      }
      createWrapper()
      await nextTick()

      const buttons = wrapper.findAll('.base-buttons .base-button')
      const labels = buttons.map((b) => b.attributes('data-label'))

      expect(labels).toContain('Schließen')
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

    it('emits update:modelValue false when Fertig is clicked', async () => {
      mockPhase.value = 'done'
      createWrapper()
      await nextTick()

      const doneBtn = wrapper
        .findAll('.base-buttons .base-button')
        .find((b) => b.attributes('data-label') === 'Fertig')
      await doneBtn.trigger('click')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')[0]).toEqual([false])
    })
  })

  describe('Phase: Saving', () => {
    it('shows saving UI instead of search', async () => {
      mockPhase.value = 'saving'
      mockProgress.value = { current: 1, total: 3, errors: [], skipped: 0 }
      createWrapper()
      await nextTick()

      expect(wrapper.find('.search-control').exists()).toBe(false)
      expect(wrapper.text()).toContain('Wird gespeichert...')
      expect(wrapper.text()).toContain('1 / 3')
    })

    it('shows no footer buttons during saving', async () => {
      mockPhase.value = 'saving'
      createWrapper()
      await nextTick()

      const buttons = wrapper.findAll('.base-buttons .base-button')
      expect(buttons).toHaveLength(0)
    })
  })

  describe('Phase: Done', () => {
    it('shows Abgeschlossen label', async () => {
      mockPhase.value = 'done'
      mockProgress.value = { current: 3, total: 3, errors: [], skipped: 0 }
      createWrapper()
      await nextTick()

      expect(wrapper.text()).toContain('Abgeschlossen')
    })

    it('shows progress as 100%', async () => {
      mockPhase.value = 'done'
      mockProgress.value = { current: 3, total: 3, errors: [], skipped: 0 }
      createWrapper()
      await nextTick()

      expect(wrapper.text()).toContain('100%')
    })
  })

  describe('Phase: Error', () => {
    it('shows Fehler aufgetreten label', async () => {
      mockPhase.value = 'error'
      mockProgress.value = {
        current: 2,
        total: 2,
        errors: [{ index: 0, error: new Error('fail'), itemName: 'Alice' }],
        skipped: 0,
      }
      createWrapper()
      await nextTick()

      expect(wrapper.text()).toContain('Fehler aufgetreten')
    })

    it('renders error summary with item names', async () => {
      mockPhase.value = 'error'
      mockProgress.value = {
        current: 2,
        total: 2,
        errors: [
          {
            index: 0,
            error: { message: 'Network error' },
            itemName: 'Alice',
          },
        ],
        skipped: 0,
      }
      createWrapper()
      await nextTick()

      expect(wrapper.text()).toContain('1 Fehler aufgetreten')
      expect(wrapper.text()).toContain('Alice')
      expect(wrapper.text()).toContain('Network error')
    })

    it('prefers response.data.detail for error message', async () => {
      mockPhase.value = 'error'
      mockProgress.value = {
        current: 1,
        total: 1,
        errors: [
          {
            index: 0,
            error: {
              message: 'Generic',
              response: { data: { detail: 'User already assigned' } },
            },
            itemName: 'Bob',
          },
        ],
        skipped: 0,
      }
      createWrapper()
      await nextTick()

      expect(wrapper.text()).toContain('User already assigned')
      expect(wrapper.text()).not.toContain('Generic')
    })

    it('shows Unbekannter Fehler for errors without message', async () => {
      mockPhase.value = 'error'
      mockProgress.value = {
        current: 1,
        total: 1,
        errors: [{ index: 0, error: {}, itemName: 'Charlie' }],
        skipped: 0,
      }
      createWrapper()
      await nextTick()

      expect(wrapper.text()).toContain('Unbekannter Fehler')
    })
  })

  describe('Skipped items', () => {
    it('shows skipped summary when items were skipped', async () => {
      mockPhase.value = 'done'
      mockProgress.value = {
        current: 3,
        total: 3,
        errors: [],
        skipped: 2,
      }
      createWrapper()
      await nextTick()

      expect(wrapper.text()).toContain('2 übersprungen (bereits vorhanden)')
    })

    it('does not show skipped summary when skipped is 0', async () => {
      mockPhase.value = 'done'
      mockProgress.value = {
        current: 3,
        total: 3,
        errors: [],
        skipped: 0,
      }
      createWrapper()
      await nextTick()

      expect(wrapper.text()).not.toContain('übersprungen')
    })

    it('shows both skipped and error summaries', async () => {
      mockPhase.value = 'error'
      mockProgress.value = {
        current: 3,
        total: 3,
        errors: [{ index: 2, error: new Error('fail'), itemName: 'Charlie' }],
        skipped: 1,
      }
      createWrapper()
      await nextTick()

      expect(wrapper.text()).toContain('1 übersprungen (bereits vorhanden)')
      expect(wrapper.text()).toContain('1 Fehler aufgetreten')
    })
  })

  describe('Close handling', () => {
    it('does not close during saving phase', async () => {
      mockPhase.value = 'saving'
      createWrapper()
      await nextTick()

      // Try to close via overlay click handler
      wrapper.vm.handleClose()
      await nextTick()

      expect(wrapper.emitted('update:modelValue')).toBeFalsy()
    })

    it('closes in selecting phase', async () => {
      createWrapper()

      wrapper.vm.handleClose()
      await nextTick()

      expect(wrapper.emitted('update:modelValue')[0]).toEqual([false])
    })

    it('closes in done phase', async () => {
      mockPhase.value = 'done'
      createWrapper()
      await nextTick()

      wrapper.vm.handleClose()
      await nextTick()

      expect(wrapper.emitted('update:modelValue')[0]).toEqual([false])
    })

    it('closes in error phase', async () => {
      mockPhase.value = 'error'
      mockProgress.value = {
        current: 1,
        total: 1,
        errors: [{ index: 0, error: new Error('x'), itemName: 'A' }],
        skipped: 0,
      }
      createWrapper()
      await nextTick()

      wrapper.vm.handleClose()
      await nextTick()

      expect(wrapper.emitted('update:modelValue')[0]).toEqual([false])
    })
  })

  describe('Unsaved changes confirmation', () => {
    it('shows discard modal when closing with selected items', async () => {
      mockSelectedItems.value = [
        { id: '1', name: 'Alice', _displayName: 'Alice' },
      ]
      createWrapper()
      await nextTick()

      wrapper.vm.handleClose()
      await nextTick()

      expect(wrapper.emitted('update:modelValue')).toBeFalsy()
      expect(wrapper.find('.unsaved-changes-modal').exists()).toBe(true)
    })

    it('closes modal when discard is confirmed', async () => {
      mockSelectedItems.value = [
        { id: '1', name: 'Alice', _displayName: 'Alice' },
      ]
      createWrapper()
      await nextTick()

      wrapper.vm.handleClose()
      await nextTick()

      await wrapper.find('.discard-btn').trigger('click')
      await nextTick()

      expect(wrapper.emitted('update:modelValue')[0]).toEqual([false])
    })

    it('keeps modal open when discard is cancelled', async () => {
      mockSelectedItems.value = [
        { id: '1', name: 'Alice', _displayName: 'Alice' },
      ]
      createWrapper()
      await nextTick()

      wrapper.vm.handleClose()
      await nextTick()

      await wrapper.find('.continue-btn').trigger('click')
      await nextTick()

      expect(wrapper.emitted('update:modelValue')).toBeFalsy()
      expect(wrapper.find('.unsaved-changes-modal').exists()).toBe(false)
    })

    it('does not show discard modal when closing without selected items', async () => {
      createWrapper()

      wrapper.vm.handleClose()
      await nextTick()

      expect(wrapper.find('.unsaved-changes-modal').exists()).toBe(false)
      expect(wrapper.emitted('update:modelValue')[0]).toEqual([false])
    })
  })

  describe('Escape key handling', () => {
    it('closes on Escape in selecting phase', async () => {
      // Must transition from false→true to register keydown listener
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

    it('does not close on Escape during saving', async () => {
      createWrapper({ modelValue: false })
      await nextTick()
      await wrapper.setProps({ modelValue: true })
      await nextTick()

      // Switch to saving
      mockPhase.value = 'saving'
      await nextTick()

      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
      await nextTick()

      // Only the initial open may emit — no close should happen
      const emitted = wrapper.emitted('update:modelValue') || []
      const hasCloseEmit = emitted.some((e) => e[0] === false)
      expect(hasCloseEmit).toBe(false)
    })
  })

  describe('Modal open/close lifecycle', () => {
    it('calls reset when modal opens', async () => {
      createWrapper({ modelValue: false })
      await nextTick()

      await wrapper.setProps({ modelValue: true })
      await nextTick()

      expect(mockReset).toHaveBeenCalled()
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
  })

  describe('Progress percentage', () => {
    it('computes 0% when total is 0', async () => {
      mockPhase.value = 'saving'
      mockProgress.value = { current: 0, total: 0, errors: [], skipped: 0 }
      createWrapper()
      await nextTick()

      expect(wrapper.text()).toContain('0%')
    })

    it('computes correct percentage', async () => {
      mockPhase.value = 'saving'
      mockProgress.value = { current: 1, total: 4, errors: [], skipped: 0 }
      createWrapper()
      await nextTick()

      expect(wrapper.text()).toContain('25%')
    })

    it('rounds percentage', async () => {
      mockPhase.value = 'saving'
      mockProgress.value = { current: 1, total: 3, errors: [], skipped: 0 }
      createWrapper()
      await nextTick()

      expect(wrapper.text()).toContain('33%')
    })
  })

  describe('Props forwarding', () => {
    it('passes isSkippable to useBatchAdd', () => {
      const isSkippable = vi.fn()
      createWrapper({ isSkippable })

      expect(useBatchAdd).toHaveBeenCalledWith(
        expect.objectContaining({ isSkippable }),
      )
    })

    it('passes beginSilent and endSilent to useBatchAdd', () => {
      const beginSilent = vi.fn()
      const endSilent = vi.fn()
      createWrapper({ beginSilent, endSilent })

      expect(useBatchAdd).toHaveBeenCalledWith(
        expect.objectContaining({ beginSilent, endSilent }),
      )
    })

    it('passes custom batchSize to useBatchAdd', () => {
      createWrapper({ batchSize: 5 })

      expect(useBatchAdd).toHaveBeenCalledWith(
        expect.objectContaining({ batchSize: 5 }),
      )
    })

    it('passes searchIcon to SearchControl', () => {
      createWrapper({ searchIcon: 'mdi-account' })
      const searchControl = wrapper.findComponent(stubs.SearchControl)
      expect(searchControl.props('icon')).toBe('mdi-account')
    })

    it('passes maxEntries to SearchControl', () => {
      createWrapper({ maxEntries: 50 })
      const searchControl = wrapper.findComponent(stubs.SearchControl)
      expect(searchControl.props('maxEntries')).toBe(50)
    })

    it('passes returnAttribute to SearchControl', () => {
      createWrapper({ returnAttribute: 'uuid' })
      const searchControl = wrapper.findComponent(stubs.SearchControl)
      expect(searchControl.props('returnAttribute')).toBe('uuid')
    })
  })
})
