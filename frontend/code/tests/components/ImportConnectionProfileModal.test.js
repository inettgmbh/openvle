import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/services', () => ({
  default: {
    beginSilent: vi.fn(),
    endSilent: vi.fn(),
    connections: {
      get: vi.fn(),
      listByObject: vi.fn(),
      clone: vi.fn().mockResolvedValue({ id: 'cloned-1' }),
    },
    vms: {
      searchVMsAndTemplates: vi.fn(),
      getVMOrTemplateName: vi.fn(),
    },
  },
}))

vi.mock('vue-toastification', () => ({
  useToast: () => ({
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
  }),
}))

import ImportConnectionProfileModal from '@/components/ImportConnectionProfileModal.vue'
import backend from '@/services'

const PROFILE = {
  id: 'src-1',
  port: 3389,
  protocol: 'rdp',
  username: 'alice',
  objectId: 'src-vm',
  objectType: 'VirtualMachine',
}

describe('ImportConnectionProfileModal', () => {
  let wrapper

  const mountModal = (props = {}) =>
    mount(ImportConnectionProfileModal, {
      props: {
        modelValue: false,
        targetObjectType: 'VirtualMachine',
        targetObjectId: 'target-vm-1',
        ...props,
      },
      global: {
        stubs: {
          CardBoxModal: {
            name: 'CardBoxModal',
            props: ['modelValue', 'title', 'disabled', 'buttonLabel'],
            emits: ['update:modelValue', 'form-submitted'],
            template:
              '<div class="cb-modal"><slot /><button class="cb-submit" :disabled="disabled" @click="$emit(\'form-submitted\')">submit</button></div>',
          },
          SearchControl: {
            name: 'SearchControl',
            props: ['modelValue'],
            emits: ['update:modelValue', 'input-started'],
            template: '<input class="src-input" />',
          },
          FormField: { template: '<div><slot /></div>' },
          FormControl: {
            props: ['modelValue'],
            emits: ['update:modelValue'],
            template: '<input />',
          },
          BaseIcon: { template: '<svg />' },
        },
      },
    })

  const openModal = async (w) => {
    await w.setProps({ modelValue: true })
    await flushPromises()
  }

  const pickTarget = async (w, ident) => {
    w.findComponent({ name: 'SearchControl' }).vm.$emit(
      'update:modelValue',
      ident,
    )
    await flushPromises()
  }

  beforeEach(() => {
    vi.clearAllMocks()
    backend.connections.listByObject.mockResolvedValue({
      items: [],
      pageDetails: { totalCount: 0 },
    })
    backend.connections.get.mockResolvedValue(PROFILE)
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
      wrapper = null
    }
  })

  it('loads existing protocols of the target on open', async () => {
    wrapper = mountModal()
    await openModal(wrapper)
    expect(backend.connections.listByObject).toHaveBeenCalledWith(
      'VirtualMachine',
      'target-vm-1',
      expect.any(Object),
    )
  })

  it('auto-selects the only profile when source target has exactly one', async () => {
    backend.connections.listByObject
      .mockResolvedValueOnce({ items: [], pageDetails: { totalCount: 0 } })
      .mockResolvedValueOnce({
        items: [PROFILE],
        pageDetails: { totalCount: 1 },
      })
    backend.connections.get.mockResolvedValue(PROFILE)

    wrapper = mountModal()
    await openModal(wrapper)
    await pickTarget(wrapper, { id: 'src-vm', type: 'VirtualMachine' })

    expect(backend.connections.listByObject).toHaveBeenLastCalledWith(
      'VirtualMachine',
      'src-vm',
      expect.any(Object),
    )
    expect(backend.connections.get).toHaveBeenCalledWith('src-1')
  })

  it('does not auto-select when source target has multiple profiles', async () => {
    const second = { ...PROFILE, id: 'src-2', protocol: 'ssh', port: 22 }
    backend.connections.listByObject
      .mockResolvedValueOnce({ items: [], pageDetails: { totalCount: 0 } })
      .mockResolvedValueOnce({
        items: [PROFILE, second],
        pageDetails: { totalCount: 2 },
      })

    wrapper = mountModal()
    await openModal(wrapper)
    await pickTarget(wrapper, { id: 'src-vm', type: 'VirtualMachine' })

    expect(backend.connections.get).not.toHaveBeenCalled()
    expect(wrapper.findAll('input[type="radio"]')).toHaveLength(2)
  })

  it('submits clone with source id + target context + form fields', async () => {
    backend.connections.listByObject
      .mockResolvedValueOnce({ items: [], pageDetails: { totalCount: 0 } })
      .mockResolvedValueOnce({
        items: [PROFILE],
        pageDetails: { totalCount: 1 },
      })

    wrapper = mountModal()
    await openModal(wrapper)
    await pickTarget(wrapper, { id: 'src-vm', type: 'VirtualMachine' })

    await wrapper.find('.cb-submit').trigger('click')
    await flushPromises()

    expect(backend.connections.clone).toHaveBeenCalledWith(
      'src-1',
      expect.objectContaining({
        objectId: 'target-vm-1',
        objectType: 'VirtualMachine',
        protocol: 'rdp',
        port: 3389,
        username: 'alice',
      }),
    )
  })

  it('emits imported and closes modal after successful clone', async () => {
    backend.connections.listByObject
      .mockResolvedValueOnce({ items: [], pageDetails: { totalCount: 0 } })
      .mockResolvedValueOnce({
        items: [PROFILE],
        pageDetails: { totalCount: 1 },
      })

    wrapper = mountModal()
    await openModal(wrapper)
    await pickTarget(wrapper, { id: 'src-vm', type: 'VirtualMachine' })

    await wrapper.find('.cb-submit').trigger('click')
    await flushPromises()

    expect(wrapper.emitted('imported')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')?.at(-1)?.[0]).toBe(false)
  })

  it('clears source protocol and shows collision hint when target already uses it', async () => {
    backend.connections.listByObject
      .mockResolvedValueOnce({
        items: [{ protocol: 'rdp' }],
        pageDetails: { totalCount: 1 },
      })
      .mockResolvedValueOnce({
        items: [PROFILE],
        pageDetails: { totalCount: 1 },
      })

    wrapper = mountModal()
    await openModal(wrapper)
    await pickTarget(wrapper, { id: 'src-vm', type: 'VirtualMachine' })

    expect(wrapper.text()).toContain('[RDP]')
    expect(wrapper.text()).toContain('bereits vergeben')

    await wrapper.find('.cb-submit').trigger('click')
    await flushPromises()

    expect(backend.connections.clone).not.toHaveBeenCalled()
  })

  it('shows hint when source target has no profiles', async () => {
    backend.connections.listByObject
      .mockResolvedValueOnce({ items: [], pageDetails: { totalCount: 0 } })
      .mockResolvedValueOnce({ items: [], pageDetails: { totalCount: 0 } })

    wrapper = mountModal()
    await openModal(wrapper)
    await pickTarget(wrapper, { id: 'src-vm', type: 'VirtualMachine' })

    expect(wrapper.text()).toContain('keine Verbindungsvorlagen')
    expect(wrapper.findAll('input[type="radio"]')).toHaveLength(0)
    expect(backend.connections.get).not.toHaveBeenCalled()
  })

  it('resets state when modal closes and reopens', async () => {
    backend.connections.listByObject
      .mockResolvedValueOnce({ items: [], pageDetails: { totalCount: 0 } })
      .mockResolvedValueOnce({
        items: [PROFILE],
        pageDetails: { totalCount: 1 },
      })

    wrapper = mountModal()
    await openModal(wrapper)
    await pickTarget(wrapper, { id: 'src-vm', type: 'VirtualMachine' })

    await wrapper.setProps({ modelValue: false })
    await flushPromises()

    backend.connections.listByObject.mockClear()
    backend.connections.listByObject.mockResolvedValue({
      items: [],
      pageDetails: { totalCount: 0 },
    })
    backend.connections.get.mockClear()

    await wrapper.setProps({ modelValue: true })
    await flushPromises()

    expect(backend.connections.listByObject).toHaveBeenCalledTimes(1)
    expect(backend.connections.get).not.toHaveBeenCalled()
  })
})
