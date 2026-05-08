<script setup>
import { mdiAccount, mdiAlert, mdiAsterisk, mdiRefresh } from '@mdi/js'
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import CardBox from '@/components/CardBox.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import SectionFullScreen from '@/components/SectionFullScreen.vue'
import LayoutGuest from '@/layouts/LayoutGuest.vue'
import backend from '@/services'
import { useMainStore } from '@/stores/main'
import { useRateLimitStore } from '@/stores/rateLimit'
import { useStyleStore } from '@/stores/style.js'
import { getBackendUrl } from '@/utils/env'

const { t } = useI18n()
const mainStore = useMainStore()
const rateLimitStore = useRateLimitStore()
const route = useRoute()
const router = useRouter()
const toast = useToast()

const form = reactive({
  login: '',
  password: '',
})

const loginPending = ref(false)

const applicationLabel = computed(() => mainStore.settings?.branding?.app?.name)

const usernameHelpLabel = computed(
  () => mainStore.settings?.auth?.local?.username?.help,
)
const passwordHelpLabel = computed(
  () => mainStore.settings?.auth?.local?.password?.help,
)
const passwordResetLink = computed(() => mainStore.settings?.auth?.reset?.url)

const localEnabled = computed(() =>
  Boolean(route?.query?.override || mainStore.settings?.auth?.local?.enabled),
)

const oidcEnabled = computed(
  () => mainStore.settings?.auth?.oidc?.enabled ?? false,
)

const oidcLabel = computed(() => mainStore.settings?.auth?.oidc?.label)

const oidcLink = computed(() => {
  if (!oidcEnabled.value) return null
  const oidcFrontendURL = `${window.location.origin}/#/auth/oidc/callback`
  return `${getBackendUrl()}/auth/oidc/login?redirect=${encodeURIComponent(oidcFrontendURL)}`
})

const settingsError = computed(() => mainStore.settingsStatus == 'error')

const loading = computed(() => mainStore.settingsStatus == 'loading')

const submit = async () => {
  try {
    loginPending.value = true
    let check = await backend.auth.login({
      username: form.login,
      password: form.password,
    })
    if (check && check.data) {
      mainStore.login(check.data)

      if (router.currentRoute?.value?.query?.redirect) {
        router.push(router.currentRoute.value.query.redirect)
      } else {
        router.push('/')
      }
    } else {
      throw Error
    }
  } catch (error) {
    if (error?.response?.data?.error_code === 'INCORRECT_CREDENTIALS') {
      toast.error(t('views.auth.login.incorrectCredentials'), {
        timeout: 8400,
      })
    }
  } finally {
    loginPending.value = false
    form.password = ''
  }
}

onMounted(async () => {
  switch (String(route?.query?.error).toLowerCase()) {
    case 'missing_token':
      toast.error(t('views.auth.login.missingToken'), {
        timeout: 8400,
      })
      break
    case 'incorrect_credentials':
      toast.error(t('views.auth.login.incorrectCredentials'), {
        timeout: 8400,
      })
      break
    case 'redirect_invalid':
      toast.error(t('views.auth.login.redirectInvalid'), {
        timeout: 8400,
      })
      break
    case 'csrf_mismatch':
      toast.error(t('views.auth.login.csrfMismatch'), {
        timeout: 8400,
      })
      break
    case 'system_user':
      toast.error(t('views.auth.login.systemUser'), {
        timeout: 8400,
      })
      break
    case 'user_not_active':
      toast.error(t('views.auth.login.userNotActive'), {
        timeout: 8400,
      })
      break
    case 'unknown_error':
      toast.error(t('views.auth.login.unknownError'), {
        timeout: 8400,
      })
      break
  }
  const { error, ...rest } = route.query
  router.replace({ query: rest })
})
</script>

<template>
  <LayoutGuest>
    <SectionFullScreen
      v-slot="{ cardClass }"
      background-image="/logo_background.svg"
    >
      <!-- Language switcher: top-right corner -->
      <div class="absolute top-4 right-4">
        <LanguageSwitcher :drop-up="false" />
      </div>

      <div class="w-full flex flex-col items-center">
        <CardBox
          :class="cardClass"
          is-form
          :is-modal="true"
          @submit.prevent="submit"
        >
          <!-- Image: App logo -->
          <div
            :class="{ 'dark-mode': useStyleStore().darkMode }"
            class="-mt-4 mb-0"
          >
            <img
              :src="
                useStyleStore().darkMode
                  ? '/logo-with-text-dark.svg'
                  : '/logo-with-text-light.svg'
              "
              alt="Portal Logo"
              class="w-auto h-30 md:h-60 mx-auto"
            />
          </div>

          <div class="grid content-start">
            <!-- Loading: Show spinner -->
            <div
              v-if="loading"
              class="flex flex-col items-center justify-center py-10"
            >
              <svg
                class="animate-spin h-10 w-10 mb-3"
                viewBox="0 0 24 24"
                role="status"
                :aria-label="$t('views.auth.login.loading')"
              >
                <circle
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                  fill="none"
                  opacity="0.2"
                />

                <path
                  d="M22 12a10 10 0 0 1-10 10"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="4"
                />
              </svg>

              <span class="text-sm opacity-75">
                {{ $t('views.auth.login.appLoading') }}
              </span>
            </div>

            <!-- Error: Show error msg -->
            <div
              v-else-if="settingsError"
              class="py-10"
              role="alert"
              aria-live="polite"
            >
              <div
                class="mx-auto max-w-md grid justify-items-center text-center gap-3"
              >
                <!-- Icon -->
                <svg
                  class="h-10 w-10 text-red-500"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <circle cx="12" cy="12" r="10" stroke-opacity="0.2" />

                  <line x1="15" y1="9" x2="9" y2="15" />

                  <line x1="9" y1="9" x2="15" y2="15" />
                </svg>

                <h3 class="text-base font-bold">
                  {{
                    $t('common.loadError', {
                      entity: $t('objectTypes.application.singular'),
                    })
                  }}
                </h3>

                <div class="w-full sm:w-auto mb-2 mt-2">
                  <BaseButton
                    class="w-full sm:w-auto"
                    color="info"
                    :icon="mdiRefresh"
                    :label="$t('views.auth.login.retry')"
                    @click="mainStore.loadSettings"
                  />
                </div>

                <p class="text-xs opacity-75 leading-snug">
                  {{ $t('views.auth.login.appLoadErrorHelp') }}
                </p>
              </div>
            </div>

            <!-- Loaded: Show login -->
            <template v-else>
              <p
                class="mb-2"
                style="text-align: center; font-weight: bold; font-size: larger"
              >
                {{ applicationLabel }}
              </p>

              <!-- Field: username -->
              <FormField
                v-if="localEnabled"
                :label="$t('views.auth.login.username')"
                :help="usernameHelpLabel"
              >
                <FormControl
                  v-model="form.login"
                  :icon="mdiAccount"
                  name="login"
                  :placeholder="$t('views.auth.login.usernamePlaceholder')"
                  autocomplete="username"
                  :required="true"
                  autofocus
                />
              </FormField>

              <!-- Field: password -->
              <FormField
                v-if="localEnabled"
                :label="$t('views.auth.login.password')"
                :help="passwordHelpLabel"
              >
                <FormControl
                  v-model="form.password"
                  :icon="mdiAsterisk"
                  type="password"
                  name="password"
                  placeholder="********"
                  autocomplete="current-password"
                  :required="true"
                />
              </FormField>
            </template>
          </div>

          <!-- Alert: Auth disabled (if auth disabled) -->
          <NotificationBar
            v-if="!loading && !settingsError && !oidcEnabled && !localEnabled"
            class="mt-5 mb-2"
            color="danger"
            :dismissable="false"
            :icon="mdiAlert"
          >
            <b>{{ $t('views.auth.login.authDisabled') }}</b>
          </NotificationBar>

          <!-- Buttons: Login & password reset (& OIDC) -->
          <template #footer>
            <div
              v-if="!loading && !settingsError"
              :class="{ '-mt-4': localEnabled }"
            >
              <BaseButtons v-if="localEnabled" class="flex justify-center">
                <!-- Button: Login -->
                <BaseButton
                  type="submit"
                  color="info"
                  :label="$t('views.auth.login.submit')"
                  :disabled="loginPending || rateLimitStore.active"
                />

                <!-- Button: Password reset -->
                <BaseButton
                  v-if="passwordResetLink"
                  :href="passwordResetLink"
                  target="_blank"
                  color="warning"
                  :label="$t('views.auth.login.forgotPassword')"
                />
              </BaseButtons>

              <!-- Buttons: OIDC -->
              <div v-if="oidcEnabled && oidcLabel && oidcLink">
                <hr v-if="localEnabled" class="m-5 mb-10" />

                <div class="mb-4 flex justify-center">
                  <BaseButton
                    :href="oidcLink"
                    color="success"
                    :label="oidcLabel"
                  />
                </div>
              </div>
            </div>
          </template>
        </CardBox>
      </div>
    </SectionFullScreen>
  </LayoutGuest>
</template>
