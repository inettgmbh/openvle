<script setup>
import {
  mdiAccount,
  mdiAccountMultipleOutline,
  mdiCheck,
  mdiClose,
  mdiContentCopy,
  mdiDelete,
  mdiInformation,
  mdiKey,
  mdiLoading,
  mdiLock,
  mdiLockOpen,
  mdiPencil,
  mdiPlus,
  mdiRename,
  mdiTextBox,
} from '@mdi/js'
import { computed, onMounted, reactive, ref, toRaw, unref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseIcon from '@/components/BaseIcon.vue'
import BaseTab from '@/components/BaseTab.vue'
import BaseTable from '@/components/BaseTable.vue'
import BaseTabs from '@/components/BaseTabs.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxCloneModal from '@/components/CardBoxCloneModal.vue'
import CardBoxDeleteModal from '@/components/CardBoxDeleteModal.vue'
import CardBoxDeleteRelationModal from '@/components/CardBoxDeleteRelationModal.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import ObjectMetadataDisplay from '@/components/ObjectMetadataDisplay.vue'
import OverlayLayer from '@/components/OverlayLayer.vue'
import PermissionsMatrix from '@/components/permissions/PermissionMatrix.vue'
import PillTag from '@/components/PillTag.vue'
import SearchModal from '@/components/SearchModal.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import { userSearchBarFields } from '@/components/Tables/searchBarFieldConfigs'
import TableChangelogs from '@/components/Tables/TableChangelogs.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { useMainStore } from '@/stores/main'
import {
  checkObjectPermissions,
  resolveFieldFromLookup,
  usePermissionRefs,
  userStatusLabel,
} from '@/utils/dataUtils'
import { userStatusIcon } from '@/utils/icons'
import { statusColorUser } from '@/utils/objectColors.js'
import { normalizePermission } from '@/utils/objectModelPermissions'
import { usePaginationChild } from '@/utils/pagination'

const { t } = useI18n()
const permissionRefs = usePermissionRefs()
const mainStore = useMainStore()

const modals = {
  addRoleMember: ref(false),
  cloneRole: ref(false),
  deleteRole: ref(false),
  deleteUsers: ref(false),
}
const clonedRole = ref({})
const cloneProgress = reactive({
  isActive: false,
  phase: 'idle',
  current: 0,
  total: 0,
  errors: [],
  newRoleId: null,
  skippedPermissions: false,
})
const dataLoading = ref(true)
const objectModel = 'Role'
const objToAdd = ref({})
const objToRemove = ref({})
const permissionsLoaded = ref(false)
const role = ref({})
const roleMembers = ref([])
const router = useRouter()
const route = useRoute()
const toast = useToast()

/* PAGINATION ONLY */
const {
  childComponents,
  loadedTabs,
  handlePaginationChanged,
  handleSortOrderChanged,
  handleSearch,
  handleDeleteObject,
  handleTabChanged,
} = usePaginationChild({
  children: [
    {
      name: 'users',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'name',
      sortDirection: 'asc',
      searchField: null,
      searchValue: null,
      fetchData: fetchRoleMembers,
    },
  ],
  fetchArgs: () => [route.params.id],
  modals,
  objToRemove,
  route,
})
/**/

const memberSearchBarFields = userSearchBarFields()

async function addRoleMember(memberId) {
  try {
    await backend.users.addRole(memberId, role.value.key)
    fetchRoleMembers()
    toast.success(t('views.roles.detail.memberAdded'))
  } catch (error) {
    toast.error(
      t('common.addError', { entity: t('objectTypes.member.singular') }),
    )
  }
}

async function cloneRole(role) {
  if (
    role.name?.toLowerCase() === 'studierende' ||
    role.name?.toLowerCase() === 'lehrende'
  ) {
    modals.cloneRole.value = true
    return toast.error(t('views.roles.form.reservedNameTooltip'))
  }

  // Initialize progress modal
  cloneProgress.isActive = true
  cloneProgress.phase = 'creating_role'
  cloneProgress.current = 0
  cloneProgress.total = 0
  cloneProgress.errors = []
  cloneProgress.newRoleId = null
  cloneProgress.skippedPermissions = false

  // Check if user can clone object permissions (explicitly check for true)
  // Use unref() to handle both raw values and refs (reactive auto-unwrap may vary)
  const canCloneObjectPermissions =
    unref(permissionRefs.canReadObjectPermissions) === true &&
    unref(permissionRefs.canCreateObjectPermissions) === true

  let newRole = null

  try {
    newRole = await backend.roles.create({
      name: role.name,
      key: role.name.toLowerCase().replace(/[^a-z0-9]+/g, '_'),
      description: role.description,
      protected: false,
    })
    cloneProgress.newRoleId = newRole.id

    if (!canCloneObjectPermissions) {
      // User lacks permissions to clone object permissions
      cloneProgress.skippedPermissions = true
    } else {
      cloneProgress.phase = 'loading_permissions'

      // First, collect all permissions to get total count
      const allPermissions = []
      let page = 1
      let hasMore = true

      while (hasMore) {
        const response = await backend.objectPermissions.list({
          page,
          limit: 200,
          search_field: 'entity_id',
          search_value: route.params.id,
        })
        allPermissions.push(...response.items)
        hasMore = response.items.length === 200
        page++
      }

      cloneProgress.total = allPermissions.length
      cloneProgress.phase = 'copying_permissions'

      // Clone each permission
      for (const perm of allPermissions) {
        try {
          const normalized = normalizePermission(perm)
          await backend.objectPermissions.create({
            objectType: normalized.objectType,
            objectId: normalized.objectId,
            entityId: newRole.id,
            entityType: 'Role',
            permissionKey: normalized.permissionKey,
          })
        } catch (err) {
          cloneProgress.errors.push({
            index: cloneProgress.current,
            error: err,
          })
        }
        cloneProgress.current++
      }
    }

    cloneProgress.phase = 'done'
    useMainStore().fetchPermissions()
  } catch (error) {
    cloneProgress.phase = 'error'
    cloneProgress.errors.push({ index: 0, error })
  }
}

function closeCloneProgress() {
  const shouldNavigate =
    cloneProgress.phase === 'done' && cloneProgress.errors.length === 0
  const targetId = cloneProgress.newRoleId

  cloneProgress.isActive = false

  if (shouldNavigate && targetId) {
    router.push({ path: `/roles/${targetId}` })
  }
}

async function deleteRole(roleId) {
  try {
    await backend.roles.delete(roleId)
    router.push({ path: `/roles` })
    toast.success(
      t('common.deleteSuccess', { entity: t('objectTypes.role.singular') }),
    )
  } catch (error) {
    toast.error(
      t('common.deleteError', { entity: t('objectTypes.role.singular') }),
    )
  }
}

async function deleteRoleMember(memberId) {
  try {
    await backend.users.deleteRole(memberId, role.value.key)
    fetchRoleMembers()
    toast.success(t('views.roles.detail.memberRemoved'))
  } catch (error) {
    toast.error(
      t('common.removeError', { entity: t('objectTypes.member.singular') }),
    )
  }
}

async function fetchRole(roleId) {
  try {
    dataLoading.value = true

    await backend.roles.get(roleId).then(async (response) => {
      role.value = response
      clonedRole.value = structuredClone(toRaw(response))
      clonedRole.value.name = ''
      await resolveFieldFromLookup(role.value, [
        { from: 'createdById', to: 'createdBy', keyspace: 'users' },
        { from: 'updatedById', to: 'updatedBy', keyspace: 'users' },
      ])
    })
  } catch (error) {
    toast.warning(
      t('common.notFound', { entity: t('objectTypes.role.singular') }),
    )
    router.push({ path: `/roles`, replace: true })
  } finally {
    dataLoading.value = false
  }
}

async function fetchRoleMembers() {
  try {
    dataLoading.value = true

    const usersComponent = childComponents.value.find(
      (component) => component.name === 'users',
    )
    await backend.roles
      .getMembers(route.params.id, {
        page: usersComponent?.currentPage,
        limit: usersComponent?.perPage,
        sort_by: usersComponent?.sortColumnKey,
        sort_order: usersComponent?.sortDirection,
        search_field: usersComponent?.searchField,
        search_value: usersComponent?.searchValue,
      })
      .then((response) => {
        roleMembers.value = response.items
        roleMembers.value.count = response.pageDetails.totalCount
      })
  } catch (error) {
    toast.warning(
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

const roleEdit = (roleId) => {
  router.push({ path: `${roleId}/edit` })
}

const pillType = computed(() => {
  if (role.value.id) {
    if (role.value.protected) {
      return 'danger'
    }
    return 'success'
  }
  return 'info'
})

const buttonsMembers = computed(() => {
  if (permissionRefs.canEdit) return ['view', 'delete']
  return ['view']
})

async function loadRoleAndPermissions(id) {
  await fetchRole(id)

  await checkObjectPermissions(
    'roles',
    id,
    permissionRefs,
    [
      {
        key: 'canAddMember',
        objectType: 'users',
        objectPermission: 'update',
        objectPath: '/*',
      },
      {
        key: 'canReadSystem',
        objectType: 'system',
        objectPermission: 'read',
        objectPath: '/*',
      },
      {
        key: 'canReadChangelogs',
        objectType: 'changelogs',
        objectPermission: 'read',
        objectPath: '/*',
      },
      {
        key: 'canReadObjectPermissions',
        objectType: 'object_permissions',
        objectPermission: 'read',
        objectPath: '/*',
      },
      {
        key: 'canCreateObjectPermissions',
        objectType: 'object_permissions',
        objectPermission: 'create',
        objectPath: '/*',
      },
    ],
    ['canCreate', 'canEdit', 'canDelete'],
  )
}

onMounted(async () => {
  await loadRoleAndPermissions(route.params.id)
  permissionsLoaded.value = true
})

watch(
  () => route.params.id,
  async (newId, oldId) => {
    if (!newId || newId === oldId) return

    dataLoading.value = true
    permissionsLoaded.value = false

    loadedTabs.clear()
    childComponents.value.forEach((component) => {
      component.currentPage = 1
    })

    try {
      await loadRoleAndPermissions(newId)
    } finally {
      permissionsLoaded.value = true
      dataLoading.value = false
    }
  },
)
</script>

<template>
  <!-- Modal: Clone progress -->
  <OverlayLayer v-show="cloneProgress.isActive">
    <CardBox class="shadow-lg w-11/12 md:w-2/5 lg:w-1/3 z-50" is-modal>
      <div class="p-6">
        <!-- Header -->
        <div class="flex items-center gap-3 mb-6">
          <div
            class="w-10 h-10 rounded-full flex items-center justify-center"
            :class="[
              cloneProgress.phase === 'done' &&
              cloneProgress.errors.length === 0
                ? 'bg-green-100 dark:bg-green-900/30'
                : cloneProgress.phase === 'error' ||
                    cloneProgress.errors.length > 0
                  ? 'bg-red-100 dark:bg-red-900/30'
                  : 'bg-blue-100 dark:bg-blue-900/30',
            ]"
          >
            <BaseIcon
              v-if="
                cloneProgress.phase === 'done' &&
                cloneProgress.errors.length === 0
              "
              :path="mdiCheck"
              class="text-green-600 dark:text-green-400"
              :size="24"
            />

            <BaseIcon
              v-else-if="
                cloneProgress.phase === 'error' ||
                cloneProgress.errors.length > 0
              "
              :path="mdiClose"
              class="text-red-600 dark:text-red-400"
              :size="24"
            />

            <BaseIcon
              v-else
              :path="mdiLoading"
              class="text-blue-600 dark:text-blue-400 animate-spin"
              :size="24"
            />
          </div>

          <div>
            <h3 class="text-lg font-semibold">
              {{ $t('views.roles.detail.cloneTitle') }}
            </h3>

            <p class="text-sm opacity-60">
              {{
                cloneProgress.phase === 'creating_role'
                  ? $t('views.roles.detail.cloneCreating')
                  : cloneProgress.phase === 'loading_permissions'
                    ? $t('views.roles.detail.cloneLoadingPerms')
                    : cloneProgress.phase === 'copying_permissions'
                      ? $t('views.roles.detail.cloneCopyingPerms')
                      : cloneProgress.phase === 'done'
                        ? $t('views.roles.detail.cloneDone')
                        : cloneProgress.phase === 'error'
                          ? $t('views.roles.detail.cloneErrorOccurred')
                          : $t('views.roles.detail.clonePreparing')
              }}
            </p>
          </div>
        </div>

        <!-- Progress Bar -->
        <div v-if="cloneProgress.total > 0" class="mb-4">
          <div class="flex justify-between text-sm opacity-60 mb-2">
            <span>{{ cloneProgress.current }} / {{ cloneProgress.total }}</span>

            <span>
              {{
                cloneProgress.total > 0
                  ? Math.round(
                      (cloneProgress.current / cloneProgress.total) * 100,
                    )
                  : 0
              }}%
            </span>
          </div>

          <div
            class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden"
          >
            <div
              class="h-full rounded-full transition-all duration-300 ease-out"
              :class="[
                cloneProgress.errors.length > 0
                  ? 'bg-red-500'
                  : cloneProgress.phase === 'done'
                    ? 'bg-green-500'
                    : 'bg-blue-500',
              ]"
              :style="{
                width: `${cloneProgress.total > 0 ? (cloneProgress.current / cloneProgress.total) * 100 : 0}%`,
              }"
            />
          </div>
        </div>

        <!-- Skipped Permissions Notice -->
        <div
          v-if="cloneProgress.skippedPermissions"
          class="mt-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200"
        >
          <p class="text-sm font-medium text-yellow-800 mb-1">
            {{ $t('views.roles.detail.clonePermsSkippedTitle') }}
          </p>

          <p class="text-xs text-yellow-700">
            {{ $t('views.roles.detail.clonePermsSkippedDesc') }}
          </p>
        </div>

        <!-- Error Summary -->
        <div
          v-if="cloneProgress.errors.length > 0"
          class="mt-4 p-3 bg-red-50 rounded-lg border border-red-200"
        >
          <p class="text-sm font-medium text-red-800 mb-2">
            {{
              $t('views.roles.detail.cloneErrorCount', {
                count: cloneProgress.errors.length,
              })
            }}
          </p>

          <ul class="text-xs text-red-700 space-y-1 max-h-24 overflow-y-auto">
            <li
              v-for="(err, idx) in cloneProgress.errors.slice(0, 5)"
              :key="idx"
            >
              {{
                err.error?.message || $t('views.roles.detail.cloneUnknownError')
              }}
            </li>
          </ul>
        </div>

        <!-- Close Button -->
        <div
          v-if="
            cloneProgress.phase === 'done' || cloneProgress.phase === 'error'
          "
          class="mt-6 flex justify-center"
        >
          <button
            type="button"
            class="px-4 py-2 text-sm font-medium rounded-lg transition-colors"
            :class="[
              cloneProgress.errors.length > 0
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-green-600 hover:bg-green-700 text-white',
            ]"
            @click="closeCloneProgress"
          >
            {{
              cloneProgress.errors.length > 0
                ? $t('common.close')
                : $t('views.roles.detail.cloneFinished')
            }}
          </button>
        </div>
      </div>
    </CardBox>
  </OverlayLayer>

  <!-- Modal: Add member to role -->
  <SearchModal
    v-model="modals.addRoleMember.value"
    :fetch-data="backend.users.search"
    :icon="mdiAccount"
    :label="$t('views.roles.detail.searchMember')"
    :title="$t('views.roles.detail.addMemberTitle')"
    @submitted="addRoleMember"
  />

  <!-- Modal: Clone role -->
  <CardBoxCloneModal
    v-model="modals.cloneRole.value"
    :name="role.name"
    :checkvalue="role.name"
    @form-submitted="cloneRole(clonedRole)"
  >
    <NotificationBar :dismissable="false" color="info" :icon="mdiInformation">
      {{ $t('views.roles.detail.cloneNotice') }}
    </NotificationBar>

    <FormField
      :label="$t('views.roles.detail.cloneNameLabel')"
      :help="$t('views.roles.form.nameHelp')"
    >
      <FormControl
        v-model="clonedRole.name"
        :icon="mdiRename"
        :placeholder="$t('views.roles.form.namePlaceholder')"
        required
      />
    </FormField>
  </CardBoxCloneModal>

  <!-- Modal: Delete member from role -->
  <CardBoxDeleteRelationModal
    v-model="modals.deleteUsers.value"
    :parent-object="role.name"
    :related-object="objToRemove.name"
    :checkvalue="$t('common.confirmation')"
    @form-submitted="deleteRoleMember(objToRemove.id)"
  />

  <!-- Modal: Delete role -->
  <CardBoxDeleteModal
    v-model="modals.deleteRole.value"
    :name="role.name"
    :checkvalue="role.name"
    @form-submitted="deleteRole(role.id)"
  />

  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiAccountMultipleOutline"
        :title="role.name ? role.name : 'Loading...'"
        :object-model="$t('objectTypes.role.singular')"
        main
        docs-path="/docs/usage/openvle/access-control/roles/"
      >
        <BaseButtons type="justify-start lg:justify-end">
          <PillTag
            :help="$t('views.roles.detail.protectedHelp')"
            disabled
            label=""
            :color="pillType"
            :icon="role.protected ? mdiLock : mdiLockOpen"
          />

          <BaseButton
            v-if="role.id && permissionRefs.canCreate"
            target="_blank"
            :icon="mdiContentCopy"
            :label="$t('common.clone')"
            color="info"
            rounded-full
            small
            @click="showModal('cloneRole', role.id)"
          />

          <BaseButton
            v-if="permissionRefs.canEdit"
            v-tooltip="
              role.protected
                ? $t('views.roles.detail.protectedEditTooltip')
                : undefined
            "
            target="_blank"
            :icon="mdiPencil"
            :label="$t('common.edit')"
            color="contrast"
            rounded-full
            small
            :disabled="role.protected"
            @click="roleEdit(role.id)"
          />

          <BaseButton
            v-if="permissionRefs.canDelete"
            v-tooltip="
              role.protected
                ? $t('views.roles.detail.protectedDeleteTooltip')
                : undefined
            "
            target="_blank"
            :icon="mdiDelete"
            :label="$t('common.delete')"
            color="danger"
            rounded-full
            small
            :disabled="role.protected"
            @click="showModal('deleteRole', role.id)"
          />
        </BaseButtons>
      </SectionTitleLineWithButton>

      <CardBox>
        <BaseTabs v-if="permissionsLoaded" @tab-changed="handleTabChanged">
          <BaseTab id="role" :title="$t('objectTypes.role.singular')">
            <FormField
              :label="$t('common.name')"
              :help="$t('views.roles.form.nameHelp')"
            >
              <FormControl v-model="role.name" :icon="mdiRename" disabled />
            </FormField>

            <FormField
              label="Key (Slug)"
              :help="$t('views.roles.form.keyHelp')"
            >
              <FormControl v-model="role.key" :icon="mdiKey" disabled />
            </FormField>

            <FormField
              :label="$t('common.description')"
              :help="$t('views.roles.form.descriptionHelp')"
            >
              <FormControl
                v-model="role.description"
                :icon="mdiTextBox"
                disabled
              />
            </FormField>

            <ObjectMetadataDisplay
              v-if="loadedTabs.has('role') && role.id"
              :object="role"
              :object-type="objectModel"
              :object-id="route.params.id"
              :can-edit="permissionRefs.canEdit"
              :tags-help="$t('views.roles.detail.tagsHelp')"
            />
          </BaseTab>

          <BaseTab
            v-if="permissionRefs.canReadObjectPermissions"
            id="permissions-z"
            :title="$t('views.roles.detail.assignedPermissions')"
          >
            <PermissionsMatrix
              v-if="loadedTabs.has('permissions-z')"
              :entity-id="route.params.id"
              :entity-type="objectModel"
              :readonly="role.protected"
            />
          </BaseTab>

          <BaseTab id="users" :title="$t('views.roles.detail.members')">
            <SectionTitleLineWithButton
              :icon="mdiAccount"
              :title="$t('views.roles.detail.members')"
              :reload="fetchRoleMembers"
            >
              <BaseButton
                v-if="permissionRefs.canAddMember"
                target="_blank"
                :icon="mdiPlus"
                :label="$t('common.add')"
                color="contrast"
                rounded-full
                small
                @click="modals.addRoleMember.value = true"
              />
            </SectionTitleLineWithButton>

            <BaseTable
              v-if="roleMembers"
              :current-page="
                childComponents.find((component) => component.name === 'users')
                  ?.currentPage
              "
              :per-page="
                childComponents.find((component) => component.name === 'users')
                  ?.perPage
              "
              :items-total="roleMembers.count"
              :data="roleMembers"
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
              :buttons="buttonsMembers"
              :symbol="true"
              :search-bar-fields="memberSearchBarFields"
              :search-bar-max-filters="1"
              search-bar-query-key="filter-users"
              :columns="[
                { label: 'symbol', key: 'username', symbol: true },
                { label: $t('common.name'), key: 'name' },
                {
                  label: $t('views.roles.detail.username'),
                  key: 'username',
                },
                { label: $t('views.roles.detail.email'), key: 'email' },
                {
                  label: $t('common.status'),
                  key: 'status',
                  color: statusColorUser,
                  icon: (value) => userStatusIcon(value),
                  formatter: (value) => userStatusLabel(value),
                },
              ]"
              @delete-object="handleDeleteObject"
              @sort-order-changed="handleSortOrderChanged"
              @pagination-changed="handlePaginationChanged"
              @search-triggered="handleSearch"
            />
          </BaseTab>

          <BaseTab
            v-if="permissionRefs.canReadChangelogs"
            id="changelogs"
            :title="$t('objectTypes.changelog.plural')"
          >
            <TableChangelogs
              v-if="role.id && loadedTabs.has('changelogs')"
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
