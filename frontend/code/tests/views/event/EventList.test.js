import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

// Use vi.hoisted to define mocks that can be referenced in vi.mock (which is hoisted)
const {
  mockList,
  mockDelete,
  mockGetVMs,
  mockBeginSilent,
  mockEndSilent,
  toastError,
  toastSuccess,
} = vi.hoisted(() => ({
  mockList: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 25, pageCount: 1, totalCount: 1 },
    items: [{ id: 'evt-1', name: 'WS26 Networking', status: 'status-1' }],
  }),
  mockDelete: vi.fn().mockResolvedValue({}),
  mockGetVMs: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 5, pageCount: 0, totalCount: 0 },
    items: [],
  }),
  mockBeginSilent: vi.fn(),
  mockEndSilent: vi.fn(),
  toastError: vi.fn(),
  toastSuccess: vi.fn(),
}))

// Mock the backend singleton (overrides the global setup mock for this file)
vi.mock('@/services', () => ({
  default: {
    events: {
      list: mockList,
      delete: mockDelete,
      getVMs: mockGetVMs,
    },
    beginSilent: mockBeginSilent,
    endSilent: mockEndSilent,
  },
}))

vi.mock('@/utils/dataUtils', () => ({
  checkObjectPermissions: vi.fn().mockResolvedValue(undefined),
  usePermissionRefs: vi.fn().mockReturnValue({
    canCreate: false,
    canEdit: false,
    canDelete: false,
  }),
  resolveFieldFromLookup: vi.fn().mockResolvedValue(undefined),
  statusEventFilter: vi.fn().mockReturnValue([]),
}))

vi.mock('@/utils/icons', () => ({
  eventStatusIcon: vi.fn(),
}))

vi.mock('@/utils/objectColors', () => ({
  statusColorEvent: vi.fn(),
}))

vi.mock('@/utils/pagination', () => ({
  usePaginationList: vi.fn().mockReturnValue({
    currentPage: { value: 1 },
    perPage: { value: 25 },
    sortColumnKey: { value: 'name' },
    sortDirection: { value: 'asc' },
    searchField: { value: null },
    searchValue: { value: null },
    handlePaginationChanged: vi.fn(),
    handleSortOrderChanged: vi.fn(),
    handleSearch: vi.fn(),
    handleDeleteObject: vi.fn(),
    initialFetch: vi.fn(),
  }),
}))

vi.mock('@/composables/useListAutoRefresh', () => ({
  useListAutoRefresh: vi.fn().mockReturnValue({
    autoRefreshEnabled: { value: false },
    intervalSeconds: 15,
    manualReload: vi.fn(),
  }),
}))

vi.mock('vue-router', () => ({
  useRouter: vi.fn().mockReturnValue({ push: vi.fn() }),
  useRoute: vi.fn().mockReturnValue({ query: {} }),
}))

vi.mock('vue-toastification', () => ({
  useToast: vi.fn().mockReturnValue({
    success: toastSuccess,
    error: toastError,
  }),
}))

const BaseTableStub = {
  name: 'BaseTable',
  template: '<div class="base-table" />',
  props: [
    'currentPage',
    'perPage',
    'itemsTotal',
    'data',
    'sortColumnKey',
    'sortDirection',
    'loading',
    'objectModel',
    'buttons',
    'columns',
    'searchBarFields',
  ],
  emits: [
    'delete-object',
    'search-triggered',
    'sort-order-changed',
    'pagination-changed',
  ],
}

const CardBoxDeleteModalStub = {
  name: 'CardBoxDeleteModal',
  template: '<div class="delete-modal" />',
  props: [
    'modelValue',
    'name',
    'checkvalue',
    'blocked',
    'warning',
    'relatedItems',
    'relatedLabel',
    'relatedCount',
  ],
  emits: ['update:modelValue', 'cancel', 'form-submitted'],
}

const stubs = {
  LayoutAuthenticated: { template: '<div class="layout"><slot /></div>' },
  SectionMain: { template: '<div class="section-main"><slot /></div>' },
  SectionTitleLineWithButton: {
    template: '<div class="section-title"><slot /></div>',
  },
  CardBox: { template: '<div class="card-box"><slot /></div>' },
  BaseButton: {
    template: '<button class="base-button">{{ label }}</button>',
    props: ['label', 'icon', 'color'],
  },
  BaseTable: BaseTableStub,
  CardBoxDeleteModal: CardBoxDeleteModalStub,
}

import EventList from '@/views/event/EventList.vue'

const vmItems = (count) =>
  Array.from({ length: count }, (_, i) => ({
    id: `vm-${i}`,
    name: `pyws-vm-${i}`,
  }))

describe('EventList delete handling', () => {
  let wrapper

  const createWrapper = async () => {
    wrapper = mount(EventList, { global: { stubs } })
    await flushPromises()
    return wrapper
  }

  const modal = () => wrapper.findComponent(CardBoxDeleteModalStub)

  const openDeleteFor = async (object) => {
    wrapper.findComponent(BaseTableStub).vm.$emit('delete-object', object)
    await flushPromises()
  }

  afterEach(() => {
    wrapper?.unmount()
    vi.clearAllMocks()
    mockGetVMs.mockResolvedValue({
      pageDetails: { page: 1, perPage: 5, pageCount: 0, totalCount: 0 },
      items: [],
    })
    mockDelete.mockResolvedValue({})
  })

  describe('proactive pre-check', () => {
    it('blocks the modal and lists assigned VMs', async () => {
      mockGetVMs.mockResolvedValue({
        pageDetails: { page: 1, perPage: 5, pageCount: 2, totalCount: 7 },
        items: vmItems(5),
      })
      await createWrapper()

      await openDeleteFor({ id: 'evt-1', name: 'WS26 Networking' })

      expect(mockGetVMs).toHaveBeenCalledWith('evt-1', { page: 1, limit: 5 })
      expect(modal().props('modelValue')).toBe(true)
      expect(modal().props('blocked')).toBe(true)
      expect(modal().props('relatedCount')).toBe(7)
      expect(modal().props('warning')).toContain('7 VMs')
      const items = modal().props('relatedItems')
      expect(items).toHaveLength(6)
      expect(items[0].label).toBe('pyws-vm-0')
      expect(items[5].label).toBe('… und 2 weitere VMs')
    })

    it('opens unblocked when no VMs are assigned', async () => {
      await createWrapper()

      await openDeleteFor({ id: 'evt-1', name: 'WS26 Networking' })

      expect(modal().props('modelValue')).toBe(true)
      expect(modal().props('blocked')).toBe(false)
      expect(modal().props('warning')).toBeNull()
      expect(modal().props('relatedItems')).toHaveLength(0)
    })

    it('fails open when the VM lookup errors', async () => {
      mockGetVMs.mockRejectedValue(new Error('boom'))
      await createWrapper()

      await openDeleteFor({ id: 'evt-1', name: 'WS26 Networking' })

      expect(modal().props('modelValue')).toBe(true)
      expect(modal().props('blocked')).toBe(false)
      // The lookup runs silenced so the interceptor shows no toast
      expect(mockBeginSilent).toHaveBeenCalled()
      expect(mockEndSilent).toHaveBeenCalled()
    })
  })

  describe('reactive delete errors', () => {
    it('shows a single localized toast on OBJECT_IN_USE', async () => {
      mockDelete.mockRejectedValue({
        response: {
          data: { error_code: 'OBJECT_IN_USE', detail: 'raw backend detail' },
        },
      })
      await createWrapper()
      await openDeleteFor({ id: 'evt-1', name: 'WS26 Networking' })

      modal().vm.$emit('form-submitted')
      await flushPromises()

      expect(toastError).toHaveBeenCalledTimes(1)
      expect(toastError.mock.calls[0][0]).toBe(
        'Die Veranstaltung kann nicht gelöscht werden, da ihr noch VMs zugewiesen sind. Bitte dekommissionieren Sie diese zuerst.',
      )
    })

    it('falls back to the generic toast with detail for other errors', async () => {
      mockDelete.mockRejectedValue({
        response: {
          data: { error_code: 'SOMETHING_ELSE', detail: 'Status invalid' },
        },
      })
      await createWrapper()
      await openDeleteFor({ id: 'evt-1', name: 'WS26 Networking' })

      modal().vm.$emit('form-submitted')
      await flushPromises()

      expect(toastError).toHaveBeenCalledTimes(1)
      const message = toastError.mock.calls[0][0]
      expect(message).toContain('Veranstaltung konnte nicht gelöscht werden')
      expect(message).toContain('Status invalid')
    })

    it('silences the interceptor while deleting and refetches on success', async () => {
      await createWrapper()
      await openDeleteFor({ id: 'evt-1', name: 'WS26 Networking' })
      mockList.mockClear()

      modal().vm.$emit('form-submitted')
      await flushPromises()

      expect(mockDelete).toHaveBeenCalledWith('evt-1')
      expect(mockBeginSilent).toHaveBeenCalled()
      expect(mockEndSilent).toHaveBeenCalled()
      expect(toastSuccess).toHaveBeenCalledTimes(1)
      expect(mockList).toHaveBeenCalledTimes(1)
    })
  })
})
