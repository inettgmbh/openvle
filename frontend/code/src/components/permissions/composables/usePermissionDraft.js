import { computed, reactive, ref, watch } from 'vue'

import { buildSnapshot, calculateChanges } from '@/utils/objectModelPermissions'

export function usePermissionDraft(permissions, entityId, entityType) {
  const isEditing = ref(false)
  const original = ref(buildSnapshot(permissions, entityId, entityType))
  const draft = reactive(buildSnapshot(permissions, entityId, entityType))

  // Watch permissions and update snapshots
  watch(
    () => permissions.value,
    (next) => {
      const snap = buildSnapshot(next, entityId, entityType)
      original.value = snap
      if (!isEditing.value) replaceDraft(snap)
    },
    { deep: true },
  )

  function replaceDraft(snap) {
    for (const k of Object.keys(draft.global)) delete draft.global[k]
    for (const k of Object.keys(draft.globalCreate))
      delete draft.globalCreate[k]
    for (const k of Object.keys(draft.objects)) delete draft.objects[k]
    for (const k of Object.keys(draft.extrasGlobal ?? {}))
      delete draft.extrasGlobal[k]
    for (const k of Object.keys(draft.extrasObjects ?? {}))
      delete draft.extrasObjects[k]

    Object.assign(draft.global, snap.global)
    Object.assign(draft.globalCreate, snap.globalCreate)

    for (const ot of Object.keys(snap.objects))
      draft.objects[ot] = { ...snap.objects[ot] }

    // Deep copy extrasGlobal (object type -> array of keys)
    draft.extrasGlobal = {}
    for (const ot of Object.keys(snap.extrasGlobal ?? {})) {
      draft.extrasGlobal[ot] = [...(snap.extrasGlobal[ot] ?? [])]
    }

    // Deep copy extrasObjects (object type -> object id -> array of keys)
    draft.extrasObjects = {}
    for (const ot of Object.keys(snap.extrasObjects ?? {})) {
      draft.extrasObjects[ot] = {}
      for (const id of Object.keys(snap.extrasObjects[ot] ?? {})) {
        draft.extrasObjects[ot][id] = [...(snap.extrasObjects[ot][id] ?? [])]
      }
    }
  }

  const hasChanges = computed(() => {
    const a = JSON.stringify(original.value)
    const b = JSON.stringify({
      global: draft.global,
      globalCreate: draft.globalCreate,
      objects: draft.objects,
      extrasGlobal: draft.extrasGlobal ?? {},
      extrasObjects: draft.extrasObjects ?? {},
    })
    return a !== b
  })

  function startEdit() {
    isEditing.value = true
    replaceDraft(original.value)
  }

  function cancelEdit() {
    isEditing.value = false
    replaceDraft(original.value)
  }

  // Synchronous rebuild from current permissions (bypasses async watcher)
  function rebuild() {
    const snap = buildSnapshot(permissions, entityId, entityType)
    original.value = snap
    if (!isEditing.value) replaceDraft(snap)
  }

  function setGlobal(objectType, level) {
    if (!isEditing.value) return
    if (level === 'none') {
      delete draft.global[objectType]
      return
    }
    draft.global[objectType] = level
  }

  function setGlobalCreate(objectType, enabled) {
    if (!isEditing.value) return
    if (!enabled) {
      delete draft.globalCreate[objectType]
      return
    }
    draft.globalCreate[objectType] = true
  }

  function setGlobalExtras(objectType, extras) {
    if (!isEditing.value) return
    if (!draft.extrasGlobal) draft.extrasGlobal = {}
    const list = Array.isArray(extras) ? extras : []
    if (list.length === 0) {
      delete draft.extrasGlobal[objectType]
      return
    }
    draft.extrasGlobal[objectType] = [...new Set(list.map((k) => String(k)))]
  }

  function setObject(objectType, objectId, level) {
    if (!isEditing.value) return
    if (level === 'object_create') return

    if (!draft.objects[objectType]) draft.objects[objectType] = {}

    if (level === 'none') {
      draft.objects[objectType][objectId] = 'none'
      return
    }

    draft.objects[objectType][objectId] = level
  }

  function setObjectExtras(objectType, objectId, extras) {
    if (!isEditing.value) return
    if (!draft.extrasObjects) draft.extrasObjects = {}
    if (!draft.extrasObjects[objectType]) draft.extrasObjects[objectType] = {}

    const list = Array.isArray(extras) ? extras : []
    if (list.length === 0) {
      delete draft.extrasObjects[objectType][objectId]
      if (Object.keys(draft.extrasObjects[objectType]).length === 0)
        delete draft.extrasObjects[objectType]
      return
    }

    draft.extrasObjects[objectType][objectId] = [
      ...new Set(list.map((k) => String(k))),
    ]
  }

  function toUpsertsAndDeletes() {
    const after = {
      global: draft.global,
      globalCreate: draft.globalCreate,
      objects: draft.objects,
      extrasGlobal: draft.extrasGlobal ?? {},
      extrasObjects: draft.extrasObjects ?? {},
    }

    return calculateChanges(original.value, after, entityId, entityType)
  }

  return {
    isEditing,
    draft,
    hasChanges,
    startEdit,
    cancelEdit,
    rebuild,
    setGlobal,
    setGlobalCreate,
    setGlobalExtras,
    setObject,
    setObjectExtras,
    toUpsertsAndDeletes,
  }
}
