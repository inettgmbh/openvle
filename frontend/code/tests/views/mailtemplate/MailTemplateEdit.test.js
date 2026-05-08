import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

// Use vi.hoisted to define mocks that can be referenced in vi.mock (which is hoisted)
const {
  mockGetMailTemplate,
  mockUpdateMailTemplate,
  mockFetchMailActionsDropdown,
} = vi.hoisted(() => ({
  mockGetMailTemplate: vi.fn().mockResolvedValue({
    id: 'template-123',
    name: 'Existing Template',
    subject: 'Test Subject',
    description: 'Test Description',
    contentHTML: '<p>Hello {{ user.name }}</p>',
    replyTo: 'reply@test.com',
    mail_action: 'action-1',
    language: 'lang-1',
  }),
  mockUpdateMailTemplate: vi.fn().mockResolvedValue({
    id: 'template-123',
    name: 'Updated Template',
  }),
  mockFetchMailActionsDropdown: vi.fn().mockResolvedValue([
    { label: 'Events Action', value: 'action-1', slug: 'events_test' },
    { label: 'VM Action', value: 'action-2', slug: 'vm_test' },
  ]),
}))

// Mock the backend singleton
vi.mock('@/services', () => ({
  default: {
    mailTemplates: {
      getMailTemplate: mockGetMailTemplate,
      get: mockGetMailTemplate,
      updateMailTemplate: mockUpdateMailTemplate,
      update: mockUpdateMailTemplate,
    },
    mailActions: {
      fetchMailActionsDropdown: mockFetchMailActionsDropdown,
      dropdown: mockFetchMailActionsDropdown,
    },
  },
}))

vi.mock('@/stores/lookup', () => ({
  useLookupStore: vi.fn().mockReturnValue({
    fetchAll: vi.fn(),
    updateFromObject: vi.fn(),
    languages: {
      'lang-1': { name: 'German', key: 'de' },
      'lang-2': { name: 'English', key: 'en' },
    },
  }),
}))

vi.mock('@/router', () => ({
  default: {
    push: vi.fn(),
    back: vi.fn(),
  },
}))

vi.mock('vue-router', () => ({
  useRoute: vi.fn().mockReturnValue({
    params: { id: 'template-123' },
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
    props: [
      'modelValue',
      'icon',
      'placeholder',
      'required',
      'type',
      'options',
      'resize',
      'rows',
    ],
  },
  BaseDivider: {
    template: '<hr />',
  },
  BaseButton: {
    template:
      '<button class="base-button" :type="type" :disabled="disabled">{{ label }}</button>',
    props: ['type', 'color', 'label', 'disabled', 'outline'],
  },
  BaseButtons: {
    template: '<div class="base-buttons"><slot /></div>',
  },
  BaseMarkdown: {
    template:
      '<div class="base-markdown"><textarea :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" /></div>',
    props: ['modelValue', 'action'],
  },
  NotificationBar: {
    template:
      '<div class="notification-bar" v-if="$slots.default"><slot /></div>',
    props: ['color', 'icon', 'dismissable'],
  },
}

import MailTemplateEdit from '@/views/mailtemplate/MailTemplateEdit.vue'

describe('MailTemplateEdit', () => {
  let wrapper

  const createWrapper = async () => {
    wrapper = mount(MailTemplateEdit, {
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

    it('renders submit button with Speichern label', async () => {
      await createWrapper()
      const submitButton = wrapper.find('button[type="submit"]')
      expect(submitButton.exists()).toBe(true)
      expect(submitButton.text()).toBe('Speichern')
    })

    it('renders cancel button', async () => {
      await createWrapper()
      const buttons = wrapper.findAll('.base-button')
      const cancelButton = buttons.find((b) => b.text() === 'Abbrechen')
      expect(cancelButton).toBeDefined()
    })
  })

  describe('Data Loading', () => {
    it('fetches mail template on mount', async () => {
      await createWrapper()
      expect(mockGetMailTemplate).toHaveBeenCalledWith('template-123')
    })

    it('populates form with loaded data', async () => {
      await createWrapper()
      expect(wrapper.vm.mailTemplate.name).toBe('Existing Template')
      expect(wrapper.vm.mailTemplate.subject).toBe('Test Subject')
      expect(wrapper.vm.mailTemplate.mail_action).toBe('action-1')
    })
  })

  describe('Validation', () => {
    it('submit button is enabled when content is valid', async () => {
      await createWrapper()
      const submitButton = wrapper.find('button[type="submit"]')
      expect(submitButton.attributes('disabled')).toBeUndefined()
    })

    it('disables submit button when placeholders are invalid', async () => {
      await createWrapper()

      wrapper.vm.mailTemplate.contentMarkdown = '{{ totally.unknown }}'
      await nextTick()
      await flushPromises()

      expect(wrapper.vm.canSubmit).toBe(false)
    })
  })

  describe('Context-based validation', () => {
    it('validates against action context from loaded template', async () => {
      await createWrapper()

      // Template has action-1 (events) already assigned
      wrapper.vm.mailTemplate.contentMarkdown = '{{ event.name }}'
      await nextTick()
      await flushPromises()

      expect(wrapper.vm.canSubmit).toBe(true)
    })

    it('rejects wrong context placeholders', async () => {
      await createWrapper()

      // Template has action-1 (events) already assigned
      wrapper.vm.mailTemplate.contentMarkdown = '{{ virtualmachine.name }}'
      await nextTick()
      await flushPromises()

      expect(wrapper.vm.canSubmit).toBe(false)
    })

    it('revalidates when action changes', async () => {
      await createWrapper()

      // Set VM placeholder
      wrapper.vm.mailTemplate.contentMarkdown = '{{ virtualmachine.name }}'
      await nextTick()

      // With events action, should be invalid
      wrapper.vm.mailTemplate.mail_action = 'action-1'
      await nextTick()
      await flushPromises()
      expect(wrapper.vm.canSubmit).toBe(false)

      // Change to VM action, should become valid
      wrapper.vm.mailTemplate.mail_action = 'action-2'
      await nextTick()
      await flushPromises()
      expect(wrapper.vm.canSubmit).toBe(true)
    })
  })

  describe('Form submission', () => {
    it('calls updateMailTemplate on valid submit', async () => {
      await createWrapper()

      wrapper.vm.mailTemplate.contentMarkdown = '{{ user.name }}'
      await nextTick()

      await wrapper.vm.submit()
      await flushPromises()

      expect(mockUpdateMailTemplate).toHaveBeenCalled()
    })

    it('does not submit when validation fails', async () => {
      await createWrapper()

      wrapper.vm.mailTemplate.contentMarkdown = '{{ invalid.placeholder }}'
      await nextTick()
      await flushPromises()

      await wrapper.vm.submit()

      expect(mockUpdateMailTemplate).not.toHaveBeenCalled()
    })
  })

  describe('Composable integration', () => {
    it('exposes canSubmit from composable', async () => {
      await createWrapper()
      expect(wrapper.vm.canSubmit).toBeDefined()
      expect(typeof wrapper.vm.canSubmit).toBe('boolean')
    })

    it('exposes validationError from composable', async () => {
      await createWrapper()
      expect(wrapper.vm.validationError).toBeDefined()
    })

    it('exposes selectedActionContext from composable', async () => {
      await createWrapper()
      expect(wrapper.vm.selectedActionContext).toBeDefined()
    })

    it('changes context when action changes', async () => {
      await createWrapper()

      // Set events action
      wrapper.vm.mailTemplate.mail_action = 'action-1'
      await nextTick()
      await flushPromises()
      expect(wrapper.vm.selectedActionContext).toBe('events')

      // Set VM action
      wrapper.vm.mailTemplate.mail_action = 'action-2'
      await nextTick()
      await flushPromises()
      expect(wrapper.vm.selectedActionContext).toBe('virtualmachines')
    })
  })

  describe('Validation error messages', () => {
    it('shows error for unknown placeholders', async () => {
      await createWrapper()

      wrapper.vm.mailTemplate.contentMarkdown = '{{ unknown.var }}'
      await nextTick()
      await flushPromises()

      expect(wrapper.vm.validationError).toContain('Unbekannte Platzhalter')
    })

    it('shows error for wrong context placeholders', async () => {
      await createWrapper()

      // action-1 is events context
      wrapper.vm.mailTemplate.mail_action = 'action-1'
      wrapper.vm.mailTemplate.contentMarkdown = '{{ virtualmachine.name }}'
      await nextTick()
      await flushPromises()

      expect(wrapper.vm.validationError).toContain('Nicht verfügbar')
    })

    it('clears error when content becomes valid', async () => {
      await createWrapper()

      wrapper.vm.mailTemplate.contentMarkdown = '{{ unknown.var }}'
      await nextTick()
      await flushPromises()
      expect(wrapper.vm.validationError).not.toBe('')

      wrapper.vm.mailTemplate.contentMarkdown = '{{ user.name }}'
      await nextTick()
      await flushPromises()
      expect(wrapper.vm.validationError).toBe('')
    })
  })
})
