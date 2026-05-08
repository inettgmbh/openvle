<script setup>
import {
  mdiAccount,
  mdiAccountOutline,
  mdiAccountQuestion,
  mdiMail,
  mdiWebBox,
} from '@mdi/js'
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
import { userStatusLabel } from '@/utils/dataUtils'
import { getUserLocaleOptions } from '@/utils/localeData'

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
} = useUnsavedChanges({ formData: user, onNavigateAway: () => router.back() })

const userLocaleOptions = getUserLocaleOptions(t)

const userStatusOptions = [
  { id: 1, label: userStatusLabel('Active'), value: 'Active' },
  { id: 2, label: userStatusLabel('Banned'), value: 'Banned' },
  {
    id: 3,
    label: userStatusLabel('E-Mail-Pending'),
    value: 'E-Mail-Pending',
  },
  { id: 4, label: userStatusLabel('Inactive'), value: 'Inactive' },
]

async function fetchUser(userId) {
  try {
    user.value = await backend.users.get(userId)
    setOriginal()
  } catch (error) {
    toast.error(
      t('common.loadError', { entity: t('objectTypes.user.singular') }),
    )
  }
}

fetchUser(route.params.id)

async function submit() {
  try {
    const res = await backend.users.update(user.value.id, {
      name: user.value.name,
      email: user.value.email,
      status: user.value.status,
      locale: user.value.locale,
    })
    toast.success(
      t('common.editSuccess', { entity: t('objectTypes.user.singular') }),
    )
    useLookupStore().updateFromObject('users', res)
    markAsSaved()
    router.push({ path: `/users/${user.value.id}` })
  } catch (error) {
    toast.error(
      t('common.editError', { entity: t('objectTypes.user.singular') }),
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
        :icon="mdiAccount"
        :title="
          $t('common.editTitle', { entity: $t('objectTypes.user.singular') })
        "
        main
        docs-path="/docs/usage/openvle/access-control/users/"
      />

      <CardBox is-form @submit.prevent="submit">
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

        <FormField :label="$t('views.users.form.emailAddress')">
          <FormControl
            v-model="user.email"
            type="email"
            :icon="mdiMail"
            :placeholder="$t('views.users.form.emailAddress')"
            required
          />
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
