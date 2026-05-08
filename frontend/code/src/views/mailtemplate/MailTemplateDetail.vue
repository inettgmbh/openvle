<script setup>
import {
  mdiClipboardAlert,
  mdiClipboardCheck,
  mdiDelete,
  mdiLock,
  mdiLockOpen,
  mdiMailboxOutline,
  mdiPencil,
  mdiRefreshAuto,
  mdiRename,
  mdiTextBox,
  mdiWebBox,
} from '@mdi/js'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseMarkdown from '@/components/BaseMarkdown.vue'
import BaseTab from '@/components/BaseTab.vue'
import BaseTable from '@/components/BaseTable.vue'
import BaseTabs from '@/components/BaseTabs.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxDeleteModal from '@/components/CardBoxDeleteModal.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import ObjectMetadataDisplay from '@/components/ObjectMetadataDisplay.vue'
import PillTag from '@/components/PillTag.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import TableChangelogs from '@/components/Tables/TableChangelogs.vue'
import TablePermissions from '@/components/Tables/TablePermissions.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { useLookupStore } from '@/stores/lookup'
import {
  checkObjectPermissions,
  emailStatusFormatter,
  resolveFieldFromLookup,
  usePermissionRefs,
} from '@/utils/dataUtils'
import { htmlToMarkdown } from '@/utils/htmlUtils'
import { emailStatusIcon } from '@/utils/icons'
import { statusColorMail, statusColorMailTemplate } from '@/utils/objectColors'
import { usePaginationChild } from '@/utils/pagination'

const { t } = useI18n()
const lookupStore = useLookupStore()
const permissionRefs = usePermissionRefs()

const modals = {
  deleteMailTemplate: ref(false),
}
const dataLoading = ref(true)
const objectModel = 'MailTemplate'
const objToRemove = ref({})
const permissionsLoaded = ref(false)
const router = useRouter()
const route = useRoute()
const toast = useToast()
const mailTemplate = ref({})

lookupStore.fetchAll('languages')

const languageName = computed(() => {
  const lang = lookupStore.languages[mailTemplate.value.language]
  return typeof lang === 'object' ? lang.name : ''
})

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
      name: 'mails',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'createdAt',
      sortDirection: 'desc',
      fetchData: fetchMailTemplateMails,
    },
  ],
  fetchArgs: () => [route.params.id],
  modals,
  objToRemove,
})
/**/

async function fetchMailTemplate(mailTemplateId) {
  try {
    dataLoading.value = true

    await backend.mailTemplates.get(mailTemplateId).then(async (response) => {
      mailTemplate.value = response
      await resolveFieldFromLookup(mailTemplate.value, [
        { from: 'createdById', to: 'createdBy', keyspace: 'users' },
        { from: 'updatedById', to: 'updatedBy', keyspace: 'users' },
        { from: 'mail_action', to: 'mailAction', keyspace: 'mailActions' },
      ])
      mailTemplate.value.mailAction = mailTemplate.value.mailAction
        ? mailTemplate.value.mailAction
        : ''
    })
  } catch (error) {
    toast.warning(
      t('common.notFound', { entity: t('objectTypes.mailTemplate.singular') }),
    )
    router.push({ path: `/mail-templates`, replace: true })
  } finally {
    dataLoading.value = false
  }
}

async function fetchMailTemplateMails() {
  try {
    dataLoading.value = true

    await backend.mailTemplates
      .getMails(route.params.id, {
        page: childComponents.value.find(
          (component) => component.name === 'mails',
        )?.currentPage,
        limit: childComponents.value.find(
          (component) => component.name === 'mails',
        )?.perPage,
        sort_by: childComponents.value.find(
          (component) => component.name === 'mails',
        )?.sortColumnKey,
        sort_order: childComponents.value.find(
          (component) => component.name === 'mails',
        )?.sortDirection,
      })
      .then(async (response) => {
        mailTemplate.value.mails = response.items
        mailTemplate.value.mailsCount = response.pageDetails.totalCount
      })
  } catch (error) {
    toast.warning(
      t('common.loadErrorPlural', { entities: t('objectTypes.mail.plural') }),
    )
  } finally {
    dataLoading.value = false
  }
}

function showModal(modal, item) {
  if (Object.prototype.hasOwnProperty.call(modals, modal)) {
    modals[modal].value = true
  }
  if (item) {
    objToRemove.value = item
  }
}

async function deleteMailTemplate(mailTemplateId) {
  try {
    await backend.mailTemplates.delete(mailTemplateId)
    router.push({ path: `/mail-templates` })
    toast.success(
      t('common.deleteSuccess', {
        entity: t('objectTypes.mailTemplate.singular'),
      }),
    )
  } catch (error) {
    toast.error(
      t('common.deleteError', {
        entity: t('objectTypes.mailTemplate.singular'),
      }),
    )
  }
}

const mailTemplateEdit = (mailTemplateId) => {
  router.push({ path: `${mailTemplateId}/edit` })
}

async function handleProtectionChange() {
  try {
    await backend.mailTemplates
      .setProtection(
        mailTemplate.value.id,
        mailTemplate.value.protected ? false : true,
      )
      .then(() => {
        fetchMailTemplate(route.params.id)
      })
    toast.success(t('views.mailTemplates.detail.protectionChanged'))
  } catch (error) {
    toast.error(
      t('common.protectionChangeError', {
        entity: t('objectTypes.mailTemplate.singular'),
      }),
    )
  }
}

const pillType = computed(() => {
  if (mailTemplate.value.id) {
    if (mailTemplate.value.protected) {
      return 'danger'
    }
    return 'success'
  }
  return 'info'
})

const tooltipMailTemplateAction = computed(() => {
  if (mailTemplate.value.mailAction) {
    return t('views.mailTemplates.detail.tooltipInUse')
  }
  return t('views.mailTemplates.detail.tooltipNotInUse')
})

const contentMarkdown = computed(() => {
  const md = htmlToMarkdown(mailTemplate.value.contentHTML)
  // Wrap placeholders in backticks for display
  return md.replace(/\{\{\s*([^}]*?)\s*\}\}/g, '`{{ $1 }}`')
})

const tooltipMailTemplateLock = computed(() => {
  if (mailTemplate.value.protected) {
    return t('views.mailTemplates.detail.tooltipProtected')
  }
  return t('views.mailTemplates.detail.tooltipNotProtected')
})

onMounted(async () => {
  fetchMailTemplate(route.params.id)
  await checkObjectPermissions(
    'mail_templates',
    route.params.id,
    permissionRefs,
    [
      {
        key: 'canReadPermissions',
        objectType: 'object_permissions',
        objectPermission: 'read',
        objectPath: `/${route.params.id}`,
      },
      {
        key: 'canReadMails',
        objectType: 'mails',
        objectPermission: 'read',
        objectPath: '/*',
      },
      {
        key: 'canReadChangelogs',
        objectType: 'changelogs',
        objectPermission: 'read',
        objectPath: '/*',
      },
    ],
    ['canCreate', 'canEdit', 'canDelete'],
  )

  permissionsLoaded.value = true
})
</script>

<template>
  <CardBoxDeleteModal
    v-model="modals.deleteMailTemplate.value"
    :name="mailTemplate.name"
    :checkvalue="mailTemplate.name"
    @form-submitted="deleteMailTemplate(objToRemove.id)"
  />

  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiMailboxOutline"
        :title="mailTemplate.name ? mailTemplate.name : 'Loading...'"
        :object-model="$t('objectTypes.mailTemplate.singular')"
        main
        docs-path="/docs/usage/openvle/mails/templates/"
      >
        <BaseButtons type="justify-start lg:justify-end">
          <PillTag
            v-if="mailTemplate.mailAction != null"
            v-tooltip="{
              text: tooltipMailTemplateAction,
            }"
            :icon="
              mailTemplate.mailAction ? mdiClipboardCheck : mdiClipboardAlert
            "
            :color="statusColorMailTemplate(mailTemplate.mailAction)"
            disabled
          />

          <PillTag
            v-if="mailTemplate.name"
            v-tooltip="{
              text: tooltipMailTemplateLock,
            }"
            :disabled="!permissionRefs.canEdit"
            :color="pillType"
            :icon="mailTemplate.protected ? mdiLock : mdiLockOpen"
            :handle-click="handleProtectionChange"
          />

          <BaseButton
            v-if="permissionRefs.canEdit"
            target="_blank"
            :icon="mdiPencil"
            :label="$t('common.edit')"
            color="contrast"
            :disabled="mailTemplate.protected"
            rounded-full
            small
            @click="mailTemplateEdit(mailTemplate.id)"
          />

          <BaseButton
            v-if="permissionRefs.canDelete"
            target="_blank"
            :icon="mdiDelete"
            :label="$t('common.delete')"
            color="danger"
            :disabled="mailTemplate.protected"
            rounded-full
            small
            @click="showModal('deleteMailTemplate', mailTemplate)"
          />
        </BaseButtons>
      </SectionTitleLineWithButton>

      <CardBox>
        <BaseTabs v-if="permissionsLoaded" @tab-changed="handleTabChanged">
          <BaseTab
            id="template"
            :title="$t('objectTypes.mailTemplate.singular')"
          >
            <FormField
              :label="$t('common.name')"
              :help="$t('views.mailTemplates.form.nameHelp')"
            >
              <FormControl
                v-model="mailTemplate.name"
                :icon="mdiRename"
                disabled
              />
            </FormField>

            <FormField
              :label="$t('common.description')"
              :help="$t('views.mailTemplates.form.descriptionHelp')"
            >
              <FormControl
                v-model="mailTemplate.description"
                :icon="mdiTextBox"
                disabled
              />
            </FormField>

            <FormField>
              <FormField
                :label="$t('views.mails.columns.subject')"
                :help="$t('views.mailTemplates.form.subjectHelp')"
              >
                <FormControl
                  v-model="mailTemplate.subject"
                  :icon="mdiTextBox"
                  disabled
                />
              </FormField>

              <FormField
                :label="$t('views.mails.fields.replyTo')"
                :help="$t('views.mailTemplates.form.replyToHelp')"
              >
                <FormControl
                  v-model="mailTemplate.replyTo"
                  placeholder="replyto@example.com"
                  :icon="mdiTextBox"
                  disabled
                />
              </FormField>
            </FormField>

            <FormField>
              <FormField
                v-if="languageName"
                :label="$t('views.mailTemplates.form.language')"
                :help="$t('views.mailTemplates.form.languageHelp')"
              >
                <FormControl
                  :model-value="languageName"
                  :icon="mdiWebBox"
                  disabled
                />
              </FormField>

              <FormField
                v-if="mailTemplate.mailAction"
                :label="$t('views.mailTemplates.form.assignedAction')"
                :help="$t('views.mailTemplates.form.assignedActionHelp')"
              >
                <FormControl
                  v-model="mailTemplate.mailAction"
                  :icon="mdiRefreshAuto"
                  :link="`/mail-actions/${mailTemplate.mail_action}`"
                  disabled
                />
              </FormField>
            </FormField>

            <ObjectMetadataDisplay
              v-if="loadedTabs.has('template') && mailTemplate.id"
              :object="mailTemplate"
              :object-type="objectModel"
              :object-id="route.params.id"
              :can-edit="permissionRefs.canEdit"
              :tags-help="$t('views.mailTemplates.detail.tagsHelp')"
            />
          </BaseTab>

          <BaseTab id="content" :title="$t('common.content')">
            <BaseMarkdown :model-value="contentMarkdown" action="view" />
          </BaseTab>

          <BaseTab
            v-if="permissionRefs.canReadMails"
            id="mails"
            :title="$t('views.mailTemplates.detail.sentMails')"
          >
            <SectionTitleLineWithButton
              :icon="mdiMailboxOutline"
              :title="$t('views.mailTemplates.detail.sentMails')"
              :reload="fetchMailTemplateMails"
            />

            <BaseTable
              v-if="mailTemplate.mails"
              :current-page="
                childComponents.find((component) => component.name === 'mails')
                  ?.currentPage
              "
              :per-page="
                childComponents.find((component) => component.name === 'mails')
                  ?.perPage
              "
              :items-total="mailTemplate.mailsCount"
              :data="mailTemplate.mails"
              :sort-column-key="
                childComponents.find((component) => component.name === 'mails')
                  ?.sortColumnKey
              "
              :sort-direction="
                childComponents.find((component) => component.name === 'mails')
                  ?.sortDirection
              "
              :loading="dataLoading"
              object-model="mails"
              :buttons="['view']"
              :columns="[
                {
                  label: $t('views.mails.columns.subject'),
                  key: 'subject',
                },
                {
                  label: $t('views.mails.columns.recipient'),
                  key: 'toMail',
                },
                {
                  label: $t('common.status'),
                  key: 'sendStatus',
                  color: statusColorMail,
                  icon: (value) => emailStatusIcon(value),
                  formatter: (value) => emailStatusFormatter(value),
                },
              ]"
              @delete-object="handleDeleteObject"
              @sort-order-changed="handleSortOrderChanged"
              @pagination-changed="handlePaginationChanged"
            />
          </BaseTab>

          <BaseTab
            v-if="permissionRefs.canReadPermissions"
            id="permissions"
            :title="$t('objectTypes.permission.plural')"
          >
            <TablePermissions
              v-if="loadedTabs.has('permissions')"
              :object-id="route.params.id"
              :object-type="objectModel"
              :per-page="10"
            />
          </BaseTab>

          <BaseTab
            v-if="permissionRefs.canReadChangelogs"
            id="changelogs"
            :title="$t('objectTypes.changelog.plural')"
          >
            <TableChangelogs
              v-if="mailTemplate.id && loadedTabs.has('changelogs')"
              :object-id="route.params.id"
              :object-type="objectModel"
              :per-page="10"
            />
          </BaseTab>
        </BaseTabs>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
