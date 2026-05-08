<script setup>
import { computed } from 'vue'

import { colorsBgLight, colorsOutline } from '@/colors.js'
import PillTagPlain from '@/components/PillTagPlain.vue'

const props = defineProps({
  help: {
    type: String,
    required: false,
    default: null,
  },
  label: {
    type: String,
    required: false,
    default: null,
  },
  color: {
    type: String,
    required: true,
  },
  icon: {
    type: String,
    default: null,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  small: Boolean,
  outline: Boolean,
  handleClick: {
    type: Function,
    required: false,
    default: null,
  },
})

const componentClass = computed(() => [
  props.small ? 'py-1 px-3' : 'py-1.5 px-4',
  props.outline ? colorsOutline[props.color] : colorsBgLight[props.color],
  props.disabled ? '' : 'cursor-pointer',
])

const clickHandler = computed(() => (props.disabled ? null : props.handleClick))
</script>

<template>
  <PillTagPlain
    class="border rounded-full"
    :class="componentClass"
    :icon="icon"
    :label="label"
    :small="small"
    :aria-disabled="disabled"
    @click="clickHandler"
  />
</template>
