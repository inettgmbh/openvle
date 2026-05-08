import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick, ref } from 'vue'

// Mock objectModelPermissions before importing
vi.mock('@/utils/objectModelPermissions', () => ({
  buildSnapshot: vi.fn((permissions, entityId, entityType) => ({
    global: {},
    globalCreate: {},
    objects: {},
    extrasGlobal: {},
    extrasObjects: {},
  })),
  calculateChanges: vi.fn((original, after, entityId, entityType) => ({
    upserts: [],
    deletes: [],
  })),
}))

import { usePermissionDraft } from '@/components/permissions/composables/usePermissionDraft'
import { buildSnapshot, calculateChanges } from '@/utils/objectModelPermissions'

describe('usePermissionDraft', () => {
  const entityId = 'user-123'
  const entityType = 'User'
  let permissions

  beforeEach(() => {
    vi.clearAllMocks()
    permissions = ref([])

    // Default mock implementation
    buildSnapshot.mockImplementation(() => ({
      global: {},
      globalCreate: {},
      objects: {},
      extrasGlobal: {},
      extrasObjects: {},
    }))
  })

  describe('Initialization', () => {
    it('initializes with isEditing as false', () => {
      const { isEditing } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )
      expect(isEditing.value).toBe(false)
    })

    it('initializes draft from buildSnapshot', () => {
      buildSnapshot.mockReturnValue({
        global: { User: 'object_read' },
        globalCreate: { User: true },
        objects: {},
        extrasGlobal: {},
        extrasObjects: {},
      })

      const { draft } = usePermissionDraft(permissions, entityId, entityType)

      expect(draft.global).toEqual({ User: 'object_read' })
      expect(draft.globalCreate).toEqual({ User: true })
    })

    it('hasChanges is false initially', () => {
      const { hasChanges } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )
      expect(hasChanges.value).toBe(false)
    })
  })

  describe('Edit Mode', () => {
    it('startEdit sets isEditing to true', () => {
      const { isEditing, startEdit } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      expect(isEditing.value).toBe(true)
    })

    it('cancelEdit sets isEditing to false', () => {
      const { isEditing, startEdit, cancelEdit } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      expect(isEditing.value).toBe(true)

      cancelEdit()
      expect(isEditing.value).toBe(false)
    })

    it('cancelEdit resets draft to original', () => {
      // Mock needs to return the same object structure on each call
      const snapshotData = {
        global: { User: 'object_read' },
        globalCreate: {},
        objects: {},
        extrasGlobal: {},
        extrasObjects: {},
      }
      buildSnapshot.mockImplementation(() => ({
        global: { ...snapshotData.global },
        globalCreate: { ...snapshotData.globalCreate },
        objects: { ...snapshotData.objects },
        extrasGlobal: { ...snapshotData.extrasGlobal },
        extrasObjects: { ...snapshotData.extrasObjects },
      }))

      const { draft, startEdit, setGlobal, cancelEdit } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      setGlobal('User', 'object_full')
      expect(draft.global.User).toBe('object_full')

      cancelEdit()
      expect(draft.global.User).toBe('object_read')
    })
  })

  describe('setGlobal', () => {
    it('does nothing when not editing', () => {
      const { draft, setGlobal } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      setGlobal('User', 'object_read')
      expect(draft.global.User).toBeUndefined()
    })

    it('sets global permission when editing', () => {
      const { draft, startEdit, setGlobal } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      setGlobal('User', 'object_read')
      expect(draft.global.User).toBe('object_read')
    })

    it('deletes global permission when level is "none"', () => {
      const snapshotData = {
        global: { User: 'object_read' },
        globalCreate: {},
        objects: {},
        extrasGlobal: {},
        extrasObjects: {},
      }
      buildSnapshot.mockImplementation(() => ({
        global: { ...snapshotData.global },
        globalCreate: { ...snapshotData.globalCreate },
        objects: { ...snapshotData.objects },
        extrasGlobal: { ...snapshotData.extrasGlobal },
        extrasObjects: { ...snapshotData.extrasObjects },
      }))

      const { draft, startEdit, setGlobal } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      expect(draft.global.User).toBe('object_read')

      setGlobal('User', 'none')
      expect(draft.global.User).toBeUndefined()
    })

    it('overwrites existing global permission', () => {
      const { draft, startEdit, setGlobal } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      setGlobal('User', 'object_read')
      expect(draft.global.User).toBe('object_read')

      setGlobal('User', 'object_update')
      expect(draft.global.User).toBe('object_update')
    })
  })

  describe('setGlobalCreate', () => {
    it('does nothing when not editing', () => {
      const { draft, setGlobalCreate } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      setGlobalCreate('User', true)
      expect(draft.globalCreate.User).toBeUndefined()
    })

    it('sets globalCreate when enabled is true', () => {
      const { draft, startEdit, setGlobalCreate } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      setGlobalCreate('User', true)
      expect(draft.globalCreate.User).toBe(true)
    })

    it('deletes globalCreate when enabled is false', () => {
      const snapshotData = {
        global: {},
        globalCreate: { User: true },
        objects: {},
        extrasGlobal: {},
        extrasObjects: {},
      }
      buildSnapshot.mockImplementation(() => ({
        global: { ...snapshotData.global },
        globalCreate: { ...snapshotData.globalCreate },
        objects: { ...snapshotData.objects },
        extrasGlobal: { ...snapshotData.extrasGlobal },
        extrasObjects: { ...snapshotData.extrasObjects },
      }))

      const { draft, startEdit, setGlobalCreate } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      expect(draft.globalCreate.User).toBe(true)

      setGlobalCreate('User', false)
      expect(draft.globalCreate.User).toBeUndefined()
    })
  })

  describe('setGlobalExtras', () => {
    it('does nothing when not editing', () => {
      const { draft, setGlobalExtras } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      setGlobalExtras('User', ['action_1'])
      expect(draft.extrasGlobal?.User).toBeUndefined()
    })

    it('sets extrasGlobal array', () => {
      const { draft, startEdit, setGlobalExtras } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      setGlobalExtras('User', ['action_1', 'action_2'])
      expect(draft.extrasGlobal.User).toEqual(['action_1', 'action_2'])
    })

    it('removes duplicates from extras', () => {
      const { draft, startEdit, setGlobalExtras } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      setGlobalExtras('User', ['action_1', 'action_1', 'action_2'])
      expect(draft.extrasGlobal.User).toEqual(['action_1', 'action_2'])
    })

    it('deletes extrasGlobal when empty array', () => {
      buildSnapshot.mockReturnValue({
        global: {},
        globalCreate: {},
        objects: {},
        extrasGlobal: { User: ['action_1'] },
        extrasObjects: {},
      })

      const { draft, startEdit, setGlobalExtras } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      setGlobalExtras('User', [])
      expect(draft.extrasGlobal.User).toBeUndefined()
    })

    it('converts non-array to empty', () => {
      const { draft, startEdit, setGlobalExtras } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      setGlobalExtras('User', null)
      expect(draft.extrasGlobal.User).toBeUndefined()
    })
  })

  describe('setObject', () => {
    it('does nothing when not editing', () => {
      const { draft, setObject } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      setObject('User', 'user-456', 'object_read')
      expect(draft.objects.User).toBeUndefined()
    })

    it('sets object-scoped permission', () => {
      const { draft, startEdit, setObject } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      setObject('User', 'user-456', 'object_read')
      expect(draft.objects.User['user-456']).toBe('object_read')
    })

    it('ignores object_create level', () => {
      const { draft, startEdit, setObject } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      setObject('User', 'user-456', 'object_create')
      expect(draft.objects.User).toBeUndefined()
    })

    it('sets "none" level instead of deleting', () => {
      buildSnapshot.mockReturnValue({
        global: {},
        globalCreate: {},
        objects: { User: { 'user-456': 'object_read' } },
        extrasGlobal: {},
        extrasObjects: {},
      })

      const { draft, startEdit, setObject } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      setObject('User', 'user-456', 'none')
      expect(draft.objects.User['user-456']).toBe('none')
    })

    it('creates objectType key if not exists', () => {
      const { draft, startEdit, setObject } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      expect(draft.objects.NewType).toBeUndefined()
      setObject('NewType', 'obj-123', 'object_read')
      expect(draft.objects.NewType['obj-123']).toBe('object_read')
    })
  })

  describe('setObjectExtras', () => {
    it('does nothing when not editing', () => {
      const { draft, setObjectExtras } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      setObjectExtras('User', 'user-456', ['action_1'])
      expect(draft.extrasObjects?.User).toBeUndefined()
    })

    it('sets object-scoped extras', () => {
      const { draft, startEdit, setObjectExtras } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      setObjectExtras('User', 'user-456', ['action_1', 'action_2'])
      expect(draft.extrasObjects.User['user-456']).toEqual([
        'action_1',
        'action_2',
      ])
    })

    it('removes duplicates from object extras', () => {
      const { draft, startEdit, setObjectExtras } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      setObjectExtras('User', 'user-456', ['action_1', 'action_1'])
      expect(draft.extrasObjects.User['user-456']).toEqual(['action_1'])
    })

    it('cleans up empty objectType when removing last extra', () => {
      buildSnapshot.mockReturnValue({
        global: {},
        globalCreate: {},
        objects: {},
        extrasGlobal: {},
        extrasObjects: { User: { 'user-456': ['action_1'] } },
      })

      const { draft, startEdit, setObjectExtras } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      setObjectExtras('User', 'user-456', [])
      expect(draft.extrasObjects.User).toBeUndefined()
    })
  })

  describe('hasChanges', () => {
    it('detects changes in global', () => {
      const { hasChanges, startEdit, setGlobal } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      expect(hasChanges.value).toBe(false)

      startEdit()
      setGlobal('User', 'object_read')

      expect(hasChanges.value).toBe(true)
    })

    it('detects changes in globalCreate', () => {
      const { hasChanges, startEdit, setGlobalCreate } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      setGlobalCreate('User', true)

      expect(hasChanges.value).toBe(true)
    })

    it('detects changes in objects', () => {
      const { hasChanges, startEdit, setObject } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      setObject('User', 'user-456', 'object_read')

      expect(hasChanges.value).toBe(true)
    })

    it('detects changes in extrasGlobal', () => {
      const { hasChanges, startEdit, setGlobalExtras } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      setGlobalExtras('User', ['action_1'])

      expect(hasChanges.value).toBe(true)
    })

    it('detects changes in extrasObjects', () => {
      const { hasChanges, startEdit, setObjectExtras } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      setObjectExtras('User', 'user-456', ['action_1'])

      expect(hasChanges.value).toBe(true)
    })

    it('returns false when changes are reverted', () => {
      const { hasChanges, startEdit, setGlobal } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      setGlobal('User', 'object_read')
      expect(hasChanges.value).toBe(true)

      setGlobal('User', 'none')
      expect(hasChanges.value).toBe(false)
    })
  })

  describe('toUpsertsAndDeletes', () => {
    it('calls calculateChanges with correct arguments', () => {
      const { startEdit, setGlobal, toUpsertsAndDeletes } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      setGlobal('User', 'object_read')
      toUpsertsAndDeletes()

      expect(calculateChanges).toHaveBeenCalledWith(
        expect.any(Object),
        expect.objectContaining({
          global: { User: 'object_read' },
        }),
        entityId,
        entityType,
      )
    })

    it('returns upserts and deletes from calculateChanges', () => {
      calculateChanges.mockReturnValue({
        upserts: [{ permission_key: 'object_read' }],
        deletes: [{ permission_key: 'object_update' }],
      })

      const { startEdit, toUpsertsAndDeletes } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      const result = toUpsertsAndDeletes()

      expect(result.upserts).toHaveLength(1)
      expect(result.deletes).toHaveLength(1)
    })
  })

  describe('Watch Permissions', () => {
    it('updates original when permissions change', async () => {
      const newSnapshot = {
        global: { Role: 'object_full' },
        globalCreate: {},
        objects: {},
        extrasGlobal: {},
        extrasObjects: {},
      }

      buildSnapshot.mockReturnValue({
        global: {},
        globalCreate: {},
        objects: {},
        extrasGlobal: {},
        extrasObjects: {},
      })

      const { draft } = usePermissionDraft(permissions, entityId, entityType)

      buildSnapshot.mockReturnValue(newSnapshot)
      permissions.value = [{ some: 'data' }]

      await nextTick()

      expect(draft.global).toEqual({ Role: 'object_full' })
    })

    it('preserves draft when editing and permissions change', async () => {
      buildSnapshot.mockReturnValue({
        global: {},
        globalCreate: {},
        objects: {},
        extrasGlobal: {},
        extrasObjects: {},
      })

      const { draft, startEdit, setGlobal } = usePermissionDraft(
        permissions,
        entityId,
        entityType,
      )

      startEdit()
      setGlobal('User', 'object_read')

      buildSnapshot.mockReturnValue({
        global: { Role: 'object_full' },
        globalCreate: {},
        objects: {},
        extrasGlobal: {},
        extrasObjects: {},
      })
      permissions.value = [{ some: 'data' }]

      await nextTick()

      // Draft should be preserved while editing
      expect(draft.global.User).toBe('object_read')
    })
  })
})
