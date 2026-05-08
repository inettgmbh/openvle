import {
  mdiAccount,
  mdiLogout,
  mdiTextBoxMultipleOutline,
  mdiThemeLightDark,
  mdiTranslate,
  mdiWeatherNight,
  mdiWeatherSunny,
} from '@mdi/js'
import { computed } from 'vue'

import i18n, { getI18nT, LOCALE_META } from '@/i18n'
import { useMainStore } from '@/stores/main'
import { useStyleStore } from '@/stores/style.js'
import { getLanguageMenuItems } from '@/utils/localeData'

const mainStore = useMainStore()
const styleStore = useStyleStore()

function getThemeIcon() {
  switch (styleStore.themeMode) {
    case 'light':
      return mdiWeatherSunny
    case 'dark':
      return mdiWeatherNight
    default:
      return mdiThemeLightDark
  }
}

function getThemeLabel() {
  const t = getI18nT()
  switch (styleStore.themeMode) {
    case 'light':
      return t('navbar.lightMode')
    case 'dark':
      return t('navbar.darkMode')
    default:
      return t('navbar.autoMode')
  }
}

export default [
  {
    isCurrentUser: true,
    menu: [
      {
        icon: mdiAccount,
        get label() {
          return getI18nT()('navbar.myProfile')
        },
        to: '/profile',
      },
      //{
      //  icon: mdiEmail,
      //  label: 'Benachrichtigungen',
      //},
      //{
      //  icon: mdiCogOutline,
      //  label: 'Einstellungen',
      //},
      // {
      //   isDivider: true,
      // },
    ],
  },
  {
    icon: mdiTextBoxMultipleOutline,
    get label() {
      return computed(() => mainStore.settings?.branding?.docs?.label).value
    },
    get href() {
      return computed(() => mainStore.settings?.branding?.docs?.url).value
    },
    target: '_blank',
  },
  {
    icon: mdiTranslate,
    get label() {
      return LOCALE_META[i18n.global.locale.value]?.name || ''
    },
    isDesktopNoLabel: true,
    menu: getLanguageMenuItems(i18n),
  },
  {
    get icon() {
      return getThemeIcon()
    },
    get label() {
      return getThemeLabel()
    },
    isDesktopNoLabel: true,
    isToggleLightDark: true,
  },
  {
    icon: mdiLogout,
    get label() {
      return getI18nT()('navbar.logout')
    },
    isDesktopNoLabel: false,
    isLogout: true,
  },
  // {
  //   icon: mdiIcon,
  //   label: 'Label',
  //   isDesktopNoLabel: true,
  //   href: 'https://example.com',
  //   target: '_blank',
  // },
]
