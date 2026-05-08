import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useRateLimitStore } from '@/stores/rateLimit'

describe('rateLimit store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-04-30T12:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('activates modal mode when retryAfter is above threshold', () => {
    const store = useRateLimitStore()

    const result = store.trigger({
      retryAfter: 60,
      resetAt: null,
      limit: 10,
      endpoint: '/auth/login',
    })

    expect(store.active).toBe(true)
    expect(store.mode).toBe('modal')
    expect(store.messageKey).toBe('views.rateLimit.endpoints.auth')
    expect(result.mode).toBe('modal')
    expect(result.shouldShowToast).toBe(false)
  })

  it('activates toast mode when retryAfter is below threshold', () => {
    const store = useRateLimitStore()

    const result = store.trigger({
      retryAfter: 5,
      endpoint: '/users/',
    })

    expect(store.active).toBe(true)
    expect(store.mode).toBe('toast')
    expect(store.messageKey).toBe('views.rateLimit.endpoints.generic')
    expect(result.shouldShowToast).toBe(true)
    expect(result.seconds).toBe(5)
  })

  it('does not request another toast while still active', () => {
    const store = useRateLimitStore()

    const first = store.trigger({ retryAfter: 5, endpoint: '/users/' })
    const second = store.trigger({ retryAfter: 5, endpoint: '/users/' })

    expect(first.shouldShowToast).toBe(true)
    expect(second.shouldShowToast).toBe(false)
  })

  it('derives effective seconds from resetAt when retryAfter is missing', () => {
    const store = useRateLimitStore()
    const reset = Math.floor(Date.now() / 1000) + 30

    const result = store.trigger({ resetAt: reset, endpoint: '/users/' })

    expect(result.seconds).toBe(30)
    expect(store.mode).toBe('modal')
  })

  it('falls back to 60 seconds when both retryAfter and resetAt are missing', () => {
    const store = useRateLimitStore()

    const result = store.trigger({ endpoint: '/users/' })

    expect(result.seconds).toBe(60)
    expect(store.mode).toBe('modal')
  })

  it('clears state automatically after the retryAfter window', () => {
    const store = useRateLimitStore()

    store.trigger({ retryAfter: 30, endpoint: '/users/' })
    expect(store.active).toBe(true)

    vi.advanceTimersByTime(30_000)
    expect(store.active).toBe(false)
    expect(store.mode).toBe(null)
    expect(store.messageKey).toBe(null)
  })

  it('clear() resets all state immediately', () => {
    const store = useRateLimitStore()

    store.trigger({ retryAfter: 30, endpoint: '/users/' })
    store.clear()

    expect(store.active).toBe(false)
    expect(store.mode).toBe(null)
    expect(store.retryAfter).toBe(null)
  })

  it('secondsRemaining is derived from resetAt at read time', () => {
    const store = useRateLimitStore()
    const reset = Math.floor(Date.now() / 1000) + 20

    store.trigger({ resetAt: reset, endpoint: '/users/' })
    expect(store.secondsRemaining).toBe(20)
  })

  it('secondsRemaining falls back to retryAfter when resetAt is null', () => {
    const store = useRateLimitStore()

    store.trigger({ retryAfter: 42, endpoint: '/users/' })
    expect(store.secondsRemaining).toBe(42)
  })

  describe('dismissable handling', () => {
    it('marks /auth/* as non-dismissable', () => {
      const store = useRateLimitStore()
      store.trigger({ retryAfter: 60, endpoint: '/auth/login' })
      expect(store.dismissable).toBe(false)
      expect(store.dismissed).toBe(false)
    })

    it('marks /me/password as dismissable and uses the password message key', () => {
      const store = useRateLimitStore()
      store.trigger({ retryAfter: 60, endpoint: '/me/password' })
      expect(store.dismissable).toBe(true)
      expect(store.messageKey).toBe('views.rateLimit.endpoints.password')
    })

    it('falls back to non-dismissable generic config for unknown endpoints', () => {
      const store = useRateLimitStore()
      store.trigger({ retryAfter: 60, endpoint: '/some/unknown' })
      expect(store.dismissable).toBe(false)
      expect(store.messageKey).toBe('views.rateLimit.endpoints.generic')
    })

    it('dismiss() flips the flag without clearing the lockout', () => {
      const store = useRateLimitStore()
      store.trigger({ retryAfter: 60, endpoint: '/me/password' })
      store.dismiss()
      expect(store.dismissed).toBe(true)
      // Still active so e.g. submit-button-disable keeps working
      expect(store.active).toBe(true)
      expect(store.mode).toBe('modal')
    })

    it('a fresh trigger resets dismissed back to false', () => {
      const store = useRateLimitStore()
      store.trigger({ retryAfter: 60, endpoint: '/me/password' })
      store.dismiss()
      expect(store.dismissed).toBe(true)

      store.trigger({ retryAfter: 60, endpoint: '/auth/login' })
      expect(store.dismissed).toBe(false)
      expect(store.dismissable).toBe(false)
    })
  })
})
