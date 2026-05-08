<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  type: {
    type: String,
    default: 'td',
  },
  modelValue: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['checked'])

const checked = ref(props.modelValue)

watch(
  () => props.modelValue,
  (newVal) => {
    checked.value = newVal
  },
)

watch(checked, (newVal) => {
  emit('checked', newVal)
})
</script>

<template>
  <component :is="type" class="lg:w-1">
    <label class="checkbox">
      <input v-model="checked" type="checkbox" />

      <span class="check" />
    </label>
  </component>
</template>
