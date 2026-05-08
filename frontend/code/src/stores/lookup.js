import { defineStore } from 'pinia'
import { reactive } from 'vue'

import backend from '@/services'
import { useMainStore } from '@/stores/main'

// Configuration mapping each keyspace to its service and permission flag
const config = {
  applications: {
    service: (id) => backend.applications.getName(id),
  },
  connectionProfiles: {
    service: (id) => backend.connections.getLabel(id),
    fetchAll: (params) => backend.connections.preload(params),
    needsPermission: false,
  },
  courses: {
    service: (id) => backend.courses.getName(id),
  },
  documents: {
    service: (id) => backend.documents.getName(id),
  },
  events: {
    service: (id) => backend.events.getName(id),
  },
  eventStatus: {
    service: (id) => backend.events.getStatusName(id),
    fetchAll: (params) => backend.events.getStatuses(params),
    needsPermission: false,
  },
  guacamoles: {
    service: (id) => backend.guacamole.getName(id),
    needsPermission: false,
  },
  languages: {
    service: async (id) => {
      const lang = await backend.languages.get(id)
      return { name: lang.nameEnglish, key: lang.key }
    },
    fetchAll: () => backend.languages.list(),
    needsPermission: false,
    static: true,
    mapItem: (item) => ({ name: item.nameEnglish, key: item.key }),
  },
  mailActions: {
    service: (id) => backend.mailActions.getName(id),
    fetchAll: (params) => backend.mailActions.list(params),
    needsPermission: false,
  },
  mail_templates: {
    service: (id) => backend.mailTemplates.getName(id),
  },
  moodleCourses: {
    service: (id) => backend.moodle.getName(id),
    fetchAll: () => backend.moodle.search(''),
    needsPermission: false,
    mapItem: (item) => item.fullname,
  },
  os: {
    service: (id) => backend.os.getName(id),
  },
  policies: {
    service: (id) => backend.policies.getName(id),
  },
  roles: {
    service: (id) => backend.roles.getName(id),
  },
  tags: {
    service: (id) => backend.tags.getLabel(id),
  },
  tasks: {
    service: (id) => backend.tasks.getName(id),
  },
  templates: {
    service: (id) => backend.templates.getName(id),
  },
  users: {
    service: (id) => backend.users.getName(id),
    fetchAll: (params) => backend.users.preload(params),
  },
  vendors: {
    service: (id) => backend.vendors.getName(id),
  },
  vms: {
    service: (id) => backend.vms.getName(id),
    fetchAll: (params) => backend.vms.preload(params),
  },
}

/**
 * A centralized lookup store to resolve UUIDs to human-readable labels,
 * with caching, permission checks and optional persistence.
 */
export const useLookupStore = defineStore(
  'lookup',
  () => {
    const mainStore = useMainStore()

    // Reactive store for each keyspace (e.g. 'users', 'templates')
    const stores = Object.fromEntries(
      Object.keys(config).map((key) => [key, reactive({})]),
    )

    const loaded = Object.fromEntries(
      Object.keys(config).map((key) => [key, false]),
    )

    const fetchPromises = new Map()

    /**
     * Preloads all available entries for a given keyspace (if fetchAll is defined).
     *
     * @param {string} keyspace - The keyspace to preload.
     * @returns {Promise<void>}
     */
    async function fetchAll(keyspace) {
      const resolver = config[keyspace]
      if (!resolver?.fetchAll) return

      if (loaded[keyspace]) return

      const store = stores[keyspace]

      // For static keyspaces, skip fetch if data is already cached from persistence
      if (resolver.static && Object.keys(store).length > 0) {
        loaded[keyspace] = true
        return
      }

      if (fetchPromises.has(keyspace)) return fetchPromises.get(keyspace)
      const needsPermission = resolver.needsPermission !== false

      const promise = (async () => {
        if (needsPermission) {
          const hasAccess = await mainStore.userCan(keyspace, 'read', '/')
          if (!hasAccess) return
        }

        try {
          const results = await resolver.fetchAll({ page: 1, limit: 100 })
          const mapper = resolver.mapItem
          for (const result of results.items) {
            if (result?.id) {
              store[result.id] = mapper ? mapper(result) : result.name
            }
          }
          loaded[keyspace] = true
        } catch (err) {
          console.error(`[lookup/${keyspace}] fetchAll error:`, err)
        } finally {
          fetchPromises.delete(keyspace)
        }
      })()

      fetchPromises.set(keyspace, promise)
      return promise
    }

    /**
     * Resolves a single ID in a given keyspace.
     *
     * @param {string} keyspace - The keyspace to resolve from (e.g. 'users', 'vms').
     * @param {string|null|undefined} id - The UUID to resolve.
     * @returns {Promise<string|Object|null>} The resolved value or ID itself on failure/no access.
     */
    async function resolve(keyspace, id) {
      if (id === undefined || id === null) return null

      const resolver = config[keyspace]
      if (!resolver) throw new Error(`[lookup] Unknown keyspace: ${keyspace}`)

      const store = stores[keyspace]
      if (store[id]) return store[id]

      const needsPermission = resolver.needsPermission !== false

      if (needsPermission) {
        const hasAccess = await mainStore.userCan(keyspace, 'read', `/${id}`)
        if (!hasAccess) return id
      }

      // try fetchAll if available
      if (resolver.fetchAll) {
        await fetchAll(keyspace)
        if (store[id]) return store[id]
      }

      // fallback to single fetch
      try {
        const result = await resolver.service(id)
        store[id] = result
        return result
      } catch (err) {
        console.error(`[lookup/${keyspace}] error for id ${id}:`, err)
        store[id] = id
        return id
      }
    }

    /**
     * Resolves multiple IDs in a given keyspace.
     *
     * @param {string} keyspace - The keyspace to resolve from (e.g. 'users', 'vms').
     * @param {Array<string>} ids - List of UUIDs to resolve.
     * @returns {Promise<Array<string|Object>>} Array of resolved values (or raw IDs on failure).
     */
    async function resolveMany(keyspace, ids) {
      const store = stores[keyspace]
      const missing = [...new Set(ids)].filter((id) => !store[id])
      if (missing.length > 0) {
        await Promise.all(missing.map((id) => resolve(keyspace, id)))
      }
      return ids.map((id) => store[id] ?? id)
    }

    /**
     * Resets all lookup-related caches and internal states.
     *
     * This function performs the following actions:
     * - Clears *all* entries in each store inside the `stores` object.
     * - Resets all flags in the `loaded` object to `false`.
     * - Clears any pending or cached fetch promises via `fetchPromises.clear()`.
     * - Re-applies default role mappings.
     *
     * @returns {void}
     */
    function reset() {
      for (const store of Object.values(stores)) {
        Object.keys(store).forEach((k) => delete store[k])
      }
      for (const key in loaded) loaded[key] = false
      fetchPromises.clear()

      applyDefaults()
    }

    /**
     * Updates the cached name of an object in the keyspace.
     *
     * @param {string} keyspace - The keyspace to update (e.g. 'users', 'vms').
     * @param {string} id - The UUID to update.
     * @param {string} newName - New resolved value.
     */
    function update(keyspace, id, newName) {
      if (!id || newName == null) return
      const resolver = config[keyspace]
      if (!resolver) throw new Error(`[lookup] Unknown keyspace: ${keyspace}`)

      const store = stores[keyspace]
      store[id] = newName
    }

    /**
     * Extracts the ID and name from an object and updates the given keyspace with them.
     *
     * This is a helper function that safely accesses the `idProp` and `nameProp` properties
     * from the provided object and calls `update(keyspace, id, name)` if valid.
     *
     * @param {string} keyspace - The keyspace or namespace in which the update should occur.
     * @param {Object} obj - The source object containing the ID and name properties.
     * @param {string} [idProp='id'] - The property name to extract the ID from.
     * @param {string} [nameProp='name'] - The property name to extract the name/label from.
     * @returns {void}
     */
    function updateFromObject(keyspace, obj, idProp = 'id', nameProp = 'name') {
      if (!obj) return
      const id = obj?.[idProp]
      const name = obj?.[nameProp]
      if (!id || name == null) return
      update(keyspace, id, name)
    }

    /**
     * Removes an entry from the cache of a keyspace.
     *
     * @param {string} keyspace - The keyspace or namespace in which the remove should occur.
     * @param {string} id - The UUID to remove.
     */
    function forget(keyspace, id) {
      if (!id) return
      const store = stores[keyspace]
      if (!store) return
      delete store[id]
    }

    /**
     * Applies default name labels predefined objects.
     *
     * @returns {void}
     */
    function applyDefaults() {
      if (mainStore?.settings?.roles?.students != undefined) {
        stores.roles[mainStore?.settings?.roles?.students] = 'Studierende'
      }
      if (mainStore?.settings?.roles?.teachers != undefined) {
        stores.roles[mainStore?.settings?.roles?.teachers] = 'Lehrende'
      }
    }

    applyDefaults()

    return {
      resolve,
      resolveMany,
      fetchAll,
      reset,
      update,
      updateFromObject,
      forget,
      applyDefaults,
      ...stores,
    }
  },
  {
    persist: true,
  },
)
