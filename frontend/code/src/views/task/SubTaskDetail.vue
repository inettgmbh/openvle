<script setup>
import {
  mdiCodeNotEqualVariant,
  mdiConsole,
  mdiCounter,
  mdiDatabase,
  mdiFileTree,
  mdiNumeric,
  mdiProgressHelper,
  mdiReloadAlert,
  mdiRename,
  mdiWrench,
} from '@mdi/js'
import { computed, onMounted, ref, watch } from 'vue'
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
  resolveObjectTypeURL,
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
const objectModel = 'SubTask'
const task = ref([])
const relatedTasks = ref([])

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
  fetch: fetchRelatedTasks,
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

async function fetchSubTask() {
  try {
    dataLoading.value = true

    await backend.tasks.getSubTask(route.params.id).then(async (response) => {
      task.value = response
      task.value.object =
        task.value.object_id + ' (' + task.value.object_type + ')'
      const objTypeURL = resolveObjectTypeURL(task.value.object_type)
      if (objTypeURL == null) {
        task.value.objectLink = null
      } else {
        task.value.objectLink = `/${objTypeURL}/${task.value.object_id}`
      }
      await resolveFieldFromLookup(task.value, [
        { from: 'createdById', to: 'createdBy', keyspace: 'users' },
        { from: 'updatedById', to: 'updatedBy', keyspace: 'users' },
        { from: 'parent_task', to: 'parentTask', keyspace: 'tasks' },
      ])
      await fetchRelatedTasks()
    })
  } catch (error) {
    toast.warning(t('views.tasks.subTaskDetail.notFound'))
    router.push({ path: `/tasks`, replace: true })
  } finally {
    dataLoading.value = false
  }
}

async function fetchRelatedTasks() {
  if (!permissionRefs.canReadTasks || !task.value.parent_task) return

  try {
    dataLoading.value = true

    await backend.tasks
      .listSubTasksByTask(task.value.parent_task, {
        page: currentPage.value,
        limit: perPage.value,
        sort_by: sortColumnKey.value,
        sort_order: sortDirection.value,
        search_field: searchField.value,
        search_value: searchValue.value,
      })
      .then(async (response) => {
        relatedTasks.value = response.items.filter(
          (item) =>
            item.id !== task.value.id && item.id !== task.value.parent_task,
        )
        relatedTasks.value.count = relatedTasks.value.length
        await resolveFieldFromLookup(relatedTasks.value, [
          { from: 'createdById', to: 'createdBy', keyspace: 'users' },
          { from: 'updatedById', to: 'updatedBy', keyspace: 'users' },
        ])
      })
  } catch (error) {
    toast.warning(
      t('common.loadErrorPlural', { entities: t('objectTypes.task.plural') }),
    )
  } finally {
    dataLoading.value = false
  }
}

async function retryTask() {
  try {
    dataLoading.value = true

    await backend.tasks.retrySubTask(route.params.id).then(async () => {})
    toast.info(t('views.tasks.subTaskDetail.retrying'))
  } catch (error) {
    toast.error(
      `${t('views.tasks.subTaskDetail.retryError')}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  } finally {
    await fetchSubTask()
    dataLoading.value = false
  }
}

const retryButtonEnabled = computed(() => {
  if (task.value.action === 'mails_send') {
    return false
  }

  const taskCreatedAt = new Date(task.value.createdAt)
  const now = new Date()

  const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000)

  if (taskCreatedAt < oneDayAgo) return false

  return true
})

const retryButtonTooltip = computed(() => {
  if (task.value.action === 'mails_send') {
    return t('views.tasks.detail.mailTaskCannotRetry')
  }

  if (retryButtonEnabled.value) {
    return undefined
  }
  return t('views.tasks.detail.taskTooOld')
})

watch(
  () => route.params.id,
  async (newId, oldId) => {
    if (newId !== oldId) {
      await fetchSubTask()

      router.replace({
        query: {
          ...route.query,
          tab: 'infos',
        },
      })
    }
  },
  { immediate: true },
)

onMounted(async () => {
  await checkObjectPermissions(
    'sub_tasks',
    route.params.id,
    permissionRefs,
    [
      {
        key: 'canReadTasks',
        objectType: 'tasks',
        objectPermission: 'read',
        objectPath: '/*',
      },
    ],
    [],
  )

  permissionsLoaded.value = true
  fetchRelatedTasks()
})
</script>

<template>
  <TaskRetryModal
    v-if="task.name && relatedTasks"
    v-model="modals.retryTaskConfirmation.value"
    :scrollable="true"
    :name="task.name"
    :object="relatedTasks"
    @confirmed="retryTask()"
  />

  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiFileTree"
        :title="task.name ? task.name : 'Loading...'"
        :object-model="$t('objectTypes.subtask.singular')"
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
              :help="$t('views.tasks.subTaskDetail.nameHelp')"
            >
              <FormControl v-model="task.name" :icon="mdiRename" disabled />
            </FormField>

            <FormField>
              <FormField
                :label="$t('common.status')"
                :help="$t('views.tasks.subTaskDetail.statusHelp')"
              >
                <FormControl
                  v-model="task.status"
                  :icon="mdiProgressHelper"
                  disabled
                />
              </FormField>

              <FormField
                :label="$t('views.tasks.subTaskDetail.parentTask')"
                :help="$t('views.tasks.subTaskDetail.parentTaskHelp')"
              >
                <FormControl
                  v-model="task.parentTask"
                  :icon="mdiFileTree"
                  :link="`/tasks/${task.parent_task}`"
                  disabled
                />
              </FormField>
            </FormField>

            <FormField>
              <FormField
                :label="$t('common.object')"
                :help="$t('views.tasks.subTaskDetail.objectHelp')"
              >
                <FormControl
                  v-model="task.object"
                  :icon="mdiDatabase"
                  :link="task.objectLink"
                  disabled
                />
              </FormField>

              <FormField
                :label="$t('views.tasks.subTaskDetail.action')"
                :help="$t('views.tasks.subTaskDetail.actionHelp')"
              >
                <FormControl v-model="task.action" :icon="mdiWrench" disabled />
              </FormField>
            </FormField>

            <FormField>
              <FormField
                :label="$t('views.tasks.subTaskDetail.attempt')"
                :help="$t('views.tasks.subTaskDetail.attemptHelp')"
              >
                <FormControl
                  v-model="task.attempt"
                  :icon="mdiCounter"
                  disabled
                />
              </FormField>

              <FormField
                :label="$t('views.tasks.subTaskDetail.redisJobId')"
                :help="$t('views.tasks.subTaskDetail.redisJobIdHelp')"
              >
                <FormControl
                  v-model="task.job_id"
                  :icon="mdiNumeric"
                  disabled
                />
              </FormField>
            </FormField>

            <FormField>
              <FormField
                :label="$t('views.tasks.subTaskDetail.responseCode')"
                :help="$t('views.tasks.subTaskDetail.responseCodeHelp')"
              >
                <FormControl
                  v-model="task.response_code"
                  :icon="mdiCodeNotEqualVariant"
                  disabled
                />
              </FormField>

              <FormField
                :label="$t('views.tasks.subTaskDetail.responseMessage')"
                :help="$t('views.tasks.subTaskDetail.responseMessageHelp')"
              >
                <FormControl
                  v-model="task.response_message"
                  :icon="mdiConsole"
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
            v-if="permissionRefs.canReadTasks"
            id="related-tasks"
            :title="$t('views.tasks.subTaskDetail.relatedTasks')"
          >
            <SectionTitleLineWithButton
              :icon="mdiFileTree"
              :title="$t('views.tasks.subTaskDetail.relatedTasks')"
              :reload="fetchRelatedTasks"
            />

            <BaseTable
              v-if="relatedTasks"
              :current-page="currentPage"
              :per-page="perPage"
              :items-total="relatedTasks.count"
              :data="relatedTasks"
              :sort-column-key="sortColumnKey"
              :sort-direction="sortDirection"
              :loading="dataLoading"
              object-model="tasks/subtasks"
              :buttons="['view']"
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
