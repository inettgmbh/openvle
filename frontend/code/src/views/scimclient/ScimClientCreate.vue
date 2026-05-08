<script setup>
import {
  mdiCheck,
  mdiCloudSyncOutline,
  mdiKey,
  mdiLink,
  mdiRename,
  mdiTextBox,
} from '@mdi/js'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseIcon from '@/components/BaseIcon.vue'
import CardBox from '@/components/CardBox.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import UnsavedChangesModal from '@/components/UnsavedChangesModal.vue'
import { useUnsavedChanges } from '@/composables/useUnsavedChanges'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import router from '@/router'
import backend from '@/services'

const toast = useToast()
const { t } = useI18n()

const client = ref({
  name: '',
  description: '',
  enabled: false,
  endpoint_url: '',
  bearer_token: '',
  sync_groups: false,
})

const {
  showDiscardModal,
  setOriginal,
  markAsSaved,
  handleCancel,
  confirmDiscard,
  cancelDiscard,
} = useUnsavedChanges({
  formData: client,
  onNavigateAway: () => router.back(),
})

function isValidUrl(string) {
  if (!string) return false
  try {
    const url = new URL(string)
    return url.protocol === 'http:' || url.protocol === 'https:'
  } catch {
    return false
  }
}

const validateEndpointUrl = (value) => {
  if (!value?.trim()) return 'Dieses Feld ist erforderlich.'
  if (!isValidUrl(value)) return 'Bitte eine gültige URL eingeben (https://...)'
  return true
}

const submitDisabled = computed(() => {
  if (!client.value.name?.trim()) return true
  if (!client.value.endpoint_url?.trim()) return true
  if (!isValidUrl(client.value.endpoint_url)) return true
  if (!client.value.bearer_token?.trim()) return true
  return false
})

async function submit() {
  try {
    const res = await backend.scimClients.create({
      name: client.value.name,
      description: client.value.description,
      enabled: client.value.enabled,
      endpoint_url: client.value.endpoint_url,
      bearer_token: client.value.bearer_token,
      sync_groups: client.value.sync_groups,
    })
    toast.success(
      t('common.createSuccess', {
        entity: t('objectTypes.scimClient.singular'),
      }),
    )
    markAsSaved()
    router.push({ path: `/scim/clients/${res.id}` })
  } catch (error) {
    toast.error(
      t('common.createError', { entity: t('objectTypes.scimClient.singular') }),
    )
  }
}

function onCancel() {
  if (handleCancel()) router.back()
}

onMounted(() => {
  setOriginal()
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiCloudSyncOutline"
        :title="
          $t('common.createTitle', {
            entity: $t('objectTypes.scimClient.singular'),
          })
        "
        main
      />

      <CardBox is-form @submit.prevent="submit">
        <FormField
          :label="$t('common.name')"
          :help="$t('views.scimClients.form.nameHelp')"
        >
          <FormControl
            v-model="client.name"
            :icon="mdiRename"
            :placeholder="$t('views.scimClients.form.externalLms')"
            required
            :validate="true"
          />
        </FormField>

        <FormField
          :label="$t('common.description')"
          :help="$t('views.scimClients.form.descriptionHelp')"
        >
          <FormControl v-model="client.description" :icon="mdiTextBox" />
        </FormField>

        <FormField
          :label="$t('views.scimClients.form.enabled')"
          :help="$t('views.scimClients.form.enableDisableHelp')"
        >
          <div class="grid grid-cols-2 gap-3">
            <button
              v-for="opt in [
                { label: $t('common.enabled'), value: true },
                { label: $t('common.disabled'), value: false },
              ]"
              :key="opt.label"
              type="button"
              class="relative flex items-center justify-center rounded-xl border-2 p-3 text-sm font-semibold transition-all"
              :class="
                client.enabled === opt.value
                  ? 'border-blue-500 bg-blue-50 text-blue-700 dark:border-blue-400 dark:bg-blue-900/30 dark:text-blue-300'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:bg-gray-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-slate-500 dark:hover:bg-slate-700'
              "
              @click="client.enabled = opt.value"
            >
              {{ opt.label }}
              <div
                v-if="client.enabled === opt.value"
                class="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-blue-500 dark:bg-blue-400"
              >
                <BaseIcon :path="mdiCheck" :size="14" class="text-white" />
              </div>
            </button>
          </div>
        </FormField>

        <FormField
          :label="$t('views.scimClients.form.endpointUrl')"
          :help="$t('views.scimClients.form.endpointUrlHelp')"
        >
          <FormControl
            v-model="client.endpoint_url"
            :icon="mdiLink"
            :placeholder="$t('views.scimClients.form.httpsexamplecomscimv')"
            required
            :validate="validateEndpointUrl"
          />
        </FormField>

        <FormField
          :label="$t('views.scimClients.form.bearerToken')"
          :help="$t('views.scimClients.create.tokenHelp')"
        >
          <FormControl
            v-model="client.bearer_token"
            :icon="mdiKey"
            :placeholder="$t('views.scimClients.form.tokenPlaceholder')"
            required
            :validate="true"
          />
        </FormField>

        <FormField
          :label="$t('views.scimClients.form.roleGroupSync')"
          :help="$t('views.scimClients.form.syncRolesAsGroupsHelp')"
        >
          <div class="grid grid-cols-2 gap-3">
            <button
              v-for="opt in [
                { label: $t('common.yes'), value: true },
                { label: $t('common.no'), value: false },
              ]"
              :key="opt.label"
              type="button"
              class="relative flex items-center justify-center rounded-xl border-2 p-3 text-sm font-semibold transition-all"
              :class="
                client.sync_groups === opt.value
                  ? 'border-blue-500 bg-blue-50 text-blue-700 dark:border-blue-400 dark:bg-blue-900/30 dark:text-blue-300'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:bg-gray-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-slate-500 dark:hover:bg-slate-700'
              "
              @click="client.sync_groups = opt.value"
            >
              {{ opt.label }}
              <div
                v-if="client.sync_groups === opt.value"
                class="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-blue-500 dark:bg-blue-400"
              >
                <BaseIcon :path="mdiCheck" :size="14" class="text-white" />
              </div>
            </button>
          </div>
        </FormField>

        <template #footer>
          <BaseButtons>
            <BaseButton
              type="submit"
              color="info"
              :label="$t('common.add')"
              :disabled="submitDisabled"
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
