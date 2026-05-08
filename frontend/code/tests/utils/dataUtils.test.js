import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

// Mock stores before importing dataUtils
vi.mock('@/stores/lookup', () => ({
  useLookupStore: () => ({
    resolve: vi.fn((keyspace, id) => Promise.resolve(`Resolved: ${id}`)),
    resolveMany: vi.fn((keyspace, ids) =>
      Promise.resolve(ids.map((id) => (id ? `Resolved: ${id}` : null))),
    ),
  }),
}))

vi.mock('@/stores/main', () => ({
  useMainStore: () => ({
    user: { id: 'test-user' },
  }),
}))

vi.mock('@/utils/icons', () => ({
  connectionProtocolFormatterIcon: vi.fn(),
  eventStatusIcon: vi.fn(),
  methodHTTPIcon: vi.fn(),
  protectionObjectIcon: vi.fn(),
  responseCodeHTTPIcon: vi.fn(),
  systemSettingVisibilityIcon: vi.fn(),
  taskStatusIcon: vi.fn(),
  templateStatusIcon: vi.fn(),
  userAuthBackendIcon: vi.fn(),
  userStatusIcon: vi.fn(),
  vmStatusIcon: vi.fn(),
}))

vi.mock('@/utils/objectModelPermissions', () => ({
  getObjectPermissionsOptions: vi.fn(() => [
    { value: 'read', label: 'Lesen' },
    { value: 'write', label: 'Schreiben' },
  ]),
}))

vi.mock('@/utils/httpStatusCodes', () => ({
  httpStatusCodes: {
    200: { message: 'OK' },
    404: { message: 'Not Found' },
  },
}))

import {
  formatDate,
  formatObjectPermissionsKey,
  parseEmailContent,
  resolveFieldFromLookup,
} from '@/utils/dataUtils'

describe('dataUtils', () => {
  describe('formatDate', () => {
    beforeEach(() => {
      // Mock Date for consistent testing
      vi.useFakeTimers()
      vi.setSystemTime(new Date('2024-06-15T12:00:00Z'))
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('returns empty string for null input', () => {
      expect(formatDate(null)).toBe('')
    })

    it('returns empty string for undefined input', () => {
      expect(formatDate(undefined)).toBe('')
    })

    it('returns empty string for empty string input', () => {
      expect(formatDate('')).toBe('')
    })

    it('formats ISO date string without timezone', () => {
      const result = formatDate('2024-01-15T10:30:00')
      expect(result).toContain('2024')
      expect(result).toContain('01')
      expect(result).toContain('15')
    })

    it('formats ISO date string with timezone', () => {
      const result = formatDate('2024-01-15T10:30:00+02:00')
      expect(result).toContain('2024')
    })

    it('returns original string for invalid date', () => {
      expect(formatDate('not-a-date')).toBe('not-a-date')
    })

    it('handles date with custom options', () => {
      const result = formatDate('2024-01-15T10:30:00', {
        year: 'numeric',
        month: 'long',
      })
      expect(result).toBeTruthy()
    })

    describe('Relative Dates', () => {
      it('shows relative label for recent past', () => {
        vi.setSystemTime(new Date('2024-06-15T12:00:30Z'))
        const result = formatDate('2024-06-15T12:00:00Z', { relative: true })
        expect(result).toBe('Vor wenigen Sekunden')
      })

      it('shows relative label for minutes ago', () => {
        vi.setSystemTime(new Date('2024-06-15T12:30:00Z'))
        const result = formatDate('2024-06-15T12:00:00Z', { relative: true })
        expect(result).toContain('Minuten')
      })

      it('shows relative label for hours ago', () => {
        vi.setSystemTime(new Date('2024-06-15T15:00:00Z'))
        const result = formatDate('2024-06-15T12:00:00Z', { relative: true })
        expect(result).toContain('Stunden')
      })

      it('shows relative label for yesterday', () => {
        vi.setSystemTime(new Date('2024-06-16T12:00:00Z'))
        const result = formatDate('2024-06-15T12:00:00Z', { relative: true })
        expect(result).toBe('Vor einem Tag')
      })

      it('shows relative label for multiple days ago', () => {
        vi.setSystemTime(new Date('2024-06-20T12:00:00Z'))
        const result = formatDate('2024-06-15T12:00:00Z', { relative: true })
        expect(result).toContain('Tagen')
      })

      it('shows relative label for near future', () => {
        vi.setSystemTime(new Date('2024-06-15T11:59:45Z'))
        const result = formatDate('2024-06-15T12:00:00Z', { relative: true })
        expect(result).toBe('In wenigen Sekunden')
      })

      it('shows relative label for minutes in future', () => {
        vi.setSystemTime(new Date('2024-06-15T11:30:00Z'))
        const result = formatDate('2024-06-15T12:00:00Z', { relative: true })
        expect(result).toContain('In')
        expect(result).toContain('Minuten')
      })

      it('shows relative label for tomorrow', () => {
        vi.setSystemTime(new Date('2024-06-14T12:00:00Z'))
        const result = formatDate('2024-06-15T12:00:00Z', { relative: true })
        expect(result).toBe('Morgen')
      })

      it('shows relative label for multiple days in future', () => {
        vi.setSystemTime(new Date('2024-06-10T12:00:00Z'))
        const result = formatDate('2024-06-15T12:00:00Z', { relative: true })
        expect(result).toContain('In')
        expect(result).toContain('Tagen')
      })
    })
  })

  describe('resolveFieldFromLookup', () => {
    it('resolves single field for single object', async () => {
      const obj = { userId: 'user-123' }
      await resolveFieldFromLookup(obj, [
        { from: 'userId', to: 'username', keyspace: 'users' },
      ])
      expect(obj.username).toBe('Resolved: user-123')
    })

    it('resolves single field for array of objects', async () => {
      const objects = [{ userId: 'user-1' }, { userId: 'user-2' }]
      await resolveFieldFromLookup(objects, [
        { from: 'userId', to: 'username', keyspace: 'users' },
      ])
      expect(objects[0].username).toBe('Resolved: user-1')
      expect(objects[1].username).toBe('Resolved: user-2')
    })

    it('resolves multiple fields', async () => {
      const obj = { userId: 'user-123', roleId: 'role-456' }
      await resolveFieldFromLookup(obj, [
        { from: 'userId', to: 'username', keyspace: 'users' },
        { from: 'roleId', to: 'roleName', keyspace: 'roles' },
      ])
      expect(obj.username).toBe('Resolved: user-123')
      expect(obj.roleName).toBe('Resolved: role-456')
    })

    it('handles null values gracefully', async () => {
      const obj = { userId: null }
      await resolveFieldFromLookup(obj, [
        { from: 'userId', to: 'username', keyspace: 'users' },
      ])
      expect(obj.username).toBeNull()
    })

    it('applies formatter function when provided', async () => {
      const obj = { userId: 'user-123' }
      await resolveFieldFromLookup(obj, [
        {
          from: 'userId',
          to: 'username',
          keyspace: 'users',
          formatter: (o) => ({ formattedName: `Name: ${o.username}` }),
        },
      ])
      expect(obj.formattedName).toBe('Name: Resolved: user-123')
    })

    it('handles formatter errors gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      const obj = { userId: 'user-123' }

      await resolveFieldFromLookup(obj, [
        {
          from: 'userId',
          to: 'username',
          keyspace: 'users',
          formatter: () => {
            throw new Error('Formatter error')
          },
        },
      ])

      expect(consoleSpy).toHaveBeenCalled()
      consoleSpy.mockRestore()
    })
  })

  describe('parseEmailContent', () => {
    it('returns fallback for null input', () => {
      expect(parseEmailContent(null)).toBe('<p><i>Kein Inhalt</i></p>')
    })

    it('returns fallback for empty string', () => {
      expect(parseEmailContent('')).toBe('<p><i>Kein Inhalt</i></p>')
    })

    it('returns raw string when no boundary is found', () => {
      const raw = '<p>Simple HTML without MIME</p>'
      expect(parseEmailContent(raw)).toBe(raw)
    })

    it('extracts HTML content from multipart email', () => {
      const raw = [
        'Content-Type: multipart/alternative; boundary="abc123"',
        '',
        '--abc123',
        'Content-Type: text/html; charset=utf-8',
        '',
        '<p>Hello World</p>',
        '--abc123--',
      ].join('\r\n')

      expect(parseEmailContent(raw)).toBe('<p>Hello World</p>')
    })

    it('extracts plain text content with <br> tags', () => {
      const raw = [
        'Content-Type: multipart/alternative; boundary="abc123"',
        '',
        '--abc123',
        'Content-Type: text/plain; charset=utf-8',
        '',
        'Line 1',
        'Line 2',
        '--abc123--',
      ].join('\r\n')

      expect(parseEmailContent(raw)).toBe('Line 1\r<br>Line 2')
    })

    it('decodes base64-encoded HTML content', () => {
      const htmlContent = '<p>Hello World</p>'
      const base64 = btoa(htmlContent)
      const raw = [
        'Content-Type: multipart/alternative; boundary="abc123"',
        '',
        '--abc123',
        'Content-Type: text/html; charset=utf-8',
        'Content-Transfer-Encoding: base64',
        '',
        base64,
        '--abc123--',
      ].join('\r\n')

      expect(parseEmailContent(raw)).toBe(htmlContent)
    })

    it('decodes base64-encoded plain text content', () => {
      const textContent = 'Hello Plain Text'
      const base64 = btoa(textContent)
      const raw = [
        'Content-Type: multipart/alternative; boundary="abc123"',
        '',
        '--abc123',
        'Content-Type: text/plain; charset=utf-8',
        'Content-Transfer-Encoding: base64',
        '',
        base64,
        '--abc123--',
      ].join('\r\n')

      expect(parseEmailContent(raw)).toBe(textContent)
    })

    it('decodes base64 content with UTF-8 characters', () => {
      const htmlContent =
        '<p>Sch\u00f6ne Gr\u00fc\u00dfe \u00fc\u00e4\u00f6</p>'
      // Encode UTF-8 string to base64
      const base64 = btoa(
        String.fromCharCode(...new TextEncoder().encode(htmlContent)),
      )
      const raw = [
        'Content-Type: multipart/alternative; boundary="abc123"',
        '',
        '--abc123',
        'Content-Type: text/html; charset=utf-8',
        'Content-Transfer-Encoding: base64',
        '',
        base64,
        '--abc123--',
      ].join('\r\n')

      expect(parseEmailContent(raw)).toBe(htmlContent)
    })

    it('handles base64 with line breaks in encoded data', () => {
      const htmlContent = '<p>Hello World</p>'
      const base64 = btoa(htmlContent)
      // Split base64 into multiple lines (as real emails do)
      const wrappedBase64 = base64.match(/.{1,10}/g).join('\r\n')
      const raw = [
        'Content-Type: multipart/alternative; boundary="abc123"',
        '',
        '--abc123',
        'Content-Type: text/html; charset=utf-8',
        'Content-Transfer-Encoding: base64',
        '',
        wrappedBase64,
        '--abc123--',
      ].join('\r\n')

      expect(parseEmailContent(raw)).toBe(htmlContent)
    })

    it('falls back to raw body when base64 decoding fails', () => {
      const raw = [
        'Content-Type: multipart/alternative; boundary="abc123"',
        '',
        '--abc123',
        'Content-Type: text/html; charset=utf-8',
        'Content-Transfer-Encoding: base64',
        '',
        '!!!not-valid-base64!!!',
        '--abc123--',
      ].join('\r\n')

      expect(parseEmailContent(raw)).toBe('!!!not-valid-base64!!!')
    })

    it('returns fallback when no text part is found', () => {
      const raw = [
        'Content-Type: multipart/alternative; boundary="abc123"',
        '',
        '--abc123',
        'Content-Type: image/png',
        '',
        'binarydata',
        '--abc123--',
      ].join('\r\n')

      expect(parseEmailContent(raw)).toBe(
        '<p><i>Kein gültiger Inhalt gefunden</i></p>',
      )
    })
  })

  describe('formatObjectPermissionsKey', () => {
    it('formats known permission key to label', () => {
      const permission = { permission_key: 'read', object_type: 'users' }
      const result = formatObjectPermissionsKey(permission)
      expect(result.permission).toBe('Lesen')
    })

    it('keeps original key for unknown permission', () => {
      const permission = {
        permission_key: 'unknown_permission',
        object_type: 'users',
      }
      const result = formatObjectPermissionsKey(permission)
      expect(result.permission).toBe('unknown_permission')
    })

    it('handles null object_type', () => {
      const permission = { permission_key: 'read', object_type: null }
      const result = formatObjectPermissionsKey(permission)
      expect(result.permission).toBeDefined()
    })

    it('returns the same object reference', () => {
      const permission = { permission_key: 'read', object_type: 'users' }
      const result = formatObjectPermissionsKey(permission)
      expect(result).toBe(permission)
    })
  })
})
