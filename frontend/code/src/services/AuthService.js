import { useToast } from 'vue-toastification'

import { getI18nT } from '@/i18n'
import { useMainStore } from '@/stores/main.js'

/**
 * Service for authentication-related API operations and route guards.
 */
export default class AuthService {
  /**
   * @param {import('axios').AxiosInstance} http
   */
  constructor(http) {
    this.http = http
    this._mainStore = null
    this._toast = null

    // Bind navigation guards to preserve 'this' context when used as callbacks
    this.requireAuth = this.requireAuth.bind(this)
    this.requireLogout = this.requireLogout.bind(this)
    this.requirePolicyAgree = this.requirePolicyAgree.bind(this)
    this.loginOIDC = this.loginOIDC.bind(this)
  }

  /**
   * Lazy-load mainStore - only call useMainStore() at runtime when Pinia is initialized.
   */
  get mainStore() {
    if (!this._mainStore) {
      this._mainStore = useMainStore()
    }
    return this._mainStore
  }

  /**
   * Lazy-load toast - only call useToast() at runtime when Vue is initialized.
   */
  get toast() {
    if (!this._toast) {
      this._toast = useToast()
    }
    return this._toast
  }

  // ============================================================
  // Authentication Methods
  // ============================================================

  /**
   * Logs the user in using form-encoded credentials.
   *
   * @param {Object} credentials - The login credentials.
   * @returns {Promise<Object>} The full Axios response object.
   */
  async login(credentials) {
    const response = await this.http.post('/auth/login', credentials, {
      headers: { 'content-type': 'application/x-www-form-urlencoded' },
    })
    return response
  }

  /**
   * Registers a new user.
   *
   * @param {Object} credentials - The signup data.
   * @returns {Promise<Object>} The full Axios response object.
   */
  async signUp(credentials) {
    const response = await this.http.post('/auth/sign-up', credentials)
    return response
  }

  /**
   * Sends a password reset request to the server.
   *
   * @param {Object} credentials - The user's email or identifier.
   * @returns {Promise<Object>} The full Axios response object.
   */
  async passwordResetRequest(credentials) {
    const response = await this.http.post('/auth/password-reset', credentials)
    return response
  }

  /**
   * Verifies the validity of a password reset token.
   *
   * @param {string} resetToken - The token to verify.
   * @returns {Promise<Object>} The full Axios response object.
   */
  async passwordResetTokenCheck(resetToken) {
    const response = await this.http.post(
      '/auth/password-reset-token/',
      resetToken,
    )
    return response
  }

  /**
   * Completes the password reset using a token and new credentials.
   *
   * @param {string} resetToken - The token received by email.
   * @param {Object} credentials - The new password credentials.
   * @returns {Promise<Object>} The full Axios response object.
   */
  async passwordResetProcess(resetToken, credentials) {
    const response = await this.http.post(
      `/auth/password-reset/${resetToken}`,
      credentials,
    )
    return response
  }

  /**
   * Attempts reauthentication using an existing session or token.
   *
   * @returns {Promise<Object>} The full Axios response object.
   */
  async reauth() {
    const response = await this.http.post('/auth/reauthenticate')
    return response
  }

  // ============================================================
  // Navigation Guards
  // ============================================================

  /**
   * Navigation guard to protect routes that require authentication.
   *
   * @param {Object} to - The target route.
   * @param {Object} from - The previous route.
   * @param {Function} next - The navigation callback.
   */
  requireAuth(to, from, next) {
    const mainStore = this.mainStore

    try {
      // Check if user is logged in and exists
      if (!mainStore.isLoggedIn || !mainStore.getUser) {
        return next({ path: '/auth/login', query: { redirect: to.fullPath } })
      }

      // Check if user has outstanding policies to accept
      if (mainStore.getOutStandingPolicies) {
        return next({ path: '/policy/' + mainStore.getOutStandingPolicies })
      }

      // Check if path requires no permission to access
      if (to.meta.noAuth === true) {
        return next()
      }

      // Check if required system setting is enabled (may need async wait)
      if (to.meta.requiredSetting) {
        if (mainStore.settingsStatus !== 'loaded') {
          return this._requireAuthWaitForSettings(to, from, next)
        }
        const value = to.meta.requiredSetting
          .split('.')
          .reduce((acc, key) => acc?.[key], mainStore.settings)
        if (!value) {
          this.toast.error(getI18nT()('errors.featureUnavailable'))
          const fallbackPath =
            !from.fullPath || from.fullPath.startsWith('/auth/')
              ? '/'
              : from.fullPath
          return next(fallbackPath)
        }
      }

      // Set path to objectId if set, otherwise to / for global access
      const objectPath = to.params.id ? `/${to.params.id}` : '/'

      // Fast path: permissions already loaded — resolve synchronously
      if (mainStore.user?.permissions !== undefined) {
        return this._resolvePermission(mainStore, to, from, next, objectPath)
      }

      // Slow path: permissions not yet available — wait async
      return mainStore
        .userCan(to.meta.type, to.meta.permission, objectPath)
        .then((allowed) => {
          if (allowed) {
            return next()
          }
          this.toast.error(getI18nT()('errors.noPermission'))
          const fallbackPath =
            !from.fullPath || from.fullPath.startsWith('/auth/')
              ? '/'
              : from.fullPath
          return next(fallbackPath)
        })
    } catch {
      // Catch errors and logout user
      mainStore.logout()
      this.toast.error(getI18nT()('errors.accountError'))
      return next({ path: '/auth/login', query: { redirect: '/' } })
    }
  }

  /**
   * Synchronous permission check when permissions are already loaded.
   * @private
   */
  _resolvePermission(mainStore, to, from, next, objectPath) {
    const allowed = mainStore.userCanSync(
      to.meta.type,
      to.meta.permission,
      objectPath,
    )
    if (allowed) {
      return next()
    }
    this.toast.error(getI18nT()('errors.noPermission'))
    const fallbackPath =
      !from.fullPath || from.fullPath.startsWith('/auth/') ? '/' : from.fullPath
    return next(fallbackPath)
  }

  /**
   * Async fallback for requireAuth when settings are not yet loaded.
   * @private
   */
  async _requireAuthWaitForSettings(to, from, next) {
    const mainStore = this.mainStore
    try {
      await new Promise((resolve) => {
        const interval = setInterval(() => {
          if (mainStore.settingsStatus === 'loaded') {
            clearInterval(interval)
            resolve()
          }
        }, 50)
      })
      const value = to.meta.requiredSetting
        .split('.')
        .reduce((acc, key) => acc?.[key], mainStore.settings)
      if (!value) {
        this.toast.error(getI18nT()('errors.featureUnavailable'))
        const fallbackPath =
          !from.fullPath || from.fullPath.startsWith('/auth/')
            ? '/'
            : from.fullPath
        return next(fallbackPath)
      }

      const objectPath = to.params.id ? `/${to.params.id}` : '/'
      if (
        await mainStore.userCan(to.meta.type, to.meta.permission, objectPath)
      ) {
        return next()
      }
      this.toast.error(getI18nT()('errors.noPermission'))
      const fallbackPath =
        !from.fullPath || from.fullPath.startsWith('/auth/')
          ? '/'
          : from.fullPath
      return next(fallbackPath)
    } catch {
      mainStore.logout()
      this.toast.error(getI18nT()('errors.accountError'))
      return next({ path: '/auth/login', query: { redirect: '/' } })
    }
  }

  /**
   * Navigation guard to redirect users who must agree to policies.
   *
   * @param {Object} to - The target route.
   * @param {Object} from - The previous route.
   * @param {Function} next - The navigation callback.
   */
  async requirePolicyAgree(to, from, next) {
    const mainStore = this.mainStore
    if (!mainStore.getOutStandingPolicies) {
      return next({ path: '/' })
    }
    return next()
  }

  /**
   * Navigation guard to prevent access if the user is already logged in.
   *
   * @param {Object} to - The target route.
   * @param {Object} from - The previous route.
   * @param {Function} next - The navigation callback.
   */
  async requireLogout(to, from, next) {
    const mainStore = this.mainStore
    if (mainStore.isLoggedIn && mainStore.getUser) {
      this.toast.info(getI18nT()('errors.alreadyLoggedIn'))
      return next(from.fullPath)
    } else {
      return next()
    }
  }

  /**
   * Navigation guard to login user via OIDC on callback URL.
   *
   * @param {Object} to - The target route.
   * @param {Object} from - The previous route.
   * @param {Function} next - The navigation callback.
   */
  async loginOIDC(to, from, next) {
    const mainStore = this.mainStore

    if (mainStore.isLoggedIn && mainStore.getUser) {
      return next({ path: from.fullPath, replace: true })
    }

    const token = to.query.access_token
      ? String(to.query.access_token)
      : undefined
    const tokenType = to.query.token_type
      ? String(to.query.token_type)
      : undefined
    const outstandingPoliciesRaw = to.query.outstanding_policies
      ? String(to.query.outstanding_policies)
      : undefined
    const redirectURL = String(to.query.redirect) || '/'
    let outstandingPolicies = []

    if (outstandingPoliciesRaw) {
      outstandingPolicies =
        String(outstandingPoliciesRaw).match(/[0-9a-fA-F-]{36}/g) || []
    }

    if (!to.query.error && !token) {
      to.query.error = 'missing_token'
    }

    if (to.query.error) {
      return next({
        name: 'login',
        query: { error: String(to.query.error) },
      })
    }

    mainStore.login({
      access_token: token,
      token_type: tokenType,
      outstanding_policies: outstandingPolicies,
    })
    return next({ path: redirectURL, replace: false })
  }
}
