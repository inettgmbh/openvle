<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import FormControlIcon from '@/components/FormControlIcon.vue'
import SearchField from '@/components/SearchField.vue'

const { t } = useI18n()

const formFieldContext = inject('formFieldControlContext', null)

const props = defineProps({
  name: {
    type: String,
    default: null,
  },
  id: {
    type: String,
    default: null,
  },
  icon: {
    type: String,
    default: null,
  },
  autofocus: Boolean,
  required: {
    type: Boolean,
    default: false,
  },
  disabled: Boolean,
  readonly: Boolean,
  modelValue: {
    type: [String, Number, Object, null],
    default: null,
  },
  fetchData: {
    type: Function,
    required: true,
  },
  fetchSelected: {
    type: Function,
    required: false,
    default: undefined,
  },
  maxEntries: {
    type: Number,
    default: 25,
  },
  returnAttribute: {
    type: String,
    default: 'id',
  },
  placeholder: {
    type: String,
    default: null,
  },
  ariaDescribedby: {
    type: String,
    default: null,
  },
  labelAttribute: {
    type: String,
    default: 'name',
  },
  allowCustomEntry: {
    type: Boolean,
    default: false,
  },
  formatter: {
    type: Function,
    default: (val) => val,
  },
  maxlength: {
    type: Number,
    default: null,
  },
  borders: {
    type: String,
    default: 'all',
    validator: (value) =>
      ['all', 'none', 'right', 'left', 'top/bottom'].includes(value),
  },
})

const emit = defineEmits(['input-started', 'update:modelValue', 'setRef'])

/**
 * We keep an internal ref that mirrors props.modelValue.
 * When the user selects something in SearchField, we update localValue
 * and emit 'update:modelValue' so v-model works in parent.
 */
const localValue = ref(props.modelValue)
const searchFieldRef = ref(null)

const fallbackId = `search-control-${Math.random().toString(36).slice(2, 9)}`
const effectiveId = computed(
  () => props.id || formFieldContext?.inputId?.value || fallbackId,
)
const effectiveDescribedby = computed(
  () =>
    props.ariaDescribedby || formFieldContext?.ariaDescribedby?.value || null,
)

const loadSelectedLabel = async (id) => {
  if (!props.fetchSelected || !id) return
  try {
    const selectedEntry = await props.fetchSelected(id)
    if (selectedEntry) {
      searchFieldRef.value?.setInitialDisplay(selectedEntry)
      localValue.value = id
      searchFieldRef.value?.setSelectedId(id)
    }
  } catch (error) {
    // Fallback: show truncated UUID with hint when fetch fails (e.g. 403)
    const shortId = id.length > 8 ? `${id.substring(0, 8)}...` : id
    searchFieldRef.value?.setInitialDisplay(
      `${shortId} (${t('common.noPermission')})`,
    )
    localValue.value = id
    searchFieldRef.value?.setSelectedId(id)
  }
}

watch(
  () => props.modelValue,
  async (newVal, oldVal) => {
    localValue.value = newVal

    if (newVal && !oldVal && props.fetchSelected) {
      await loadSelectedLabel(newVal)
    }
  },
  { immediate: true },
)

const onSelect = (selectedValue) => {
  localValue.value = selectedValue
  emit('update:modelValue', selectedValue)
}

const onInput = () => emit('input-started')

onMounted(() => {
  emit('setRef', searchFieldRef.value)
})

const inputElClass = computed(() => 'relative block w-full')
const controlIconH = computed(() => 'h-12')
</script>

<template>
  <div :class="inputElClass">
    <SearchField
      :id="effectiveId"
      ref="searchFieldRef"
      :allow-custom-entry="allowCustomEntry"
      :borders="borders"
      :formatter="formatter"
      :fetch-data="fetchData"
      :max-entries="maxEntries"
      :label-attribute="labelAttribute"
      :return-attribute="returnAttribute"
      :placeholder="placeholder"
      :required="props.required"
      :autofocus="autofocus"
      :icon="icon"
      :disabled="disabled"
      :aria-describedby="effectiveDescribedby"
      :maxlength="maxlength"
      @select="onSelect"
      @input="onInput"
    />

    <FormControlIcon v-if="icon" :icon="icon" :h="controlIconH" />

    <input v-if="name" type="hidden" :name="name" :value="localValue" />
  </div>
</template>
