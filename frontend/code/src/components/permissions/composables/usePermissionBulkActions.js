/**
 * Composable for bulk permission actions (select all / deselect all).
 *
 * @param {Object} options
 * @param {import('vue').Ref<boolean>} options.isEditing - Whether edit mode is active
 * @param {import('vue').ComputedRef<Array>} options.rows - Permission rows from usePermissionRows
 * @param {Function} options.setGlobal - Set global permission level
 * @param {Function} options.setGlobalCreate - Set global create permission
 * @param {Function} options.setGlobalExtras - Set global extra permissions
 * @param {Function} options.setObject - Set object-scoped permission level
 * @param {Function} options.setObjectExtras - Set object-scoped extra permissions
 */
export function usePermissionBulkActions({
  isEditing,
  rows,
  setGlobal,
  setGlobalCreate,
  setGlobalExtras,
  setObject,
  setObjectExtras,
}) {
  /**
   * Level keys in order of priority (highest first).
   */
  const LEVEL_KEYS_BY_PRIORITY = [
    'object_delete',
    'object_update',
    'object_read',
  ]

  /**
   * Keys that are considered level keys (not extras).
   */
  const LEVEL_KEY_SET = new Set([
    'object_create',
    'object_read',
    'object_update',
    'object_delete',
    'object_full',
  ])

  /**
   * Deselects all permissions (global and object-scoped) for all object types.
   * Sets everything to 'none' and clears all extras.
   */
  function deselectAll() {
    if (!isEditing.value) return

    for (const row of rows.value) {
      // Reset global permissions
      setGlobal(row.objectType, 'none')
      setGlobalCreate(row.objectType, false)
      setGlobalExtras(row.objectType, [])

      // Reset object-scoped permissions
      for (const entry of row.objectEntries ?? []) {
        setObject(row.objectType, entry.objectId, 'none')
        setObjectExtras(row.objectType, entry.objectId, [])
      }
    }
  }

  /**
   * Selects maximum global permissions for all object types.
   * - If object_full is available: selects Vollzugriff
   * - For Dashboard (object_admins available): selects only object_admins
   * - For others without object_full: selects highest level + all extras
   * Object-scoped permissions remain unchanged (none).
   */
  function selectAll() {
    if (!isEditing.value) return

    for (const row of rows.value) {
      const allowedKeys = row.allowedGlobalKeys ?? []

      if (allowedKeys.length === 0) continue

      // Check if object_full is available
      if (allowedKeys.includes('object_full')) {
        setGlobal(row.objectType, 'object_full')
        // object_full implies create, so clear explicit create toggle
        setGlobalCreate(row.objectType, false)
        // object_full implies all extras, so clear explicit extras
        setGlobalExtras(row.objectType, [])
      } else if (allowedKeys.includes('object_admins')) {
        // Dashboard special case: only select object_admins (not object_verwaltende)
        setGlobal(row.objectType, 'none')
        setGlobalCreate(row.objectType, false)
        setGlobalExtras(row.objectType, ['object_admins'])
      } else {
        // No object_full available - select highest level + all extras
        // Find highest available level
        let highestLevel = 'none'
        for (const level of LEVEL_KEYS_BY_PRIORITY) {
          if (allowedKeys.includes(level)) {
            highestLevel = level
            break
          }
        }

        setGlobal(row.objectType, highestLevel)

        // Set create if available
        setGlobalCreate(row.objectType, allowedKeys.includes('object_create'))

        // Collect all extra permissions (non-level, non-create keys)
        const extras = allowedKeys.filter((k) => !LEVEL_KEY_SET.has(k))
        setGlobalExtras(row.objectType, extras)
      }

      // Object-scoped permissions: keep on 'none' (don't change)
    }
  }

  return {
    deselectAll,
    selectAll,
  }
}
