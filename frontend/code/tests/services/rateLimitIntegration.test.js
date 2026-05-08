import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.unmock('@/services/BackendClient')
vi.unmock('@/stores/rateLimit')

vi.mock('@/services/ActivityService', () => ({ default: vi.fn() }))
vi.mock('@/services/ApplicationService', () => ({ default: vi.fn() }))
vi.mock('@/services/AuthService', () => ({ default: vi.fn() }))
vi.mock('@/services/ChangelogService', () => ({ default: vi.fn() }))
vi.mock('@/services/ConnectionParamsService', () => ({ default: vi.fn() }))
vi.mock('@/services/ConnectionService', () => ({ default: vi.fn() }))
vi.mock('@/services/CourseService', () => ({ default: vi.fn() }))
vi.mock('@/services/DocumentService', () => ({ default: vi.fn() }))
vi.mock('@/services/EventService', () => ({ default: vi.fn() }))
vi.mock('@/services/GuacamoleService', () => ({ default: vi.fn() }))
vi.mock('@/services/LanguageService', () => ({ default: vi.fn() }))
vi.mock('@/services/MailActionService', () => ({ default: vi.fn() }))
vi.mock('@/services/MailService', () => ({ default: vi.fn() }))
vi.mock('@/services/MailTemplateService', () => ({ default: vi.fn() }))
vi.mock('@/services/MeService', () => ({ default: vi.fn() }))
vi.mock('@/services/MoodleService', () => ({ default: vi.fn() }))
vi.mock('@/services/ObjectPermissionService', () => ({ default: vi.fn() }))
vi.mock('@/services/OSService', () => ({ default: vi.fn() }))
vi.mock('@/services/PolicyService', () => ({ default: vi.fn() }))
vi.mock('@/services/ProxmoxService', () => ({ default: vi.fn() }))
vi.mock('@/services/RoleService', () => ({ default: vi.fn() }))
vi.mock('@/services/ScimClientService', () => ({ default: vi.fn() }))
vi.mock('@/services/ScimProviderService', () => ({ default: vi.fn() }))
vi.mock('@/services/StatisticService', () => ({ default: vi.fn() }))
vi.mock('@/services/SystemService', () => ({ default: vi.fn() }))
vi.mock('@/services/TagService', () => ({ default: vi.fn() }))
vi.mock('@/services/TaskService', () => ({ default: vi.fn() }))
vi.mock('@/services/TemplateService', () => ({ default: vi.fn() }))
vi.mock('@/services/UserService', () => ({ default: vi.fn() }))
vi.mock('@/services/VendorService', () => ({ default: vi.fn() }))
vi.mock('@/services/VMService', () => ({ default: vi.fn() }))

import BackendClient from '@/services/BackendClient'
import { useRateLimitStore } from '@/stores/rateLimit'

describe('BackendClient + rateLimit store integration', () => {
  let mockToast

  beforeEach(() => {
    setActivePinia(createPinia())
    mockToast = {
      success: vi.fn(),
      warning: vi.fn(),
      error: vi.fn(),
      info: vi.fn(),
    }
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('triggers store when 429 response is received', async () => {
    const client = new BackendClient({ toast: mockToast })
    const store = useRateLimitStore()

    expect(store.active).toBe(false)

    const error = {
      config: { url: '/auth/login' },
      response: {
        status: 429,
        headers: {
          'retry-after': '389',
          'x-ratelimit-reset': '1777580100',
          'x-ratelimit-limit': '10',
        },
        data: {
          detail: 'Too many requests. Please try again later.',
          error_code: 'RATE_LIMIT_EXCEEDED',
        },
      },
    }

    await expect(client.handleError(error)).rejects.toBe(error)

    expect(store.active).toBe(true)
    expect(store.mode).toBe('modal')
    expect(store.messageKey).toBe('views.rateLimit.endpoints.auth')
    expect(store.retryAfter).toBe(389)
    expect(mockToast.warning).not.toHaveBeenCalled()
  })

  it('shows toast when 429 retry-after is short', async () => {
    const client = new BackendClient({ toast: mockToast })
    const store = useRateLimitStore()

    const error = {
      config: { url: '/users/' },
      response: {
        status: 429,
        headers: { 'retry-after': '3' },
        data: { error_code: 'RATE_LIMIT_EXCEEDED' },
      },
    }

    await expect(client.handleError(error)).rejects.toBe(error)

    expect(store.active).toBe(true)
    expect(store.mode).toBe('toast')
    expect(mockToast.warning).toHaveBeenCalledTimes(1)
  })
})
