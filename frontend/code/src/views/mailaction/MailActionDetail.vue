<script setup>
import {
  mdiAlertCircleOutline,
  mdiClipboardAlert,
  mdiClipboardCheck,
  mdiEmailSync,
  mdiKey,
  mdiMailboxOutline,
  mdiRelationOneToMany,
  mdiRename,
  mdiTextBox,
} from '@mdi/js'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseTab from '@/components/BaseTab.vue'
import BaseTable from '@/components/BaseTable.vue'
import BaseTabs from '@/components/BaseTabs.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxDeleteRelationModal from '@/components/CardBoxDeleteRelationModal.vue'
import CardBoxModal from '@/components/CardBoxModal.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import ObjectMetadataDisplay from '@/components/ObjectMetadataDisplay.vue'
import PillTag from '@/components/PillTag.vue'
import SearchControl from '@/components/SearchControl.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import { useMailTemplatePlaceholders } from '@/composables/useMailTemplatePlaceholders'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { useLookupStore } from '@/stores/lookup'
import {
  checkObjectPermissions,
  keyToFlag,
  usePermissionRefs,
} from '@/utils/dataUtils'
import { statusColorMailTemplate } from '@/utils/objectColors'
import { usePaginationChild } from '@/utils/pagination'

const { t } = useI18n()
const lookupStore = useLookupStore()
const permissionRefs = usePermissionRefs()

const modals = {
  assignAction: ref(false),
  deleteMailtemplates: ref(false),
}
const dataLoading = ref(true)
const objectModel = 'MailActions'
const objToAdd = ref([])
const objToRemove = ref({})
const permissionsLoaded = ref(false)
const router = useRouter()
const route = useRoute()
const searchControlUserRef = ref(null)
const toast = useToast()
const mailAction = ref({})
const selectedTemplateContent = ref('')

lookupStore.fetchAll('languages')

const languageNameMap = computed(() => {
  const map = {}
  for (const [id, val] of Object.entries(lookupStore.languages)) {
    if (typeof val === 'object') map[id] = val.name
  }
  return map
})

const languageFlagMap = computed(() => {
  const map = {}
  for (const [id, val] of Object.entries(lookupStore.languages)) {
    if (typeof val === 'object') map[id] = keyToFlag(val.key)
  }
  return map
})

// Placeholder validation for assigning mail templates
const actionsForValidation = computed(() => {
  if (!mailAction.value?.id) return []
  return [{ value: mailAction.value.id, slug: mailAction.value.slug }]
})

const selectedActionIdRef = computed(() => mailAction.value?.id || '')
const contentRef = computed(() => selectedTemplateContent.value)

const { validationError, canSubmit } = useMailTemplatePlaceholders({
  content: contentRef,
  actions: actionsForValidation,
  selectedActionId: selectedActionIdRef,
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
      name: 'mailtemplates',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'name',
      sortDirection: 'asc',
      fetchData: fetchMailActionTemplates,
    },
  ],
  fetchArgs: () => [route.params.id],
  modals,
  objToRemove,
})
/**/

async function assignAction(mailTemplateId) {
  try {
    await backend.mailTemplates.assignMailAction(
      mailTemplateId,
      route.params.id,
    )
    fetchMailActionTemplates()
    toast.success(
      t('common.addSuccess', {
        entity: t('objectTypes.mailTemplate.singular'),
      }),
    )
  } catch (error) {
    toast.error(
      `${t('common.addError', { entity: t('objectTypes.mailTemplate.singular') })}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  }
}

async function unassignAction(mailTemplateId) {
  try {
    await backend.mailTemplates.unassignMailAction(mailTemplateId)
    fetchMailActionTemplates()
    toast.success(
      t('common.removeSuccess', {
        entity: t('objectTypes.mailTemplate.singular'),
      }),
    )
  } catch (error) {
    toast.error(
      `${t('common.removeError', { entity: t('objectTypes.mailTemplate.singular') })}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  }
}

async function fetchMailAction(mailActionId) {
  try {
    dataLoading.value = true

    await backend.mailActions.get(mailActionId).then(async (response) => {
      mailAction.value = response
      fetchMailActionTemplates()
    })
  } catch (error) {
    toast.warning(
      t('common.notFound', { entity: t('objectTypes.mailAction.singular') }),
    )
    router.push({ path: `/mail-actions`, replace: true })
  } finally {
    dataLoading.value = false
  }
}

async function fetchMailActionTemplates() {
  try {
    dataLoading.value = true

    await backend.mailTemplates
      .list({
        page: childComponents.value.find(
          (component) => component.name === 'mailtemplates',
        )?.currentPage,
        limit: childComponents.value.find(
          (component) => component.name === 'mailtemplates',
        )?.perPage,
        sort_by: childComponents.value.find(
          (component) => component.name === 'mailtemplates',
        )?.sortColumnKey,
        sort_order: childComponents.value.find(
          (component) => component.name === 'mailtemplates',
        )?.sortDirection,
        search_field: 'mail_action',
        search_value: route.params.id,
      })
      .then(async (response) => {
        mailAction.value.mailtemplates = response.items
        mailAction.value.mailtemplatesCount = response.pageDetails.totalCount
      })
  } catch (error) {
    toast.warning(
      t('common.loadErrorPlural', {
        entities: t('objectTypes.mailTemplate.plural'),
      }),
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

const tooltipMailAction = computed(() => {
  if (mailAction.value.mailtemplatesCount) {
    return t('views.mailActions.detail.tooltipHasTemplate')
  }
  return t('views.mailActions.detail.tooltipNoTemplate')
})

const resetAssignForm = () => {
  objToAdd.value.mailTemplateId = ''
  selectedTemplateContent.value = ''
  searchControlUserRef.value?.setInitialDisplay('')
  searchControlUserRef.value?.setSelectedId('')
}

onMounted(async () => {
  fetchMailAction(route.params.id)
  await checkObjectPermissions(
    'mail_templates',
    route.params.id,
    permissionRefs,
    [
      {
        key: 'canReadMailTemplates',
        objectType: 'mail_templates',
        objectPermission: 'read',
        objectPath: '/*',
      },
    ],
    [],
  )

  permissionsLoaded.value = true
})

// Watch for template selection and fetch content for validation
watch(
  () => objToAdd.value.mailTemplateId,
  async (newId) => {
    if (newId) {
      try {
        const template = await backend.mailTemplates.get(newId)
        selectedTemplateContent.value = template.contentHTML || ''
      } catch {
        selectedTemplateContent.value = ''
      }
    } else {
      selectedTemplateContent.value = ''
    }
  },
)
</script>

<template>
  <!-- Modal: Assing e-mail action to e-mail template -->
  <CardBoxModal
    v-model="modals.assignAction.value"
    form
    :title="$t('views.mailActions.detail.assignModalTitle')"
    button="success"
    has-cancel
    has-search
    :button-label="$t('common.assign')"
    :disabled="!canSubmit"
    @cancel="resetAssignForm()"
    @form-submitted="assignAction(objToAdd.mailTemplateId)"
  >
    <FormField :label="$t('views.mailActions.detail.selectTemplate')">
      <SearchControl
        v-model="objToAdd.mailTemplateId"
        :fetch-data="backend.mailTemplates.search"
        :icon="mdiMailboxOutline"
        required
        @set-ref="
          (ref) => {
            searchControlUserRef = ref
          }
        "
      />
    </FormField>

    <NotificationBar
      v-if="validationError"
      color="danger"
      :dismissable="false"
      :icon="mdiAlertCircleOutline"
    >
      {{ $t('views.mailActions.detail.invalidVariablesWarning') }}
    </NotificationBar>
  </CardBoxModal>

  <!-- Modal: Unassign e-mail action from e-mail template -->
  <CardBoxDeleteRelationModal
    v-model="modals.deleteMailtemplates.value"
    :parent-object="mailAction.name"
    :related-object="objToRemove.name"
    :checkvalue="$t('common.confirmation')"
    @form-submitted="unassignAction(objToRemove.id)"
  />

  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiEmailSync"
        :title="mailAction.name ? mailAction.name : 'Loading...'"
        :object-model="$t('views.mailActions.detail.objectModel')"
        main
        docs-path="/docs/usage/openvle/mails/templates/"
      >
        <BaseButtons type="justify-start lg:justify-end">
          <PillTag
            v-if="mailAction.id"
            v-tooltip="{
              text: tooltipMailAction,
            }"
            :icon="
              mailAction.mailtemplatesCount
                ? mdiClipboardCheck
                : mdiClipboardAlert
            "
            :color="statusColorMailTemplate(mailAction.mailtemplatesCount)"
            disabled
          />
        </BaseButtons>
      </SectionTitleLineWithButton>

      <CardBox>
        <BaseTabs v-if="permissionsLoaded" @tab-changed="handleTabChanged">
          <BaseTab
            id="mail-action"
            :title="$t('views.mailActions.detail.objectModel')"
          >
            <FormField
              :label="$t('common.name')"
              :help="$t('views.mailActions.detail.fields.nameHelp')"
            >
              <FormControl
                v-model="mailAction.name"
                :icon="mdiRename"
                disabled
              />
            </FormField>

            <FormField
              :label="$t('common.description')"
              :help="$t('views.mailActions.detail.fields.descriptionHelp')"
            >
              <FormControl
                v-model="mailAction.description"
                :icon="mdiTextBox"
                type="textarea"
                disabled
              />
            </FormField>

            <FormField
              label="Slug"
              :help="$t('views.mailActions.detail.fields.slugHelp')"
            >
              <FormControl v-model="mailAction.slug" :icon="mdiKey" disabled />
            </FormField>

            <ObjectMetadataDisplay
              v-if="loadedTabs.has('mail-action')"
              :object="mailAction"
              :object-type="objectModel"
              :object-id="route.params.id"
              :show-created="false"
              :show-tags="false"
              :show-updated="false"
            />
          </BaseTab>

          <BaseTab
            v-if="permissionRefs.canReadMailTemplates"
            id="mailtemplates"
            :title="$t('objectTypes.mailTemplate.plural')"
          >
            <SectionTitleLineWithButton
              :icon="mdiMailboxOutline"
              :title="$t('objectTypes.mailTemplate.plural')"
              :reload="fetchMailActionTemplates"
            >
              <BaseButton
                target="_blank"
                :icon="mdiRelationOneToMany"
                :label="$t('common.assign')"
                color="info"
                rounded-full
                small
                @click="showModal('assignAction', mailAction.id)"
              />
            </SectionTitleLineWithButton>

            <BaseTable
              v-if="mailAction.mailtemplates"
              :current-page="
                childComponents.find(
                  (component) => component.name === 'mailtemplates',
                )?.currentPage
              "
              :per-page="
                childComponents.find(
                  (component) => component.name === 'mailtemplates',
                )?.perPage
              "
              :items-total="mailAction.mailtemplatesCount"
              :data="mailAction.mailtemplates"
              :sort-column-key="
                childComponents.find(
                  (component) => component.name === 'mailtemplates',
                )?.sortColumnKey
              "
              :sort-direction="
                childComponents.find(
                  (component) => component.name === 'mailtemplates',
                )?.sortDirection
              "
              :loading="dataLoading"
              object-model="mailtemplates"
              :buttons="['view', 'delete']"
              :columns="[
                { label: $t('common.name'), key: 'name' },
                {
                  label: $t('common.description'),
                  key: 'description',
                },
                {
                  label: $t('views.mailTemplates.form.language'),
                  key: 'language',
                  color: () => 'info',
                  formatter: (value) => languageFlagMap[value] || '',
                  tooltip: (value) => languageNameMap[value] || '',
                  width: '100px',
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
