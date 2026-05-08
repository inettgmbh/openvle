<script setup>
import {
  mdiAccountMultipleOutline,
  mdiKey,
  mdiRename,
  mdiTextBox,
} from '@mdi/js'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
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
import { useMainStore } from '@/stores/main'

const { t } = useI18n()
const route = useRoute()
const toast = useToast()

const role = ref({})

const {
  showDiscardModal,
  setOriginal,
  markAsSaved,
  handleCancel,
  confirmDiscard,
  cancelDiscard,
} = useUnsavedChanges({
  formData: role,
  onNavigateAway: () => router.back(),
})

async function submit() {
  try {
    const res = await backend.roles.create({
      name: role.value.name,
      key: role.value.key,
      description: role.value.description,
      protected: false,
    })
    toast.success(
      t('common.createSuccess', { entity: t('objectTypes.role.singular') }),
    )
    useMainStore().fetchPermissions()
    markAsSaved()
    router.push({ path: `/roles/${res.id}` })
  } catch (error) {
    toast.error(
      t('common.createError', { entity: t('objectTypes.role.singular') }),
    )
  }
}

const submitTooltip = computed(() => {
  if (
    role.value?.name?.toLowerCase() === 'studierende' ||
    role.value?.name?.toLowerCase() === 'lehrende'
  ) {
    return t('views.roles.form.reservedNameTooltip')
  }
  return undefined
})

const submitDisabled = computed(() => {
  if (
    role.value?.name?.toLowerCase() === 'studierende' ||
    role.value?.name?.toLowerCase() === 'lehrende'
  ) {
    return true
  }
  return false
})

function onCancel() {
  if (handleCancel()) router.back()
}

onMounted(() => {
  role.value.name = route.query.name
  role.value.description = route.query.description
  setOriginal()
})

role.value.key = computed(() =>
  role.value.name
    ? role.value.name.toLowerCase().replace(/[^a-z0-9]+/g, '_')
    : '',
)
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiAccountMultipleOutline"
        :title="
          $t('common.createTitle', { entity: $t('objectTypes.role.singular') })
        "
        main
        docs-path="/docs/usage/openvle/access-control/roles/"
      />

      <CardBox is-form @submit.prevent="submit">
        <FormField
          :label="$t('common.name')"
          :help="$t('views.roles.form.nameHelp')"
        >
          <FormControl
            v-model="role.name"
            :icon="mdiRename"
            :placeholder="$t('views.roles.form.namePlaceholder')"
            required
          />
        </FormField>

        <FormField
          label="Key (Slug)"
          :help="$t('views.roles.form.keyHelp')"
          :tooltip="$t('views.roles.form.keyTooltip')"
        >
          <FormControl
            v-model="role.key"
            :icon="mdiKey"
            :placeholder="$t('views.roles.form.keyPlaceholder')"
            required
            readonly
          />
        </FormField>

        <FormField
          :label="$t('common.description')"
          :help="$t('views.roles.form.descriptionHelp')"
        >
          <FormControl v-model="role.description" :icon="mdiTextBox" />
        </FormField>

        <template #footer>
          <BaseButtons>
            <BaseButton
              v-tooltip="submitTooltip"
              :disabled="submitDisabled"
              type="submit"
              color="info"
              :label="$t('common.add')"
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
