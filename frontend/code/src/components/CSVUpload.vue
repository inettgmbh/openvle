<script setup>
import {
  mdiAlert,
  mdiArrowLeft,
  mdiArrowRight,
  mdiCheckCircle,
  mdiCloseCircle,
  mdiDownload,
  mdiFileDelimitedOutline,
  mdiRestart,
  mdiUploadCircle,
} from '@mdi/js'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseIcon from '@/components/BaseIcon.vue'
import FormControl from '@/components/FormControl.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import PillTag from '@/components/PillTag.vue'
import { useCSVImport } from '@/composables/useCSVImport'
import {
  CSV_ROW_STATUS,
  CSV_ROW_STATUS_COLOR,
  CSV_ROW_STATUS_ICON,
  CSV_ROW_STATUS_LABEL,
} from '@/utils/csvImportStatus'

const { t } = useI18n()

const props = defineProps({
  requiredMappings: {
    type: Array,
    required: true,
  },
  onImportConfirm: {
    type: Function,
    required: true,
  },
  onFinish: {
    type: Function,
    default: undefined,
  },
  limit: {
    type: Number,
    default: null,
  },
  emitOnClose: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['closed'])

const {
  // State
  allowRetry,
  csvHeaders,
  fileName,
  fileSize,
  hasImportStarted,
  headerMapping,
  isImporting,
  limitExceeded,
  noFile,
  parseError,
  parsedRowCount,
  rawRows,
  rowError,
  rowStatus,

  // Computed
  canConfirm,
  currentStep,
  failedCount,
  hasDuplicateMappings,
  isImportFinished,
  progressPercent,
  remainingCount,
  successCount,
  totalCount,

  // Methods
  confirmImport,
  parseFile,
  reset,
} = useCSVImport({
  requiredMappings: props.requiredMappings,
  onImportConfirm: props.onImportConfirm,
  onFinish: props.onFinish,
  limit: props.limit,
})

// ── File input & drag-and-drop ──────────────────────────
const fileInputRef = ref(null)
const isDragOver = ref(false)

function openFileDialog() {
  fileInputRef.value?.click()
}

async function handleFileInput(e) {
  const file = e.target.files?.[0]
  if (file) await parseFile(file)
}

async function handleDrop(e) {
  isDragOver.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) await parseFile(file)
}

function handleDragOver() {
  isDragOver.value = true
}

function handleDragLeave() {
  isDragOver.value = false
}

// ── Navigation helpers ──────────────────────────────────
function goToStep3() {
  if (canConfirm.value) {
    hasImportStarted.value = true
  }
}

function goBackToMapping() {
  hasImportStarted.value = false
}

// ── Table helpers ───────────────────────────────────────
const tableColumns = computed(() => {
  const cols = csvHeaders.value.map((key) => ({
    key,
    label: key,
  }))
  return cols
})

const previewRows = computed(() =>
  rawRows.value.map((row, index) => ({
    ...row,
    _index: index,
    _status: rowStatus.value[index] || CSV_ROW_STATUS.PENDING,
    _error: rowError.value[index] || '',
  })),
)

const failedRows = computed(() =>
  previewRows.value.filter((r) => r._status === CSV_ROW_STATUS.FAILED),
)

// ── Duplicate-mapping helper ────────────────────────────
function isAlreadyMapped(mappingKey, csvCol) {
  if (!csvCol) return false
  return Object.entries(headerMapping.value).some(
    ([k, v]) => k !== mappingKey && v === csvCol,
  )
}

// ── Close / reset ───────────────────────────────────────
function close() {
  if (props.emitOnClose) {
    return emit('closed', true)
  }
  doReset()
}

function doReset() {
  reset()
  if (fileInputRef.value) {
    fileInputRef.value.value = null
  }
}

// ── File size formatter ─────────────────────────────────
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// ── Template download ───────────────────────────────────
function downloadTemplate() {
  const headers = props.requiredMappings.map((m) => m.label)
  const csv = headers.join(',') + '\n'
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = t('components.csvUpload.templateFilename')
  a.click()
  URL.revokeObjectURL(url)
}

// ── Stepper config ──────────────────────────────────────
const steps = computed(() => [
  { num: 1, label: t('components.csvUpload.stepUpload') },
  { num: 2, label: t('components.csvUpload.stepMapping') },
  { num: 3, label: t('components.csvUpload.stepImport') },
  { num: 4, label: t('components.csvUpload.stepResult') },
])
</script>

<template>
  <div class="space-y-4">
    <!-- Hidden file input -->
    <input
      ref="fileInputRef"
      type="file"
      accept=".csv"
      class="hidden"
      data-testid="file-input"
      @change="handleFileInput"
    />

    <!-- Stepper indicator -->
    <nav class="flex items-center justify-between px-2" data-testid="stepper">
      <template v-for="(step, idx) in steps" :key="step.num">
        <!-- Step circle + label -->
        <div class="flex flex-col items-center gap-1">
          <div
            class="flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold border-2 transition-colors"
            :class="[
              currentStep === step.num
                ? 'border-blue-500 bg-blue-500 text-white'
                : currentStep > step.num
                  ? 'border-emerald-500 bg-emerald-500 text-white'
                  : 'border-gray-300 dark:border-slate-600 text-gray-400 dark:text-slate-500',
            ]"
          >
            <BaseIcon
              v-if="currentStep > step.num"
              :path="mdiCheckCircle"
              :size="16"
              w="w-4"
              h="h-4"
            />

            <span v-else>{{ step.num }}</span>
          </div>

          <span
            class="text-xs font-medium"
            :class="[
              currentStep >= step.num
                ? 'text-gray-700 dark:text-slate-300'
                : 'text-gray-400 dark:text-slate-500',
            ]"
          >
            {{ step.label }}
          </span>
        </div>

        <!-- Connector line -->
        <div
          v-if="idx < steps.length - 1"
          class="flex-1 h-0.5 mx-2 mb-5 transition-colors"
          :class="[
            currentStep > step.num
              ? 'bg-emerald-500'
              : 'bg-gray-200 dark:bg-slate-700',
          ]"
        />
      </template>
    </nav>

    <!-- ═══════════════════════════════════════════════════ -->
    <!-- Step 1: File upload                                -->
    <!-- ═══════════════════════════════════════════════════ -->
    <div v-show="currentStep === 1" class="min-h-[200px]" data-testid="step-1">
      <!-- Error notifications -->
      <NotificationBar
        v-if="limitExceeded"
        :dismissable="false"
        color="danger"
        :icon="mdiAlert"
      >
        {{
          t('components.csvUpload.limitExceeded', {
            count: parsedRowCount,
            limit: limit,
          })
        }}
      </NotificationBar>

      <NotificationBar
        v-if="parseError"
        :dismissable="false"
        color="danger"
        :icon="mdiAlert"
      >
        {{ parseError }}
      </NotificationBar>

      <!-- Upload instructions -->
      <NotificationBar
        v-if="!limitExceeded && !parseError && noFile"
        :dismissable="false"
        color="info"
        :icon="mdiUploadCircle"
      >
        <div>
          <b>{{ t('components.csvUpload.selectFile') }}: </b>

          <template v-if="limit">
            {{ t('components.csvUpload.maxRows', { limit: limit }) }}
          </template>

          {{ t('components.csvUpload.delimiterInfo') }}
        </div>
      </NotificationBar>

      <!-- Required columns info -->
      <div
        v-if="noFile && !limitExceeded && !parseError"
        class="mt-3 flex items-center justify-between gap-4 p-3 rounded-lg bg-gray-50 dark:bg-slate-800"
        data-testid="required-columns"
      >
        <div class="text-sm">
          <span class="font-medium text-gray-700 dark:text-slate-300">
            {{ t('components.csvUpload.requiredColumns') }}
          </span>

          <span v-for="(m, idx) in requiredMappings" :key="m.key" class="ml-1">
            <code
              class="px-1.5 py-0.5 rounded bg-gray-200 dark:bg-slate-700 text-gray-800 dark:text-slate-200 text-xs font-mono"
              >{{ m.label }}</code
            >

            <span v-if="idx < requiredMappings.length - 1">,</span>
          </span>
        </div>

        <BaseButton
          color="info"
          :icon="mdiDownload"
          :label="t('components.csvUpload.template')"
          small
          outline
          @click="downloadTemplate"
        />
      </div>

      <!-- Drag-and-drop zone -->
      <div
        class="mt-4 border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer"
        :class="[
          isDragOver
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
            : 'border-gray-300 dark:border-slate-600 hover:border-blue-400 dark:hover:border-blue-500',
        ]"
        data-testid="drop-zone"
        @click="openFileDialog"
        @drop.prevent="handleDrop"
        @dragover.prevent="handleDragOver"
        @dragleave.prevent="handleDragLeave"
      >
        <BaseIcon
          :path="mdiFileDelimitedOutline"
          :size="48"
          w="w-12"
          h="h-12"
          class="mx-auto text-gray-400 dark:text-slate-500 mb-3"
        />

        <p class="text-gray-600 dark:text-slate-400">
          {{ t('components.csvUpload.dragOrSelect') }}
        </p>
      </div>

      <!-- File info after upload -->
      <div
        v-if="!noFile && !limitExceeded && !parseError && rawRows.length"
        class="mt-4 flex items-center gap-3 p-3 rounded-lg bg-gray-50 dark:bg-slate-800"
        data-testid="file-info"
      >
        <BaseIcon
          :path="mdiCheckCircle"
          :size="20"
          w="w-5"
          h="h-5"
          class="text-emerald-500"
        />

        <div class="flex-1 text-sm">
          <span class="font-medium">{{ fileName }}</span>

          <span class="text-gray-500 dark:text-slate-400 ml-2">
            ({{ formatFileSize(fileSize) }},
            {{ t('components.csvUpload.rowCount', { count: rawRows.length }) }})
          </span>
        </div>

        <BaseButton
          color="info"
          :icon="mdiArrowRight"
          :label="t('components.csvUpload.next')"
          small
          rounded-full
          @click.stop
        />
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════ -->
    <!-- Step 2: Column mapping                             -->
    <!-- ═══════════════════════════════════════════════════ -->
    <div v-show="currentStep === 2" class="min-h-[200px]" data-testid="step-2">
      <NotificationBar
        v-if="hasDuplicateMappings"
        :dismissable="false"
        color="warning"
        :icon="mdiAlert"
      >
        {{ t('components.csvUpload.duplicateMapping') }}
      </NotificationBar>

      <h3 class="font-semibold mb-3">
        {{ t('components.csvUpload.mapColumns') }}
      </h3>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div
          v-for="mapping in requiredMappings"
          :key="mapping.key"
          class="flex flex-col"
        >
          <label class="text-sm font-medium mb-1">{{ mapping.label }}</label>

          <FormControl
            :id="mapping.key"
            v-model="headerMapping[mapping.key]"
            :required="true"
            :disabled="false"
            type="select"
            :options="[
              {
                label: t('components.csvUpload.pleaseSelect'),
                value: '',
                disabled: true,
                selected: true,
              },
              ...csvHeaders.map((col) => ({
                label: isAlreadyMapped(mapping.key, col)
                  ? col + ' (' + t('components.csvUpload.alreadyMapped') + ')'
                  : col,
                value: col,
                id: col,
              })),
            ]"
          />
        </div>
      </div>

      <!-- Navigation buttons -->
      <BaseButtons class="mt-6">
        <BaseButton
          color="whiteDark"
          :icon="mdiArrowLeft"
          :label="t('components.csvUpload.back')"
          small
          @click="doReset"
        />

        <BaseButton
          :disabled="!canConfirm"
          :color="canConfirm ? 'info' : 'whiteDark'"
          :icon="mdiArrowRight"
          :label="t('components.csvUpload.showPreview')"
          small
          @click="goToStep3"
        />
      </BaseButtons>
    </div>

    <!-- ═══════════════════════════════════════════════════ -->
    <!-- Step 3: Preview & import                           -->
    <!-- ═══════════════════════════════════════════════════ -->
    <div v-show="currentStep === 3" class="min-h-[200px]" data-testid="step-3">
      <!-- Progress bar -->
      <div v-if="isImporting || isImportFinished" class="mb-4">
        <div class="flex justify-between text-sm mb-1">
          <span v-if="isImporting" class="font-medium">
            {{ t('components.csvUpload.importRunning') }}
          </span>

          <span
            v-else
            class="font-medium text-emerald-600 dark:text-emerald-400"
          >
            {{ t('components.csvUpload.importComplete') }}
          </span>

          <span class="text-gray-500 dark:text-slate-400">
            {{ progressPercent }}%
          </span>
        </div>

        <div
          class="w-full bg-gray-200 dark:bg-slate-700 rounded h-3 overflow-hidden flex"
        >
          <div
            class="bg-emerald-500 h-full transition-all duration-300"
            :style="{ width: (successCount / totalCount) * 100 + '%' }"
          />

          <div
            class="bg-red-500 h-full transition-all duration-300"
            :style="{ width: (failedCount / totalCount) * 100 + '%' }"
          />
        </div>

        <div class="flex gap-4 mt-2 text-sm text-gray-600 dark:text-slate-400">
          <span
            >{{ t('components.csvUpload.successful') }}:
            {{ successCount }}</span
          >

          <span>{{ t('components.csvUpload.failed') }}: {{ failedCount }}</span>

          <span
            >{{ t('components.csvUpload.remaining') }}:
            {{ remainingCount }}</span
          >
        </div>
      </div>

      <!-- Preview table (scrollable) -->
      <div
        class="max-h-[400px] overflow-y-auto border rounded dark:border-slate-700"
        data-testid="preview-table"
      >
        <table class="w-full text-sm table-fixed">
          <colgroup>
            <col class="w-[48px]" />

            <col v-for="col in tableColumns" :key="col.key" />

            <col class="w-[150px]" />

            <col class="w-[200px]" />
          </colgroup>

          <thead class="bg-gray-50 dark:bg-slate-800 sticky top-0 z-10">
            <tr>
              <th
                class="text-left px-3 py-2 font-medium text-gray-600 dark:text-slate-400"
              >
                #
              </th>

              <th
                v-for="col in tableColumns"
                :key="col.key"
                class="text-left px-3 py-2 font-medium text-gray-600 dark:text-slate-400"
              >
                {{ col.label }}
              </th>

              <th
                class="text-left px-3 py-2 font-medium text-gray-600 dark:text-slate-400 whitespace-nowrap"
              >
                {{ t('common.status') }}
              </th>

              <th
                class="text-left px-3 py-2 font-medium text-gray-600 dark:text-slate-400"
              >
                {{ t('components.csvUpload.error') }}
              </th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="(row, idx) in previewRows"
              :key="idx"
              class="border-t dark:border-slate-700"
            >
              <td class="px-3 py-2 text-gray-400">{{ idx + 1 }}</td>

              <td
                v-for="col in tableColumns"
                :key="col.key"
                class="px-3 py-2 truncate"
              >
                {{ row[col.key] }}
              </td>

              <td class="px-3 py-2 whitespace-nowrap">
                <PillTag
                  :label="CSV_ROW_STATUS_LABEL[row._status]"
                  :color="CSV_ROW_STATUS_COLOR[row._status]"
                  :icon="CSV_ROW_STATUS_ICON[row._status]"
                  small
                  disabled
                />
              </td>

              <td
                class="px-3 py-2 text-red-600 dark:text-red-400 text-xs break-words"
              >
                {{ row._error }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Action buttons -->
      <BaseButtons class="mt-4">
        <BaseButton
          v-if="!isImporting && !isImportFinished"
          color="whiteDark"
          :icon="mdiArrowLeft"
          :label="t('components.csvUpload.back')"
          small
          @click="goBackToMapping"
        />

        <BaseButton
          v-if="!isImportFinished"
          :disabled="isImporting"
          :color="'success'"
          :label="
            t('components.csvUpload.startImport', {
              count: rawRows.length,
            })
          "
          small
          @click="confirmImport()"
        />
      </BaseButtons>
    </div>

    <!-- ═══════════════════════════════════════════════════ -->
    <!-- Step 4: Result                                     -->
    <!-- ═══════════════════════════════════════════════════ -->
    <div v-show="currentStep === 4" class="min-h-[200px]" data-testid="step-4">
      <!-- Summary cards -->
      <div class="grid grid-cols-3 gap-4 mb-4">
        <div class="p-4 rounded-lg bg-gray-50 dark:bg-slate-800 text-center">
          <div class="text-2xl font-bold text-gray-700 dark:text-slate-200">
            {{ totalCount }}
          </div>

          <div class="text-sm text-gray-500 dark:text-slate-400">
            {{ t('components.csvUpload.total') }}
          </div>
        </div>

        <div
          class="p-4 rounded-lg bg-emerald-50 dark:bg-emerald-900/20 text-center"
        >
          <div
            class="text-2xl font-bold text-emerald-600 dark:text-emerald-400"
          >
            {{ successCount }}
          </div>

          <div class="text-sm text-gray-500 dark:text-slate-400">
            {{ t('components.csvUpload.successful') }}
          </div>
        </div>

        <div
          class="p-4 rounded-lg text-center"
          :class="
            failedCount > 0
              ? 'bg-red-50 dark:bg-red-900/20'
              : 'bg-gray-50 dark:bg-slate-800'
          "
        >
          <div
            class="text-2xl font-bold"
            :class="
              failedCount > 0
                ? 'text-red-600 dark:text-red-400'
                : 'text-gray-700 dark:text-slate-200'
            "
          >
            {{ failedCount }}
          </div>

          <div class="text-sm text-gray-500 dark:text-slate-400">
            {{ t('components.csvUpload.failed') }}
          </div>
        </div>
      </div>

      <!-- Final progress bar -->
      <div
        class="w-full bg-gray-200 dark:bg-slate-700 rounded h-3 overflow-hidden flex mb-4"
      >
        <div
          class="bg-emerald-500 h-full transition-all duration-300"
          :style="{ width: (successCount / totalCount) * 100 + '%' }"
        />

        <div
          class="bg-red-500 h-full transition-all duration-300"
          :style="{ width: (failedCount / totalCount) * 100 + '%' }"
        />
      </div>

      <!-- Failed rows table -->
      <div v-if="failedRows.length" class="mb-4">
        <h3 class="font-semibold text-red-600 dark:text-red-400 mb-2">
          {{
            t('components.csvUpload.failedRows', {
              count: failedRows.length,
            })
          }}
        </h3>

        <div
          class="max-h-[300px] overflow-y-auto border rounded dark:border-slate-700"
          data-testid="failed-table"
        >
          <table class="w-full text-sm">
            <thead class="bg-gray-50 dark:bg-slate-800 sticky top-0 z-10">
              <tr>
                <th
                  class="text-left px-3 py-2 font-medium text-gray-600 dark:text-slate-400"
                >
                  #
                </th>

                <th
                  v-for="col in tableColumns"
                  :key="col.key"
                  class="text-left px-3 py-2 font-medium text-gray-600 dark:text-slate-400"
                >
                  {{ col.label }}
                </th>

                <th
                  class="text-left px-3 py-2 font-medium text-gray-600 dark:text-slate-400"
                >
                  {{ t('components.csvUpload.error') }}
                </th>
              </tr>
            </thead>

            <tbody>
              <tr
                v-for="row in failedRows"
                :key="row._index"
                class="border-t dark:border-slate-700"
              >
                <td class="px-3 py-2 text-gray-400">{{ row._index + 1 }}</td>

                <td
                  v-for="col in tableColumns"
                  :key="col.key"
                  class="px-3 py-2"
                >
                  {{ row[col.key] }}
                </td>

                <td class="px-3 py-2 text-red-600 dark:text-red-400 text-xs">
                  {{ row._error }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Result action buttons -->
      <BaseButtons>
        <BaseButton
          v-if="failedCount <= 0"
          color="success"
          :icon="mdiCheckCircle"
          :label="t('common.close')"
          small
          @click="close"
        />

        <BaseButton
          v-if="failedCount > 0"
          color="warning"
          :icon="mdiCloseCircle"
          :disabled="!allowRetry || isImporting"
          :label="t('components.csvUpload.retryFailed', { count: failedCount })"
          small
          @click="confirmImport(true)"
        />

        <BaseButton
          color="whiteDark"
          :icon="mdiRestart"
          :label="t('components.csvUpload.restart')"
          small
          @click="doReset"
        />
      </BaseButtons>
    </div>
  </div>
</template>
