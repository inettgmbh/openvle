<script setup>
import { mdiCheck, mdiClose, mdiCloseCircle, mdiLoading } from '@mdi/js'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseIcon from '@/components/BaseIcon.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxComponentTitle from '@/components/CardBoxComponentTitle.vue'
import FormField from '@/components/FormField.vue'
import OverlayLayer from '@/components/OverlayLayer.vue'
import SearchControl from '@/components/SearchControl.vue'
import UnsavedChangesModal from '@/components/UnsavedChangesModal.vue'
import { useBatchAdd } from '@/composables/useBatchAdd'
import { useStyleStore } from '@/stores/style.js'

const { t } = useI18n()
const styleStore = useStyleStore()

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true,
  },
  title: {
    type: String,
    required: true,
  },
  fetchData: {
    type: Function,
    required: true,
  },
  execute: {
    type: Function,
    required: true,
  },
  idKey: {
    type: String,
    default: 'id',
  },
  labelKey: {
    type: String,
    default: 'name',
  },
  returnAttribute: {
    type: String,
    default: 'id',
  },
  searchIcon: {
    type: String,
    default: null,
  },
  searchLabel: {
    type: String,
    default: null,
  },
  batchSize: {
    type: Number,
    default: 3,
  },
  existingIds: {
    type: Array,
    default: () => [],
  },
  maxEntries: {
    type: Number,
    default: 25,
  },
  isSkippable: {
    type: Function,
    default: null,
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

const emit = defineEmits(['update:modelValue', 'saved'])

const searchControlRef = ref(null)
const searchValue = ref(null)
const lastSearchResults = ref([])

const {
  selectedItems,
  phase,
  progress,
  addItem,
  removeItem,
  hasItem,
  performSave,
  reset,
} = useBatchAdd({
  execute: (item) => props.execute(item),
  onComplete: (result) => emit('saved', result),
  isSkippable: props.isSkippable,
  beginSilent: props.beginSilent,
  endSilent: props.endSilent,
  idKey: props.idKey,
  batchSize: props.batchSize,
})

const progressPercent = computed(() => {
  if (progress.value.total === 0) return 0
  return Math.round((progress.value.current / progress.value.total) * 100)
})

const isDone = computed(() => phase.value === 'done' || phase.value === 'error')

const hasErrors = computed(() => progress.value.errors?.length > 0)

// Wrap fetchData to cache results for display name lookup
async function wrappedFetchData(query) {
  const result = await props.fetchData(query)
  lastSearchResults.value = result.items
  return result
}

// When SearchControl emits a value, find the full item from cache
watch(searchValue, (newVal) => {
  if (!newVal) return

  const fullItem = lastSearchResults.value.find(
    (item) => item[props.returnAttribute] === newVal,
  )

  if (fullItem) {
    if (props.existingIds.includes(fullItem[props.idKey])) {
      // Already exists on the object — ignore
      resetSearchControl()
      return
    }

    // Store display name for chips and error messages
    const enriched = {
      ...fullItem,
      _displayName: fullItem[props.labelKey] || fullItem[props.idKey],
    }
    addItem(enriched)
  }

  resetSearchControl()
})

function resetSearchControl() {
  searchValue.value = null
  searchControlRef.value?.setInitialDisplay('')
  searchControlRef.value?.setSelectedId('')
}

const showDiscardModal = ref(false)

function handleClose() {
  if (phase.value === 'saving') return
  if (phase.value === 'selecting' && selectedItems.value.length > 0) {
    showDiscardModal.value = true
    return
  }
  emit('update:modelValue', false)
}

function confirmDiscard() {
  showDiscardModal.value = false
  emit('update:modelValue', false)
}

function cancelDiscard() {
  showDiscardModal.value = false
}

function handleKeydown(e) {
  if (e.key === 'Escape') {
    if (phase.value === 'saving') return
    handleClose()
  }
}

// Reset state when modal opens/closes
watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) {
      reset()
      lastSearchResults.value = []
      searchValue.value = null
      showDiscardModal.value = false
      window.addEventListener('keydown', handleKeydown)
    } else {
      window.removeEventListener('keydown', handleKeydown)
    }
  },
)

async function handleSave() {
  await performSave()
}

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
</script>

<template>
  <OverlayLayer v-show="modelValue" @overlay-click="handleClose">
    <CardBox v-show="modelValue" :class="componentClass" is-modal has-search>
      <CardBoxComponentTitle :title="title">
        <BaseButton
          v-if="phase === 'selecting'"
          :icon="mdiClose"
          color="whiteDark"
          small
          rounded-full
          @click.prevent="handleClose"
        />
      </CardBoxComponentTitle>

      <div :class="[contentClass, 'max-h-[calc(80vh-100px)]']">
        <!-- Phase: Selecting -->
        <template v-if="phase === 'selecting'">
          <slot name="warning" />

          <slot name="options" />

          <!-- Search -->
          <FormField :label="searchLabel">
            <SearchControl
              v-model="searchValue"
              :fetch-data="wrappedFetchData"
              :icon="searchIcon"
              :return-attribute="returnAttribute"
              :max-entries="maxEntries"
              @set-ref="(ref) => (searchControlRef = ref)"
            />
          </FormField>

          <!-- Selected items as chips -->
          <div v-if="selectedItems.length > 0" class="space-y-2">
            <p class="text-xs font-medium text-gray-500 dark:text-gray-400">
              {{
                t('components.batchAddModal.selected', {
                  count: selectedItems.length,
                })
              }}
            </p>

            <div class="flex flex-wrap gap-2 max-h-48 overflow-y-auto">
              <span
                v-for="item in selectedItems"
                :key="item[idKey]"
                class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300"
              >
                <span class="max-w-[200px] truncate">
                  {{ item._displayName }}
                </span>

                <button
                  type="button"
                  class="ml-0.5 flex items-center hover:text-blue-600 dark:hover:text-blue-100 transition-colors"
                  @click="removeItem(item[idKey])"
                >
                  <BaseIcon :path="mdiCloseCircle" w="w-4" h="h-4" />
                </button>
              </span>
            </div>
          </div>
        </template>

        <!-- Phase: Saving / Done / Error -->
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
                    phase === 'saving'
                      ? t('components.batchAddModal.saving')
                      : phase === 'done'
                        ? t('components.batchAddModal.completed')
                        : t('components.batchAddModal.errorsOccurred')
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

            <!-- Skipped summary -->
            <div
              v-if="progress.skipped > 0"
              class="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800"
            >
              <p
                class="text-sm font-medium text-yellow-800 dark:text-yellow-200"
              >
                {{
                  t('components.batchAddModal.skipped', {
                    count: progress.skipped,
                  })
                }}
              </p>
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
                  t('components.batchAddModal.errorCount', {
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
                    t('components.batchAddModal.unknownError')
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
            v-if="phase === 'selecting'"
            :label="t('common.save')"
            color="success"
            :disabled="selectedItems.length === 0"
            @click="handleSave"
          />

          <BaseButton
            v-if="phase === 'selecting'"
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

  <UnsavedChangesModal
    v-model="showDiscardModal"
    @discard="confirmDiscard"
    @continue="cancelDiscard"
  />
</template>
