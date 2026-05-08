import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import SearchControl from '@/components/SearchControl.vue'

vi.mock('@/components/FormControlIcon.vue', () => ({
  default: {
    name: 'FormControlIcon',
    template: '<span class="form-control-icon"></span>',
    props: ['icon', 'h'],
  },
}))

// External spies that the mock SearchField calls
const setInitialDisplaySpy = vi.fn()
const setSelectedIdSpy = vi.fn()

vi.mock('@/components/SearchField.vue', () => ({
  default: {
    name: 'SearchField',
    template: '<div class="search-field-mock"></div>',
    props: [
      'id',
      'allowCustomEntry',
      'borders',
      'formatter',
      'fetchData',
      'maxEntries',
      'labelAttribute',
      'returnAttribute',
      'placeholder',
      'required',
      'autofocus',
      'icon',
      'disabled',
      'ariaDescribedby',
      'maxlength',
    ],
    setup() {
      return {
        setInitialDisplay: (...args) => setInitialDisplaySpy(...args),
        setSelectedId: (...args) => setSelectedIdSpy(...args),
        reset: vi.fn(),
        focus: vi.fn(),
      }
    },
  },
}))

vi.mock('@/stores/style.js', () => ({
  useStyleStore: () => ({ darkMode: false }),
}))

const LONG_UUID = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
const SHORT_ID = 'abc'

describe('SearchControl', () => {
  const fetchData = vi.fn()

  beforeEach(() => {
    setInitialDisplaySpy.mockClear()
    setSelectedIdSpy.mockClear()
  })

  const createWrapper = (props = {}) => {
    return mount(SearchControl, {
      props: {
        fetchData,
        ...props,
      },
      global: {
        directives: {
          tooltip: () => {},
        },
      },
    })
  }

  describe('loadSelectedLabel – success', () => {
    it('displays the fetched label', async () => {
      const fetchSelected = vi.fn().mockResolvedValue('Vendor ABC')

      createWrapper({
        modelValue: LONG_UUID,
        fetchSelected,
      })
      await flushPromises()

      expect(fetchSelected).toHaveBeenCalledWith(LONG_UUID)
      expect(setInitialDisplaySpy).toHaveBeenCalledWith('Vendor ABC')
      expect(setSelectedIdSpy).toHaveBeenCalledWith(LONG_UUID)
    })

    it('does nothing when fetchSelected returns falsy', async () => {
      const fetchSelected = vi.fn().mockResolvedValue(null)

      createWrapper({
        modelValue: LONG_UUID,
        fetchSelected,
      })
      await flushPromises()

      expect(setInitialDisplaySpy).not.toHaveBeenCalled()
      expect(setSelectedIdSpy).not.toHaveBeenCalled()
    })
  })

  describe('loadSelectedLabel – error fallback', () => {
    it('shows truncated UUID with hint on fetch error', async () => {
      const fetchSelected = vi
        .fn()
        .mockRejectedValue(new Error('Request failed with status code 403'))

      createWrapper({
        modelValue: LONG_UUID,
        fetchSelected,
      })
      await flushPromises()

      expect(setInitialDisplaySpy).toHaveBeenCalledWith(
        'a1b2c3d4... (keine Berechtigung)',
      )
      expect(setSelectedIdSpy).toHaveBeenCalledWith(LONG_UUID)
    })

    it('shows full short ID with hint when ID <= 8 chars', async () => {
      const fetchSelected = vi.fn().mockRejectedValue(new Error('403'))

      createWrapper({
        modelValue: SHORT_ID,
        fetchSelected,
      })
      await flushPromises()

      expect(setInitialDisplaySpy).toHaveBeenCalledWith(
        'abc (keine Berechtigung)',
      )
    })

    it('preserves full UUID in localValue for form submission', async () => {
      const fetchSelected = vi.fn().mockRejectedValue(new Error('403'))

      const wrapper = createWrapper({
        name: 'vendor_id',
        modelValue: LONG_UUID,
        fetchSelected,
      })
      await flushPromises()

      const hiddenInput = wrapper.find('input[type="hidden"]')
      expect(hiddenInput.exists()).toBe(true)
      expect(hiddenInput.element.value).toBe(LONG_UUID)
    })

    it('sets selectedId so required validation passes', async () => {
      const fetchSelected = vi.fn().mockRejectedValue(new Error('403'))

      createWrapper({
        modelValue: LONG_UUID,
        fetchSelected,
      })
      await flushPromises()

      expect(setSelectedIdSpy).toHaveBeenCalledWith(LONG_UUID)
    })
  })

  describe('loadSelectedLabel – guard clauses', () => {
    it('does not call fetchSelected when no modelValue', async () => {
      const fetchSelected = vi.fn()

      createWrapper({
        modelValue: null,
        fetchSelected,
      })
      await flushPromises()

      expect(fetchSelected).not.toHaveBeenCalled()
    })

    it('does not call fetchSelected when prop is not provided', async () => {
      createWrapper({
        modelValue: LONG_UUID,
      })
      await flushPromises()

      expect(setInitialDisplaySpy).not.toHaveBeenCalled()
    })
  })

  describe('modelValue watch', () => {
    it('loads label when modelValue changes from null to a value', async () => {
      const fetchSelected = vi.fn().mockResolvedValue('New Vendor')

      const wrapper = createWrapper({
        modelValue: null,
        fetchSelected,
      })
      await flushPromises()

      expect(fetchSelected).not.toHaveBeenCalled()

      await wrapper.setProps({ modelValue: LONG_UUID })
      await flushPromises()

      expect(fetchSelected).toHaveBeenCalledWith(LONG_UUID)
      expect(setInitialDisplaySpy).toHaveBeenCalledWith('New Vendor')
    })

    it('shows fallback when modelValue changes and fetch fails', async () => {
      const fetchSelected = vi.fn().mockRejectedValue(new Error('403'))

      const wrapper = createWrapper({
        modelValue: null,
        fetchSelected,
      })
      await flushPromises()

      await wrapper.setProps({ modelValue: LONG_UUID })
      await flushPromises()

      expect(setInitialDisplaySpy).toHaveBeenCalledWith(
        'a1b2c3d4... (keine Berechtigung)',
      )
      expect(setSelectedIdSpy).toHaveBeenCalledWith(LONG_UUID)
    })
  })

  describe('hidden input', () => {
    it('renders hidden input with name prop and value', async () => {
      const wrapper = createWrapper({
        name: 'vendor_id',
        modelValue: LONG_UUID,
        fetchSelected: vi.fn().mockResolvedValue('Vendor'),
      })
      await flushPromises()

      const hiddenInput = wrapper.find('input[type="hidden"]')
      expect(hiddenInput.exists()).toBe(true)
      expect(hiddenInput.attributes('name')).toBe('vendor_id')
      expect(hiddenInput.element.value).toBe(LONG_UUID)
    })

    it('does not render hidden input without name prop', () => {
      const wrapper = createWrapper()

      expect(wrapper.find('input[type="hidden"]').exists()).toBe(false)
    })
  })
})
