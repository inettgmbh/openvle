import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

// Use vi.hoisted to define mocks that can be referenced in vi.mock (which is hoisted)
const { mockList, mockListByObject } = vi.hoisted(() => ({
  mockList: vi.fn().mockResolvedValue({
    items: [],
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 0 },
  }),
  mockListByObject: vi.fn().mockResolvedValue({
    items: [],
    pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 0 },
  }),
}))

// Mock the backend singleton
vi.mock('@/services', () => ({
  default: {
    changelog: {
      list: mockList,
      listByObject: mockListByObject,
    },
  },
}))

vi.mock('@/stores/lookup', () => ({
  useLookupStore: vi.fn().mockReturnValue({
    resolve: vi
      .fn()
      .mockImplementation((keyspace, value) => Promise.resolve(value)),
  }),
}))

vi.mock('@/utils/dataUtils', () => ({
  resolveFieldFromLookup: vi.fn().mockResolvedValue({}),
}))

// Stubs for child components
const SectionTitleLineWithButtonStub = {
  name: 'SectionTitleLineWithButton',
  template: '<div class="section-title"><slot /></div>',
  props: ['icon', 'title', 'reload'],
}

const BaseTableStub = {
  name: 'BaseTable',
  template: `
    <div class="base-table">
      <table>
        <tbody>
          <tr v-for="item in data" :key="item.id">
            <td class="username-cell">{{ item.username }}</td>
            <td class="changes-cell"><slot name="cell-parsedChanges" :value="item.parsedChanges" :item="item" /></td>
            <td>{{ item.timestamp }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="!data.length" class="empty">Keine Daten</div>
    </div>
  `,
  props: [
    'objectModel',
    'data',
    'columns',
    'loading',
    'itemsTotal',
    'currentPage',
    'perPage',
    'sortColumnKey',
    'sortDirection',
    'createdColumnKey',
    'createdColumnLabel',
  ],
  emits: ['paginationChanged', 'sortOrderChanged'],
}

const ChangelogChangesCellStub = {
  name: 'ChangelogChangesCell',
  template:
    '<div class="changelog-cell">{{ changes?.length || 0 }} changes</div>',
  props: ['changes', 'formatFieldKey', 'formatDisplayValue', 'shortenMiddle'],
}

const stubs = {
  SectionTitleLineWithButton: SectionTitleLineWithButtonStub,
  BaseTable: BaseTableStub,
  ChangelogChangesCell: ChangelogChangesCellStub,
}

import TableChangelogs from '@/components/Tables/TableChangelogs.vue'

// Reference the mock functions for test assertions
const ChangelogService = {
  list: mockList,
  listByObject: mockListByObject,
}

describe('TableChangelogs', () => {
  let wrapper

  const createWrapper = async (props = {}) => {
    wrapper = mount(TableChangelogs, {
      props: {
        perPage: 10,
        ...props,
      },
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
    it('renders the component', async () => {
      await createWrapper()
      expect(wrapper.exists()).toBe(true)
    })

    it('renders section title', async () => {
      await createWrapper()
      expect(wrapper.find('.section-title').exists()).toBe(true)
    })

    it('renders BaseTable component', async () => {
      await createWrapper()
      expect(wrapper.find('.base-table').exists()).toBe(true)
    })

    it('shows empty state when no data', async () => {
      await createWrapper()
      expect(wrapper.find('.empty').exists()).toBe(true)
    })
  })

  describe('Data Fetching', () => {
    it('calls getChangelogsByObjectId when objectId and objectType are provided', async () => {
      await createWrapper({
        objectId: 'test-id',
        objectType: 'user',
      })

      expect(ChangelogService.listByObject).toHaveBeenCalledWith(
        'user',
        'test-id',
        expect.objectContaining({
          page: 1,
          limit: 10,
          sort_by: 'timestamp',
          sort_order: 'desc',
        }),
      )
    })

    it('calls getChangelogs when all prop is true', async () => {
      await createWrapper({ all: true })

      expect(ChangelogService.list).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 1,
          limit: 10,
          sort_by: 'timestamp',
          sort_order: 'desc',
        }),
      )
    })

    it('refetches data when objectId changes', async () => {
      await createWrapper({
        objectId: 'id-1',
        objectType: 'user',
      })

      expect(ChangelogService.listByObject).toHaveBeenCalledTimes(1)

      await wrapper.setProps({ objectId: 'id-2' })
      await flushPromises()

      expect(ChangelogService.listByObject).toHaveBeenCalledTimes(2)
    })
  })

  describe('Data Display', () => {
    beforeEach(() => {
      ChangelogService.listByObject.mockResolvedValue({
        items: [
          {
            id: 'log-1',
            userId: 'user-1',
            username: 'testuser',
            timestamp: '2024-01-15T10:30:00Z',
            object: 'User',
            valueOld: "{'name': 'Old Name'}",
            valueNew: "{'name': 'New Name'}",
          },
        ],
        pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 1 },
      })
    })

    it('displays changelog data in table', async () => {
      await createWrapper({
        objectId: 'test-id',
        objectType: 'user',
      })

      expect(wrapper.find('.username-cell').text()).toContain('testuser')
    })

    it('parses changelog changes correctly', async () => {
      await createWrapper({
        objectId: 'test-id',
        objectType: 'user',
      })

      const changelogCell = wrapper.find('.changelog-cell')
      expect(changelogCell.exists()).toBe(true)
    })
  })

  describe('Pagination', () => {
    it('emits pagination event to BaseTable', async () => {
      ChangelogService.listByObject.mockResolvedValue({
        items: [],
        pageDetails: { page: 2, perPage: 10, pageCount: 2, totalCount: 15 },
      })

      await createWrapper({
        objectId: 'test-id',
        objectType: 'user',
      })

      const baseTable = wrapper.findComponent(BaseTableStub)
      await baseTable.vm.$emit('paginationChanged', 2, 10)
      await flushPromises()

      expect(ChangelogService.listByObject).toHaveBeenLastCalledWith(
        'user',
        'test-id',
        expect.objectContaining({ page: 2, limit: 10 }),
      )
    })
  })

  describe('Sorting', () => {
    it('handles sort order change event', async () => {
      await createWrapper({
        objectId: 'test-id',
        objectType: 'user',
      })

      const baseTable = wrapper.findComponent(BaseTableStub)
      await baseTable.vm.$emit('sortOrderChanged', 'asc', 'userId')
      await flushPromises()

      expect(ChangelogService.listByObject).toHaveBeenLastCalledWith(
        'user',
        'test-id',
        expect.objectContaining({
          sort_by: 'userId',
          sort_order: 'asc',
        }),
      )
    })
  })

  describe('Change Parsing', () => {
    it('parses Python-style JSON in changes', async () => {
      ChangelogService.listByObject.mockResolvedValue({
        items: [
          {
            id: 'log-1',
            userId: 'user-1',
            timestamp: '2024-01-15T10:30:00Z',
            object: 'User',
            valueOld: "{'active': True, 'count': None}",
            valueNew: "{'active': False, 'count': 5}",
          },
        ],
        pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 1 },
      })

      await createWrapper({
        objectId: 'test-id',
        objectType: 'user',
      })

      const changelogCell = wrapper.find('.changelog-cell')
      expect(changelogCell.exists()).toBe(true)
    })

    it('handles UUID values in changes', async () => {
      ChangelogService.listByObject.mockResolvedValue({
        items: [
          {
            id: 'log-1',
            userId: 'user-1',
            timestamp: '2024-01-15T10:30:00Z',
            object: 'Role',
            valueOld: "{'id': UUID('123e4567-e89b-12d3-a456-426614174000')}",
            valueNew: "{'id': UUID('987fcdeb-51a2-3b4c-d567-890123456789')}",
          },
        ],
        pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 1 },
      })

      await createWrapper({
        objectId: 'test-id',
        objectType: 'role',
      })

      const changelogCell = wrapper.find('.changelog-cell')
      expect(changelogCell.exists()).toBe(true)
    })

    it('handles datetime values in changes', async () => {
      ChangelogService.listByObject.mockResolvedValue({
        items: [
          {
            id: 'log-1',
            userId: 'user-1',
            timestamp: '2024-01-15T10:30:00Z',
            object: 'Event',
            valueOld: "{'date_start': datetime.date(2024, 1, 1)}",
            valueNew: "{'date_start': datetime.date(2024, 2, 1)}",
          },
        ],
        pageDetails: { page: 1, perPage: 10, pageCount: 1, totalCount: 1 },
      })

      await createWrapper({
        objectId: 'test-id',
        objectType: 'event',
      })

      const changelogCell = wrapper.find('.changelog-cell')
      expect(changelogCell.exists()).toBe(true)
    })
  })

  describe('Error Handling', () => {
    it('handles API errors gracefully', async () => {
      const consoleError = vi
        .spyOn(console, 'error')
        .mockImplementation(() => {})
      ChangelogService.listByObject.mockRejectedValueOnce(
        new Error('API Error'),
      )

      await createWrapper({
        objectId: 'test-id',
        objectType: 'user',
      })

      expect(consoleError).toHaveBeenCalledWith(
        'Failed to load changelogs:',
        expect.any(Error),
      )

      consoleError.mockRestore()
    })
  })

  describe('Reload Functionality', () => {
    it('provides reload function to section title', async () => {
      await createWrapper({
        objectId: 'test-id',
        objectType: 'user',
      })

      const sectionTitle = wrapper.findComponent(SectionTitleLineWithButtonStub)
      expect(sectionTitle.props('reload')).toBeInstanceOf(Function)
    })

    it('reload function fetches data again', async () => {
      await createWrapper({
        objectId: 'test-id',
        objectType: 'user',
      })

      expect(ChangelogService.listByObject).toHaveBeenCalledTimes(1)

      const sectionTitle = wrapper.findComponent(SectionTitleLineWithButtonStub)
      await sectionTitle.props('reload')()
      await flushPromises()

      expect(ChangelogService.listByObject).toHaveBeenCalledTimes(2)
    })
  })

  describe('Field Labels', () => {
    it('formats known field keys with German labels', async () => {
      await createWrapper()

      const formatFieldKey = wrapper.vm.formatFieldKey

      expect(formatFieldKey('description')).toBe('Beschreibung')
      expect(formatFieldKey('active')).toBe('Aktiv')
      expect(formatFieldKey('protected')).toBe('Geschützt')
      expect(formatFieldKey('datestart')).toBe('Startdatum')
    })

    it('formats unknown field keys to title case', async () => {
      await createWrapper()

      const formatFieldKey = wrapper.vm.formatFieldKey
      expect(formatFieldKey('some_custom_field')).toBe('Some Custom Field')
    })
  })

  describe('Value Formatting', () => {
    it('formats boolean values correctly', async () => {
      await createWrapper()

      const formatDisplayValue = wrapper.vm.formatDisplayValue

      const trueResult = formatDisplayValue(true)
      expect(trueResult.isSimple).toBe(true)
      expect(trueResult.value).toBe('Ja')

      const falseResult = formatDisplayValue(false)
      expect(falseResult.isSimple).toBe(true)
      expect(falseResult.value).toBe('Nein')
    })

    it('formats empty values correctly', async () => {
      await createWrapper()

      const formatDisplayValue = wrapper.vm.formatDisplayValue

      expect(formatDisplayValue(null).isEmpty).toBe(true)
      expect(formatDisplayValue('').isEmpty).toBe(true)
      expect(formatDisplayValue([]).isEmpty).toBe(true)
    })

    it('formats arrays with key property', async () => {
      await createWrapper()

      const formatDisplayValue = wrapper.vm.formatDisplayValue
      const result = formatDisplayValue([{ key: 'read' }, { key: 'write' }])

      expect(result.isList).toBe(true)
      expect(result.items).toContain('Read')
      expect(result.items).toContain('Write')
    })
  })

  describe('Value Shortening', () => {
    it('shortens long strings', async () => {
      await createWrapper()

      const shortenMiddle = wrapper.vm.shortenMiddle
      const longString = 'A'.repeat(100)
      const result = shortenMiddle(longString)

      expect(result).toContain('[...]')
      expect(result.length).toBeLessThan(longString.length)
    })

    it('does not shorten short strings', async () => {
      await createWrapper()

      const shortenMiddle = wrapper.vm.shortenMiddle
      const shortString = 'Short text'
      const result = shortenMiddle(shortString)

      expect(result).toBe(shortString)
    })

    it('handles null and undefined', async () => {
      await createWrapper()

      const shortenMiddle = wrapper.vm.shortenMiddle

      expect(shortenMiddle(null)).toBe('')
      expect(shortenMiddle(undefined)).toBe('')
    })
  })
})
