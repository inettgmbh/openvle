<script setup>
import {
  mdiCheck,
  mdiEmailOutline,
  mdiMailboxOutline,
  mdiNumeric1Circle,
  mdiNumeric2Circle,
  mdiNumeric3Circle,
  mdiTextBox,
} from '@mdi/js'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseIcon from '@/components/BaseIcon.vue'
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

const { t } = useI18n()
const route = useRoute()
const toast = useToast()

const mail = ref({})
const templateId = ref(null)
const userId = ref(null)
const selectedTemplate = ref(null)
const selectedUser = ref(null)

const {
  showDiscardModal,
  setOriginal,
  markAsSaved,
  handleCancel,
  confirmDiscard,
  cancelDiscard,
} = useUnsavedChanges({
  formData: mail,
  onNavigateAway: () => router.back(),
})

const hasTemplate = computed(() => !!selectedTemplate.value?.id)
const hasUser = computed(() => !!selectedUser.value?.id)

const currentStep = computed(() => {
  if (!hasTemplate.value) return 1
  if (!hasUser.value) return 2
  return 3
})

const canSubmit = computed(
  () =>
    currentStep.value >= 3 &&
    mail.value.subject &&
    mail.value.fromName &&
    mail.value.fromMail &&
    mail.value.toMail,
)

let initializing = false

async function loadTemplate(id) {
  const template = await backend.mailTemplates.get(id)
  selectedTemplate.value = template
  mail.value.subject = template.subject || ''
  mail.value.fromName = template.fromName || ''
  mail.value.fromMail = template.fromMail || ''
  mail.value.replyTo = template.replyTo || ''
}

async function loadUser(id) {
  const user = await backend.users.get(id)
  selectedUser.value = user
  mail.value.toMail = user.email || ''
}

// Fetch full template when selected
watch(templateId, async (id) => {
  if (initializing || !id) return
  try {
    await loadTemplate(id)
  } catch {
    toast.error(
      t('common.loadError', { entity: t('objectTypes.mailTemplate.singular') }),
    )
  }
})

// Fetch full user when selected
watch(userId, async (id) => {
  if (initializing || !id) return
  try {
    await loadUser(id)
  } catch {
    toast.error(
      t('common.loadError', { entity: t('objectTypes.user.singular') }),
    )
  }
})

function onTemplateSearchStarted() {
  templateId.value = null
  selectedTemplate.value = null
  mail.value.subject = ''
  mail.value.fromName = ''
  mail.value.fromMail = ''
  mail.value.replyTo = ''
  // Reset dependent steps
  userId.value = null
  selectedUser.value = null
  mail.value.toMail = ''
}

function onUserSearchStarted() {
  userId.value = null
  selectedUser.value = null
  mail.value.toMail = ''
}

async function submit() {
  try {
    const res = await backend.mails.create({
      subject: mail.value.subject,
      fromName: mail.value.fromName,
      fromMail: mail.value.fromMail,
      toMail: mail.value.toMail,
      templateId: selectedTemplate.value.id,
      replyTo: mail.value.replyTo,
    })
    toast.success(t('views.mails.create.success'))
    markAsSaved()
    router.push({ path: `/mails/${res.id}` })
  } catch {
    toast.error(t('views.mails.create.error'))
  }
}

function onCancel() {
  if (handleCancel()) router.back()
}

onMounted(async () => {
  initializing = true

  if (route.query.templateId) {
    templateId.value = route.query.templateId
    try {
      await loadTemplate(route.query.templateId)
    } catch {
      // Template fetch failed, fields stay empty
    }
  }

  if (route.query.userId) {
    userId.value = route.query.userId
    try {
      await loadUser(route.query.userId)
    } catch {
      // User fetch failed, field stays empty
    }
  }

  // Explicit query param overrides
  if (route.query.subject) mail.value.subject = route.query.subject
  if (route.query.fromName) mail.value.fromName = route.query.fromName
  if (route.query.fromMail) mail.value.fromMail = route.query.fromMail
  if (route.query.replyTo) mail.value.replyTo = route.query.replyTo

  initializing = false
  setOriginal()
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiMailboxOutline"
        :title="
          $t('common.sendTitle', { entity: $t('objectTypes.mail.singular') })
        "
        main
        docs-path="/docs/usage/openvle/mails/"
      />

      <CardBox is-form @submit.prevent="submit">
        <!-- Step 1: Select mail template -->
        <div class="mb-6">
          <div class="mb-3 flex items-center gap-2">
            <BaseIcon
              :path="mdiNumeric1Circle"
              :size="24"
              :class="
                hasTemplate
                  ? 'text-green-600 dark:text-green-400'
                  : 'text-blue-600 dark:text-blue-400'
              "
            />

            <span class="font-medium">{{
              $t('views.mails.form.steps.selectTemplate')
            }}</span>

            <BaseIcon
              v-if="hasTemplate"
              :path="mdiCheck"
              :size="18"
              class="text-green-600 dark:text-green-400"
            />
          </div>

          <SearchControl
            v-model="templateId"
            :icon="mdiTextBox"
            :fetch-data="backend.mailTemplates.search"
            :fetch-selected="backend.mailTemplates.getName"
            :placeholder="$t('common.searchPlaceholder')"
            required
            :autofocus="true"
            @input-started="onTemplateSearchStarted"
          />
        </div>

        <!-- Step 2: Select user -->
        <div class="mb-6">
          <div class="mb-3 flex items-center gap-2">
            <BaseIcon
              :path="mdiNumeric2Circle"
              :size="24"
              :class="
                hasUser
                  ? 'text-green-600 dark:text-green-400'
                  : currentStep >= 2
                    ? 'text-blue-600 dark:text-blue-400'
                    : 'text-gray-300 dark:text-slate-600'
              "
            />

            <span
              class="font-medium"
              :class="
                currentStep < 2 ? 'text-gray-400 dark:text-slate-500' : ''
              "
            >
              {{ $t('views.mails.form.steps.selectUser') }}
            </span>

            <BaseIcon
              v-if="hasUser"
              :path="mdiCheck"
              :size="18"
              class="text-green-600 dark:text-green-400"
            />
          </div>

          <div :class="{ 'pointer-events-none opacity-40': !hasTemplate }">
            <SearchControl
              v-model="userId"
              :icon="mdiEmailOutline"
              :fetch-data="backend.users.search"
              :fetch-selected="backend.users.formatById"
              :placeholder="$t('common.searchPlaceholder')"
              required
              :disabled="!hasTemplate"
              @input-started="onUserSearchStarted"
            />
          </div>
        </div>

        <!-- Step 3: Mail settings -->
        <div class="mb-2">
          <div class="mb-3 flex items-center gap-2">
            <BaseIcon
              :path="mdiNumeric3Circle"
              :size="24"
              :class="
                currentStep >= 3
                  ? 'text-blue-600 dark:text-blue-400'
                  : 'text-gray-300 dark:text-slate-600'
              "
            />

            <span
              class="font-medium"
              :class="
                currentStep < 3 ? 'text-gray-400 dark:text-slate-500' : ''
              "
            >
              {{ $t('views.mails.form.steps.settings') }}
            </span>
          </div>

          <div
            :class="{
              'pointer-events-none opacity-40': currentStep < 3,
            }"
          >
            <FormField
              :label="$t('views.mails.columns.subject')"
              :help="$t('views.mails.form.fields.subjectHelp')"
            >
              <FormControl
                v-model="mail.subject"
                :icon="mdiTextBox"
                :placeholder="$t('views.mails.columns.subject')"
                :disabled="currentStep < 3"
                required
              />
            </FormField>

            <FormField>
              <FormField
                :label="$t('views.mails.fields.fromName')"
                :help="$t('views.mails.form.fields.fromNameHelp')"
              >
                <FormControl
                  v-model="mail.fromName"
                  :icon="mdiTextBox"
                  placeholder="Max Mustermann"
                  :disabled="currentStep < 3"
                  required
                />
              </FormField>

              <FormField
                :label="$t('views.mails.fields.fromMail')"
                :help="$t('views.mails.form.fields.fromMailHelp')"
              >
                <FormControl
                  v-model="mail.fromMail"
                  :icon="mdiEmailOutline"
                  placeholder="absender@example.com"
                  :disabled="currentStep < 3"
                  required
                />
              </FormField>
            </FormField>

            <FormField
              :label="$t('views.mails.fields.replyTo')"
              :help="$t('views.mails.form.fields.replyToHelp')"
            >
              <FormControl
                v-model="mail.replyTo"
                :icon="mdiEmailOutline"
                placeholder="antwort@example.com"
                :disabled="currentStep < 3"
              />
            </FormField>
          </div>
        </div>

        <template #footer>
          <BaseButtons>
            <BaseButton
              type="submit"
              color="info"
              :label="$t('views.mails.form.send')"
              :disabled="!canSubmit"
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
