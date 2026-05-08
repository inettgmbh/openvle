<script setup>
import { mdiCheck, mdiClose, mdiLoading } from '@mdi/js'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseIcon from '@/components/BaseIcon.vue'
import CardBox from '@/components/CardBox.vue'
import OverlayLayer from '@/components/OverlayLayer.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  progress: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['update:modelValue', 'close'])

const progressPercent = computed(() => {
  if (props.progress.total === 0) return 0
  return Math.round((props.progress.current / props.progress.total) * 100)
})

const { t } = useI18n()

const phaseLabels = computed(() => ({
  idle: t('components.saveProgressModal.phaseIdle'),
  deleting: t('components.saveProgressModal.phaseDeleting'),
  creating: t('components.saveProgressModal.phaseCreating'),
  refreshing: t('components.saveProgressModal.phaseRefreshing'),
  done: t('components.saveProgressModal.phaseDone'),
  error: t('components.saveProgressModal.phaseError'),
}))

const phaseLabel = computed(() => phaseLabels.value[props.progress.phase] || '')

const isDone = computed(() => props.progress.phase === 'done')
const hasErrors = computed(() => props.progress.errors?.length > 0)

const canClose = computed(() => isDone.value || hasErrors.value)

function handleClose() {
  if (canClose.value) {
    emit('update:modelValue', false)
    emit('close')
  }
}

const componentClass = computed(() => {
  return ['shadow-lg', 'w-11/12', 'md:w-2/5', 'lg:w-1/3', 'z-50']
})
</script>

<template>
  <OverlayLayer v-show="modelValue">
    <CardBox :class="componentClass" is-modal>
      <div class="p-6">
        <!-- Header -->
        <div class="flex items-center gap-3 mb-6">
          <div
            class="w-10 h-10 rounded-full flex items-center justify-center"
            :class="[
              isDone && !hasErrors
                ? 'bg-green-100 dark:bg-green-900/30'
                : hasErrors
                  ? 'bg-red-100 dark:bg-red-900/30'
                  : 'bg-blue-100 dark:bg-blue-900/30',
            ]"
          >
            <BaseIcon
              v-if="isDone && !hasErrors"
              :path="mdiCheck"
              class="text-green-600 dark:text-green-400"
              :size="24"
            />

            <BaseIcon
              v-else-if="hasErrors"
              :path="mdiClose"
              class="text-red-600 dark:text-red-400"
              :size="24"
            />

            <BaseIcon
              v-else
              :path="mdiLoading"
              class="text-blue-600 dark:text-blue-400 animate-spin"
              :size="24"
            />
          </div>

          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {{ t('components.saveProgressModal.title') }}
            </h3>

            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ phaseLabel }}
            </p>
          </div>
        </div>

        <!-- Progress Bar -->
        <div class="mb-4">
          <div
            class="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-2"
          >
            <span>{{ progress.current }} / {{ progress.total }}</span>

            <span>{{ progressPercent }}%</span>
          </div>

          <div
            class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden"
          >
            <div
              class="h-full rounded-full transition-all duration-300 ease-out"
              :class="[
                hasErrors
                  ? 'bg-red-500'
                  : isDone
                    ? 'bg-green-500'
                    : 'bg-blue-500',
              ]"
              :style="{ width: `${progressPercent}%` }"
            />
          </div>
        </div>

        <!-- Error Summary -->
        <div
          v-if="hasErrors"
          class="mt-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800"
        >
          <p class="text-sm font-medium text-red-800 dark:text-red-200 mb-2">
            {{
              t('components.saveProgressModal.errorsOccurred', {
                count: progress.errors.length,
              })
            }}
          </p>

          <ul
            class="text-xs text-red-700 dark:text-red-300 space-y-1 max-h-24 overflow-y-auto"
          >
            <li v-for="(err, idx) in progress.errors" :key="idx">
              {{
                t('components.saveProgressModal.operationIndex', {
                  index: err.index + 1,
                })
              }}:
              {{
                err.error?.message ||
                t('components.saveProgressModal.unknownError')
              }}
            </li>

            <li>
              {{ t('components.saveProgressModal.errorHint') }}
            </li>
          </ul>
        </div>

        <!-- Close Button -->
        <div v-if="canClose" class="mt-6 flex justify-center">
          <button
            type="button"
            class="px-4 py-2 text-sm font-medium rounded-lg transition-colors"
            :class="[
              hasErrors
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-green-600 hover:bg-green-700 text-white',
            ]"
            @click="handleClose"
          >
            {{ hasErrors ? t('common.close') : t('common.done') }}
          </button>
        </div>
      </div>
    </CardBox>
  </OverlayLayer>
</template>
