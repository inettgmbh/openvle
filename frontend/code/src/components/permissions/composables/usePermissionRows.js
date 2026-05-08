import { computed, reactive } from 'vue'

import { useMainStore } from '@/stores/main'
import {
  getAllObjectModelsSorted,
  getObjectModelByBackendType,
} from '@/utils/objectModelPermissions'
import { normalizePermission } from '@/utils/objectModelPermissions'

export function usePermissionRows(
  permissions,
  draft,
  entityId,
  entityType,
  isEditing,
  objectModelQuery,
  onlyWithPermissions,
  prefetchObjectLabel,
  // Non-reactive label lookup. Using the reactive `getObjectLabelSync` here
  // would cause the entire `rows` computed to re-run on every async label
  // resolution, cascading into a full matrix re-render per resolved object.
  getObjectLabelSnapshot,
  getObjectTypeLabel,
) {
  const mainStore = useMainStore()
  const expanded = reactive({})

  const objectModels = computed(() => getAllObjectModelsSorted())

  function getPreferredBackendObjectType(model) {
    const preferred = model?.backendObjectTypes?.[0]
    return preferred ?? model?.key ?? model?.label ?? ''
  }

  function supportsObjectScope(objectType) {
    const model = getObjectModelByBackendType(objectType)
    if (!model) return true
    return !!model?.scopes?.object
  }

  function getAllowedKeys(objectType, scope) {
    const model = getObjectModelByBackendType(objectType)
    if (!model) return null

    if (!model?.scopes?.[scope]) return []

    const keys = model?.permissionKeys?.[scope]
    if (!Array.isArray(keys)) return []

    return keys
  }

  function sortObjectTypesByLabel(a, b) {
    return getObjectTypeLabel(a).localeCompare(getObjectTypeLabel(b), 'de')
  }

  function matchesObjectTypeQuery(objectType, query) {
    const q = String(query ?? '')
      .trim()
      .toLowerCase()
    if (!q) return true

    const label = getObjectTypeLabel(objectType).toLowerCase()
    const backend = String(objectType ?? '').toLowerCase()

    return label.includes(q) || backend.includes(q)
  }

  function hasAnyPermission(objectType) {
    const globalLevel = draft.global[objectType]
    if (globalLevel && globalLevel !== 'none') return true

    if (draft.globalCreate[objectType]) return true

    const globalExtras = draft.extrasGlobal?.[objectType]
    if (globalExtras?.length > 0) return true

    const objMap = draft.objects[objectType]
    if (objMap) {
      for (const id of Object.keys(objMap)) {
        if (objMap[id] && objMap[id] !== 'none') return true
      }
    }

    const extrasObjMap = draft.extrasObjects?.[objectType]
    if (extrasObjMap) {
      for (const id of Object.keys(extrasObjMap)) {
        if (extrasObjMap[id]?.length > 0) return true
      }
    }

    return false
  }

  function isFeatureEnabled(flag) {
    if (!flag) return true
    const parts = flag.split('.')
    let value = mainStore.settings
    for (const part of parts) {
      value = value?.[part]
    }
    return !!value
  }

  // Index permissions by objectType once, instead of re-iterating the full
  // list for every row. Filters by entity up-front so the row loop only sees
  // relevant entries.
  const objectIdsByType = computed(() => {
    const map = new Map()
    for (const raw of permissions.value) {
      const p = normalizePermission(raw)
      if (p.entityId !== entityId) continue
      if (p.entityType !== entityType) continue
      if (!p.objectType) continue
      if (!map.has(p.objectType)) map.set(p.objectType, new Set())
      if (p.objectId) map.get(p.objectType).add(p.objectId)
    }
    return map
  })

  const rows = computed(() => {
    const objectTypes = new Set()

    for (const model of objectModels.value) {
      const preferredType = getPreferredBackendObjectType(model)
      if (!preferredType) continue
      // Skip models gated by an inactive feature flag;
      // they still appear if existing permissions reference them (added below)
      if (model.featureFlag && !isFeatureEnabled(model.featureFlag)) continue
      objectTypes.add(preferredType)
    }

    for (const ot of objectIdsByType.value.keys()) objectTypes.add(ot)

    for (const ot of Object.keys(draft.global)) objectTypes.add(ot)
    for (const ot of Object.keys(draft.globalCreate)) objectTypes.add(ot)
    for (const ot of Object.keys(draft.objects)) objectTypes.add(ot)
    for (const ot of Object.keys(draft.extrasGlobal ?? {})) objectTypes.add(ot)
    for (const ot of Object.keys(draft.extrasObjects ?? {})) objectTypes.add(ot)

    const sorted = [...objectTypes].sort(sortObjectTypesByLabel)

    let filtered = objectModelQuery.value.trim()
      ? sorted.filter((ot) =>
          matchesObjectTypeQuery(ot, objectModelQuery.value),
        )
      : sorted

    if (onlyWithPermissions.value) {
      filtered = filtered.filter((ot) => hasAnyPermission(ot))
    }

    return filtered.map((objectType) => {
      const objMap = draft.objects[objectType] ?? {}
      const extrasObjMap = draft.extrasObjects?.[objectType] ?? {}

      const objectScopeAllowed = supportsObjectScope(objectType)

      const originalObjectIds = objectIdsByType.value.get(objectType) ?? null

      // Combine draft and original object IDs
      const allObjectIds = new Set([
        ...Object.keys(objMap),
        ...Object.keys(extrasObjMap),
        ...(originalObjectIds ?? []),
      ])

      if (objectScopeAllowed) {
        for (const objectId of allObjectIds) {
          prefetchObjectLabel(objectType, objectId)
        }
      }

      const ids = objectScopeAllowed
        ? [...allObjectIds].filter((id) => {
            if (isEditing.value) {
              // In editing mode, show all objects that exist in draft OR original
              return true
            }
            const level = objMap[id] ?? 'none'
            const extras = extrasObjMap[id] ?? []
            return level !== 'none' || extras.length > 0
          })
        : []

      const objectEntries = ids
        .sort((a, b) =>
          getObjectLabelSnapshot(objectType, a).localeCompare(
            getObjectLabelSnapshot(objectType, b),
            'de',
          ),
        )
        .map((objectId) => ({ objectId }))

      if (expanded[objectType] === undefined) expanded[objectType] = false

      const allowedGlobalKeys = getAllowedKeys(objectType, 'global')
      const allowedObjectKeys = getAllowedKeys(objectType, 'object')

      // Compact signature of all draft state that affects this row's render.
      // Used by v-memo on PermissionMatrixRow to skip re-rendering rows whose
      // state is unchanged. Reference equality of `draft.objects[objectType]`
      // is unreliable (mutations happen in place), so we serialize it.
      const memoParts = [
        objectType,
        expanded[objectType] ? '1' : '0',
        draft.global[objectType] ?? '',
        draft.globalCreate[objectType] ? '1' : '0',
        (draft.extrasGlobal?.[objectType] ?? []).join(','),
      ]
      if (objectScopeAllowed) {
        const objs = draft.objects[objectType]
        if (objs) {
          const keys = Object.keys(objs).sort()
          memoParts.push(keys.map((k) => `${k}=${objs[k]}`).join(';'))
        } else {
          memoParts.push('')
        }
        const extras = draft.extrasObjects?.[objectType]
        if (extras) {
          const keys = Object.keys(extras).sort()
          memoParts.push(
            keys.map((k) => `${k}=${(extras[k] ?? []).join(',')}`).join(';'),
          )
        } else {
          memoParts.push('')
        }
        memoParts.push(String(objectEntries.length))
      }
      const memoKey = memoParts.join('|')

      return {
        objectType,
        objectEntries,
        objectScopeAllowed,
        allowedGlobalKeys,
        allowedObjectKeys,
        expanded: expanded[objectType],
        memoKey,
      }
    })
  })

  const allExpanded = computed(
    () =>
      rows.value.length > 0 && rows.value.every((r) => expanded[r.objectType]),
  )

  function toggleExpanded(objectType) {
    expanded[objectType] = !expanded[objectType]
  }

  function toggleAll() {
    const next = !allExpanded.value
    for (const r of rows.value) expanded[r.objectType] = next
  }

  return {
    rows,
    expanded,
    allExpanded,
    toggleExpanded,
    toggleAll,
    getObjectTypeLabel,
  }
}
