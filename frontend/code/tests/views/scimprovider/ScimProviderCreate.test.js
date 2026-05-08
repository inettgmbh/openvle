import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

// Use vi.hoisted to define mocks that can be referenced in vi.mock (which is hoisted)
const { mockCreateProvider } = vi.hoisted(() => ({
  mockCreateProvider: vi.fn().mockResolvedValue({
    id: 'provider-123',
    name: 'Test Provider',
    bearer_token: 'generated-token-abc123',
  }),
}))

// Mock the backend singleton
vi.mock('@/services', () => ({
  default: {
    scimProviders: {
      create: mockCreateProvider,
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
  ScimTokenModal: {
    template: '<div class="token-modal" />',
    props: ['modelValue', 'token'],
  },
}

import ScimProviderCreate from '@/views/scimprovider/ScimProviderCreate.vue'

describe('ScimProviderCreate', () => {
  let wrapper

  const createWrapper = async () => {
    wrapper = mount(ScimProviderCreate, {
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
    it('disables submit button when name is empty', async () => {
      await createWrapper()
      const submitButton = wrapper.find('button[type="submit"]')
      expect(submitButton.attributes('disabled')).toBeDefined()
    })

    it('enables submit button when name is filled', async () => {
      await createWrapper()
      wrapper.vm.provider.name = 'Authentik'
      await flushPromises()
      const submitButton = wrapper.find('button[type="submit"]')
      expect(submitButton.attributes('disabled')).toBeUndefined()
    })
  })

  describe('Submission', () => {
    it('calls create with correct payload on submit', async () => {
      await createWrapper()

      wrapper.vm.provider.name = 'Authentik'
      wrapper.vm.provider.description = 'Authentik provider'
      wrapper.vm.provider.enabled = true
      wrapper.vm.provider.default_user_status = 'Active'

      await wrapper.vm.submit()
      await flushPromises()

      expect(mockCreateProvider).toHaveBeenCalledWith({
        name: 'Authentik',
        description: 'Authentik provider',
        enabled: true,
        default_user_status: 'Active',
      })
    })

    it('shows error toast on failure', async () => {
      mockCreateProvider.mockRejectedValueOnce(new Error('Server error'))
      await createWrapper()

      wrapper.vm.provider.name = 'Test'

      await wrapper.vm.submit()
      await flushPromises()

      const { useToast } = await import('vue-toastification')
      const toast = useToast()
      expect(toast.error).toHaveBeenCalledWith(
        'SCIM Provider konnte nicht angelegt werden',
      )
    })
  })
})
