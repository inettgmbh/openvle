<script setup>
import { mdiAlert, mdiClose, mdiInformation, mdiPencil } from '@mdi/js'
import { mdiContentCopy } from '@mdi/js'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxComponentTitle from '@/components/CardBoxComponentTitle.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import OverlayLayer from '@/components/OverlayLayer.vue'
import { useStyleStore } from '@/stores/style.js'
import { useAutofocusInput } from '@/utils/useAutofocusInput'

const { t } = useI18n()
const styleStore = useStyleStore()

const props = defineProps({
  modelValue: {
    type: [String, Number, Boolean],
    default: null,
  },
  name: {
    type: String,
    default: null,
  },
  checkvalue: {
    type: String,
    default: null,
  },
  warning: {
    type: String,
    default: null,
  },
  info: {
    type: String,
    default: null,
  },
  relatedItems: {
    type: Array,
    default: () => [],
  },
  relatedLabel: {
    type: String,
    default: null,
  },
  relatedCount: {
    type: Number,
    default: null,
  },
  requireExtraConfirm: {
    type: Boolean,
    default: false,
  },
  extraConfirmLabel: {
    type: String,
    default: null,
  },
  blocked: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'cancel', 'form-submitted'])

const value = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const extraConfirmed = ref(false)

watch(value, (open) => {
  if (!open) extraConfirmed.value = false
})

const confirmCancel = (mode) => {
  value.value = false
  confirmationName.value = ''
  extraConfirmed.value = false
  emit(mode)
}

const confirm = () => confirmCancel('form-submitted')

const cancel = () => confirmCancel('cancel')

const copied = ref(false)

const confirmationName = ref('')

const { autoFocusInputRef } = useAutofocusInput(value)

const isNameMatch = computed(() => confirmationName.value === props.checkvalue)

const canConfirm = computed(() => {
  if (props.blocked) return false
  if (!isNameMatch.value) return false
  if (props.requireExtraConfirm && !extraConfirmed.value) return false
  return true
})

const confirmTooltip = computed(() => {
  if (canConfirm.value) return null
  if (props.blocked) return t('components.deleteModal.tooltipBlocked')
  const needsExtra = props.requireExtraConfirm && !extraConfirmed.value
  if (!isNameMatch.value && needsExtra) {
    return t('components.deleteModal.tooltipBothMissing')
  }
  if (!isNameMatch.value) {
    return t('components.deleteModal.tooltipNameMissing')
  }
  return t('components.deleteModal.tooltipExtraMissing')
})

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

onMounted(() => {
  window.addEventListener('keydown', handleEscape)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleEscape)
})
</script>

<template>
  <OverlayLayer v-show="value" @overlay-click="cancel">
    <CardBox
      v-show="value"
      class="shadow-lg max-h-modal w-11/12 md:w-3/5 lg:w-2/5 xl:w-4/12 z-50"
      is-modal
      :class="{ dark: styleStore.darkMode }"
    >
      <CardBoxComponentTitle :title="t('components.deleteModal.confirmAction')">
        <BaseButton
          :icon="mdiClose"
          color="whiteDark"
          small
          rounded-full
          @click.prevent="cancel"
        />
      </CardBoxComponentTitle>

      <div class="space-y-3">
        <p>
          {{
            t('components.deleteModal.willBeDeleted', {
              name: props.name,
            })
          }}
        </p>

        <NotificationBar
          v-if="info"
          :dismissable="false"
          color="info"
          :icon="mdiInformation"
          class="!mb-0"
        >
          {{ info }}
        </NotificationBar>

        <NotificationBar
          v-if="warning"
          :dismissable="false"
          :color="blocked ? 'danger' : 'warning'"
          :icon="mdiAlert"
          class="!mb-0"
        >
          {{ warning }}
        </NotificationBar>

        <div
          v-if="relatedItems.length > 0"
          class="border border-gray-200 dark:border-slate-700 rounded-lg overflow-hidden divide-y divide-gray-200 dark:divide-slate-700 bg-white dark:bg-slate-900/30"
        >
          <div
            v-if="relatedLabel"
            class="flex items-center justify-between gap-2 px-3 py-2.5 bg-gray-50 dark:bg-slate-800/40"
          >
            <span class="font-medium text-sm truncate">{{ relatedLabel }}</span>

            <span
              class="inline-flex items-center shrink-0 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-200 text-gray-700 dark:bg-slate-700 dark:text-slate-200"
            >
              {{ relatedCount ?? relatedItems.length }}
            </span>
          </div>

          <ul
            class="divide-y divide-gray-100 dark:divide-slate-800 max-h-40 overflow-y-auto"
          >
            <li
              v-for="(item, idx) in relatedItems"
              :key="idx"
              class="flex items-baseline justify-between gap-2 text-sm px-4 py-2 min-w-0 hover:bg-gray-50 dark:hover:bg-slate-800/40"
            >
              <span
                class="truncate min-w-0 flex-1 text-gray-900 dark:text-gray-100"
              >
                {{ item.label }}
              </span>

              <span
                v-if="item.sublabel"
                class="text-xs text-gray-500 dark:text-gray-400 shrink-0"
                >{{ item.sublabel }}</span
              >
            </li>
          </ul>
        </div>

        <label v-if="requireExtraConfirm" class="checkbox select-none">
          <input v-model="extraConfirmed" type="checkbox" />

          <span class="check" />

          <span class="pl-2 text-sm text-gray-800 dark:text-gray-200">{{
            extraConfirmLabel
          }}</span>
        </label>

        <template v-if="!blocked">
          <hr />

          {{ t('components.deleteModal.confirmPrompt') }}<br />

          <p class="flex items-center gap-2">
            <b>"{{ props.checkvalue }}"</b>

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
          </p>

          <FormField>
            <FormControl
              v-model="confirmationName"
              :icon="mdiPencil"
              :placeholder="props.checkvalue"
              @set-ref="(el) => (autoFocusInputRef = el)"
            />
          </FormField>
        </template>
      </div>

      <template #footer>
        <BaseButtons>
          <BaseButton
            v-tooltip="confirmTooltip"
            :label="t('common.delete')"
            color="danger"
            type="submit"
            :disabled="!canConfirm"
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
  </OverlayLayer>
</template>
