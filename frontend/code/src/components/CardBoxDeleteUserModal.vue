<script setup>
import {
  mdiAlert,
  mdiChevronDown,
  mdiContentCopy,
  mdiOpenInNew,
  mdiPencil,
} from '@mdi/js'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseDivider from '@/components/BaseDivider.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxModal from '@/components/CardBoxModal.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import backend from '@/services'
import {
  resolveFieldFromLookup,
  resolveObjectTypeToGerman,
} from '@/utils/dataUtils'
import { useAutofocusInput } from '@/utils/useAutofocusInput'

const { t } = useI18n()

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true,
  },
  checkvalue: {
    type: String,
    default: null,
  },
  object: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['update:modelValue', 'confirmed'])

const cancel = () => confirmCancel('cancel')
const confirm = () => confirmCancel('form-submitted')
const confirmationName = ref('')
const copied = ref(false)
const object = computed(() => props.object)
const loading = ref(true)
const modalVisible = ref(props.modelValue)
const router = useRouter()
const toast = useToast()
const sections = ref([])

const LIST_KEYS = [
  'virtual_machines',
  'connections',
  'mails',
  'changelogs',
  'object_permissions',
  'tags',
  'event_memberships',
]

// Sections shown as a counter only — no expand, no item list.
const COUNTER_ONLY_KEYS = new Set([
  'mails',
  'changelogs',
  'object_permissions',
  'policy_memberships',
])

const SECTION_KEYS = [...LIST_KEYS, 'policy_memberships']

// Per-list mapping for the "open in new tab" button.
// idField is the property on the item that goes into the URL path.
const SECTION_LINK_CONFIG = {
  virtual_machines: { path: 'vms', idField: 'id' },
  connections: { path: 'guacamoles', idField: 'id' },
  mails: { path: 'mails', idField: 'id' },
  tags: { path: 'tags', idField: 'key' },
  event_memberships: { path: 'events', idField: 'event' },
}

const isEmpty = computed(() => sections.value.length === 0)

const fetchUserDeletePreview = async () => {
  try {
    loading.value = true

    const response = await backend.users.getDeletePreview(object.value?.id)
    const targetData = response['__v_raw'] || response
    const stats = targetData.stats ?? {}

    const itemsWithEvent = LIST_KEYS.filter(
      (key) => !COUNTER_ONLY_KEYS.has(key),
    ).flatMap((key) => {
      const items = targetData[key]?.items ?? []
      return items.map((item) => ({
        ...item,
        __key: key,
        event: item.event ?? item.eventId,
      }))
    })

    await resolveFieldFromLookup(itemsWithEvent, [
      { from: 'event', to: 'eventName', keyspace: 'events' },
    ])

    sections.value = SECTION_KEYS.map((key) => {
      const counterOnly = COUNTER_ONLY_KEYS.has(key)
      const items = counterOnly
        ? []
        : itemsWithEvent.filter((it) => it.__key === key)
      const truncated = !counterOnly && targetData[key]?.truncated === true
      const total = stats[key] ?? items.length
      const link = SECTION_LINK_CONFIG[key]
      return {
        key,
        items,
        shown: items.length,
        total,
        truncated,
        collapsible: !counterOnly,
        label: resolveObjectTypeToGerman(key, { plural: true }),
        objectPath: link?.path ?? null,
        idField: link?.idField ?? 'id',
      }
    })
      .filter((s) => s.total > 0 || s.items.length > 0)
      .sort((a, b) => a.label.localeCompare(b.label, 'de'))

    loading.value = false
  } catch (error) {
    toast.error(
      `${t('components.deleteUserModal.previewError')}:\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  }
}

const displayLabel = (item, key) => {
  switch (key) {
    case 'event_memberships':
      return [item.name ?? item.eventName, item.role?.name]
        .filter(Boolean)
        .join(' — ')
    case 'tags':
      return [item.key, item.value].filter(Boolean).join(': ')
    default:
      return item.name ?? item.id
  }
}

const sectionCountText = (section) =>
  section.truncated
    ? t('components.deleteUserModal.sectionCountTruncated', {
        shown: section.shown,
        total: section.total,
      })
    : String(section.total)

const value = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const { autoFocusInputRef } = useAutofocusInput(value)

const confirmCancel = (mode) => {
  value.value = false
  confirmationName.value = ''
  emit(mode)
}

const isNameMatch = computed(() => confirmationName.value === props.checkvalue)

const handleEscape = (e) => {
  if (e.key === 'Escape' && value.value) {
    cancel()
  }
}

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    setTimeout(() => (copied.value = false), 1200)
  } catch (err) {
    console.error('Copy to clipboard failed:', err)
  }
}

const viewItem = (item, section) => {
  const idValue = item[section.idField]
  if (!section.objectPath || !idValue) return
  return window.open(
    router.resolve({ path: `/${section.objectPath}/${idValue}` }).href,
    '_blank',
  )
}

watch(
  () => modalVisible.value,
  (newVal) => {
    emit('update:modelValue', newVal)

    if (newVal) {
      fetchUserDeletePreview()
    }
  },
)

watch(
  () => props.modelValue,
  (newVal) => {
    modalVisible.value = newVal
  },
)

onMounted(() => {
  window.addEventListener('keydown', handleEscape)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleEscape)
})
</script>

<template>
  <CardBoxModal
    v-model="modalVisible"
    :has-button="false"
    :title="t('components.deleteModal.confirmAction')"
    custom-class="z-50 !w-full md:!w-4/5 lg:!w-3/4 xl:!max-w-6xl"
  >
    <template v-if="loading">
      <div class="flex flex-col justify-center items-center min-h-[300px]">
        <svg
          class="animate-spin h-10 w-10 text-warning"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          ></circle>

          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8v8H4z"
          ></path>
        </svg>

        <p class="mt-4 text-warning">{{ t('common.loading') }}</p>
      </div>
    </template>

    <template v-else>
      <CardBox class="grid mb-6">
        <div>
          <NotificationBar :dismissable="false" color="danger" :icon="mdiAlert">
            <p>
              {{ t('components.deleteUserModal.userWillBeDeleted') }}
              <b> {{ object.name + ' (' + object.email + ')' }}</b>
            </p>
          </NotificationBar>

          <p v-if="isEmpty" class="mt-4">
            {{ t('components.deleteUserModal.emptyState') }}
          </p>

          <template v-else>
            <p class="mt-4">
              {{ t('components.deleteUserModal.objectsAutoDeleted') }}
            </p>

            <div
              class="mt-3 max-h-[50vh] overflow-y-auto overflow-x-hidden border border-gray-200 dark:border-slate-700 rounded-lg divide-y divide-gray-200 dark:divide-slate-700 bg-white dark:bg-slate-900/30"
            >
              <template v-for="section in sections" :key="section.key">
                <details v-if="section.collapsible" class="group">
                  <summary
                    class="flex items-center justify-between gap-2 cursor-pointer select-none px-3 py-2.5 bg-gray-50 dark:bg-slate-800/40 hover:bg-gray-100 dark:hover:bg-slate-800 group-open:bg-gray-100 dark:group-open:bg-slate-800 transition-colors"
                  >
                    <span class="font-medium flex items-center gap-2 min-w-0">
                      <span class="truncate">{{ section.label }}</span>

                      <span
                        :class="[
                          'inline-flex items-center shrink-0 px-2 py-0.5 rounded-full text-xs font-medium',
                          section.truncated
                            ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200'
                            : 'bg-gray-200 text-gray-700 dark:bg-slate-700 dark:text-slate-200',
                        ]"
                      >
                        {{ sectionCountText(section) }}
                      </span>
                    </span>

                    <svg
                      class="w-5 h-5 shrink-0 text-gray-400 transition-transform group-open:rotate-180"
                      viewBox="0 0 24 24"
                      fill="currentColor"
                    >
                      <path :d="mdiChevronDown" />
                    </svg>
                  </summary>

                  <ul
                    class="divide-y divide-gray-100 dark:divide-slate-800 bg-white dark:bg-slate-900/20"
                  >
                    <li
                      v-for="(item, idx) in section.items"
                      :key="item.id ?? idx"
                      class="flex items-center justify-between gap-2 text-sm px-4 py-2 min-w-0 hover:bg-gray-50 dark:hover:bg-slate-800/40"
                    >
                      <span class="truncate min-w-0 flex-1">{{
                        displayLabel(item, section.key) || '—'
                      }}</span>

                      <BaseButton
                        v-if="section.objectPath && item[section.idField]"
                        :icon="mdiOpenInNew"
                        color="info"
                        small
                        outline
                        rounded-full
                        @click="viewItem(item, section)"
                      />
                    </li>
                  </ul>
                </details>

                <div
                  v-else
                  class="flex items-center gap-2 px-3 py-2.5 bg-gray-50 dark:bg-slate-800/40"
                >
                  <span class="font-medium flex items-center gap-2 min-w-0">
                    <span class="truncate">{{ section.label }}</span>

                    <span
                      class="inline-flex items-center shrink-0 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-200 text-gray-700 dark:bg-slate-700 dark:text-slate-200"
                    >
                      {{ section.total }}
                    </span>
                  </span>
                </div>
              </template>
            </div>
          </template>

          <BaseDivider />

          {{ t('components.deleteModal.confirmPrompt') }}

          <b class="pr-2">"{{ props.checkvalue }}"</b>

          <BaseButton
            :icon="mdiContentCopy"
            color="light"
            small
            rounded-full
            :class="[
              'transition-colors duration-300',
              copied ? 'bg-green-500 text-white' : '',
            ]"
            @click="copyToClipboard(props.checkvalue)"
          />

          <FormField class="pt-4">
            <FormControl
              v-model="confirmationName"
              :icon="mdiPencil"
              :placeholder="props.checkvalue"
              @set-ref="(el) => (autoFocusInputRef = el)"
            />
          </FormField>
        </div>

        <template #footer>
          <BaseButtons>
            <BaseButton
              :label="t('common.delete')"
              color="danger"
              type="submit"
              :disabled="!isNameMatch"
              @click="confirm"
            />

            <BaseButton
              :label="t('common.cancel')"
              color="danger"
              outline
              @click="cancel"
            />
          </BaseButtons>
        </template>
      </CardBox>
    </template>
  </CardBoxModal>
</template>

<style scoped>
details > summary {
  list-style: none;
}
details > summary::-webkit-details-marker {
  display: none;
}
</style>
