<script setup>
import { mdiInformation } from '@mdi/js'
import { computed, provide, useId, useSlots } from 'vue'

import BaseIcon from '@/components/BaseIcon.vue'

const props = defineProps({
  label: {
    type: String,
    default: null,
  },
  labelFor: {
    type: String,
    default: null,
  },
  help: {
    type: String,
    default: null,
  },
  tooltip: {
    type: String,
    default: null,
  },
})

const slots = useSlots()
const uid = useId()

const inputId = computed(() => props.labelFor || `input-${uid}`)
const helpId = computed(() => (props.help ? `help-${uid}` : null))
const tooltipId = computed(() => (props.tooltip ? `tooltip-${uid}` : null))

const ariaDescribedby = computed(
  () => [helpId.value, tooltipId.value].filter(Boolean).join(' ') || null,
)

const wrapperClass = computed(() => {
  const length = slots.default?.()?.length || 0
  const base = []

  if (length > 1) base.push('grid grid-cols-1 gap-3')
  if (length === 2) base.push('md:grid-cols-2')

  return base
})

provide('formFieldControlContext', {
  inputId,
  ariaDescribedby,
})
</script>

<template>
  <div class="mb-6 last:mb-0">
    <div class="flex items-center gap-2">
      <label v-if="label" :for="inputId" class="block font-bold mb-2">
        {{ label }}
      </label>

      <span
        v-if="tooltip"
        :id="tooltipId"
        v-tooltip="{ text: tooltip }"
        class="cursor-pointer text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-white"
      >
        <BaseIcon
          :path="mdiInformation"
          w="w-10 md:w-5"
          h="h-10 md:h-5"
          size="24"
          class="md:mr-2"
        />
      </span>
    </div>

    <div :class="wrapperClass">
      <slot />
    </div>

    <div
      v-if="help"
      :id="helpId"
      class="text-xs text-gray-500 dark:text-slate-400 mt-1"
    >
      {{ help }}
    </div>
  </div>
</template>
