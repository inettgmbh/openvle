<script setup>
import { mdiFileTree, mdiMailboxOutline, mdiRename, mdiTextBox } from '@mdi/js'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseMarkdown from '@/components/BaseMarkdown.vue'
import BaseTab from '@/components/BaseTab.vue'
import BaseTable from '@/components/BaseTable.vue'
import BaseTabs from '@/components/BaseTabs.vue'
import CardBox from '@/components/CardBox.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import ObjectMetadataDisplay from '@/components/ObjectMetadataDisplay.vue'
import PillTag from '@/components/PillTag.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import {
  checkObjectPermissions,
  emailStatusFormatter,
  parseEmailContent,
  resolveFieldFromLookup,
  usePermissionRefs,
} from '@/utils/dataUtils'
import { htmlToMarkdown } from '@/utils/htmlUtils'
import {
  emailStatusIcon,
  mailCreateTypeIcon,
  taskStatusIcon,
} from '@/utils/icons'
import { statusColorMail, statusColorTask } from '@/utils/objectColors'
import { usePaginationChild } from '@/utils/pagination'
import {
  emailSendStatusTooltip,
  mailCreateTypeTooltip,
  taskStatusTooltip,
} from '@/utils/tooltips'

const permissionRefs = usePermissionRefs()

const modals = {}

const { t } = useI18n()
const dataLoading = ref(true)
const objToRemove = ref({})
const permissionsLoaded = ref(false)
const route = useRoute()
const router = useRouter()
const toast = useToast()
const mail = ref({})

/* PAGINATION ONLY */
const {
  childComponents,
  loadedTabs,
  handlePaginationChanged,
  handleSortOrderChanged,
  handleDeleteObject,
  handleTabChanged,
} = usePaginationChild({
  children: [
    {
      name: 'tasks/subtasks',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'createdAt',
      sortDirection: 'desc',
      fetchData: fetchMailTasks,
    },
  ],
  fetchArgs: () => [route.params.id],
  modals,
  objToRemove,
})
/**/

async function fetchMail(id) {
  try {
    dataLoading.value = true

    await backend.mails.get(id).then(async (response) => {
      mail.value = response
      await resolveFieldFromLookup(mail.value, [
        { from: 'createdById', to: 'createdBy', keyspace: 'users' },
        { from: 'templateId', to: 'template', keyspace: 'mail_templates' },
      ])
    })
  } catch (error) {
    toast.warning(t('views.mails.detail.notFound'))
    router.push({ path: `/mails`, replace: true })
  } finally {
    dataLoading.value = false
  }
}

async function fetchMailTasks() {
  try {
    dataLoading.value = true

    await backend.tasks
      .listSubTasks({
        page: childComponents.value.find(
          (component) => component.name === 'tasks/subtasks',
        )?.currentPage,
        limit: childComponents.value.find(
          (component) => component.name === 'tasks/subtasks',
        )?.perPage,
        sort_by: childComponents.value.find(
          (component) => component.name === 'tasks/subtasks',
        )?.sortColumnKey,
        sort_order: childComponents.value.find(
          (component) => component.name === 'tasks/subtasks',
        )?.sortDirection,
        search_field: 'object_id',
        search_value: route.params.id,
      })
      .then(async (response) => {
        mail.value.tasks = response.items
        mail.value.tasksCount = response.pageDetails.totalCount
        await resolveFieldFromLookup(mail.value.tasks, [
          { from: 'createdById', to: 'createdBy', keyspace: 'users' },
        ])
      })
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', { entities: t('objectTypes.task.plural') }),
    )
  } finally {
    dataLoading.value = false
  }
}

async function pillClicked() {
  router.push({ path: `/events/${mail.value.event}` })
}

const parsedContentMarkdown = computed(() => {
  const raw = mail.value?.content_rendered
  if (!raw) return ''
  return htmlToMarkdown(parseEmailContent(raw))
})

onMounted(async () => {
  fetchMail(route.params.id)
  await checkObjectPermissions(
    'mails',
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
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiMailboxOutline"
        :title="$t('views.mails.detail.title')"
        main
        docs-path="/docs/usage/openvle/mails/sent/"
      >
        <PillTag
          v-tooltip="mailCreateTypeTooltip(mail.event)"
          :color="mail.event ? 'success' : 'info'"
          :disabled="mail.event ? false : true"
          :label="
            mail.event
              ? $t('views.mails.detail.event')
              : $t('views.mails.detail.manual')
          "
          :icon="mailCreateTypeIcon(mail.event)"
          :handle-click="pillClicked"
        />

        <PillTag
          v-if="mail.id"
          v-tooltip="emailSendStatusTooltip(mail.sendStatus)"
          :label="emailStatusFormatter(mail.sendStatus)"
          :color="statusColorMail(mail.sendStatus)"
          :icon="emailStatusIcon(mail.sendStatus)"
          :disabled="true"
        />
      </SectionTitleLineWithButton>

      <CardBox>
        <BaseTabs v-if="permissionsLoaded" @tab-changed="handleTabChanged">
          <BaseTab id="email" :title="$t('objectTypes.mail.singular')">
            <FormField>
              <FormField
                :label="$t('views.mails.detail.fields.template')"
                :help="$t('views.mails.detail.fields.templateHelp')"
              >
                <FormControl
                  v-model="mail.template"
                  :icon="mdiRename"
                  :link="`/mail-templates/${mail.templateId}`"
                  disabled
                />
              </FormField>

              <FormField
                :label="$t('views.mails.columns.recipient')"
                :help="$t('views.mails.detail.fields.recipientHelp')"
              >
                <FormControl
                  v-model="mail.toMail"
                  :icon="mdiTextBox"
                  :link="mail.user_id ? `/users/${mail.user_id}` : null"
                  disabled
                />
              </FormField>
            </FormField>

            <FormField>
              <FormField
                :label="$t('views.mails.columns.subject')"
                :help="$t('views.mails.detail.fields.subjectHelp')"
              >
                <FormControl
                  v-model="mail.subject"
                  :icon="mdiTextBox"
                  disabled
                />
              </FormField>

              <FormField
                :label="$t('views.mails.fields.replyTo')"
                :help="$t('views.mails.detail.fields.replyToHelp')"
              >
                <FormControl
                  v-model="mail.replyTo"
                  placeholder="replyto@example.com"
                  :icon="mdiTextBox"
                  disabled
                />
              </FormField>
            </FormField>

            <FormField>
              <FormField
                :label="$t('views.mails.fields.fromName')"
                :help="$t('views.mails.detail.fields.fromNameHelp')"
              >
                <FormControl
                  v-model="mail.fromName"
                  placeholder="Max Mustermann"
                  :icon="mdiTextBox"
                  disabled
                />
              </FormField>

              <FormField
                :label="$t('views.mails.fields.fromMail')"
                :help="$t('views.mails.detail.fields.fromMailHelp')"
              >
                <FormControl
                  v-model="mail.fromMail"
                  placeholder="beispiel@example.com"
                  :icon="mdiTextBox"
                  disabled
                />
              </FormField>
            </FormField>

            <ObjectMetadataDisplay
              :object="mail"
              object-type="mails"
              :object-id="route.params.id"
              :show-tags="false"
              :show-updated="false"
            />
          </BaseTab>

          <BaseTab id="content" :title="$t('common.content')">
            <BaseMarkdown :model-value="parsedContentMarkdown" action="view" />
          </BaseTab>

          <BaseTab
            v-if="permissionRefs.canReadSubTasks"
            id="tasks/subtasks"
            :title="$t('objectTypes.task.plural')"
          >
            <SectionTitleLineWithButton
              :icon="mdiFileTree"
              :title="$t('objectTypes.task.plural')"
              :reload="fetchMailTasks"
            >
            </SectionTitleLineWithButton>

            <BaseTable
              :current-page="
                childComponents.find(
                  (component) => component.name === 'tasks/subtasks',
                )?.currentPage
              "
              :per-page="
                childComponents.find(
                  (component) => component.name === 'tasks/subtasks',
                )?.perPage
              "
              :items-total="mail.tasksCount"
              :data="mail.tasks"
              :sort-column-key="
                childComponents.find(
                  (component) => component.name === 'tasks/subtasks',
                )?.sortColumnKey
              "
              :sort-direction="
                childComponents.find(
                  (component) => component.name === 'tasks/subtasks',
                )?.sortDirection
              "
              :loading="dataLoading"
              object-model="tasks/subtasks"
              :buttons="['view']"
              :columns="[
                { label: $t('common.name'), key: 'name' },
                {
                  label: $t('common.status'),
                  key: 'status',
                  color: statusColorTask,
                  icon: (value) => taskStatusIcon(value),
                  tooltip: (value) => taskStatusTooltip(value),
                  formatter: ['', ''],
                },
                {
                  label: $t('views.mails.detail.columns.triggeredBy'),
                  key: 'createdBy',
                  sortKey: 'createdById',
                },
              ]"
              @delete-object="handleDeleteObject"
              @sort-order-changed="handleSortOrderChanged"
              @pagination-changed="handlePaginationChanged"
            />
          </BaseTab>
        </BaseTabs>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
