<script setup>
import BaseIcon from '@/components/BaseIcon.vue'

defineProps({
  icon: {
    type: String,
    required: true,
  },
  value: {
    type: [Number, String],
    required: true,
  },
  label: {
    type: String,
    required: true,
  },
  subtitle: {
    type: String,
    default: null,
  },
  color: {
    type: String,
    default: 'blue',
    validator: (value) =>
      ['blue', 'emerald', 'amber', 'red', 'orange'].includes(value),
  },
})

// Color mappings for different states
const colorClasses = {
  blue: {
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    border: 'border-blue-200 dark:border-blue-800',
    iconBg: 'bg-blue-100 dark:bg-blue-800/50',
    iconText: 'text-blue-600 dark:text-blue-400',
    label: 'text-blue-600 dark:text-blue-400',
    subtitle: 'text-blue-500/70 dark:text-blue-400/70',
  },
  emerald: {
    bg: 'bg-emerald-50 dark:bg-emerald-900/20',
    border: 'border-emerald-200 dark:border-emerald-800',
    iconBg: 'bg-emerald-100 dark:bg-emerald-800/50',
    iconText: 'text-emerald-600 dark:text-emerald-400',
    label: 'text-emerald-600 dark:text-emerald-400',
    subtitle: 'text-emerald-500/70 dark:text-emerald-400/70',
  },
  amber: {
    bg: 'bg-amber-50 dark:bg-amber-900/20',
    border: 'border-amber-200 dark:border-amber-800',
    iconBg: 'bg-amber-100 dark:bg-amber-800/50',
    iconText: 'text-amber-600 dark:text-amber-400',
    label: 'text-amber-600 dark:text-amber-400',
    subtitle: 'text-amber-500/70 dark:text-amber-400/70',
  },
  red: {
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-200 dark:border-red-800',
    iconBg: 'bg-red-100 dark:bg-red-800/50',
    iconText: 'text-red-600 dark:text-red-400',
    label: 'text-red-600 dark:text-red-400',
    subtitle: 'text-red-500/70 dark:text-red-400/70',
  },
  orange: {
    bg: 'bg-orange-50 dark:bg-orange-900/20',
    border: 'border-orange-200 dark:border-orange-800',
    iconBg: 'bg-orange-100 dark:bg-orange-800/50',
    iconText: 'text-orange-600 dark:text-orange-400',
    label: 'text-orange-600 dark:text-orange-400',
    subtitle: 'text-orange-500/70 dark:text-orange-400/70',
  },
}
</script>

<template>
  <div
    :class="[
      'rounded-lg p-4 border',
      colorClasses[color].bg,
      colorClasses[color].border,
    ]"
  >
    <div class="flex items-center gap-3">
      <div :class="['p-2 rounded-lg shrink-0', colorClasses[color].iconBg]">
        <BaseIcon
          :path="icon"
          size="20"
          :class="colorClasses[color].iconText"
        />
      </div>

      <div>
        <div class="text-2xl font-bold text-gray-900 dark:text-slate-100">
          {{ value }}
        </div>

        <div :class="['text-xs', colorClasses[color].label]">
          {{ label }}
        </div>

        <div v-if="subtitle" :class="['text-xs', colorClasses[color].subtitle]">
          {{ subtitle }}
        </div>
      </div>
    </div>
  </div>
</template>
