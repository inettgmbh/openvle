<script setup>
import {
  mdiAlertCircleOutline,
  mdiMailboxOutline,
  mdiRefreshAuto,
  mdiRename,
  mdiTextBox,
  mdiWebBox,
} from '@mdi/js'
import { computed, ref } from 'vue'
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
import NotificationBar from '@/components/NotificationBar.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import UnsavedChangesModal from '@/components/UnsavedChangesModal.vue'
import { useMailTemplatePlaceholders } from '@/composables/useMailTemplatePlaceholders'
import { useUnsavedChanges } from '@/composables/useUnsavedChanges'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import router from '@/router'
import backend from '@/services'
import { useLookupStore } from '@/stores/lookup'
import {
  htmlToMarkdown,
  htmlToPlainText,
  markdownToHtml,
} from '@/utils/htmlUtils'

const { t } = useI18n()
const lookupStore = useLookupStore()
const mailTemplate = ref({})
const route = useRoute()
const toast = useToast()
const actions = ref([])

const {
  showDiscardModal,
  setOriginal,
  markAsSaved,
  handleCancel,
  confirmDiscard,
  cancelDiscard,
} = useUnsavedChanges({
  formData: mailTemplate,
  onNavigateAway: () => router.back(),
})

// Computed refs for the placeholder validation composable
const contentRef = computed(() => mailTemplate.value.contentMarkdown || '')
const selectedActionRef = computed(() => mailTemplate.value.mail_action || '')

const { validationError, canSubmit, selectedActionContext } =
  useMailTemplatePlaceholders({
    content: contentRef,
    actions,
    selectedActionId: selectedActionRef,
  })

const isFormValid = computed(() => {
  return (
    canSubmit.value &&
    !!mailTemplate.value.name?.trim() &&
    !!mailTemplate.value.subject?.trim() &&
    !!mailTemplate.value.language &&
    !!mailTemplate.value.contentMarkdown?.trim()
  )
})

lookupStore.fetchAll('languages')

const languages = computed(() =>
  Object.entries(lookupStore.languages)
    .filter(([, val]) => typeof val === 'object')
    .map(([id, val]) => ({ label: val.name, value: id }))
    .sort((a, b) => a.label.localeCompare(b.label)),
)

backend.mailActions.dropdown().then((response) => {
  actions.value = response
})

async function fetchMailTemplate(id) {
  try {
    mailTemplate.value = await backend.mailTemplates.get(id)
    // Convert existing HTML content to Markdown for editing
    mailTemplate.value.contentMarkdown = htmlToMarkdown(
      mailTemplate.value.contentHTML,
    )
    setOriginal()
  } catch (error) {
    toast.error(
      t('common.loadError', { entity: t('objectTypes.mailTemplate.singular') }),
    )
  }
}
fetchMailTemplate(route.params.id)

async function submit() {
  if (!isFormValid.value) {
    toast.error(t('views.mailTemplates.form.invalidPlaceholders'))
    return
  }

  try {
    const html = markdownToHtml(mailTemplate.value.contentMarkdown)
    const res = await backend.mailTemplates.update(mailTemplate.value.id, {
      name: mailTemplate.value.name,
      subject: mailTemplate.value.subject,
      description: mailTemplate.value.description,
      contentHTML: html,
      contentPlain: htmlToPlainText(html),
      replyTo: mailTemplate.value.replyTo,
      mail_action: mailTemplate.value.mail_action,
      language: mailTemplate.value.language,
    })
    toast.success(
      t('common.editSuccess', {
        entity: t('objectTypes.mailTemplate.singular'),
      }),
    )
    useLookupStore().updateFromObject('mail_templates', res)
    markAsSaved()
    router.push({ path: `/mail-templates/${mailTemplate.value.id}` })
  } catch (error) {
    toast.error(
      t('common.editError', { entity: t('objectTypes.mailTemplate.singular') }),
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
        :icon="mdiMailboxOutline"
        :title="
          $t('common.editTitle', {
            entity: $t('objectTypes.mailTemplate.singular'),
          })
        "
        main
        docs-path="/docs/usage/openvle/mails/templates/"
      />

      <CardBox is-form @submit.prevent="submit">
        <FormField
          :label="$t('common.name')"
          :help="$t('views.mailTemplates.form.nameHelp')"
        >
          <FormControl
            v-model="mailTemplate.name"
            :icon="mdiRename"
            :placeholder="$t('views.mailTemplates.form.namePlaceholder')"
            required
          />
        </FormField>

        <FormField
          :label="$t('common.description')"
          :help="$t('views.mailTemplates.form.descriptionHelp')"
        >
          <FormControl v-model="mailTemplate.description" :icon="mdiTextBox" />
        </FormField>

        <FormField>
          <FormField
            :label="$t('views.mails.columns.subject')"
            :help="$t('views.mailTemplates.form.subjectHelp')"
          >
            <FormControl
              v-model="mailTemplate.subject"
              :icon="mdiTextBox"
              required
            />
          </FormField>

          <FormField
            :label="$t('views.mails.fields.replyTo')"
            :help="$t('views.mailTemplates.form.replyToHelp')"
          >
            <FormControl
              v-model="mailTemplate.replyTo"
              placeholder="replyto@example.com"
              :icon="mdiTextBox"
              type="email"
            />
          </FormField>
        </FormField>

        <FormField>
          <FormField
            :label="$t('views.mailTemplates.form.language')"
            :help="$t('views.mailTemplates.form.languageHelp')"
          >
            <FormControl
              v-model="mailTemplate.language"
              :icon="mdiWebBox"
              :options="languages"
              required
            />
          </FormField>

          <FormField
            :label="$t('views.mailTemplates.form.assignedAction')"
            :help="$t('views.mailTemplates.form.assignedActionHelp')"
          >
            <FormControl
              v-model="mailTemplate.mail_action"
              :icon="mdiRefreshAuto"
              :options="actions"
            />
          </FormField>
        </FormField>

        <BaseDivider />

        <FormField
          :label="$t('views.mailTemplates.form.content')"
          :help="`${$t('views.mailTemplates.form.contentHelp')}${selectedActionContext === 'events' ? ', {{ event.name }}, {{ subtask.status }}, ...' : selectedActionContext === 'virtualmachines' ? ', {{ virtualmachine.name }}, {{ virtualmachine.ipv4 }}, ...' : ''}`"
        >
          <BaseMarkdown
            v-model="mailTemplate.contentMarkdown"
            action="edit"
            :toolbars-exclude="['table', 'code', 'codeRow']"
          />
        </FormField>

        <NotificationBar
          v-if="validationError"
          color="danger"
          :dismissable="false"
          :icon="mdiAlertCircleOutline"
        >
          {{ validationError }}
        </NotificationBar>

        <template #footer>
          <BaseButtons>
            <BaseButton
              type="submit"
              color="info"
              :label="$t('common.save')"
              :disabled="!isFormValid"
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
