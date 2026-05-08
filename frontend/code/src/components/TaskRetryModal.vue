<script setup>
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseDivider from '@/components/BaseDivider.vue'
import CardBoxModal from '@/components/CardBoxModal.vue'

const { t } = useI18n()

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true,
  },
  name: {
    type: String,
    required: true,
  },
  object: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['update:modelValue', 'confirmed'])

const object = computed(() => props.object)
const modalVisible = ref(props.modelValue)

const onFormSubmit = () => {
  emit('confirmed', true)
  emit('update:modelValue', false)
}

watch(
  () => modalVisible.value,
  (newVal) => {
    emit('update:modelValue', newVal)
  },
)

watch(
  () => props.modelValue,
  (newVal) => {
    modalVisible.value = newVal
  },
)
</script>

<template>
  <CardBoxModal
    v-model="modalVisible"
    :title="t('components.deleteModal.confirmAction')"
    button="danger"
    has-cancel
    :button-label="t('components.taskRetryModal.retry')"
    custom-class="z-50 w-full md:w-4/5 lg:w-3/5 xl:w-3/5"
    @form-submitted="onFormSubmit()"
  >
    <p>
      {{ t('components.taskRetryModal.taskWillRetry', { name: props.name }) }}
    </p>

    <p>
      {{ t('components.taskRetryModal.noGuarantee') }}
    </p>

    <p>
      {{ t('components.taskRetryModal.externalDependencies') }}
    </p>

    <BaseDivider :nav-bar="true" />

    <p>
      <u>{{ t('components.taskRetryModal.failedSubtasksRetried') }}</u>
    </p>

    <ul>
      <li
        v-for="obj in object.filter((s) => s.status === 'failed')"
        :key="obj.id"
      >
        <b>{{ obj.name }}</b>
      </li>
    </ul>

    <div v-if="object.some((s) => s.status === 'queued')">
      <BaseDivider :nav-bar="true" class="pb-3" />

      <p class="pb-2">
        <u>{{ t('components.taskRetryModal.queuedSubtasksMayTrigger') }}</u>
      </p>

      <ul>
        <li
          v-for="obj in object.filter((s) => s.status === 'queued')"
          :key="obj.id"
        >
          <b>{{ obj.name }}</b>
        </li>
      </ul>
    </div>

    <BaseDivider :nav-bar="true" />

    <p>{{ t('components.taskRetryModal.confirmRetry') }}</p>
  </CardBoxModal>
</template>

<style scoped>
ul {
  list-style: disc;
  padding-left: 1.25rem;
}
li {
  margin-bottom: 0.5rem;
}
</style>
