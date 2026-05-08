import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'

const { mockGetMail, mockListSubTasks, mockRouterPush } = vi.hoisted(() => ({
  mockRouterPush: vi.fn(),
  mockGetMail: vi.fn().mockResolvedValue({
    id: 'mail-123',
    subject: 'Test Subject',
    toMail: 'recipient@test.com',
    replyTo: 'reply@test.com',
    fromName: 'Test Sender',
    fromMail: 'sender@test.com',
    sendStatus: 'sent',
    templateId: 'template-456',
    createdById: 'user-1',
    event: 'event-789',
    content_rendered: '<p>Hello World</p>',
  }),
  mockListSubTasks: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 0 },
    items: [],
  }),
}))

vi.mock('@/services', () => ({
  default: {
    mails: {
      get: mockGetMail,
    },
    tasks: {
      listSubTasks: mockListSubTasks,
    },
  },
}))

vi.mock('vue-router', () => ({
  useRoute: vi.fn().mockReturnValue({
    params: { id: 'mail-123' },
  }),
  useRouter: vi.fn().mockReturnValue({
    push: mockRouterPush,
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

vi.mock('@/utils/dataUtils', () => ({
  checkObjectPermissions: vi.fn().mockResolvedValue({}),
  emailStatusFormatter: vi.fn((val) => val),
  parseEmailContent: vi.fn((raw) => raw),
  resolveFieldFromLookup: vi.fn().mockResolvedValue({}),
  usePermissionRefs: vi.fn().mockReturnValue({
    canReadTasks: ref(true),
  }),
}))

vi.mock('@/utils/icons', () => ({
  emailStatusIcon: vi.fn(),
  mailCreateTypeIcon: vi.fn(),
  taskStatusIcon: vi.fn(),
}))

vi.mock('@/utils/objectColors', () => ({
  statusColorMail: vi.fn(),
  statusColorTask: vi.fn(),
}))

vi.mock('@/utils/tooltips', () => ({
  emailSendStatusTooltip: vi.fn(),
  mailCreateTypeTooltip: vi.fn(),
  taskStatusTooltip: vi.fn(),
}))

vi.mock('@/utils/pagination', () => ({
  usePaginationChild: vi.fn().mockReturnValue({
    childComponents: ref([
      {
        name: 'subtasks',
        perPage: 10,
        currentPage: 1,
        sortColumnKey: 'createdAt',
        sortDirection: 'desc',
      },
    ]),
    loadedTabs: ref(new Set(['email'])),
    handlePaginationChanged: vi.fn(),
    handleSortOrderChanged: vi.fn(),
    handleDeleteObject: vi.fn(),
    handleTabChanged: vi.fn(),
  }),
}))

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
    template: '<div class="card-box"><slot /></div>',
  },
  BaseTabs: {
    template: '<div class="base-tabs"><slot /></div>',
  },
  BaseTab: {
    template: '<div class="base-tab"><slot /></div>',
    props: ['id', 'title'],
  },
  BaseTable: {
    template: '<table class="base-table" />',
  },
  BaseMarkdown: {
    template: '<div class="base-markdown">{{ modelValue }}</div>',
    props: ['modelValue', 'action'],
  },
  FormField: {
    template: '<div class="form-field"><slot /></div>',
  },
  FormControl: {
    template: '<input class="form-control" :value="modelValue" />',
    props: ['modelValue', 'icon', 'disabled', 'placeholder', 'link'],
  },
  PillTag: {
    template: '<span class="pill-tag">{{ label }}</span>',
    props: ['color', 'disabled', 'label', 'icon', 'handleClick'],
  },
  ObjectMetadataDisplay: {
    template: '<div class="metadata" />',
  },
}

const tooltipDirectiveStub = {
  mounted() {},
  updated() {},
  beforeUnmount() {},
}

import MailDetail from '@/views/mail/MailDetail.vue'

describe('MailDetail', () => {
  let wrapper

  const createWrapper = async () => {
    wrapper = mount(MailDetail, {
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

    it('renders the card box', async () => {
      await createWrapper()
      expect(wrapper.find('.card-box').exists()).toBe(true)
    })

    it('renders the tabs container', async () => {
      await createWrapper()
      expect(wrapper.find('.base-tabs').exists()).toBe(true)
    })

    it('renders pill tags for status', async () => {
      await createWrapper()
      const pills = wrapper.findAll('.pill-tag')
      expect(pills.length).toBeGreaterThanOrEqual(1)
    })
  })

  describe('Data Loading', () => {
    it('fetches mail on mount', async () => {
      await createWrapper()
      expect(mockGetMail).toHaveBeenCalledWith('mail-123')
    })

    it('populates mail data after fetch', async () => {
      await createWrapper()
      expect(wrapper.vm.mail.subject).toBe('Test Subject')
      expect(wrapper.vm.mail.toMail).toBe('recipient@test.com')
      expect(wrapper.vm.mail.fromName).toBe('Test Sender')
      expect(wrapper.vm.mail.fromMail).toBe('sender@test.com')
    })

    it('sets dataLoading to false after fetch', async () => {
      await createWrapper()
      expect(wrapper.vm.dataLoading).toBe(false)
    })
  })

  describe('Content Preview', () => {
    it('converts content_rendered to markdown for preview', async () => {
      await createWrapper()
      // parseEmailContent is mocked as pass-through, htmlToMarkdown converts HTML to markdown
      expect(wrapper.vm.parsedContentMarkdown).toBeTruthy()
    })

    it('returns empty string when no content_rendered', async () => {
      mockGetMail.mockResolvedValueOnce({
        id: 'mail-empty',
        subject: 'Empty Mail',
        toMail: 'test@test.com',
      })
      await createWrapper()
      expect(wrapper.vm.parsedContentMarkdown).toBe('')
    })

    it('renders BaseMarkdown in preview tab', async () => {
      await createWrapper()
      const markdown = wrapper.find('.base-markdown')
      expect(markdown.exists()).toBe(true)
    })
  })

  describe('Error Handling', () => {
    it('redirects to /mails on fetch error', async () => {
      mockGetMail.mockRejectedValueOnce(new Error('Not found'))
      await createWrapper()

      expect(mockRouterPush).toHaveBeenCalledWith({
        path: '/mails',
        replace: true,
      })
    })
  })

  describe('Event Navigation', () => {
    it('navigates to event on pill click', async () => {
      await createWrapper()
      await wrapper.vm.pillClicked()

      expect(mockRouterPush).toHaveBeenCalledWith({
        path: '/events/event-789',
      })
    })

    it('shows Veranstaltung label when event is set', async () => {
      await createWrapper()
      const pills = wrapper.findAll('.pill-tag')
      const eventPill = pills.find((p) => p.text() === 'Veranstaltung')
      expect(eventPill).toBeDefined()
    })

    it('shows Manuell label when no event', async () => {
      mockGetMail.mockResolvedValueOnce({
        id: 'mail-manual',
        subject: 'Manual Mail',
        toMail: 'test@test.com',
      })
      await createWrapper()
      const pills = wrapper.findAll('.pill-tag')
      const manualPill = pills.find((p) => p.text() === 'Manuell')
      expect(manualPill).toBeDefined()
    })
  })
})
