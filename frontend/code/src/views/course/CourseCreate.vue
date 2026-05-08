<script setup>
import { mdiRename, mdiSchoolOutline, mdiTextBox } from '@mdi/js'
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

const { t } = useI18n()
const route = useRoute()
const course = ref({})
const toast = useToast()
const mainStore = useMainStore()

const moodleEnabled = computed(() => !!mainStore.settings?.moodle?.enabled)

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

async function submit() {
  try {
    const payload = {
      name: course.value.name,
      description: course.value.description,
    }
    if (moodleEnabled.value && course.value.moodleCourseId != null) {
      payload.moodleCourseId = course.value.moodleCourseId
    }
    const res = await backend.courses.create(payload)
    toast.success(
      t('common.createSuccess', { entity: t('objectTypes.course.singular') }),
    )
    useMainStore().fetchPermissions()
    markAsSaved()
    router.push({ path: `/courses/${res.id}` })
  } catch (error) {
    toast.error(
      t('common.createError', { entity: t('objectTypes.course.singular') }),
    )
  }
}

function onCancel() {
  if (handleCancel()) router.back()
}

onMounted(() => {
  course.value.description = route.query.description
  course.value.name = route.query.name
  setOriginal()
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiSchoolOutline"
        :title="
          $t('common.createTitle', {
            entity: $t('objectTypes.course.singular'),
          })
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
            :placeholder="$t('views.courses.form.namePlaceholder')"
            required
          />
        </FormField>

        <FormField
          :label="$t('common.description')"
          :help="$t('views.courses.form.descriptionHelp')"
        >
          <FormControl v-model="course.description" :icon="mdiTextBox" />
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
