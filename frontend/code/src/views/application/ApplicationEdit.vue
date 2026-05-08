<script setup>
import { mdiDomain, mdiKey, mdiPlus, mdiRename, mdiTextBox } from '@mdi/js'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import CardBox from '@/components/CardBox.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import SearchControl from '@/components/SearchControl.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import UnsavedChangesModal from '@/components/UnsavedChangesModal.vue'
import VendorCreateModal from '@/components/VendorCreateModal.vue'
import { useUnsavedChanges } from '@/composables/useUnsavedChanges'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import router from '@/router'
import backend from '@/services'
import { checkObjectPermissions, usePermissionRefs } from '@/utils/dataUtils'

const { t } = useI18n()
const application = ref({})
const route = useRoute()
const toast = useToast()
const permissionRefs = usePermissionRefs()
const vendorSearchRef = ref(null)
const showVendorCreateModal = ref(false)

const {
  showDiscardModal,
  setOriginal,
  markAsSaved,
  handleCancel,
  confirmDiscard,
  cancelDiscard,
} = useUnsavedChanges({
  formData: application,
  onNavigateAway: () => router.back(),
})

async function fetchApplication(applicationId) {
  try {
    application.value = await backend.applications.get(applicationId)
    setOriginal()
  } catch (error) {
    toast.error(
      t('common.loadError', { entity: t('objectTypes.application.singular') }),
    )
  }
}

async function submit() {
  try {
    await backend.applications.update(application.value.id, {
      name: application.value.name,
      description: application.value.description,
      vendor: application.value.vendor,
    })
    toast.success(
      t('common.editSuccess', {
        entity: t('objectTypes.application.singular'),
      }),
    )
    markAsSaved()
    router.push({ path: `/applications/${application.value.id}` })
  } catch (error) {
    toast.error(
      t('common.editError', { entity: t('objectTypes.application.singular') }),
    )
  }
}

function onCancel() {
  if (handleCancel()) router.back()
}

function onVendorCreated({ id, name }) {
  application.value.vendor = id
  vendorSearchRef.value?.setInitialDisplay(name)
  vendorSearchRef.value?.setSelectedId(id)
}

onMounted(async () => {
  fetchApplication(route.params.id)
  await checkObjectPermissions(
    'vendors',
    '*',
    permissionRefs,
    [],
    ['canCreate'],
  )
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiKey"
        :title="
          t('common.editTitle', {
            entity: t('objectTypes.application.singular'),
          })
        "
        main
        docs-path="/docs/usage/openvle/infrastructure/applications/"
      />

      <CardBox is-form @submit.prevent="submit">
        <FormField
          :label="t('common.name')"
          :help="t('views.applications.form.nameHelp')"
        >
          <FormControl
            v-model="application.name"
            :icon="mdiRename"
            :placeholder="$t('views.applications.form.namePlaceholder')"
            required
          />
        </FormField>

        <FormField :label="t('objectTypes.vendor.singular')">
          <div class="flex items-start gap-2">
            <div class="flex-1">
              <SearchControl
                v-model="application.vendor"
                :icon="mdiDomain"
                :fetch-data="backend.vendors.search"
                :fetch-selected="backend.vendors.getName"
                required
                @set-ref="(ref) => (vendorSearchRef = ref)"
              />
            </div>

            <BaseButton
              v-if="permissionRefs.canCreate"
              v-tooltip="t('views.applications.form.createVendorTooltip')"
              :icon="mdiPlus"
              color="info"
              small
              rounded-full
              outline
              type="button"
              class="mt-2 shrink-0"
              @click="showVendorCreateModal = true"
            />
          </div>
        </FormField>

        <FormField
          :label="t('common.description')"
          :help="t('views.applications.form.descriptionHelp')"
        >
          <FormControl v-model="application.description" :icon="mdiTextBox" />
        </FormField>

        <template #footer>
          <BaseButtons>
            <BaseButton type="submit" color="info" :label="t('common.save')" />

            <BaseButton
              type="button"
              color="info"
              :label="t('common.cancel')"
              outline
              @click="onCancel"
            />
          </BaseButtons>
        </template>
      </CardBox>

      <VendorCreateModal
        v-model="showVendorCreateModal"
        @created="onVendorCreated"
      />

      <UnsavedChangesModal
        v-model="showDiscardModal"
        @discard="confirmDiscard"
        @continue="cancelDiscard"
      />
    </SectionMain>
  </LayoutAuthenticated>
</template>
