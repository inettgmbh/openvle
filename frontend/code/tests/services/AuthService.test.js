import { beforeEach, describe, expect, it, vi } from 'vitest'

// Unmock the service under test (global mock is in setupMocks.js)
vi.unmock('@/services/AuthService.js')

import AuthService from '@/services/AuthService'

// Mock the store and toast imports
vi.mock('@/stores/main.js', () => ({
  useMainStore: vi.fn(() => ({
    isLoggedIn: false,
    getUser: null,
    getOutStandingPolicies: null,
    userCan: vi.fn().mockResolvedValue(true),
    logout: vi.fn(),
    login: vi.fn(),
  })),
}))

vi.mock('vue-toastification', () => ({
  useToast: vi.fn(() => ({
    success: vi.fn(),
    warning: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  })),
}))

describe('AuthService', () => {
  let service
  let mockHttp

  beforeEach(() => {
    vi.clearAllMocks()

    mockHttp = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    }
    service = new AuthService(mockHttp)
  })

  describe('Constructor', () => {
    it('sets http instance', () => {
      expect(service.http).toBe(mockHttp)
    })

    it('binds navigation guard methods', () => {
      // Verify that methods are bound (they should work when called directly)
      expect(typeof service.requireAuth).toBe('function')
      expect(typeof service.requireLogout).toBe('function')
      expect(typeof service.requirePolicyAgree).toBe('function')
      expect(typeof service.loginOIDC).toBe('function')
    })
  })

  describe('Lazy-loaded Properties', () => {
    it('mainStore getter returns store instance', () => {
      const store = service.mainStore
      expect(store).toBeDefined()
      expect(store.isLoggedIn).toBe(false)
    })

    it('mainStore caches the instance', () => {
      const store1 = service.mainStore
      const store2 = service.mainStore
      expect(store1).toBe(store2)
    })

    it('toast getter returns toast instance', () => {
      const toast = service.toast
      expect(toast).toBeDefined()
      expect(typeof toast.error).toBe('function')
    })

    it('toast caches the instance', () => {
      const toast1 = service.toast
      const toast2 = service.toast
      expect(toast1).toBe(toast2)
    })
  })

  describe('Authentication Methods', () => {
    describe('login', () => {
      it('sends login request with form-encoded content type', async () => {
        const credentials = { username: 'test', password: 'secret' }
        const response = { data: { token: 'jwt-token' } }
        mockHttp.post.mockResolvedValue(response)

        const result = await service.login(credentials)

        expect(mockHttp.post).toHaveBeenCalledWith('/auth/login', credentials, {
          headers: { 'content-type': 'application/x-www-form-urlencoded' },
        })
        expect(result).toEqual(response)
      })
    })

    describe('signUp', () => {
      it('sends signup request', async () => {
        const credentials = {
          username: 'newuser',
          email: 'new@example.com',
          password: 'secret',
        }
        const response = { data: { message: 'Success' } }
        mockHttp.post.mockResolvedValue(response)

        const result = await service.signUp(credentials)

        expect(mockHttp.post).toHaveBeenCalledWith('/auth/sign-up', credentials)
        expect(result).toEqual(response)
      })
    })

    describe('passwordResetRequest', () => {
      it('sends password reset request', async () => {
        const credentials = { email: 'user@example.com' }
        const response = { data: { message: 'Email sent' } }
        mockHttp.post.mockResolvedValue(response)

        const result = await service.passwordResetRequest(credentials)

        expect(mockHttp.post).toHaveBeenCalledWith(
          '/auth/password-reset',
          credentials,
        )
        expect(result).toEqual(response)
      })
    })

    describe('passwordResetTokenCheck', () => {
      it('validates reset token', async () => {
        const token = 'reset-token-123'
        const response = { data: { valid: true } }
        mockHttp.post.mockResolvedValue(response)

        const result = await service.passwordResetTokenCheck(token)

        expect(mockHttp.post).toHaveBeenCalledWith(
          '/auth/password-reset-token/',
          token,
        )
        expect(result).toEqual(response)
      })
    })

    describe('passwordResetProcess', () => {
      it('completes password reset', async () => {
        const token = 'reset-token-123'
        const credentials = { password: 'newpass', password_repeat: 'newpass' }
        const response = { data: { message: 'Password updated' } }
        mockHttp.post.mockResolvedValue(response)

        const result = await service.passwordResetProcess(token, credentials)

        expect(mockHttp.post).toHaveBeenCalledWith(
          '/auth/password-reset/reset-token-123',
          credentials,
        )
        expect(result).toEqual(response)
      })
    })

    describe('reauth', () => {
      it('sends reauthentication request', async () => {
        const response = { data: { token: 'new-token' } }
        mockHttp.post.mockResolvedValue(response)

        const result = await service.reauth()

        expect(mockHttp.post).toHaveBeenCalledWith('/auth/reauthenticate')
        expect(result).toEqual(response)
      })
    })
  })

  describe('Navigation Guards', () => {
    let mockNext
    let mockTo
    let mockFrom

    beforeEach(() => {
      mockNext = vi.fn()
      mockTo = { fullPath: '/dashboard', meta: {}, params: {} }
      mockFrom = { fullPath: '/previous' }
    })

    describe('requireAuth', () => {
      it('redirects to login when not logged in', async () => {
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          isLoggedIn: false,
          getUser: null,
          getOutStandingPolicies: null,
        })

        // Create new service instance to get fresh store mock
        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null // Reset cached store

        await freshService.requireAuth(mockTo, mockFrom, mockNext)

        expect(mockNext).toHaveBeenCalledWith({
          path: '/auth/login',
          query: { redirect: '/dashboard' },
        })
      })

      it('redirects to policy page when outstanding policies', async () => {
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          isLoggedIn: true,
          getUser: { id: '123' },
          getOutStandingPolicies: 'policy-uuid-123',
        })

        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null

        await freshService.requireAuth(mockTo, mockFrom, mockNext)

        expect(mockNext).toHaveBeenCalledWith({
          path: '/policy/policy-uuid-123',
        })
      })

      it('allows access when noAuth meta is true', async () => {
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          isLoggedIn: true,
          getUser: { id: '123' },
          getOutStandingPolicies: null,
        })

        mockTo.meta.noAuth = true
        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null

        await freshService.requireAuth(mockTo, mockFrom, mockNext)

        expect(mockNext).toHaveBeenCalledWith()
      })

      it('checks permissions when required', async () => {
        const mockUserCan = vi.fn().mockResolvedValue(true)
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          isLoggedIn: true,
          getUser: { id: '123' },
          getOutStandingPolicies: null,
          userCan: mockUserCan,
        })

        mockTo.meta = { type: 'users', permission: 'read' }
        mockTo.params = { id: 'user-456' }

        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null

        await freshService.requireAuth(mockTo, mockFrom, mockNext)

        expect(mockUserCan).toHaveBeenCalledWith('users', 'read', '/user-456')
        expect(mockNext).toHaveBeenCalledWith()
      })

      it('denies access when permission check fails', async () => {
        const mockUserCan = vi.fn().mockResolvedValue(false)
        const mockToastError = vi.fn()
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          isLoggedIn: true,
          getUser: { id: '123' },
          getOutStandingPolicies: null,
          userCan: mockUserCan,
        })

        const { useToast } = await import('vue-toastification')
        useToast.mockReturnValue({ error: mockToastError })

        mockTo.meta = { type: 'users', permission: 'delete' }

        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null
        freshService._toast = null

        await freshService.requireAuth(mockTo, mockFrom, mockNext)

        expect(mockToastError).toHaveBeenCalledWith(
          'Du hast keine Berechtigung dies zu tun',
        )
        expect(mockNext).toHaveBeenCalledWith('/previous')
      })

      it('redirects to home when permission fails and coming from auth page', async () => {
        const mockUserCan = vi.fn().mockResolvedValue(false)
        const mockToastError = vi.fn()
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          isLoggedIn: true,
          getUser: { id: '123' },
          getOutStandingPolicies: null,
          userCan: mockUserCan,
        })

        const { useToast } = await import('vue-toastification')
        useToast.mockReturnValue({ error: mockToastError })

        mockTo.meta = { type: 'users', permission: 'delete' }
        mockFrom.fullPath = '/auth/login'

        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null
        freshService._toast = null

        await freshService.requireAuth(mockTo, mockFrom, mockNext)

        expect(mockNext).toHaveBeenCalledWith('/')
      })

      it('redirects to home when permission fails and from path is empty', async () => {
        const mockUserCan = vi.fn().mockResolvedValue(false)
        const mockToastError = vi.fn()
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          isLoggedIn: true,
          getUser: { id: '123' },
          getOutStandingPolicies: null,
          userCan: mockUserCan,
        })

        const { useToast } = await import('vue-toastification')
        useToast.mockReturnValue({ error: mockToastError })

        mockTo.meta = { type: 'users', permission: 'delete' }
        mockFrom.fullPath = ''

        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null
        freshService._toast = null

        await freshService.requireAuth(mockTo, mockFrom, mockNext)

        expect(mockNext).toHaveBeenCalledWith('/')
      })
    })

    describe('requireAuth - requiredSetting', () => {
      it('allows access when required setting is enabled', async () => {
        const mockUserCan = vi.fn().mockResolvedValue(true)
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          isLoggedIn: true,
          getUser: { id: '123' },
          getOutStandingPolicies: null,
          userCan: mockUserCan,
          settingsStatus: 'loaded',
          settings: {
            features: {
              scope: {
                example: true,
              },
            },
          },
        })

        mockTo.meta = {
          requiredSetting: 'features.scope.example',
          type: 'users',
          permission: 'read',
        }

        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null

        await freshService.requireAuth(mockTo, mockFrom, mockNext)

        expect(mockNext).toHaveBeenCalledWith()
      })

      it('denies access when required setting is disabled', async () => {
        const mockToastError = vi.fn()
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          isLoggedIn: true,
          getUser: { id: '123' },
          getOutStandingPolicies: null,
          settingsStatus: 'loaded',
          settings: {
            features: {
              scope: {
                example: false,
              },
            },
          },
        })

        const { useToast } = await import('vue-toastification')
        useToast.mockReturnValue({ error: mockToastError })

        mockTo.meta = { requiredSetting: 'features.scope.example' }

        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null
        freshService._toast = null

        await freshService.requireAuth(mockTo, mockFrom, mockNext)

        expect(mockToastError).toHaveBeenCalledWith(
          'Diese Funktion ist nicht verfügbar',
        )
        expect(mockNext).toHaveBeenCalledWith('/previous')
      })

      it('denies access when required setting path does not exist', async () => {
        const mockToastError = vi.fn()
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          isLoggedIn: true,
          getUser: { id: '123' },
          getOutStandingPolicies: null,
          settingsStatus: 'loaded',
          settings: {
            features: {},
          },
        })

        const { useToast } = await import('vue-toastification')
        useToast.mockReturnValue({ error: mockToastError })

        mockTo.meta = { requiredSetting: 'features.nonexistent.setting' }

        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null
        freshService._toast = null

        await freshService.requireAuth(mockTo, mockFrom, mockNext)

        expect(mockToastError).toHaveBeenCalledWith(
          'Diese Funktion ist nicht verfügbar',
        )
        expect(mockNext).toHaveBeenCalledWith('/previous')
      })

      it('redirects to home when setting disabled and coming from auth page', async () => {
        const mockToastError = vi.fn()
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          isLoggedIn: true,
          getUser: { id: '123' },
          getOutStandingPolicies: null,
          settingsStatus: 'loaded',
          settings: {
            features: {
              scope: {
                example: false,
              },
            },
          },
        })

        const { useToast } = await import('vue-toastification')
        useToast.mockReturnValue({ error: mockToastError })

        mockTo.meta = { requiredSetting: 'features.scope.example' }
        mockFrom.fullPath = '/auth/login'

        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null
        freshService._toast = null

        await freshService.requireAuth(mockTo, mockFrom, mockNext)

        expect(mockNext).toHaveBeenCalledWith('/')
      })

      it('redirects to home when setting disabled and from path is empty', async () => {
        const mockToastError = vi.fn()
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          isLoggedIn: true,
          getUser: { id: '123' },
          getOutStandingPolicies: null,
          settingsStatus: 'loaded',
          settings: {
            features: {
              scope: {
                example: false,
              },
            },
          },
        })

        const { useToast } = await import('vue-toastification')
        useToast.mockReturnValue({ error: mockToastError })

        mockTo.meta = { requiredSetting: 'features.scope.example' }
        mockFrom.fullPath = ''

        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null
        freshService._toast = null

        await freshService.requireAuth(mockTo, mockFrom, mockNext)

        expect(mockNext).toHaveBeenCalledWith('/')
      })

      it('redirects to home when setting disabled and coming from any auth route', async () => {
        const mockToastError = vi.fn()
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          isLoggedIn: true,
          getUser: { id: '123' },
          getOutStandingPolicies: null,
          settingsStatus: 'loaded',
          settings: {
            features: {
              scope: {
                example: false,
              },
            },
          },
        })

        const { useToast } = await import('vue-toastification')
        useToast.mockReturnValue({ error: mockToastError })

        mockTo.meta = { requiredSetting: 'features.scope.example' }
        mockFrom.fullPath = '/auth/sign-up'

        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null
        freshService._toast = null

        await freshService.requireAuth(mockTo, mockFrom, mockNext)

        expect(mockNext).toHaveBeenCalledWith('/')
      })

      it('waits for settings to load before checking', async () => {
        const mockUserCan = vi.fn().mockResolvedValue(true)
        let settingsStatus = 'loading'
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          isLoggedIn: true,
          getUser: { id: '123' },
          getOutStandingPolicies: null,
          userCan: mockUserCan,
          get settingsStatus() {
            return settingsStatus
          },
          settings: {
            features: {
              scope: {
                example: true,
              },
            },
          },
        })

        mockTo.meta = {
          requiredSetting: 'features.scope.example',
          type: 'users',
          permission: 'read',
        }

        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null

        // Simulate settings loading after a short delay
        setTimeout(() => {
          settingsStatus = 'loaded'
        }, 100)

        await freshService.requireAuth(mockTo, mockFrom, mockNext)

        expect(mockNext).toHaveBeenCalledWith()
      })
    })

    describe('requirePolicyAgree', () => {
      it('redirects to home when no outstanding policies', async () => {
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          getOutStandingPolicies: null,
        })

        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null

        await freshService.requirePolicyAgree(mockTo, mockFrom, mockNext)

        expect(mockNext).toHaveBeenCalledWith({ path: '/' })
      })

      it('allows access when policies need agreement', async () => {
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          getOutStandingPolicies: 'policy-123',
        })

        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null

        await freshService.requirePolicyAgree(mockTo, mockFrom, mockNext)

        expect(mockNext).toHaveBeenCalledWith()
      })
    })

    describe('requireLogout', () => {
      it('allows access when not logged in', async () => {
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          isLoggedIn: false,
          getUser: null,
        })

        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null

        await freshService.requireLogout(mockTo, mockFrom, mockNext)

        expect(mockNext).toHaveBeenCalledWith()
      })

      it('redirects when already logged in', async () => {
        const mockToastInfo = vi.fn()
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          isLoggedIn: true,
          getUser: { id: '123' },
        })

        const { useToast } = await import('vue-toastification')
        useToast.mockReturnValue({ info: mockToastInfo })

        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null
        freshService._toast = null

        await freshService.requireLogout(mockTo, mockFrom, mockNext)

        expect(mockToastInfo).toHaveBeenCalledWith('Du bist bereits angemeldet')
        expect(mockNext).toHaveBeenCalledWith('/previous')
      })
    })

    describe('loginOIDC', () => {
      it('redirects when already logged in', async () => {
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          isLoggedIn: true,
          getUser: { id: '123' },
        })

        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null

        await freshService.loginOIDC(mockTo, mockFrom, mockNext)

        expect(mockNext).toHaveBeenCalledWith({
          path: '/previous',
          replace: true,
        })
      })

      it('handles missing token error', async () => {
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          isLoggedIn: false,
          getUser: null,
        })

        mockTo.query = {}
        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null

        await freshService.loginOIDC(mockTo, mockFrom, mockNext)

        expect(mockNext).toHaveBeenCalledWith({
          name: 'login',
          query: { error: 'missing_token' },
        })
      })

      it('handles OIDC error', async () => {
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          isLoggedIn: false,
          getUser: null,
        })

        mockTo.query = { error: 'access_denied' }
        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null

        await freshService.loginOIDC(mockTo, mockFrom, mockNext)

        expect(mockNext).toHaveBeenCalledWith({
          name: 'login',
          query: { error: 'access_denied' },
        })
      })

      it('logs in user with OIDC token', async () => {
        const mockLogin = vi.fn()
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          isLoggedIn: false,
          getUser: null,
          login: mockLogin,
        })

        mockTo.query = {
          access_token: 'oidc-token-123',
          token_type: 'Bearer',
          redirect: '/dashboard',
        }

        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null

        await freshService.loginOIDC(mockTo, mockFrom, mockNext)

        expect(mockLogin).toHaveBeenCalledWith({
          access_token: 'oidc-token-123',
          token_type: 'Bearer',
          outstanding_policies: [],
        })
        expect(mockNext).toHaveBeenCalledWith({
          path: '/dashboard',
          replace: false,
        })
      })

      it('parses outstanding policies from query', async () => {
        const mockLogin = vi.fn()
        const { useMainStore } = await import('@/stores/main.js')
        useMainStore.mockReturnValue({
          isLoggedIn: false,
          getUser: null,
          login: mockLogin,
        })

        mockTo.query = {
          access_token: 'token',
          token_type: 'Bearer',
          outstanding_policies: '12345678-1234-1234-1234-123456789abc',
          redirect: '/',
        }

        const freshService = new AuthService(mockHttp)
        freshService._mainStore = null

        await freshService.loginOIDC(mockTo, mockFrom, mockNext)

        expect(mockLogin).toHaveBeenCalledWith(
          expect.objectContaining({
            outstanding_policies: ['12345678-1234-1234-1234-123456789abc'],
          }),
        )
      })
    })
  })
})
