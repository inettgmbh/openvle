import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

// Use vi.hoisted to define mocks that can be referenced in vi.mock (which is hoisted)
const { mockListProviders } = vi.hoisted(() => ({
  mockListProviders: vi.fn().mockResolvedValue({
    pageDetails: { page: 1, perPage: 25, pageCount: 1, totalCount: 2 },
    items: [
      {
        id: '1',
        name: 'Authentik',
        description: 'Authentik provider',
        enabled: true,
      },
      { id: '2', name: 'Okta', description: 'Okta provider', enabled: false },
    ],
  }),
}))

// Mock the backend singleton
vi.mock('@/services', () => ({
  default: {
    scimProviders: {
      list: mockListProviders,
      delete: vi.fn().mockResolvedValue({}),
    },
  },
}))

vi.mock('@/utils/dataUtils', () => ({
  checkObjectPermissions: vi.fn().mockResolvedValue(undefined),
  usePermissionRefs: vi.fn().mockReturnValue({
    canCreate: false,
    canEdit: false,
    canDelete: false,
  }),
  userStatusLabel: vi.fn((v) => v),
  statusUserFilter: vi.fn().mockReturnValue([]),
}))

vi.mock('@/utils/icons', () => ({
  scimEnabledIcon: vi.fn(),
  userStatusIcon: vi.fn(),
}))

vi.mock('@/utils/objectColors', () => ({
  statusColorScimEnabled: vi.fn(),
  statusColorUser: vi.fn(),
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

vi.mock('vue-router', () => ({
  useRouter: vi.fn().mockReturnValue({
    push: vi.fn(),
  }),
  useRoute: vi.fn().mockReturnValue({
    query: {},
  }),
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
    template: '<div class="section-title"><slot /></div>',
  },
  CardBox: {
    template: '<div class="card-box"><slot /></div>',
  },
  CardBoxDeleteModal: {
    template: '<div class="delete-modal" />',
  },
  BaseButton: {
    template: '<button class="base-button">{{ label }}</button>',
    props: ['label', 'icon', 'color'],
  },
  BaseTable: {
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
    ],
  },
}

import ScimProviderList from '@/views/scimprovider/ScimProviderList.vue'

describe('ScimProviderList', () => {
  let wrapper

  const createWrapper = async () => {
    wrapper = mount(ScimProviderList, {
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
    it('renders the page', async () => {
      await createWrapper()
      expect(wrapper.find('.layout').exists()).toBe(true)
    })

    it('renders the table component', async () => {
      await createWrapper()
      expect(wrapper.find('.base-table').exists()).toBe(true)
    })

    it('sets up pagination with fetch function', async () => {
      const { usePaginationList } = await import('@/utils/pagination')
      await createWrapper()
      expect(usePaginationList).toHaveBeenCalledWith(
        expect.objectContaining({
          fetch: expect.any(Function),
          syncQuery: true,
        }),
      )
    })
  })
})
