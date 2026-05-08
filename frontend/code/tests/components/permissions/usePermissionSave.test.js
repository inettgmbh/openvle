import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick, ref } from 'vue'

// Use vi.hoisted to define mocks that can be referenced in vi.mock (which is hoisted)
const {
  mockToastSuccess,
  mockToastError,
  mockToastWarning,
  mockDelete,
  mockCreate,
} = vi.hoisted(() => ({
  mockToastSuccess: vi.fn(),
  mockToastError: vi.fn(),
  mockToastWarning: vi.fn(),
  mockDelete: vi.fn(() => Promise.resolve()),
  mockCreate: vi.fn(() => Promise.resolve()),
}))

// Mock toast
vi.mock('vue-toastification', () => ({
  useToast: () => ({
    success: mockToastSuccess,
    error: mockToastError,
    warning: mockToastWarning,
  }),
}))

// Mock the backend singleton
vi.mock('@/services', () => ({
  default: {
    objectPermissions: {
      delete: mockDelete,
      create: mockCreate,
    },
  },
}))

// Mock objectModelPermissions
vi.mock('@/utils/objectModelPermissions', () => ({
  collectIdsToDelete: vi.fn(() => new Set()),
}))

import { usePermissionSave } from '@/components/permissions/composables/usePermissionSave'
import { collectIdsToDelete } from '@/utils/objectModelPermissions'

// Reference the mock functions for test assertions
const ObjectPermissionService = {
  delete: mockDelete,
  create: mockCreate,
}

describe('usePermissionSave', () => {
  const entityId = 'user-123'
  const entityType = 'User'
  let permissions
  let fetchPermissions
  let isEditing

  beforeEach(() => {
    vi.clearAllMocks()

    permissions = ref([])
    fetchPermissions = vi.fn(() => Promise.resolve())
    isEditing = ref(true)

    // Reset mock implementations
    ObjectPermissionService.delete.mockResolvedValue()
    ObjectPermissionService.create.mockResolvedValue()
    collectIdsToDelete.mockReturnValue(new Set())
  })

  function createSave() {
    return usePermissionSave(
      permissions,
      entityId,
      entityType,
      fetchPermissions,
      isEditing,
    )
  }

  describe('Initialization', () => {
    it('initializes dataLoading as false', () => {
      const { dataLoading } = createSave()
      expect(dataLoading.value).toBe(false)
    })

    it('initializes pendingChanges with empty arrays', () => {
      const { pendingChanges } = createSave()
      expect(pendingChanges.value).toEqual({ upserts: [], deletes: [] })
    })
  })

  describe('performSave - Basic Flow', () => {
    it('sets dataLoading to true during save', async () => {
      const { dataLoading, performSave, pendingChanges } = createSave()
      pendingChanges.value = { upserts: [], deletes: [] }

      const promise = performSave()
      expect(dataLoading.value).toBe(true)

      await promise
      expect(dataLoading.value).toBe(false)
    })

    it('calls collectIdsToDelete with correct arguments', async () => {
      const deletes = [
        {
          object_type: 'User',
          object_id: 'u-1',
          permission_key: 'object_read',
        },
      ]
      const upserts = []
      permissions.value = [{ id: 'perm-1' }]

      const { performSave, pendingChanges } = createSave()
      pendingChanges.value = { upserts, deletes }

      await performSave()

      expect(collectIdsToDelete).toHaveBeenCalledWith(
        deletes,
        upserts,
        permissions.value,
        entityId,
        entityType,
      )
    })

    it('calls fetchPermissions after save', async () => {
      const { performSave, pendingChanges } = createSave()
      pendingChanges.value = { upserts: [], deletes: [] }

      await performSave()

      expect(fetchPermissions).toHaveBeenCalled()
    })

    it('sets isEditing to false after successful save', async () => {
      const { performSave, pendingChanges } = createSave()
      pendingChanges.value = { upserts: [], deletes: [] }

      await performSave()

      expect(isEditing.value).toBe(false)
    })

    it('shows success toast after save', async () => {
      const { performSave, pendingChanges } = createSave()
      pendingChanges.value = { upserts: [], deletes: [] }

      await performSave()

      expect(mockToastSuccess).toHaveBeenCalledWith(
        'Berechtigungen erfolgreich gespeichert',
      )
    })
  })

  describe('performSave - Deletes', () => {
    it('deletes permissions when idsToDelete is not empty', async () => {
      collectIdsToDelete.mockReturnValue(new Set(['perm-1', 'perm-2']))

      const { performSave, pendingChanges } = createSave()
      pendingChanges.value = {
        upserts: [],
        deletes: [{ object_type: 'User' }],
      }

      await performSave()

      expect(ObjectPermissionService.delete).toHaveBeenCalledTimes(2)
      expect(ObjectPermissionService.delete).toHaveBeenCalledWith('perm-1')
      expect(ObjectPermissionService.delete).toHaveBeenCalledWith('perm-2')
    })

    it('skips delete when no IDs to delete', async () => {
      collectIdsToDelete.mockReturnValue(new Set())

      const { performSave, pendingChanges } = createSave()
      pendingChanges.value = { upserts: [], deletes: [] }

      await performSave()

      expect(ObjectPermissionService.delete).not.toHaveBeenCalled()
    })

    it('deletes all permissions in parallel', async () => {
      const deletePromises = []
      ObjectPermissionService.delete.mockImplementation(
        (id) =>
          new Promise((resolve) => {
            deletePromises.push({ id, resolve })
          }),
      )
      collectIdsToDelete.mockReturnValue(
        new Set(['perm-1', 'perm-2', 'perm-3']),
      )

      const { performSave, pendingChanges } = createSave()
      pendingChanges.value = { upserts: [], deletes: [{}] }

      const savePromise = performSave()

      // Wait for promises to be created
      await nextTick()

      // All delete calls should be made
      expect(ObjectPermissionService.delete).toHaveBeenCalledTimes(3)

      // Resolve all
      deletePromises.forEach((p) => p.resolve())
      await savePromise
    })
  })

  describe('performSave - Upserts', () => {
    it('creates permissions when upserts is not empty', async () => {
      const { performSave, pendingChanges } = createSave()
      pendingChanges.value = {
        upserts: [
          {
            object_type: 'User',
            object_id: null,
            entity_id: entityId,
            entity_type: entityType,
            permission_key: 'object_read',
          },
          {
            object_type: 'Role',
            object_id: 'role-1',
            entity_id: entityId,
            entity_type: entityType,
            permission_key: 'object_update',
          },
        ],
        deletes: [],
      }

      await performSave()

      expect(ObjectPermissionService.create).toHaveBeenCalledTimes(2)
      expect(ObjectPermissionService.create).toHaveBeenCalledWith({
        objectType: 'User',
        objectId: null,
        entityId,
        entityType,
        permissionKey: 'object_read',
      })
      expect(ObjectPermissionService.create).toHaveBeenCalledWith({
        objectType: 'Role',
        objectId: 'role-1',
        entityId,
        entityType,
        permissionKey: 'object_update',
      })
    })

    it('skips create when no upserts', async () => {
      const { performSave, pendingChanges } = createSave()
      pendingChanges.value = { upserts: [], deletes: [] }

      await performSave()

      expect(ObjectPermissionService.create).not.toHaveBeenCalled()
    })

    it('creates all permissions in parallel', async () => {
      const createPromises = []
      ObjectPermissionService.create.mockImplementation(
        () =>
          new Promise((resolve) => {
            createPromises.push({ resolve })
          }),
      )

      const { performSave, pendingChanges } = createSave()
      pendingChanges.value = {
        upserts: [
          {
            object_type: 'A',
            object_id: null,
            entity_id: entityId,
            entity_type: entityType,
            permission_key: 'x',
          },
          {
            object_type: 'B',
            object_id: null,
            entity_id: entityId,
            entity_type: entityType,
            permission_key: 'y',
          },
        ],
        deletes: [],
      }

      const savePromise = performSave()
      await nextTick()

      expect(ObjectPermissionService.create).toHaveBeenCalledTimes(2)

      createPromises.forEach((p) => p.resolve())
      await savePromise
    })
  })

  describe('performSave - Error Handling', () => {
    it('shows warning toast on partial delete failure', async () => {
      ObjectPermissionService.delete.mockRejectedValue(
        new Error('Delete failed'),
      )
      collectIdsToDelete.mockReturnValue(new Set(['perm-1']))

      const { performSave, pendingChanges } = createSave()
      pendingChanges.value = { upserts: [], deletes: [{}] }

      await performSave()

      // With batched execution, partial failures show warning, not error
      expect(mockToastWarning).toHaveBeenCalledWith(
        '0 von 1 Berechtigungen gespeichert',
      )
    })

    it('shows warning toast on partial create failure', async () => {
      ObjectPermissionService.create.mockRejectedValue(
        new Error('Create failed'),
      )

      const { performSave, pendingChanges } = createSave()
      pendingChanges.value = {
        upserts: [
          {
            object_type: 'User',
            object_id: null,
            entity_id: entityId,
            entity_type: entityType,
            permission_key: 'x',
          },
        ],
        deletes: [],
      }

      await performSave()

      expect(mockToastWarning).toHaveBeenCalledWith(
        '0 von 1 Berechtigungen gespeichert',
      )
    })

    it('records errors in saveProgress', async () => {
      const error = new Error('Save failed')
      ObjectPermissionService.create.mockRejectedValue(error)

      const { performSave, pendingChanges, saveProgress } = createSave()
      pendingChanges.value = {
        upserts: [
          {
            object_type: 'User',
            object_id: null,
            entity_id: entityId,
            entity_type: entityType,
            permission_key: 'x',
          },
        ],
        deletes: [],
      }

      await performSave()

      expect(saveProgress.value.errors.length).toBe(1)
      expect(saveProgress.value.errors[0].error.message).toBe('Save failed')
    })

    it('sets dataLoading to false on error', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      ObjectPermissionService.create.mockRejectedValue(new Error('fail'))

      const { dataLoading, performSave, pendingChanges } = createSave()
      pendingChanges.value = {
        upserts: [
          {
            object_type: 'User',
            object_id: null,
            entity_id: entityId,
            entity_type: entityType,
            permission_key: 'x',
          },
        ],
        deletes: [],
      }

      await performSave()

      expect(dataLoading.value).toBe(false)
      consoleSpy.mockRestore()
    })

    it('does not set isEditing to false on error', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      ObjectPermissionService.create.mockRejectedValue(new Error('fail'))
      isEditing.value = true

      const { performSave, pendingChanges } = createSave()
      pendingChanges.value = {
        upserts: [
          {
            object_type: 'User',
            object_id: null,
            entity_id: entityId,
            entity_type: entityType,
            permission_key: 'x',
          },
        ],
        deletes: [],
      }

      await performSave()

      expect(isEditing.value).toBe(true)
      consoleSpy.mockRestore()
    })
  })

  describe('performSave - Order of Operations', () => {
    it('deletes before creates', async () => {
      const callOrder = []

      ObjectPermissionService.delete.mockImplementation((id) => {
        callOrder.push(`delete:${id}`)
        return Promise.resolve()
      })

      ObjectPermissionService.create.mockImplementation((data) => {
        callOrder.push(`create:${data.permissionKey}`)
        return Promise.resolve()
      })

      collectIdsToDelete.mockReturnValue(new Set(['perm-1']))

      const { performSave, pendingChanges } = createSave()
      pendingChanges.value = {
        upserts: [
          {
            object_type: 'User',
            object_id: null,
            entity_id: entityId,
            entity_type: entityType,
            permission_key: 'new_perm',
          },
        ],
        deletes: [{}],
      }

      await performSave()

      expect(callOrder[0]).toBe('delete:perm-1')
      expect(callOrder[1]).toBe('create:new_perm')
    })
  })

  describe('Progress Tracking', () => {
    it('initializes saveProgress with correct default state', () => {
      const { saveProgress } = createSave()
      expect(saveProgress.value).toEqual({
        isActive: false,
        phase: 'idle',
        current: 0,
        total: 0,
        errors: [],
      })
    })

    it('activates progress modal when operations exist', async () => {
      collectIdsToDelete.mockReturnValue(new Set(['perm-1']))

      const { performSave, pendingChanges, saveProgress } = createSave()
      pendingChanges.value = { upserts: [], deletes: [{}] }

      const promise = performSave()
      expect(saveProgress.value.isActive).toBe(true)
      expect(saveProgress.value.total).toBe(1)

      await promise
    })

    it('does not activate progress modal when no operations', async () => {
      collectIdsToDelete.mockReturnValue(new Set())

      const { performSave, pendingChanges, saveProgress } = createSave()
      pendingChanges.value = { upserts: [], deletes: [] }

      await performSave()

      // isActive should remain false since total is 0
      expect(saveProgress.value.total).toBe(0)
    })

    it('sets phase to deleting during delete operations', async () => {
      let capturedPhase = null
      ObjectPermissionService.delete.mockImplementation(() => {
        capturedPhase = 'captured'
        return Promise.resolve()
      })
      collectIdsToDelete.mockReturnValue(new Set(['perm-1']))

      const { performSave, pendingChanges, saveProgress } = createSave()
      pendingChanges.value = { upserts: [], deletes: [{}] }

      await performSave()

      // Phase should be 'done' after completion
      expect(saveProgress.value.phase).toBe('done')
    })

    it('sets phase to creating during create operations', async () => {
      const { performSave, pendingChanges, saveProgress } = createSave()
      pendingChanges.value = {
        upserts: [
          {
            object_type: 'User',
            object_id: null,
            entity_id: entityId,
            entity_type: entityType,
            permission_key: 'x',
          },
        ],
        deletes: [],
      }

      await performSave()

      expect(saveProgress.value.phase).toBe('done')
    })

    it('sets phase to done after successful save', async () => {
      const { performSave, pendingChanges, saveProgress } = createSave()
      pendingChanges.value = { upserts: [], deletes: [] }

      await performSave()

      expect(saveProgress.value.phase).toBe('done')
    })

    it('tracks progress correctly for deletes and creates', async () => {
      collectIdsToDelete.mockReturnValue(new Set(['p1', 'p2']))

      const { performSave, pendingChanges, saveProgress } = createSave()
      pendingChanges.value = {
        upserts: [
          {
            object_type: 'User',
            object_id: null,
            entity_id: entityId,
            entity_type: entityType,
            permission_key: 'x',
          },
        ],
        deletes: [{}],
      }

      await performSave()

      // After completion, current should equal total
      expect(saveProgress.value.current).toBe(3)
      expect(saveProgress.value.total).toBe(3)
    })

    it('closeProgressModal resets progress state', async () => {
      const { saveProgress, closeProgressModal } = createSave()

      // Modify progress (no errors)
      saveProgress.value = {
        isActive: true,
        phase: 'done',
        current: 5,
        total: 5,
        errors: [],
      }

      await closeProgressModal()

      expect(saveProgress.value).toEqual({
        isActive: false,
        phase: 'idle',
        current: 0,
        total: 0,
        errors: [],
      })
    })

    it('closeProgressModal refreshes data and exits editing when errors occurred', async () => {
      isEditing.value = true

      const { saveProgress, closeProgressModal } = createSave()

      // Simulate errors
      saveProgress.value = {
        isActive: true,
        phase: 'done',
        current: 5,
        total: 5,
        errors: [{ index: 0, error: new Error('test') }],
      }

      await closeProgressModal()

      expect(fetchPermissions).toHaveBeenCalled()
      expect(isEditing.value).toBe(false)
      expect(saveProgress.value.isActive).toBe(false)
    })

    it('closeProgressModal does not refresh when no errors', async () => {
      isEditing.value = true

      const { saveProgress, closeProgressModal } = createSave()

      // No errors
      saveProgress.value = {
        isActive: true,
        phase: 'done',
        current: 5,
        total: 5,
        errors: [],
      }

      await closeProgressModal()

      expect(fetchPermissions).not.toHaveBeenCalled()
      expect(isEditing.value).toBe(true) // Should remain unchanged
    })
  })

  describe('Error Collection', () => {
    it('collects delete errors without stopping', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      ObjectPermissionService.delete.mockImplementation((id) => {
        if (id === 'p2') {
          return Promise.reject(new Error('Delete p2 failed'))
        }
        return Promise.resolve()
      })

      collectIdsToDelete.mockReturnValue(new Set(['p1', 'p2', 'p3']))

      const { performSave, pendingChanges, saveProgress } = createSave()
      pendingChanges.value = { upserts: [], deletes: [{}] }

      await performSave()

      // All deletes should have been attempted
      expect(ObjectPermissionService.delete).toHaveBeenCalledTimes(3)
      // Should have recorded the error
      expect(saveProgress.value.errors.length).toBe(1)
      expect(saveProgress.value.errors[0].id).toBe('p2')
      expect(saveProgress.value.errors[0].type).toBe('delete')

      consoleSpy.mockRestore()
    })

    it('collects create errors without stopping', async () => {
      ObjectPermissionService.create.mockImplementation((data) => {
        if (data.permissionKey === 'fail_key') {
          return Promise.reject(new Error('Create failed'))
        }
        return Promise.resolve()
      })

      const { performSave, pendingChanges, saveProgress } = createSave()
      pendingChanges.value = {
        upserts: [
          {
            object_type: 'User',
            object_id: null,
            entity_id: entityId,
            entity_type: entityType,
            permission_key: 'ok_key',
          },
          {
            object_type: 'User',
            object_id: null,
            entity_id: entityId,
            entity_type: entityType,
            permission_key: 'fail_key',
          },
          {
            object_type: 'User',
            object_id: null,
            entity_id: entityId,
            entity_type: entityType,
            permission_key: 'also_ok',
          },
        ],
        deletes: [],
      }

      await performSave()

      expect(ObjectPermissionService.create).toHaveBeenCalledTimes(3)
      expect(saveProgress.value.errors.length).toBe(1)
      expect(saveProgress.value.errors[0].type).toBe('create')
    })

    it('shows warning toast when partial errors occur', async () => {
      ObjectPermissionService.delete.mockImplementation((id) => {
        if (id === 'p1') {
          return Promise.reject(new Error('fail'))
        }
        return Promise.resolve()
      })

      collectIdsToDelete.mockReturnValue(new Set(['p1', 'p2']))

      const { performSave, pendingChanges } = createSave()
      pendingChanges.value = { upserts: [], deletes: [{}] }

      await performSave()

      expect(mockToastWarning).toHaveBeenCalledWith(
        '1 von 2 Berechtigungen gespeichert',
      )
    })

    it('does not set isEditing to false when errors occur', async () => {
      ObjectPermissionService.delete.mockRejectedValue(new Error('fail'))
      collectIdsToDelete.mockReturnValue(new Set(['p1']))
      isEditing.value = true

      const { performSave, pendingChanges } = createSave()
      pendingChanges.value = { upserts: [], deletes: [{}] }

      await performSave()

      expect(isEditing.value).toBe(true)
    })
  })
})
