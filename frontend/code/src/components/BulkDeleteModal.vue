<script setup>
import { mdiCheck, mdiClose, mdiLoading } from '@mdi/js'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseIcon from '@/components/BaseIcon.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxComponentTitle from '@/components/CardBoxComponentTitle.vue'
import OverlayLayer from '@/components/OverlayLayer.vue'
import { useStyleStore } from '@/stores/style.js'
import { executeBatched } from '@/utils/batchedExecution'

const { t } = useI18n()
const styleStore = useStyleStore()

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true,
  },
  items: {
    type: Array,
    required: true,
  },
  execute: {
    type: Function,
    required: true,
  },
  labelKey: {
    type: String,
    default: 'name',
  },
  batchSize: {
    type: Number,
    default: 3,
  },
  beginSilent: {
    type: Function,
    default: null,
  },
  endSilent: {
    type: Function,
    default: null,
  },
})

const emit = defineEmits(['update:modelValue', 'completed'])

const phase = ref('confirming')
const progress = ref({ current: 0, total: 0, errors: [] })
const snapshotCount = ref(0)

const progressPercent = computed(() => {
  if (progress.value.total === 0) return 0
  return Math.round((progress.value.current / progress.value.total) * 100)
})

const isDone = computed(() => phase.value === 'done' || phase.value === 'error')

const hasErrors = computed(() => progress.value.errors.length > 0)

const displayItems = computed(() => props.items.slice(0, 10))

const remainingCount = computed(() => Math.max(0, props.items.length - 10))

const componentClass = computed(() => {
  const base = [
    'shadow-lg w-11/12 md:w-3/5 lg:w-2/5 xl:w-4/12 z-50 flex flex-col',
    'max-h-screen md:max-h-[90vh]',
  ]
  if (styleStore.darkMode) base.push('dark')
  return base
})

const contentClass = computed(() => ({
  'space-y-3 flex-grow px-4': true,
  dark: styleStore.darkMode,
}))

async function handleDelete() {
  phase.value = 'deleting'
  progress.value = { current: 0, total: props.items.length, errors: [] }

  const operations = props.items.map((item) => () => props.execute(item))

  if (props.beginSilent) props.beginSilent()

  const { errors } = await executeBatched(operations, {
    batchSize: props.batchSize,
    onProgress: (completed) => {
      progress.value.current = completed
    },
  })

  if (props.endSilent) props.endSilent()

  if (errors.length > 0) {
    progress.value.errors = errors.map((e) => ({
      itemName: props.items[e.index]?.[props.labelKey] || `#${e.index + 1}`,
      error: e.error,
    }))
    phase.value = 'error'
  } else {
    phase.value = 'done'
  }

  emit('completed', {
    succeeded: props.items.length - errors.length,
    failed: errors.length,
    total: props.items.length,
  })
}

function handleClose() {
  if (phase.value === 'deleting') return
  emit('update:modelValue', false)
}

function handleKeydown(e) {
  if (e.key === 'Escape') {
    if (phase.value === 'deleting') return
    handleClose()
  }
}

onMounted(() => {
  if (props.modelValue) {
    snapshotCount.value = props.items.length
  }
})

// Reset state when modal opens/closes
watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) {
      phase.value = 'confirming'
      progress.value = { current: 0, total: 0, errors: [] }
      snapshotCount.value = props.items.length
      window.addEventListener('keydown', handleKeydown)
    } else {
      window.removeEventListener('keydown', handleKeydown)
    }
  },
)
</script>

<template>
  <OverlayLayer v-show="modelValue" @overlay-click="handleClose">
    <CardBox v-show="modelValue" :class="componentClass" is-modal>
      <CardBoxComponentTitle
        :title="t('components.bulkDeleteModal.title', { count: snapshotCount })"
      >
        <BaseButton
          v-if="phase === 'confirming'"
          :icon="mdiClose"
          color="whiteDark"
          small
          rounded-full
          @click.prevent="handleClose"
        />
      </CardBoxComponentTitle>

      <div :class="[contentClass, 'max-h-[calc(80vh-100px)]']">
        <!-- Phase: Confirming -->
        <template v-if="phase === 'confirming'">
          <slot name="warning" />

          <slot name="description" />

          <ul
            class="text-sm text-gray-700 dark:text-gray-300 space-y-1 max-h-48 overflow-y-auto"
          >
            <li v-for="item in displayItems" :key="item.id || item[labelKey]">
              &bull; {{ item[labelKey] }}
            </li>

            <li
              v-if="remainingCount > 0"
              class="text-gray-500 dark:text-gray-400 italic"
            >
              ...
              {{
                t('components.bulkDeleteModal.andMore', {
                  count: remainingCount,
                })
              }}
            </li>
          </ul>

          <p class="text-sm text-gray-600 dark:text-gray-400">
            {{ t('components.bulkDeleteModal.areYouSure') }}
          </p>
        </template>

        <!-- Phase: Deleting / Done / Error -->
        <template v-else>
          <div class="py-4 overflow-y-auto">
            <!-- Status icon + label -->
            <div class="flex items-center gap-3 mb-6">
              <div
                class="w-10 h-10 rounded-full flex items-center justify-center"
                :class="[
                  phase === 'done'
                    ? 'bg-green-100 dark:bg-green-900/30'
                    : phase === 'error'
                      ? 'bg-red-100 dark:bg-red-900/30'
                      : 'bg-blue-100 dark:bg-blue-900/30',
                ]"
              >
                <BaseIcon
                  v-if="phase === 'done'"
                  :path="mdiCheck"
                  class="text-green-600 dark:text-green-400"
                  :size="24"
                />

                <BaseIcon
                  v-else-if="phase === 'error'"
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
                <h3
                  class="text-lg font-semibold text-gray-900 dark:text-gray-100"
                >
                  {{
                    phase === 'deleting'
                      ? t('components.bulkDeleteModal.removing')
                      : phase === 'done'
                        ? t('components.bulkDeleteModal.completed')
                        : t('components.bulkDeleteModal.errorsOccurred')
                  }}
                </h3>

                <p class="text-sm text-gray-500 dark:text-gray-400">
                  {{ progress.current }} / {{ progress.total }}
                </p>
              </div>
            </div>

            <!-- Progress bar -->
            <div class="mb-4">
              <div
                class="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-2"
              >
                <span> {{ progress.current }} / {{ progress.total }} </span>

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
                      : phase === 'done'
                        ? 'bg-green-500'
                        : 'bg-blue-500',
                  ]"
                  :style="{ width: `${progressPercent}%` }"
                />
              </div>
            </div>

            <!-- Error summary -->
            <div
              v-if="hasErrors"
              class="mt-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800"
            >
              <p
                class="text-sm font-medium text-red-800 dark:text-red-200 mb-2"
              >
                {{
                  t('components.bulkDeleteModal.errorCount', {
                    count: progress.errors.length,
                  })
                }}
              </p>

              <ul
                class="text-xs text-red-700 dark:text-red-300 space-y-1 max-h-24 overflow-y-auto"
              >
                <li v-for="(err, idx) in progress.errors" :key="idx">
                  {{ err.itemName }}:
                  {{
                    err.error?.response?.data?.detail ||
                    err.error?.message ||
                    t('components.bulkDeleteModal.unknownError')
                  }}
                </li>
              </ul>
            </div>
          </div>
        </template>
      </div>

      <!-- Footer -->
      <template #footer>
        <BaseButtons>
          <BaseButton
            v-if="phase === 'confirming'"
            :label="t('common.remove')"
            color="danger"
            @click="handleDelete"
          />

          <BaseButton
            v-if="phase === 'confirming'"
            :label="t('common.cancel')"
            color="info"
            outline
            @click="handleClose"
          />

          <BaseButton
            v-if="isDone"
            :label="hasErrors ? t('common.close') : t('common.done')"
            :color="hasErrors ? 'danger' : 'success'"
            @click="handleClose"
          />
        </BaseButtons>
      </template>
    </CardBox>
  </OverlayLayer>
</template>
