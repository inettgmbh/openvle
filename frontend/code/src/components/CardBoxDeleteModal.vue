<script setup>
import { mdiAlert, mdiClose, mdiPencil } from '@mdi/js'
import { mdiContentCopy } from '@mdi/js'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxComponentTitle from '@/components/CardBoxComponentTitle.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
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
  relatedItems: {
    type: Array,
    default: () => [],
  },
  relatedLabel: {
    type: String,
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
  if (!isNameMatch.value) return false
  if (props.requireExtraConfirm && !extraConfirmed.value) return false
  return true
})

const confirmTooltip = computed(() => {
  if (canConfirm.value) return null
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

        <div
          v-if="warning"
          class="flex items-start gap-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-700/50 text-amber-900 dark:text-amber-200 text-sm"
        >
          <svg
            viewBox="0 0 24 24"
            class="w-5 h-5 flex-none mt-0.5 fill-current"
            aria-hidden="true"
          >
            <path :d="mdiAlert" />
          </svg>

          <p class="leading-snug">{{ warning }}</p>
        </div>

        <div v-if="relatedItems.length > 0" class="space-y-1">
          <p
            v-if="relatedLabel"
            class="text-sm font-medium text-gray-700 dark:text-gray-200"
          >
            {{ relatedLabel }}
          </p>

          <ul
            class="text-sm space-y-1 max-h-40 overflow-y-auto rounded border border-gray-200 dark:border-gray-700 p-2 bg-gray-50 dark:bg-slate-800/50"
          >
            <li
              v-for="(item, idx) in relatedItems"
              :key="idx"
              class="flex items-baseline gap-2"
            >
              <span class="text-gray-900 dark:text-gray-100">{{
                item.label
              }}</span>

              <span
                v-if="item.sublabel"
                class="text-xs text-gray-500 dark:text-gray-400"
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
