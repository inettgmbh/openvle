<script setup>
import { mdiDomain, mdiRename, mdiTextBox } from '@mdi/js'
import { onMounted, ref } from 'vue'
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

const vendor = ref({})

const {
  showDiscardModal,
  setOriginal,
  markAsSaved,
  handleCancel,
  confirmDiscard,
  cancelDiscard,
} = useUnsavedChanges({
  formData: vendor,
  onNavigateAway: () => router.back(),
})

async function submit() {
  try {
    const res = await backend.vendors.create({
      name: vendor.value.name,
      description: vendor.value.description,
    })
    toast.success(
      t('common.createSuccess', { entity: t('objectTypes.vendor.singular') }),
    )
    useMainStore().fetchPermissions()
    markAsSaved()
    router.push({ path: `/vendors/${res.id}` })
  } catch (error) {
    toast.error(
      t('common.createError', { entity: t('objectTypes.vendor.singular') }),
    )
  }
}

function onCancel() {
  if (handleCancel()) router.back()
}

onMounted(() => {
  vendor.value.description = route.query.description
  vendor.value.name = route.query.name
  setOriginal()
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiDomain"
        :title="
          $t('common.createTitle', {
            entity: $t('objectTypes.vendor.singular'),
          })
        "
        main
        docs-path="/docs/usage/openvle/infrastructure/vendors/"
      />

      <CardBox is-form @submit.prevent="submit">
        <FormField
          :label="$t('common.name')"
          :help="$t('views.vendors.form.nameHelp')"
        >
          <FormControl
            v-model="vendor.name"
            :icon="mdiRename"
            :placeholder="$t('views.vendors.form.namePlaceholder')"
            required
          />
        </FormField>

        <FormField
          :label="$t('common.description')"
          :help="$t('views.vendors.form.descriptionHelp')"
        >
          <FormControl v-model="vendor.description" :icon="mdiTextBox" />
        </FormField>

        <template #footer>
          <BaseButtons>
            <BaseButton type="submit" color="info" :label="$t('common.add')" />

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
