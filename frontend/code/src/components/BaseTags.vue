<script setup>
import { mdiPlus, mdiTag } from '@mdi/js'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseDivider from '@/components/BaseDivider.vue'
import CardBoxModal from '@/components/CardBoxModal.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import PillTag from '@/components/PillTag.vue'
import PillTagWithDelete from '@/components/PillTagWithDelete.vue'
import SearchControl from '@/components/SearchControl.vue'
import { FIELD_LIMITS } from '@/config/fieldLimits'
import backend from '@/services'
import { useAutofocusInput } from '@/utils/useAutofocusInput'

const { t } = useI18n()
const addedTag = ref({ key: '', value: '' })
const router = useRouter()
const searchComponent = ref(null)
const showModal = ref(false)
const { autoFocusInputRef } = useAutofocusInput(showModal)
const tags = ref([])
const toast = useToast()

const props = defineProps({
  help: {
    type: String,
    required: false,
    default: null,
  },
  color: {
    type: String,
    required: false,
    default: 'info',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  small: {
    type: Boolean,
    default: false,
    required: false,
  },
  outline: {
    type: Boolean,
    default: false,
    required: false,
  },
  objectType: {
    type: String,
    required: true,
  },
  objectId: {
    type: String,
    required: true,
  },
  canEdit: {
    type: Boolean,
    default: false,
  },
})

const handleTagClick = (tagKey, tagValue) => {
  router.push({ path: `/tags/${tagKey}/${tagValue}` })
}

const tagPreview = computed(() => {
  if (addedTag.value.key || addedTag.value.value) {
    return `${addedTag.value.key}: ${addedTag.value.value}`
  }
  return ''
})

async function addTag(tagKey, tagValue) {
  try {
    if (tagKey === undefined || tagKey === '' || tagKey === null) {
      showModal.value = true
      return toast.warning(t('components.baseTags.nameRequired'))
    }

    if (tagValue === undefined || tagValue === '' || tagValue === null) {
      showModal.value = true
      return toast.warning(t('components.baseTags.valueRequired'))
    }

    const exists = tags.value.some(
      (tag) => tag.key === tagKey && tag.value === tagValue,
    )
    if (exists) {
      toast.warning(t('components.baseTags.tagExists'))
      return
    }

    await backend.tags.create({
      key: tagKey,
      value: tagValue,
      objectId: props.objectId,
      objectType: props.objectType,
    })
    fetchTags()
    showModal.value = false
    toast.success(t('components.baseTags.tagAdded'))
    resetTag()
  } catch (error) {
    toast.error(t('common.addError', { entity: t('objectTypes.tag.singular') }))
  }
}

async function fetchTags() {
  try {
    await backend.tags
      .listByObject(props.objectType, props.objectId, {
        page: 1,
        limit: 50,
        sort_by: 'key',
        sort_order: 'asc',
      })
      .then((response) => {
        tags.value = response.items
        tags.value.tagsCount = response.pageDetails.totalCount
      })
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', { entities: t('objectTypes.tag.plural') }),
    )
  }
}

async function resetTag() {
  addedTag.value = { key: '', value: '' }
  searchComponent.value.reset()
}

function sanitizeTagInput(input) {
  const formatted = String(input)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
  return formatted
}

async function deleteTag(tagId) {
  try {
    await backend.tags.delete(tagId)
    await fetchTags()
    toast.success(t('components.baseTags.tagDeleted'))
  } catch (error) {
    toast.error(
      t('common.deleteError', { entity: t('objectTypes.tag.singular') }),
    )
  }
}

const onSelect = (selectedValue) => {
  addedTag.value.key = sanitizeTagInput(selectedValue)
}

fetchTags()
</script>

<template>
  <!-- Add Tag Modal -->
  <CardBoxModal
    v-model="showModal"
    form
    :title="t('components.baseTags.addTag')"
    button="success"
    has-cancel
    has-search
    :button-label="t('common.add')"
    @cancel="resetTag()"
    @form-submitted="addTag(addedTag.key, addedTag.value)"
  >
    <FormField>
      <FormField
        :label="t('common.name')"
        :help="t('common.maxChars', { max: FIELD_LIMITS.tag.key })"
      >
        <SearchControl
          v-model="addedTag.key"
          :icon="mdiTag"
          :fetch-data="backend.tags.search"
          :formatter="(val) => sanitizeTagInput(val)"
          :allow-custom-entry="true"
          label-attribute="key"
          return-attribute="key"
          :maxlength="FIELD_LIMITS.tag.key"
          required
          @input="
            (event) => (addedTag.key = sanitizeTagInput(event.target.value))
          "
          @set-ref="
            (ref) => {
              autoFocusInputRef = ref
              searchComponent = ref
            }
          "
          @update:model-value="onSelect"
        />
      </FormField>

      <FormField
        :label="t('common.value')"
        :help="t('common.maxChars', { max: FIELD_LIMITS.tag.value })"
      >
        <FormControl
          v-model="addedTag.value"
          :maxlength="FIELD_LIMITS.tag.value"
          :icon="mdiTag"
          placeholder="3"
          required
          @input="
            (event) => (addedTag.value = sanitizeTagInput(event.target.value))
          "
        />
      </FormField>
    </FormField>

    <BaseDivider />

    <FormField
      :label="t('components.baseTags.preview')"
      :help="t('components.baseTags.formatHelp')"
    >
      <FormControl
        :model-value="tagPreview"
        :icon="mdiTag"
        :placeholder="$t('components.baseTags.tagExample')"
        :disabled="true"
      />
    </FormField>
  </CardBoxModal>

  <FormField>
    <FormField :label="$t('components.baseTags.tags')" :help="help">
      <div class="flex flex-wrap gap-2 items-start">
        <PillTag
          v-if="canEdit"
          :color="color"
          outline
          :icon="mdiPlus"
          :small="small"
          @click="showModal = true"
        />

        <PillTagWithDelete
          v-for="tag in tags"
          :key="tag.key + ':' + tag.value"
          class="mr-1 mb-1"
          :label="tag.key + ': ' + tag.value"
          :color="color"
          :icon="mdiTag"
          :handle-click="() => handleTagClick(tag.key, tag.value)"
          :on-delete="canEdit ? () => deleteTag(tag.id) : undefined"
          :small="small"
        />
      </div>
    </FormField>
  </FormField>
</template>
