<script setup>
import { mdiCheck, mdiCloudLockOutline, mdiRename, mdiTextBox } from '@mdi/js'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
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
import { userStatusLabel } from '@/utils/dataUtils'

const provider = ref({})
const route = useRoute()
const toast = useToast()
const { t } = useI18n()

const statusOptions = [
  { label: userStatusLabel('Active'), value: 'Active' },
  { label: userStatusLabel('Inactive'), value: 'Inactive' },
  { label: userStatusLabel('Banned'), value: 'Banned' },
  { label: userStatusLabel('E-Mail-Pending'), value: 'E-Mail-Pending' },
]

const {
  showDiscardModal,
  setOriginal,
  markAsSaved,
  handleCancel,
  confirmDiscard,
  cancelDiscard,
} = useUnsavedChanges({
  formData: provider,
  onNavigateAway: () => router.back(),
})

async function fetchProvider(id) {
  try {
    provider.value = await backend.scimProviders.get(id)
    setOriginal()
  } catch (error) {
    toast.error(
      t('common.editError', { entity: t('objectTypes.scimProvider.singular') }),
    )
  }
}
fetchProvider(route.params.id)

async function submit() {
  try {
    await backend.scimProviders.update(provider.value.id, {
      name: provider.value.name,
      description: provider.value.description,
      enabled: provider.value.enabled,
      default_user_status: provider.value.default_user_status,
    })
    toast.success(
      t('common.editSuccess', {
        entity: t('objectTypes.scimProvider.singular'),
      }),
    )
    markAsSaved()
    router.push({ path: `/scim/providers/${provider.value.id}` })
  } catch (error) {
    toast.error(
      t('common.editError', { entity: t('objectTypes.scimProvider.singular') }),
    )
  }
}

const submitDisabled = computed(() => !provider.value.name?.trim())

function onCancel() {
  if (handleCancel()) router.back()
}
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiCloudLockOutline"
        :title="
          $t('common.editTitle', {
            entity: $t('objectTypes.scimProvider.singular'),
          })
        "
        main
      />

      <CardBox is-form @submit.prevent="submit">
        <FormField
          :label="$t('common.name')"
          :help="$t('views.scimProviders.form.nameHelp')"
        >
          <FormControl
            v-model="provider.name"
            :icon="mdiRename"
            :placeholder="$t('views.scimProviders.form.name')"
            required
            :validate="true"
          />
        </FormField>

        <FormField
          :label="$t('common.description')"
          :help="$t('views.scimProviders.edit.descriptionKeepExisting')"
        >
          <FormControl v-model="provider.description" :icon="mdiTextBox" />
        </FormField>

        <FormField
          :label="$t('views.scimProviders.form.enabled')"
          :help="$t('views.scimProviders.form.enableDisableHelp')"
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
                provider.enabled === opt.value
                  ? 'border-blue-500 bg-blue-50 text-blue-700 dark:border-blue-400 dark:bg-blue-900/30 dark:text-blue-300'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:bg-gray-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-slate-500 dark:hover:bg-slate-700'
              "
              @click="provider.enabled = opt.value"
            >
              {{ opt.label }}
              <div
                v-if="provider.enabled === opt.value"
                class="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-blue-500 dark:bg-blue-400"
              >
                <BaseIcon :path="mdiCheck" :size="14" class="text-white" />
              </div>
            </button>
          </div>
        </FormField>

        <FormField
          :label="$t('views.scimProviders.form.defaultUserStatus')"
          :help="$t('views.scimProviders.form.defaultUserStatusHelp')"
        >
          <div class="grid grid-cols-3 gap-3">
            <button
              v-for="option in statusOptions"
              :key="option.value"
              type="button"
              class="relative flex items-center justify-center rounded-xl border-2 p-3 text-sm font-semibold transition-all"
              :class="
                provider.default_user_status === option.value
                  ? 'border-blue-500 bg-blue-50 text-blue-700 dark:border-blue-400 dark:bg-blue-900/30 dark:text-blue-300'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:bg-gray-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-slate-500 dark:hover:bg-slate-700'
              "
              @click="provider.default_user_status = option.value"
            >
              {{ option.label }}
              <div
                v-if="provider.default_user_status === option.value"
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
              :label="$t('common.save')"
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
