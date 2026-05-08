import { computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { resolveLocale, setLocale } from '@/i18n'
import { useMainStore } from '@/stores/main'

const LOCALE_STORAGE_KEY = 'openvle-locale'

/**
 * Resolves the effective locale using the priority chain:
 * JWT user locale > localStorage > browser language.
 *
 * @param {string|undefined} userLocale - The locale from the JWT/store.
 * @returns {string} The resolved locale code.
 */
function resolveEffectiveLocale(userLocale) {
  if (userLocale) return resolveLocale(userLocale)
  const stored = localStorage.getItem(LOCALE_STORAGE_KEY)
  if (stored) return stored
  return resolveLocale(navigator.language)
}

/**
 * Switches the active locale, persists to localStorage, and updates
 * the store user locale when logged in.
 *
 * @param {string} code - A supported locale code ('de', 'en', 'fr').
 */
export async function switchLocale(code) {
  const resolved = resolveLocale(code)
  await setLocale(resolved)
  localStorage.setItem(LOCALE_STORAGE_KEY, resolved)

  const mainStore = useMainStore()
  if (mainStore.isLoggedIn) {
    mainStore.user.locale = resolved
    // TODO: persist locale to backend via API
  }
}

/**
 * Composable that keeps the i18n locale in sync with the user's locale
 * from the store. Call once in a top-level layout component.
 *
 * Priority chain: JWT user locale > localStorage > browser language.
 *
 * @returns {{ locale: import('vue').Ref<string> }}
 */
export function useLocale() {
  const { locale } = useI18n()
  const mainStore = useMainStore()
  const userLocale = computed(() => mainStore.user?.locale)

  watch(
    userLocale,
    async (val) => {
      const effective = resolveEffectiveLocale(val)
      await setLocale(effective)
      localStorage.setItem(LOCALE_STORAGE_KEY, effective)
    },
    { immediate: true },
  )

  return { locale }
}
