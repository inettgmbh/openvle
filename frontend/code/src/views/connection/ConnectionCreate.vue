<script setup>
import {
  mdiAccountBox,
  mdiCheck,
  mdiInformationOutline,
  mdiKey,
  mdiMonitor,
  mdiNetwork,
  mdiNumeric1Circle,
  mdiNumeric2Circle,
  mdiNumeric3Circle,
  mdiRemoteDesktop,
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
import { useConnectionForm } from '@/composables/useConnectionForm'
import { useUnsavedChanges } from '@/composables/useUnsavedChanges'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import router from '@/router'
import backend from '@/services'
import { useMainStore } from '@/stores/main'

const mainStore = useMainStore()
const connection = ref({})
const route = useRoute()
const toast = useToast()
const { t } = useI18n()

const existingProtocols = ref(new Set())
const isLoadingProtocols = ref(false)
const showInfo = ref(false)

// Toggle to enforce unique protocols per entity.
// When false, duplicate protocols are allowed with a warning.
const STRICT_PROTOCOL_UNIQUENESS = true

const {
  showDiscardModal,
  setOriginal,
  markAsSaved,
  handleCancel,
  confirmDiscard,
  cancelDiscard,
} = useUnsavedChanges({
  formData: connection,
  onNavigateAway: () => router.back(),
})

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
      toast.info(t('views.connections.form.protocolAlreadyAssigned'))
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
        connection.value.port = null
      }
      toast.info(
        'Für dieses Objekt existiert bereits eine Verbindungsvorlage mit diesem Protokoll',
        {
          timeout: 2400,
        },
      )
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
      toast.error(
        'Für dieses Objekt existiert bereits eine Verbindungsvorlage mit diesem Protokoll',
      )
      return false
    }
  }

  return true
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
      'Ungültiges Format'
    )
  }
  return true
}

async function submit() {
  if (!validateProtocolUniqueness()) return

  try {
    const res = await backend.connections.create({
      port: connection.value.port,
      protocol: connection.value.protocol,
      username: connection.value.username,
      password: connection.value.password,
      objectId: connection.value.entity.id,
      objectType: connection.value.entity.type,
    })
    toast.success(
      t('common.createSuccess', {
        entity: t('objectTypes.guacamoleConnectionProfile.singular'),
      }),
    )
    mainStore.fetchPermissions()
    markAsSaved()
    router.push({ path: `/connections/${res.id}` })
  } catch (error) {
    toast.error(
      t('common.createError', {
        entity: t('objectTypes.guacamoleConnectionProfile.singular'),
      }),
    )
  }
}

function onVMSearchStarted() {
  connection.value.entity = null
  connection.value.protocol = null
  connection.value.port = null
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

function onCancel() {
  if (handleCancel()) router.back()
}

onMounted(async () => {
  connection.value.port = route.query.port || null
  connection.value.protocol = route.query.protocol || null
  connection.value.username = route.query.username || null

  if (route.query.entityId && route.query.entityType) {
    connection.value.entity = {
      id: route.query.entityId,
      type: route.query.entityType,
    }
    await loadExistingProtocols()
  } else {
    connection.value.entity = null
  }

  if (
    connection.value.protocol &&
    existingProtocols.value.has(connection.value.protocol)
  ) {
    if (STRICT_PROTOCOL_UNIQUENESS) {
      connection.value.protocol = null
      connection.value.port = null
    }
    toast.info(
      'Das Protokoll aus der URL ist für dieses Objekt bereits vergeben',
    )
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
            entity: $t('objectTypes.guacamoleConnectionProfile.singular'),
          })
        "
        main
        docs-path="/docs/usage/openvle/connections/"
      />

      <CardBox is-form @submit.prevent="submit">
        <!-- Info banner -->
        <div
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
                Verbindungsvorlagen definieren Zugangsdaten für VMs und werden
                bei der VM-Erstellung vererbt.
                <button
                  type="button"
                  class="ml-1 font-medium underline hover:no-underline"
                  @click="showInfo = !showInfo"
                >
                  {{ showInfo ? 'Weniger' : 'Mehr erfahren' }}
                </button>
              </p>

              <div
                v-if="showInfo"
                class="mt-2 space-y-1 text-sm text-blue-700 dark:text-blue-300"
              >
                <p>
                  • Jede Verbindungsvorlage ist <b>1:1</b> einer VM oder
                  VM-Vorlage zugeordnet
                </p>

                <p>
                  • Kann beliebig vielen Benutzern zugewiesen werden
                  <b>(1:n)</b>
                </p>

                <p>• Wird von VM-Vorlagen auf erstellte VMs <b>vererbt</b></p>

                <p class="pt-1 italic">
                  Empfehlung: Verbindungsvorlagen auf Ebene der VM-Vorlage
                  anlegen
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 1: Select VM -->
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

            <span class="font-medium">VM oder VM-Vorlage auswählen</span>

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
            :placeholder="$t('views.connections.form.searchByName')"
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
              Protokoll & Port
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
                    ? 'Bereits vergeben'
                    : `Port ${p.port}`
                }}

                <i v-if="p.disabled && !STRICT_PROTOCOL_UNIQUENESS">
                  (bereits vorhanden)
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
              :help="$t('views.connections.form.defaultPortCanBeAdjusted')"
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
              Zugangsdaten der VM
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
                :help="$t('views.connections.form.localUserWithinVm')"
              >
                <FormControl
                  v-model="connection.username"
                  :icon="mdiAccountBox"
                  :placeholder="$t('views.connections.form.exampleUsername')"
                  :disabled="currentStep < 3"
                  :validate="validateUsername"
                  required
                />
              </FormField>

              <FormField
                :label="$t('common.password')"
                :help="$t('views.connections.form.hiddenAfterSave')"
              >
                <FormControl
                  v-model="connection.password"
                  :icon="mdiKey"
                  type="password"
                  placeholder="••••••••"
                  :disabled="currentStep < 3"
                  required
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
              :label="
                $t('common.createTitle', {
                  entity: $t('objectTypes.guacamoleConnectionProfile.singular'),
                })
              "
              :disabled="
                currentStep < 3 || !isUsernameValid || !connection.password
              "
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
