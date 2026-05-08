import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

// Use vi.hoisted to define mocks that can be referenced in vi.mock (which is hoisted)
const { mockCreateClient } = vi.hoisted(() => ({
  mockCreateClient: vi.fn().mockResolvedValue({
    id: 'client-123',
    name: 'Test Client',
  }),
}))

// Mock the backend singleton
vi.mock('@/services', () => ({
  default: {
    scimClients: {
      create: mockCreateClient,
    },
  },
}))

vi.mock('@/router', () => ({
  default: {
    push: vi.fn(),
    back: vi.fn(),
  },
}))

vi.mock('vue-router', () => ({
  useRoute: vi.fn().mockReturnValue({
    query: {},
  }),
  onBeforeRouteLeave: vi.fn(),
}))

vi.mock('vue-toastification', () => ({
  useToast: vi.fn().mockReturnValue({
    success: vi.fn(),
    error: vi.fn(),
  }),
}))

// Stub all child components
const stubs = {
  LayoutAuthenticated: {
    template: '<div class="layout"><slot /></div>',
  },
  SectionMain: {
    template: '<div class="section-main"><slot /></div>',
  },
  SectionTitleLineWithButton: {
    template: '<div class="section-title" />',
  },
  CardBox: {
    template:
      '<form class="card-box" @submit.prevent="$emit(\'submit\')"><slot /><slot name="footer" /></form>',
  },
  FormField: {
    template: '<div class="form-field"><slot /></div>',
  },
  FormControl: {
    template:
      '<input class="form-control" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
    props: ['modelValue', 'icon', 'placeholder', 'required', 'type', 'options'],
  },
  BaseButton: {
    template:
      '<button class="base-button" :type="type" :disabled="disabled">{{ label }}</button>',
    props: ['type', 'color', 'label', 'disabled', 'outline'],
  },
  BaseButtons: {
    template: '<div class="base-buttons"><slot /></div>',
  },
  BaseIcon: {
    template: '<i class="base-icon" />',
    props: ['path', 'size'],
  },
  UnsavedChangesModal: {
    template: '<div class="unsaved-modal" />',
  },
}

import ScimClientCreate from '@/views/scimclient/ScimClientCreate.vue'

describe('ScimClientCreate', () => {
  let wrapper

  const createWrapper = async () => {
    wrapper = mount(ScimClientCreate, {
      global: {
        stubs,
      },
    })
    await flushPromises()
    return wrapper
  }

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders the form', async () => {
      await createWrapper()
      expect(wrapper.find('.card-box').exists()).toBe(true)
    })

    it('renders submit button', async () => {
      await createWrapper()
      const submitButton = wrapper.find('button[type="submit"]')
      expect(submitButton.exists()).toBe(true)
      expect(submitButton.text()).toBe('Hinzufügen')
    })

    it('renders cancel button', async () => {
      await createWrapper()
      const buttons = wrapper.findAll('.base-button')
      const cancelButton = buttons.find((b) => b.text() === 'Abbrechen')
      expect(cancelButton).toBeDefined()
    })
  })

  describe('Validation', () => {
    it('disables submit button when required fields are empty', async () => {
      await createWrapper()
      const submitButton = wrapper.find('button[type="submit"]')
      expect(submitButton.attributes('disabled')).toBeDefined()
    })

    it('enables submit button when all required fields are filled', async () => {
      await createWrapper()
      wrapper.vm.client.name = 'External LMS'
      wrapper.vm.client.endpoint_url = 'https://example.com/scim/v2'
      wrapper.vm.client.bearer_token = 'my-token'
      await flushPromises()
      const submitButton = wrapper.find('button[type="submit"]')
      expect(submitButton.attributes('disabled')).toBeUndefined()
    })

    it('keeps submit disabled with invalid URL', async () => {
      await createWrapper()
      wrapper.vm.client.name = 'External LMS'
      wrapper.vm.client.endpoint_url = 'not-a-url'
      wrapper.vm.client.bearer_token = 'my-token'
      await flushPromises()
      const submitButton = wrapper.find('button[type="submit"]')
      expect(submitButton.attributes('disabled')).toBeDefined()
    })
  })

  describe('Submission', () => {
    it('calls create with correct payload on submit', async () => {
      await createWrapper()

      wrapper.vm.client.name = 'External LMS'
      wrapper.vm.client.description = 'LMS client'
      wrapper.vm.client.enabled = true
      wrapper.vm.client.endpoint_url = 'https://lms.example.com/scim/v2'
      wrapper.vm.client.bearer_token = 'my-token'
      wrapper.vm.client.sync_groups = true

      await wrapper.vm.submit()
      await flushPromises()

      expect(mockCreateClient).toHaveBeenCalledWith({
        name: 'External LMS',
        description: 'LMS client',
        enabled: true,
        endpoint_url: 'https://lms.example.com/scim/v2',
        bearer_token: 'my-token',
        sync_groups: true,
      })
    })

    it('navigates to detail on success', async () => {
      await createWrapper()

      wrapper.vm.client.name = 'Test'
      wrapper.vm.client.endpoint_url = 'https://example.com/scim'
      wrapper.vm.client.bearer_token = 'token'

      await wrapper.vm.submit()
      await flushPromises()

      const router = (await import('@/router')).default
      expect(router.push).toHaveBeenCalledWith({
        path: '/scim/clients/client-123',
      })
    })

    it('shows error toast on failure', async () => {
      mockCreateClient.mockRejectedValueOnce(new Error('Server error'))
      await createWrapper()

      wrapper.vm.client.name = 'Test'
      wrapper.vm.client.endpoint_url = 'https://example.com/scim'
      wrapper.vm.client.bearer_token = 'token'

      await wrapper.vm.submit()
      await flushPromises()

      const { useToast } = await import('vue-toastification')
      const toast = useToast()
      expect(toast.error).toHaveBeenCalledWith(
        'SCIM Client konnte nicht angelegt werden',
      )
    })
  })
})
