<script setup>
import {
  mdiAccountGroup,
  mdiAlert,
  mdiCalendarRange,
  mdiCheckAll,
  mdiConnection,
  mdiDesktopClassic,
  mdiFileDocumentOutline,
  mdiInformationOutline,
  mdiSchool,
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
})

const emit = defineEmits(['update:modelValue', 'confirmed'])

const { t } = useI18n()

// Event-specific data
const eventVms = ref(0)
const eventGuacamoles = ref(0)

// Load event-specific data
async function loadEventVMs() {
  const response = await backend.events.getVMs(props.object?.id, {
    page: 1,
    limit: 1,
  })
  eventVms.value = response.pageDetails.totalCount
}

async function loadEventGuacamoles() {
  const response = await backend.events.getGuacamoles(props.object?.id, {
    page: 1,
    limit: 1,
  })
  eventGuacamoles.value = response.pageDetails.totalCount
}

// Use shared composable
const {
  loading,
  loadError,
  modalVisible,
  event,
  totalParticipantsCount,
  textUsersCount,
  duration,
  actualDuration,
  onFormSubmit,
  closeModal,
  loadAllData,
  mainStore,
} = useEventWarningModal({
  modelValue: toRef(props, 'modelValue'),
  object: toRef(props, 'object'),
  emit,
  onOpen: (load) => load([loadEventVMs(), loadEventGuacamoles()]),
})

const moodleEnabled = computed(() => !!mainStore?.settings?.moodle?.enabled)
</script>

<template>
  <CardBoxModal
    v-model="modalVisible"
    :has-button="false"
    :title="$t('components.eventWarningStop.confirmationRequired')"
    custom-class="!w-[60vw]"
  >
    <!-- Loading State -->
    <EventWarningLoadingSpinner v-if="loading" />

    <!-- Error State -->
    <template v-else-if="loadError">
      <NotificationBar :dismissable="false" color="danger" :icon="mdiAlert">
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
        <!-- Warning Notification -->
        <NotificationBar :dismissable="false" color="danger" :icon="mdiAlert">
          <div class="space-y-2">
            <p>
              <strong>{{
                $t('components.eventWarningStop.stopImmediate')
              }}</strong>
            </p>

            <p class="text-sm">
              {{ $t('components.eventWarningStop.stopDescription') }}
            </p>

            <p>
              <strong>{{
                $t('components.eventWarningStop.irreversible')
              }}</strong>
            </p>
          </div>
        </NotificationBar>

        <!-- Important Hints -->
        <div
          class="bg-gray-50 dark:bg-slate-800/50 rounded-lg p-4 border border-gray-200 dark:border-slate-700"
        >
          <div class="flex items-start gap-3">
            <BaseIcon
              :path="mdiInformationOutline"
              class="text-blue-500 dark:text-blue-400 mt-0.5 shrink-0"
              size="20"
            />

            <div class="text-sm space-y-1">
              <p>{{ $t('components.eventWarningStop.dataLossHint') }}</p>

              <p v-if="moodleEnabled && event?.moodleCourseId != null">
                {{ $t('components.eventWarningStop.moodleHint') }}
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
            {{ $t('components.eventWarningStop.deploymentDetails') }}
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
                  {{ $t('components.eventWarningStop.environment') }}:
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

              <div class="text-sm space-y-2">
                <div>
                  <p class="text-gray-500 dark:text-slate-400">
                    {{ $t('components.eventWarningStop.plannedPeriod') }}
                  </p>

                  <p class="text-gray-900 dark:text-slate-100">
                    {{
                      formatDate(event?.dateStart, {
                        weekday: 'long',
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric',
                      })
                    }}
                    {{ $t('components.eventWarningStop.until') }}
                    {{
                      formatDate(event?.dateEnd, {
                        weekday: 'long',
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric',
                      })
                    }}
                    ({{ duration }})
                  </p>
                </div>

                <div>
                  <p class="text-gray-500 dark:text-slate-400">
                    {{ $t('components.eventWarningStop.actualPeriod') }}
                  </p>

                  <p class="text-gray-900 dark:text-slate-100">
                    {{
                      formatDate(event?.dateStart, {
                        weekday: 'long',
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric',
                      })
                    }}
                    {{ $t('components.eventWarningStop.until') }}
                    {{
                      formatDate(new Date(), {
                        weekday: 'long',
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric',
                      })
                    }}
                    ({{ actualDuration }})
                  </p>
                </div>
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
                  {{ $t('components.eventWarningStop.lastDeploymentMessage') }}
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
            :label="$t('components.eventWarningStop.participants')"
            :subtitle="textUsersCount"
            color="blue"
          />

          <EventWarningResourceCard
            :icon="mdiDesktopClassic"
            :value="eventVms"
            :label="$t('components.eventWarningStop.vmsToDelete')"
            color="red"
          />

          <EventWarningResourceCard
            :icon="mdiConnection"
            :value="eventGuacamoles"
            :label="$t('components.eventWarningStop.connectionsToDelete')"
            color="orange"
          />
        </div>

        <BaseDivider />

        <!-- Footer Actions -->
        <CardBoxComponentFooter>
          <BaseButtons>
            <BaseButton
              :label="$t('common.confirm')"
              type="submit"
              :icon="mdiCheckAll"
              color="danger"
              @click="onFormSubmit"
            />

            <BaseButton
              type="button"
              color="danger"
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
