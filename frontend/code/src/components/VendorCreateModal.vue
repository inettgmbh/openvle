<script setup>
import { mdiDomain, mdiTextBox } from '@mdi/js'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'vue-toastification'

import CardBoxModal from '@/components/CardBoxModal.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import backend from '@/services'
import { useMainStore } from '@/stores/main'

const { t } = useI18n()

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'created'])

const toast = useToast()
const name = ref('')
const description = ref('')
const isSubmitting = ref(false)
const autoFocusInputRef = ref(null)

function resetForm() {
  name.value = ''
  description.value = ''
  isSubmitting.value = false
}

// Reset form when modal opens
watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      resetForm()
      autoFocusInputRef.value?.focus()
    }
  },
)

async function onSubmit() {
  if (!name.value.trim() || isSubmitting.value) return
  isSubmitting.value = true
  try {
    const res = await backend.vendors.create({
      name: name.value.trim(),
      description: description.value.trim() || undefined,
    })
    toast.success(
      t('common.createSuccess', { entity: t('objectTypes.vendor.singular') }),
    )
    useMainStore().fetchPermissions()
    emit('created', { id: res.id, name: res.name })
    emit('update:modelValue', false)
  } catch (error) {
    toast.error(
      t('common.createError', { entity: t('objectTypes.vendor.singular') }),
    )
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <CardBoxModal
    :model-value="modelValue"
    :title="
      t('common.createTitle', { entity: t('objectTypes.vendor.singular') })
    "
    button="success"
    has-cancel
    :button-label="t('common.add')"
    :disabled="!name.trim() || isSubmitting"
    @update:model-value="emit('update:modelValue', $event)"
    @form-submitted="onSubmit"
    @cancel="resetForm"
  >
    <FormField :label="t('common.name')">
      <FormControl
        v-model="name"
        :icon="mdiDomain"
        :placeholder="t('common.name')"
        required
        @set-ref="(ref) => (autoFocusInputRef = ref)"
      />
    </FormField>

    <FormField :label="t('common.description')">
      <FormControl v-model="description" :icon="mdiTextBox" />
    </FormField>
  </CardBoxModal>
</template>
