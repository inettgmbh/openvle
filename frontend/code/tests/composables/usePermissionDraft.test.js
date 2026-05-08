import { beforeEach, describe, expect, it } from 'vitest'
import { nextTick, ref } from 'vue'

import { usePermissionDraft } from '@/components/permissions/composables/usePermissionDraft'

function makePermission(objectType, permissionKey, objectId = null) {
  return {
    id: crypto.randomUUID(),
    entity_id: 'entity-1',
    entity_type: 'Role',
    object_type: objectType,
    object_id: objectId,
    permission_key: permissionKey,
  }
}

describe('usePermissionDraft', () => {
  let permissions

  beforeEach(() => {
    permissions = ref([])
  })

  describe('rebuild', () => {
    it('synchronously updates draft from current permissions', () => {
      const { draft, rebuild } = usePermissionDraft(
        permissions,
        'entity-1',
        'Role',
      )

      expect(Object.keys(draft.global)).toHaveLength(0)

      permissions.value = [
        makePermission('User', 'object_read'),
        makePermission('Event', 'object_full'),
      ]
      rebuild()

      expect(draft.global.User).toBe('object_read')
      expect(draft.global.Event).toBe('object_full')
    })

    it('processes all permissions into draft', () => {
      const { draft, rebuild } = usePermissionDraft(
        permissions,
        'entity-1',
        'Role',
      )

      permissions.value = [
        makePermission('User', 'object_read'),
        makePermission('User', 'object_create'),
        makePermission('Event', 'object_full'),
        makePermission('Template', 'object_update'),
        makePermission('VM', 'object_read', 'vm-1'),
      ]
      rebuild()

      expect(draft.global.User).toBe('object_read')
      expect(draft.globalCreate.User).toBe(true)
      expect(draft.global.Event).toBe('object_full')
      expect(draft.globalCreate.Event).toBe(true)
      expect(draft.global.Template).toBe('object_update')
      expect(draft.objects.VM?.['vm-1']).toBe('object_read')
    })

    it('does not overwrite draft during editing', () => {
      const { draft, rebuild, startEdit, setGlobal } = usePermissionDraft(
        permissions,
        'entity-1',
        'Role',
      )

      permissions.value = [makePermission('User', 'object_read')]
      rebuild()

      startEdit()
      setGlobal('User', 'object_full')

      // Rebuild with new data should not overwrite editing draft
      permissions.value = [
        ...permissions.value,
        makePermission('Event', 'object_read'),
      ]
      rebuild()

      expect(draft.global.User).toBe('object_full')
    })

    it('picks maxLevel when multiple permissions exist for same objectType', () => {
      const { draft, rebuild } = usePermissionDraft(
        permissions,
        'entity-1',
        'Role',
      )

      permissions.value = [
        makePermission('User', 'object_read'),
        makePermission('User', 'object_full'),
      ]
      rebuild()

      expect(draft.global.User).toBe('object_full')
    })

    it('handles empty permissions', () => {
      const { draft, rebuild } = usePermissionDraft(
        permissions,
        'entity-1',
        'Role',
      )

      permissions.value = []
      rebuild()

      expect(Object.keys(draft.global)).toHaveLength(0)
      expect(Object.keys(draft.globalCreate)).toHaveLength(0)
      expect(Object.keys(draft.objects)).toHaveLength(0)
    })
  })

  describe('watcher', () => {
    it('updates draft when permissions change', async () => {
      const { draft } = usePermissionDraft(permissions, 'entity-1', 'Role')

      permissions.value = [makePermission('User', 'object_read')]
      await nextTick()

      expect(draft.global.User).toBe('object_read')
    })
  })
})
