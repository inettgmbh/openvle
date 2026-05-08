<script setup>
import { mdiDomain, mdiRename, mdiTextBox } from '@mdi/js'
import { ref } from 'vue'
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
import { useLookupStore } from '@/stores/lookup'

const vendor = ref({})
const route = useRoute()
const toast = useToast()
const { t } = useI18n()

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

async function fetchVendor(vendorId) {
  try {
    vendor.value = await backend.vendors.get(vendorId)
    setOriginal()
  } catch (error) {
    toast.error(
      t('common.loadError', { entity: t('objectTypes.vendor.singular') }),
    )
  }
}
fetchVendor(route.params.id)

async function submit() {
  try {
    const res = await backend.vendors.update(vendor.value.id, {
      name: vendor.value.name,
      description: vendor.value.description,
    })
    toast.success(
      t('common.editSuccess', { entity: t('objectTypes.vendor.singular') }),
    )
    useLookupStore().updateFromObject('vendors', res)
    markAsSaved()
    router.push({ path: `/vendors/${vendor.value.id}` })
  } catch (error) {
    toast.error(
      t('common.editError', { entity: t('objectTypes.vendor.singular') }),
    )
  }
}

function onCancel() {
  if (handleCancel()) router.back()
}
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiDomain"
        :title="
          $t('common.editTitle', { entity: $t('objectTypes.vendor.singular') })
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
            <BaseButton type="submit" color="info" :label="$t('common.save')" />

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
