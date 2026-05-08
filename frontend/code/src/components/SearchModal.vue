<script setup>
import { mdiText } from '@mdi/js'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import CardBoxModal from '@/components/CardBoxModal.vue'
import FormField from '@/components/FormField.vue'
import SearchControl from '@/components/SearchControl.vue'
import { useAutofocusInput } from '@/utils/useAutofocusInput'

const { t } = useI18n()

const props = defineProps({
  maxEntries: {
    type: Number,
    required: false,
    default: 25,
  },
  modelValue: {
    type: Boolean,
    required: true,
  },
  fetchData: {
    type: Function,
    required: true,
  },
  returnAttribute: {
    type: String,
    default: 'id',
  },
  title: {
    type: String,
    required: true,
  },
  placeholder: {
    type: String,
    default: null,
  },
  required: {
    type: Boolean,
    default: false,
  },
  icon: {
    type: String,
    default: mdiText,
  },
  label: {
    type: String,
    default: null,
  },
})

const emit = defineEmits(['update:modelValue', 'submitted'])

const modalVisible = ref(props.modelValue)
const { autoFocusInputRef } = useAutofocusInput(modalVisible)
const objToAdd = ref(null)
const searchComponent = ref(null)

const onSelect = (selectedValue) => {
  objToAdd.value = selectedValue
}

const onFormSubmit = () => {
  if (objToAdd.value) {
    emit('submitted', objToAdd.value)
    emit('update:modelValue', false)
    resetSearchComponent()
  } else {
    console.warn('No item selected to submit.')
  }
}

const onModalCancel = () => {
  resetSearchComponent()
}

const onModalToggle = (newVal) => {
  modalVisible.value = newVal
}

const resetSearchComponent = () => {
  if (searchComponent.value) {
    searchComponent.value.reset()
    objToAdd.value = null
  }
}

watch(
  () => props.modelValue,
  (newVal) => {
    modalVisible.value = newVal
  },
)

watch(modalVisible, (newVal) => {
  emit('update:modelValue', newVal)
})
</script>

<template>
  <CardBoxModal
    v-model="modalVisible"
    form
    :title="props.title"
    button="success"
    has-cancel
    has-search
    :button-label="t('common.add')"
    @form-submitted="onFormSubmit"
    @cancel="onModalCancel"
    @update:model-value="onModalToggle"
  >
    <FormField :label="props.label">
      <SearchControl
        :icon="props.icon"
        :placeholder="props.placeholder || t('common.searchPlaceholder')"
        :return-attribute="props.returnAttribute"
        :max-entries="props.maxEntries"
        :fetch-data="props.fetchData"
        :required="props.required"
        @update:model-value="onSelect"
        @set-ref="
          (ref) => {
            searchComponent = ref
            autoFocusInputRef = ref
          }
        "
      />
    </FormField>
  </CardBoxModal>
</template>
