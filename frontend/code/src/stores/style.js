import { defineStore } from 'pinia'

export const useStyleStore = defineStore('style', {
  state: () => ({
    /* Styles */
    asideStyle: '',
    asideScrollbarsStyle: '',
    asideBrandStyle: '',
    asideMenuItemStyle: '',
    asideMenuItemActiveStyle: 'font-bold text-black dark:text-white',
    asideMenuDropdownStyle: '',
    navBarItemLabelStyle: '',
    navBarItemLabelHoverStyle: '',
    navBarItemLabelActiveColorStyle: '',
    overlayStyle: '',
    whiteBg: 'bg-white',
    whiteText: 'text-black',
    darkBg: 'bg-slate-900/70',
    darkBgModal: 'bg-gray-800',
    darkText: 'text-white',

    /* Theme Mode */
    themeMode: 'auto', // 'auto' | 'light' | 'dark'
    _themeMediaQuery: null,
    _themeMediaQueryListener: null,
    isDark: false,
  }),
  persist: true,
  getters: {
    /**
     * Indicates whether dark mode is currently active.
     *
     * @param {Object} state
     * @returns {boolean}
     */
    darkMode(state) {
      return state.isDark
    },
  },
  actions: {
    /**
     * Initializes a media query watcher to track the system's theme mode.
     * Automatically applies dark or light theme based on system preference or user selection.
     */
    initializeThemeWatcher() {
      if (typeof window !== 'undefined' && window.matchMedia) {
        this._themeMediaQuery = window.matchMedia(
          '(prefers-color-scheme: dark)',
        )

        this._themeMediaQueryListener = () => {
          if (this.themeMode === 'auto') {
            this.isDark = this._themeMediaQuery.matches
          } else {
            this.isDark = this.themeMode === 'dark'
          }

          document.body.classList[this.isDark ? 'add' : 'remove'](
            'dark-scrollbars',
          )
          document.documentElement.classList[this.isDark ? 'add' : 'remove'](
            'dark-scrollbars-compat',
          )
        }

        this._themeMediaQuery.addEventListener(
          'change',
          this._themeMediaQueryListener,
        )

        // Direkt initial setzen
        this._themeMediaQueryListener()
      }
    },

    /**
     * Cleans up the media query event listener.
     * Should be called when the component/store is destroyed.
     */
    destroyThemeWatcher() {
      if (this._themeMediaQuery && this._themeMediaQueryListener) {
        this._themeMediaQuery.removeEventListener(
          'change',
          this._themeMediaQueryListener,
        )
        this._themeMediaQuery = null
        this._themeMediaQueryListener = null
      }
    },

    /**
     * Cycles through theme modes in the order: auto -> dark -> light -> auto ...
     */
    nextThemeMode() {
      const themeModes = ['auto', 'dark', 'light']
      const index = themeModes.indexOf(this.themeMode)
      const nextIndex = (index + 1) % themeModes.length
      this.setThemeMode(themeModes[nextIndex])
    },

    /**
     * Manually sets the theme mode and updates the state accordingly.
     *
     * @param {'auto'|'light'|'dark'} mode - Desired theme mode.
     */
    setThemeMode(mode) {
      this.themeMode = mode

      if (this._themeMediaQueryListener) {
        this._themeMediaQueryListener()
      }
    },
  },
})
