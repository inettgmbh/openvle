<script setup>
import {
  mdiAccountGroup,
  mdiAlert,
  mdiAlertCircleOutline,
  mdiCalendarRange,
  mdiCheckAll,
  mdiCheckCircleOutline,
  mdiConnection,
  mdiDesktopClassic,
  mdiFileDocumentOutline,
  mdiInformationOutline,
  mdiSchool,
  mdiServerNetwork,
} from '@mdi/js'
import { computed, ref, toRef } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseDivider from '@/components/BaseDivider.vue'
import BaseIcon from '@/components/BaseIcon.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxComponentFooter from '@/components/CardBoxComponentFooter.vue'
import CardBoxModal from '@/components/CardBoxModal.vue'
import EventWarningLoadingSpinner from '@/components/EventWarningLoadingSpinner.vue'
import EventWarningResourceCard from '@/components/EventWarningResourceCard.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import { useEventWarningModal } from '@/composables/useEventWarningModal'
import backend from '@/services'
import { formatDate } from '@/utils/dataUtils'

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true,
  },
  object: {
    type: Object,
    default: null,
  },
  permissions: {
    type: Object,
    default: null,
  },
  totalParticipants: {
    type: Number,
    default: 0,
  },
})

const emit = defineEmits(['update:modelValue', 'confirmed'])

const { t } = useI18n()

// Template and profile data
const templates = ref([])
const templatesTotalCount = ref(0)
const totalGuacamoleConnectionProfiles = ref(0)
const allProfiles = ref([])
const courseMoodleCourseId = ref(null)

// Use shared composable
const {
  loading,
  loadError,
  modalVisible,
  event,
  userStudentsCount,
  userTeachersCount,
  textUsersCount,
  duration,
  onFormSubmit,
  closeModal,
  mainStore,
} = useEventWarningModal({
  modelValue: toRef(props, 'modelValue'),
  object: toRef(props, 'object'),
  emit,
  onOpen: (load) => load([loadCourseTemplates()]),
})

const moodleEnabled = computed(() => !!mainStore?.settings?.moodle?.enabled)

// Participant count from props (for rollout, we use the prop)
const totalParticipantsCount = computed(() => props.totalParticipants || 0)
const hasParticipants = computed(() => totalParticipantsCount.value > 0)

// Settings-based requirements
const studentRequired = computed(
  () => (mainStore?.settings?.events?.create?.participants?.students ?? 0) > 0,
)

const teacherRequired = computed(
  () => (mainStore?.settings?.events?.create?.participants?.teachers ?? 0) > 0,
)

// Guacamole connection calculations
const totalGuacamoles = computed(() => {
  const students = userStudentsCount.value
  const teachers = userTeachersCount.value
  const totalUsers = students + teachers
  const connectionsPerVM = totalGuacamoleConnectionProfiles.value
  const studentConnections = students * connectionsPerVM
  const teacherConnections = teachers * totalUsers * connectionsPerVM
  return studentConnections + teacherConnections
})

// VM calculations
const vmsToCreateCount = computed(
  () =>
    (userStudentsCount.value + userTeachersCount.value) *
    templatesTotalCount.value,
)

// Permission checks
const missingPermissions = computed(() => {
  const missing = []
  if (!props.permissions?.canReadCourse) {
    missing.push(t('components.eventWarningRollout.permEnvironments'))
  }
  if (!props.permissions?.canReadConnectionProfiles) {
    missing.push(t('components.eventWarningRollout.permConnectionProfiles'))
  }
  return missing
})

const permissionWarningText = computed(() => {
  if (!missingPermissions.value.length) return null
  const names = missingPermissions.value.join(` ${t('common.and')} `)
  return t('components.eventWarningRollout.permissionWarning', { names })
})

// Deployment validation checks
function checkTemplatesAvailable() {
  if (missingPermissions.value.length) return null
  if (!templatesTotalCount.value) {
    return {
      title: t('components.eventWarningRollout.checks.noTemplates.title'),
      message: t('components.eventWarningRollout.checks.noTemplates.message'),
    }
  }
  return null
}

function checkTemplatesDeployable() {
  if (missingPermissions.value.length) return null

  const invalidTemplates = templates.value?.items?.filter(
    (tmpl) => !tmpl.proxmoxNode || !tmpl.proxmoxId,
  )

  if (invalidTemplates?.length) {
    const names = invalidTemplates.map((tmpl) => tmpl.name).join(', ')
    return {
      title: t('components.eventWarningRollout.checks.missingProxmox.title'),
      message: t(
        'components.eventWarningRollout.checks.missingProxmox.message',
        { names },
      ),
    }
  }
  return null
}

function checkParticipantsAvailable() {
  const noParticipants = !props.totalParticipants
  const noStudents = !userStudentsCount.value
  const noTeachers = !userTeachersCount.value

  if (noParticipants && studentRequired.value && teacherRequired.value) {
    return {
      title: t('components.eventWarningRollout.checks.noParticipants.title'),
      message: t(
        'components.eventWarningRollout.checks.noParticipants.message',
      ),
    }
  }

  if (noStudents && studentRequired.value) {
    return {
      title: t('components.eventWarningRollout.checks.noStudents.title'),
      message: t('components.eventWarningRollout.checks.noStudents.message'),
    }
  }

  if (noTeachers && teacherRequired.value) {
    return {
      title: t('components.eventWarningRollout.checks.noTeachers.title'),
      message: t('components.eventWarningRollout.checks.noTeachers.message'),
    }
  }

  return null
}

function checkGuacamoleAvailable() {
  if (!templates.value?.items?.length) return null

  const incompleteTemplates = templates.value.items.filter(
    (tmpl) => (profilesByTemplate.value[tmpl.id] || []).length === 0,
  )

  if (incompleteTemplates.length > 0) {
    const names = incompleteTemplates.map((tmpl) => tmpl.name).join(', ')
    return {
      title: t(
        'components.eventWarningRollout.checks.missingConnProfiles.title',
      ),
      message: t(
        'components.eventWarningRollout.checks.missingConnProfiles.message',
        { names },
      ),
    }
  }
  return null
}

function checkEventDates() {
  const endDate = new Date(event.value?.dateEnd)

  if (isNaN(endDate.getTime())) return null
  if (endDate >= new Date()) return null

  return {
    title: t('components.eventWarningRollout.checks.endDatePast.title'),
    message: t('components.eventWarningRollout.checks.endDatePast.message'),
  }
}

const deploymentChecks = computed(() =>
  [
    checkTemplatesAvailable(),
    checkTemplatesDeployable(),
    checkParticipantsAvailable(),
    checkGuacamoleAvailable(),
    checkEventDates(),
  ].filter(Boolean),
)

const submitEnabled = computed(() => deploymentChecks.value.length === 0)

const submitTooltip = computed(() =>
  submitEnabled.value
    ? t('components.eventWarningRollout.submitReady')
    : t('components.eventWarningRollout.submitCheck'),
)

// Profile mapping
const profilesByTemplate = computed(() => {
  const map = {}
  if (Array.isArray(allProfiles.value)) {
    for (const profile of allProfiles.value) {
      if (!map[profile.objectId]) {
        map[profile.objectId] = []
      }
      map[profile.objectId].push(profile)
    }
  }
  return map
})

function connectionsText(profiles) {
  const count = Array.isArray(profiles) ? profiles.length : 0
  return t('components.eventWarningRollout.connectionProfileCount', { count })
}

// Data loading
async function loadCourseTemplates() {
  if (!event.value?.courseId) {
    templates.value = []
    templatesTotalCount.value = 0
    allProfiles.value = []
    totalGuacamoleConnectionProfiles.value = 0
    courseMoodleCourseId.value = null
    return
  }

  // Fetch course to check for Moodle template course
  if (moodleEnabled.value) {
    try {
      const course = await backend.courses.get(event.value.courseId)
      courseMoodleCourseId.value = course.moodleCourseId ?? null
    } catch {
      courseMoodleCourseId.value = null
    }
  }

  const response = await backend.courses.getTemplates(event.value.courseId, {})
  templates.value = response
  templatesTotalCount.value = response?.pageDetails?.totalCount || 0

  if (response?.items?.length) {
    const profilesPromises = response.items.map((template) =>
      backend.connections.listByObject('Template', template.id, {}),
    )

    const profilesResults = await Promise.all(profilesPromises)

    allProfiles.value = profilesResults.flatMap((result) => result.items || [])
    totalGuacamoleConnectionProfiles.value = profilesResults.reduce(
      (acc, result) => acc + (result?.pageDetails?.totalCount || 0),
      0,
    )
  } else {
    allProfiles.value = []
    totalGuacamoleConnectionProfiles.value = 0
  }
}
</script>

<template>
  <CardBoxModal
    v-model="modalVisible"
    :has-button="false"
    :title="$t('components.eventWarningRollout.eventRollout')"
    custom-class="!w-[60vw]"
    scrollable
  >
    <!-- Loading State -->
    <EventWarningLoadingSpinner v-if="loading" />

    <!-- Error State -->
    <template v-else-if="loadError">
      <NotificationBar
        :dismissable="false"
        color="danger"
        :icon="mdiAlertCircleOutline"
      >
        <p class="font-semibold">{{ $t('common.errorLoading') }}</p>

        <p class="text-sm">{{ loadError }}</p>
      </NotificationBar>

      <div class="mt-4 flex justify-end">
        <BaseButton
          :label="$t('common.close')"
          color="danger"
          outline
          @click="closeModal"
        />
      </div>
    </template>

    <!-- Content -->
    <template v-else>
      <CardBox class="space-y-6">
        <!-- All Notifications -->
        <div class="space-y-3 pb-2">
          <!-- Status Notifications -->
          <NotificationBar
            v-if="submitEnabled && permissionWarningText"
            :dismissable="false"
            color="warning"
            :icon="mdiAlertCircleOutline"
          >
            {{ permissionWarningText }}
          </NotificationBar>

          <NotificationBar
            v-if="submitEnabled && !permissionWarningText"
            :dismissable="false"
            color="success"
            :icon="mdiCheckCircleOutline"
          >
            <span class="font-semibold">{{
              $t('components.eventWarningRollout.readyToRollout')
            }}</span>
          </NotificationBar>

          <!-- Validation Errors -->
          <NotificationBar
            v-for="(check, index) in deploymentChecks"
            :key="index"
            color="danger"
            :dismissable="false"
            :icon="mdiAlertCircleOutline"
          >
            <p class="font-semibold">{{ check.title }}</p>

            <p class="text-sm">{{ check.message }}</p>
          </NotificationBar>

          <!-- High VM Count Warning -->
          <NotificationBar
            v-if="vmsToCreateCount > 150"
            :dismissable="false"
            color="warning"
            :icon="mdiAlert"
          >
            <p class="font-semibold">
              {{ $t('components.eventWarningRollout.highVmCount') }}
            </p>

            <p class="text-sm">
              {{
                $t('components.eventWarningRollout.highVmCountMessage', {
                  count: vmsToCreateCount,
                })
              }}
            </p>
          </NotificationBar>
        </div>

        <!-- Important Hints -->
        <div
          v-if="deploymentChecks.length === 0"
          class="bg-gray-50 dark:bg-slate-800/50 rounded-lg p-4 border border-gray-200 dark:border-slate-700"
        >
          <div class="flex items-start gap-3">
            <BaseIcon
              :path="mdiInformationOutline"
              class="text-blue-500 dark:text-blue-400 mt-0.5 shrink-0"
              size="20"
            />

            <div class="text-sm space-y-2">
              <p>
                <strong>{{
                  $t('components.eventWarningRollout.immediateStart')
                }}</strong>
                {{ $t('components.eventWarningRollout.immediateStartSub') }}
              </p>

              <p>
                <strong>{{
                  $t('components.eventWarningRollout.irreversible')
                }}</strong>
                {{ $t('components.eventWarningRollout.irreversibleSub') }}
              </p>

              <p v-if="courseMoodleCourseId != null">
                <strong>{{
                  $t('components.eventWarningRollout.moodleHint')
                }}</strong>
                {{ $t('components.eventWarningRollout.moodleHintSub') }}
              </p>
            </div>
          </div>
        </div>

        <BaseDivider />

        <!-- Deployment Details -->
        <div>
          <h3
            class="text-lg font-semibold mb-4 flex items-center gap-2 text-gray-900 dark:text-slate-100"
          >
            <BaseIcon :path="mdiFileDocumentOutline" size="20" />
            {{ $t('components.eventWarningRollout.deploymentDetails') }}
          </h3>

          <!-- Event Info Card -->
          <div
            class="bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 divide-y divide-gray-200 dark:divide-slate-700"
          >
            <!-- Name & Course -->
            <div class="p-3 flex items-center gap-3">
              <BaseIcon
                :path="mdiSchool"
                class="text-gray-400 dark:text-slate-500 shrink-0"
                size="18"
              />

              <div class="min-w-0">
                <p
                  class="font-medium text-gray-900 dark:text-slate-100 truncate"
                >
                  {{ event?.name || '-' }}
                </p>

                <p class="text-sm text-gray-500 dark:text-slate-400 truncate">
                  {{ $t('components.eventWarningRollout.environment') }}:
                  {{ event?.course || '-' }}
                </p>
              </div>
            </div>

            <!-- Date Range -->
            <div class="p-3 flex items-center gap-3">
              <BaseIcon
                :path="mdiCalendarRange"
                class="text-gray-400 dark:text-slate-500 shrink-0"
                size="18"
              />

              <div class="text-sm">
                <p class="text-gray-900 dark:text-slate-100">
                  {{ $t('components.eventWarningRollout.todayUntil') }}
                  {{
                    formatDate(event?.dateEnd, {
                      day: '2-digit',
                      month: '2-digit',
                      year: 'numeric',
                    })
                  }}
                </p>

                <p class="text-gray-500 dark:text-slate-400">
                  {{ $t('components.eventWarningRollout.duration') }}:
                  {{ duration }}
                </p>
              </div>
            </div>

            <!-- Deployment Status (if exists) -->
            <div
              v-if="event?.deployment_status"
              class="p-3 flex items-center gap-3"
            >
              <BaseIcon
                :path="mdiInformationOutline"
                class="text-gray-400 dark:text-slate-500 shrink-0"
                size="18"
              />

              <div class="text-sm">
                <p class="text-gray-500 dark:text-slate-400">
                  {{ $t('components.eventWarningRollout.lastMessage') }}
                </p>

                <p class="text-gray-900 dark:text-slate-100">
                  {{ event.deployment_status }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Resources Summary -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-2">
          <EventWarningResourceCard
            :icon="mdiAccountGroup"
            :value="totalParticipantsCount"
            :label="$t('components.eventWarningRollout.participants')"
            :subtitle="textUsersCount"
            color="blue"
          />

          <EventWarningResourceCard
            :icon="mdiDesktopClassic"
            :value="vmsToCreateCount"
            :label="$t('components.eventWarningRollout.vmsToCreate')"
            color="emerald"
          />

          <EventWarningResourceCard
            :icon="mdiConnection"
            :value="totalGuacamoles"
            :label="$t('components.eventWarningRollout.connectionsToCreate')"
            color="amber"
          />
        </div>

        <!-- VM Templates Details -->
        <div v-if="templates?.items?.length" class="space-y-2 mt-2">
          <h4
            class="text-sm font-medium text-gray-700 dark:text-slate-300 flex items-center gap-2"
          >
            <BaseIcon :path="mdiDesktopClassic" size="16" />
            {{ $t('components.eventWarningRollout.vmTemplates') }} ({{
              templatesTotalCount
            }})
          </h4>

          <div class="space-y-2">
            <div
              v-for="item in templates.items"
              :key="item.id"
              :class="[
                'rounded border p-3',
                profilesByTemplate[item.id]?.length
                  ? 'bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700'
                  : 'bg-red-50 dark:bg-red-900/20 border-red-300 dark:border-red-700',
              ]"
            >
              <div class="flex items-center justify-between">
                <span
                  class="font-medium text-gray-900 dark:text-slate-100 text-sm"
                >
                  {{ item.name }}
                </span>

                <span
                  :class="[
                    'text-xs',
                    profilesByTemplate[item.id]?.length
                      ? 'text-gray-500 dark:text-slate-400'
                      : 'text-red-600 dark:text-red-400 font-medium',
                  ]"
                >
                  {{ connectionsText(profilesByTemplate[item.id]) }}
                </span>
              </div>

              <!-- Connection Profiles -->
              <div
                v-if="profilesByTemplate[item.id]?.length"
                class="mt-2 space-y-1"
              >
                <div
                  v-for="profile in profilesByTemplate[item.id]"
                  :key="profile.id"
                  class="flex items-center gap-2 text-xs text-gray-600 dark:text-slate-400"
                >
                  <BaseIcon
                    :path="mdiConnection"
                    size="12"
                    class="text-gray-400 dark:text-slate-500"
                  />

                  <span class="font-mono">
                    {{ profile.protocol }}://{{ profile.username }}@{{
                      item.name
                    }}:{{ profile.port }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Formula Explanation -->
        <div
          class="text-xs text-gray-500 dark:text-slate-500 bg-gray-50 dark:bg-slate-800/30 rounded p-3"
        >
          <div class="flex items-start gap-2">
            <BaseIcon
              :path="mdiServerNetwork"
              size="14"
              class="mt-0.5 shrink-0"
            />

            <div>
              <p class="mb-1">
                <strong
                  >{{ $t('components.eventWarningRollout.formula') }}:</strong
                >
              </p>

              <p>{{ $t('components.eventWarningRollout.formulaVMs') }}</p>

              <p>
                {{ $t('components.eventWarningRollout.formulaConnections') }}
              </p>
            </div>
          </div>
        </div>

        <BaseDivider />

        <!-- Footer Actions -->
        <CardBoxComponentFooter>
          <BaseButtons>
            <BaseButton
              v-tooltip="submitTooltip"
              :label="$t('components.eventWarningRollout.rollout')"
              type="submit"
              :icon="mdiCheckAll"
              color="warning"
              :disabled="!submitEnabled"
              @click="onFormSubmit"
            />

            <BaseButton
              type="button"
              color="warning"
              :label="$t('common.cancel')"
              outline
              @click="closeModal"
            />
          </BaseButtons>
        </CardBoxComponentFooter>
      </CardBox>
    </template>
  </CardBoxModal>
</template>
