<script setup>
import { mdiRefreshAuto, mdiReload, mdiTextBoxMultipleOutline } from '@mdi/js'
import { computed, useSlots } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseIcon from '@/components/BaseIcon.vue'
import IconRounded from '@/components/IconRounded.vue'
import { useMainStore } from '@/stores/main'

const { t } = useI18n()
const mainStore = useMainStore()

const props = defineProps({
  docsPath: {
    type: String,
    default: null,
    required: false,
  },
  icon: {
    type: String,
    default: null,
  },
  title: {
    type: String,
    required: true,
  },
  reload: {
    type: Function,
    default: undefined,
    required: false,
  },
  reloadDisabled: {
    type: Boolean,
    default: false,
  },
  reloadDisabledTooltip: {
    type: String,
    default: null,
  },
  objectModel: {
    type: String,
    default: null,
  },
  autoRefreshEnabled: {
    type: Boolean,
    default: false,
  },
  // > 0 enables the auto-refresh toggle UI; 0 hides it entirely
  autoRefreshIntervalSeconds: {
    type: Number,
    default: 0,
  },
  main: Boolean,
})

const emit = defineEmits(['update:autoRefreshEnabled'])

const reloadTooltip = computed(() => {
  if (props.reloadDisabled) {
    return { text: props.reloadDisabledTooltip }
  }
  return { text: t('common.refresh') }
})

const showAutoRefresh = computed(() => props.autoRefreshIntervalSeconds > 0)

const autoRefreshTooltip = computed(() => ({
  text: props.autoRefreshEnabled
    ? t('common.autoRefresh', {
        seconds: props.autoRefreshIntervalSeconds,
      })
    : t('common.autoRefreshOff'),
}))

function toggleAutoRefresh() {
  emit('update:autoRefreshEnabled', !props.autoRefreshEnabled)
}

const docsBaseURL = computed(
  () => mainStore.settings?.branding?.docs?.deepurl + props.docsPath,
)

const hasSlot = computed(() => useSlots().default)
</script>

<template>
  <section
    :class="{ 'pt-6': !main }"
    class="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between"
  >
    <div class="flex items-center min-w-0 gap-2 lg:flex-1">
      <IconRounded
        v-if="icon && main"
        :icon="icon"
        color="light"
        class="flex-shrink-0"
        bg
      />

      <BaseIcon v-else-if="icon" :path="icon" class="flex-shrink-0" size="20" />

      <div class="min-w-0 flex-1">
        <h1
          :class="main ? 'text-3xl' : 'text-2xl'"
          class="leading-tight break-words min-w-0"
        >
          {{ title }}
        </h1>

        <p
          v-if="props.objectModel"
          class="text-sm italic text-gray-600 dark:text-gray-400 mt-1 break-words"
        >
          {{ props.objectModel }}
        </p>
      </div>

      <BaseButton
        v-if="docsPath"
        v-tooltip="{ text: t('components.sectionTitle.docsLink') }"
        :icon="mdiTextBoxMultipleOutline"
        color="whiteDark"
        class="flex-shrink-0"
        :href="docsBaseURL"
        target="_blank"
      />

      <BaseButton
        v-if="reload"
        v-tooltip="reloadTooltip"
        :icon="mdiReload"
        color="whiteDark"
        class="flex-shrink-0"
        :disabled="reloadDisabled"
        @click="reload"
      />

      <BaseButton
        v-if="showAutoRefresh"
        v-tooltip="autoRefreshTooltip"
        :icon="mdiRefreshAuto"
        :color="autoRefreshEnabled ? 'success' : 'whiteDark'"
        :outline="!autoRefreshEnabled"
        class="flex-shrink-0"
        @click="toggleAutoRefresh"
      />
    </div>

    <BaseButtons v-if="hasSlot" class="self-end lg:self-auto lg:flex-shrink-0">
      <slot />
    </BaseButtons>
  </section>
</template>
