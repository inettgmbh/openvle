import { describe, expect, it, vi } from 'vitest'

vi.mock('@/i18n', () => ({
  SUPPORTED_LOCALES: ['de', 'en', 'es', 'fr'],
  LOCALE_META: {
    de: { flag: '\uD83C\uDDE9\uD83C\uDDEA', name: 'Deutsch' },
    en: { flag: '\uD83C\uDDEC\uD83C\uDDE7', name: 'English' },
    es: { flag: '\uD83C\uDDEA\uD83C\uDDF8', name: 'Espa\u00F1ol' },
    fr: { flag: '\uD83C\uDDEB\uD83C\uDDF7', name: 'Fran\u00E7ais' },
  },
}))

import {
  DEFAULT_USER_LOCALE,
  getLanguageMenuItems,
  getLocaleLabel,
  getUserLocaleOptions,
} from '@/utils/localeData'

describe('localeData', () => {
  describe('DEFAULT_USER_LOCALE', () => {
    it('is de_DE', () => {
      expect(DEFAULT_USER_LOCALE).toBe('de_DE')
    })
  })

  describe('getUserLocaleOptions', () => {
    const mockT = (key) => {
      const map = {
        'views.users.locale.german': 'Deutsch',
        'views.users.locale.english': 'Englisch',
        'views.users.locale.spanish': 'Spanisch',
        'views.users.locale.french': 'Franz\u00F6sisch',
      }
      return map[key] ?? key
    }

    it('returns an option for each supported locale', () => {
      const options = getUserLocaleOptions(mockT)
      expect(options).toHaveLength(4)
    })

    it('returns options with sequential ids starting at 1', () => {
      const options = getUserLocaleOptions(mockT)
      const ids = options.map((o) => o.id)
      expect(ids).toEqual([1, 2, 3, 4])
    })

    it('maps locale codes to backend format values', () => {
      const options = getUserLocaleOptions(mockT)
      const values = options.map((o) => o.value)
      expect(values).toEqual(['de_DE', 'en_US', 'es_ES', 'fr_FR'])
    })

    it('uses the t function to resolve labels', () => {
      const spy = vi.fn(mockT)
      getUserLocaleOptions(spy)
      expect(spy).toHaveBeenCalledWith('views.users.locale.german')
      expect(spy).toHaveBeenCalledWith('views.users.locale.english')
      expect(spy).toHaveBeenCalledWith('views.users.locale.spanish')
      expect(spy).toHaveBeenCalledWith('views.users.locale.french')
    })

    it('sets translated labels on each option', () => {
      const options = getUserLocaleOptions(mockT)
      expect(options[0].label).toBe('Deutsch')
      expect(options[1].label).toBe('Englisch')
      expect(options[2].label).toBe('Spanisch')
      expect(options[3].label).toBe('Franz\u00F6sisch')
    })

    it('returns options compatible with FormControl (id, label, value)', () => {
      const options = getUserLocaleOptions(mockT)
      for (const option of options) {
        expect(option).toHaveProperty('id')
        expect(option).toHaveProperty('label')
        expect(option).toHaveProperty('value')
        expect(typeof option.id).toBe('number')
        expect(typeof option.label).toBe('string')
        expect(typeof option.value).toBe('string')
      }
    })

    it('includes de_DE as first option', () => {
      const options = getUserLocaleOptions(mockT)
      expect(options[0].value).toBe('de_DE')
    })
  })

  describe('getLocaleLabel', () => {
    it('returns flag and name for known locale', () => {
      expect(getLocaleLabel('de')).toBe('\uD83C\uDDE9\uD83C\uDDEA  Deutsch')
      expect(getLocaleLabel('en')).toBe('\uD83C\uDDEC\uD83C\uDDE7  English')
    })

    it('returns the raw code for unknown locale', () => {
      expect(getLocaleLabel('xx')).toBe('xx')
    })
  })

  describe('getLanguageMenuItems', () => {
    function createMockI18n(activeLocale) {
      return {
        global: {
          locale: { value: activeLocale },
        },
      }
    }

    it('returns an item for each supported locale', () => {
      const items = getLanguageMenuItems(createMockI18n('de'))
      expect(items).toHaveLength(4)
    })

    it('sets isLanguageSwitch to the locale code', () => {
      const items = getLanguageMenuItems(createMockI18n('de'))
      const codes = items.map((i) => i.isLanguageSwitch)
      expect(codes).toEqual(['de', 'en', 'es', 'fr'])
    })

    it('appends checkmark to the active locale label', () => {
      const items = getLanguageMenuItems(createMockI18n('de'))
      const deItem = items.find((i) => i.isLanguageSwitch === 'de')
      expect(deItem.label).toContain('\u2713')
    })

    it('does not append checkmark to inactive locale labels', () => {
      const items = getLanguageMenuItems(createMockI18n('de'))
      const others = items.filter((i) => i.isLanguageSwitch !== 'de')
      for (const item of others) {
        expect(item.label).not.toContain('\u2713')
      }
    })

    it('updates checkmark reactively when locale changes', () => {
      const mockI18n = createMockI18n('de')
      const items = getLanguageMenuItems(mockI18n)

      const enItem = items.find((i) => i.isLanguageSwitch === 'en')
      expect(enItem.label).not.toContain('\u2713')

      mockI18n.global.locale.value = 'en'
      expect(enItem.label).toContain('\u2713')
    })
  })
})
