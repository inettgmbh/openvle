<script setup>
import { computed } from 'vue'

import {
  gradientBgBlueGreen,
  gradientBgDarkGray,
  gradientBgPinkRed,
  gradientBgPurplePink,
} from '@/colors'
import { useStyleStore } from '@/stores/style'

const props = defineProps({
  bg: {
    type: String,
    required: false,
    default: null,
    validator: (value) =>
      ['purplePink', 'pinkRed', 'blueGreen'].includes(value),
  },
  backgroundImage: {
    type: String,
    required: false,
    default: null,
  },
})

const colorClass = computed(() => {
  if (useStyleStore().darkMode) {
    return gradientBgDarkGray
  }

  switch (props.bg) {
    case 'purplePink':
      return gradientBgPurplePink
    case 'pinkRed':
      return gradientBgPinkRed
    case 'blueGreen':
      return gradientBgBlueGreen
  }

  return ''
})

const backgroundStyle = computed(() => {
  if (props.backgroundImage) {
    return {
      backgroundImage: `url(${props.backgroundImage})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
    }
  }

  return {}
})
</script>

<template>
  <div
    class="relative flex min-h-screen items-center justify-center"
    :class="colorClass"
    :style="backgroundStyle"
  >
    <slot card-class="w-11/12 md:w-7/12 lg:w-6/12 xl:w-4/12 shadow-2xl" />
  </div>
</template>
