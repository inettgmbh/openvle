<script setup>
import {
  mdiApplicationBrackets,
  mdiDomain,
  mdiPlus,
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
import SearchControl from '@/components/SearchControl.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import UnsavedChangesModal from '@/components/UnsavedChangesModal.vue'
import VendorCreateModal from '@/components/VendorCreateModal.vue'
import { useUnsavedChanges } from '@/composables/useUnsavedChanges'
import { FIELD_LIMITS } from '@/config/fieldLimits'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import router from '@/router'
import backend from '@/services'
import { useMainStore } from '@/stores/main'
import { checkObjectPermissions, usePermissionRefs } from '@/utils/dataUtils'

const { t } = useI18n()
const os = ref({})
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
  formData: os,
  onNavigateAway: () => router.back(),
})

async function submit() {
  try {
    const res = await backend.os.create({
      name: os.value.name,
      key: os.value.key,
      description: os.value.description,
      vendor: os.value.vendor,
    })
    toast.success(
      t('common.createSuccess', { entity: t('objectTypes.os.singular') }),
    )
    useMainStore().fetchPermissions()
    markAsSaved()
    router.push({ path: `/os/${res.id}` })
  } catch (error) {
    toast.error(
      t('common.createError', { entity: t('objectTypes.os.singular') }),
    )
  }
}

function onCancel() {
  if (handleCancel()) router.back()
}

os.value.key = computed(() =>
  os.value.name ? os.value.name.toLowerCase().replace(/[^a-z0-9]+/g, '_') : '',
)

function onVendorCreated({ id, name }) {
  os.value.vendor = id
  vendorSearchRef.value?.setInitialDisplay(name)
  vendorSearchRef.value?.setSelectedId(id)
}

onMounted(async () => {
  os.value.description = route.query.description
  os.value.name = route.query.name
  os.value.vendor = route.query.vendor
  setOriginal()
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
        :icon="mdiApplicationBrackets"
        :title="
          $t('common.createTitle', { entity: $t('objectTypes.os.singular') })
        "
        main
        docs-path="/docs/usage/openvle/infrastructure/os/"
      />

      <CardBox is-form @submit.prevent="submit">
        <FormField
          :label="$t('common.name')"
          :help="$t('views.os.form.nameHelp')"
        >
          <FormControl
            v-model="os.name"
            :icon="mdiRename"
            :maxlength="FIELD_LIMITS.os.name"
            :placeholder="$t('views.os.form.namePlaceholder')"
            :autofocus="true"
            required
          />
        </FormField>

        <FormField :label="$t('objectTypes.vendor.singular')">
          <div class="flex items-start gap-2">
            <div class="flex-1">
              <SearchControl
                v-model="os.vendor"
                :icon="mdiDomain"
                :fetch-data="backend.vendors.search"
                :fetch-selected="backend.vendors.getName"
                required
                @set-ref="(ref) => (vendorSearchRef = ref)"
              />
            </div>

            <BaseButton
              v-if="permissionRefs.canCreate"
              v-tooltip="$t('views.os.form.createVendorTooltip')"
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
          :label="$t('common.description')"
          :help="$t('views.os.form.descriptionHelp')"
        >
          <FormControl
            v-model="os.description"
            :icon="mdiTextBox"
            :maxlength="FIELD_LIMITS.os.description"
          />
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
