<script setup>
import {
  mdiCalendarOutline,
  mdiLabel,
  mdiRename,
  mdiSchoolOutline,
  mdiTextBox,
} from '@mdi/js'
import VueDatePicker from '@vuepic/vue-datepicker'
import '@vuepic/vue-datepicker/dist/main.css'
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
import { useUnsavedChanges } from '@/composables/useUnsavedChanges'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import router from '@/router'
import backend from '@/services'
import { useMainStore } from '@/stores/main'
import { useStyleStore } from '@/stores/style.js'
import { validateEventSlug } from '@/utils/dataUtils'

const { t } = useI18n()
const route = useRoute()
const event = ref({})
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
    const res = await backend.events.create({
      name: event.value.name,
      description: event.value.description,
      dateStart,
      dateEnd,
      course: event.value.course,
      slug: event.value.slug,
    })
    toast.success(
      t('common.createSuccess', { entity: t('objectTypes.event.singular') }),
    )
    mainStore.fetchPermissions()
    markAsSaved()
    router.push({ path: `/events/${res.id}` })
  } catch (error) {
    let errorMsg = t('common.createError', {
      entity: t('objectTypes.event.singular'),
    })
    const errorCode = error?.response?.data?.error_code
    if (errorCode === 'DUPLICATE_FIELD') {
      errorMsg = t('views.events.create.errorDuplicate')
    } else if (errorCode === 'INVALID_FIELD_VALUE') {
      errorMsg = t('views.events.create.errorInvalidSlug')
    }

    toast.error(errorMsg, {
      timeout: 8400,
    })
  }
}

const createEnabled = computed(() => {
  if (!event.value.name || event.value.name.length <= 0) {
    return false
  }
  const validationError = validateEventSlug(event.value.slug)
  if (validationError !== true) {
    return false
  }

  return true
})

function onCancel() {
  if (handleCancel()) router.back()
}

onMounted(() => {
  event.value.name = route.query.name
  event.value.description = route.query.description
  event.value.dateStart = route.query.dateStart
  event.value.dateEnd = route.query.dateEnd
  event.value.course = route.query.course
  event.value.slug = route.query.slug
  setOriginal()
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiCalendarOutline"
        :title="
          $t('common.createTitle', { entity: $t('objectTypes.event.singular') })
        "
        main
        docs-path="/docs/usage/openvle/events/"
      />

      <CardBox is-form @submit.prevent="submit">
        <div class="flex gap-4">
          <FormField
            :label="$t('common.name')"
            :help="$t('views.events.form.nameHelp')"
            class="w-[65%]"
          >
            <FormControl
              v-model="event.name"
              :icon="mdiRename"
              maxlength="25"
              :placeholder="$t('views.events.form.namePlaceholder')"
              :autofocus="true"
              required
            />
          </FormField>

          <FormField
            :label="$t('views.events.form.slug')"
            :help="$t('views.events.form.slugHelp')"
            :tooltip="$t('views.events.form.slugTooltip')"
            class="w-[35%]"
          >
            <FormControl
              v-model="event.slug"
              :icon="mdiLabel"
              :validate="(val) => validateEventSlug(val)"
              maxlength="8"
              :placeholder="$t('views.events.form.slugPlaceholder')"
              required
            />
          </FormField>
        </div>

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
            :tooltip="$t('views.events.form.dateStartTooltip')"
          >
            <VueDatePicker
              v-model="event.dateStart"
              utc="preserve"
              :enable-time-picker="false"
              text-input
              :month-change-on-scroll="false"
              :clearable="true"
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
            :tooltip="$t('views.events.form.dateEndTooltip')"
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
            <BaseButton
              type="submit"
              color="info"
              :label="$t('common.add')"
              :disabled="!createEnabled"
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

<style>
.dp__theme_dark {
  --dp-background-color: rgb(30 41 59);
}
</style>
