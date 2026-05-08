<script setup>
import {
  mdiAccount,
  mdiAccountKey,
  mdiAccountMultiple,
  mdiAccountNetwork,
  mdiAccountOutline,
  mdiAsterisk,
  mdiClockPlusOutline,
  mdiFormTextboxPassword,
  mdiLock,
  mdiMail,
  mdiNumeric,
  mdiShieldAccount,
  mdiTextBox,
} from '@mdi/js'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseDivider from '@/components/BaseDivider.vue'
import BaseIcon from '@/components/BaseIcon.vue'
import BaseTable from '@/components/BaseTable.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxModal from '@/components/CardBoxModal.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import PillTag from '@/components/PillTag.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { useMainStore } from '@/stores/main'
import { useRateLimitStore } from '@/stores/rateLimit'
import { formatDate, formatDateRelativeWithWeekday } from '@/utils/dataUtils'
import { getObjectModelLabelByKeyspace } from '@/utils/objectModelPermissions'
import { usePaginationList } from '@/utils/pagination'

const { t } = useI18n()
const mainStore = useMainStore()
const rateLimitStore = useRateLimitStore()
const user = ref([])
const modalPasswordChange = ref(false)
const toast = useToast()

async function fetchOwnUser() {
  try {
    await backend.me.get().then((response) => {
      user.value = response
      user.value.external = user.value.user_type !== 'internal'
    })
  } catch (error) {
    toast.error(t('views.userProfile.loadError'))
  }
}
fetchOwnUser()

const passwordForm = reactive({
  password_current: '',
  password: '',
  password_confirmation: '',
})

async function changePassword(passwordForm) {
  try {
    await backend.me.updatePassword(
      passwordForm.password_current,
      passwordForm.password,
      passwordForm.password_confirmation,
    )
    toast.success(t('views.userProfile.passwordChanged'))
    modalPasswordChange.value = false
    passwordForm.password_current = ''
    passwordForm.password = ''
    passwordForm.password_confirmation = ''
  } catch {
    // Re-open the modal so the user can correct + retry — unless a
    // rate-limit just kicked in (the watcher above closes the modal in
    // that case
    if (!rateLimitStore.active) modalPasswordChange.value = true
  }
}

// Close the password modal automatically when a rate-limit kicks in,
// so the user only sees the (more important) rate-limit modal.
watch(
  () => rateLimitStore.active,
  (active) => {
    if (active) modalPasswordChange.value = false
  },
)

const passwordChangeTooltip = computed(() => {
  if (!rateLimitStore.active) return null
  const time = rateLimitStore.expiresAt
    ? new Date(rateLimitStore.expiresAt).toLocaleTimeString(undefined, {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      })
    : ''
  return {
    text: t('views.userProfile.passwordChangeRateLimited', { time }),
  }
})

/* Activities */
const activities = ref([])
const activitiesLoading = ref(true)

const {
  currentPage,
  perPage,
  sortColumnKey,
  sortDirection,
  searchField,
  searchValue,
} = usePaginationList({
  initialPage: 1,
  initialPerPage: 100,
  initialSortColumn: 'timestamp',
  initialSortOrder: 'desc',
  initialSearchField: null,
  initialSearchValue: null,
  fetch: fetchActivities,
  useReplace: true,
  syncQuery: false,
})

async function fetchActivities() {
  try {
    activitiesLoading.value = true

    const response = await backend.activities.listOwn({
      page: currentPage.value,
      limit: perPage.value,
      sort_by: sortColumnKey.value,
      sort_order: sortDirection.value,
      search_field: searchField.value,
      search_value: searchValue.value,
    })
    activities.value = response.items
    activities.value.count = response.pageDetails.totalCount
  } catch (error) {
    toast.error(
      `${t('common.loadErrorPlural', { entities: t('objectTypes.activity.plural') })}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  } finally {
    activitiesLoading.value = false
  }
}

onMounted(() => {
  fetchActivities()
})

// Filter activities to exclude GET requests, enrich with description, limit to 25
const filteredActivities = computed(() => {
  return activities.value
    .filter((activity) => activity.requestMethod?.toUpperCase() !== 'GET')
    .slice(0, 25)
    .map((activity) => ({
      ...activity,
      actionDescription: buildActionDescription(
        activity.requestMethod,
        activity.requestUrl,
      ),
    }))
})

/**
 * Extracts the object model label from an API URL.
 * @param {string} url - The API URL (e.g., "/v1/users/uuid/")
 * @returns {string} Translated object label (e.g., "Benutzer")
 */
function getObjectModelFromUrl(url) {
  if (!url) return t('common.object')

  const segments = url
    .replace(/^\/v\d+\//, '')
    .split('/')
    .filter(Boolean)

  if (segments.length === 0) return t('common.object')

  const keyspace = segments[0]
  if (keyspace == 'object-permissions')
    return t('objectTypes.permission.singular')
  return getObjectModelLabelByKeyspace(keyspace)
}

/**
 * Translates HTTP method to German past tense verb.
 * @param {string} method - HTTP method (POST, PUT, PATCH, DELETE)
 * @returns {string} German past tense verb
 */
function translateMethodPastTense(method) {
  switch (method?.toUpperCase()) {
    case 'POST':
      return t('views.userProfile.actionCreated')
    case 'PUT':
    case 'PATCH':
      return t('views.userProfile.actionChanged')
    case 'DELETE':
      return t('views.userProfile.actionDeleted')
    default:
      return method || '–'
  }
}

/**
 * Builds a human-readable action description.
 * @param {string} method - HTTP method
 * @param {string} url - Request URL
 * @returns {string} Description like "Rolle erstellt"
 */
function buildActionDescription(method, url) {
  // Login is a POST to /auth/
  if (method?.toUpperCase() === 'POST' && /\/auth(\/|$)/.test(url)) {
    return 'Login'
  }

  const model = getObjectModelFromUrl(url)
  const action = translateMethodPastTense(method)
  return `${model} ${action}`
}
</script>

<template>
  <CardBoxModal
    v-model="modalPasswordChange"
    form
    :title="$t('views.userProfile.changePassword')"
    button="success"
    has-cancel
    has-search
    :button-label="$t('views.system.settings.change')"
    :disabled="rateLimitStore.active"
    @form-submitted="changePassword(passwordForm)"
  >
    <FormField
      :label="$t('views.userProfile.currentPassword')"
      :help="$t('views.userProfile.required')"
    >
      <FormControl
        v-model="passwordForm.password_current"
        :icon="mdiAsterisk"
        name="password_current"
        type="password"
        required
        autocomplete="current-password"
      />
    </FormField>

    <BaseDivider />

    <FormField
      :label="$t('views.userProfile.newPassword')"
      :help="$t('views.userProfile.required')"
    >
      <FormControl
        v-model="passwordForm.password"
        :icon="mdiFormTextboxPassword"
        name="password"
        type="password"
        required
        autocomplete="new-password"
      />
    </FormField>

    <FormField
      :label="$t('views.userProfile.newPasswordConfirm')"
      :help="$t('views.userProfile.required')"
    >
      <FormControl
        v-model="passwordForm.password_confirmation"
        :icon="mdiFormTextboxPassword"
        name="password_confirmation"
        type="password"
        required
        autocomplete="new-password"
      />
    </FormField>
  </CardBoxModal>

  <LayoutAuthenticated>
    <SectionMain>
      <!-- Page header -->
      <SectionTitleLineWithButton
        :icon="mdiAccount"
        :title="$t('routes.profile')"
        main
      >
        <BaseButtons>
          <BaseButton
            v-if="user.id && !user.external"
            v-tooltip="passwordChangeTooltip"
            :icon="mdiLock"
            :label="$t('views.userProfile.changePassword')"
            color="warning"
            rounded-full
            small
            :disabled="rateLimitStore.active"
            @click="modalPasswordChange = true"
          />
        </BaseButtons>
      </SectionTitleLineWithButton>

      <!-- Profile hero card -->
      <CardBox class="mb-6">
        <div class="flex flex-col items-center py-4">
          <UserAvatar
            :userid="mainStore.user.id ? mainStore.user.id : ''"
            class="w-24 h-24 mb-4"
          />

          <h1 class="text-2xl font-bold">
            {{ user.name || user.username }}
          </h1>

          <p
            v-if="user.name && user.username"
            class="text-sm text-gray-500 dark:text-slate-400 mt-1"
          >
            {{ user.username }}
          </p>

          <div class="mt-3">
            <PillTag
              v-if="user.id && user.external"
              :label="$t('views.userProfile.externalAccount')"
              color="info"
              :icon="mdiAccountNetwork"
              :disabled="true"
            />

            <PillTag
              v-if="user.id && !user.external"
              :label="$t('views.userProfile.localAccount')"
              color="success"
              :icon="mdiShieldAccount"
              :disabled="true"
            />
          </div>
        </div>
      </CardBox>

      <!-- Info grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- General info -->
        <CardBox>
          <SectionTitleLineWithButton
            :icon="mdiAccount"
            :title="$t('views.userProfile.general')"
          />

          <div class="space-y-5">
            <div class="flex items-start gap-3">
              <BaseIcon
                :path="mdiAccount"
                class="text-gray-400 dark:text-slate-500 flex-shrink-0"
                size="20"
              />

              <div class="min-w-0">
                <div class="text-xs text-gray-500 dark:text-slate-400">
                  {{ $t('views.userProfile.username') }}
                </div>

                <div class="mt-0.5 truncate">
                  {{ user.username || '–' }}
                </div>
              </div>
            </div>

            <div class="flex items-start gap-3">
              <BaseIcon
                :path="mdiAccountOutline"
                class="text-gray-400 dark:text-slate-500 flex-shrink-0"
                size="20"
              />

              <div class="min-w-0">
                <div class="text-xs text-gray-500 dark:text-slate-400">
                  {{ $t('common.name') }}
                </div>

                <div class="mt-0.5 truncate">
                  {{ user.name || '–' }}
                </div>
              </div>
            </div>

            <div class="flex items-start gap-3">
              <BaseIcon
                :path="mdiMail"
                class="text-gray-400 dark:text-slate-500 flex-shrink-0"
                size="20"
              />

              <div class="min-w-0">
                <div class="text-xs text-gray-500 dark:text-slate-400">
                  {{ $t('views.userProfile.email') }}
                </div>

                <div class="mt-0.5 truncate">
                  {{ user.email || '–' }}
                </div>
              </div>
            </div>
          </div>

          <BaseDivider />

          <div class="space-y-5">
            <div class="flex items-start gap-3">
              <BaseIcon
                :path="mdiNumeric"
                class="text-gray-400 dark:text-slate-500 flex-shrink-0"
                size="20"
              />

              <div class="min-w-0">
                <div class="text-xs text-gray-500 dark:text-slate-400">
                  {{ $t('views.userProfile.internalId') }}
                </div>

                <div class="mt-0.5 font-mono text-sm truncate">
                  {{ user.id || '–' }}
                </div>
              </div>
            </div>

            <div class="flex items-start gap-3">
              <BaseIcon
                :path="mdiClockPlusOutline"
                class="text-gray-400 dark:text-slate-500 flex-shrink-0"
                size="20"
              />

              <div class="min-w-0">
                <div class="text-xs text-gray-500 dark:text-slate-400">
                  {{ $t('common.createdAt') }}
                </div>

                <div class="mt-0.5">
                  {{ user.createdAt ? formatDate(user.createdAt) : '–' }}
                </div>
              </div>
            </div>
          </div>
        </CardBox>

        <!-- Roles -->
        <CardBox>
          <SectionTitleLineWithButton
            :icon="mdiAccountMultiple"
            :title="$t('views.userProfile.roles')"
          />

          <div v-if="user.roles?.length" class="flex flex-wrap gap-2">
            <PillTag
              v-for="role in user.roles"
              :key="role.key"
              :label="role.name"
              color="info"
              :icon="mdiAccountKey"
              :disabled="true"
            />
          </div>

          <p v-else class="text-sm text-gray-500 dark:text-slate-400 italic">
            {{ $t('views.userProfile.noRolesAssigned') }}
          </p>
        </CardBox>
      </div>

      <!-- Recent activities -->
      <SectionTitleLineWithButton
        :icon="mdiTextBox"
        :title="$t('views.userProfile.recentActivities')"
      />

      <CardBox class="mb-6" has-table>
        <BaseTable
          v-if="filteredActivities"
          :current-page="currentPage"
          :per-page="perPage"
          :items-total="filteredActivities.length"
          :data="filteredActivities"
          :sort-column-key="sortColumnKey"
          :created-column-enabled="false"
          :pagination="false"
          :sort-direction="sortDirection"
          :loading="activitiesLoading"
          object-model="activities"
          :columns="[
            {
              label: $t('views.userProfile.timestamp'),
              key: 'timestamp',
              sortable: false,
              width: '250px',
            },
            {
              label: $t('views.userProfile.ipAddress'),
              key: 'requestClientIP',
              sortable: false,
              width: '200px',
            },
            {
              label: $t('views.userProfile.activity'),
              key: 'actionDescription',
              sortable: false,
            },
          ]"
        >
          <template #cell-timestamp="{ value }">
            <span :title="formatDate(value)">
              {{ formatDateRelativeWithWeekday(value) }}
            </span>
          </template>
        </BaseTable>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
