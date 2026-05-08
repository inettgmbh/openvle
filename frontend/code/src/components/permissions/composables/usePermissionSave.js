import { ref } from 'vue'
import { useToast } from 'vue-toastification'

import { getI18nT } from '@/i18n'
import backend from '@/services'
import { executeBatched } from '@/utils/batchedExecution'
import { collectIdsToDelete } from '@/utils/objectModelPermissions'

const t = getI18nT()
export function usePermissionSave(
  permissions,
  entityId,
  entityType,
  fetchPermissions,
  isEditing,
) {
  const toast = useToast()
  const dataLoading = ref(false)
  const pendingChanges = ref({ upserts: [], deletes: [] })

  // Progress tracking state
  const saveProgress = ref({
    isActive: false,
    phase: 'idle',
    current: 0,
    total: 0,
    errors: [],
  })

  function resetProgress() {
    saveProgress.value = {
      isActive: false,
      phase: 'idle',
      current: 0,
      total: 0,
      errors: [],
    }
  }

  function updateProgress(current, total) {
    saveProgress.value.current = current
    saveProgress.value.total = total
  }

  async function performSave() {
    const { upserts, deletes } = pendingChanges.value

    dataLoading.value = true
    resetProgress()

    // Collect IDs to delete
    const idsToDelete = collectIdsToDelete(
      deletes,
      upserts,
      permissions.value,
      entityId,
      entityType,
    )

    const deleteIds = [...idsToDelete]
    const totalOperations = deleteIds.length + upserts.length

    // Show progress modal if there are operations
    if (totalOperations > 0) {
      saveProgress.value.isActive = true
      saveProgress.value.total = totalOperations
    }

    const allErrors = []
    let completedCount = 0

    try {
      // Phase 1: Delete permissions
      if (deleteIds.length > 0) {
        saveProgress.value.phase = 'deleting'

        const deleteOperations = deleteIds.map(
          (id) => () => backend.objectPermissions.delete(id),
        )

        const { errors: deleteErrors } = await executeBatched(
          deleteOperations,
          {
            batchSize: 3,
            delayMs: 100,
            onProgress: (completed) => {
              updateProgress(completed, totalOperations)
            },
          },
        )

        if (deleteErrors.length > 0) {
          allErrors.push(
            ...deleteErrors.map((e) => ({
              ...e,
              type: 'delete',
              id: deleteIds[e.index],
            })),
          )
        }

        completedCount = deleteIds.length
      }

      // Phase 2: Create permissions
      if (upserts.length > 0) {
        saveProgress.value.phase = 'creating'

        const createOperations = upserts.map(
          (data) => () =>
            backend.objectPermissions.create({
              objectType: data.object_type,
              objectId: data.object_id,
              entityId: data.entity_id,
              entityType: data.entity_type,
              permissionKey: data.permission_key,
            }),
        )

        const { errors: createErrors } = await executeBatched(
          createOperations,
          {
            batchSize: 3,
            delayMs: 100,
            onProgress: (completed) => {
              updateProgress(completedCount + completed, totalOperations)
            },
          },
        )

        if (createErrors.length > 0) {
          allErrors.push(
            ...createErrors.map((e) => ({
              ...e,
              type: 'create',
              data: upserts[e.index],
            })),
          )
        }
      }

      // Phase 3: Refresh data
      saveProgress.value.phase = 'refreshing'
      await fetchPermissions()

      // Phase 4: Done
      saveProgress.value.phase = 'done'
      saveProgress.value.errors = allErrors

      if (allErrors.length === 0) {
        toast.success(t('components.permissionSave.saveSuccess'))
        isEditing.value = false
      } else {
        toast.warning(
          t('components.permissionSave.partialSave', {
            saved: totalOperations - allErrors.length,
            total: totalOperations,
          }),
        )
      }
    } catch (error) {
      console.error('Error saving permissions:', error)
      saveProgress.value.phase = 'error'
      saveProgress.value.errors = [{ index: -1, error }]
      toast.error(t('components.permissionSave.saveError'))
    } finally {
      dataLoading.value = false
    }
  }

  async function closeProgressModal() {
    const hadErrors = saveProgress.value.errors.length > 0

    if (hadErrors) {
      // Exit editing mode and refresh data for a clean state
      isEditing.value = false
      await fetchPermissions()
    }

    resetProgress()
  }

  return {
    dataLoading,
    pendingChanges,
    performSave,
    saveProgress,
    closeProgressModal,
  }
}
