<script setup>
import { mdiChevronDown, mdiChevronUp } from '@mdi/js'

const props = defineProps({
  objectType: { type: String, required: true },
  objectEntries: { type: Array, default: () => [] },
  expanded: { type: Boolean, default: false },
  isEditing: { type: Boolean, default: false },
  getObjectTypeLabel: { type: Function, required: true },
  objectEntriesAllowed: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle-expanded'])
</script>

<template>
  <tr class="border-t border-gray-200 dark:border-gray-700">
    <td class="px-4 py-3 align-top">
      <div class="font-medium text-gray-900 dark:text-gray-100">
        {{ getObjectTypeLabel(objectType) }}
      </div>

      <div class="text-xs text-gray-500 dark:text-gray-400">
        {{ $t('components.permissionMatrixRow.globalHint') }}
      </div>
    </td>

    <td class="px-4 py-3 align-top">
      <slot name="global" />
    </td>

    <td class="px-4 py-3 align-top whitespace-nowrap">
      <button
        v-if="objectEntries.length"
        type="button"
        class="w-[130px] px-2.5 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 text-xs hover:bg-gray-50 dark:hover:bg-gray-800 bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300 inline-flex items-center justify-center gap-1.5"
        @click="emit('toggle-expanded')"
      >
        <svg
          viewBox="0 0 24 24"
          class="w-3.5 h-3.5 flex-shrink-0"
          fill="currentColor"
          aria-hidden="true"
        >
          <path :d="expanded ? mdiChevronUp : mdiChevronDown" />
        </svg>

        <span>{{
          expanded
            ? $t('components.permissionMatrixRow.collapse')
            : $t('components.permissionMatrixRow.expand')
        }}</span>

        <span
          class="ml-auto tabular-nums bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded text-[10px] font-medium"
        >
          {{ objectEntries.length }}
        </span>
      </button>

      <span
        v-else-if="!objectEntriesAllowed"
        v-tooltip="$t('components.permissionMatrixRow.notPossibleTooltip')"
        class="text-gray-400 dark:text-gray-500 text-sm italic"
        >{{ $t('components.permissionMatrixRow.notPossible') }}</span
      >

      <span
        v-else
        v-tooltip="$t('components.permissionMatrixRow.noneAvailableTooltip')"
        class="text-gray-400 dark:text-gray-500 text-sm italic"
        >{{ $t('components.permissionMatrixRow.noneAvailable') }}</span
      >
    </td>
  </tr>

  <tr
    v-if="objectEntries.length && expanded"
    class="border-t border-gray-200 dark:border-gray-700 bg-gray-50/40 dark:bg-gray-800/40"
  >
    <td colspan="3" class="px-4 py-4">
      <slot name="expanded" />
    </td>
  </tr>
</template>
