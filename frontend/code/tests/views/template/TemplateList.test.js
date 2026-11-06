import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

// Use vi.hoisted to define mocks that can be referenced in vi.mock (which is hoisted)
const {
  mockList,
  mockDelete,
  mockGetVMs,
  mockGetCourses,
  mockBeginSilent,
  mockEndSilent,
  toastError,
  toastSuccess,
} = vi.hoisted(() => {
  const emptyPage = {
    pageDetails: { page: 1, perPage: 5, pageCount: 0, totalCount: 0 },
    items: [],
  }
  return {
    mockList: vi.fn().mockResolvedValue({
      pageDetails: { page: 1, perPage: 25, pageCount: 1, totalCount: 1 },
      items: [{ id: 'tpl-1', name: 'Debian 12', status: 'Available' }],
    }),
    mockDelete: vi.fn().mockResolvedValue({}),
    mockGetVMs: vi.fn().mockResolvedValue(emptyPage),
    mockGetCourses: vi.fn().mockResolvedValue(emptyPage),
    mockBeginSilent: vi.fn(),
    mockEndSilent: vi.fn(),
    toastError: vi.fn(),
    toastSuccess: vi.fn(),
  }
})

// Mock the backend singleton (overrides the global setup mock for this file)
vi.mock('@/services', () => ({
  default: {
    templates: {
      list: mockList,
      delete: mockDelete,
      getVMs: mockGetVMs,
      getCourses: mockGetCourses,
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
  statusTemplateFilter: vi.fn().mockReturnValue([]),
  protectedObjectFilter: vi.fn().mockReturnValue([]),
}))

vi.mock('@/utils/icons', () => ({
  templateStatusIcon: vi.fn(),
}))

vi.mock('@/utils/objectColors', () => ({
  statusColorTemplates: vi.fn(),
}))

vi.mock('@/utils/tooltips', () => ({
  templateStatusTooltip: vi.fn(),
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
  BaseButtons: { template: '<div><slot /></div>' },
  BaseTable: BaseTableStub,
  CardBoxDeleteModal: CardBoxDeleteModalStub,
}

import TemplateList from '@/views/template/TemplateList.vue'

const page = (names, totalCount) => ({
  pageDetails: { page: 1, perPage: 5, pageCount: 1, totalCount },
  items: names.map((name, i) => ({ id: `${name}-${i}`, name })),
})

describe('TemplateList delete handling', () => {
  let wrapper

  const createWrapper = async () => {
    wrapper = mount(TemplateList, { global: { stubs } })
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
    const emptyPage = {
      pageDetails: { page: 1, perPage: 5, pageCount: 0, totalCount: 0 },
      items: [],
    }
    mockGetVMs.mockResolvedValue(emptyPage)
    mockGetCourses.mockResolvedValue(emptyPage)
    mockDelete.mockResolvedValue({})
  })

  describe('proactive pre-check', () => {
    it('blocks the modal and lists VMs and courses with type sublabels', async () => {
      mockGetVMs.mockResolvedValue(page(['vm-a', 'vm-b'], 2))
      mockGetCourses.mockResolvedValue(page(['Kurs A'], 1))
      await createWrapper()

      await openDeleteFor({ id: 'tpl-1', name: 'Debian 12' })

      expect(mockGetVMs).toHaveBeenCalledWith('tpl-1', { page: 1, limit: 5 })
      expect(mockGetCourses).toHaveBeenCalledWith('tpl-1', {
        page: 1,
        limit: 5,
      })
      expect(modal().props('modelValue')).toBe(true)
      expect(modal().props('blocked')).toBe(true)
      expect(modal().props('relatedCount')).toBe(3)
      expect(modal().props('warning')).toContain('3 Objekten')
      const items = modal().props('relatedItems')
      expect(items).toHaveLength(3)
      expect(items[0]).toEqual({ label: 'vm-a', sublabel: 'VM' })
      expect(items[2]).toEqual({ label: 'Kurs A', sublabel: 'Umgebung' })
    })

    it('caps the list and appends a "more" row for the remainder', async () => {
      mockGetVMs.mockResolvedValue(
        page(['vm-a', 'vm-b', 'vm-c', 'vm-d', 'vm-e'], 6),
      )
      mockGetCourses.mockResolvedValue(page(['Kurs A', 'Kurs B'], 2))
      await createWrapper()

      await openDeleteFor({ id: 'tpl-1', name: 'Debian 12' })

      expect(modal().props('relatedCount')).toBe(8)
      const items = modal().props('relatedItems')
      expect(items).toHaveLength(6)
      expect(items[5].label).toBe('… und 3 weitere Objekte')
    })

    it('opens unblocked when nothing references the template', async () => {
      await createWrapper()

      await openDeleteFor({ id: 'tpl-1', name: 'Debian 12' })

      expect(modal().props('modelValue')).toBe(true)
      expect(modal().props('blocked')).toBe(false)
      expect(modal().props('warning')).toBeNull()
    })

    it('fails open when a lookup errors', async () => {
      mockGetCourses.mockRejectedValue(new Error('boom'))
      await createWrapper()

      await openDeleteFor({ id: 'tpl-1', name: 'Debian 12' })

      expect(modal().props('modelValue')).toBe(true)
      expect(modal().props('blocked')).toBe(false)
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
      await openDeleteFor({ id: 'tpl-1', name: 'Debian 12' })

      modal().vm.$emit('form-submitted')
      await flushPromises()

      expect(toastError).toHaveBeenCalledTimes(1)
      expect(toastError.mock.calls[0][0]).toBe(
        'Die VM-Vorlage kann nicht gelöscht werden, da sie noch verwendet wird (VMs, Umgebungen oder Veranstaltungen). Bitte entfernen Sie zuerst die Verknüpfungen.',
      )
    })

    it('falls back to the generic toast with detail for other errors', async () => {
      mockDelete.mockRejectedValue({
        response: {
          data: {
            error_code: 'PROTECTED_OBJECT',
            detail: 'Template geschützt',
          },
        },
      })
      await createWrapper()
      await openDeleteFor({ id: 'tpl-1', name: 'Debian 12' })

      modal().vm.$emit('form-submitted')
      await flushPromises()

      expect(toastError).toHaveBeenCalledTimes(1)
      const message = toastError.mock.calls[0][0]
      expect(message).toContain('VM-Vorlage konnte nicht gelöscht werden')
      expect(message).toContain('Template geschützt')
    })
  })
})
