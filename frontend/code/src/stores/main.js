import * as Sentry from '@sentry/vue'
import { defineStore } from 'pinia'
import { reactive } from 'vue'
import { useToast } from 'vue-toastification'

import { getI18nT, setLocale } from '@/i18n'
import router from '@/router'
import backend from '@/services'
import { useLookupStore } from '@/stores/lookup'
import { useUserSettingsStore } from '@/stores/userSettings'
import { parseBoolEnv } from '@/utils/env.js'

const toast = useToast()

export const useMainStore = defineStore('main', {
  state: () => ({
    user: reactive({
      permissions: [],
      role: '',
    }),

    /* Save outstanding policies of user so we can show them one after one */
    outstandingPolicies: [],

    /* Save system settings (from the backend to modular show function) */
    settings: [],
    settingsStatus: 'empty',

    /* Field focus with ctrl+k (to register only once) */
    isFieldFocusRegistered: false,
  }),
  persist: true,
  getters: {
    isLoggedIn: (state) => {
      return state.user.token
    },
    getUser: (state) => {
      return state.user
    },
    getUsername: (state) => {
      return state.user?.username
    },
    getUserMail: (state) => {
      return state.user?.email
    },
    getUserToken: (state) => {
      return state.user?.token
    },
    getOutStandingPolicies: (state) => {
      return state.outstandingPolicies[0]
    },
    getUserId: (state) => {
      return state.user?.id
    },
    getUserRole: (state) => {
      return state.user?.role
    },
  },
  actions: {
    /**
     * Initialize store.
     *
     * @returns {Promise<void>}
     */
    async init() {
      if (
        this.settings &&
        typeof this.settings === 'object' &&
        Object.keys(this.settings).length > 0 &&
        this.isLoggedIn
      ) {
        return
      } else {
        await this.loadSettings()
      }
    },

    /**
     * Load system settings from backend.
     *
     * @returns {Promise<void>}
     */
    async loadSettings() {
      this.settingsStatus = 'loading'
      const toBool = (v) => {
        if (typeof v === 'boolean') return v
        if (v == null) return false
        const s = String(v).trim().toLowerCase()
        return s === 'true' || s === '1' || s === 'yes' || s === 'on'
      }

      const toInt = (v) => {
        const n =
          typeof v === 'number' ? Math.trunc(v) : parseInt(String(v), 10)
        return Number.isFinite(n) ? n : null
      }

      const toFloat = (v) => {
        const n = typeof v === 'number' ? v : parseFloat(String(v))
        return Number.isFinite(n) ? n : null
      }

      const toJSON = (v) => {
        if (v == null || v === '') return null
        try {
          return typeof v === 'string' ? JSON.parse(v) : v
        } catch {
          return v
        }
      }

      const castByType = (type, value) => {
        switch ((type || '').toLowerCase()) {
          case 'boolean':
            return toBool(value)
          case 'int':
          case 'integer':
            return toInt(value)
          case 'number':
          case 'float':
            return toFloat(value)
          case 'json':
            return toJSON(value)
          case 'string':
          default:
            return value
        }
      }

      const isPlainObject = (v) =>
        v !== null && typeof v === 'object' && !Array.isArray(v)

      try {
        const response = await backend.system.list({})

        if (!Array.isArray(response?.items)) {
          throw new Error('settings response missing items array')
        }

        this.settingsStatus = 'loaded'

        const nestedSettings = {}
        for (const { key, value, type } of response.items) {
          const parts = key.split('.')
          let curr = nestedSettings
          for (let i = 0; i < parts.length; i++) {
            const part = parts[i]
            const last = i === parts.length - 1
            if (last) {
              curr[part] = castByType(type, value)
            } else {
              if (!isPlainObject(curr[part])) curr[part] = {}
              curr = curr[part]
            }
          }
        }

        this.settings = nestedSettings

        // Apply lookup store defaults so they're immediately resolvable
        useLookupStore().applyDefaults()
      } catch (e) {
        console.warn(e)
        this.settingsStatus = 'error'
      }
    },

    /**
     * Logout current user, reset state and redirect to login screen.
     *
     * @returns {Promise<void>}
     */
    async logout() {
      router.push({ path: `/auth/login` })
      this.$reset()
      useLookupStore().reset()
      useUserSettingsStore().reset()
      await this.init()
    },

    /**
     * Login a user with access-token
     *
     * @param {string} access_token - The jwt access-token provided by the backend
     * @param {string} token_type - The type of the returned token
     * @returns {Promise<void>}
     */
    async login(backendLoginResponse) {
      const splitted = backendLoginResponse['access_token'].split('.')
      if (splitted.length < 2) return false
      const jwtPayload = JSON.parse(atob(splitted[1]))
      this.user = jwtPayload.user
      this.user.id = jwtPayload.sub
      this.user.token = backendLoginResponse['access_token']
      this.user.token_exp = jwtPayload.exp
      this.user.token_iat = jwtPayload.iat
      this.user.token_type = backendLoginResponse['token_type']
      this.user.locale = jwtPayload.user?.locale || null // fixme to api endpoint

      // Sync UI language to user's locale
      if (this.user.locale) {
        await setLocale(this.user.locale)
      }

      if (jwtPayload.type === 'bearer') {
        await this.fetchPermissions()
        await this.fetchUserDashboard()
      }

      /* Set user in sentry, if sentry is enabled */
      const sentryEnabled = parseBoolEnv(import.meta.env.VITE_SENTRY_ENABLED)
      const sentryTransmitUserDetails = parseBoolEnv(
        import.meta.env.VITE_SENTRY_TRANSMIT_USER_DETAILS,
      )
      if (sentryEnabled && sentryTransmitUserDetails) {
        Sentry.setUser({
          username: this.user.username,
          email: this.user.email,
        })
      }

      /** Handle outstanding policies */
      if (
        backendLoginResponse['outstanding_policies'] &&
        backendLoginResponse['outstanding_policies'].length > 0
      ) {
        this.addOutstandingPolicies(
          backendLoginResponse['outstanding_policies'],
        )
        const t = getI18nT()
        toast.info(t('errors.loginPolicyRequired'), { timeout: 4200 })
        return router.push(
          '/policy/' + backendLoginResponse['outstanding_policies'][0],
        )
      } else {
        const t = getI18nT()
        toast.success(t('errors.loginSuccess'))
      }

      /* Reload settings with authorization included (provides more data) */
      await this.loadSettings()

      // Inject current user into lookup store so their ID is always resolvable
      useLookupStore().update('users', this.user.id, this.user.name)
    },

    /**
     * Checks if the user has the requested permission for the specified object.
     *
     * @param {string} objectType - The type of the object (e.g., 'templates', 'vms').
     * @param {string} objectPermission - The permission to check (e.g., 'read', 'create', 'update', 'delete').
     * @param {string} objectPath - The path to check (e.g., '/' for any object, '/*' for all object, or '/<objectId>' for one object).
     * @returns {Promise<boolean>} Resolves to true if permission is granted, otherwise false.
     */
    /**
     * Synchronous permission check. Only works when permissions are already loaded.
     * Used by the route guard for instant navigation when permissions are available.
     *
     * @param {string} objectType - The object type to check.
     * @param {string} objectPermission - The required permission.
     * @param {string} objectPath - The object path.
     * @returns {boolean} Whether the user has the permission.
     */
    userCanSync(objectType, objectPermission, objectPath) {
      if (objectPath === undefined) return false
      if (this.user.permissions === undefined) return false

      return this._hasPermission(
        this.user.permissions,
        objectType,
        objectPath,
        objectPermission,
      )
    },

    async userCan(objectType, objectPermission, objectPath) {
      /** Exit early if requested path is undefined */
      if (objectPath === undefined) return false

      /** Wait until user permissions are available */
      if (this.user.permissions === undefined) {
        await new Promise((resolve) => {
          const interval = setInterval(() => {
            if (this.user.permissions !== undefined) {
              clearInterval(interval)
              resolve()
            }
          }, 50)
        })
      }

      // Initial check with current permissions
      if (
        this._hasPermission(
          this.user.permissions,
          objectType,
          objectPath,
          objectPermission,
        )
      ) {
        return true
      }

      // If permissions might be outdated (>2.5 min), reload and retry
      if (Date.now() - this.user.loadedAt > 150000) {
        await this.fetchPermissions()
        await this.fetchUserDashboard()
        return this._hasPermission(
          this.user.permissions,
          objectType,
          objectPath,
          objectPermission,
        )
      }

      return false
    },

    /**
     * Checks whether a user has a specific permission for a given object path and type.
     * @private
     */
    _hasPermission(permissions, objectType, objectPath, objectPermission) {
      /** Some permissions imply other permissions */
      const impliedPermissions = {
        create: ['read'],
        update: ['read'],
        delete: ['read', 'update'],
        reset: ['read'],
      }

      function permissionImplies(allowed, requested) {
        return allowed.some(
          (p) =>
            p === requested ||
            (impliedPermissions[p] &&
              impliedPermissions[p].includes(requested)) ||
            p === 'full',
        )
      }

      for (const permission of permissions) {
        const { type, path, permissions: allowed } = permission

        if (objectPath === undefined) return false

        const isGlobalRead =
          objectPath === '/*' &&
          path === '/' &&
          objectPermission === 'read' &&
          type === objectType &&
          permissionImplies(allowed, objectPermission)

        if (isGlobalRead) return true

        const matchesPath =
          objectPath.startsWith(path) ||
          (objectPath === '/' &&
            path !== '/' &&
            permissionImplies(allowed, objectPermission))

        const matchesPermission = permissionImplies(allowed, objectPermission)

        if (type === objectType && matchesPath && matchesPermission) {
          return true
        }
      }

      return false
    },

    /**
     * Fetches the user's current permissions from the backend.
     *
     * @returns {Promise<boolean>} True when finished loading.
     */
    async fetchPermissions() {
      this.user.permissions = await backend.me.getPermissions()
      this.user.loadedAt = Date.now()
      return true
    },

    /**
     * Parses the user's permissions and assigns their role.
     *
     * @returns {Promise<void>}
     */
    async fetchUserDashboard() {
      // Find the dashboard item
      const dashboardItem = this.user.permissions.find(
        (item) => item.type === 'dashboards',
      )
      // Default to an empty array if no dashboard item is found
      const permissions = dashboardItem ? dashboardItem.permissions : []
      // Check permissions and assign role
      if (permissions.includes('admins')) {
        this.user.role = 'admin'
      } else if (permissions.includes('verwaltende')) {
        this.user.role = 'verwaltende'
      } else if (permissions.includes('lehrende')) {
        this.user.role = 'lehrende'
      } else {
        this.user.role = 'student'
      }
    },

    /**
     * Adds outstanding policy IDs to the user's list.
     *
     * @param {Array<string>|string} id - One or more outstanding policy IDs to add.
     */
    addOutstandingPolicies(id) {
      this.outstandingPolicies = this.outstandingPolicies.concat(
        Object.values(id),
      )
    },

    /**
     * Removes a policy ID from outstanding list.
     *
     * @param {string} id - The ID of the policy to remove.
     */
    removeOutstandingPolicy(id) {
      const index = this.outstandingPolicies.indexOf(id)
      if (index !== -1) {
        this.outstandingPolicies.splice(index, 1)
      }
    },

    /**
     * Updates user details with selected fields.
     *
     * @param {Object} payload - The user fields to update.
     * @param {string} [payload.name]
     * @param {string} [payload.username]
     * @param {string} [payload.email]
     */
    setUser(payload) {
      if (payload.name) {
        this.user.name = payload.name
      }
      if (payload.username) {
        this.user.username = payload.username
      }
      if (payload.email) {
        this.user.email = payload.email
      }
    },
  },
})
