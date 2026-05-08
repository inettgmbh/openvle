<script setup>
import { mdiClockPlusOutline, mdiNumeric, mdiUpdate } from '@mdi/js'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseDivider from '@/components/BaseDivider.vue'
import BaseTags from '@/components/BaseTags.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import { formatDate, getUserLink } from '@/utils/dataUtils'

const { t } = useI18n()

const props = defineProps({
  object: {
    type: Object,
    required: true,
  },
  objectType: {
    type: String,
    required: true,
  },
  objectId: {
    type: String,
    required: true,
  },
  showCreated: {
    type: Boolean,
    default: true,
  },
  showId: {
    type: Boolean,
    default: true,
  },
  showTags: {
    type: Boolean,
    default: true,
  },
  showUpdated: {
    type: Boolean,
    default: true,
  },
  tagsHelp: {
    type: String,
    default: 'Tags',
  },
  canEdit: {
    type: Boolean,
    default: false,
  },
})

const linkCreatedBy = computed(() =>
  getUserLink(props.object.createdBy, props.object.createdById),
)
const linkUpdatedBy = computed(() =>
  getUserLink(props.object.updatedBy, props.object.updatedById),
)
</script>

<template>
  <div>
    <BaseDivider />

    <BaseTags
      v-if="objectId && showTags"
      :help="tagsHelp"
      :object-type="objectType"
      :object-id="objectId"
      :can-edit="canEdit"
    />

    <BaseDivider v-if="showTags" />

    <FormField v-if="showId" :label="$t('common.id')">
      <FormControl :model-value="object.id" :icon="mdiNumeric" disabled />
    </FormField>

    <FormField v-if="showCreated" :label="t('components.metadata.creation')">
      <FormControl
        :model-value="formatDate(object.createdAt)"
        :icon="mdiClockPlusOutline"
        disabled
      />

      <FormControl
        :model-value="object.createdBy"
        :icon="mdiClockPlusOutline"
        :link="linkCreatedBy"
        disabled
      />
    </FormField>

    <FormField v-if="showUpdated" :label="t('components.metadata.lastChange')">
      <FormControl
        :model-value="formatDate(object.updatedAt)"
        :icon="mdiUpdate"
        disabled
      />

      <FormControl
        :model-value="object.updatedBy"
        :icon="mdiUpdate"
        :link="linkUpdatedBy"
        disabled
      />
    </FormField>
  </div>
</template>
