<script setup>
import { mdiFileSign, mdiRename, mdiTextBox } from '@mdi/js'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseMarkdown from '@/components/BaseMarkdown.vue'
import CardBox from '@/components/CardBox.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import UnsavedChangesModal from '@/components/UnsavedChangesModal.vue'
import { useUnsavedChanges } from '@/composables/useUnsavedChanges'
import { FIELD_LIMITS } from '@/config/fieldLimits'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import router from '@/router'
import backend from '@/services'

const { t } = useI18n()
const policy = ref({})
const route = useRoute()
const toast = useToast()

const {
  showDiscardModal,
  setOriginal,
  markAsSaved,
  handleCancel,
  confirmDiscard,
  cancelDiscard,
} = useUnsavedChanges({
  formData: policy,
  onNavigateAway: () => router.back(),
})

async function fetchPolicy(policyId) {
  try {
    policy.value = await backend.policies.get(policyId)
    policy.value.protectedOld = policy.value.protected
    setOriginal()
  } catch (error) {
    toast.error(
      t('common.loadError', { entity: t('objectTypes.policy.singular') }),
    )
  }
}
fetchPolicy(route.params.id)

async function submit() {
  try {
    await backend.policies.update(policy.value.id, {
      name: policy.value.name,
      description: policy.value.description,
      content: policy.value.content,
    })
    toast.success(
      t('common.editSuccess', { entity: t('objectTypes.policy.singular') }),
    )
    markAsSaved()
    router.push({ path: `/policies/${policy.value.id}` })
  } catch (error) {
    toast.error(
      t('common.editError', { entity: t('objectTypes.policy.singular') }),
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
        :icon="mdiFileSign"
        :title="
          $t('common.editTitle', { entity: $t('objectTypes.policy.singular') })
        "
        main
        docs-path="/docs/usage/openvle/access-control/policies/"
      />

      <CardBox is-form @submit.prevent="submit">
        <FormField
          :label="$t('common.name')"
          :help="$t('views.policies.form.nameHelp')"
        >
          <FormControl
            v-model="policy.name"
            :icon="mdiRename"
            :maxlength="FIELD_LIMITS.policy.name"
            :placeholder="$t('views.policies.form.editPlaceholder')"
            required
          />
        </FormField>

        <FormField
          :label="$t('common.description')"
          :help="$t('views.policies.form.descriptionHelp')"
        >
          <FormControl
            v-model="policy.description"
            :icon="mdiTextBox"
            :maxlength="FIELD_LIMITS.policy.description"
          />
        </FormField>

        <FormField
          :label="$t('views.policies.form.content')"
          :help="$t('views.policies.form.contentHelp')"
        />

        <BaseMarkdown v-model="policy.content" action="edit" />

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
