<script setup>
import {
  mdiAccount,
  mdiAlert,
  mdiAlertCircle,
  mdiAutorenew,
  mdiCalendarEndOutline,
  mdiCalendarRange,
  mdiCheckCircle,
  mdiCloudRefreshVariant,
  mdiCogs,
  mdiDelete,
  mdiInformation,
  mdiListStatus,
  mdiPencil,
  mdiProgressClock,
  mdiRefresh,
  mdiStopCircle,
} from '@mdi/js'
import { computed, ref, toRefs } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/BaseButton.vue'
import BaseIcon from '@/components/BaseIcon.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import { useMainStore } from '@/stores/main'
import { useStyleStore } from '@/stores/style.js'
import { formatDate } from '@/utils/dataUtils'

const props = defineProps({
  event: {
    type: Object,
    default: null,
  },
  userPermissions: {
    type: Object,
    default() {
      return { edit: false, delete: false, rollout: false, stop: false }
    },
  },
})

const emit = defineEmits(['action', 'reload'])

const { t } = useI18n()
const mainStore = useMainStore()
const styleStore = useStyleStore()
const openStepId = ref(null)

const { event, userPermissions } = toRefs(props)

const deploymentErrorMsg = computed(() => {
  const msg = String(event.value?.deployment_status || '')

  const patterns = [
    'The following error occurred while trying to start the event: ',
    'The following error occurred while trying to end the event: ',
  ]

  for (const p of patterns) {
    if (msg.startsWith(p)) return msg.replace(p, '')
  }

  return msg
})

const errorMsg = computed(() => deploymentErrorMsg.value)

const shiftDate = (dateStr, days) => {
  if (!dateStr || days == null) return null

  const date = new Date(dateStr)

  if (isNaN(date.getTime())) return dateStr

  date.setDate(date.getDate() + days)

  return date.toISOString().slice(0, 10)
}

const prepStartDate = computed(() => {
  const dateStr = event.value?.dateStart
  const days = -mainStore.settings?.events?.start?.prep_time?.days
  return shiftDate(dateStr, days)
})

const prepEndDate = computed(() => {
  const dateStr = event.value?.dateEnd
  const days = mainStore.settings?.events?.end?.prep_time?.days
  return shiftDate(dateStr, days)
})

const STATUS_CONFIG = computed(() => ({
  pending: {
    label: t('components.eventStatus.statusPending'),
    icon: mdiProgressClock,
    badge: 'bg-indigo-100 text-indigo-800',
    circle: 'border-gray-300 bg-gray-400',
  },
  manual: {
    label: t('components.eventStatus.statusManual'),
    icon: mdiCogs,
    badge: 'bg-amber-200 text-amber-800',
    circle: 'border-amber-300',
  },
  running: {
    label: t('components.eventStatus.statusRunning'),
    icon: mdiAutorenew,
    badge: 'bg-blue-200 text-blue-800',
    circle: 'border-blue-300 bg-blue-500',
  },
  done: {
    label: t('components.eventStatus.statusDone'),
    icon: mdiCheckCircle,
    badge: 'bg-green-200 text-green-800',
    circle: 'border-green-300 bg-green-500',
  },
  error: {
    label: t('components.eventStatus.statusError'),
    icon: mdiAlertCircle,
    badge: 'bg-red-200 text-red-800',
    circle: 'border-red-300 bg-red-500',
  },
}))

const stepTemplate = computed(() => [
  {
    id: '10',
    name: 'geplant',
    title: t('components.eventStatus.steps.planned.title'),
    actionLabel: t('components.eventStatus.steps.planned.actionLabel'),
    description: t('components.eventStatus.steps.planned.description'),
    help: [
      t('components.eventStatus.steps.planned.help1'),
      t('components.eventStatus.steps.planned.help2'),
      t('components.eventStatus.steps.planned.help3'),
    ],
  },
  {
    id: '20',
    name: 'deploying',
    title: t('components.eventStatus.steps.deploying.title'),
    actionLabel: t('components.eventStatus.steps.deploying.actionLabel'),
    description: t('components.eventStatus.steps.deploying.description'),
    help: [
      t('components.eventStatus.steps.deploying.help1'),
      t('components.eventStatus.steps.deploying.help2'),
      t('components.eventStatus.steps.deploying.help3'),
      t('components.eventStatus.steps.deploying.help4'),
    ],
  },
  {
    id: '30',
    name: 'aktiv',
    title: t('components.eventStatus.steps.active.title'),
    actionLabel: t('components.eventStatus.steps.active.actionLabel'),
    description: t('components.eventStatus.steps.active.description'),
    help: [
      t('components.eventStatus.steps.active.help1'),
      t('components.eventStatus.steps.active.help2'),
      t('components.eventStatus.steps.active.help3'),
      t('components.eventStatus.steps.active.help4'),
    ],
  },
  {
    id: '50',
    name: 'archiving',
    title: t('components.eventStatus.steps.archiving.title'),
    actionLabel: t('components.eventStatus.steps.archiving.actionLabel'),
    description: t('components.eventStatus.steps.archiving.description'),
    help: [
      t('components.eventStatus.steps.archiving.help1'),
      t('components.eventStatus.steps.archiving.help2'),
      t('components.eventStatus.steps.archiving.help3'),
      t('components.eventStatus.steps.archiving.help4'),
      t('components.eventStatus.steps.archiving.help5'),
    ],
  },
  {
    id: '60',
    name: 'archiviert',
    title: t('components.eventStatus.steps.archived.title'),
    actionLabel: t('components.eventStatus.steps.archived.actionLabel'),
    description: t('components.eventStatus.steps.archived.description'),
    help: [
      t('components.eventStatus.steps.archived.help1'),
      t('components.eventStatus.steps.archived.help2'),
      t('components.eventStatus.steps.archived.help3'),
    ],
  },
])

const EVENT_STATUS_DEFAULTS = {
  status: 'pending',
  useCreated: false,
  useUpdated: false,
  updatedBy: null,
  error: null,
  help: null,
}

const EVENT_STATUS_MAP = {
  geplant: {
    geplant: { status: 'running', useCreated: true },
    deploying: {
      status: 'pending',
      date: {
        label: formatDate(prepStartDate.value, { relative: true }),
        object: prepStartDate.value,
      },
    },
    aktiv: { status: 'pending' },
    archiving: { status: 'pending' },
    archiviert: { status: 'pending' },
  },

  deploying: {
    geplant: { status: 'done', useCreated: true },
    deploying: { status: 'running', useUpdated: true },
    aktiv: { status: 'pending' },
    archiving: { status: 'pending' },
    archiviert: { status: 'pending' },
  },

  coreError: {
    geplant: { status: 'done', useCreated: true },
    deploying: {
      status: 'error',
      useUpdated: true,
      error: () =>
        t('components.eventStatus.errors.preRolloutCheck', {
          error: errorMsg.value,
        }),
    },
    aktiv: { status: 'manual' },
    archiving: { status: 'pending' },
    archiviert: { status: 'pending' },
  },

  deployingError: {
    geplant: { status: 'done', useCreated: true },
    deploying: {
      status: 'error',
      useUpdated: true,
      error: () =>
        t('components.eventStatus.errors.deploying', { error: errorMsg.value }),
    },
    aktiv: { status: 'manual' },
    archiving: { status: 'pending' },
    archiviert: { status: 'pending' },
  },

  aktiv: {
    geplant: { status: 'done', useCreated: true },
    deploying: { status: 'done', useUpdated: true },
    aktiv: { status: 'running', useUpdated: true, updatedBy: 'system' },
    archiving: {
      status: !event.value?.dateEnd ? 'manual' : 'pending',
      date: {
        label: event.value?.dateEnd
          ? formatDate(prepEndDate.value, { relative: true })
          : null,
        object: prepEndDate.value,
      },
    },
    archiviert: { status: 'pending' },
  },

  archiving: {
    geplant: { status: 'done', useCreated: true },
    deploying: { status: 'done', useUpdated: true },
    aktiv: { status: 'done', useUpdated: true, updatedBy: 'system' },
    archiving: { status: 'running', useUpdated: true },
    archiviert: { status: 'pending' },
  },

  archivingError: {
    geplant: { status: 'done', useCreated: true },
    deploying: { status: 'done', useUpdated: true },
    aktiv: { status: 'done' },
    archiving: {
      status: 'error',
      useUpdated: true,
      error: () =>
        t('components.eventStatus.errors.archiving', { error: errorMsg.value }),
    },
    archiviert: { status: 'manual' },
  },

  archiviert: {
    geplant: { status: 'done', useCreated: true },
    deploying: { status: 'done', useUpdated: true },
    aktiv: { status: 'done', useUpdated: true, updatedBy: 'system' },
    archiving: { status: 'done', useUpdated: true },
    archiviert: { status: 'done', useUpdated: true, updatedBy: 'system' },
  },
}

function normalizeEventStatus(raw) {
  const s = String(raw).toLowerCase()

  if (s.includes('core fehler')) return 'coreError'
  if (s.includes('deployment fehler')) return 'deployingError'
  if (s.includes('archival fehler')) return 'archivingError'

  return s
}

function buildStep(step, override, event) {
  const cfg = { ...EVENT_STATUS_DEFAULTS, ...(override || {}) }

  let updatedAt = null
  let updatedBy = null

  if (cfg.useCreated) {
    updatedAt = event.createdAt
    updatedBy = event.createdBy
  } else if (cfg.useUpdated) {
    updatedAt = event.updatedAt
    updatedBy = cfg.updatedBy === 'system' ? 'System' : event.updatedBy
  }

  return {
    ...step,
    date: cfg.date ?? null,
    status: cfg.status,
    updatedAt,
    updatedBy,
    help: cfg.help || step.help,
    error: typeof cfg.error === 'function' ? cfg.error() : cfg.error,
  }
}

const mergedSteps = computed(() => {
  const eventStatus = normalizeEventStatus(event.value?.status || '')
  const overrides = EVENT_STATUS_MAP[eventStatus] || {}

  return stepTemplate.value
    .map((step) => {
      const override = overrides[step.name]
      return override ? buildStep(step, override, event.value) : step
    })
    .sort((a, b) => Number(a.id) - Number(b.id))
})

function stepAction(step, action) {
  emit('action', action)
}

function toggleDetails(step) {
  openStepId.value = openStepId.value === step.id ? null : step.id
}

const componentClass = computed(() => {
  const base = ['p-4', 'shadow-lg', 'rounded-lg']

  if (styleStore.darkMode) {
    base.push(styleStore.darkText, styleStore.darkBg)
  } else {
    base.push(styleStore.whiteBg)
  }

  return base
})

const cardHeaderStatusTooltip = (step) => {
  if (step.status === 'manual') {
    if (step.name === 'aktiv') {
      return t('components.eventStatus.tooltipManualRollout')
    }
    if (step.name === 'archiving') {
      return t('components.eventStatus.tooltipManualArchive')
    }
    if (step.name === 'archiviert') {
      return t('components.eventStatus.tooltipManualReArchive')
    }
  }

  if (step.date && step.date.object) {
    return formatDate(step.date.object, {
      weekday: 'long',
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
      timeZoneName: 'shortOffset',
    })
  }

  return undefined
}

const emitReload = () => {
  return emit('reload')
}
</script>

<template>
  <SectionTitleLineWithButton
    :title="$t('common.status')"
    :icon="mdiListStatus"
    :reload="emitReload"
  />

  <!-- Information Notification -->
  <NotificationBar :dismissable="false" color="info" :icon="mdiInformation">
    <p>
      <b>{{ t('components.eventStatus.infoTitle') }}</b>

      <br />

      {{ t('components.eventStatus.infoSubtext') }}
    </p>
  </NotificationBar>

  <div :class="componentClass">
    <div class="relative">
      <div
        v-for="(step, index) in mergedSteps"
        :key="step.id"
        class="grid grid-cols-[48px_1fr] gap-4 relative mb-8 last:mb-0"
      >
        <!-- Line -->
        <div
          v-if="index < mergedSteps.length - 1"
          class="absolute left-[22px] top-[22px] bottom-[-32px] w-[2px] bg-gray-200 dark:bg-slate-700"
        ></div>

        <!-- Icon -->
        <div class="relative flex items-start">
          <div
            class="w-11 h-11 flex items-center justify-center rounded-full border-2 bg-white dark:bg-slate-900 z-10"
            :class="STATUS_CONFIG[step?.status]?.circle"
          >
            <BaseIcon
              v-if="STATUS_CONFIG[step?.status]?.icon"
              :path="STATUS_CONFIG[step?.status]?.icon"
              size="22"
            />
          </div>
        </div>

        <!-- Card -->
        <div
          class="p-5 bg-white dark:bg-slate-800 border rounded-xl shadow-sm"
          :class="STATUS_CONFIG[step?.status]?.circle"
        >
          <!-- Header -->
          <div class="flex justify-between items-start mb-1">
            <h3 class="font-semibold text-base">{{ step.title }}</h3>

            <span
              v-tooltip="cardHeaderStatusTooltip(step)"
              class="text-xs font-semibold px-2 py-1 rounded-full"
              :class="STATUS_CONFIG[step?.status]?.badge"
            >
              {{
                step?.date?.label
                  ? step.date.label
                  : STATUS_CONFIG[step?.status]?.label
              }}
            </span>
          </div>

          <!-- Description -->
          <p class="text-sm text-gray-600 dark:text-gray-300 pb-2">
            {{ step.description }}
          </p>

          <!-- Error -->
          <NotificationBar
            v-if="step.error"
            :dismissable="false"
            color="danger"
            :icon="mdiAlert"
          >
            <span class="pl-2 font-medium">{{ step.error }}</span>
          </NotificationBar>

          <!-- Date & users -->
          <!-- fixme: needs fix in backend for full metadata of each step-->
          <div
            v-if="step.updatedAt && step.name === 'geplant'"
            class="mt-3 text-xs text-gray-500 dark:text-gray-300"
          >
            <!-- Label -->
            <div class="font-medium mb-1">
              {{ step.actionLabel }}
            </div>

            <!-- Date & User data -->
            <div class="flex items-center space-x-3">
              <div
                class="px-2 py-1 bg-gray-100 dark:bg-slate-700 rounded-md flex items-center"
              >
                <BaseIcon :path="mdiCalendarRange" size="16" class="mr-1" />

                <time
                  v-tooltip="
                    formatDate(step.updatedAt, {
                      weekday: 'long',
                      day: '2-digit',
                      month: '2-digit',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                      hour12: false,
                      timeZoneName: 'shortOffset',
                    })
                  "
                  >{{
                    formatDate(step.updatedAt, {
                      relative: true,
                      day: '2-digit',
                      month: '2-digit',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })
                  }}</time
                >
              </div>

              <div
                class="px-2 py-1 bg-gray-100 dark:bg-slate-700 rounded-md flex items-center"
              >
                <BaseIcon :path="mdiAccount" size="16" class="mr-1" />
                {{ step.updatedBy }}
              </div>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="mt-4 flex justify-end space-x-2">
            <!-- Stop Button-->
            <BaseButton
              v-if="
                userPermissions.stop &&
                step.status === 'running' &&
                step.name === 'aktiv'
              "
              :icon="mdiStopCircle"
              color="danger"
              :label="$t('components.eventStatus.stop')"
              small
              @click="stepAction(step, 'stop')"
            />

            <!-- Extend Button-->
            <BaseButton
              v-if="
                userPermissions.edit &&
                step.status === 'running' &&
                step.name === 'aktiv'
              "
              :icon="mdiCalendarEndOutline"
              color="warning"
              :label="$t('components.eventStatus.extendShorten')"
              small
              @click="stepAction(step, 'extend')"
            />

            <!-- Retry Rollout Button-->
            <BaseButton
              v-if="
                step.status === 'error' &&
                step.name === 'deploying' &&
                userPermissions.rollout
              "
              :icon="mdiRefresh"
              color="danger"
              :label="$t('common.retry')"
              small
              @click="stepAction(step, 'rollout')"
            />

            <!-- Retry Archiving Button-->
            <BaseButton
              v-if="
                step.status === 'error' &&
                step.name === 'archiving' &&
                userPermissions.stop
              "
              :icon="mdiRefresh"
              color="danger"
              :label="$t('common.retry')"
              small
              @click="stepAction(step, 'stop')"
            />

            <!-- Delete Button-->
            <BaseButton
              v-if="
                userPermissions.delete &&
                ((step.status === 'done' && step.name === 'archiviert') ||
                  (step.status !== 'done' && step.name === 'geplant'))
              "
              :icon="mdiDelete"
              color="danger"
              :label="$t('common.delete')"
              small
              @click="stepAction(step, 'delete')"
            />

            <!-- Edit Button-->
            <BaseButton
              v-if="
                userPermissions.edit &&
                step.status !== 'done' &&
                step.name === 'geplant'
              "
              :icon="mdiPencil"
              color="info"
              :label="$t('common.edit')"
              small
              @click="stepAction(step, 'edit')"
            />

            <!-- Rollout Button-->
            <BaseButton
              v-if="
                userPermissions.rollout &&
                step.status === 'running' &&
                step.name === 'geplant'
              "
              :icon="mdiCloudRefreshVariant"
              color="success"
              :label="$t('components.eventStatus.rollout')"
              small
              @click="stepAction(step, 'rollout')"
            />

            <!-- Details Button -->
            <BaseButton
              :icon="mdiInformation"
              color="info"
              :label="$t('common.details')"
              small
              @click="toggleDetails(step)"
            />
          </div>

          <!-- Details -->
          <transition name="slide-fade">
            <div
              v-if="openStepId === step.id"
              class="mt-4 p-4 bg-gray-50 dark:bg-slate-700/50 rounded-lg border border-gray-200 dark:border-slate-600"
            >
              <!-- Overview -->
              <div class="mb-4">
                <h4 class="font-semibold mb-1">{{ t('common.overview') }}</h4>

                <p class="text-sm text-gray-700 dark:text-gray-300">
                  {{ step.description }}
                </p>
              </div>

              <!-- Tips -->
              <div v-if="step.help && step.help.length" class="mb-1">
                <h4 class="font-semibold mb-1">
                  {{ t('components.eventStatus.tipsWarnings') }}
                </h4>

                <ul class="list-disc list-inside text-sm ml-1 space-y-1">
                  <li v-for="option in step.help" :key="option">
                    {{ option }}
                  </li>
                </ul>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
.slide-fade-enter-from {
  opacity: 0;
  transform: translateY(-4px);
  max-height: 0;
}
.slide-fade-enter-to {
  opacity: 1;
  transform: translateY(0);
  max-height: 800px;
}
.slide-fade-leave-from {
  opacity: 1;
  max-height: 800px;
}
.slide-fade-leave-to {
  opacity: 0;
  max-height: 0;
}
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}
</style>
