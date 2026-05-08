import { defineStore } from 'pinia'

export const usePreferencesStore = defineStore('preferences', {
  state: () => ({
    preferences: {
      tables: {}, // { users: { perPage: 20, sortKey: 'name', sortDirection: 'asc' } }
      filters: {}, // { users: { query: 'johndoe', active: true } }
      views: {}, // { dashboard: { layout: 'compact' } }
      forms: {}, // { userEdit: { showAdvanced: false } }
    },
  }),

  actions: {
    ensureNamespace(namespace) {
      if (!this.preferences[namespace]) {
        this.preferences[namespace] = {}
      }
    },

    ensureModel(namespace, objectModel) {
      this.ensureNamespace(namespace)
      if (!this.preferences[namespace][objectModel]) {
        this.preferences[namespace][objectModel] = {}
      }
    },

    setPreference(objectModel, key, value, namespace = 'tables') {
      this.ensureModel(namespace, objectModel)
      this.preferences[namespace][objectModel][key] = value
    },

    getPreference(objectModel, key, defaultValue = null, namespace = 'tables') {
      return this.preferences?.[namespace]?.[objectModel]?.[key] ?? defaultValue
    },

    getModelPreferences(objectModel, namespace = 'tables') {
      return this.preferences?.[namespace]?.[objectModel] ?? {}
    },

    resetPreferences(objectModel, namespace = 'tables') {
      if (!this.preferences?.[namespace]) return
      delete this.preferences[namespace][objectModel]
    },

    resetNamespace(namespace = 'tables') {
      this.ensureNamespace(namespace)
      this.preferences[namespace] = {}
    },

    resetAllPreferences() {
      this.preferences = {}
    },
  },

  persist: true,
})
