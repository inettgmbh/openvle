<script setup>
import { computed, useSlots } from 'vue'

defineOptions({ name: 'BaseButtons' })

const props = defineProps({
  noWrap: Boolean,
  type: {
    type: String,
    default: 'justify-start',
  },
  classAddon: {
    type: String,
    default: 'mr-3 last:mr-0 mb-3',
  },
  mb: {
    type: String,
    default: '-mb-3',
  },
})

const slots = useSlots()

const parentClass = computed(() => [
  'flex',
  'items-center',
  props.type,
  props.noWrap ? 'flex-nowrap' : 'flex-wrap',
  props.mb,
])
</script>

<template>
  <div :class="parentClass">
    <template v-if="slots.default">
      <template v-for="(element, index) in slots.default?.()" :key="index">
        <template v-if="Array.isArray(element?.children)">
          <component
            :is="child"
            v-for="(child, childIndex) in element.children"
            :key="`${index}-${childIndex}`"
            :class="classAddon"
          />
        </template>

        <component :is="element" v-else :key="index" :class="classAddon" />
      </template>
    </template>
  </div>
</template>
