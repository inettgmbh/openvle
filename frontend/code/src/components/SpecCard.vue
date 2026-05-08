<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseIcon from '@/components/BaseIcon.vue'

const { t } = useI18n()

const props = defineProps({
  icon: {
    type: String,
    required: true,
  },
  value: {
    type: [String, Number],
    required: true,
  },
  label: {
    type: String,
    required: true,
  },
  link: {
    type: String,
    default: null,
  },
  hint: {
    type: String,
    default: null,
  },
  copyable: Boolean,
  color: {
    type: String,
    default: 'blue',
    validator: (v) =>
      [
        'blue',
        'emerald',
        'amber',
        'violet',
        'rose',
        'sky',
        'slate',
        'cyan',
      ].includes(v),
  },
})

const colorClasses = computed(() => {
  const map = {
    blue: {
      bg: 'bg-blue-50 dark:bg-blue-900/30',
      icon: 'text-blue-500 dark:text-blue-400',
      hover: 'hover:border-blue-400 dark:hover:border-blue-500',
    },
    emerald: {
      bg: 'bg-emerald-50 dark:bg-emerald-900/30',
      icon: 'text-emerald-500 dark:text-emerald-400',
      hover: 'hover:border-emerald-400 dark:hover:border-emerald-500',
    },
    amber: {
      bg: 'bg-amber-50 dark:bg-amber-900/30',
      icon: 'text-amber-500 dark:text-amber-400',
      hover: 'hover:border-amber-400 dark:hover:border-amber-500',
    },
    violet: {
      bg: 'bg-violet-50 dark:bg-violet-900/30',
      icon: 'text-violet-500 dark:text-violet-400',
      hover: 'hover:border-violet-400 dark:hover:border-violet-500',
    },
    rose: {
      bg: 'bg-rose-50 dark:bg-rose-900/30',
      icon: 'text-rose-500 dark:text-rose-400',
      hover: 'hover:border-rose-400 dark:hover:border-rose-500',
    },
    sky: {
      bg: 'bg-sky-50 dark:bg-sky-900/30',
      icon: 'text-sky-500 dark:text-sky-400',
      hover: 'hover:border-sky-400 dark:hover:border-sky-500',
    },
    slate: {
      bg: 'bg-slate-100 dark:bg-slate-700/40',
      icon: 'text-slate-500 dark:text-slate-400',
      hover: 'hover:border-slate-400 dark:hover:border-slate-500',
    },
    cyan: {
      bg: 'bg-cyan-50 dark:bg-cyan-900/30',
      icon: 'text-cyan-500 dark:text-cyan-400',
      hover: 'hover:border-cyan-400 dark:hover:border-cyan-500',
    },
  }
  return map[props.color]
})

const copied = ref(false)

async function handleDblClick() {
  if (!props.copyable || !props.value) return
  await navigator.clipboard.writeText(String(props.value))
  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 1500)
}
</script>

<template>
  <component
    :is="link ? 'router-link' : 'div'"
    :to="link"
    class="relative flex h-full flex-col items-center rounded-xl border border-gray-200 bg-white px-4 py-4 shadow-sm dark:border-slate-700 dark:bg-slate-800"
    :class="[
      link ? `transition-all hover:shadow-md ${colorClasses.hover}` : '',
      copyable ? 'select-none' : '',
    ]"
    @dblclick="handleDblClick"
  >
    <!-- Copy feedback overlay -->
    <Transition name="fade">
      <span
        v-if="copied"
        class="absolute inset-0 flex items-center justify-center rounded-xl bg-white/90 text-sm font-medium text-emerald-600 dark:bg-slate-800/90 dark:text-emerald-400"
      >
        {{ t('common.copied') }}
      </span>
    </Transition>
    <!-- Top: icon -->
    <span
      class="flex size-9 shrink-0 items-center justify-center rounded-lg"
      :class="colorClasses.bg"
    >
      <BaseIcon :path="icon" size="18" :class="colorClasses.icon" />
    </span>

    <!-- Middle: value (fills remaining space, vertically centered) -->
    <span
      class="flex flex-1 items-center py-2 text-center text-xl font-semibold tracking-tight text-gray-900 dark:text-white"
    >
      {{ value }}
    </span>

    <!-- Bottom: hint + label (fixed at bottom) -->
    <div class="flex shrink-0 flex-col items-center">
      <span
        v-if="hint"
        class="mb-1 text-center text-[10px] italic text-gray-400 dark:text-slate-500"
      >
        {{ hint }}
      </span>

      <span
        class="text-xs font-medium uppercase tracking-wide text-gray-400 dark:text-slate-500"
      >
        {{ label }}
      </span>
    </div>
  </component>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
