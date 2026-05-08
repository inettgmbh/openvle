<script setup>
import {
  mdiCalendarOutline,
  mdiRename,
  mdiSchoolOutline,
  mdiTextBox,
} from '@mdi/js'
import VueDatePicker from '@vuepic/vue-datepicker'
import '@vuepic/vue-datepicker/dist/main.css'
import { ref } from 'vue'
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
import { useUnsavedChanges } from '@/composables/useUnsavedChanges'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import router from '@/router'
import backend from '@/services'
import { useLookupStore } from '@/stores/lookup'
import { useMainStore } from '@/stores/main'
import { useStyleStore } from '@/stores/style.js'

const { t } = useI18n()
const event = ref({})
const route = useRoute()
const toast = useToast()
const mainStore = useMainStore()

const {
  showDiscardModal,
  setOriginal,
  markAsSaved,
  handleCancel,
  confirmDiscard,
  cancelDiscard,
} = useUnsavedChanges({
  formData: event,
  onNavigateAway: () => router.back(),
})

async function fetchEvent(eventId) {
  try {
    event.value = await backend.events.get(eventId)
    if (event.value.dateEnd == '2099-12-31') {
      event.value.dateEnd = null
    }
    setOriginal()
  } catch (error) {
    toast.error(
      t('common.loadError', { entity: t('objectTypes.event.singular') }),
    )
  }
}
fetchEvent(route.params.id)

async function submit() {
  try {
    const dateStart = new Date(event.value.dateStart)
      .toISOString()
      .split('T')[0]

    let dateEnd
    const endDateRaw = event.value.dateEnd
    const parsedEndDate = new Date(endDateRaw)

    if (endDateRaw && !isNaN(parsedEndDate)) {
      dateEnd = parsedEndDate.toISOString().split('T')[0]
    } else {
      dateEnd = '2099-12-31'
    }
    const res = await backend.events.update(event.value.id, {
      name: event.value.name,
      description: event.value.description,
      dateStart,
      dateEnd,
      course: event.value.course,
    })
    toast.success(
      t('common.editSuccess', { entity: t('objectTypes.event.singular') }),
    )
    useLookupStore().updateFromObject('events', res)
    markAsSaved()
    router.push({ path: `/events/${event.value.id}` })
  } catch (error) {
    toast.error(
      t('common.editError', { entity: t('objectTypes.event.singular') }) +
        '\n' +
        error?.response?.data?.detail,
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
        :icon="mdiCalendarOutline"
        :title="
          $t('common.editTitle', { entity: $t('objectTypes.event.singular') })
        "
        main
        docs-path="/docs/usage/openvle/events/"
      />

      <CardBox is-form @submit.prevent="submit">
        <FormField
          :label="$t('common.name')"
          :help="$t('views.events.form.nameHelp')"
        >
          <FormControl v-model="event.name" :icon="mdiRename" required />
        </FormField>

        <FormField
          :label="$t('common.description')"
          :help="$t('views.events.form.descriptionHelp')"
        >
          <FormControl v-model="event.description" :icon="mdiTextBox" />
        </FormField>

        <FormField>
          <FormField
            :label="$t('views.events.form.dateStart')"
            :help="
              $t('views.events.form.dateStartHelpWithPrep', {
                days: mainStore?.settings?.events?.start?.prep_time?.days,
              })
            "
          >
            <VueDatePicker
              v-model="event.dateStart"
              utc="preserve"
              :enable-time-picker="false"
              text-input
              :month-change-on-scroll="false"
              :clearable="false"
              :placeholder="$t('views.events.form.datePickerPlaceholder')"
              :min-date="new Date()"
              format="EEE, dd.MM.yyyy"
              locale="de"
              week-numbers="iso"
              auto-apply
              :dark="useStyleStore().darkMode"
              :required="true"
            />
          </FormField>

          <FormField
            :label="$t('views.events.form.dateEnd')"
            :help="
              $t('views.events.form.dateEndHelpWithPrep', {
                days: mainStore?.settings?.events?.end?.prep_time?.days,
              })
            "
          >
            <VueDatePicker
              v-model="event.dateEnd"
              utc="preserve"
              :enable-time-picker="false"
              text-input
              :month-change-on-scroll="false"
              :clearable="true"
              :placeholder="$t('views.events.form.dateEndPlaceholder')"
              :min-date="event.dateStart"
              format="EEE, dd.MM.yyyy"
              locale="de"
              week-numbers="iso"
              auto-apply
              :dark="useStyleStore().darkMode"
            />
          </FormField>
        </FormField>

        <FormField
          :label="$t('views.events.form.course')"
          :help="$t('views.events.form.courseHelp')"
        >
          <SearchControl
            v-model="event.course"
            :icon="mdiSchoolOutline"
            :fetch-data="backend.courses.search"
            :fetch-selected="backend.courses.getName"
            required
          />
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

<style>
.dp__theme_dark {
  --dp-background-color: rgb(30 41 59);
}
</style>
