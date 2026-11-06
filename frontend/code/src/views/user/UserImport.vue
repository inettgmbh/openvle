<script setup>
import { mdiAccount } from '@mdi/js'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import CardBox from '@/components/CardBox.vue'
import CSVUpload from '@/components/CSVUpload.vue'
import FormField from '@/components/FormField.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import UnsavedChangesModal from '@/components/UnsavedChangesModal.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { DEFAULT_USER_LOCALE } from '@/utils/localeData'

const { t } = useI18n()

// The backend stores a single `name`. Source CSVs sometimes carry the full name
// in one column and sometimes split it into first/last — let the importer pick
// which shape their file has. 'split' keeps the historical behaviour.
const nameMode = ref('split') // 'split' | 'full'
const csvUploadRef = ref(null)

// Confirmation before a switch that would reset an in-progress import.
const pendingMode = ref(null)
const showDiscardModal = ref(false)

const nameModeOptions = computed(() => [
  { value: 'split', label: t('views.users.import.nameFormatSplit') },
  { value: 'full', label: t('views.users.import.nameFormatFull') },
])

const userImportHeadersCSV = computed(() => {
  const email = { key: 'email', label: t('views.users.import.email') }
  const username = { key: 'username', label: t('views.users.import.username') }
  const nameColumns =
    nameMode.value === 'full'
      ? [{ key: 'fullname', label: t('views.users.import.fullname') }]
      : [
          { key: 'firstname', label: t('views.users.import.firstname') },
          { key: 'lastname', label: t('views.users.import.lastname') },
        ]

  return [email, ...nameColumns, username]
})

function requestModeChange(mode) {
  if (mode === nameMode.value) return

  // Past step 1 means a file was already uploaded/mapped — switching remounts
  // CSVUpload and discards that progress, so confirm first.
  if ((csvUploadRef.value?.currentStep ?? 1) > 1) {
    pendingMode.value = mode
    showDiscardModal.value = true
    return
  }

  nameMode.value = mode
}

function confirmModeChange() {
  if (pendingMode.value) nameMode.value = pendingMode.value
  pendingMode.value = null
  showDiscardModal.value = false
}

function cancelModeChange() {
  pendingMode.value = null
  showDiscardModal.value = false
}

// Arrow-key navigation for the radiogroup (selection follows focus).
function onModeKeydown(event) {
  const navKeys = ['ArrowRight', 'ArrowDown', 'ArrowLeft', 'ArrowUp']
  if (!navKeys.includes(event.key)) return

  event.preventDefault()
  const values = nameModeOptions.value.map((o) => o.value)
  const forward = event.key === 'ArrowRight' || event.key === 'ArrowDown'
  const nextIndex =
    (values.indexOf(nameMode.value) + (forward ? 1 : -1) + values.length) %
    values.length

  requestModeChange(values[nextIndex])
}

function buildName(row) {
  return nameMode.value === 'full'
    ? (row.fullname ?? '').trim()
    : `${row.firstname ?? ''} ${row.lastname ?? ''}`.trim()
}

async function createUser(row) {
  if (!row.email?.includes('@'))
    throw new Error(t('views.users.import.invalidEmail'))

  try {
    await backend.users.create({
      username: row.username,
      email: row.email,
      name: buildName(row),
      status: 'Active',
      locale: DEFAULT_USER_LOCALE,
    })
    return true
  } catch (error) {
    if (error?.response?.data?.detail) {
      throw new Error(error?.response?.data?.detail)
    } else {
      throw new Error(t('views.users.import.unknownError'))
    }
  }
}
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiAccount"
        :title="
          $t('common.importTitle', { entity: $t('objectTypes.user.singular') })
        "
        main
        docs-path="/docs/usage/openvle/access-control/users/"
      />

      <CardBox class="min-h-[500px]">
        <FormField
          :label="$t('views.users.import.nameFormat')"
          :tooltip="$t('views.users.import.nameFormatHint')"
        >
          <div
            role="radiogroup"
            :aria-label="$t('views.users.import.nameFormat')"
            class="inline-flex gap-1 rounded-lg border border-gray-300 bg-gray-100 p-1 dark:border-slate-600 dark:bg-slate-800/60"
          >
            <button
              v-for="opt in nameModeOptions"
              :key="opt.value"
              type="button"
              role="radio"
              :data-mode="opt.value"
              :aria-checked="nameMode === opt.value"
              :tabindex="nameMode === opt.value ? 0 : -1"
              class="cursor-pointer rounded-md px-4 py-2 text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              :class="
                nameMode === opt.value
                  ? 'bg-blue-500 text-white shadow-sm'
                  : 'text-gray-600 hover:bg-white/70 hover:text-gray-900 dark:text-slate-300 dark:hover:bg-slate-700/60 dark:hover:text-white'
              "
              @click="requestModeChange(opt.value)"
              @keydown="onModeKeydown"
            >
              {{ opt.label }}
            </button>
          </div>
        </FormField>

        <CSVUpload
          :key="nameMode"
          ref="csvUploadRef"
          :required-mappings="userImportHeadersCSV"
          :on-import-confirm="createUser"
          :limit="5000"
        />
      </CardBox>
    </SectionMain>

    <UnsavedChangesModal
      v-model="showDiscardModal"
      @discard="confirmModeChange"
      @continue="cancelModeChange"
    />
  </LayoutAuthenticated>
</template>
