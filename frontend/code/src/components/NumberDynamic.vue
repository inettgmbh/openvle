<script setup>
import numeral from 'numeral'
import { computed, onMounted, ref, watch } from 'vue'

import { formatGermanNumber } from '@/utils/dataUtils'

const props = defineProps({
  prefix: {
    type: String,
    default: null,
  },
  suffix: {
    type: String,
    default: null,
  },
  value: {
    type: Number,
    default: 0,
  },
  duration: {
    type: Number,
    default: 500,
  },
})

const newValue = ref(0)

const newValueFormatted = computed(() =>
  newValue.value < 1000
    ? newValue.value
    : numeral(newValue.value).format('0,0'),
)

const value = computed(() => props.value)

const grow = (m) => {
  const v = Math.ceil(newValue.value + m)

  if (v > value.value) {
    newValue.value = value.value
    return false
  }

  newValue.value = v

  setTimeout(() => {
    grow(m)
  }, 25)
}

const growInit = () => {
  newValue.value = 0
  grow(props.value / (props.duration / 25))
}

watch(value, () => {
  growInit()
})

onMounted(() => {
  growInit()
})
</script>

<template>
  <div>{{ prefix }}{{ formatGermanNumber(newValueFormatted) }}{{ suffix }}</div>
</template>
