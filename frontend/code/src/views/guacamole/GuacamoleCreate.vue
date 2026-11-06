<script setup>
import {
  mdiAccountBox,
  mdiCheck,
  mdiMonitor,
  mdiRemoteDesktop,
  mdiRename,
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
import SearchControl from '@/components/SearchControl.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import UnsavedChangesModal from '@/components/UnsavedChangesModal.vue'
import { protocolConfig } from '@/composables/useConnectionForm'
import { useUnsavedChanges } from '@/composables/useUnsavedChanges'
import { FIELD_LIMITS } from '@/config/fieldLimits'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import router from '@/router'
import backend from '@/services'
import { useMainStore } from '@/stores/main'

const guacamole = ref({})
const route = useRoute()
const toast = useToast()
const { t } = useI18n()

const selectedVm = ref(null)
const connections = ref([])
const noConnectionsError = ref(false)
const loadingConnections = ref(false)

const validateName = (value) => {
  if (!value?.trim()) return t('components.formControl.fieldRequired')
  return true
}

const canSubmit = computed(
  () =>
    !!guacamole.value.name?.trim() &&
    !!guacamole.value.userId &&
    !!selectedVm.value &&
    !!guacamole.value.connection_profile,
)

const {
  showDiscardModal,
  setOriginal,
  markAsSaved,
  handleCancel,
  confirmDiscard,
  cancelDiscard,
} = useUnsavedChanges({
  formData: guacamole,
  onNavigateAway: () => router.back(),
})

async function fetchConnectionsForVM(vmId) {
  loadingConnections.value = true
  noConnectionsError.value = false
  connections.value = []

  try {
    const response = await backend.connections.listByObject(
      'VirtualMachine',
      vmId,
      { limit: 100 },
    )
    const items = response.items || []

    connections.value = items.map((item) => {
      const config = protocolConfig[item.protocol] || {}
      return {
        id: item.id,
        protocol: item.protocol,
        label: config.label || item.protocol?.toUpperCase(),
        description: config.description || '',
        icon: config.icon || mdiMonitor,
        port: item.port,
        username: item.username,
      }
    })

    if (items.length === 0) {
      noConnectionsError.value = true
    } else if (items.length === 1) {
      guacamole.value.connection_profile = items[0].id
    }
  } finally {
    loadingConnections.value = false
  }
}

watch(selectedVm, (vmId) => {
  guacamole.value.connection_profile = null
  connections.value = []
  noConnectionsError.value = false

  if (vmId) {
    fetchConnectionsForVM(vmId)
  }
})

async function submit() {
  try {
    const res = await backend.guacamole.create({
      name: guacamole.value.name,
      userId: guacamole.value.userId,
      connection_profile: guacamole.value.connection_profile,
    })
    toast.success(
      t('common.createSuccess', {
        entity: t('objectTypes.guacamole.singular'),
      }),
    )
    useMainStore().fetchPermissions()
    markAsSaved()
    router.push({ path: `/guacamoles/${res.id}` })
  } catch (error) {
    toast.error(
      'Verbindung konnte nicht angelegt werden:\n' +
        error?.response?.data?.detail,
    )
  }
}

function onCancel() {
  if (handleCancel()) router.back()
}

onMounted(async () => {
  guacamole.value.name = route.query.name
  guacamole.value.userId = route.query.userId

  if (route.query.vmId) {
    // Pre-select VM from query parameter
    selectedVm.value = route.query.vmId
  } else if (route.query.connection_profile) {
    // Backwards compatibility: resolve VM from connection profile
    try {
      const profile = await backend.connections.get(
        route.query.connection_profile,
      )
      if (profile?.objectId) {
        selectedVm.value = profile.objectId
      }
    } catch {
      // Profile not found, ignore
    }
  }

  setOriginal()
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiRemoteDesktop"
        :title="
          $t('common.createTitle', {
            entity: $t('objectTypes.guacamole.singular'),
          })
        "
        main
        docs-path="/docs/usage/openvle/connections/"
      />

      <CardBox is-form @submit.prevent="submit">
        <FormField
          :label="$t('common.name')"
          :help="$t('views.guacamole.form.nameHelp')"
          tooltip="Dieser Name wird dem Nutzenden genauso angezeigt – er sollte daher aussagekräftig sein"
        >
          <FormControl
            v-model="guacamole.name"
            :icon="mdiRename"
            :maxlength="FIELD_LIMITS.guacamole.name"
            :placeholder="$t('views.guacamole.form.namePlaceholder')"
            :validate="validateName"
            :autofocus="true"
            required
          />
        </FormField>

        <FormField
          :label="$t('views.guacamole.form.user')"
          :help="$t('views.guacamole.form.selectUserHelp')"
        >
          <SearchControl
            v-model="guacamole.userId"
            :icon="mdiAccountBox"
            :fetch-data="backend.users.search"
            :fetch-selected="backend.users.formatById"
            required
          />
        </FormField>

        <!-- Step 2: Select VM -->
        <FormField
          :label="$t('objectTypes.virtualMachine.singular')"
          :help="$t('views.guacamole.form.vmHelp')"
        >
          <SearchControl
            v-model="selectedVm"
            :icon="mdiMonitor"
            :fetch-data="backend.vms.search"
            :fetch-selected="backend.vms.getName"
            required
          />
        </FormField>

        <!-- Step 3: Select connection profile -->
        <FormField
          v-if="selectedVm && connections.length > 0"
          :label="$t('views.guacamole.form.connectionTemplate')"
          :help="$t('views.guacamole.form.selectTemplateHelp')"
        >
          <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <button
              v-for="c in connections"
              :key="c.id"
              type="button"
              class="relative flex flex-col items-center rounded-xl border-2 p-4 transition-all"
              :class="[
                guacamole.connection_profile === c.id
                  ? 'border-blue-500 bg-blue-50 dark:border-blue-400 dark:bg-blue-900/30'
                  : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50 dark:border-slate-600 dark:bg-slate-800 dark:hover:border-slate-500 dark:hover:bg-slate-700',
                connections.length === 1 ? 'cursor-default' : 'cursor-pointer',
              ]"
              @click="guacamole.connection_profile = c.id"
            >
              <BaseIcon
                :path="c.icon"
                :size="28"
                :class="
                  guacamole.connection_profile === c.id
                    ? 'text-blue-600 dark:text-blue-400'
                    : 'text-gray-500 dark:text-slate-400'
                "
              />

              <span
                class="mt-2 text-sm font-semibold"
                :class="
                  guacamole.connection_profile === c.id
                    ? 'text-blue-700 dark:text-blue-300'
                    : 'text-gray-700 dark:text-slate-200'
                "
              >
                {{ c.label }}
              </span>

              <span
                class="mt-0.5 text-xs"
                :class="
                  guacamole.connection_profile === c.id
                    ? 'text-blue-600 dark:text-blue-400'
                    : 'text-gray-400 dark:text-slate-500'
                "
              >
                Port {{ c.port }}
              </span>

              <!-- Selection indicator -->
              <div
                v-if="guacamole.connection_profile === c.id"
                class="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-blue-500 dark:bg-blue-400"
              >
                <BaseIcon :path="mdiCheck" :size="14" class="text-white" />
              </div>
            </button>
          </div>
        </FormField>

        <div
          v-if="noConnectionsError"
          class="text-red-500 dark:text-red-400 text-sm px-3 py-2"
        >
          {{ $t('views.guacamole.form.noConnectionProfiles') }}
        </div>

        <template #footer>
          <BaseButtons>
            <BaseButton
              type="submit"
              color="info"
              :label="$t('common.add')"
              :disabled="!canSubmit"
            />

            <BaseButton
              type="button"
              color="info"
              :label="$t('common.cancel')"
              outline
              @click="onCancel"
            />
          </BaseButtons>
        </template>
      </CardBox>

      <UnsavedChangesModal
        v-model="showDiscardModal"
        @discard="confirmDiscard"
        @continue="cancelDiscard"
      />
    </SectionMain>
  </LayoutAuthenticated>
</template>
