import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick, ref } from 'vue'

// Use vi.hoisted to define mocks that can be referenced in vi.mock (which is hoisted)
const {
  mockGetMailAction,
  mockGetMailTemplate,
  mockGetMailTemplates,
  mockSearchMailtemplates,
  mockAssignMailTemplate,
  mockUnassignMailTemplate,
} = vi.hoisted(() => ({
  mockGetMailAction: vi.fn().mockResolvedValue({
    id: 'action-123',
    name: 'Events Test Action',
    description: 'An action for events',
    slug: 'events_test_action',
    mailtemplates: [],
    mailtemplatesCount: 0,
  }),
  mockGetMailTemplate: vi.fn().mockResolvedValue({
    id: 'template-123',
    name: 'Test Template',
    contentHTML: '<p>Hello {{ user.name }}</p>',
  }),
  mockGetMailTemplates: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 0 },
    items: [],
  }),
  mockSearchMailtemplates: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 25, pageCount: 1, totalCount: 1 },
    items: [{ id: 'template-123', name: 'Test Template' }],
  }),
  mockAssignMailTemplate: vi.fn().mockResolvedValue({ success: true }),
  mockUnassignMailTemplate: vi.fn().mockResolvedValue({ success: true }),
}))

// Mock the backend singleton
vi.mock('@/services', () => ({
  default: {
    mailActions: {
      getMailAction: mockGetMailAction,
      get: mockGetMailAction,
    },
    mailTemplates: {
      getMailTemplate: mockGetMailTemplate,
      get: mockGetMailTemplate,
      getMailTemplates: mockGetMailTemplates,
      list: mockGetMailTemplates,
      searchMailtemplates: mockSearchMailtemplates,
      search: mockSearchMailtemplates,
      assingMailTemplate: mockAssignMailTemplate,
      assignMailTemplate: mockAssignMailTemplate,
      unassingMailTemplate: mockUnassignMailTemplate,
      unassignMailTemplate: mockUnassignMailTemplate,
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

vi.mock('@/utils/dataUtils', () => ({
  checkObjectPermissions: vi.fn().mockResolvedValue({}),
  usePermissionRefs: vi.fn().mockReturnValue({
    canReadMailTemplates: ref(true),
  }),
  keyToFlag: vi.fn().mockReturnValue('\ud83c\udde9\ud83c\uddea'),
}))

vi.mock('@/utils/objectColors', () => ({
  statusColorMailTemplate: vi.fn().mockReturnValue('success'),
}))

vi.mock('@/utils/pagination', () => ({
  usePaginationChild: vi.fn().mockReturnValue({
    childComponents: ref([
      {
        name: 'mailtemplates',
        perPage: 10,
        currentPage: 1,
        sortColumnKey: 'name',
        sortDirection: 'asc',
      },
    ]),
    loadedTabs: ref(new Set(['mail-action'])),
    handlePaginationChanged: vi.fn(),
    handleSortOrderChanged: vi.fn(),
    handleDeleteObject: vi.fn(),
    handleTabChanged: vi.fn(),
  }),
}))

vi.mock('vue-router', () => ({
  useRoute: vi.fn().mockReturnValue({
    params: { id: 'action-123' },
  }),
  useRouter: vi.fn().mockReturnValue({
    push: vi.fn(),
  }),
  onBeforeRouteLeave: vi.fn(),
}))

vi.mock('vue-toastification', () => ({
  useToast: vi.fn().mockReturnValue({
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
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
    template: '<div class="section-title"><slot /></div>',
  },
  CardBox: {
    template: '<div class="card-box"><slot /><slot name="footer" /></div>',
  },
  CardBoxModal: {
    template: `
      <div v-if="modelValue" class="modal">
        <slot />
        <button
          class="submit-btn"
          :disabled="disabled"
          @click="$emit('form-submitted')"
        >{{ buttonLabel }}</button>
        <button class="cancel-btn" @click="$emit('cancel')">Cancel</button>
      </div>
    `,
    props: [
      'modelValue',
      'title',
      'button',
      'buttonLabel',
      'hasCancel',
      'hasSearch',
      'disabled',
      'form',
    ],
  },
  CardBoxDeleteRelationModal: {
    template: '<div class="delete-modal" />',
  },
  FormField: {
    template: '<div class="form-field"><slot /></div>',
  },
  FormControl: {
    template:
      '<input class="form-control" :value="modelValue" :disabled="disabled" />',
    props: ['modelValue', 'icon', 'disabled', 'type'],
  },
  SearchControl: {
    template:
      '<input class="search-control" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
    props: ['modelValue', 'fetchData', 'icon', 'required'],
  },
  BaseButton: {
    template:
      '<button class="base-button" :disabled="disabled">{{ label }}</button>',
    props: [
      'icon',
      'label',
      'color',
      'roundedFull',
      'small',
      'target',
      'disabled',
    ],
  },
  BaseButtons: {
    template: '<div class="base-buttons"><slot /></div>',
  },
  BaseTabs: {
    template: '<div class="base-tabs"><slot /></div>',
  },
  BaseTab: {
    template: '<div class="base-tab"><slot /></div>',
  },
  BaseTable: {
    template: '<table class="base-table" />',
  },
  PillTag: {
    template: '<span class="pill-tag" />',
  },
  ObjectMetadataDisplay: {
    template: '<div class="metadata" />',
  },
  NotificationBar: {
    template:
      '<div class="notification-bar" v-if="$slots.default"><slot /></div>',
    props: ['color', 'icon', 'dismissable'],
  },
}

import MailActionDetail from '@/views/mailaction/MailActionDetail.vue'

// No-op tooltip directive stub for tests
const tooltipDirectiveStub = {
  mounted() {},
  updated() {},
  beforeUnmount() {},
}

describe('MailActionDetail', () => {
  let wrapper

  const createWrapper = async () => {
    wrapper = mount(MailActionDetail, {
      global: {
        stubs,
        directives: {
          tooltip: tooltipDirectiveStub,
        },
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
    it('renders the component', async () => {
      await createWrapper()
      expect(wrapper.exists()).toBe(true)
    })

    it('renders assign modal when opened', async () => {
      await createWrapper()

      wrapper.vm.modals.assignAction.value = true
      await nextTick()

      const modal = wrapper.find('.modal')
      expect(modal.exists()).toBe(true)
    })
  })

  describe('Placeholder Validation in Assign Modal', () => {
    beforeEach(() => {
      mockGetMailTemplate.mockResolvedValue({
        id: 'template-123',
        name: 'Test Template',
        contentHTML: '<p>Hello {{ user.name }}</p>',
      })
    })

    it('validates template placeholders when template is selected', async () => {
      await createWrapper()

      wrapper.vm.modals.assignAction.value = true
      await nextTick()

      wrapper.vm.objToAdd.mailTemplateId = 'template-123'
      await nextTick()
      await flushPromises()

      expect(mockGetMailTemplate).toHaveBeenCalledWith('template-123')
    })

    it('allows submission when template has valid placeholders', async () => {
      await createWrapper()

      wrapper.vm.modals.assignAction.value = true
      await nextTick()

      wrapper.vm.objToAdd.mailTemplateId = 'template-123'
      await nextTick()
      await flushPromises()

      expect(wrapper.vm.canSubmit).toBe(true)
    })

    it('disables submission when template has invalid placeholders', async () => {
      mockGetMailTemplate.mockResolvedValue({
        id: 'template-invalid',
        name: 'Invalid Template',
        contentHTML: '<p>{{ totally.unknown.placeholder }}</p>',
      })

      await createWrapper()

      wrapper.vm.modals.assignAction.value = true
      await nextTick()

      wrapper.vm.objToAdd.mailTemplateId = 'template-invalid'
      await nextTick()
      await flushPromises()

      expect(wrapper.vm.canSubmit).toBe(false)
    })

    it('shows error for wrong context placeholders', async () => {
      mockGetMailTemplate.mockResolvedValue({
        id: 'template-vm',
        name: 'VM Template',
        contentHTML: '<p>{{ virtualmachine.name }}</p>',
      })

      await createWrapper()

      wrapper.vm.modals.assignAction.value = true
      await nextTick()

      wrapper.vm.objToAdd.mailTemplateId = 'template-vm'
      await nextTick()
      await flushPromises()

      expect(wrapper.vm.validationError).not.toBe('')
      expect(wrapper.vm.canSubmit).toBe(false)
    })

    it('allows event placeholders for events action', async () => {
      mockGetMailTemplate.mockResolvedValue({
        id: 'template-event',
        name: 'Event Template',
        contentHTML: '<p>{{ event.name }} - {{ subtask.status }}</p>',
      })

      await createWrapper()

      wrapper.vm.modals.assignAction.value = true
      await nextTick()

      wrapper.vm.objToAdd.mailTemplateId = 'template-event'
      await nextTick()
      await flushPromises()

      expect(wrapper.vm.canSubmit).toBe(true)
      expect(wrapper.vm.validationError).toBe('')
    })
  })

  describe('Modal disabled state', () => {
    it('submit button is disabled when canSubmit is false', async () => {
      mockGetMailTemplate.mockResolvedValue({
        id: 'template-invalid',
        name: 'Invalid Template',
        contentHTML: '<p>{{ unknown.placeholder }}</p>',
      })

      await createWrapper()

      wrapper.vm.modals.assignAction.value = true
      await nextTick()

      wrapper.vm.objToAdd.mailTemplateId = 'template-invalid'
      await nextTick()
      await flushPromises()

      const submitBtn = wrapper.find('.submit-btn')
      expect(submitBtn.attributes('disabled')).toBeDefined()
    })

    it('submit button is enabled when canSubmit is true', async () => {
      mockGetMailTemplate.mockResolvedValue({
        id: 'template-123',
        name: 'Test Template',
        contentHTML: '<p>Hello {{ user.name }}</p>',
      })

      await createWrapper()

      wrapper.vm.modals.assignAction.value = true
      await nextTick()

      wrapper.vm.objToAdd.mailTemplateId = 'template-123'
      await nextTick()
      await flushPromises()

      const submitBtn = wrapper.find('.submit-btn')
      expect(submitBtn.attributes('disabled')).toBeUndefined()
    })
  })

  describe('Notification Bar', () => {
    it('shows notification bar when validation error exists', async () => {
      mockGetMailTemplate.mockResolvedValue({
        id: 'template-invalid',
        name: 'Invalid Template',
        contentHTML: '<p>{{ virtualmachine.name }}</p>',
      })

      await createWrapper()

      wrapper.vm.modals.assignAction.value = true
      await nextTick()

      wrapper.vm.objToAdd.mailTemplateId = 'template-invalid'
      await nextTick()
      await flushPromises()

      const notificationBar = wrapper.find('.notification-bar')
      expect(notificationBar.exists()).toBe(true)
    })

    it('hides notification bar when no validation error', async () => {
      await createWrapper()

      wrapper.vm.modals.assignAction.value = true
      await nextTick()

      const notificationBar = wrapper.find('.notification-bar')
      expect(notificationBar.exists()).toBe(false)
    })
  })

  describe('Reset Form', () => {
    it('resets selectedTemplateContent when form is reset', async () => {
      mockGetMailTemplate.mockResolvedValue({
        id: 'template-123',
        name: 'Test Template',
        contentHTML: '<p>Hello {{ user.name }}</p>',
      })

      await createWrapper()

      wrapper.vm.objToAdd.mailTemplateId = 'template-123'
      await nextTick()
      await flushPromises()

      wrapper.vm.resetAssignForm()
      await nextTick()

      expect(wrapper.vm.selectedTemplateContent).toBe('')
      expect(wrapper.vm.objToAdd.mailTemplateId).toBe('')
    })
  })

  describe('Composable Integration', () => {
    it('uses mail action slug for context detection', async () => {
      await createWrapper()

      expect(wrapper.vm.mailAction.slug).toBe('events_test_action')
      expect(wrapper.vm.actionsForValidation).toEqual([
        { value: 'action-123', slug: 'events_test_action' },
      ])
    })

    it('exposes canSubmit from composable', async () => {
      await createWrapper()
      expect(wrapper.vm.canSubmit).toBeDefined()
      expect(typeof wrapper.vm.canSubmit).toBe('boolean')
    })

    it('exposes validationError from composable', async () => {
      await createWrapper()
      expect(wrapper.vm.validationError).toBeDefined()
    })
  })
})
