import {
  mdiAccountHardHat,
  mdiAccountMultipleCheckOutline,
  mdiAccountSearch,
  mdiEmailFastOutline,
  mdiEyeOutline,
  mdiFastForward,
  mdiFlash,
  mdiKey,
  mdiPauseCircleOutline,
  mdiPencilOutline,
  mdiPlayCircleOutline,
  mdiPlusBoxOutline,
  mdiPower,
  mdiRestart,
  mdiSendCircleOutline,
  mdiShieldAccountVariant,
  mdiShieldCrownOutline,
  mdiSnowflake,
  mdiStopCircleOutline,
  mdiTrashCanOutline,
  mdiVectorArrangeAbove,
  mdiWrenchCog,
} from '@mdi/js'

import objectModelConfig from '@/config/objectModels.permissions.json'
import i18n, { getI18nT } from '@/i18n'

/**
 * @typedef {Object} ObjectModelPermissionConfig
 * @property {string} key
 * @property {string} label
 * @property {string[]} backendObjectTypes
 * @property {string} keyspace
 * @property {{ global: boolean, object: boolean }} scopes
 * @property {{ global?: string[], object?: string[] }} permissionKeys
 */

const CONFIG_VERSION = 1

/**
 * @typedef {Object} ObjectPermission
 *
 * @property {string} key
 *   Unique permission key.
 * @property {string} label
 *   Human-readable permission label.
 * @property {string} description
 *   Detailed description of the permission.
 * @property {string} [short]
 *   Optional short label.
 * @property {string[]} scope
 *   Scopes in which the permission is applicable.
 * @property {string} [model]
 *   Optional model the permission applies to.
 * @property {string} [icon]
 *   Icon identifier for UI representation.
 */

// Cache: definitions and lookup maps keyed by current i18n locale.
// Building the array involves ~30 t() calls, so we memoize per-locale and
// invalidate transparently when the locale changes.
//
// Some keys (e.g. `object_actions_start`, `object_actions_stop`) exist with
// different `model` fields — currently shared between VM and Event. The
// by-key map prefers entries without a `model` (model-agnostic permissions);
// the `byKeyAndModel` map disambiguates when callers pass a model context.
let _definitionsLocale = null
let _definitionsCache = null
let _definitionsByKey = null
let _definitionsByKeyAndModel = null

function buildDefinitions() {
  const t = getI18nT()
  return [
    {
      key: 'object_create',
      label: t('permissions.objectCreate.label'),
      description: t('permissions.objectCreate.description'),
      scope: ['global'],
      icon: mdiPlusBoxOutline,
    },
    {
      key: 'object_read',
      label: t('permissions.objectRead.label'),
      description: t('permissions.objectRead.description'),
      scope: ['global', 'object'],
      icon: mdiEyeOutline,
    },
    {
      key: 'object_reset',
      label: t('permissions.objectReset.label'),
      short: t('permissions.objectReset.short'),
      description: t('permissions.objectReset.description'),
      model: 'VirtualMachine',
      scope: ['object'],
      icon: mdiWrenchCog,
    },
    {
      key: 'object_update',
      label: t('permissions.objectUpdate.label'),
      short: t('permissions.objectUpdate.short'),
      description: t('permissions.objectUpdate.description'),
      scope: ['global', 'object'],
      icon: mdiPencilOutline,
    },
    {
      key: 'object_delete',
      label: t('permissions.objectDelete.label'),
      short: t('permissions.objectDelete.short'),
      description: t('permissions.objectDelete.description'),
      scope: ['global', 'object'],
      icon: mdiTrashCanOutline,
    },
    {
      key: 'object_full',
      label: t('permissions.objectFull.label'),
      description: t('permissions.objectFull.description'),
      scope: ['global', 'object'],
      icon: mdiShieldCrownOutline,
    },

    // Users
    {
      key: 'object_set_password',
      label: t('permissions.objectSetPassword.label'),
      description: t('permissions.objectSetPassword.description'),
      model: 'User',
      scope: ['global'],
      icon: mdiKey,
    },
    {
      key: 'object_search',
      label: t('permissions.objectSearch.label'),
      description: t('permissions.objectSearch.description'),
      model: 'User',
      scope: ['global'],
      icon: mdiAccountSearch,
    },

    // Mails
    {
      key: 'object_send',
      label: t('permissions.objectSend.label'),
      description: t('permissions.objectSend.description'),
      model: 'Mails',
      scope: ['global'],
      icon: mdiSendCircleOutline,
    },
    {
      key: 'object_send_bulk',
      label: t('permissions.objectSendBulk.label'),
      description: t('permissions.objectSendBulk.description'),
      model: 'Mails',
      scope: ['global'],
      icon: mdiEmailFastOutline,
    },

    // Dashboards
    {
      key: 'object_admins',
      label: t('permissions.objectAdmins.label'),
      short: t('permissions.objectAdmins.short'),
      description: t('permissions.objectAdmins.description'),
      model: 'Dashboard',
      scope: ['global'],
      icon: mdiShieldAccountVariant,
    },
    {
      key: 'object_verwaltende',
      label: t('permissions.objectVerwaltende.label'),
      description: t('permissions.objectVerwaltende.description'),
      model: 'Dashboard',
      scope: ['global'],
      icon: mdiAccountHardHat,
    },

    // Policy
    {
      key: 'object_users_read',
      label: t('permissions.objectUsersRead.label'),
      description: t('permissions.objectUsersRead.description'),
      model: 'Policy',
      scope: ['global'],
      icon: mdiAccountMultipleCheckOutline,
    },

    // Events
    {
      key: 'object_templates_update',
      label: t('permissions.objectTemplatesUpdate.label'),
      description: t('permissions.objectTemplatesUpdate.description'),
      model: 'Events',
      scope: ['global'],
      icon: mdiVectorArrangeAbove,
    },

    // VMs
    {
      key: 'object_actions_start',
      label: t('permissions.vm.actionsStart.label'),
      short: t('permissions.vm.actionsStart.short'),
      description: t('permissions.vm.actionsStart.description'),
      model: 'VirtualMachine',
      scope: ['global', 'object'],
      icon: mdiPlayCircleOutline,
    },
    {
      key: 'object_actions_stop',
      label: t('permissions.vm.actionsStop.label'),
      short: t('permissions.vm.actionsStop.short'),
      description: t('permissions.vm.actionsStop.description'),
      model: 'VirtualMachine',
      scope: ['global', 'object'],
      icon: mdiStopCircleOutline,
    },
    {
      key: 'object_actions_shutdown',
      label: t('permissions.vm.actionsShutdown.label'),
      short: t('permissions.vm.actionsShutdown.short'),
      description: t('permissions.vm.actionsShutdown.description'),
      model: 'VirtualMachine',
      scope: ['global', 'object'],
      icon: mdiPower,
    },
    {
      key: 'object_actions_pause',
      label: t('permissions.vm.actionsPause.label'),
      short: t('permissions.vm.actionsPause.short'),
      description: t('permissions.vm.actionsPause.description'),
      model: 'VirtualMachine',
      scope: ['global', 'object'],
      icon: mdiPauseCircleOutline,
    },
    {
      key: 'object_actions_hibernate',
      label: t('permissions.vm.actionsHibernate.label'),
      short: t('permissions.vm.actionsHibernate.short'),
      description: t('permissions.vm.actionsHibernate.description'),
      model: 'VirtualMachine',
      scope: ['global', 'object'],
      icon: mdiSnowflake,
    },
    {
      key: 'object_actions_resume',
      label: t('permissions.vm.actionsResume.label'),
      short: t('permissions.vm.actionsResume.short'),
      description: t('permissions.vm.actionsResume.description'),
      model: 'VirtualMachine',
      scope: ['global', 'object'],
      icon: mdiFastForward,
    },
    {
      key: 'object_actions_reboot',
      label: t('permissions.vm.actionsReboot.label'),
      short: t('permissions.vm.actionsReboot.short'),
      description: t('permissions.vm.actionsReboot.description'),
      model: 'VirtualMachine',
      scope: ['global', 'object'],
      icon: mdiRestart,
    },
    {
      key: 'object_actions_reset',
      label: t('permissions.vm.actionsReset.label'),
      short: t('permissions.vm.actionsReset.short'),
      description: t('permissions.vm.actionsReset.description'),
      model: 'VirtualMachine',
      scope: ['global', 'object'],
      icon: mdiFlash,
    },

    // Events
    {
      key: 'object_actions_start',
      label: t('permissions.event.actionsStart.label'),
      short: t('permissions.event.actionsStart.short'),
      description: t('permissions.event.actionsStart.description'),
      model: 'Event',
      scope: ['global', 'object'],
      icon: mdiPlayCircleOutline,
    },
    {
      key: 'object_actions_stop',
      label: t('permissions.event.actionsStop.label'),
      short: t('permissions.event.actionsStop.short'),
      description: t('permissions.event.actionsStop.description'),
      model: 'Event',
      scope: ['global', 'object'],
      icon: mdiStopCircleOutline,
    },
  ]
}

function rebuildDefinitionCaches() {
  _definitionsCache = buildDefinitions()
  _definitionsByKey = new Map()
  _definitionsByKeyAndModel = new Map()

  for (const def of _definitionsCache) {
    // For the by-key map, prefer model-agnostic entries (no `model` field),
    // otherwise keep the first occurrence. Without this, lookups for keys
    // shared between models (e.g. VM + Event share `object_actions_stop`)
    // would arbitrarily resolve to whichever entry comes last in the list.
    const existing = _definitionsByKey.get(def.key)
    if (!existing || (existing.model && !def.model)) {
      _definitionsByKey.set(def.key, def)
    }
    if (def.model) {
      _definitionsByKeyAndModel.set(`${def.key}|${def.model}`, def)
    }
  }

  _definitionsLocale = i18n.global.locale.value ?? null
}

/**
 * Returns the list of all object permission definitions with i18n-resolved labels.
 *
 * The result is memoized per locale; subsequent calls with the same locale
 * return the same array reference, avoiding repeated t() lookups in hot paths.
 *
 * @returns {ObjectPermission[]}
 */
export function getObjectPermissionDefinitions() {
  if (_definitionsCache && _definitionsLocale === i18n.global.locale.value) {
    return _definitionsCache
  }
  rebuildDefinitionCaches()
  return _definitionsCache
}

function getDefinitionsByKey() {
  if (_definitionsByKey && _definitionsLocale === i18n.global.locale.value) {
    return _definitionsByKey
  }
  rebuildDefinitionCaches()
  return _definitionsByKey
}

function getDefinitionsByKeyAndModel() {
  if (
    _definitionsByKeyAndModel &&
    _definitionsLocale === i18n.global.locale.value
  ) {
    return _definitionsByKeyAndModel
  }
  rebuildDefinitionCaches()
  return _definitionsByKeyAndModel
}

/**
 * Returns a single permission definition by key, optionally scoped to a model.
 *
 * When a `model` is provided, the model-specific entry is preferred (so
 * `(object_actions_stop, 'VirtualMachine')` returns the VM entry, not the
 * Event one). Without a model, the first model-agnostic entry is returned,
 * or — if all entries are model-scoped — the first occurrence.
 *
 * @param {string} key
 * @param {string|null} [model] - Optional model identifier (e.g. 'VirtualMachine', 'Event').
 * @returns {ObjectPermission | null}
 */
export function getObjectPermissionByKey(key, model = null) {
  if (!key) return null
  if (model) {
    const direct = getDefinitionsByKeyAndModel().get(`${key}|${model}`)
    if (direct) return direct
  }
  return getDefinitionsByKey().get(key) ?? null
}

/**
 * Permission levels for global (object-type wide) permissions.
 *
 * Order matters: later entries imply a higher permission level.
 *
 * @type {Array<'none'|'object_create'|'object_read'|'object_update'|'object_delete'|'object_full'>}
 */
export const GLOBAL_LEVELS = [
  'none',
  'object_create',
  'object_read',
  'object_update',
  'object_delete',
  'object_full',
]

/**
 * Permission levels for object-scoped permissions (per object ID).
 *
 * Order matters: later entries imply a higher permission level.
 *
 * @type {Array<'none'|'object_read'|'object_update'|'object_delete'|'object_full'>}
 */
export const OBJECT_LEVELS = [
  'none',
  'object_read',
  'object_update',
  'object_delete',
  'object_full',
]

/**
 * Index lookup for global permission levels.
 *
 * @type {Map<string, number>}
 */
export const GLOBAL_LEVEL_INDEX = new Map(GLOBAL_LEVELS.map((k, i) => [k, i]))

/**
 * Index lookup for object permission levels.
 *
 * @type {Map<string, number>}
 */
export const OBJECT_LEVEL_INDEX = new Map(OBJECT_LEVELS.map((k, i) => [k, i]))

/**
 * Keys that are considered "level" keys (as opposed to extra permissions).
 *
 * @type {Set<string>}
 */
export const LEVEL_KEYS = new Set([
  'object_read',
  'object_update',
  'object_delete',
  'object_full',
])

/**
 * Level keys that are mutually exclusive (only one should exist per scope).
 *
 * @type {Set<string>}
 */
export const EXCLUSIVE_LEVEL_KEYS = new Set([
  'object_read',
  'object_update',
  'object_delete',
  'object_full',
])

// The object model config is static at runtime — compute once, reuse forever.
let _modelConfigCache = null
let _modelByKeyCache = null
let _modelByBackendTypeCache = null
let _modelByKeyspaceCache = null

function buildModelConfig() {
  if (objectModelConfig.version !== CONFIG_VERSION) {
    console.warn(
      `[objectModelPermissions] Unsupported config version ${objectModelConfig.version}`,
    )
  }

  const list = objectModelConfig.objectModels.filter((m) => !m.disabled)
  const byKey = new Map()
  const byBackendType = new Map()
  const byKeyspace = new Map()

  for (const model of list) {
    if (model.key) byKey.set(model.key, model)
    if (model.keyspace) byKeyspace.set(model.keyspace.toLowerCase(), model)
    for (const t of model.backendObjectTypes ?? []) {
      byBackendType.set(String(t).toLowerCase(), model)
    }
  }

  _modelConfigCache = list
  _modelByKeyCache = byKey
  _modelByBackendTypeCache = byBackendType
  _modelByKeyspaceCache = byKeyspace
}

/**
 * Returns the configured object model definitions (memoized).
 *
 * @returns {ObjectModelPermissionConfig[]}
 */
export function getObjectModelConfig() {
  if (!_modelConfigCache) buildModelConfig()
  return _modelConfigCache
}

/**
 * Returns all object model keys (stable, technical identifiers)
 */
export function getAllObjectModelKeys() {
  return getObjectModelConfig().map((m) => m.key)
}

/**
 * Find object model config by technical key
 *
 * @param {string} key
 * @returns {ObjectModelPermissionConfig | null}
 */
export function getObjectModelByKey(key) {
  if (!_modelByKeyCache) buildModelConfig()
  return _modelByKeyCache.get(key) ?? null
}

/**
 * Find object model config by backend object_type
 * (robust against casing & naming differences)
 *
 * @param {string} backendObjectType
 * @returns {ObjectModelPermissionConfig | null}
 */
export function getObjectModelByBackendType(backendObjectType) {
  if (!backendObjectType) return null
  if (!_modelByBackendTypeCache) buildModelConfig()
  return _modelByBackendTypeCache.get(backendObjectType.toLowerCase()) ?? null
}

/**
 * Returns label for object model
 *
 * @param {string} key
 */
export function getObjectModelLabel(key) {
  return getObjectModelByKey(key)?.label ?? key
}

/**
 * Returns keyspace for lookup store resolution
 *
 * @param {string} key
 */
export function getObjectModelKeyspace(key) {
  return getObjectModelByKey(key)?.keyspace ?? null
}

/**
 * Find object model config by keyspace (URL path segment)
 *
 * @param {string} keyspace - The keyspace/URL path (e.g., "users", "vms", "guacamoles")
 * @returns {ObjectModelPermissionConfig | null}
 */
export function getObjectModelByKeyspace(keyspace) {
  if (!keyspace) return null
  if (!_modelByKeyspaceCache) buildModelConfig()
  return _modelByKeyspaceCache.get(keyspace.toLowerCase()) ?? null
}

/**
 * Returns label for object model by keyspace (URL path segment)
 *
 * @param {string} keyspace - The keyspace/URL path (e.g., "users", "vms")
 * @returns {string} The label or the keyspace if not found
 */
export function getObjectModelLabelByKeyspace(keyspace) {
  return getObjectModelByKeyspace(keyspace)?.label ?? keyspace
}

/**
 * Returns whether a scope is supported by the object model
 *
 * @param {string} key
 * @param {'global' | 'object'} scope
 */
export function supportsScope(key, scope) {
  const model = getObjectModelByKey(key)
  return !!model?.scopes?.[scope]
}

/**
 * Returns allowed permission keys for an object model + scope
 *
 * @param {string} key
 * @param {'global' | 'object'} scope
 * @returns {string[]}
 */
export function getPermissionKeysForScope(key, scope) {
  const model = getObjectModelByKey(key)
  if (!model) return []

  if (!model.scopes?.[scope]) return []

  return model.permissionKeys?.[scope] ?? []
}

/**
 * Returns whether a specific permission key is allowed
 *
 * @param {string} key
 * @param {'global' | 'object'} scope
 * @param {string} permissionKey
 */
export function isPermissionAllowed(key, scope, permissionKey) {
  return getPermissionKeysForScope(key, scope).includes(permissionKey)
}

/**
 * Returns all object models sorted by label (de locale)
 */
export function getAllObjectModelsSorted() {
  return [...getObjectModelConfig()].sort((a, b) =>
    a.label.localeCompare(b.label, 'de'),
  )
}

/**
 * Returns whether the permission key is a CRUD-like permission
 *
 * @param {string} permissionKey
 */
export function isCrudPermission(permissionKey) {
  return [
    'object_create',
    'object_read',
    'object_update',
    'object_delete',
    'object_full',
  ].includes(permissionKey)
}

/**
 * Returns the available permission options for a given object model.
 *
 * This is a convenience wrapper around {@link getObjectPermissionsOptionsByScope}
 * that always resolves permissions in the `'object'` scope.
 *
 * @param {string} model - The object model identifier (e.g. 'templates', 'virtual_machines').
 * @returns {Array<Object>} A list of permission option objects for the given model.
 */
export function getObjectPermissionsOptions(model) {
  return getObjectPermissionsOptionsByScope('object', model)
}

/**
 * Returns permission definitions filtered by scope and object model.
 *
 * This function filters the global `OBJECT_PERMISSIONS` list by:
 * - `scope`: the permission scope (e.g. `'object'`, `'global'`)
 * - `model`: the target object model (supports single values or arrays)
 *
 * If `scope` or `model` is not provided, the corresponding filter is ignored.
 *
 * @param {string|null|undefined} scope - The permission scope to filter by.
 * @param {string|null|undefined} model - The object model identifier to filter by.
 * @returns {Array<Object>} A list of permission definition objects matching the given filters.
 */
export function getObjectPermissionsByScope(scope, model) {
  function matchesModel(item, model) {
    if (!model) {
      return true
    }

    if (!item.model) {
      return true
    }

    if (Array.isArray(item.model)) {
      return item.model.includes(model)
    }

    return item.model === model
  }

  function matchesScope(item, scope) {
    if (!scope) {
      return true
    }

    const scopes = item.scope ?? []
    return scopes.includes(scope)
  }

  return getObjectPermissionDefinitions().filter((item) => {
    return matchesScope(item, scope) && matchesModel(item, model)
  })
}

/**
 * Returns selectable permission options filtered by scope and object model.
 *
 * This function resolves permission definitions via {@link getObjectPermissionsByScope}
 * and maps them into a simplified option format suitable for UI components
 * such as selects or multi-selects.
 *
 * Each returned option contains:
 * - `value`: the permission key
 * - `label`: the human-readable permission name
 * - `description`: an optional description of the permission
 *
 * @param {string|null|undefined} scope - The permission scope to filter by (e.g. `'object'`, `'global'`).
 * @param {string|null|undefined} model - The object model identifier to filter by.
 * @returns {Array<{ value: string, label: string, description?: string }>} A list of permission option objects.
 */
export function getObjectPermissionsOptionsByScope(scope, model) {
  return getObjectPermissionsByScope(scope, model).map((p) => ({
    label: p.label,
    value: p.key,
    description: p.description,
  }))
}

/**
 * Resolves a human-readable label (or custom value) for a permission key.
 *
 * The function attempts to resolve the permission in the following order:
 * 1. Globally (without scope or model)
 * 2. Scoped to the given `scope` and/or `model`
 *
 * If no matching permission definition is found, the original permission key
 * is returned as a fallback.
 *
 * A custom `selector` function can be provided to extract a different property
 * from the matched permission definition (e.g. `description`).
 *
 * @param {Object} options - Resolution options.
 * @param {string} options.permission - The permission key to resolve.
 * @param {string|null|undefined} [options.scope] - Optional permission scope.
 * @param {string|null|undefined} [options.model] - Optional object model identifier.
 * @param {(permission: Object) => any} [options.selector] - Optional selector function (defaults to returning `label`).
 * @returns {string} The resolved permission label or the permission key as fallback.
 */
export function getObjectPermissionLabel({
  permission,
  scope,
  model,
  selector = (p) => p.label,
}) {
  if (!permission) return ''

  // Direct lookup against the memoized maps; honors `model` when given so
  // shared keys (e.g. VM + Event both define `object_actions_stop`) resolve
  // to the model-specific entry.
  const direct = getObjectPermissionByKey(permission, model)
  if (direct) return selector(direct) ?? permission

  if (scope) {
    const scopedMatch = getObjectPermissionsByScope(scope, model).find(
      (p) => p.key === permission,
    )
    if (scopedMatch) return selector(scopedMatch) ?? permission
  }

  return permission
}

/**
 * Resolves a short, human-readable label for a permission key.
 *
 * This is a convenience wrapper around {@link getObjectPermissionLabel}
 * that prefers the `short` label of a permission definition and falls back
 * to the full `label` if no short label is available.
 *
 * @param {Object} options - Resolution options.
 * @param {string} options.permission - The permission key to resolve.
 * @param {string|null|undefined} [options.scope] - Optional permission scope.
 * @param {string|null|undefined} [options.model] - Optional object model identifier.
 * @returns {string} The resolved short permission label or the permission key as fallback.
 */
export function getObjectPermissionShortLabel({ permission, scope, model }) {
  return getObjectPermissionLabel({
    permission,
    scope,
    model,
    selector: (p) => p.short ?? p.label,
  })
}

/**
 * Normalizes a raw permission object into a consistent shape.
 *
 * Supports both snake_case and camelCase input formats.
 *
 * @param {Object} p - Raw permission object from API/store.
 * @returns {{
 *   id: string|null,
 *   objectType: string|null,
 *   objectId: string|null,
 *   entityId: string|null,
 *   entityType: string|null,
 *   permissionKey: string|null
 * }} Normalized permission object.
 */
export function normalizePermission(p) {
  return {
    id: p.id ?? null,
    objectType: p.object_type ?? p.objectType ?? null,
    objectId: p.object_id ?? p.objectId ?? null,
    entityId: p.entity_id ?? p.entityId ?? null,
    entityType: p.entity_type ?? p.entityType ?? null,
    permissionKey: p.permission_key ?? p.permissionKey ?? null,
  }
}

/**
 * Returns the maximum (highest) permission level from a list of keys.
 *
 * Uses the given index map to compare level order.
 *
 * @param {string[]} keys - Permission keys to compare.
 * @param {Map<string, number>} indexMap - Map of permission key -> numeric rank.
 * @returns {string} The highest level key found (defaults to `'none'` if none match).
 */
export function maxLevel(keys, indexMap) {
  let best = 'none'
  let bestIdx = 0
  for (const k of keys) {
    const idx = indexMap.get(k) ?? 0
    if (idx > bestIdx) {
      bestIdx = idx
      best = k
    }
  }
  return best
}

/**
 * Builds a permission snapshot for a single entity (e.g. a role or user).
 *
 * The snapshot separates:
 * - `global` levels per objectType
 * - `globalCreate` toggles per objectType (legacy create support)
 * - `objects` levels per objectType and objectId
 * - `extrasGlobal` extra global permissions per objectType (arrays for stability)
 * - `extrasObjects` extra object permissions per objectType/objectId (arrays for stability)
 *
 * @param {Array<Object>|{ value?: Array<Object> }|null|undefined} perms - Permissions list or a Vue ref-like object containing `.value`.
 * @param {string} entityId - The entity ID to filter for.
 * @param {string} entityType - The entity type to filter for.
 * @returns {{
 *   global: Record<string, string>,
 *   globalCreate: Record<string, boolean>,
 *   objects: Record<string, Record<string, string>>,
 *   extrasGlobal: Record<string, string[]>,
 *   extrasObjects: Record<string, Record<string, string[]>>
 * }} Snapshot representation.
 */
export function buildSnapshot(perms, entityId, entityType) {
  const list = Array.isArray(perms) ? perms : (perms?.value ?? [])

  const global = {}
  const globalCreate = {}
  const objects = {}

  const extrasGlobal = {}
  const extrasObjects = {}

  for (const raw of list) {
    const p = normalizePermission(raw)
    if (!p.objectType) continue
    if (p.entityId !== entityId) continue
    if (p.entityType !== entityType) continue
    if (!p.permissionKey) continue

    if (p.objectId == null) {
      if (p.permissionKey === 'object_create') {
        globalCreate[p.objectType] = true
        continue
      }

      if (LEVEL_KEYS.has(p.permissionKey)) {
        if (p.permissionKey === 'object_full') {
          globalCreate[p.objectType] = true
        }

        global[p.objectType] = maxLevel(
          [global[p.objectType] ?? 'none', p.permissionKey],
          GLOBAL_LEVEL_INDEX,
        )
        continue
      }

      // extra global permission
      if (!extrasGlobal[p.objectType]) extrasGlobal[p.objectType] = new Set()
      extrasGlobal[p.objectType].add(p.permissionKey)
    } else {
      if (p.permissionKey === 'object_create') continue

      if (LEVEL_KEYS.has(p.permissionKey)) {
        if (!objects[p.objectType]) objects[p.objectType] = {}
        objects[p.objectType][p.objectId] = maxLevel(
          [objects[p.objectType][p.objectId] ?? 'none', p.permissionKey],
          OBJECT_LEVEL_INDEX,
        )
        continue
      }

      // extra object permission
      if (!extrasObjects[p.objectType]) extrasObjects[p.objectType] = {}
      if (!extrasObjects[p.objectType][p.objectId])
        extrasObjects[p.objectType][p.objectId] = new Set()
      extrasObjects[p.objectType][p.objectId].add(p.permissionKey)
    }
  }

  // normalize sets to arrays for reactivity + JSON stringify stability
  const extrasGlobalArr = Object.fromEntries(
    Object.entries(extrasGlobal).map(([ot, set]) => [ot, [...set]]),
  )
  const extrasObjectsArr = Object.fromEntries(
    Object.entries(extrasObjects).map(([ot, byId]) => [
      ot,
      Object.fromEntries(
        Object.entries(byId).map(([id, set]) => [id, [...set]]),
      ),
    ]),
  )

  return {
    global,
    globalCreate,
    objects,
    extrasGlobal: extrasGlobalArr,
    extrasObjects: extrasObjectsArr,
  }
}

/**
 * Calculates permission upserts and deletes by diffing two snapshots.
 *
 * Output format is designed to be used for API write operations:
 * - `upserts` contain full permission identifiers including `entity_id` / `entity_type`
 * - `deletes` contain delete specs; some represent "delete all" for a scope
 *
 * @param {Object} before - Snapshot before changes.
 * @param {Object} after - Snapshot after changes.
 * @param {string} entityId - Entity ID used for building upserts.
 * @param {string} entityType - Entity type used for building upserts.
 * @returns {{
 *   upserts: Array<{ entity_id: string, entity_type: string, object_type: string, object_id: string|null, permission_key: string }>,
 *   deletes: Array<{ object_type: string, object_id: string|null, permission_key?: string, previous?: string }>
 * }} Change set.
 */
export function calculateChanges(before, after, entityId, entityType) {
  const upserts = []
  const deletes = []

  const allObjectTypes = new Set([
    ...Object.keys(before.global),
    ...Object.keys(after.global),
    ...Object.keys(before.globalCreate),
    ...Object.keys(after.globalCreate),
    ...Object.keys(before.objects),
    ...Object.keys(after.objects),
    ...Object.keys(before.extrasGlobal ?? {}),
    ...Object.keys(after.extrasGlobal ?? {}),
    ...Object.keys(before.extrasObjects ?? {}),
    ...Object.keys(after.extrasObjects ?? {}),
  ])

  const hasDeleteAllGlobal = (ot) =>
    deletes.some(
      (d) =>
        d.object_type === ot && d.object_id == null && !('permission_key' in d),
    )

  const hasDeleteAllObject = (ot, id) =>
    deletes.some(
      (d) =>
        d.object_type === ot &&
        String(d.object_id) === String(id) &&
        !('permission_key' in d),
    )

  for (const ot of allObjectTypes) {
    // create toggle (legacy)
    const bCreate = !!before.globalCreate?.[ot]
    const aCreate = !!after.globalCreate?.[ot]
    if (bCreate !== aCreate) {
      if (!aCreate) {
        deletes.push({
          object_type: ot,
          object_id: null,
          permission_key: 'object_create',
        })
      } else {
        upserts.push({
          entity_id: entityId,
          entity_type: entityType,
          object_type: ot,
          object_id: null,
          permission_key: 'object_create',
        })
      }
    }

    // global level
    const bG = before.global?.[ot] ?? 'none'
    const aG = after.global?.[ot] ?? 'none'
    if (bG !== aG) {
      if (aG === 'none') {
        deletes.push({
          object_type: ot,
          object_id: null,
          previous: bG,
        })
      } else {
        upserts.push({
          entity_id: entityId,
          entity_type: entityType,
          object_type: ot,
          object_id: null,
          permission_key: aG,
        })
      }
    }

    // object level
    const bO = before.objects?.[ot] ?? {}
    const aO = after.objects?.[ot] ?? {}
    const bOE = before.extrasObjects?.[ot] ?? {}
    const aOE = after.extrasObjects?.[ot] ?? {}

    const allIds = new Set([
      ...Object.keys(bO),
      ...Object.keys(aO),
      ...Object.keys(bOE),
      ...Object.keys(aOE),
    ])

    for (const id of allIds) {
      const bL = bO[id] ?? 'none'
      const aL = aO[id] ?? 'none'
      if (bL !== aL) {
        if (aL === 'none') {
          deletes.push({ object_type: ot, object_id: id })
        } else {
          upserts.push({
            entity_id: entityId,
            entity_type: entityType,
            object_type: ot,
            object_id: id,
            permission_key: aL,
          })
        }
      }
    }

    // extras global
    const bEG = new Set((before.extrasGlobal?.[ot] ?? []).map((k) => String(k)))
    const aEG = new Set((after.extrasGlobal?.[ot] ?? []).map((k) => String(k)))
    const allEG = new Set([...bEG, ...aEG])

    for (const key of allEG) {
      if (bEG.has(key) === aEG.has(key)) continue

      if (!aEG.has(key)) {
        if (!hasDeleteAllGlobal(ot)) {
          deletes.push({
            object_type: ot,
            object_id: null,
            permission_key: key,
          })
        }
      } else {
        upserts.push({
          entity_id: entityId,
          entity_type: entityType,
          object_type: ot,
          object_id: null,
          permission_key: key,
        })
      }
    }

    // extras object
    const bObjExtras = before.extrasObjects?.[ot] ?? {}
    const aObjExtras = after.extrasObjects?.[ot] ?? {}

    const idsExtras = new Set([
      ...Object.keys(bObjExtras),
      ...Object.keys(aObjExtras),
    ])
    for (const id of idsExtras) {
      const bSet = new Set((bObjExtras[id] ?? []).map((k) => String(k)))
      const aSet = new Set((aObjExtras[id] ?? []).map((k) => String(k)))
      const allKeys = new Set([...bSet, ...aSet])

      for (const key of allKeys) {
        if (bSet.has(key) === aSet.has(key)) continue

        if (!aSet.has(key)) {
          if (!hasDeleteAllObject(ot, id)) {
            deletes.push({
              object_type: ot,
              object_id: id,
              permission_key: key,
            })
          }
        } else {
          upserts.push({
            entity_id: entityId,
            entity_type: entityType,
            object_type: ot,
            object_id: id,
            permission_key: key,
          })
        }
      }
    }
  }

  return { upserts, deletes }
}

/**
 * Collects permission IDs to delete based on calculated delete specs and upserts.
 *
 * - Resolves matching permission IDs from the current permissions list.
 * - Additionally ensures exclusivity: when an upsert uses an exclusive level key,
 *   existing exclusive level permissions in the same scope are marked for deletion.
 *
 * @param {Array<Object>} deletes - Delete specifications from {@link calculateChanges}.
 * @param {Array<Object>} upserts - Upsert specifications from {@link calculateChanges}.
 * @param {Array<Object>} permissions - Current permissions list (raw objects).
 * @param {string} entityId - Entity ID to filter for.
 * @param {string} entityType - Entity type to filter for.
 * @returns {Set<string|null>} A set of permission IDs to delete.
 */
export function collectIdsToDelete(
  deletes,
  upserts,
  permissions,
  entityId,
  entityType,
) {
  const idsToDelete = new Set()

  // Process explicit deletes
  for (const deleteSpec of deletes) {
    for (const perm of permissions) {
      const p = normalizePermission(perm)

      if (p.entityId !== entityId) continue
      if (p.entityType !== entityType) continue
      if (p.objectType !== deleteSpec.object_type) continue
      if (
        String(p.objectId ?? 'null') !== String(deleteSpec.object_id ?? 'null')
      )
        continue

      if ('permission_key' in deleteSpec) {
        if (p.permissionKey === deleteSpec.permission_key) {
          idsToDelete.add(p.id)
        }
      } else {
        idsToDelete.add(p.id)
      }
    }
  }

  // For each upsert with exclusive level key, delete existing exclusive level
  for (const upsert of upserts) {
    if (!EXCLUSIVE_LEVEL_KEYS.has(upsert.permission_key)) {
      continue
    }

    for (const perm of permissions) {
      const p = normalizePermission(perm)

      if (p.entityId !== entityId) continue
      if (p.entityType !== entityType) continue
      if (p.objectType !== upsert.object_type) continue
      if (String(p.objectId ?? 'null') !== String(upsert.object_id ?? 'null'))
        continue

      if (EXCLUSIVE_LEVEL_KEYS.has(p.permissionKey)) {
        idsToDelete.add(p.id)
      }
    }
  }

  return idsToDelete
}
