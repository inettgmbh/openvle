<script setup>
import { mdiTimerSandFull } from '@mdi/js'
import { computed, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseIcon from '@/components/BaseIcon.vue'
import CardBoxModal from '@/components/CardBoxModal.vue'
import { useRateLimitStore } from '@/stores/rateLimit'
import { formatRetryDuration } from '@/utils/formatRetryDuration'

const { t } = useI18n()
const store = useRateLimitStore()

const tick = ref(0)

let intervalId = null

function startTicker() {
  if (intervalId) return
  intervalId = setInterval(() => {
    tick.value++
  }, 1000)
}

function stopTicker() {
  if (intervalId) {
    clearInterval(intervalId)
    intervalId = null
  }
}

const secondsRemaining = computed(() => {
  void tick.value
  if (!store.expiresAt) return 0
  return Math.max(0, Math.ceil((store.expiresAt - Date.now()) / 1000))
})

const visible = computed({
  get: () =>
    store.active &&
    store.mode === 'modal' &&
    !store.dismissed &&
    secondsRemaining.value > 0,
  set: (value) => {
    if (!value && store.dismissable) store.dismiss()
  },
})

const formattedDuration = computed(() =>
  formatRetryDuration(secondsRemaining.value, t),
)

const formattedTime = computed(() => {
  if (!store.expiresAt) return ''
  return new Date(store.expiresAt).toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
})

const message = computed(() => {
  if (!store.messageKey) return ''
  return t(`${store.messageKey}.time`, { time: formattedTime.value })
})

const progressPercent = computed(() => {
  if (!store.totalSeconds) return 0
  const ratio = secondsRemaining.value / store.totalSeconds
  return Math.max(0, Math.min(100, ratio * 100))
})

watch(
  () => store.active,
  (active) => {
    if (active) startTicker()
    else stopTicker()
  },
  { immediate: true },
)

onUnmounted(stopTicker)
</script>

<template>
  <CardBoxModal
    v-model="visible"
    :title="t('views.rateLimit.title')"
    :crossmark="store.dismissable"
    :has-button="false"
  >
    <div class="flex flex-col items-center text-center gap-5 py-2">
      <!-- Icon -->
      <div
        class="rounded-full bg-yellow-100 dark:bg-yellow-500/10 p-4 text-yellow-500"
      >
        <BaseIcon :path="mdiTimerSandFull" w="w-12" h="h-12" :size="48" />
      </div>

      <!-- Countdown -->
      <div
        class="text-3xl font-bold tabular-nums tracking-tight"
        aria-live="polite"
      >
        {{ formattedDuration }}
      </div>

      <!-- Message -->
      <p class="text-sm opacity-80 max-w-sm whitespace-pre-line">
        {{ message }}
      </p>

      <!-- Progress bar -->
      <div
        class="w-full h-1.5 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden"
        role="progressbar"
        :aria-valuenow="Math.round(progressPercent)"
        aria-valuemin="0"
        aria-valuemax="100"
      >
        <div
          class="h-full bg-yellow-500 transition-all duration-1000 ease-linear"
          :style="{ width: `${progressPercent}%` }"
        />
      </div>
    </div>
  </CardBoxModal>
</template>
