import { LOCALE_META, SUPPORTED_LOCALES } from '@/i18n'

// Maps short locale codes to backend locale identifiers and i18n label keys
const LOCALE_BACKEND_MAP = {
  de: { value: 'de_DE', labelKey: 'views.users.locale.german' },
  en: { value: 'en_US', labelKey: 'views.users.locale.english' },
  es: { value: 'es_ES', labelKey: 'views.users.locale.spanish' },
  fr: { value: 'fr_FR', labelKey: 'views.users.locale.french' },
}

export const DEFAULT_USER_LOCALE = 'de_DE'

/**
 * Returns FormControl-compatible options for the user locale dropdown.
 *
 * @param {Function} t - The vue-i18n translate function.
 * @returns {Array<Object>} Options with id, label, and value.
 */
export function getUserLocaleOptions(t) {
  return SUPPORTED_LOCALES.filter((code) => code in LOCALE_BACKEND_MAP).map(
    (code, index) => ({
      id: index + 1,
      label: t(LOCALE_BACKEND_MAP[code].labelKey),
      value: LOCALE_BACKEND_MAP[code].value,
    }),
  )
}

/**
 * Returns a formatted label for a locale code (e.g. "🇩🇪  Deutsch").
 *
 * @param {string} code - A supported locale code.
 * @returns {string} The formatted label.
 */
export function getLocaleLabel(code) {
  const meta = LOCALE_META[code]
  return meta ? `${meta.flag}  ${meta.name}` : code
}

/**
 * Returns NavBarItem-compatible menu entries for the language switcher.
 * The active locale gets a trailing checkmark.
 *
 * @param {import('vue-i18n').I18n} i18n - The i18n instance (for reactive locale access).
 * @returns {Array<Object>} Menu items with reactive label getters.
 */
export function getLanguageMenuItems(i18n) {
  return SUPPORTED_LOCALES.map((code) => ({
    get label() {
      const base = getLocaleLabel(code)
      return i18n.global.locale.value === code ? `${base}  \u2713` : base
    },
    isLanguageSwitch: code,
  }))
}
