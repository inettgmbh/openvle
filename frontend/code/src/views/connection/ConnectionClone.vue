<script setup>
import {
  mdiAccountBox,
  mdiAlertCircle,
  mdiCheck,
  mdiContentCopy,
  mdiInformationOutline,
  mdiKey,
  mdiMonitor,
  mdiNetwork,
  mdiNumeric1Circle,
  mdiNumeric2Circle,
  mdiNumeric3Circle,
} from '@mdi/js'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseIcon from '@/components/BaseIcon.vue'
import CardBox from '@/components/CardBox.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import SearchControl from '@/components/SearchControl.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import { useConnectionForm } from '@/composables/useConnectionForm'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import router from '@/router'
import backend from '@/services'
import { useMainStore } from '@/stores/main'

const mainStore = useMainStore()
const connection = ref({})
const route = useRoute()
const toast = useToast()
const { t } = useI18n()

const queryError = ref(null)
const sourceId = ref(null)

const existingProtocols = ref(new Set())
const isLoadingProtocols = ref(false)

// Toggle to enforce unique protocols per entity.
// When false, duplicate protocols are allowed with a warning.
const STRICT_PROTOCOL_UNIQUENESS = true

const { protocolButtons, getDefaultPort } = useConnectionForm({
  existingProtocols,
})

const hasEntity = computed(() => !!connection.value.entity?.id)
const hasProtocol = computed(() => !!connection.value.protocol)

const currentStep = computed(() => {
  if (!hasEntity.value) return 1
  if (!hasProtocol.value) return 2
  return 3
})

function selectProtocol(value) {
  if (!connection.value.entity?.id) return
  if (isLoadingProtocols.value) return

  if (existingProtocols.value.has(value)) {
    if (STRICT_PROTOCOL_UNIQUENESS) {
      toast.info(t('views.connections.clone.protocolAlreadyAssigned'))
      return
    }
  }

  connection.value.protocol = value
}

async function loadExistingProtocols() {
  existingProtocols.value = new Set()

  const entity = connection.value.entity
  if (!entity?.id || !entity?.type) return

  isLoadingProtocols.value = true
  try {
    const templates = await backend.connections.listByObject(
      entity.type,
      entity.id,
      { page: 1, limit: 200 },
    )

    existingProtocols.value = new Set(
      (templates?.items || []).map((t) => t.protocol).filter(Boolean),
    )

    if (
      connection.value.protocol &&
      existingProtocols.value.has(connection.value.protocol)
    ) {
      if (STRICT_PROTOCOL_UNIQUENESS) {
        connection.value.protocol = null
      }
      toast.info(t('views.connections.clone.duplicateProtocolWarning'), {
        timeout: 2400,
      })
    }
  } catch (error) {
    existingProtocols.value = new Set()
  } finally {
    isLoadingProtocols.value = false
  }
}

function validateProtocolUniqueness() {
  const entity = connection.value.entity
  const protocol = connection.value.protocol

  if (!entity?.id || !entity?.type || !protocol) return true

  if (existingProtocols.value.has(protocol)) {
    if (STRICT_PROTOCOL_UNIQUENESS) {
      toast.error(t('views.connections.clone.duplicateProtocolWarning'))
      return false
    }
  }

  return true
}

function isEmpty(value) {
  return value === undefined || value === null || value === ''
}

const isUsernameValid = computed(() => {
  const pattern = mainStore.settings?.connection?.profiles?.username?.regex
  if (!pattern) return true
  return new RegExp(pattern).test(connection.value.username || '')
})

function validateUsername(value) {
  const pattern = mainStore.settings?.connection?.profiles?.username?.regex
  if (!pattern) return true
  if (!new RegExp(pattern).test(value)) {
    return (
      mainStore.settings?.connection?.profiles?.username?.help ||
      t('views.connections.clone.invalidFormat')
    )
  }
  return true
}

function validateQueryAndInit() {
  const q = route.query

  const requiredFields = {
    source: q.source,
    protocol: q.protocol,
    port: q.port,
    username: q.username,
  }

  const missing = Object.entries(requiredFields)
    .filter(([, v]) => isEmpty(v))
    .map(([k]) => k)

  if (missing.length > 0) {
    queryError.value = t('views.connections.clone.missingSourceData', {
      fields: missing.join(', '),
    })
    toast.error(t('views.connections.clone.sourceDataError'))
    router.replace({ path: '/connections' })
    return false
  }

  // Store source ID for cloning
  sourceId.value = q.source

  // Pre-fill from source (but NOT the entity - user must select new target)
  connection.value.port = q.port
  connection.value.protocol = q.protocol
  connection.value.username = q.username
  connection.value.entity = null

  return true
}

async function submit() {
  if (!validateProtocolUniqueness()) return

  try {
    const res = await backend.connections.clone(sourceId.value, {
      objectId: connection.value.entity.id,
      objectType: connection.value.entity.type,
      port: connection.value.port,
      protocol: connection.value.protocol,
      username: connection.value.username,
      password: connection.value.password,
    })
    toast.success(
      t('common.cloneSuccess', {
        entity: t('objectTypes.guacamoleConnectionProfile.singular'),
      }),
    )
    router.push({ path: `/connections/${res.id}` })
  } catch (error) {
    toast.error(
      `${t('common.cloneError', { entity: t('objectTypes.guacamoleConnectionProfile.singular') })}\n${error?.response?.data?.detail ?? t('common.unknownError')}`,
    )
  }
}

function onVMSearchStarted() {
  connection.value.entity = null
  existingProtocols.value = new Set()
}

watch(
  () => [connection.value.entity?.id, connection.value.entity?.type],
  async ([id, type]) => {
    if (!id || !type) return
    await loadExistingProtocols()
  },
)

watch(
  () => connection.value.protocol,
  (protocol) => {
    connection.value.port = getDefaultPort(protocol)
  },
)

onMounted(() => {
  validateQueryAndInit()
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiContentCopy"
        :title="$t('views.connections.clone.connectionTemplateClone')"
        main
        docs-path="/docs/usage/openvle/connections/"
      />

      <CardBox is-form @submit.prevent="submit">
        <!-- Error banner -->
        <NotificationBar
          v-if="queryError"
          :dismissable="false"
          :icon="mdiAlertCircle"
          color="danger"
          class="mb-6"
        >
          <p>
            <b>{{ $t('views.connections.clone.copyAborted') }}</b>

            <br />
            {{ queryError }}
          </p>
        </NotificationBar>

        <!-- Info banner -->
        <div
          v-if="!queryError"
          class="mb-6 rounded-lg border border-blue-200 bg-blue-50 p-3 dark:border-blue-800 dark:bg-blue-900/20"
        >
          <div class="flex items-start gap-3">
            <BaseIcon
              :path="mdiInformationOutline"
              class="mt-0.5 shrink-0 text-blue-600 dark:text-blue-400"
              :size="20"
            />

            <div class="min-w-0 flex-1">
              <p class="text-sm text-blue-800 dark:text-blue-200">
                <b>{{ $t('views.connections.clone.copyInfoBold') }}</b>
                {{ $t('views.connections.clone.copyInfoText') }}
              </p>

              <p class="mt-1 text-xs text-blue-700 dark:text-blue-300">
                {{ $t('views.connections.clone.passwordHint') }}
              </p>
            </div>
          </div>
        </div>

        <!-- Step 1: Select target VM -->
        <div class="mb-6">
          <div class="mb-3 flex items-center gap-2">
            <BaseIcon
              :path="mdiNumeric1Circle"
              :size="24"
              :class="
                hasEntity
                  ? 'text-green-600 dark:text-green-400'
                  : 'text-blue-600 dark:text-blue-400'
              "
            />

            <span class="font-medium">{{
              $t('views.connections.clone.selectTarget')
            }}</span>

            <BaseIcon
              v-if="hasEntity"
              :path="mdiCheck"
              :size="18"
              class="text-green-600 dark:text-green-400"
            />
          </div>

          <SearchControl
            v-model="connection.entity"
            return-attribute="ident"
            :icon="mdiMonitor"
            :fetch-data="backend.vms.searchVMsAndTemplates"
            :fetch-selected="backend.vms.getVMOrTemplateName"
            :placeholder="$t('views.connections.clone.searchByName')"
            required
            :autofocus="true"
            @input-started="onVMSearchStarted"
          />
        </div>

        <!-- Step 2: Select protocol -->
        <div class="mb-6">
          <div class="mb-3 flex items-center gap-2">
            <BaseIcon
              :path="mdiNumeric2Circle"
              :size="24"
              :class="
                hasProtocol
                  ? 'text-green-600 dark:text-green-400'
                  : currentStep >= 2
                    ? 'text-blue-600 dark:text-blue-400'
                    : 'text-gray-300 dark:text-slate-600'
              "
            />

            <span
              class="font-medium"
              :class="
                currentStep < 2 ? 'text-gray-400 dark:text-slate-500' : ''
              "
            >
              {{ $t('views.connections.clone.protocolAndPort') }}
            </span>

            <BaseIcon
              v-if="hasProtocol"
              :path="mdiCheck"
              :size="18"
              class="text-green-600 dark:text-green-400"
            />
          </div>

          <!-- Protocol buttons -->
          <div
            class="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4"
            :class="{ 'pointer-events-none opacity-40': !hasEntity }"
          >
            <button
              v-for="p in protocolButtons"
              :key="p.value"
              type="button"
              class="relative flex flex-col items-center rounded-xl border-2 p-4 transition-all"
              :class="[
                connection.protocol === p.value
                  ? 'border-blue-500 bg-blue-50 dark:border-blue-400 dark:bg-blue-900/30'
                  : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50 dark:border-slate-600 dark:bg-slate-800 dark:hover:border-slate-500 dark:hover:bg-slate-700',
                p.disabled && STRICT_PROTOCOL_UNIQUENESS
                  ? 'cursor-not-allowed opacity-40'
                  : 'cursor-pointer',
              ]"
              :disabled="
                (p.disabled && STRICT_PROTOCOL_UNIQUENESS) ||
                isLoadingProtocols ||
                !hasEntity
              "
              @click="selectProtocol(p.value)"
            >
              <BaseIcon
                :path="p.icon"
                :size="28"
                :class="
                  connection.protocol === p.value
                    ? 'text-blue-600 dark:text-blue-400'
                    : 'text-gray-500 dark:text-slate-400'
                "
              />

              <span
                class="mt-2 text-sm font-semibold"
                :class="
                  connection.protocol === p.value
                    ? 'text-blue-700 dark:text-blue-300'
                    : 'text-gray-700 dark:text-slate-200'
                "
              >
                {{ p.label }}
              </span>

              <span
                class="mt-0.5 text-xs"
                :class="
                  connection.protocol === p.value
                    ? 'text-blue-600 dark:text-blue-400'
                    : 'text-gray-400 dark:text-slate-500'
                "
              >
                {{
                  STRICT_PROTOCOL_UNIQUENESS && p.disabled
                    ? $t('views.connections.clone.alreadyAssigned')
                    : `Port ${p.port}`
                }}

                <i v-if="p.disabled && !STRICT_PROTOCOL_UNIQUENESS">
                  ({{ $t('views.connections.clone.alreadyExists') }})
                </i>
              </span>

              <!-- Selection indicator -->
              <div
                v-if="connection.protocol === p.value"
                class="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-blue-500 dark:bg-blue-400"
              >
                <BaseIcon :path="mdiCheck" :size="14" class="text-white" />
              </div>
            </button>
          </div>

          <!-- Port field -->
          <div :class="{ 'pointer-events-none opacity-40': !hasEntity }">
            <FormField
              :label="$t('common.port')"
              :help="$t('views.connections.clone.portCanBeAdjusted')"
            >
              <FormControl
                v-model="connection.port"
                :icon="mdiNetwork"
                type="number"
                :disabled="!hasEntity"
                required
              />
            </FormField>
          </div>
        </div>

        <!-- Step 3: Credentials -->
        <div class="mb-2">
          <div class="mb-3 flex items-center gap-2">
            <BaseIcon
              :path="mdiNumeric3Circle"
              :size="24"
              :class="
                currentStep >= 3
                  ? 'text-blue-600 dark:text-blue-400'
                  : 'text-gray-300 dark:text-slate-600'
              "
            />

            <span
              class="font-medium"
              :class="
                currentStep < 3 ? 'text-gray-400 dark:text-slate-500' : ''
              "
            >
              {{ $t('views.connections.clone.vmCredentials') }}
            </span>
          </div>

          <div
            :class="{
              'pointer-events-none opacity-40': currentStep < 3,
            }"
          >
            <FormField>
              <FormField
                :label="$t('common.username')"
                :help="$t('views.connections.clone.localUserWithinVm')"
              >
                <FormControl
                  v-model="connection.username"
                  :icon="mdiAccountBox"
                  :placeholder="$t('views.connections.clone.exampleUsername')"
                  :disabled="currentStep < 3"
                  :validate="validateUsername"
                  required
                />
              </FormField>

              <FormField
                :label="$t('common.password')"
                :help="
                  $t('views.connections.clone.leaveEmptyForSourcePassword')
                "
              >
                <FormControl
                  v-model="connection.password"
                  :icon="mdiKey"
                  type="password"
                  :placeholder="
                    $t('views.connections.clone.keepSourcePassword')
                  "
                  :disabled="currentStep < 3"
                />
              </FormField>
            </FormField>
          </div>
        </div>

        <template #footer>
          <BaseButtons>
            <BaseButton
              type="submit"
              color="info"
              :label="$t('views.connections.clone.connectionTemplateClone')"
              :disabled="currentStep < 3 || !isUsernameValid"
            />

            <BaseButton
              type="reset"
              color="info"
              :label="$t('common.cancel')"
              outline
              @click="router.back()"
            />
          </BaseButtons>
        </template>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
