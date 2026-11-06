<script setup>
import { mdiRename, mdiSchoolOutline, mdiTextBox } from '@mdi/js'
import { computed, ref } from 'vue'
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
import { FIELD_LIMITS } from '@/config/fieldLimits'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import router from '@/router'
import backend from '@/services'
import { useLookupStore } from '@/stores/lookup'
import { useMainStore } from '@/stores/main'

const course = ref({})
const mainStore = useMainStore()

const moodleEnabled = computed(() => !!mainStore.settings?.moodle?.enabled)
const route = useRoute()
const toast = useToast()
const { t } = useI18n()

const {
  showDiscardModal,
  setOriginal,
  markAsSaved,
  handleCancel,
  confirmDiscard,
  cancelDiscard,
} = useUnsavedChanges({
  formData: course,
  onNavigateAway: () => router.back(),
})

async function fetchCourse(id) {
  try {
    course.value = await backend.courses.get(id)
    setOriginal()
  } catch (error) {
    toast.error(
      t('common.loadError', { entity: t('objectTypes.course.singular') }),
    )
  }
}
fetchCourse(route.params.id)

async function submit() {
  try {
    const payload = {
      name: course.value.name,
      description: course.value.description,
    }
    if (moodleEnabled.value) {
      payload.moodleCourseId = course.value.moodleCourseId ?? null
    }
    const res = await backend.courses.update(course.value.id, payload)
    toast.success(
      t('common.editSuccess', { entity: t('objectTypes.course.singular') }),
    )
    useLookupStore().updateFromObject('courses', res)
    markAsSaved()
    router.push({ path: `/courses/${course.value.id}` })
  } catch (error) {
    toast.error(
      t('common.editError', { entity: t('objectTypes.course.singular') }),
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
        :icon="mdiSchoolOutline"
        :title="
          $t('common.editTitle', { entity: $t('objectTypes.course.singular') })
        "
        main
        docs-path="/docs/usage/openvle/courses/"
      />

      <CardBox is-form @submit.prevent="submit">
        <FormField
          :label="$t('common.name')"
          :help="$t('views.courses.form.nameHelp')"
        >
          <FormControl
            v-model="course.name"
            :icon="mdiRename"
            :maxlength="FIELD_LIMITS.course.name"
            :placeholder="$t('views.courses.form.namePlaceholder')"
            required
          />
        </FormField>

        <FormField
          :label="$t('common.description')"
          :help="$t('views.courses.form.descriptionHelp')"
        >
          <FormControl
            v-model="course.description"
            :icon="mdiTextBox"
            :maxlength="FIELD_LIMITS.course.description"
          />
        </FormField>

        <!-- Moodle course picker (feature-gated) -->
        <FormField
          v-if="moodleEnabled"
          :label="$t('views.courses.form.moodleCourse')"
          :help="$t('views.courses.form.moodleCourseHelp')"
        >
          <SearchControl
            v-model="course.moodleCourseId"
            :icon="mdiSchoolOutline"
            :fetch-data="backend.moodle.search"
            :fetch-selected="backend.moodle.getName"
            label-attribute="fullname"
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
