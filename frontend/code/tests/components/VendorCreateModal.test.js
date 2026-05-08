import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

const { mockCreate, mockFetchPermissions } = vi.hoisted(() => ({
  mockCreate: vi.fn().mockResolvedValue({
    id: 'new-vendor-id',
    name: 'Neuer Hersteller',
  }),
  mockFetchPermissions: vi.fn(),
}))

vi.mock('@/services', () => ({
  default: {
    vendors: {
      create: mockCreate,
    },
  },
}))

vi.mock('@/stores/main', () => ({
  useMainStore: vi.fn().mockReturnValue({
    fetchPermissions: mockFetchPermissions,
  }),
}))

vi.mock('vue-toastification', () => ({
  useToast: vi.fn().mockReturnValue({
    success: vi.fn(),
    error: vi.fn(),
  }),
}))

const stubs = {
  CardBoxModal: {
    template: `
      <div class="modal" v-if="modelValue">
        <slot />
        <button class="submit-btn" :disabled="disabled" @click="$emit('form-submitted')">Submit</button>
        <button class="cancel-btn" @click="$emit('cancel')">Cancel</button>
      </div>
    `,
    props: [
      'modelValue',
      'title',
      'button',
      'hasCancel',
      'buttonLabel',
      'disabled',
    ],
    emits: ['update:modelValue', 'form-submitted', 'cancel'],
  },
  FormField: {
    template: '<div class="form-field"><slot /></div>',
  },
  FormControl: {
    template:
      '<input class="form-control" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
    props: ['modelValue', 'icon', 'placeholder', 'required'],
    emits: ['update:modelValue', 'set-ref'],
  },
}

import VendorCreateModal from '@/components/VendorCreateModal.vue'

describe('VendorCreateModal', () => {
  let wrapper

  const createWrapper = (props = {}) => {
    wrapper = mount(VendorCreateModal, {
      props: {
        modelValue: true,
        ...props,
      },
      global: { stubs },
    })
    return wrapper
  }

  afterEach(() => {
    if (wrapper) wrapper.unmount()
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders when modelValue is true', () => {
      createWrapper()
      expect(wrapper.find('.modal').exists()).toBe(true)
    })

    it('does not render when modelValue is false', () => {
      createWrapper({ modelValue: false })
      expect(wrapper.find('.modal').exists()).toBe(false)
    })

    it('renders name and description form fields', () => {
      createWrapper()
      const fields = wrapper.findAll('.form-field')
      expect(fields).toHaveLength(2)
    })
  })

  describe('Submit button disabled state', () => {
    it('disables submit when name is empty', () => {
      createWrapper()
      const btn = wrapper.find('.submit-btn')
      expect(btn.attributes('disabled')).toBeDefined()
    })

    it('enables submit when name is filled', async () => {
      createWrapper()
      const inputs = wrapper.findAll('.form-control')
      await inputs[0].setValue('Test Vendor')
      await nextTick()

      const btn = wrapper.find('.submit-btn')
      expect(btn.attributes('disabled')).toBeUndefined()
    })
  })

  describe('Form submission', () => {
    it('calls backend.vendors.create with name and description', async () => {
      createWrapper()
      const inputs = wrapper.findAll('.form-control')
      await inputs[0].setValue('Neuer Hersteller')
      await inputs[1].setValue('Beschreibung')
      await nextTick()

      await wrapper.find('.submit-btn').trigger('click')
      await flushPromises()

      expect(mockCreate).toHaveBeenCalledWith({
        name: 'Neuer Hersteller',
        description: 'Beschreibung',
      })
    })

    it('calls backend.vendors.create without description when empty', async () => {
      createWrapper()
      const inputs = wrapper.findAll('.form-control')
      await inputs[0].setValue('Nur Name')
      await nextTick()

      await wrapper.find('.submit-btn').trigger('click')
      await flushPromises()

      expect(mockCreate).toHaveBeenCalledWith({
        name: 'Nur Name',
        description: undefined,
      })
    })

    it('emits created with id and name on success', async () => {
      createWrapper()
      const inputs = wrapper.findAll('.form-control')
      await inputs[0].setValue('Neuer Hersteller')
      await nextTick()

      await wrapper.find('.submit-btn').trigger('click')
      await flushPromises()

      expect(wrapper.emitted('created')).toBeTruthy()
      expect(wrapper.emitted('created')[0]).toEqual([
        { id: 'new-vendor-id', name: 'Neuer Hersteller' },
      ])
    })

    it('emits update:modelValue false to close modal on success', async () => {
      createWrapper()
      const inputs = wrapper.findAll('.form-control')
      await inputs[0].setValue('Test')
      await nextTick()

      await wrapper.find('.submit-btn').trigger('click')
      await flushPromises()

      const emitted = wrapper.emitted('update:modelValue')
      expect(emitted[emitted.length - 1]).toEqual([false])
    })

    it('calls fetchPermissions on success', async () => {
      createWrapper()
      const inputs = wrapper.findAll('.form-control')
      await inputs[0].setValue('Test')
      await nextTick()

      await wrapper.find('.submit-btn').trigger('click')
      await flushPromises()

      expect(mockFetchPermissions).toHaveBeenCalled()
    })

    it('does not emit created on API error', async () => {
      mockCreate.mockRejectedValueOnce(new Error('API Error'))
      createWrapper()
      const inputs = wrapper.findAll('.form-control')
      await inputs[0].setValue('Test')
      await nextTick()

      await wrapper.find('.submit-btn').trigger('click')
      await flushPromises()

      expect(wrapper.emitted('created')).toBeFalsy()
    })

    it('does not submit when name is only whitespace', async () => {
      createWrapper()
      const inputs = wrapper.findAll('.form-control')
      await inputs[0].setValue('   ')
      await nextTick()

      await wrapper.find('.submit-btn').trigger('click')
      await flushPromises()

      expect(mockCreate).not.toHaveBeenCalled()
    })

    it('trims name before sending', async () => {
      createWrapper()
      const inputs = wrapper.findAll('.form-control')
      await inputs[0].setValue('  Trimmed Name  ')
      await nextTick()

      await wrapper.find('.submit-btn').trigger('click')
      await flushPromises()

      expect(mockCreate).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'Trimmed Name' }),
      )
    })
  })

  describe('Form reset', () => {
    it('resets form fields when modal reopens', async () => {
      createWrapper()
      const inputs = wrapper.findAll('.form-control')
      await inputs[0].setValue('Dirty Name')
      await inputs[1].setValue('Dirty Description')

      await wrapper.setProps({ modelValue: false })
      await wrapper.setProps({ modelValue: true })
      await nextTick()

      expect(wrapper.vm.name).toBe('')
      expect(wrapper.vm.description).toBe('')
    })

    it('resets form fields on cancel', async () => {
      createWrapper()
      const inputs = wrapper.findAll('.form-control')
      await inputs[0].setValue('Dirty Name')
      await nextTick()

      await wrapper.find('.cancel-btn').trigger('click')
      await nextTick()

      expect(wrapper.vm.name).toBe('')
      expect(wrapper.vm.description).toBe('')
    })
  })
})
