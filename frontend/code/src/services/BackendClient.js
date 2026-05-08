import axios from 'axios'

// Import all service classes
import { getI18nT } from '@/i18n'
import ActivityService from '@/services/ActivityService'
import ApplicationService from '@/services/ApplicationService'
import AuthService from '@/services/AuthService'
import ChangelogService from '@/services/ChangelogService'
import ConnectionParamsService from '@/services/ConnectionParamsService'
import ConnectionService from '@/services/ConnectionService'
import CourseService from '@/services/CourseService'
import DocumentService from '@/services/DocumentService'
import EventService from '@/services/EventService'
import GuacamoleService from '@/services/GuacamoleService'
import LanguageService from '@/services/LanguageService'
import MailActionService from '@/services/MailActionService'
import MailService from '@/services/MailService'
import MailTemplateService from '@/services/MailTemplateService'
import MeService from '@/services/MeService'
import MoodleService from '@/services/MoodleService'
import ObjectPermissionService from '@/services/ObjectPermissionService'
import OSService from '@/services/OSService'
import PolicyService from '@/services/PolicyService'
import ProxmoxService from '@/services/ProxmoxService'
import RoleService from '@/services/RoleService'
import ScimClientService from '@/services/ScimClientService'
import ScimProviderService from '@/services/ScimProviderService'
import StatisticService from '@/services/StatisticService'
import SystemService from '@/services/SystemService'
import TagService from '@/services/TagService'
import TaskService from '@/services/TaskService'
import TemplateService from '@/services/TemplateService'
import UserService from '@/services/UserService'
import VendorService from '@/services/VendorService'
import VMService from '@/services/VMService'
import { useRateLimitStore } from '@/stores/rateLimit'
import { getBackendUrl } from '@/utils/env'
import { formatRetryDuration } from '@/utils/formatRetryDuration'

/**
 * Central backend client that provides unified access to all API services.
 *
 * Features:
 * - Single axios instance shared by all services
 * - Automatic auth token injection via request interceptor
 * - Centralized error handling via response interceptor
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
export default class BackendClient {
  /**
   * Creates a new BackendClient instance.
   *
   * @param {Object} options - Configuration options.
   * @param {string} [options.baseURL] - Base URL for API requests. Defaults to VITE_BACKEND_URL.
   * @param {Object} [options.toast] - Toast notification instance for showing messages.
   * @param {Function} [options.getToken] - Function that returns the current auth token.
   * @param {Function} [options.onLogout] - Callback invoked when session expires (401).
   * @param {number} [options.timeout=5000] - Request timeout in milliseconds.
   */
  constructor({ baseURL, toast, getToken, onLogout, timeout = 5000 } = {}) {
    this.toast = toast
    this.getToken = getToken
    this.onLogout = onLogout
    this._suppressToastCount = 0
    this._rateLimitStore = null

    // Create single axios instance for all services
    this.http = axios.create({
      baseURL: baseURL ?? getBackendUrl(),
      timeout,
    })

    // Request interceptor: Add auth header
    this.http.interceptors.request.use(
      (config) => {
        const token = this.getToken?.()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error),
    )

    // Response interceptor: Centralized error handling
    this.http.interceptors.response.use(
      (response) => response,
      (error) => this.handleError(error),
    )

    // Instantiate all services with shared http instance
    this.activities = new ActivityService(this.http)
    this.applications = new ApplicationService(this.http)
    this.auth = new AuthService(this.http)
    this.changelog = new ChangelogService(this.http)
    this.connectionParams = new ConnectionParamsService(this.http)
    this.connections = new ConnectionService(this.http)
    this.courses = new CourseService(this.http)
    this.documents = new DocumentService(this.http)
    this.events = new EventService(this.http)
    this.guacamole = new GuacamoleService(this.http, this.connections)
    this.languages = new LanguageService(this.http)
    this.mailActions = new MailActionService(this.http)
    this.mails = new MailService(this.http)
    this.mailTemplates = new MailTemplateService(this.http)
    this.me = new MeService(this.http)
    this.moodle = new MoodleService(this.http)
    this.objectPermissions = new ObjectPermissionService(this.http)
    this.os = new OSService(this.http)
    this.policies = new PolicyService(this.http)
    this.proxmox = new ProxmoxService(this.http)
    this.roles = new RoleService(this.http)
    this.scimClients = new ScimClientService(this.http)
    this.scimProviders = new ScimProviderService(this.http)
    this.statistics = new StatisticService(this.http)
    this.system = new SystemService(this.http)
    this.tags = new TagService(this.http)
    this.tasks = new TaskService(this.http)
    this.templates = new TemplateService(this.http)
    this.users = new UserService(this.http)
    this.vendors = new VendorService(this.http)
    this.vms = new VMService(this.http, this)

    // Bind all service methods so they can be safely passed as callbacks
    // (e.g. :fetch-data="backend.roles.search" in Vue templates)
    this._bindAllServiceMethods()
  }

  /**
   * Binds all methods of every service instance so `this` is preserved
   * when methods are passed as references (e.g. as Vue prop callbacks).
   */
  _bindAllServiceMethods() {
    for (const key of Object.keys(this)) {
      const service = this[key]
      if (!service || typeof service !== 'object') continue
      const proto = Object.getPrototypeOf(service)
      if (!proto || proto === Object.prototype) continue

      for (const name of Object.getOwnPropertyNames(proto)) {
        if (name === 'constructor') continue
        const descriptor = Object.getOwnPropertyDescriptor(proto, name)
        if (descriptor && (descriptor.get || descriptor.set)) continue
        if (typeof proto[name] === 'function') {
          service[name] = service[name].bind(service)
        }
      }
    }
  }

  /**
   * Lazy-load rateLimitStore
   */
  get rateLimitStore() {
    if (!this._rateLimitStore) {
      this._rateLimitStore = useRateLimitStore()
    }
    return this._rateLimitStore
  }

  /**
   * Suppresses error toasts from the response interceptor.
   * Call `endSilent()` when done. Calls can be nested safely.
   */
  beginSilent() {
    this._suppressToastCount++
  }

  /**
   * Re-enables error toasts after a `beginSilent()` call.
   */
  endSilent() {
    this._suppressToastCount = Math.max(0, this._suppressToastCount - 1)
  }

  /**
   * Shows a notification to the user.
   * Suppressed while `beginSilent()` is active.
   *
   * @param {'success'|'warning'|'error'|'info'} type - The notification type.
   * @param {string} message - The message to display.
   */
  notify(type, message) {
    if (this._suppressToastCount > 0) return
    if (this.toast?.[type]) {
      this.toast[type](message)
    }
  }

  /**
   * Centralized error handler for API responses.
   *
   * @param {Error} error - The axios error object.
   * @returns {Promise<never>} Rejected promise with the error.
   */
  handleError(error) {
    const t = getI18nT()

    // Network error (no response)
    if (error?.code === 'ERR_NETWORK') {
      this.notify('warning', t('errors.networkError'))
      return Promise.reject(error)
    }

    const status = error?.response?.status
    const errorCode = error?.response?.data?.error_code
    const detail = error?.response?.data?.detail
    const message = error?.response?.data?.message
    const headers = error?.response?.headers ?? {}

    // Rate limit (429) - hand off to global store; toast for short windows
    if (status === 429 || errorCode === 'RATE_LIMIT_EXCEEDED') {
      const toNumber = (value) => {
        const parsed = Number(value)
        return Number.isFinite(parsed) ? parsed : null
      }
      const result = this.rateLimitStore.trigger({
        retryAfter: toNumber(headers['retry-after']),
        resetAt: toNumber(headers['x-ratelimit-reset']),
        limit: toNumber(headers['x-ratelimit-limit']),
        endpoint: error.config?.url,
      })
      if (result.shouldShowToast) {
        this.notify(
          'warning',
          t(`${result.messageKey}.duration`, {
            duration: formatRetryDuration(result.seconds, t),
          }),
        )
      }
      return Promise.reject(error)
    }

    // Check for auth-related errors via error_code
    const isAuthError =
      errorCode === 'CREDENTIALS_NOT_VALID' ||
      errorCode === 'INVALID_AUTH_TOKEN'

    // Session expired (401)
    if (status === 401 && isAuthError) {
      this.notify('warning', t('errors.sessionExpired'))
      this.onLogout?.()
      return Promise.reject(error)
    }

    // Inactive user (400)
    if (status === 400 && errorCode === 'USER_NOT_ACTIVE') {
      this.notify('warning', t('errors.accountNotActive'))
      this.onLogout?.()
      return Promise.reject(error)
    }

    // Incorrect credentials - login view shows its own toast
    if (errorCode === 'INCORRECT_CREDENTIALS') {
      return Promise.reject(error)
    }

    // Forbidden (403) - silent for permission checks
    if (status === 403) {
      return Promise.reject(error)
    }

    // Not found (404) - often expected, don't show toast
    if (status === 404) {
      return Promise.reject(error)
    }

    // Validation error (422) - show first error detail
    if (status === 422) {
      const validationDetail = Array.isArray(detail) ? detail[0]?.msg : detail
      if (validationDetail) {
        this.notify('error', validationDetail)
      }
      return Promise.reject(error)
    }

    // General error - show toast
    const errorMessage = detail ?? message ?? t('errors.generic')
    if (status >= 400) {
      this.notify('error', errorMessage)
    }

    return Promise.reject(error)
  }
}
