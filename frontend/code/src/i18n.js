import { createI18n } from 'vue-i18n'

import de from '@/locales/de.json'

// Lazy-loaded locale imports — only fetched when the locale is activated
const localeLoaders = {
  de: () => Promise.resolve(de),
  en: () => import('@/locales/en.json'),
  es: () => import('@/locales/es.json'),
  fr: () => import('@/locales/fr.json'),
}

// Single source of truth for all locales — add new languages here
export const LOCALE_META = {
  de: { flag: '\uD83C\uDDE9\uD83C\uDDEA', name: 'Deutsch' },
  en: { flag: '\uD83C\uDDEC\uD83C\uDDE7', name: 'English' },
  es: { flag: '\uD83C\uDDEA\uD83C\uDDF8', name: 'Espa\u00F1ol' },
  fr: { flag: '\uD83C\uDDEB\uD83C\uDDF7', name: 'Fran\u00E7ais' },
}

export const SUPPORTED_LOCALES = Object.keys(LOCALE_META)

const DEFAULT_LOCALE = 'de'

/**
 * Resolves a raw locale string (e.g. 'de_DE', 'en-US') to a supported short locale.
 *
 * @param {string} raw - The raw locale identifier.
 * @returns {string} A supported locale code.
 */
export function resolveLocale(raw) {
  if (!raw) return DEFAULT_LOCALE
  const short = raw.replace(/[-_].*/, '').toLowerCase()
  return SUPPORTED_LOCALES.includes(short) ? short : DEFAULT_LOCALE
}

const storedLocale = localStorage.getItem('openvle-locale')
const initialLocale = storedLocale || resolveLocale(navigator.language)

const i18n = createI18n({
  legacy: false,
  locale: DEFAULT_LOCALE,
  fallbackLocale: DEFAULT_LOCALE,
  messages: { de },
  missingWarn: false,
})

export default i18n

// Track which locales have been loaded
const loadedLocales = new Set([DEFAULT_LOCALE])

/**
 * Loads locale messages if not already loaded, then activates the locale.
 *
 * @param {string} locale - The locale to set (resolved via resolveLocale).
 * @returns {Promise<void>}
 */
export async function setLocale(locale) {
  const resolved = resolveLocale(locale)

  if (!loadedLocales.has(resolved)) {
    const messages = await localeLoaders[resolved]()
    i18n.global.setLocaleMessage(resolved, messages.default || messages)
    loadedLocales.add(resolved)
  }

  i18n.global.locale.value = resolved
  document.documentElement.lang = resolved
}

/**
 * Returns the global t() function for use outside Vue components (services, utils).
 *
 * @returns {Function} The vue-i18n translate function.
 */
export function getI18nT() {
  return i18n.global.t
}

// Load initial locale if not the default
if (initialLocale !== DEFAULT_LOCALE) {
  setLocale(initialLocale)
}
