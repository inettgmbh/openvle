import { beforeEach, describe, expect, it, vi } from 'vitest'
import { computed, ref } from 'vue'

import { usePermissionBulkActions } from '@/components/permissions/composables/usePermissionBulkActions'

describe('usePermissionBulkActions', () => {
  let isEditing
  let rows
  let setGlobal
  let setGlobalCreate
  let setGlobalExtras
  let setObject
  let setObjectExtras

  beforeEach(() => {
    isEditing = ref(false)
    rows = computed(() => [])
    setGlobal = vi.fn()
    setGlobalCreate = vi.fn()
    setGlobalExtras = vi.fn()
    setObject = vi.fn()
    setObjectExtras = vi.fn()
  })

  function createComposable(rowsData = []) {
    rows = computed(() => rowsData)
    return usePermissionBulkActions({
      isEditing,
      rows,
      setGlobal,
      setGlobalCreate,
      setGlobalExtras,
      setObject,
      setObjectExtras,
    })
  }

  describe('deselectAll', () => {
    it('does nothing when not editing', () => {
      const { deselectAll } = createComposable([
        {
          objectType: 'User',
          allowedGlobalKeys: ['object_read'],
          objectEntries: [],
        },
      ])

      deselectAll()

      expect(setGlobal).not.toHaveBeenCalled()
      expect(setGlobalCreate).not.toHaveBeenCalled()
      expect(setGlobalExtras).not.toHaveBeenCalled()
    })

    it('sets all global permissions to none when editing', () => {
      isEditing.value = true
      const { deselectAll } = createComposable([
        {
          objectType: 'User',
          allowedGlobalKeys: ['object_full'],
          objectEntries: [],
        },
        {
          objectType: 'Role',
          allowedGlobalKeys: ['object_read'],
          objectEntries: [],
        },
      ])

      deselectAll()

      expect(setGlobal).toHaveBeenCalledWith('User', 'none')
      expect(setGlobal).toHaveBeenCalledWith('Role', 'none')
      expect(setGlobalCreate).toHaveBeenCalledWith('User', false)
      expect(setGlobalCreate).toHaveBeenCalledWith('Role', false)
      expect(setGlobalExtras).toHaveBeenCalledWith('User', [])
      expect(setGlobalExtras).toHaveBeenCalledWith('Role', [])
    })

    it('resets object-scoped permissions to none', () => {
      isEditing.value = true
      const { deselectAll } = createComposable([
        {
          objectType: 'User',
          allowedGlobalKeys: ['object_full'],
          objectEntries: [{ objectId: 'user-1' }, { objectId: 'user-2' }],
        },
      ])

      deselectAll()

      expect(setObject).toHaveBeenCalledWith('User', 'user-1', 'none')
      expect(setObject).toHaveBeenCalledWith('User', 'user-2', 'none')
      expect(setObjectExtras).toHaveBeenCalledWith('User', 'user-1', [])
      expect(setObjectExtras).toHaveBeenCalledWith('User', 'user-2', [])
    })

    it('handles empty rows', () => {
      isEditing.value = true
      const { deselectAll } = createComposable([])

      deselectAll()

      expect(setGlobal).not.toHaveBeenCalled()
    })
  })

  describe('selectAll', () => {
    it('does nothing when not editing', () => {
      const { selectAll } = createComposable([
        {
          objectType: 'User',
          allowedGlobalKeys: ['object_read'],
          objectEntries: [],
        },
      ])

      selectAll()

      expect(setGlobal).not.toHaveBeenCalled()
    })

    it('selects object_full when available', () => {
      isEditing.value = true
      const { selectAll } = createComposable([
        {
          objectType: 'User',
          allowedGlobalKeys: [
            'object_create',
            'object_read',
            'object_update',
            'object_delete',
            'object_full',
          ],
          objectEntries: [],
        },
      ])

      selectAll()

      expect(setGlobal).toHaveBeenCalledWith('User', 'object_full')
      expect(setGlobalCreate).toHaveBeenCalledWith('User', false)
      expect(setGlobalExtras).toHaveBeenCalledWith('User', [])
    })

    it('selects highest level when object_full is not available', () => {
      isEditing.value = true
      const { selectAll } = createComposable([
        {
          objectType: 'Activity',
          allowedGlobalKeys: ['object_read'],
          objectEntries: [],
        },
      ])

      selectAll()

      expect(setGlobal).toHaveBeenCalledWith('Activity', 'object_read')
      expect(setGlobalCreate).toHaveBeenCalledWith('Activity', false)
      expect(setGlobalExtras).toHaveBeenCalledWith('Activity', [])
    })

    it('selects object_delete as highest when available', () => {
      isEditing.value = true
      const { selectAll } = createComposable([
        {
          objectType: 'Template',
          allowedGlobalKeys: ['object_read', 'object_update', 'object_delete'],
          objectEntries: [],
        },
      ])

      selectAll()

      expect(setGlobal).toHaveBeenCalledWith('Template', 'object_delete')
    })

    it('selects object_update as highest when object_delete is not available', () => {
      isEditing.value = true
      const { selectAll } = createComposable([
        {
          objectType: 'System',
          allowedGlobalKeys: ['object_read', 'object_update'],
          objectEntries: [],
        },
      ])

      selectAll()

      expect(setGlobal).toHaveBeenCalledWith('System', 'object_update')
    })

    it('enables create when available and no object_full', () => {
      isEditing.value = true
      const { selectAll } = createComposable([
        {
          objectType: 'Document',
          allowedGlobalKeys: ['object_create', 'object_read', 'object_update'],
          objectEntries: [],
        },
      ])

      selectAll()

      expect(setGlobalCreate).toHaveBeenCalledWith('Document', true)
    })

    it('sets only object_admins for Dashboard (special case)', () => {
      isEditing.value = true
      const { selectAll } = createComposable([
        {
          objectType: 'Dashboard',
          allowedGlobalKeys: ['object_admins', 'object_verwaltende'],
          objectEntries: [],
        },
      ])

      selectAll()

      expect(setGlobal).toHaveBeenCalledWith('Dashboard', 'none')
      expect(setGlobalCreate).toHaveBeenCalledWith('Dashboard', false)
      // Only object_admins, not object_verwaltende
      expect(setGlobalExtras).toHaveBeenCalledWith('Dashboard', [
        'object_admins',
      ])
    })

    it('sets extras for object types with special permissions', () => {
      isEditing.value = true
      const { selectAll } = createComposable([
        {
          objectType: 'Mail',
          allowedGlobalKeys: ['object_read', 'object_send', 'object_send_bulk'],
          objectEntries: [],
        },
      ])

      selectAll()

      expect(setGlobal).toHaveBeenCalledWith('Mail', 'object_read')
      expect(setGlobalExtras).toHaveBeenCalledWith('Mail', [
        'object_send',
        'object_send_bulk',
      ])
    })

    it('does not modify object-scoped permissions', () => {
      isEditing.value = true
      const { selectAll } = createComposable([
        {
          objectType: 'User',
          allowedGlobalKeys: ['object_full'],
          objectEntries: [{ objectId: 'user-1' }],
        },
      ])

      selectAll()

      expect(setObject).not.toHaveBeenCalled()
      expect(setObjectExtras).not.toHaveBeenCalled()
    })

    it('skips rows with empty allowedGlobalKeys', () => {
      isEditing.value = true
      const { selectAll } = createComposable([
        { objectType: 'Empty', allowedGlobalKeys: [], objectEntries: [] },
        {
          objectType: 'User',
          allowedGlobalKeys: ['object_full'],
          objectEntries: [],
        },
      ])

      selectAll()

      expect(setGlobal).not.toHaveBeenCalledWith('Empty', expect.anything())
      expect(setGlobal).toHaveBeenCalledWith('User', 'object_full')
    })

    it('skips rows with null allowedGlobalKeys', () => {
      isEditing.value = true
      const { selectAll } = createComposable([
        { objectType: 'Null', allowedGlobalKeys: null, objectEntries: [] },
      ])

      selectAll()

      expect(setGlobal).not.toHaveBeenCalled()
    })

    it('handles VM with action permissions', () => {
      isEditing.value = true
      const { selectAll } = createComposable([
        {
          objectType: 'VirtualMachine',
          allowedGlobalKeys: [
            'object_create',
            'object_read',
            'object_update',
            'object_delete',
            'object_full',
            'object_reset',
            'object_actions_start',
            'object_actions_stop',
          ],
          objectEntries: [],
        },
      ])

      selectAll()

      // Should select object_full (clears extras)
      expect(setGlobal).toHaveBeenCalledWith('VirtualMachine', 'object_full')
      expect(setGlobalExtras).toHaveBeenCalledWith('VirtualMachine', [])
    })

    it('handles multiple object types correctly', () => {
      isEditing.value = true
      const { selectAll } = createComposable([
        {
          objectType: 'User',
          allowedGlobalKeys: ['object_full'],
          objectEntries: [],
        },
        {
          objectType: 'Dashboard',
          allowedGlobalKeys: ['object_admins', 'object_verwaltende'],
          objectEntries: [],
        },
        {
          objectType: 'Activity',
          allowedGlobalKeys: ['object_read'],
          objectEntries: [],
        },
      ])

      selectAll()

      // User: has object_full
      expect(setGlobal).toHaveBeenCalledWith('User', 'object_full')

      // Dashboard: special case - only object_admins
      expect(setGlobal).toHaveBeenCalledWith('Dashboard', 'none')
      expect(setGlobalExtras).toHaveBeenCalledWith('Dashboard', [
        'object_admins',
      ])

      // Activity: only object_read
      expect(setGlobal).toHaveBeenCalledWith('Activity', 'object_read')
    })
  })

  describe('Edge Cases', () => {
    it('handles rows with undefined allowedGlobalKeys', () => {
      isEditing.value = true
      const { selectAll, deselectAll } = createComposable([
        { objectType: 'Test', objectEntries: [] },
      ])

      // Should not throw
      expect(() => selectAll()).not.toThrow()
      expect(() => deselectAll()).not.toThrow()
    })

    it('handles rows with undefined objectEntries', () => {
      isEditing.value = true
      rows = computed(() => [
        { objectType: 'Test', allowedGlobalKeys: ['object_read'] },
      ])
      const { deselectAll } = usePermissionBulkActions({
        isEditing,
        rows,
        setGlobal,
        setGlobalCreate,
        setGlobalExtras,
        setObject,
        setObjectExtras,
      })

      // Should not throw when objectEntries is undefined
      expect(() => deselectAll()).not.toThrow()
    })
  })
})
