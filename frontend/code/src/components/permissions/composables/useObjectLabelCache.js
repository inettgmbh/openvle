import { shallowRef } from 'vue'

import { getI18nT } from '@/i18n'
import { useLookupStore } from '@/stores/lookup'
import {
  resolveObjectTypeToFrontendURLs,
  resolveObjectTypeToGerman,
} from '@/utils/dataUtils'
import { getObjectModelByBackendType } from '@/utils/objectModelPermissions'

export function useObjectLabelCache(objectLabelResolver) {
  const lookupStore = useLookupStore()
  // Plain (non-reactive) cache. Reactive notification happens through
  // `labelVersion` — only readers that opt in via `getObjectLabelSync` get
  // re-rendered when a label resolves. Computeds that should not be
  // invalidated by async label resolution use `getObjectLabelSnapshot`.
  const objectLabelCache = {}
  const objectLabelInFlight = new Map()
  const labelVersion = shallowRef(0)

  function getObjectTypeLabel(objectType) {
    const model = getObjectModelByBackendType(String(objectType ?? ''))
    if (model?.objectTypeKey) {
      const t = getI18nT()
      const i18nKey = `objectTypes.${model.objectTypeKey}.plural`
      const translated = t(i18nKey)
      if (translated !== i18nKey) return translated
      if (model.label) return model.label
    } else if (model?.key) {
      if (model.label) return model.label
    }

    const key = String(objectType ?? '')
    const lower = key.toLowerCase()

    return resolveObjectTypeToGerman(lower, { plural: true }) ?? key
  }

  function getObjectTypeKeyspace(objectType) {
    const key = String(objectType ?? '')

    const model = getObjectModelByBackendType(key)

    if (model?.keyspace == null) return null
    if (model?.keyspace) return model.keyspace

    const lower = key.toLowerCase()
    const map = resolveObjectTypeToFrontendURLs

    const normalize = (value) => {
      if (typeof value !== 'string') return value

      return value
        .replace(/-/g, '_')
        .replace(/^connections$/, 'connectionProfiles')
    }

    if (map && typeof map === 'object') {
      if (map[key]) return normalize(map[key])
      if (map[lower]) return normalize(map[lower])

      if (lower.endsWith('s') && map[lower.slice(0, -1)])
        return normalize(map[lower.slice(0, -1)])
      if (!lower.endsWith('s') && map[lower + 's'])
        return normalize(map[lower + 's'])
    }

    return normalize(key)
  }

  function readLabel(objectType, objectId) {
    const ot = String(objectType)
    const id = String(objectId)

    const cached = objectLabelCache[ot]?.[id]
    if (cached) return cached

    return `${getObjectTypeLabel(ot)} – ${id.slice(0, 8)}…`
  }

  // Reactive: reads `labelVersion` so callers (templates) re-render when a
  // label resolves async.
  function getObjectLabelSync(objectType, objectId) {
    // Touch the version ref to register a reactive dependency.
    labelVersion.value
    return readLabel(objectType, objectId)
  }

  // Non-reactive snapshot: same lookup without registering a dependency on
  // `labelVersion`. Use inside computeds whose result should not be
  // invalidated each time a label resolves.
  function getObjectLabelSnapshot(objectType, objectId) {
    return readLabel(objectType, objectId)
  }

  async function prefetchObjectLabel(objectType, objectId) {
    const ot = String(objectType)
    const id = String(objectId)
    const key = `${ot}:${id}`

    if (!objectLabelCache[ot]) objectLabelCache[ot] = {}
    if (objectLabelCache[ot][id]) return

    if (objectLabelInFlight.has(key)) return objectLabelInFlight.get(key)

    objectLabelCache[ot][id] = `${getObjectTypeLabel(ot)} – ${id.slice(0, 8)}…`

    const promise = (async () => {
      if (objectLabelResolver) {
        const label = await objectLabelResolver(ot, id)
        if (label) {
          objectLabelCache[ot][id] = label
          return
        }
      }

      const keyspace = getObjectTypeKeyspace(ot)
      if (!keyspace) return

      const label = await lookupStore.resolve(keyspace, id)
      if (label) objectLabelCache[ot][id] = label
    })()

    objectLabelInFlight.set(key, promise)
    try {
      await promise
    } finally {
      objectLabelInFlight.delete(key)
      labelVersion.value++
    }
  }

  return {
    getObjectLabelSync,
    getObjectLabelSnapshot,
    prefetchObjectLabel,
    getObjectTypeLabel,
  }
}
