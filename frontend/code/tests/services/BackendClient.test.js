import { beforeEach, describe, expect, it, vi } from 'vitest'

// Unmock BackendClient (no global mock exists, but ensure it's not accidentally mocked)
vi.unmock('@/services/BackendClient')

import BackendClient from '@/services/BackendClient'

// Mock all service imports
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

const mockRateLimitTrigger = vi.fn()
vi.mock('@/stores/rateLimit', () => ({
  useRateLimitStore: () => ({ trigger: mockRateLimitTrigger }),
}))

describe('BackendClient', () => {
  let mockToast
  let mockGetToken
  let mockOnLogout

  beforeEach(() => {
    vi.clearAllMocks()

    mockToast = {
      success: vi.fn(),
      warning: vi.fn(),
      error: vi.fn(),
      info: vi.fn(),
    }
    mockGetToken = vi.fn()
    mockOnLogout = vi.fn()
  })

  describe('Constructor', () => {
    it('creates an axios instance with default timeout', () => {
      const client = new BackendClient({
        toast: mockToast,
        getToken: mockGetToken,
        onLogout: mockOnLogout,
      })

      expect(client.http).toBeDefined()
      expect(client.http.defaults.timeout).toBe(5000)
    })

    it('uses custom timeout when provided', () => {
      const client = new BackendClient({
        toast: mockToast,
        timeout: 10000,
      })

      expect(client.http.defaults.timeout).toBe(10000)
    })

    it('uses custom baseURL when provided', () => {
      const client = new BackendClient({
        baseURL: 'https://custom-api.example.com',
        toast: mockToast,
      })

      expect(client.http.defaults.baseURL).toBe(
        'https://custom-api.example.com',
      )
    })

    it('instantiates all services', () => {
      const client = new BackendClient({
        toast: mockToast,
        getToken: mockGetToken,
        onLogout: mockOnLogout,
      })

      expect(client.activities).toBeDefined()
      expect(client.applications).toBeDefined()
      expect(client.auth).toBeDefined()
      expect(client.changelog).toBeDefined()
      expect(client.connections).toBeDefined()
      expect(client.courses).toBeDefined()
      expect(client.events).toBeDefined()
      expect(client.guacamole).toBeDefined()
      expect(client.languages).toBeDefined()
      expect(client.mailActions).toBeDefined()
      expect(client.mails).toBeDefined()
      expect(client.mailTemplates).toBeDefined()
      expect(client.objectPermissions).toBeDefined()
      expect(client.os).toBeDefined()
      expect(client.policies).toBeDefined()
      expect(client.proxmox).toBeDefined()
      expect(client.roles).toBeDefined()
      expect(client.scimClients).toBeDefined()
      expect(client.scimProviders).toBeDefined()
      expect(client.statistics).toBeDefined()
      expect(client.system).toBeDefined()
      expect(client.tags).toBeDefined()
      expect(client.tasks).toBeDefined()
      expect(client.templates).toBeDefined()
      expect(client.users).toBeDefined()
      expect(client.vendors).toBeDefined()
      expect(client.vms).toBeDefined()
    })
  })

  describe('Request Interceptor', () => {
    it('adds Authorization header when token is available', async () => {
      mockGetToken.mockReturnValue('test-jwt-token')

      const client = new BackendClient({
        baseURL: 'https://api.example.com',
        toast: mockToast,
        getToken: mockGetToken,
      })

      // Intercept the request config
      const requestInterceptor = client.http.interceptors.request.handlers[0]
      const config = { headers: {} }
      const result = await requestInterceptor.fulfilled(config)

      expect(result.headers.Authorization).toBe('Bearer test-jwt-token')
    })

    it('does not add Authorization header when no token', async () => {
      mockGetToken.mockReturnValue(null)

      const client = new BackendClient({
        baseURL: 'https://api.example.com',
        toast: mockToast,
        getToken: mockGetToken,
      })

      const requestInterceptor = client.http.interceptors.request.handlers[0]
      const config = { headers: {} }
      const result = await requestInterceptor.fulfilled(config)

      expect(result.headers.Authorization).toBeUndefined()
    })

    it('does not add Authorization header when getToken is not provided', async () => {
      const client = new BackendClient({
        baseURL: 'https://api.example.com',
        toast: mockToast,
      })

      const requestInterceptor = client.http.interceptors.request.handlers[0]
      const config = { headers: {} }
      const result = await requestInterceptor.fulfilled(config)

      expect(result.headers.Authorization).toBeUndefined()
    })
  })

  describe('notify', () => {
    it('calls toast method with message', () => {
      const client = new BackendClient({
        toast: mockToast,
      })

      client.notify('success', 'Test message')
      expect(mockToast.success).toHaveBeenCalledWith('Test message')

      client.notify('warning', 'Warning message')
      expect(mockToast.warning).toHaveBeenCalledWith('Warning message')

      client.notify('error', 'Error message')
      expect(mockToast.error).toHaveBeenCalledWith('Error message')

      client.notify('info', 'Info message')
      expect(mockToast.info).toHaveBeenCalledWith('Info message')
    })

    it('does nothing when toast is not provided', () => {
      const client = new BackendClient({})

      // Should not throw
      expect(() => client.notify('success', 'Test')).not.toThrow()
    })

    it('suppresses toasts while silent', () => {
      const client = new BackendClient({ toast: mockToast })

      client.beginSilent()
      client.notify('error', 'Suppressed')
      expect(mockToast.error).not.toHaveBeenCalled()

      client.endSilent()
      client.notify('error', 'Visible')
      expect(mockToast.error).toHaveBeenCalledWith('Visible')
    })

    it('supports nested beginSilent/endSilent', () => {
      const client = new BackendClient({ toast: mockToast })

      client.beginSilent()
      client.beginSilent()
      client.endSilent()
      client.notify('error', 'Still suppressed')
      expect(mockToast.error).not.toHaveBeenCalled()

      client.endSilent()
      client.notify('error', 'Now visible')
      expect(mockToast.error).toHaveBeenCalledWith('Now visible')
    })

    it('endSilent does not go below zero', () => {
      const client = new BackendClient({ toast: mockToast })

      client.endSilent()
      client.endSilent()
      client.notify('info', 'Works fine')
      expect(mockToast.info).toHaveBeenCalledWith('Works fine')
    })
  })

  describe('handleError', () => {
    it('handles network errors', async () => {
      const client = new BackendClient({
        toast: mockToast,
        onLogout: mockOnLogout,
      })

      const error = { code: 'ERR_NETWORK' }

      await expect(client.handleError(error)).rejects.toBe(error)
      expect(mockToast.warning).toHaveBeenCalledWith(
        'Verbindung fehlgeschlagen - Server nicht erreichbar',
      )
    })

    it('handles 401 with credentials error - triggers logout', async () => {
      const client = new BackendClient({
        toast: mockToast,
        onLogout: mockOnLogout,
      })

      const error = {
        response: {
          status: 401,
          data: { error_code: 'CREDENTIALS_NOT_VALID' },
        },
      }

      await expect(client.handleError(error)).rejects.toBe(error)
      expect(mockToast.warning).toHaveBeenCalledWith(
        'Sitzung abgelaufen - Bitte erneut anmelden',
      )
      expect(mockOnLogout).toHaveBeenCalled()
    })

    it('handles 401 with token expired error - triggers logout', async () => {
      const client = new BackendClient({
        toast: mockToast,
        onLogout: mockOnLogout,
      })

      const error = {
        response: {
          status: 401,
          data: { error_code: 'INVALID_AUTH_TOKEN' },
        },
      }

      await expect(client.handleError(error)).rejects.toBe(error)
      expect(mockOnLogout).toHaveBeenCalled()
    })

    it('handles 400 inactive user - triggers logout', async () => {
      const client = new BackendClient({
        toast: mockToast,
        onLogout: mockOnLogout,
      })

      const error = {
        response: {
          status: 400,
          data: { error_code: 'USER_NOT_ACTIVE' },
        },
      }

      await expect(client.handleError(error)).rejects.toBe(error)
      expect(mockToast.warning).toHaveBeenCalledWith('Account nicht aktiv')
      expect(mockOnLogout).toHaveBeenCalled()
    })

    it('handles INCORRECT_CREDENTIALS silently without toast', async () => {
      const client = new BackendClient({
        toast: mockToast,
        onLogout: mockOnLogout,
      })

      const error = {
        response: {
          status: 401,
          data: {
            error_code: 'INCORRECT_CREDENTIALS',
            detail: 'Incorrect username or password',
          },
        },
      }

      await expect(client.handleError(error)).rejects.toBe(error)
      expect(mockToast.error).not.toHaveBeenCalled()
      expect(mockToast.warning).not.toHaveBeenCalled()
      expect(mockOnLogout).not.toHaveBeenCalled()
    })

    it('handles 403 silently without toast', async () => {
      const client = new BackendClient({
        toast: mockToast,
        onLogout: mockOnLogout,
      })

      const error = {
        response: {
          status: 403,
          data: { detail: 'Forbidden' },
        },
      }

      await expect(client.handleError(error)).rejects.toBe(error)
      expect(mockToast.error).not.toHaveBeenCalled()
      expect(mockToast.warning).not.toHaveBeenCalled()
    })

    it('handles 404 silently without toast', async () => {
      const client = new BackendClient({
        toast: mockToast,
        onLogout: mockOnLogout,
      })

      const error = {
        response: {
          status: 404,
          data: { detail: 'Not found' },
        },
      }

      await expect(client.handleError(error)).rejects.toBe(error)
      expect(mockToast.error).not.toHaveBeenCalled()
    })

    it('handles 429 rate limit - calls store trigger with parsed headers', async () => {
      mockRateLimitTrigger.mockReturnValue({
        mode: 'modal',
        messageKey: 'views.rateLimit.endpoints.auth',
        seconds: 389,
        shouldShowToast: false,
      })
      const client = new BackendClient({
        toast: mockToast,
        onLogout: mockOnLogout,
      })

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
      expect(mockRateLimitTrigger).toHaveBeenCalledWith({
        retryAfter: 389,
        resetAt: 1777580100,
        limit: 10,
        endpoint: '/auth/login',
      })
      expect(mockToast.warning).not.toHaveBeenCalled()
      expect(mockToast.error).not.toHaveBeenCalled()
    })

    it('handles 429 rate limit - shows warning toast for short windows', async () => {
      mockRateLimitTrigger.mockReturnValue({
        mode: 'toast',
        messageKey: 'views.rateLimit.endpoints.auth',
        seconds: 5,
        shouldShowToast: true,
      })
      const client = new BackendClient({
        toast: mockToast,
        onLogout: mockOnLogout,
      })

      const error = {
        config: { url: '/auth/login' },
        response: {
          status: 429,
          headers: { 'retry-after': '5' },
          data: { error_code: 'RATE_LIMIT_EXCEEDED' },
        },
      }

      await expect(client.handleError(error)).rejects.toBe(error)
      expect(mockToast.warning).toHaveBeenCalledTimes(1)
      expect(mockToast.error).not.toHaveBeenCalled()
    })

    it('handles 422 validation error with array detail', async () => {
      const client = new BackendClient({
        toast: mockToast,
        onLogout: mockOnLogout,
      })

      const error = {
        response: {
          status: 422,
          data: {
            detail: [{ msg: 'Field is required', loc: ['body', 'name'] }],
          },
        },
      }

      await expect(client.handleError(error)).rejects.toBe(error)
      expect(mockToast.error).toHaveBeenCalledWith('Field is required')
    })

    it('handles 422 validation error with string detail', async () => {
      const client = new BackendClient({
        toast: mockToast,
        onLogout: mockOnLogout,
      })

      const error = {
        response: {
          status: 422,
          data: { detail: 'Invalid input' },
        },
      }

      await expect(client.handleError(error)).rejects.toBe(error)
      expect(mockToast.error).toHaveBeenCalledWith('Invalid input')
    })

    it('handles general 500 error with detail', async () => {
      const client = new BackendClient({
        toast: mockToast,
        onLogout: mockOnLogout,
      })

      const error = {
        response: {
          status: 500,
          data: { detail: 'Internal server error' },
        },
      }

      await expect(client.handleError(error)).rejects.toBe(error)
      expect(mockToast.error).toHaveBeenCalledWith('Internal server error')
    })

    it('handles general error with message fallback', async () => {
      const client = new BackendClient({
        toast: mockToast,
        onLogout: mockOnLogout,
      })

      const error = {
        response: {
          status: 500,
          data: { message: 'Server error message' },
        },
      }

      await expect(client.handleError(error)).rejects.toBe(error)
      expect(mockToast.error).toHaveBeenCalledWith('Server error message')
    })

    it('handles general error with default message', async () => {
      const client = new BackendClient({
        toast: mockToast,
        onLogout: mockOnLogout,
      })

      const error = {
        response: {
          status: 500,
          data: {},
        },
      }

      await expect(client.handleError(error)).rejects.toBe(error)
      expect(mockToast.error).toHaveBeenCalledWith(
        'Ein Fehler ist aufgetreten.',
      )
    })
  })
})
