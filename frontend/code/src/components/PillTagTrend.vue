<script setup>
import { mdiAlertCircleOutline, mdiChevronDown, mdiChevronUp } from '@mdi/js'
import { computed } from 'vue'

import PillTag from '@/components/PillTag.vue'

const props = defineProps({
  trend: {
    type: String,
    required: true,
  },
  trendType: {
    type: String,
    default: null,
  },
  small: Boolean,
})

const trendStyle = computed(() => {
  if (props.trendType === 'up') {
    return {
      icon: mdiChevronUp,
      style: 'success',
    }
  }

  if (props.trendType === 'down') {
    return {
      icon: mdiChevronDown,
      style: 'danger',
    }
  }

  if (props.trendType === 'alert') {
    return {
      icon: mdiAlertCircleOutline,
      style: 'warning',
    }
  }

  return {
    style: 'info',
  }
})
</script>

<template>
  <PillTag
    :label="trend"
    :color="trendStyle.style"
    :icon="trendStyle.icon"
    :small="small"
  />
</template>
