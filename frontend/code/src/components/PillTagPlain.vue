<script setup>
import { computed } from 'vue'

import BaseIcon from '@/components/BaseIcon.vue'

const props = defineProps({
  label: {
    type: String,
    required: false,
    default: null,
  },
  icon: {
    type: String,
    default: null,
  },
  small: Boolean,
})

const hasLabel = computed(() => !!props.label)
</script>

<template>
  <div
    class="inline-flex items-center capitalize leading-none"
    :class="[small ? 'text-xs' : 'text-sm']"
  >
    <BaseIcon
      v-if="icon"
      :path="icon"
      h="h-4"
      w="w-4"
      :class="[
        small ? 'h-3.5 w-3.5' : '',
        hasLabel ? (small ? 'mr-1' : 'mr-2') : '',
      ]"
      :size="small ? 14 : null"
    />

    <span v-if="label">{{ label }}</span>
  </div>
</template>
