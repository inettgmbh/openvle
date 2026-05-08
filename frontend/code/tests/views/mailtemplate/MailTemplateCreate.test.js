import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

// Use vi.hoisted to define mocks that can be referenced in vi.mock (which is hoisted)
const { mockFetchMailActionsDropdown, mockAddMailTemplate } = vi.hoisted(
  () => ({
    mockFetchMailActionsDropdown: vi.fn().mockResolvedValue([
      { label: 'Events Action', value: 'action-1', slug: 'events_test' },
      { label: 'VM Action', value: 'action-2', slug: 'vm_test' },
    ]),
    mockAddMailTemplate: vi.fn().mockResolvedValue({
      id: 'template-123',
      name: 'Test Template',
    }),
  }),
)

// Mock the backend singleton
vi.mock('@/services', () => ({
  default: {
    mailTemplates: {
      addMailTemplate: mockAddMailTemplate,
      create: mockAddMailTemplate,
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
    languages: {
      'lang-1': { name: 'German', key: 'de' },
      'lang-2': { name: 'English', key: 'en' },
    },
  }),
}))

vi.mock('@/stores/main', () => ({
  useMainStore: vi.fn().mockReturnValue({
    fetchPermissions: vi.fn(),
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

import MailTemplateCreate from '@/views/mailtemplate/MailTemplateCreate.vue'

describe('MailTemplateCreate', () => {
  let wrapper

  const createWrapper = async () => {
    wrapper = mount(MailTemplateCreate, {
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
    it('submit button is enabled when all required fields are filled', async () => {
      await createWrapper()

      wrapper.vm.mailTemplate.name = 'Test Template'
      wrapper.vm.mailTemplate.subject = 'Test Subject'
      wrapper.vm.mailTemplate.language = 'lang-1'
      wrapper.vm.mailTemplate.contentMarkdown = 'Hello {{ user.name }}'
      await nextTick()
      await flushPromises()

      const submitButton = wrapper.find('button[type="submit"]')
      expect(submitButton.attributes('disabled')).toBeUndefined()
    })

    it('disables submit button when placeholders are invalid', async () => {
      await createWrapper()

      wrapper.vm.mailTemplate.contentMarkdown = '{{ totally.unknown }}'
      await nextTick()
      await flushPromises()

      const submitButton = wrapper.find('button[type="submit"]')
      expect(submitButton.attributes('disabled')).toBeDefined()
    })

    it('allows valid always placeholders', async () => {
      await createWrapper()

      wrapper.vm.mailTemplate.name = 'Test Template'
      wrapper.vm.mailTemplate.subject = 'Test Subject'
      wrapper.vm.mailTemplate.language = 'lang-1'
      wrapper.vm.mailTemplate.contentMarkdown =
        'Hello {{ user.name }}, welcome to {{ project.name }}'
      await nextTick()
      await flushPromises()

      const submitButton = wrapper.find('button[type="submit"]')
      expect(submitButton.attributes('disabled')).toBeUndefined()
    })
  })

  describe('Context-based validation', () => {
    it('validates against events context when events action selected', async () => {
      await createWrapper()

      wrapper.vm.mailTemplate.mail_action = 'action-1'
      wrapper.vm.mailTemplate.contentMarkdown = '{{ event.name }}'
      await nextTick()
      await flushPromises()

      expect(wrapper.vm.canSubmit).toBe(true)
    })

    it('rejects VM placeholders when events action selected', async () => {
      await createWrapper()

      wrapper.vm.mailTemplate.mail_action = 'action-1'
      wrapper.vm.mailTemplate.contentMarkdown = '{{ virtualmachine.name }}'
      await nextTick()
      await flushPromises()

      expect(wrapper.vm.canSubmit).toBe(false)
    })

    it('validates against VM context when VM action selected', async () => {
      await createWrapper()

      wrapper.vm.mailTemplate.mail_action = 'action-2'
      wrapper.vm.mailTemplate.contentMarkdown = '{{ virtualmachine.ipv4 }}'
      await nextTick()
      await flushPromises()

      expect(wrapper.vm.canSubmit).toBe(true)
    })

    it('rejects event placeholders when VM action selected', async () => {
      await createWrapper()

      wrapper.vm.mailTemplate.mail_action = 'action-2'
      wrapper.vm.mailTemplate.contentMarkdown = '{{ event.name }}'
      await nextTick()
      await flushPromises()

      expect(wrapper.vm.canSubmit).toBe(false)
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

    it('detects events context correctly', async () => {
      await createWrapper()

      wrapper.vm.mailTemplate.mail_action = 'action-1'
      await nextTick()
      await flushPromises()

      expect(wrapper.vm.selectedActionContext).toBe('events')
    })

    it('detects VM context correctly', async () => {
      await createWrapper()

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

      wrapper.vm.mailTemplate.mail_action = 'action-1' // events
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
