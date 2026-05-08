<script setup>
import {
  mdiCalendarOutline,
  mdiFileTree,
  mdiProgressHelper,
  mdiReloadAlert,
  mdiRename,
} from '@mdi/js'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseTab from '@/components/BaseTab.vue'
import BaseTable from '@/components/BaseTable.vue'
import BaseTabs from '@/components/BaseTabs.vue'
import CardBox from '@/components/CardBox.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import ObjectMetadataDisplay from '@/components/ObjectMetadataDisplay.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import { SearchOperators } from '@/components/Tables/searchOperators'
import TaskRetryModal from '@/components/TaskRetryModal.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import {
  checkObjectPermissions,
  resolveFieldFromLookup,
  statusTaskFilter,
  usePermissionRefs,
} from '@/utils/dataUtils'
import { taskStatusIcon } from '@/utils/icons'
import { statusColorTask } from '@/utils/objectColors'
import { usePaginationList } from '@/utils/pagination'
import { taskStatusTooltip } from '@/utils/tooltips'

const modals = {
  retryTaskConfirmation: ref(false),
}

const { t } = useI18n()
const permissionsLoaded = ref(false)
const permissionRefs = usePermissionRefs()
const router = useRouter()
const route = useRoute()
const toast = useToast()
const objectModel = 'Task'
const task = ref([])
const subtasks = ref([])

/* PAGINATION ONLY */
const dataLoading = ref(true)
const {
  currentPage,
  perPage,
  sortColumnKey,
  sortDirection,
  searchField,
  searchValue,
  handlePaginationChanged,
  handleSortOrderChanged,
  handleSearch,
} = usePaginationList({
  initialPage: 1,
  initialPerPage: 10,
  initialSortColumn: 'createdAt',
  initialSortOrder: 'desc',
  initialSearchField: null,
  initialSearchValue: null,
  fetch: fetchSubTasks,
  useReplace: true,
  syncQuery: true,
})
/**/

const searchBarFields = [
  { preset: 'name', operators: SearchOperators.CONTAINS_ONLY },
  {
    preset: 'status',
    operators: SearchOperators.EQUALS_ONLY_ONLY,
    options: statusTaskFilter(),
  },
  { preset: 'taskAction', operators: SearchOperators.CONTAINS_ONLY },
  { preset: 'taskAttempt', operators: SearchOperators.EQUALS_ONLY_ONLY },
  { preset: 'taskJobId', operators: SearchOperators.CONTAINS_ONLY },
  { preset: 'taskResponseCode', operators: SearchOperators.CONTAINS_ONLY },
  { preset: 'taskResponseMessage', operators: SearchOperators.CONTAINS_ONLY },
  { preset: 'createdById', operators: SearchOperators.EQUALS_ONLY_ONLY },
  { preset: 'updatedById', operators: SearchOperators.EQUALS_ONLY_ONLY },
]

async function fetchTask() {
  try {
    dataLoading.value = true

    await backend.tasks.get(route.params.id).then(async (response) => {
      task.value = response
      fetchSubTasks()
      await resolveFieldFromLookup(task.value, [
        { from: 'createdById', to: 'createdBy', keyspace: 'users' },
        { from: 'updatedById', to: 'updatedBy', keyspace: 'users' },
        { from: 'event_id', to: 'event', keyspace: 'events' },
      ])
      if (task.value.event_id) {
        task.value.eventURL = `/events/${task.value.event_id}`
      } else {
        task.value.eventURL = null
      }
    })
  } catch (error) {
    toast.warning(
      t('common.notFound', { entity: t('objectTypes.task.singular') }),
    )
    router.push({ path: `/tasks`, replace: true })
  } finally {
    dataLoading.value = false
  }
}

async function fetchSubTasks() {
  try {
    dataLoading.value = true

    await backend.tasks
      .listSubTasksByTask(route.params.id, {
        page: currentPage.value,
        limit: perPage.value,
        sort_by: sortColumnKey.value,
        sort_order: sortDirection.value,
        search_field: searchField.value,
        search_value: searchValue.value,
      })
      .then(async (response) => {
        subtasks.value = response.items
        subtasks.value.count = response.pageDetails.totalCount
        await resolveFieldFromLookup(subtasks.value, [
          { from: 'createdById', to: 'createdBy', keyspace: 'users' },
          { from: 'updatedById', to: 'updatedBy', keyspace: 'users' },
        ])
      })
  } catch (error) {
    toast.warning(
      t('common.loadErrorPlural', {
        entities: t('objectTypes.subtask.plural'),
      }),
    )
  } finally {
    dataLoading.value = false
  }
}

async function retrySubTask(subtasks) {
  try {
    dataLoading.value = true

    for (const subtask of subtasks) {
      await backend.tasks.retrySubTask(subtask.id).then(async () => {})
      toast.info(
        t('views.tasks.detail.subTaskRetrying', { name: subtask.name }),
      )
    }
  } catch (error) {
    toast.error(
      `${t('views.tasks.detail.subTaskRetryError')}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  } finally {
    await fetchTask()
    dataLoading.value = false
  }
}

const retryButtonEnabled = computed(() => {
  if (task.value.name === 'Send mail') {
    return false
  }

  const taskCreatedAt = new Date(task.value.createdAt)
  const now = new Date()

  const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000)

  if (taskCreatedAt < oneDayAgo) return false

  return true
})

const retryButtonTooltip = computed(() => {
  if (task.value.name === 'Send mail') {
    return t('views.tasks.detail.mailTaskCannotRetry')
  }

  if (retryButtonEnabled.value) {
    return undefined
  }
  return t('views.tasks.detail.taskTooOld')
})

onMounted(async () => {
  await checkObjectPermissions(
    'tasks',
    route.params.id,
    permissionRefs,
    [
      {
        key: 'canReadSubTasks',
        objectType: 'sub_tasks',
        objectPermission: 'read',
        objectPath: '/*',
      },
    ],
    [],
  )

  permissionsLoaded.value = true
})

fetchTask()
</script>

<template>
  <TaskRetryModal
    v-if="task.name && subtasks"
    v-model="modals.retryTaskConfirmation.value"
    :scrollable="true"
    :name="task.name"
    :object="subtasks"
    @confirmed="retrySubTask(subtasks.filter((s) => s.status === 'failed'))"
  />

  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiFileTree"
        :title="task.name ? task.name : 'Loading...'"
        :object-model="$t('objectTypes.task.singular')"
        main
        docs-path="/docs/usage/openvle/system/tasks/"
      >
        <BaseButton
          v-if="task.status && task.status === 'failed'"
          v-tooltip="retryButtonTooltip"
          :icon="mdiReloadAlert"
          :disabled="!retryButtonEnabled"
          :label="$t('common.retry')"
          color="danger"
          rounded-full
          small
          @click="modals.retryTaskConfirmation.value = true"
        />
      </SectionTitleLineWithButton>

      <CardBox>
        <BaseTabs v-if="permissionsLoaded">
          <BaseTab id="infos" :title="$t('common.infos')">
            <FormField
              :label="$t('common.name')"
              :help="$t('views.tasks.detail.nameHelp')"
            >
              <FormControl v-model="task.name" :icon="mdiRename" disabled />
            </FormField>

            <FormField>
              <FormField
                :label="$t('common.status')"
                :help="$t('views.tasks.detail.statusHelp')"
              >
                <FormControl
                  v-model="task.status"
                  :icon="mdiProgressHelper"
                  disabled
                />
              </FormField>

              <FormField
                :label="$t('views.tasks.detail.event')"
                :help="$t('views.tasks.detail.eventHelp')"
              >
                <FormControl
                  v-model="task.event"
                  :icon="mdiCalendarOutline"
                  :link="task.eventURL"
                  disabled
                />
              </FormField>
            </FormField>

            <ObjectMetadataDisplay
              :object="task"
              :object-type="objectModel"
              :object-id="route.params.id"
              :show-tags="false"
            />
          </BaseTab>

          <BaseTab
            id="tasks/subtasks"
            :title="$t('views.tasks.detail.subTasks')"
          >
            <SectionTitleLineWithButton
              :icon="mdiFileTree"
              :title="$t('views.tasks.detail.subTasks')"
              :reload="fetchSubTasks"
            />

            <BaseTable
              v-if="subtasks"
              :current-page="currentPage"
              :per-page="perPage"
              :items-total="subtasks.count"
              :data="subtasks"
              :sort-column-key="sortColumnKey"
              :sort-direction="sortDirection"
              :loading="dataLoading"
              object-model="tasks/subtasks"
              :buttons="permissionRefs.canReadSubTasks ? ['view'] : []"
              :search-bar-fields="searchBarFields"
              :search-bar-max-filters="1"
              :columns="[
                {
                  label: $t('common.name'),
                  key: 'name',
                },
                {
                  label: $t('common.status'),
                  key: 'status',
                  color: statusColorTask,
                  icon: (value) => taskStatusIcon(value),
                  tooltip: (value) => taskStatusTooltip(value),
                  filters: statusTaskFilter(),
                  formatter: ['', ''],
                },
                {
                  label: $t('views.tasks.columns.triggeredBy'),
                  key: 'createdBy',
                  sortKey: 'createdById',
                },
              ]"
              @search-triggered="handleSearch"
              @sort-order-changed="handleSortOrderChanged"
              @pagination-changed="handlePaginationChanged"
            />
          </BaseTab>
        </BaseTabs>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
