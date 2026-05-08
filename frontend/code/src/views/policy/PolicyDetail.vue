<script setup>
import {
  mdiAccountBoxOutline,
  mdiDelete,
  mdiFileSign,
  mdiPencil,
  mdiRename,
  mdiTextBox,
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
import CardBoxModal from '@/components/CardBoxModal.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import ObjectMetadataDisplay from '@/components/ObjectMetadataDisplay.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import TableChangelogs from '@/components/Tables/TableChangelogs.vue'
import TablePermissions from '@/components/Tables/TablePermissions.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import {
  checkObjectPermissions,
  resolveFieldFromLookup,
  usePermissionRefs,
} from '@/utils/dataUtils'
import { policyStatusIcon } from '@/utils/icons'
import { usePaginationChild } from '@/utils/pagination'

const { t } = useI18n()
const permissionRefs = usePermissionRefs()

const modals = {
  deletePolicy: ref(false),
  disablePolicy: ref(false),
  enablePolicy: ref(false),
}
const objToRemove = ref({})
const dataLoading = ref(true)
const objectModel = 'Policy'
const permissionsLoaded = ref(false)
const policy = ref([])
const router = useRouter()
const route = useRoute()
const toast = useToast()

/* PAGINATION ONLY */
const {
  childComponents,
  loadedTabs,
  handlePaginationChanged,
  handleSortOrderChanged,
  handleTabChanged,
} = usePaginationChild({
  children: [
    {
      name: 'users',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'createdAt',
      sortDirection: 'desc',
      fetchData: fetchPolicyUsers,
    },
  ],
  fetchArgs: () => [route.params.id],
  modals,
  objToRemove,
})
/**/

async function deletePolicy(policyId) {
  try {
    await backend.policies.delete(policyId)
    router.push({ path: `/policies` })
    toast.success(
      t('common.deleteSuccess', { entity: t('objectTypes.policy.singular') }),
    )
  } catch (error) {
    toast.error(
      t('common.deleteError', { entity: t('objectTypes.policy.singular') }),
    )
  }
}

async function disablePolicy(policyId) {
  try {
    await backend.policies.disable(policyId)
    fetchPolicy(route.params.id)
    toast.success(
      t('common.disableSuccess', { entity: t('objectTypes.policy.singular') }),
    )
  } catch (error) {
    toast.error(
      t('common.disableError', { entity: t('objectTypes.policy.singular') }),
    )
  }
}

async function enablePolicy(policyId) {
  try {
    await backend.policies.enable(policyId)
    fetchPolicy(route.params.id)
    toast.success(
      t('common.enableSuccess', { entity: t('objectTypes.policy.singular') }),
    )
  } catch (error) {
    toast.error(
      t('common.enableError', { entity: t('objectTypes.policy.singular') }),
    )
  }
}

async function fetchPolicy(policyId) {
  try {
    dataLoading.value = true

    await backend.policies.get(policyId).then(async (response) => {
      policy.value = response
      fetchPolicyUsers() // load on mount to ensure action checks run properly
      await resolveFieldFromLookup(policy.value, [
        { from: 'createdById', to: 'createdBy', keyspace: 'users' },
        { from: 'updatedById', to: 'updatedBy', keyspace: 'users' },
      ])
    })
  } catch (error) {
    toast.warning(
      t('common.notFound', { entity: t('objectTypes.policy.singular') }),
    )
    router.push({ path: `/policies`, replace: true })
  } finally {
    dataLoading.value = false
  }
}

async function fetchPolicyUsers() {
  try {
    dataLoading.value = true

    await backend.policies
      .getUsers(route.params.id, {
        page: childComponents.value.find(
          (component) => component.name === 'users',
        )?.currentPage,
        limit: childComponents.value.find(
          (component) => component.name === 'users',
        )?.perPage,
        sort_by: childComponents.value.find(
          (component) => component.name === 'users',
        )?.sortColumnKey,
        sort_order: childComponents.value.find(
          (component) => component.name === 'users',
        )?.sortDirection,
      })
      .then(async (response) => {
        policy.value.users = response.items
        policy.value.usersCount = response.pageDetails.totalCount
        await resolveFieldFromLookup(policy.value.users, [
          { from: 'user_id', to: 'username', keyspace: 'users' },
        ])
      })
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', { entities: t('objectTypes.user.plural') }),
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

const policyEdit = (policyId) => {
  router.push({ path: `${policyId}/edit` })
}

const pillType = computed(() => {
  if (policy.value.id) {
    if (policy.value.active) {
      return 'success'
    }
    return 'danger'
  }
  return 'info'
})

const policyModifyable = computed(() => {
  // Policy still loading, so edit disabled
  if (!policy.value.id) {
    return true
  }
  // Policy is active, so edit disabled
  if (policy.value.active) {
    return true
  }
  // Policy already has users, so edit disabled
  if (policy.value.users && policy.value.users.length !== 0) {
    return true
  }
  return false
})

const policyChangable = computed(() => {
  // Policy still loading, so changable disabled
  if (!policy.value.id) {
    return true
  }
  // Policy has no users, so changable enabled
  if (policy.value.users && policy.value.users.length === 0) {
    return false
  }
  if (policy.value.active) {
    return false
  }
  if (!policy.value.active) {
    return true
  }
  return true
})

onMounted(async () => {
  fetchPolicy(route.params.id)
  await checkObjectPermissions('policies', route.params.id, permissionRefs, [
    {
      key: 'canReadPermissions',
      objectType: 'object_permissions',
      objectPermission: 'read',
      objectPath: `/${route.params.id}`,
    },
    {
      key: 'canReadChangelogs',
      objectType: 'changelogs',
      objectPermission: 'read',
      objectPath: '/*',
    },
  ])

  permissionsLoaded.value = true
})
</script>

<template>
  <!-- Delete Policy -->
  <CardBoxDeleteModal
    v-model="modals.deletePolicy.value"
    :name="objToRemove.name"
    :checkvalue="objToRemove.name"
    @form-submitted="deletePolicy(objToRemove.id)"
  />

  <!-- Enable Policy -->
  <CardBoxModal
    v-model="modals.enablePolicy.value"
    :title="$t('views.policies.detail.confirmAction')"
    button="danger"
    has-cancel
    :button-label="$t('views.policies.detail.activate')"
    @form-submitted="enablePolicy(objToRemove.id)"
  >
    <p>
      {{
        $t('views.policies.detail.enableConfirmText', {
          name: objToRemove.name,
        })
      }}
    </p>

    <p>
      {{ $t('views.policies.detail.enableConfirmInfo') }}
    </p>

    <p>{{ $t('views.policies.detail.areYouSure') }}</p>
  </CardBoxModal>

  <!-- Disable Policy -->
  <CardBoxModal
    v-model="modals.disablePolicy.value"
    :title="$t('views.policies.detail.confirmAction')"
    button="danger"
    has-cancel
    :button-label="$t('views.policies.detail.deactivate')"
    @form-submitted="disablePolicy(objToRemove.id)"
  >
    <p>
      {{
        $t('views.policies.detail.disableConfirmText', {
          name: objToRemove.name,
        })
      }}
    </p>

    <p>{{ $t('views.policies.detail.disableConfirmInfo') }}</p>

    <p>{{ $t('views.policies.detail.areYouSure') }}</p>
  </CardBoxModal>

  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiFileSign"
        :title="policy.name ? policy.name : 'Loading...'"
        :object-model="$t('objectTypes.policy.singular')"
        main
        docs-path="/docs/usage/openvle/access-control/policies/"
      >
        <BaseButtons type="justify-start lg:justify-end">
          <BaseButton
            v-if="policy.id && permissionRefs.canEdit"
            v-tooltip="
              policy.active
                ? $t('views.policies.detail.deactivateTooltip')
                : $t('views.policies.detail.activateTooltip')
            "
            target="_blank"
            :icon="policyStatusIcon(policy.active)"
            :label="policy.active ? $t('common.active') : $t('common.inactive')"
            :color="pillType"
            rounded-full
            small
            :disabled="policyChangable"
            @click="
              showModal(
                policy.active ? 'disablePolicy' : 'enablePolicy',
                policy,
              )
            "
          />

          <BaseButton
            v-if="permissionRefs.canEdit"
            target="_blank"
            :icon="mdiPencil"
            :label="$t('common.edit')"
            color="contrast"
            rounded-full
            small
            :disabled="policyModifyable"
            @click="policyEdit(policy.id)"
          />

          <BaseButton
            v-if="permissionRefs.canDelete"
            target="_blank"
            :icon="mdiDelete"
            :label="$t('common.delete')"
            color="danger"
            rounded-full
            small
            :disabled="policyModifyable"
            @click="showModal('deletePolicy', policy)"
          />
        </BaseButtons>
      </SectionTitleLineWithButton>

      <CardBox>
        <BaseTabs v-if="permissionsLoaded" @tab-changed="handleTabChanged">
          <BaseTab id="policy" :title="$t('objectTypes.policy.singular')">
            <FormField
              :label="$t('common.name')"
              :help="$t('views.policies.form.nameHelp')"
            >
              <FormControl v-model="policy.name" :icon="mdiRename" disabled />
            </FormField>

            <FormField
              :label="$t('common.description')"
              :help="$t('views.policies.form.descriptionHelp')"
            >
              <FormControl
                v-model="policy.description"
                :icon="mdiTextBox"
                disabled
              />
            </FormField>

            <ObjectMetadataDisplay
              v-if="loadedTabs.has('policy') && policy.id"
              :object="policy"
              :object-type="objectModel"
              :object-id="route.params.id"
              :can-edit="permissionRefs.canEdit"
              :tags-help="$t('views.policies.detail.tagsHelp')"
            />
          </BaseTab>

          <BaseTab id="content" :title="$t('views.policies.form.content')">
            <BaseMarkdown v-model="policy.content" action="view" />
          </BaseTab>

          <BaseTab id="user" :title="$t('views.policies.detail.consents')">
            <SectionTitleLineWithButton
              :icon="mdiAccountBoxOutline"
              :title="$t('views.policies.detail.usersWithConsent')"
              :reload="fetchPolicyUsers"
            />

            <BaseTable
              v-if="policy.users"
              :current-page="
                childComponents.find((component) => component.name === 'users')
                  ?.currentPage
              "
              :per-page="
                childComponents.find((component) => component.name === 'users')
                  ?.perPage
              "
              :items-total="policy.usersCount"
              :data="policy.users"
              :sort-column-key="
                childComponents.find((component) => component.name === 'users')
                  ?.sortColumnKey
              "
              :sort-direction="
                childComponents.find((component) => component.name === 'users')
                  ?.sortDirection
              "
              :loading="dataLoading"
              object-model="users"
              :columns="[
                {
                  label: $t('objectTypes.user.singular'),
                  key: 'username',
                  sortKey: 'user_id',
                },
              ]"
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
              v-if="policy.id && loadedTabs.has('changelogs')"
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
