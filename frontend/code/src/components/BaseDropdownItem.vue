<script setup>
import BaseIcon from '@/components/BaseIcon.vue'

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['select'])

const onClick = (e) => {
  if (props.disabled) {
    e.preventDefault()
    return
  }

  emit('select', props.item)

  if (props.item?.onClick) props.item.onClick()
}
</script>

<template>
  <button
    v-tooltip="
      disabled && item.disabledTooltip ? item.disabledTooltip : item.tooltip
    "
    type="button"
    class="w-full flex items-center gap-3 px-3 py-2 text-sm rounded-lg hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 ring-offset-2 ring-slate-300 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed text-slate-700 dark:text-slate-200"
    :aria-disabled="disabled ? 'true' : 'false'"
    :disabled="disabled"
    role="menuitem"
    @click="onClick"
  >
    <BaseIcon
      v-if="item.icon"
      class="shrink-0"
      w="18"
      h="18"
      :path="item.icon"
      aria-hidden="true"
      focusable="false"
    />

    <span class="truncate">{{ item.label }}</span>
  </button>
</template>
