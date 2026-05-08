import { vi } from 'vitest'

export default {
  // ============================================================
  // Authentication Methods
  // ============================================================
  login: vi.fn().mockResolvedValue({
    user: {
      id: '9ff629d7-327b-4a05-8a4a-28f0b97af923',
      name: 'test563',
      email: 'test563@example.de',
      roles: [{ key: 'studierende', name: 'Studierende' }],
    },
    token: 'mocked-jwt-token',
  }),

  signUp: vi.fn().mockResolvedValue({
    data: {
      message: 'User successfully signed up',
    },
  }),

  passwordResetRequest: vi.fn().mockResolvedValue({
    data: {
      message: 'Password reset request successful',
    },
  }),

  passwordResetTokenCheck: vi.fn().mockResolvedValue({
    data: {
      valid: true,
    },
  }),

  passwordResetProcess: vi.fn().mockResolvedValue({
    data: {
      message: 'Password reset successful',
    },
  }),

  reauth: vi.fn().mockResolvedValue({
    data: {
      access_token: 'new-fake-jwt-token',
      token_type: 'Bearer',
    },
  }),

  // ============================================================
  // Navigation Guards
  // ============================================================
  requireAuth: vi.fn((to, from, next) => next()),
  requirePolicyAgree: vi.fn((to, from, next) => next()),
  requireLogout: vi.fn((to, from, next) => next()),
  loginOIDC: vi.fn((to, from, next) => next()),
}
