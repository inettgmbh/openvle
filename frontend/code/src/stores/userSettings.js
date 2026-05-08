import { defineStore } from 'pinia'

/**
 * Stable view-kind identifiers. Use these instead of string literals so
 * typos like "creat" or "lits" can't sneak in. Add new kinds here as the
 * app grows.
 */
export const VIEW_KIND = Object.freeze({
  LIST: 'list',
  DETAIL: 'detail',
  CREATE: 'create',
  EDIT: 'edit',
  BULK_ACTION: 'bulkAction',
  IMPORT: 'import',
})

/**
 * Stable object-model identifiers used by `state.objects.{objectType}`.
 * Plural form to match existing `object-model` BaseTable props and route
 * paths (`/vms`, `/events`, …). Extend as more views adopt persisted
 * preferences.
 */
export const OBJECT_TYPE = Object.freeze({
  VMS: 'vms',
  EVENTS: 'events',
  TEMPLATES: 'templates',
  RATE_LIMITS: 'rateLimits',
})

function pathParts(path) {
  return String(path).split('.').filter(Boolean)
}

function getAtPath(root, path) {
  return pathParts(path).reduce(
    (acc, key) => (acc != null ? acc[key] : undefined),
    root,
  )
}

function setAtPath(root, path, value) {
  const parts = pathParts(path)
  if (parts.length === 0) return
  let cursor = root
  for (let i = 0; i < parts.length - 1; i++) {
    const key = parts[i]
    if (
      cursor[key] === undefined ||
      cursor[key] === null ||
      typeof cursor[key] !== 'object'
    ) {
      cursor[key] = {}
    }
    cursor = cursor[key]
  }
  cursor[parts[parts.length - 1]] = value
}

/**
 * Persists per-user UI preferences locally and survives reloads.
 *
 * Layout:
 *   {
 *     objects: {                    // settings tied to an object model
 *       [objectType]: {             // OBJECT_TYPE.VMS, OBJECT_TYPE.EVENTS, …
 *         [viewKind]: {             // VIEW_KIND.LIST, VIEW_KIND.DETAIL, …
 *           [settingKey]: value,
 *         }
 *       }
 *     },
 *     app: {                        // views not tied to an object model
 *       [viewKey]: { [settingKey]: value },
 *     },
 *     global: {                     // app-wide preferences
 *       [settingKey]: value,
 *     },
 *   }
 *
 * Access is path-based using dot notation; missing intermediate objects
 * are auto-created on writes.
 *
 * Example paths:
 *   - "objects.vms.list.autoRefresh"
 *   - "objects.events.detail.activeTab"
 *   - "app.dashboard.widgets"
 *   - "global.tablePerPageDefault"
 *
 * The store is `persist: true` and serializes the entire state tree to
 * localStorage. The same shape is intended to be sent verbatim to a
 * future backend endpoint for cross-device sync; keep new settings
 * JSON-serializable. On logout the store is reset.
 */
export const useUserSettingsStore = defineStore('userSettings', {
  state: () => ({
    objects: {},
    app: {},
    global: {},
  }),

  persist: true,

  actions: {
    /**
     * Reads the value at the given dot-path, falling back when missing.
     *
     * @param {string} path - e.g. "objects.vms.list.autoRefresh"
     * @param {*} [fallback]
     * @returns {*}
     */
    get(path, fallback = undefined) {
      const value = getAtPath(this.$state, path)
      return value === undefined ? fallback : value
    },

    /**
     * Writes the value at the given dot-path, creating intermediate
     * objects as needed.
     *
     * @param {string} path
     * @param {*} value
     */
    set(path, value) {
      setAtPath(this.$state, path, value)
    },

    /**
     * Wipes all stored settings. Called on logout.
     */
    reset() {
      this.$reset()
    },
  },
})
