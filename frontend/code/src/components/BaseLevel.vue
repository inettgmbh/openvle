<script setup>
import { computed, useSlots } from 'vue'

defineOptions({ name: 'BaseLevel' })

const props = defineProps({
  mobile: Boolean,
  type: {
    type: String,
    default: 'justify-between',
  },
})

const slots = useSlots()

const parentClass = computed(() => {
  const base = [props.type, 'items-center']
  const layout = props.mobile ? ['flex'] : ['block', 'md:flex']
  return [...base, ...layout]
})

const getChildClass = (index, total) => {
  const base = ['flex', 'items-center', 'justify-center']
  if (!props.mobile && index < total - 1) {
    return [...base, 'mb-6', 'md:mb-0']
  }
  return base
}
</script>

<template>
  <div :class="parentClass">
    <template v-if="slots.default">
      <div
        v-for="(element, index) in slots.default?.()"
        :key="index"
        :class="getChildClass(index, slots.default().length)"
      >
        <component :is="element" />
      </div>
    </template>
  </div>
</template>
