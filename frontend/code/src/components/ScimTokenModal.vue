<script setup>
import { mdiContentCopy } from '@mdi/js'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/BaseButton.vue'
import CardBoxModal from '@/components/CardBoxModal.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  token: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue'])

const copied = ref(false)

async function copyToken() {
  try {
    await navigator.clipboard.writeText(props.token)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch {
    // Fallback for environments without clipboard API
    const textArea = document.createElement('textarea')
    textArea.value = props.token
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  }
}
</script>

<template>
  <CardBoxModal
    :model-value="modelValue"
    :title="$t('views.scimClients.form.bearerToken')"
    button-:label="$t('common.close')"
    @update:model-value="emit('update:modelValue', $event)"
    @form-submitted="emit('update:modelValue', false)"
    @cancel="emit('update:modelValue', false)"
  >
    <div class="space-y-4">
      <p class="text-sm text-red-600 dark:text-red-400 font-semibold">
        Dieser Token wird nur einmal angezeigt. Bitte kopieren Sie diesen jetzt.
      </p>

      <div
        class="flex items-center gap-2 p-3 bg-gray-100 dark:bg-slate-700 rounded-lg"
      >
        <code
          class="flex-1 text-sm break-all font-mono text-gray-800 dark:text-gray-200"
        >
          {{ token }}
        </code>

        <BaseButton
          :icon="mdiContentCopy"
          :label="copied ? 'Kopiert!' : 'Kopieren'"
          :color="copied ? 'success' : 'info'"
          small
          @click="copyToken"
        />
      </div>
    </div>
  </CardBoxModal>
</template>
