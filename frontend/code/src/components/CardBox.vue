<script setup>
import { computed, useSlots } from 'vue'

import CardBoxComponentBody from '@/components/CardBoxComponentBody.vue'
import CardBoxComponentFooter from '@/components/CardBoxComponentFooter.vue'
import { useStyleStore } from '@/stores/style.js'

const styleStore = useStyleStore()

const props = defineProps({
  rounded: {
    type: String,
    default: 'rounded-2xl',
  },
  flex: {
    type: String,
    default: 'flex-col',
  },
  hasComponentLayout: Boolean,
  hasTable: Boolean,
  hasSearch: Boolean,
  isForm: Boolean,
  isHoverable: Boolean,
  isModal: Boolean,
})

const emit = defineEmits(['submit'])

const slots = useSlots()

const hasFooterSlot = computed(() => slots.footer && !!slots.footer())

const componentClass = computed(() => {
  const base = [props.rounded, props.flex]

  if (styleStore.darkMode) {
    base.push(
      styleStore.darkText,
      props.isModal ? styleStore.darkBgModal : styleStore.darkBg,
    )
  } else {
    base.push(styleStore.whiteBg)
  }

  if (props.isHoverable) {
    base.push('hover:shadow-lg transition-shadow duration-500')
  }

  return base
})

const submit = (event) => {
  emit('submit', event)
}
</script>

<template>
  <component
    :is="isForm ? 'form' : 'div'"
    :class="componentClass"
    class="flex"
    @submit="submit"
  >
    <slot v-if="hasComponentLayout" />

    <template v-else>
      <CardBoxComponentBody
        :no-padding="hasTable"
        :is-modal="isModal"
        :has-search="hasSearch"
      >
        <slot />
      </CardBoxComponentBody>

      <CardBoxComponentFooter v-if="hasFooterSlot">
        <slot name="footer" />
      </CardBoxComponentFooter>
    </template>
  </component>
</template>
