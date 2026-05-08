<script setup>
import {
  mdiApplicationBrackets,
  mdiRename,
  mdiVectorArrangeAbove,
} from '@mdi/js'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseDivider from '@/components/BaseDivider.vue'
import BaseMarkdown from '@/components/BaseMarkdown.vue'
import CardBox from '@/components/CardBox.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import SearchControl from '@/components/SearchControl.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import UnsavedChangesModal from '@/components/UnsavedChangesModal.vue'
import { useUnsavedChanges } from '@/composables/useUnsavedChanges'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import router from '@/router'
import backend from '@/services'
import { useLookupStore } from '@/stores/lookup'

const { t } = useI18n()
const template = ref({})
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
  formData: template,
  onNavigateAway: () => router.back(),
})

async function fetchTemplate(templateId) {
  try {
    template.value = await backend.templates.get(templateId)
    template.value.ram = template.value.ram / 1024
    setOriginal()
  } catch (error) {
    toast.error(
      t('common.loadError', { entity: t('objectTypes.template.singular') }),
    )
  }
}
fetchTemplate(route.params.id)

async function submit() {
  try {
    const res = await backend.templates.update(template.value.id, {
      name: template.value.name,
      description: template.value.description,
      cpu: template.value.cpu,
      ram: template.value.ram * 1024,
      os: template.value.os,
    })
    toast.success(
      t('common.editSuccess', { entity: t('objectTypes.template.singular') }),
    )
    useLookupStore().updateFromObject('templates', res)
    markAsSaved()
    router.push({ path: `/templates/${template.value.id}` })
  } catch (error) {
    toast.error(
      t('common.editError', { entity: t('objectTypes.template.singular') }),
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
        :icon="mdiVectorArrangeAbove"
        :title="
          $t('common.editTitle', {
            entity: $t('objectTypes.template.singular'),
          })
        "
        main
        docs-path="/docs/usage/openvle/vms/templates/"
      />

      <CardBox is-form @submit.prevent="submit">
        <FormField>
          <FormField
            :label="$t('common.name')"
            :help="$t('views.templates.form.nameHelp')"
          >
            <FormControl
              v-model="template.name"
              :icon="mdiRename"
              :placeholder="$t('views.templates.form.namePlaceholder')"
              maxlength="50"
              required
            />
          </FormField>

          <FormField
            :label="$t('views.templates.form.os')"
            :help="$t('views.templates.form.osHelp')"
          >
            <SearchControl
              v-model="template.os"
              :icon="mdiApplicationBrackets"
              :fetch-data="backend.os.search"
              :fetch-selected="backend.os.getName"
              required
            />
          </FormField>
        </FormField>

        <BaseDivider />

        <FormField>
          <FormField
            :label="$t('views.templates.form.cpuCores')"
            :help="$t('views.templates.form.cpuCoresHelp')"
          >
            <FormControl
              v-model="template.cpu"
              type="range"
              placeholder="2"
              :min="1"
              :max="12"
              required
            />
          </FormField>

          <FormField
            :label="$t('views.templates.form.ram')"
            :help="$t('views.templates.form.ramHelp')"
          >
            <FormControl
              v-model="template.ram"
              type="range"
              placeholder="4"
              :min="1"
              :max="20"
              :step="1"
              required
            />
          </FormField>
        </FormField>

        <BaseDivider />

        <FormField
          :label="$t('common.description')"
          :help="$t('views.templates.form.descriptionHelp')"
        />

        <BaseMarkdown v-model="template.description" action="edit" />

        <BaseDivider />

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

<style scoped>
body {
  margin: 0;
}

.editor {
  height: 100vh;
  display: flex;
}

.input,
.output {
  overflow: auto;
  width: 50%;
  height: 100%;
  box-sizing: border-box;
  padding: 0 20px;
}

.input {
  border: none;
  border-right: 1px solid #ccc;
  resize: none;
  outline: none;
  background-color: #f6f6f6;
  font-size: 14px;
  font-family: 'Monaco', courier, monospace;
  padding: 20px;
}

code {
  color: #f66;
}
</style>
