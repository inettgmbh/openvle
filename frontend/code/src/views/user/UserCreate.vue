<script setup>
import {
  mdiAccount,
  mdiAccountOutline,
  mdiAccountQuestion,
  mdiFormTextboxPassword,
  mdiMail,
  mdiWebBox,
} from '@mdi/js'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import CardBox from '@/components/CardBox.vue'
import FormCheckRadio from '@/components/FormCheckRadio.vue'
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
import { userStatusLabel } from '@/utils/dataUtils'
import { DEFAULT_USER_LOCALE, getUserLocaleOptions } from '@/utils/localeData'

const { t } = useI18n()
const route = useRoute()
const toast = useToast()

const user = ref({})

const {
  showDiscardModal,
  setOriginal,
  markAsSaved,
  handleCancel,
  confirmDiscard,
  cancelDiscard,
} = useUnsavedChanges({
  formData: user,
  onNavigateAway: () => router.back(),
})

const userStatusOptions = [
  { id: 1, label: userStatusLabel('Active'), value: 'Active', selected: true },
  { id: 2, label: userStatusLabel('Banned'), value: 'Banned' },
  { id: 4, label: userStatusLabel('Inactive'), value: 'Inactive' },
]

const userLocaleOptions = getUserLocaleOptions(t)

const externalUser = ref(true)

async function submit() {
  try {
    const res = await backend.users.create(user.value)
    toast.success(
      t('common.createSuccess', { entity: t('objectTypes.user.singular') }),
    )
    useMainStore().fetchPermissions()
    markAsSaved()
    router.push({ path: `/users/${res.id}` })
  } catch (error) {
    toast.error(
      `${t('common.createError', { entity: t('objectTypes.user.singular') })}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  }
}

function onCancel() {
  if (handleCancel()) router.back()
}

onMounted(() => {
  user.value.email = route.query.email
  user.value.name = route.query.name
  user.value.status = route.query.status ? route.query.status : 'Active'
  user.value.locale = DEFAULT_USER_LOCALE
  user.value.username = route.query.username
  setOriginal()
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiAccount"
        :title="
          $t('common.createTitle', { entity: $t('objectTypes.user.singular') })
        "
        main
        docs-path="/docs/usage/openvle/access-control/users/"
      />

      <CardBox is-form @submit.prevent="submit">
        <FormField>
          <FormField
            :label="$t('common.name')"
            :help="$t('views.users.form.canonicalNameHelp')"
          >
            <FormControl
              v-model="user.name"
              :icon="mdiAccountOutline"
              :placeholder="$t('common.name')"
              required
            />
          </FormField>
        </FormField>

        <FormField>
          <FormField :label="$t('views.users.form.username')">
            <FormControl
              v-model="user.username"
              :icon="mdiAccount"
              :placeholder="$t('views.users.form.username')"
              required
            />
          </FormField>

          <FormField :label="$t('views.users.form.emailAddress')">
            <FormControl
              v-model="user.email"
              type="email"
              :icon="mdiMail"
              :placeholder="$t('views.users.form.emailAddress')"
              required
            />
          </FormField>
        </FormField>

        <FormField>
          <FormField :label="$t('common.status')">
            <FormControl
              v-model="user.status"
              :icon="mdiAccountQuestion"
              :options="userStatusOptions"
              required
            />
          </FormField>

          <FormField :label="$t('views.users.form.language')">
            <FormControl
              v-model="user.locale"
              :icon="mdiWebBox"
              :options="userLocaleOptions"
              required
            />
          </FormField>
        </FormField>

        <FormField :label="$t('views.users.form.access')">
          <FormCheckRadio
            v-model="externalUser"
            type="switch"
            name="external-switch"
            input-value="key"
            :label="$t('views.users.form.externalUserSwitch')"
            :help="$t('views.users.form.externalUserHelp')"
          />
        </FormField>

        <FormField v-if="!externalUser">
          <FormField
            :label="$t('views.users.form.password')"
            :help="$t('views.users.form.required')"
          >
            <FormControl
              v-model="user.password"
              :icon="mdiFormTextboxPassword"
              name="password"
              type="password"
              required
              autocomplete="new-password"
            />
          </FormField>

          <FormField
            :label="$t('views.users.form.passwordConfirm')"
            :help="$t('views.users.form.required')"
          >
            <FormControl
              v-model="user.password_repeat"
              :icon="mdiFormTextboxPassword"
              name="password_repeat"
              type="password"
              required
              autocomplete="new-password"
            />
          </FormField>
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
