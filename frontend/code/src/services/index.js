import { useToast } from 'vue-toastification'

import BackendClient from '@/services/BackendClient'
import { useMainStore } from '@/stores/main'

/**
 * Singleton backend client instance.
 *
 * Provides unified access to all API services with centralized:
 * - Auth token injection via request interceptor
 * - Error handling via response interceptor
 * - Session expiry detection with automatic logout
 *
 * @example
 * import backend from '@/services'
 *
 * // CRUD operations
 * await backend.users.list({ page: 1, limit: 10 })
 * await backend.users.get(userId)
 * await backend.users.create({ name, email })
 * await backend.roles.getName(roleId)
 */
const backend = new BackendClient({
  toast: useToast(),

  /**
   * Gets the current auth token from mainStore.
   * Called at runtime when Pinia is already initialized.
   *
   * @returns {string|null} The current auth token or null.
   */
  getToken: () => {
    const mainStore = useMainStore()
    return mainStore.user?.token ?? null
  },

  /**
   * Handles session expiry by calling mainStore.logout().
   * Called at runtime when Pinia is already initialized.
   */
  onLogout: () => {
    const mainStore = useMainStore()
    mainStore.logout()
  },
})

export default backend
