import App from './App.vue'
import './css/main.css'
import i18n, { getI18nT } from './i18n'
import router from './router'

import * as Sentry from '@sentry/vue'
import { createSentryPiniaPlugin } from '@sentry/vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import { computed, createApp } from 'vue'
import Toast, { TYPE } from 'vue-toastification'
import 'vue-toastification/dist/index.css'

import tooltip from '@/directives/tooltipDirective.js'
import { useMainStore } from '@/stores/main.js'
import { parseBoolEnv } from '@/utils/env.js'

/* Pinia State Mangement*/
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

// Sentry Pinia Plugin for state tracking in errors
const sentryEnabled = parseBoolEnv(import.meta.env.VITE_SENTRY_ENABLED)
if (sentryEnabled) {
  pinia.use(createSentryPiniaPlugin())
}

/* Toast Notifications */
const toastOptions = {
  timeout: 1800,
  toastDefaults: {
    [TYPE.ERROR]: {
      timeout: 5600,
      closeButton: false,
    },
    [TYPE.SUCCESS]: {
      timeout: 1800,
      hideProgressBar: true,
    },
    [TYPE.WARNING]: {
      timeout: 2400,
      hideProgressBar: true,
    },
  },
}

const app = createApp(App)

/* Load Sentry (if enabled) */
if (sentryEnabled) {
  let sentryErrorReportEnabled = parseBoolEnv(
    import.meta.env.VITE_SENTRY_REPORT_ERROR_ENABLED,
  )
  let sentryUserReportEnabled = parseBoolEnv(
    import.meta.env.VITE_SENTRY_REPORT_USER_ENABLED,
  )
  let sentryTransmitUserDetails = parseBoolEnv(
    import.meta.env.VITE_SENTRY_TRANSMIT_USER_DETAILS,
  )

  Sentry.init({
    app,
    dsn: import.meta.env.VITE_SENTRY_DSN,
    release: process.env.VUE_SENTRY_RELEASE,
    environment: import.meta.env.VITE_SENTRY_ENV,
    enableLogs: true,

    sendDefaultPii: sentryTransmitUserDetails,

    transportOptions: {
      maxQueueSize: 30,
    },

    beforeSend(event) {
      /* Show error reporting modal, if enabled */
      if (event.exception && event.event_id && sentryErrorReportEnabled) {
        let sentryUserId = null
        let sentryUsername = 'Anonymous'
        let sentryUserEmail = 'anonymous@example.org'
        if (sentryTransmitUserDetails) {
          sentryUserId = mainStore.getUserId
          sentryUsername = mainStore.getUsername
          sentryUserEmail = mainStore.getUserMail
        }
        Sentry.showReportDialog({
          eventId: event.event_id,
          user: {
            id: sentryUserId,
            name: sentryUsername,
            email: sentryUserEmail,
          },
        })
      }
      /* Drop user infos for privacy, if not disabled */
      if (!sentryTransmitUserDetails && event.user) {
        delete event.user.email
        delete event.user.username
      }
      return event
    },
    integrations: [
      Sentry.browserTracingIntegration({ router }),
      Sentry.replayIntegration({
        unmask: ['.sentry-unmask'],
        unblock: ['.sentry-unblock'],
        ignore: ['.sentry-ignore', '[data-sentry-ignore]'],
        networkDetailAllowUrls: [window.location.origin],
        networkRequestHeaders: ['Cache-Control'],
        networkResponseHeaders: ['Referrer-Policy'],
        networkCaptureBodies: true,
        minReplayDuration: 5000,
      }),
      Sentry.browserProfilingIntegration(),
      Sentry.consoleLoggingIntegration({
        levels: ['warn', 'error'],
      }),
      sentryUserReportEnabled &&
        Sentry.feedbackIntegration({
          colorScheme: 'system',
          enableScreenshot: true,
          showBranding: false,
          id: 'feedback-integration',
          showName: false,
          showEmail: false,
          messageLabel: 'Beschreibung',
          isRequiredLabel: '(Erforderlich)',
          addScreenshotButtonLabel: 'Screenshot hinzufügen',
          removeScreenshotButtonLabel: 'Screenshot entfernen',
          cancelButtonLabel: 'Abbrechen',
          confirmButtonLabel: 'Bestätigen',
          submitButtonLabel: 'Bug Report absenden',
          triggerLabel: 'Fehler melden',
          formTitle: 'Fehler melden',
          messagePlaceholder: 'Was ist der Fehler? Was haben Sie erwartet?',
          successMessageText: 'Vielen Dank für Ihren Bericht!',
          autoInject: true,
          showOnConsoleError: false,
        }),
    ].filter(Boolean),

    // Tracing - explicit parsing of sample rates
    tracesSampleRate:
      parseFloat(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE) || 0,
    // Set 'tracePropagationTargets' to control for which URLs distributed tracing should be enabled
    tracePropagationTargets: import.meta.env
      .VITE_SENTRY_TRACE_PROPAGATION_TARGETS,

    // Profiling sample rate (tied to traces)
    profilesSampleRate:
      parseFloat(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE) || 0,

    // Session Replay
    replaysSessionSampleRate:
      parseFloat(import.meta.env.VITE_SENTRY_REPLAYS_SESSION_SAMPLE_RATE) || 0,
    replaysOnErrorSampleRate:
      parseFloat(import.meta.env.VITE_SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE) || 0,
  })
}

/* Load i18n support (configured in src/i18n.js) */

app
  .use(router)
  .use(pinia)
  .use(Toast, toastOptions)
  .use(i18n)
  .directive('tooltip', tooltip)

/* Initialize Store*/
useMainStore().init()

app.mount('#app')

/* Pinia Load States */
const mainStore = useMainStore(pinia)

const defaultDocumentTitle = computed(
  () => mainStore.settings?.branding?.app?.title ?? 'OpenVLE',
).value

/* Set document title to view title */
router.afterEach((to) => {
  const t = getI18nT()
  const titleParams = to.meta?.titleEntityKey
    ? { entity: t(to.meta.titleEntityKey) }
    : {}
  const title = to.meta?.titleKey
    ? t(to.meta.titleKey, titleParams)
    : to.meta?.title || null
  document.title = title
    ? `${title} — ${defaultDocumentTitle}`
    : defaultDocumentTitle
})
