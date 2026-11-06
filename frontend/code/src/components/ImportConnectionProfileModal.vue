<script setup>
import {
  mdiAccountBox,
  mdiAlertCircleOutline,
  mdiCheck,
  mdiKey,
  mdiMonitor,
  mdiNetwork,
  mdiNumeric1Circle,
  mdiNumeric2Circle,
  mdiNumeric3Circle,
} from '@mdi/js'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'vue-toastification'

import BaseIcon from '@/components/BaseIcon.vue'
import CardBoxModal from '@/components/CardBoxModal.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import SearchControl from '@/components/SearchControl.vue'
import { useConnectionForm } from '@/composables/useConnectionForm'
import { FIELD_LIMITS } from '@/config/fieldLimits'
import backend from '@/services'
import { useMainStore } from '@/stores/main'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  targetObjectType: { type: String, required: true },
  targetObjectId: { type: String, required: true },
})

const emit = defineEmits(['update:modelValue', 'imported'])

const { t } = useI18n()
const toast = useToast()
const mainStore = useMainStore()

const STRICT_PROTOCOL_UNIQUENESS = true

const sourceTarget = ref(null)
const sourceProfiles = ref([])
const sourceProfilesLoaded = ref(false)
const isLoadingSourceProfiles = ref(false)
const sourceId = ref(null)
const sourceLoaded = ref(false)
const sourceProtocolCollision = ref(null)
const isSubmitting = ref(false)

const formData = ref({
  port: null,
  protocol: null,
  username: '',
  password: '',
})

const existingProtocols = ref(new Set())
const isLoadingProtocols = ref(false)

const { protocolButtons, getDefaultPort } = useConnectionForm({
  existingProtocols,
})

const hasTarget = computed(() => !!sourceTarget.value?.id)
const hasSource = computed(() => !!sourceId.value && sourceLoaded.value)
const hasProtocol = computed(() => !!formData.value.protocol)

const noProfilesAvailable = computed(
  () =>
    hasTarget.value &&
    sourceProfilesLoaded.value &&
    sourceProfiles.value.length === 0,
)

const showProfilePicker = computed(
  () =>
    hasTarget.value &&
    sourceProfilesLoaded.value &&
    sourceProfiles.value.length > 1,
)

const currentStep = computed(() => {
  if (!hasSource.value) return 1
  if (!hasProtocol.value) return 2
  return 3
})

const isUsernameValid = computed(() => {
  const pattern = mainStore.settings?.connection?.profiles?.username?.regex
  if (!pattern) return true
  return new RegExp(pattern).test(formData.value.username || '')
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

function reset() {
  sourceTarget.value = null
  sourceProfiles.value = []
  sourceProfilesLoaded.value = false
  isLoadingSourceProfiles.value = false
  sourceId.value = null
  sourceLoaded.value = false
  sourceProtocolCollision.value = null
  isSubmitting.value = false
  formData.value = { port: null, protocol: null, username: '', password: '' }
  existingProtocols.value = new Set()
}

function selectProtocol(value) {
  if (!hasSource.value) return
  if (isLoadingProtocols.value) return
  if (existingProtocols.value.has(value) && STRICT_PROTOCOL_UNIQUENESS) return
  formData.value.protocol = value
}

async function loadExistingProtocols() {
  existingProtocols.value = new Set()
  isLoadingProtocols.value = true
  try {
    const list = await backend.connections.listByObject(
      props.targetObjectType,
      props.targetObjectId,
      { page: 1, limit: 200 },
    )
    existingProtocols.value = new Set(
      (list?.items || []).map((p) => p.protocol).filter(Boolean),
    )
  } catch {
    existingProtocols.value = new Set()
  } finally {
    isLoadingProtocols.value = false
  }
}

async function loadSourceProfilesForTarget(target) {
  sourceProfiles.value = []
  sourceProfilesLoaded.value = false
  sourceId.value = null
  sourceLoaded.value = false
  sourceProtocolCollision.value = null
  formData.value = { port: null, protocol: null, username: '', password: '' }
  if (!target?.id || !target?.type) return

  isLoadingSourceProfiles.value = true
  try {
    const list = await backend.connections.listByObject(
      target.type,
      target.id,
      { page: 1, limit: 200 },
    )
    sourceProfiles.value = list?.items ?? []
    sourceProfilesLoaded.value = true
    if (sourceProfiles.value.length === 1) {
      sourceId.value = sourceProfiles.value[0].id
    }
  } catch {
    sourceProfiles.value = []
    sourceProfilesLoaded.value = true
  } finally {
    isLoadingSourceProfiles.value = false
  }
}

async function loadSourceProfile(id) {
  sourceLoaded.value = false
  sourceProtocolCollision.value = null
  if (!id) return
  try {
    const source = await backend.connections.get(id)
    const collides =
      !!source.protocol &&
      existingProtocols.value.has(source.protocol) &&
      STRICT_PROTOCOL_UNIQUENESS
    sourceProtocolCollision.value = collides ? source.protocol : null
    formData.value.protocol = collides ? null : (source.protocol ?? null)
    formData.value.port = source.port ?? getDefaultPort(source.protocol) ?? null
    formData.value.username = source.username ?? ''
    formData.value.password = ''
    sourceLoaded.value = true
  } catch {
    sourceId.value = null
    sourceLoaded.value = false
    sourceProtocolCollision.value = null
    toast.error(t('views.connections.import.sourceLoadError'))
  }
}

function profileLabel(profile) {
  const proto = String(profile.protocol ?? '').toUpperCase() || '–'
  const user = profile.username || '–'
  const port = profile.port ?? '–'
  return `[${proto}] ${user}:${port}`
}

function onTargetSearchStarted() {
  sourceTarget.value = null
  sourceProfiles.value = []
  sourceProfilesLoaded.value = false
  sourceId.value = null
  sourceLoaded.value = false
  sourceProtocolCollision.value = null
  formData.value = { port: null, protocol: null, username: '', password: '' }
}

async function submit() {
  if (!hasSource.value || !hasProtocol.value || !isUsernameValid.value) return
  if (
    existingProtocols.value.has(formData.value.protocol) &&
    STRICT_PROTOCOL_UNIQUENESS
  ) {
    return
  }

  isSubmitting.value = true
  backend.beginSilent()
  try {
    await backend.connections.clone(sourceId.value, {
      objectId: props.targetObjectId,
      objectType: props.targetObjectType,
      port: formData.value.port,
      protocol: formData.value.protocol,
      username: formData.value.username,
      password: formData.value.password,
    })
    toast.success(t('views.connections.import.success'))
    emit('imported')
    emit('update:modelValue', false)
  } catch (error) {
    toast.error(
      `${t('common.cloneError', { entity: t('objectTypes.guacamoleConnectionProfile.singular') })}\n${error?.response?.data?.detail ?? t('common.unknownError')}`,
      { timeout: 8400 },
    )
  } finally {
    backend.endSilent()
    isSubmitting.value = false
  }
}

watch(
  () => props.modelValue,
  async (open) => {
    if (open) {
      reset()
      await loadExistingProtocols()
    }
  },
)

watch(sourceTarget, async (target) => {
  await loadSourceProfilesForTarget(target)
})

watch(sourceId, async (id) => {
  if (id) {
    await loadSourceProfile(id)
  } else {
    sourceLoaded.value = false
  }
})

watch(
  () => formData.value.protocol,
  (protocol) => {
    if (protocol) {
      const fallbackPort = getDefaultPort(protocol)
      if (!formData.value.port && fallbackPort) {
        formData.value.port = fallbackPort
      }
    }
  },
)

const submitDisabled = computed(
  () =>
    isSubmitting.value ||
    currentStep.value < 3 ||
    !isUsernameValid.value ||
    !formData.value.port,
)
</script>

<template>
  <CardBoxModal
    :model-value="modelValue"
    :title="$t('views.connections.import.title')"
    :button-label="$t('views.connections.import.submitLabel')"
    button="info"
    has-cancel
    has-search
    custom-class="md:!w-4/5 lg:!w-3/5 xl:!w-1/2"
    :disabled="submitDisabled"
    @update:model-value="emit('update:modelValue', $event)"
    @form-submitted="submit"
  >
    <!-- Step 1: Pick source target + profile -->
    <div class="mb-2">
      <div class="mb-3 flex items-center gap-2">
        <BaseIcon
          :path="mdiNumeric1Circle"
          :size="24"
          :class="
            hasSource
              ? 'text-green-600 dark:text-green-400'
              : 'text-blue-600 dark:text-blue-400'
          "
        />

        <span class="font-medium">{{
          $t('views.connections.import.selectSource')
        }}</span>

        <BaseIcon
          v-if="hasSource"
          :path="mdiCheck"
          :size="18"
          class="text-green-600 dark:text-green-400"
        />
      </div>

      <SearchControl
        v-model="sourceTarget"
        return-attribute="ident"
        :icon="mdiMonitor"
        :fetch-data="backend.vms.searchVMsAndTemplates"
        :fetch-selected="backend.vms.getVMOrTemplateName"
        :placeholder="$t('views.connections.import.searchPlaceholder')"
        :autofocus="true"
        @input-started="onTargetSearchStarted"
      />

      <div
        v-if="noProfilesAvailable"
        class="mt-3 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-700/50 dark:bg-amber-900/30 dark:text-amber-200"
      >
        <BaseIcon :path="mdiAlertCircleOutline" :size="20" class="flex-none" />

        <p class="leading-snug">
          {{ $t('views.connections.import.noProfilesAvailable') }}
        </p>
      </div>

      <div
        v-else-if="showProfilePicker"
        class="mt-3 space-y-1 rounded-lg border border-gray-200 dark:border-gray-700 p-2 bg-gray-50 dark:bg-slate-800/50"
      >
        <p
          class="px-1 pb-1 text-xs font-medium text-gray-700 dark:text-gray-200"
        >
          {{ $t('views.connections.import.pickProfile') }}
        </p>

        <label
          v-for="profile in sourceProfiles"
          :key="profile.id"
          class="flex cursor-pointer items-center gap-2 rounded px-2 py-1 text-sm hover:bg-white dark:hover:bg-slate-700/40"
          :class="{
            'bg-white dark:bg-slate-700/60': sourceId === profile.id,
          }"
        >
          <input
            v-model="sourceId"
            type="radio"
            :value="profile.id"
            class="accent-blue-600"
          />

          <span class="font-mono text-gray-900 dark:text-gray-100">{{
            profileLabel(profile)
          }}</span>
        </label>
      </div>
    </div>

    <div
      v-if="sourceProtocolCollision"
      class="mb-2 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-700/50 dark:bg-amber-900/30 dark:text-amber-200"
    >
      <BaseIcon :path="mdiAlertCircleOutline" :size="20" class="flex-none" />

      <p class="leading-snug">
        {{
          $t('views.connections.import.protocolCollision', {
            protocol: sourceProtocolCollision.toUpperCase(),
          })
        }}
      </p>
    </div>

    <!-- Step 2: Protocol/Port -->
    <div class="mb-2">
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
          :class="currentStep < 2 ? 'text-gray-400 dark:text-slate-500' : ''"
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

      <div
        class="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4"
        :class="{ 'pointer-events-none opacity-40': !hasSource }"
      >
        <button
          v-for="p in protocolButtons"
          :key="p.value"
          type="button"
          class="relative flex flex-col items-center rounded-xl border-2 p-3 transition-all"
          :class="[
            formData.protocol === p.value
              ? 'border-blue-500 bg-blue-50 dark:border-blue-400 dark:bg-blue-900/30'
              : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50 dark:border-slate-600 dark:bg-slate-800 dark:hover:border-slate-500 dark:hover:bg-slate-700',
            p.disabled && STRICT_PROTOCOL_UNIQUENESS
              ? 'cursor-not-allowed opacity-40'
              : 'cursor-pointer',
          ]"
          :disabled="
            (p.disabled && STRICT_PROTOCOL_UNIQUENESS) ||
            isLoadingProtocols ||
            !hasSource
          "
          @click="selectProtocol(p.value)"
        >
          <BaseIcon
            :path="p.icon"
            :size="24"
            :class="
              formData.protocol === p.value
                ? 'text-blue-600 dark:text-blue-400'
                : 'text-gray-500 dark:text-slate-400'
            "
          />

          <span
            class="mt-1 text-sm font-semibold"
            :class="
              formData.protocol === p.value
                ? 'text-blue-700 dark:text-blue-300'
                : 'text-gray-700 dark:text-slate-200'
            "
          >
            {{ p.label }}
          </span>

          <span
            class="mt-0.5 text-xs"
            :class="
              formData.protocol === p.value
                ? 'text-blue-600 dark:text-blue-400'
                : 'text-gray-400 dark:text-slate-500'
            "
          >
            {{
              STRICT_PROTOCOL_UNIQUENESS && p.disabled
                ? $t('views.connections.clone.alreadyAssigned')
                : `Port ${p.port}`
            }}
          </span>

          <div
            v-if="formData.protocol === p.value"
            class="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-blue-500 dark:bg-blue-400"
          >
            <BaseIcon :path="mdiCheck" :size="14" class="text-white" />
          </div>
        </button>
      </div>

      <div :class="{ 'pointer-events-none opacity-40': !hasSource }">
        <FormField
          :label="$t('common.port')"
          :help="$t('views.connections.clone.portCanBeAdjusted')"
        >
          <FormControl
            v-model="formData.port"
            :icon="mdiNetwork"
            type="number"
            :disabled="!hasSource"
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
          :class="currentStep < 3 ? 'text-gray-400 dark:text-slate-500' : ''"
        >
          {{ $t('views.connections.clone.vmCredentials') }}
        </span>
      </div>

      <div :class="{ 'pointer-events-none opacity-40': currentStep < 3 }">
        <FormField
          :label="$t('common.username')"
          :help="$t('views.connections.clone.localUserWithinVm')"
        >
          <FormControl
            v-model="formData.username"
            :icon="mdiAccountBox"
            :maxlength="FIELD_LIMITS.connectionprofile.username"
            :placeholder="$t('views.connections.clone.exampleUsername')"
            :disabled="currentStep < 3"
            :validate="validateUsername"
            required
          />
        </FormField>

        <FormField
          :label="$t('common.password')"
          :help="$t('views.connections.clone.leaveEmptyForSourcePassword')"
        >
          <FormControl
            v-model="formData.password"
            :icon="mdiKey"
            type="password"
            :maxlength="FIELD_LIMITS.connectionprofile.password"
            :placeholder="$t('views.connections.clone.keepSourcePassword')"
            :disabled="currentStep < 3"
          />
        </FormField>
      </div>
    </div>
  </CardBoxModal>
</template>
