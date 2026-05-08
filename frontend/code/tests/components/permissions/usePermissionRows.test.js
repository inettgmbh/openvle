import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick, reactive, ref } from 'vue'

// Mock main store
vi.mock('@/stores/main', () => ({
  useMainStore: vi.fn(() => ({ settings: {} })),
}))

// Mock objectModelPermissions
vi.mock('@/utils/objectModelPermissions', () => ({
  getAllObjectModelsSorted: vi.fn(() => []),
  getObjectModelByBackendType: vi.fn(() => null),
  normalizePermission: vi.fn((p) => p),
}))

import { usePermissionRows } from '@/components/permissions/composables/usePermissionRows'
import { useMainStore } from '@/stores/main'
import {
  getAllObjectModelsSorted,
  getObjectModelByBackendType,
  normalizePermission,
} from '@/utils/objectModelPermissions'

describe('usePermissionRows', () => {
  const entityId = 'user-123'
  const entityType = 'User'
  let permissions
  let draft
  let isEditing
  let objectModelQuery
  let onlyWithPermissions
  let prefetchObjectLabel
  let getObjectLabelSync
  let getObjectTypeLabel

  beforeEach(() => {
    vi.clearAllMocks()

    permissions = ref([])
    draft = reactive({
      global: {},
      globalCreate: {},
      objects: {},
      extrasGlobal: {},
      extrasObjects: {},
    })
    isEditing = ref(false)
    objectModelQuery = ref('')
    onlyWithPermissions = ref(false)
    prefetchObjectLabel = vi.fn()
    getObjectLabelSync = vi.fn((ot, id) => `${ot} - ${id}`)
    getObjectTypeLabel = vi.fn((ot) => `Label: ${ot}`)

    // Default mocks
    getAllObjectModelsSorted.mockReturnValue([])
    getObjectModelByBackendType.mockReturnValue(null)
    normalizePermission.mockImplementation((p) => p)
  })

  function createRows() {
    return usePermissionRows(
      permissions,
      draft,
      entityId,
      entityType,
      isEditing,
      objectModelQuery,
      onlyWithPermissions,
      prefetchObjectLabel,
      getObjectLabelSync,
      getObjectTypeLabel,
    )
  }

  describe('Initialization', () => {
    it('returns empty rows when no permissions or models', () => {
      const { rows } = createRows()
      expect(rows.value).toEqual([])
    })

    it('returns expanded as reactive object', () => {
      const { expanded } = createRows()
      expect(typeof expanded).toBe('object')
    })

    it('allExpanded is false when no rows', () => {
      const { allExpanded } = createRows()
      expect(allExpanded.value).toBe(false)
    })
  })

  describe('Row Generation from Object Models', () => {
    it('creates rows from object models', () => {
      getAllObjectModelsSorted.mockReturnValue([
        { key: 'User', backendObjectTypes: ['User'], label: 'Benutzer' },
        { key: 'Role', backendObjectTypes: ['Role'], label: 'Rollen' },
      ])

      const { rows } = createRows()

      expect(rows.value).toHaveLength(2)
      expect(rows.value[0].objectType).toBe('Role') // Sorted by label
      expect(rows.value[1].objectType).toBe('User')
    })

    it('uses first backendObjectType as preferredType', () => {
      getAllObjectModelsSorted.mockReturnValue([
        {
          key: 'VM',
          backendObjectTypes: ['VirtualMachine', 'VM'],
          label: 'VMs',
        },
      ])

      const { rows } = createRows()

      expect(rows.value[0].objectType).toBe('VirtualMachine')
    })

    it('falls back to key when no backendObjectTypes', () => {
      getAllObjectModelsSorted.mockReturnValue([
        { key: 'CustomType', label: 'Custom' },
      ])

      const { rows } = createRows()

      expect(rows.value[0].objectType).toBe('CustomType')
    })
  })

  describe('Row Generation from Permissions', () => {
    it('adds objectTypes from permissions', () => {
      normalizePermission.mockImplementation((p) => ({
        entityId: p.entity_id,
        entityType: p.entity_type,
        objectType: p.object_type,
        objectId: p.object_id,
        permissionKey: p.permission_key,
      }))

      permissions.value = [
        {
          entity_id: entityId,
          entity_type: entityType,
          object_type: 'Application',
          object_id: null,
          permission_key: 'object_read',
        },
      ]

      const { rows } = createRows()

      expect(rows.value).toHaveLength(1)
      expect(rows.value[0].objectType).toBe('Application')
    })

    it('filters out permissions for different entity', () => {
      normalizePermission.mockImplementation((p) => ({
        entityId: p.entity_id,
        entityType: p.entity_type,
        objectType: p.object_type,
      }))

      permissions.value = [
        {
          entity_id: 'other-user',
          entity_type: entityType,
          object_type: 'Application',
        },
      ]

      const { rows } = createRows()

      expect(rows.value).toHaveLength(0)
    })
  })

  describe('Row Generation from Draft', () => {
    it('includes objectTypes from draft.global', () => {
      draft.global = { Course: 'object_read' }

      const { rows } = createRows()

      expect(rows.value).toHaveLength(1)
      expect(rows.value[0].objectType).toBe('Course')
    })

    it('includes objectTypes from draft.globalCreate', () => {
      draft.globalCreate = { Event: true }

      const { rows } = createRows()

      expect(rows.value).toHaveLength(1)
      expect(rows.value[0].objectType).toBe('Event')
    })

    it('includes objectTypes from draft.objects', () => {
      draft.objects = { Template: { 'tpl-123': 'object_read' } }

      const { rows } = createRows()

      expect(rows.value).toHaveLength(1)
      expect(rows.value[0].objectType).toBe('Template')
    })

    it('includes objectTypes from draft.extrasGlobal', () => {
      draft.extrasGlobal = { Policy: ['action_approve'] }

      const { rows } = createRows()

      expect(rows.value).toHaveLength(1)
      expect(rows.value[0].objectType).toBe('Policy')
    })

    it('includes objectTypes from draft.extrasObjects', () => {
      draft.extrasObjects = { Document: { 'doc-123': ['action_sign'] } }

      const { rows } = createRows()

      expect(rows.value).toHaveLength(1)
      expect(rows.value[0].objectType).toBe('Document')
    })
  })

  describe('Object Entries', () => {
    it('generates objectEntries from draft.objects', () => {
      draft.objects = {
        User: {
          'user-1': 'object_read',
          'user-2': 'object_update',
        },
      }

      const { rows } = createRows()

      expect(rows.value[0].objectEntries).toHaveLength(2)
    })

    it('generates objectEntries from draft.extrasObjects', () => {
      draft.extrasObjects = {
        User: {
          'user-1': ['action_1'],
          'user-2': ['action_2'],
        },
      }

      const { rows } = createRows()

      expect(rows.value[0].objectEntries).toHaveLength(2)
    })

    it('combines objectEntries from objects and extrasObjects', () => {
      draft.objects = { User: { 'user-1': 'object_read' } }
      draft.extrasObjects = { User: { 'user-2': ['action_1'] } }

      const { rows } = createRows()

      expect(rows.value[0].objectEntries).toHaveLength(2)
    })

    it('filters out "none" entries when not editing', () => {
      draft.objects = {
        User: {
          'user-1': 'object_read',
          'user-2': 'none',
        },
      }
      isEditing.value = false

      const { rows } = createRows()

      expect(rows.value[0].objectEntries).toHaveLength(1)
      expect(rows.value[0].objectEntries[0].objectId).toBe('user-1')
    })

    it('includes "none" entries when editing', () => {
      draft.objects = {
        User: {
          'user-1': 'object_read',
          'user-2': 'none',
        },
      }
      isEditing.value = true

      const { rows } = createRows()

      expect(rows.value[0].objectEntries).toHaveLength(2)
    })

    it('sorts objectEntries by label', () => {
      draft.objects = {
        User: {
          'user-z': 'object_read',
          'user-a': 'object_read',
        },
      }
      getObjectLabelSync.mockImplementation((ot, id) =>
        id === 'user-z' ? 'Zara' : 'Adam',
      )

      const { rows } = createRows()

      expect(rows.value[0].objectEntries[0].objectId).toBe('user-a')
      expect(rows.value[0].objectEntries[1].objectId).toBe('user-z')
    })

    it('prefetches labels for object entries', () => {
      draft.objects = { User: { 'user-1': 'object_read' } }
      isEditing.value = true // Need editing mode to see all entries

      const { rows } = createRows()

      // Access rows.value to trigger computed evaluation
      const _ = rows.value

      expect(prefetchObjectLabel).toHaveBeenCalledWith('User', 'user-1')
    })
  })

  describe('Object Scope Support', () => {
    it('marks objectScopeAllowed as true by default', () => {
      draft.global = { User: 'object_read' }

      const { rows } = createRows()

      expect(rows.value[0].objectScopeAllowed).toBe(true)
    })

    it('marks objectScopeAllowed as false when model has no object scope', () => {
      draft.global = { User: 'object_read' }
      getObjectModelByBackendType.mockReturnValue({
        scopes: { global: true, object: false },
      })

      const { rows } = createRows()

      expect(rows.value[0].objectScopeAllowed).toBe(false)
    })

    it('returns empty objectEntries when object scope not allowed', () => {
      draft.objects = { User: { 'user-1': 'object_read' } }
      getObjectModelByBackendType.mockReturnValue({
        scopes: { global: true },
      })

      const { rows } = createRows()

      expect(rows.value[0].objectEntries).toHaveLength(0)
    })
  })

  describe('Allowed Keys', () => {
    it('returns null for allowedGlobalKeys when no model', () => {
      draft.global = { User: 'object_read' }

      const { rows } = createRows()

      expect(rows.value[0].allowedGlobalKeys).toBeNull()
    })

    it('returns allowed keys from model', () => {
      draft.global = { User: 'object_read' }
      getObjectModelByBackendType.mockReturnValue({
        scopes: { global: true, object: true },
        permissionKeys: {
          global: ['object_read', 'object_update', 'object_create'],
          object: ['object_read', 'object_update'],
        },
      })

      const { rows } = createRows()

      expect(rows.value[0].allowedGlobalKeys).toEqual([
        'object_read',
        'object_update',
        'object_create',
      ])
      expect(rows.value[0].allowedObjectKeys).toEqual([
        'object_read',
        'object_update',
      ])
    })

    it('returns empty array when scope not supported', () => {
      draft.global = { User: 'object_read' }
      getObjectModelByBackendType.mockReturnValue({
        scopes: { global: true },
        permissionKeys: {
          global: ['object_read'],
        },
      })

      const { rows } = createRows()

      expect(rows.value[0].allowedObjectKeys).toEqual([])
    })
  })

  describe('Filtering', () => {
    it('filters rows by objectModelQuery (label match)', () => {
      getAllObjectModelsSorted.mockReturnValue([
        { key: 'User', backendObjectTypes: ['User'], label: 'Benutzer' },
        { key: 'Role', backendObjectTypes: ['Role'], label: 'Rollen' },
      ])
      getObjectTypeLabel.mockImplementation((ot) =>
        ot === 'User' ? 'Benutzer' : 'Rollen',
      )
      objectModelQuery.value = 'benutzer'

      const { rows } = createRows()

      expect(rows.value).toHaveLength(1)
      expect(rows.value[0].objectType).toBe('User')
    })

    it('filters rows by objectModelQuery (backend match)', () => {
      getAllObjectModelsSorted.mockReturnValue([
        { key: 'User', backendObjectTypes: ['User'], label: 'Benutzer' },
        { key: 'Role', backendObjectTypes: ['Role'], label: 'Rollen' },
      ])
      objectModelQuery.value = 'user'

      const { rows } = createRows()

      expect(rows.value).toHaveLength(1)
    })

    it('shows all rows when query is empty', () => {
      getAllObjectModelsSorted.mockReturnValue([
        { key: 'User', backendObjectTypes: ['User'], label: 'Benutzer' },
        { key: 'Role', backendObjectTypes: ['Role'], label: 'Rollen' },
      ])
      objectModelQuery.value = ''

      const { rows } = createRows()

      expect(rows.value).toHaveLength(2)
    })

    it('is case insensitive', () => {
      getAllObjectModelsSorted.mockReturnValue([
        { key: 'User', backendObjectTypes: ['User'], label: 'Benutzer' },
      ])
      getObjectTypeLabel.mockReturnValue('Benutzer')
      objectModelQuery.value = 'BENUTZER'

      const { rows } = createRows()

      expect(rows.value).toHaveLength(1)
    })
  })

  describe('Only With Permissions Filter', () => {
    beforeEach(() => {
      getAllObjectModelsSorted.mockReturnValue([
        { key: 'User', backendObjectTypes: ['User'], label: 'Benutzer' },
        { key: 'Role', backendObjectTypes: ['Role'], label: 'Rollen' },
        { key: 'Event', backendObjectTypes: ['Event'], label: 'Events' },
      ])
    })

    it('shows all rows when onlyWithPermissions is false', () => {
      onlyWithPermissions.value = false

      const { rows } = createRows()

      expect(rows.value).toHaveLength(3)
    })

    it('filters out models without permissions when enabled', () => {
      draft.global = { User: 'object_read' }
      onlyWithPermissions.value = true

      const { rows } = createRows()

      expect(rows.value).toHaveLength(1)
      expect(rows.value[0].objectType).toBe('User')
    })

    it('keeps models with globalCreate permission', () => {
      draft.globalCreate = { Role: true }
      onlyWithPermissions.value = true

      const { rows } = createRows()

      expect(rows.value).toHaveLength(1)
      expect(rows.value[0].objectType).toBe('Role')
    })

    it('keeps models with global extras', () => {
      draft.extrasGlobal = { Event: ['object_reset'] }
      onlyWithPermissions.value = true

      const { rows } = createRows()

      expect(rows.value).toHaveLength(1)
      expect(rows.value[0].objectType).toBe('Event')
    })

    it('keeps models with object-scoped permissions', () => {
      draft.objects = { User: { 'user-1': 'object_update' } }
      onlyWithPermissions.value = true

      const { rows } = createRows()

      expect(rows.value).toHaveLength(1)
      expect(rows.value[0].objectType).toBe('User')
    })

    it('keeps models with object-scoped extras', () => {
      draft.extrasObjects = { Role: { 'role-1': ['action_approve'] } }
      onlyWithPermissions.value = true

      const { rows } = createRows()

      expect(rows.value).toHaveLength(1)
      expect(rows.value[0].objectType).toBe('Role')
    })

    it('filters out models with only "none" global level', () => {
      draft.global = { User: 'none', Role: 'object_read' }
      onlyWithPermissions.value = true

      const { rows } = createRows()

      expect(rows.value).toHaveLength(1)
      expect(rows.value[0].objectType).toBe('Role')
    })

    it('filters out models with only "none" object-scoped levels', () => {
      draft.objects = { User: { 'user-1': 'none' } }
      onlyWithPermissions.value = true

      const { rows } = createRows()

      expect(rows.value).toHaveLength(0)
    })

    it('filters out models with empty extras arrays', () => {
      draft.extrasGlobal = { User: [] }
      draft.extrasObjects = { Role: { 'role-1': [] } }
      onlyWithPermissions.value = true

      const { rows } = createRows()

      expect(rows.value).toHaveLength(0)
    })

    it('combines with text search filter', () => {
      draft.global = { User: 'object_read', Role: 'object_update' }
      getObjectTypeLabel.mockImplementation((ot) =>
        ot === 'User' ? 'Benutzer' : ot === 'Role' ? 'Rollen' : 'Events',
      )
      onlyWithPermissions.value = true
      objectModelQuery.value = 'benutzer'

      const { rows } = createRows()

      expect(rows.value).toHaveLength(1)
      expect(rows.value[0].objectType).toBe('User')
    })
  })

  describe('Expand/Collapse', () => {
    it('initializes expanded as false for each row', () => {
      getAllObjectModelsSorted.mockReturnValue([
        { key: 'User', backendObjectTypes: ['User'] },
      ])

      const { rows, expanded } = createRows()

      expect(rows.value[0].expanded).toBe(false)
      expect(expanded.User).toBe(false)
    })

    it('toggleExpanded toggles the expanded state', () => {
      getAllObjectModelsSorted.mockReturnValue([
        { key: 'User', backendObjectTypes: ['User'] },
      ])

      const { rows, expanded, toggleExpanded } = createRows()

      // Access rows.value to trigger initialization of expanded state
      const _ = rows.value

      expect(expanded.User).toBe(false)
      toggleExpanded('User')
      expect(expanded.User).toBe(true)
      toggleExpanded('User')
      expect(expanded.User).toBe(false)
    })

    it('allExpanded is true when all rows expanded', () => {
      getAllObjectModelsSorted.mockReturnValue([
        { key: 'User', backendObjectTypes: ['User'] },
        { key: 'Role', backendObjectTypes: ['Role'] },
      ])

      const { allExpanded, toggleExpanded } = createRows()

      expect(allExpanded.value).toBe(false)

      toggleExpanded('User')
      expect(allExpanded.value).toBe(false)

      toggleExpanded('Role')
      expect(allExpanded.value).toBe(true)
    })

    it('toggleAll expands all rows', () => {
      getAllObjectModelsSorted.mockReturnValue([
        { key: 'User', backendObjectTypes: ['User'] },
        { key: 'Role', backendObjectTypes: ['Role'] },
      ])

      const { expanded, allExpanded, toggleAll } = createRows()

      expect(allExpanded.value).toBe(false)

      toggleAll()

      expect(expanded.User).toBe(true)
      expect(expanded.Role).toBe(true)
      expect(allExpanded.value).toBe(true)
    })

    it('toggleAll collapses all when all expanded', () => {
      getAllObjectModelsSorted.mockReturnValue([
        { key: 'User', backendObjectTypes: ['User'] },
        { key: 'Role', backendObjectTypes: ['Role'] },
      ])

      const { expanded, toggleAll } = createRows()

      toggleAll() // expand all
      expect(expanded.User).toBe(true)

      toggleAll() // collapse all
      expect(expanded.User).toBe(false)
      expect(expanded.Role).toBe(false)
    })
  })

  describe('Sorting', () => {
    it('sorts rows by objectType label', () => {
      getAllObjectModelsSorted.mockReturnValue([
        { key: 'ZType', backendObjectTypes: ['ZType'] },
        { key: 'AType', backendObjectTypes: ['AType'] },
      ])
      getObjectTypeLabel.mockImplementation((ot) =>
        ot === 'ZType' ? 'Zebra' : 'Alpha',
      )

      const { rows } = createRows()

      expect(rows.value[0].objectType).toBe('AType')
      expect(rows.value[1].objectType).toBe('ZType')
    })
  })

  describe('Feature Flag Filtering', () => {
    it('shows model when featureFlag setting is active', () => {
      useMainStore.mockReturnValue({
        settings: { moodle: { enabled: true } },
      })
      getAllObjectModelsSorted.mockReturnValue([
        {
          key: 'MoodleCourse',
          backendObjectTypes: ['MoodleCourse'],
          label: 'Moodle-Kurse',
          featureFlag: 'moodle.enabled',
        },
      ])

      const { rows } = createRows()

      expect(rows.value).toHaveLength(1)
      expect(rows.value[0].objectType).toBe('MoodleCourse')
    })

    it('hides model when featureFlag setting is inactive', () => {
      useMainStore.mockReturnValue({
        settings: { moodle: { enabled: false } },
      })
      getAllObjectModelsSorted.mockReturnValue([
        {
          key: 'MoodleCourse',
          backendObjectTypes: ['MoodleCourse'],
          label: 'Moodle-Kurse',
          featureFlag: 'moodle.enabled',
        },
      ])

      const { rows } = createRows()

      expect(rows.value).toHaveLength(0)
    })

    it('shows model with inactive featureFlag when existing permissions reference it', () => {
      useMainStore.mockReturnValue({
        settings: { moodle: { enabled: false } },
      })
      getAllObjectModelsSorted.mockReturnValue([
        {
          key: 'MoodleCourse',
          backendObjectTypes: ['MoodleCourse'],
          label: 'Moodle-Kurse',
          featureFlag: 'moodle.enabled',
        },
      ])
      normalizePermission.mockImplementation((p) => ({
        entityId: p.entity_id,
        entityType: p.entity_type,
        objectType: p.object_type,
        objectId: p.object_id,
        permissionKey: p.permission_key,
      }))
      permissions.value = [
        {
          entity_id: entityId,
          entity_type: entityType,
          object_type: 'MoodleCourse',
          object_id: null,
          permission_key: 'object_read',
        },
      ]

      const { rows } = createRows()

      expect(rows.value).toHaveLength(1)
      expect(rows.value[0].objectType).toBe('MoodleCourse')
    })

    it('always shows model without featureFlag property', () => {
      useMainStore.mockReturnValue({ settings: {} })
      getAllObjectModelsSorted.mockReturnValue([
        {
          key: 'User',
          backendObjectTypes: ['User'],
          label: 'Benutzer',
        },
      ])

      const { rows } = createRows()

      expect(rows.value).toHaveLength(1)
      expect(rows.value[0].objectType).toBe('User')
    })
  })
})
