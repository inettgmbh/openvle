import { defineStore } from 'pinia'

const TOAST_THRESHOLD_SECONDS = 10
const FALLBACK_SECONDS = 60

/**
 * Per-endpoint configuration for the rate-limit modal/toast.
 *
 * `match` runs against the request URL; the first hit wins. New entries
 * can override the default message key and whether the modal is
 * dismissable. Order matters — put more specific patterns first.
 *
 * `dismissable: true` lets the user close the modal manually (close X /
 * overlay click) — useful when the rate-limited endpoint isn't blocking
 * the rest of the app (e.g. password change). Default is non-dismissable
 * (login lockouts, where the user shouldn't keep retrying blindly).
 */
const ENDPOINT_CONFIG = [
  {
    match: (url) => /\/me\/password/.test(url),
    messageKey: 'views.rateLimit.endpoints.password',
    dismissable: true,
  },
  {
    match: (url) => /\/auth\//.test(url),
    messageKey: 'views.rateLimit.endpoints.auth',
    dismissable: false,
  },
]

const DEFAULT_CONFIG = {
  messageKey: 'views.rateLimit.endpoints.generic',
  dismissable: false,
}

function resolveEndpointConfig(endpoint) {
  if (!endpoint) return DEFAULT_CONFIG
  return (
    ENDPOINT_CONFIG.find((entry) => entry.match(endpoint)) ?? DEFAULT_CONFIG
  )
}

function nowSeconds() {
  return Math.floor(Date.now() / 1000)
}

let clearTimer = null

export const useRateLimitStore = defineStore('rateLimit', {
  state: () => ({
    active: false,
    mode: null,
    retryAfter: null,
    resetAt: null,
    limit: null,
    endpoint: null,
    messageKey: null,
    expiresAt: null,
    totalSeconds: null,
    dismissable: false,
    dismissed: false,
  }),

  getters: {
    secondsRemaining(state) {
      if (!state.expiresAt) return 0
      return Math.max(0, Math.ceil((state.expiresAt - Date.now()) / 1000))
    },
  },

  actions: {
    /**
     * Activates the rate-limit state for a given endpoint.
     * Returns metadata so callers can show a toast for short windows.
     */
    trigger({ retryAfter, resetAt, limit, endpoint }) {
      const fromReset = resetAt ? Math.max(0, resetAt - nowSeconds()) : null
      // Prefer retryAfter (countdown) over resetAt (timestamp, prone to clock skew)
      const effectiveSeconds = retryAfter ?? fromReset ?? FALLBACK_SECONDS
      const wasActive = this.active
      const config = resolveEndpointConfig(endpoint)

      this.retryAfter = retryAfter ?? null
      this.resetAt = resetAt ?? null
      this.limit = limit ?? null
      this.endpoint = endpoint ?? null
      this.messageKey = config.messageKey
      this.dismissable = config.dismissable
      this.dismissed = false
      this.mode = effectiveSeconds < TOAST_THRESHOLD_SECONDS ? 'toast' : 'modal'
      this.totalSeconds = Math.max(effectiveSeconds, 1)
      this.expiresAt = Date.now() + this.totalSeconds * 1000
      this.active = true

      if (clearTimer) clearTimeout(clearTimer)
      clearTimer = setTimeout(
        () => this.clear(),
        Math.max(effectiveSeconds, 1) * 1000,
      )

      return {
        mode: this.mode,
        messageKey: this.messageKey,
        seconds: effectiveSeconds,
        shouldShowToast: this.mode === 'toast' && !wasActive,
      }
    },

    /**
     * User dismissed the modal manually. Only meaningful when the
     * current endpoint config has `dismissable: true`. The store stays
     * `active` (so e.g. submit-button-disabling still works) until the
     * timer expires; the modal just hides.
     */
    dismiss() {
      this.dismissed = true
    },

    clear() {
      this.active = false
      this.mode = null
      this.retryAfter = null
      this.resetAt = null
      this.limit = null
      this.endpoint = null
      this.messageKey = null
      this.expiresAt = null
      this.totalSeconds = null
      this.dismissable = false
      this.dismissed = false
      if (clearTimer) {
        clearTimeout(clearTimer)
        clearTimer = null
      }
    },
  },
})
