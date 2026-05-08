<script setup>
import { computed, unref } from 'vue'

import FormCheckRadio from '@/components/FormCheckRadio.vue'

const props = defineProps({
  options: {
    type: [Array, Object],
    default: () => [],
  },
  name: {
    type: String,
    required: true,
  },
  type: {
    type: String,
    default: 'checkbox',
    validator: (value) => ['checkbox', 'radio', 'switch'].includes(value),
  },
  componentClass: {
    type: String,
    default: null,
  },
  isColumn: Boolean,
  modelValue: {
    type: [Array, String, Number, Boolean],
    default: null,
  },
})

const emit = defineEmits(['update:modelValue'])

const computedValue = computed({
  get: () => props.modelValue,
  set: (value) => {
    emit('update:modelValue', value)
  },
})

const resolvedOptions = computed(() => {
  const unwrapped = unref(props.options)

  if (unwrapped && typeof unwrapped === 'object' && !Array.isArray(unwrapped)) {
    return Object.entries(unwrapped).map(([key, label]) => ({
      value: key,
      label,
    }))
  }

  return Array.isArray(unwrapped) ? unwrapped : []
})
</script>

<template>
  <div
    class="flex justify-start flex-wrap -mb-3"
    :class="{ 'flex-col': isColumn }"
  >
    <FormCheckRadio
      v-for="option in resolvedOptions"
      :key="option.value"
      v-model="computedValue"
      :type="type"
      :name="name"
      :input-value="option.value"
      :label="option.label"
    />
  </div>
</template>
