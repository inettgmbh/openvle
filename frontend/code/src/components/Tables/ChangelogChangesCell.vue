<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  changes: {
    type: Array,
    default: () => [],
  },
  formatFieldKey: {
    type: Function,
    required: true,
  },
  formatDisplayValue: {
    type: Function,
    required: true,
  },
  shortenMiddle: {
    type: Function,
    required: true,
  },
})

function hasChanges(changes) {
  return changes && Array.isArray(changes) && changes.length > 0
}
</script>

<template>
  <!-- No changes -->
  <span v-if="!hasChanges(changes)" class="italic text-gray-500">
    {{ t('components.changelog.noChanges') }}
  </span>

  <!-- Changes list -->
  <ul v-else class="space-y-1">
    <li v-for="(change, idx) in changes" :key="idx" class="changelog-item">
      <!-- Raw diff (unparseable) -->
      <template v-if="change.isRaw">
        <strong>{{ change.key }}:</strong>

        <div class="mt-1">
          <pre class="text-xs text-red-500">
- {{ shortenMiddle(change.oldValue) }}</pre
          >

          <pre class="text-xs text-green-600">
+ {{ shortenMiddle(change.newValue) }}</pre
          >
        </div>
      </template>

      <!-- Permission change -->
      <template v-else-if="change.isPermission">
        <div
          class="border-l-2 pl-2 py-0.5"
          :class="
            change.added
              ? 'border-green-500 dark:border-green-400'
              : 'border-red-500 dark:border-red-400'
          "
        >
          <div
            class="text-xs"
            :class="
              change.added
                ? 'text-green-600 dark:text-green-400'
                : 'text-red-600 dark:text-red-400'
            "
          >
            {{
              change.added
                ? t('components.changelog.permissionAdded')
                : t('components.changelog.permissionRemoved')
            }}
          </div>

          <div class="flex items-center gap-1">
            <strong>{{ change.permissionObjectType }}</strong>

            <span class="text-gray-400 dark:text-gray-500">·</span>

            <span>{{ change.permissionLabel }}</span>

            <span
              class="ml-1 text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 dark:bg-slate-700 dark:text-gray-400"
            >
              {{ change.permissionScope ? change.permissionScope : 'Global' }}
            </span>
          </div>
        </div>
      </template>

      <!-- Structured change -->
      <template v-else>
        <strong>{{ formatFieldKey(change.key) }}: </strong>

        <span class="inline-flex gap-2 items-center flex-wrap">
          <!-- Old value -->
          <s class="changelog-value">
            <template v-if="formatDisplayValue(change.oldValue).isEmpty">
              <span class="italic text-gray-500">
                {{ formatDisplayValue(change.oldValue).value }}
              </span>
            </template>

            <template v-else-if="formatDisplayValue(change.oldValue).isList">
              <ul class="list-disc list-inside">
                <li
                  v-for="(entry, entryIdx) in formatDisplayValue(
                    change.oldValue,
                  ).items"
                  :key="entryIdx"
                >
                  {{ shortenMiddle(entry) }}
                </li>
              </ul>
            </template>

            <template v-else>
              {{ shortenMiddle(formatDisplayValue(change.oldValue).value) }}
            </template>
          </s>

          <!-- Arrow -->
          <span class="text-2xl font-bold align-middle mx-1">→</span>

          <!-- New value -->
          <span class="changelog-value">
            <template v-if="formatDisplayValue(change.newValue).isEmpty">
              <span class="italic text-gray-500">
                {{ formatDisplayValue(change.newValue).value }}
              </span>
            </template>

            <template v-else-if="formatDisplayValue(change.newValue).isList">
              <ul class="list-disc list-inside">
                <li
                  v-for="(entry, entryIdx) in formatDisplayValue(
                    change.newValue,
                  ).items"
                  :key="entryIdx"
                >
                  {{ shortenMiddle(entry) }}
                </li>
              </ul>
            </template>

            <template v-else>
              {{ shortenMiddle(formatDisplayValue(change.newValue).value) }}
            </template>
          </span>
        </span>
      </template>
    </li>
  </ul>
</template>

<style scoped>
.changelog-item {
  line-height: 1.5;
}

.changelog-value {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}
</style>
