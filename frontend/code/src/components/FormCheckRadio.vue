<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: {
    type: String,
    required: true,
  },
  type: {
    type: String,
    default: 'checkbox',
    validator: (value) => ['checkbox', 'radio', 'switch'].includes(value),
  },
  label: {
    type: String,
    default: null,
  },
  modelValue: {
    type: [Array, String, Number, Boolean],
    default: null,
  },
  inputValue: {
    type: [String, Number, Boolean],
    default: true,
  },
  help: {
    type: String,
    default: null,
  },
})

const emit = defineEmits(['update:modelValue'])

const isChecked = computed(() => {
  if (props.type === 'radio') {
    return props.modelValue === props.inputValue
  }

  if (Array.isArray(props.modelValue)) {
    return props.modelValue.includes(props.inputValue)
  }

  if (typeof props.modelValue === 'boolean') {
    return props.modelValue
  }

  return false
})

function onChange(event) {
  const checked = event.target.checked

  if (props.type === 'radio') {
    emit('update:modelValue', props.inputValue)
  } else if (Array.isArray(props.modelValue)) {
    const newValue = [...props.modelValue]
    const index = newValue.indexOf(props.inputValue)
    if (checked && index === -1) {
      newValue.push(props.inputValue)
    } else if (!checked && index !== -1) {
      newValue.splice(index, 1)
    }
    emit('update:modelValue', newValue)
  } else if (typeof props.modelValue === 'boolean') {
    emit('update:modelValue', checked)
  } else {
    emit('update:modelValue', checked ? props.inputValue : null)
  }
}

const inputType = computed(() =>
  props.type === 'radio' ? 'radio' : 'checkbox',
)
</script>

<template>
  <label :class="type">
    <input
      :type="inputType"
      :name="name"
      :value="inputValue"
      :checked="isChecked"
      @change="onChange"
    />

    <span class="check" />

    <span class="pl-2">{{ label }}</span>
  </label>

  <div v-if="help" class="text-xs text-gray-500 dark:text-slate-400 mt-1">
    {{ help }}
  </div>
</template>
