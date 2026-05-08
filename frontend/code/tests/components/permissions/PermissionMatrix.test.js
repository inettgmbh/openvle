import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

const ENTITY_ID = 'role-abc-123'
const ENTITY_TYPE = 'Role'
const PER_PAGE = 200

// -- Mock data --

function makePermission(id, objectType, permissionKey) {
  return {
    id,
    entity_id: ENTITY_ID,
    entity_type: ENTITY_TYPE,
    object_type: objectType,
    object_id: null,
    permission_key: permissionKey,
  }
}

function generatePermissions(count) {
  const types = [
    'User',
    'Event',
    'Template',
    'VirtualMachine',
    'Guacamole',
    'Role',
    'Policy',
    'Mail',
    'Task',
    'SubTask',
  ]
  return Array.from({ length: count }, (_, i) => {
    const objectType = types[i % types.length]
    return makePermission(`p${i + 1}`, objectType, 'object_full')
  })
}

// -- Hoisted mocks --

const { mockList } = vi.hoisted(() => ({
  mockList: vi.fn(),
}))

vi.mock('@/services', () => ({
  default: {
    objectPermissions: {
      list: mockList,
    },
  },
}))

vi.mock('vue-toastification', () => ({
  useToast: vi.fn().mockReturnValue({
    success: vi.fn(),
    error: vi.fn(),
  }),
}))

vi.mock('@/utils/dataUtils', () => ({
  checkObjectPermissions: vi.fn().mockResolvedValue({}),
  usePermissionRefs: vi.fn().mockReturnValue({
    canCreate: false,
    canDelete: false,
    canEdit: false,
  }),
}))

vi.mock('@/utils/objectModelPermissions', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    getAllObjectModelsSorted: vi.fn().mockReturnValue([]),
  }
})

// -- Stubs --

const stubs = {
  BaseButton: {
    template: '<button :disabled="disabled"><slot /></button>',
    props: ['color', 'icon', 'small', 'disabled', 'label', 'roundedFull'],
  },
  SectionTitleLineWithButton: {
    template: '<div class="section-title"><slot /></div>',
    props: [
      'icon',
      'title',
      'reload',
      'reloadDisabled',
      'reloadDisabledTooltip',
    ],
  },
  PermissionModalCreate: { template: '<div />', props: ['modelValue'] },
  PermissionChangesConfirmModal: { template: '<div />', props: ['modelValue'] },
  UnsavedChangesModal: { template: '<div />', props: ['modelValue'] },
  SaveProgressModal: { template: '<div />', props: ['modelValue', 'progress'] },
  PermissionMatrixInfo: { template: '<div />' },
  PermissionMatrixRow: {
    template: '<tr><td>{{ objectType }}</td></tr>',
    props: [
      'objectType',
      'objectEntries',
      'expanded',
      'isEditing',
      'getObjectTypeLabel',
      'objectEntriesAllowed',
    ],
  },
  PermissionSelector: { template: '<span />', props: ['mode', 'modelValue'] },
  ObjectScopedPermissionsTable: { template: '<div />' },
}

import PermissionMatrix from '@/components/permissions/PermissionMatrix.vue'

describe('PermissionMatrix', () => {
  let wrapper

  /**
   * Sets up mockList to serve paginated results from the given items array.
   * Uses the component's actual PER_PAGE (200) for slicing.
   */
  function setupMockPaginated(items) {
    const totalCount = items.length

    mockList.mockImplementation(async (params) => {
      const page = params.page ?? 1
      const limit = params.limit ?? PER_PAGE
      const start = (page - 1) * limit
      const end = start + limit
      return {
        pageDetails: {
          page,
          perPage: limit,
          pageCount: Math.ceil(totalCount / limit),
          totalCount,
        },
        items: items.slice(start, end),
      }
    })
  }

  async function createWrapper() {
    wrapper = mount(PermissionMatrix, {
      props: {
        entityId: ENTITY_ID,
        entityType: ENTITY_TYPE,
      },
      global: { stubs },
    })
    await flushPromises()
    return wrapper
  }

  afterEach(() => {
    if (wrapper) wrapper.unmount()
    vi.clearAllMocks()
  })

  describe('fetch pagination', () => {
    it('fetches all items in a single request when within limit', async () => {
      setupMockPaginated(generatePermissions(5))
      await createWrapper()

      expect(mockList).toHaveBeenCalledTimes(1)
      expect(mockList).toHaveBeenCalledWith(
        expect.objectContaining({ page: 1, limit: PER_PAGE }),
      )
    })

    it('fetches multiple pages when items exceed perPage limit', async () => {
      // 450 items / 200 per page = 3 pages
      setupMockPaginated(generatePermissions(450))
      await createWrapper()

      expect(mockList).toHaveBeenCalledTimes(3)
      expect(mockList).toHaveBeenCalledWith(
        expect.objectContaining({ page: 1 }),
      )
      expect(mockList).toHaveBeenCalledWith(
        expect.objectContaining({ page: 2 }),
      )
      expect(mockList).toHaveBeenCalledWith(
        expect.objectContaining({ page: 3 }),
      )
    })

    it('collects all items from all pages', async () => {
      const items = generatePermissions(450)
      setupMockPaginated(items)
      await createWrapper()

      // All 10 distinct object types from 450 permissions should appear
      const rows = wrapper.findAllComponents(stubs.PermissionMatrixRow)
      const renderedTypes = rows.map((r) => r.props('objectType'))

      const expectedTypes = [...new Set(items.map((i) => i.object_type))]
      for (const type of expectedTypes) {
        expect(renderedTypes).toContain(type)
      }
    })

    it('uses sort_by id for stable pagination', async () => {
      setupMockPaginated(generatePermissions(5))
      await createWrapper()

      expect(mockList).toHaveBeenCalledWith(
        expect.objectContaining({ sort_by: 'id' }),
      )
    })

    it('passes entity_id as search filter', async () => {
      setupMockPaginated(generatePermissions(5))
      await createWrapper()

      expect(mockList).toHaveBeenCalledWith(
        expect.objectContaining({
          search_field: 'entity_id',
          search_value: ENTITY_ID,
        }),
      )
    })

    it('does not fetch additional pages when exactly at limit', async () => {
      setupMockPaginated(generatePermissions(200))
      await createWrapper()

      expect(mockList).toHaveBeenCalledTimes(1)
    })

    it('fetches second page when one item over limit', async () => {
      setupMockPaginated(generatePermissions(201))
      await createWrapper()

      expect(mockList).toHaveBeenCalledTimes(2)
    })
  })
})
