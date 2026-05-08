<script setup>
import {
  mdiAccount,
  mdiAccountMultipleOutline,
  mdiEarth,
  mdiInformation,
  mdiKey,
  mdiNumeric1Circle,
  mdiPlus,
} from '@mdi/js'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseTable from '@/components/BaseTable.vue'
import CardBoxDeleteModal from '@/components/CardBoxDeleteModal.vue'
import CardBoxModal from '@/components/CardBoxModal.vue'
import FormControl from '@/components/FormControl.vue'
import FormDropdownPrefix from '@/components/FormDropdownPrefix.vue'
import FormField from '@/components/FormField.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import SearchControl from '@/components/SearchControl.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import { SearchOperators } from '@/components/Tables/searchOperators'
import backend from '@/services'
import { SYSTEM_USER_ID } from '@/services/UserService'
import {
  checkObjectPermissions,
  formatObjectPermissionsKey,
  resolveFieldFromLookup,
  usePermissionRefs,
} from '@/utils/dataUtils'
import { getObjectPermissionsOptions } from '@/utils/objectModelPermissions'
import { useAutofocusInput } from '@/utils/useAutofocusInput'

const props = defineProps({
  objectId: { type: String, required: true },
  objectType: { type: String, required: true },
  all: { type: Boolean, default: false },
  perPage: { type: Number, default: 10 },
  runMode: { type: String, required: false, default: 'object' },
})

const permissionRefs = usePermissionRefs()
const toast = useToast()
const { t } = useI18n()

const modals = {
  addObjectPermission: ref(false),
  editObjectPermission: ref(false),
  deleteObjectPermission: ref(false),
}

const dataLoading = ref(false)

const addUserId = ref('')
const addPermissionObject = ref({
  entityType: 'User',
  permission: '',
})
const editPermission = ref('')
const editUserDisplay = ref({})

const objToRemove = ref({})
const originalPermission = ref('')
const permissions = ref([])
const searchControlUserRef = ref(null)
const { autoFocusInputRef } = useAutofocusInput(modals.addObjectPermission)

const pagination = ref({
  currentPage: 1,
  sortColumnKey: 'createdAt',
  sortDirection: 'asc',
  perPage: props.perPage,
  searchField: null,
  searchValue: null,
})

const objectPermissionsOptions = getObjectPermissionsOptions(props.objectType)

const isProtectedPermission = (item) => item.createdById === SYSTEM_USER_ID

const buttons = computed(() => {
  const btns = []

  if (permissionRefs.canEdit) {
    btns.push({
      type: 'edit',
      disabled: isProtectedPermission,
      disabledTooltip: t('components.tablePermissions.protectedRolesWarning'),
    })
  }

  if (permissionRefs.canDelete) {
    btns.push({
      type: 'delete',
      disabled: isProtectedPermission,
      disabledTooltip: t('components.tablePermissions.protectedRolesWarning'),
    })
  }

  return btns
})

const handlePaginationChanged = (newPage, newPerPage) => {
  pagination.value.currentPage = newPage
  pagination.value.perPage = newPerPage
  fetchPermissions()
}

const handleSortOrderChanged = (newSortOrder, newSortColumn) => {
  pagination.value.sortColumnKey = newSortColumn
  pagination.value.sortDirection = newSortOrder
  fetchPermissions()
}

const handleSearch = ({ field, value }) => {
  pagination.value.searchField = field
  pagination.value.searchValue = value
  pagination.value.currentPage = 1
  fetchPermissions()
}

const searchBarFields = computed(() => [
  {
    key: 'entity_id',
    label: t('components.tablePermissions.searchAssignedToPerson'),
    icon: mdiAccount,
    type: 'lookup',
    operators: SearchOperators.EQUALS_ONLY_ONLY,
    get fetchData() {
      return backend.users.search
    },
    get fetchSelected() {
      return backend.users.formatById
    },
    labelAttribute: 'name',
    returnAttribute: 'id',
    minChars: 3,
  },
  {
    key: 'entity_id',
    label: t('components.tablePermissions.searchAssignedToRole'),
    icon: mdiAccountMultipleOutline,
    type: 'lookup',
    operators: SearchOperators.EQUALS_ONLY_ONLY,
    get fetchData() {
      return backend.roles.search
    },
    get fetchSelected() {
      return backend.roles.getName
    },
    labelAttribute: 'name',
    returnAttribute: 'id',
    minChars: 3,
  },
  {
    key: 'entity_type',
    label: t('components.tablePermissions.columnType'),
    icon: mdiInformation,
    operators: SearchOperators.EQUALS_ONLY_ONLY,
    options: [
      {
        value: 'User',
        label: t('components.tablePermissions.person'),
        icon: mdiAccount,
      },
      {
        value: 'Role',
        label: t('components.tablePermissions.tooltipRole'),
        icon: mdiAccountMultipleOutline,
      },
    ],
  },
  {
    key: 'permission_key',
    label: t('components.tablePermissions.columnPermission'),
    icon: mdiKey,
    operators: SearchOperators.EQUALS_ONLY_ONLY,
    options: objectPermissionsOptions.map((opt) => ({
      value: opt.value,
      label: opt.label,
    })),
  },
  {
    preset: 'createdById',
    label: t('components.tablePermissions.searchAssignedBy'),
    operators: SearchOperators.EQUALS_ONLY_ONLY,
  },
])

const handleDeleteObject = (object, componentName) => {
  objToRemove.value = object
  modals[
    `delete${componentName.charAt(0).toUpperCase() + componentName.slice(1)}`
  ].value = true
}

const handleEditObject = (obj, componentName) => {
  const permission = permissions.value.find((p) => p.id === obj.id)
  if (permission) {
    objToRemove.value = obj.id
    editUserDisplay.value = permission

    const optionMatch = objectPermissionsOptions.find(
      (opt) =>
        opt.value === permission.permission ||
        opt.label === permission.permission,
    )

    originalPermission.value = optionMatch?.value || ''
    editPermission.value = optionMatch?.value || ''
  }
  modals[
    `edit${componentName.charAt(0).toUpperCase() + componentName.slice(1)}`
  ].value = true
}

const showModal = (modal, item) => {
  if (Object.prototype.hasOwnProperty.call(modals, modal)) {
    modals[modal].value = true
  }
  if (item) {
    objToRemove.value = item
  }
}

async function fetchPermissions() {
  dataLoading.value = true
  try {
    const response = await backend.objectPermissions.listByObject(
      props.objectType,
      props.objectId,
      {
        page: pagination.value.currentPage,
        limit: pagination.value.perPage,
        sort_by: pagination.value.sortColumnKey,
        sort_order: pagination.value.sortDirection,
        search_field: pagination.value.searchField,
        search_value: pagination.value.searchValue,
      },
    )
    permissions.value = response.items
    permissions.value.permissionsCount = response.pageDetails.totalCount

    const configs = [
      {
        entity_type: 'User',
        keyspace: 'users',
        label: t('components.tablePermissions.person'),
      },
      {
        entity_type: 'Role',
        keyspace: 'roles',
        label: t('components.tablePermissions.role'),
      },
    ]

    for (const { entity_type, keyspace, label } of configs) {
      for (const obj of permissions.value.filter(
        (o) => o.entity_type === entity_type,
      )) {
        await resolveFieldFromLookup(obj, [
          { from: 'entity_id', to: 'entity', keyspace },
          {
            from: 'createdById',
            to: 'createdBy',
            keyspace: 'users',
            formatter: formatObjectPermissionsKey,
          },
        ])

        obj.entity_label = label
      }
    }
  } catch (error) {
    toast.error(
      `${t('common.loadError', { entity: t('objectTypes.permission.singular') })}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  } finally {
    dataLoading.value = false
  }
}

async function addObjectPermission(entityId, permissionKey, entityType) {
  try {
    await backend.objectPermissions.create({
      objectType: props.objectType,
      objectId: props.objectId,
      entityId,
      entityType,
      permissionKey,
    })
    toast.success(t('components.tablePermissions.permissionAdded'))
    modals.addObjectPermission.value = false
  } catch (error) {
    toast.error(
      `${t('common.addError', { entity: t('objectTypes.permission.singular') })}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  } finally {
    fetchPermissions()
    resetAddPermissionForm()
  }
}

async function editObjectPermission(permissionId, newPermission) {
  const old = permissions.value.find((p) => p.id === permissionId)
  if (!old)
    return toast.error(t('components.tablePermissions.oldPermissionNotFound'))

  try {
    await backend.objectPermissions.delete(permissionId)
    await backend.objectPermissions.create({
      objectType: props.objectType,
      objectId: old.object_id,
      entityId: old.entity_id,
      entityType: old.entity_type,
      permissionKey: newPermission,
    })
    toast.success(t('components.tablePermissions.permissionEdited'))
    modals.editObjectPermission.value = false
  } catch {
    toast.error(
      t('common.editError', { entity: t('objectTypes.permission.singular') }),
    )
  } finally {
    fetchPermissions()
  }
}

async function deleteObjectPermission(permissionId) {
  try {
    await backend.objectPermissions.delete(permissionId)
    toast.success(t('components.tablePermissions.permissionRemoved'))
    modals.deleteObjectPermission.value = false
  } catch (error) {
    toast.error(
      `${t('common.removeError', { entity: t('objectTypes.permission.singular') })}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  } finally {
    fetchPermissions()
  }
}

const deleteConfirmLabel = (id) => {
  const p = permissions.value.find((p) => p.id === id)
  return t('components.tablePermissions.deleteLabel', {
    permission: p?.permission,
    entityLabel: p?.entity_label,
    entity: p?.entity,
  })
}

const isPermissionUnchanged = computed(() => {
  return originalPermission.value === editPermission.value
})

const resetAddPermissionForm = () => {
  addUserId.value = ''
  addPermissionObject.value.permission = ''
  addPermissionObject.value.entityType = 'User'
  searchControlUserRef.value?.setInitialDisplay('')
  searchControlUserRef.value?.setSelectedId('')
}

watch(
  () => addPermissionObject.value.entityType,
  () => {
    addUserId.value = null
    searchControlUserRef.value?.setInitialDisplay('')
    searchControlUserRef.value?.setSelectedId('')
  },
)

const addPermissionOptions = computed(() => [
  {
    label: t('components.tablePermissions.person'),
    value: 'User',
    icon: mdiAccount,
    fetchData: backend.users.search,
    fetchSelected: backend.users.formatById,
    placeholder: t('components.tablePermissions.searchUserPlaceholder'),
  },
  {
    label: t('components.tablePermissions.role'),
    value: 'Role',
    icon: mdiAccountMultipleOutline,
    fetchData: backend.roles.search,
    fetchSelected: backend.roles.getName,
    placeholder: t('components.tablePermissions.searchRolePlaceholder'),
  },
])

onMounted(async () => {
  fetchPermissions()

  await checkObjectPermissions(
    'object_permissions',
    props.objectId,
    permissionRefs,
    [],
    ['canCreate', 'canDelete'],
  )

  permissionRefs.canEdit = permissionRefs.canCreate && permissionRefs.canDelete
})
</script>

<template>
  <!-- Modal: Add permission -->
  <CardBoxModal
    v-model="modals.addObjectPermission.value"
    form
    :title="$t('components.tablePermissions.permissionAdd')"
    button="success"
    has-cancel
    has-search
    scrollable
    button-:label="$t('components.tablePermissions.permissionAdd')"
    @cancel="resetAddPermissionForm()"
    @form-submitted="
      addObjectPermission(
        addUserId,
        addPermissionObject.permission,
        addPermissionObject.entityType,
      )
    "
  >
    <!-- Entity type and id selection (user or role) -->
    <FormField :label="$t('components.tablePermissions.assignTo')">
      <div class="flex">
        <FormDropdownPrefix
          v-model:prefix-value="addPermissionObject.entityType"
          :options="addPermissionOptions"
          required
        />

        <div class="flex-1">
          <SearchControl
            v-model="addUserId"
            borders="right"
            :fetch-data="
              addPermissionOptions.find(
                (option) => option.value === addPermissionObject.entityType,
              )?.fetchData ?? null
            "
            :fetch-selected="
              addPermissionOptions.find(
                (option) => option.value === addPermissionObject.entityType,
              )?.fetchSelected ?? null
            "
            :placeholder="
              addPermissionOptions.find(
                (option) => option.value === addPermissionObject.entityType,
              )?.placeholder ?? null
            "
            required
            @set-ref="
              (ref) => {
                searchControlUserRef = ref
                autoFocusInputRef = ref
              }
            "
          />
        </div>
      </div>
    </FormField>

    <!-- Permission selection -->
    <FormField :label="$t('components.tablePermissions.permission')">
      <div class="space-y-2">
        <label
          v-for="option in objectPermissionsOptions"
          :key="option.value"
          class="flex items-start gap-3 p-2 rounded-lg cursor-pointer border border-transparent hover:border-gray-200"
          :class="
            addPermissionObject.permission === option.value
              ? 'bg-gray-800 text-white dark:bg-gray-700 border-gray-200'
              : 'hover:bg-gray-50 dark:hover:bg-gray-800'
          "
        >
          <input
            v-model="addPermissionObject.permission"
            type="radio"
            class="mt-1 form-radio"
            :value="option.value"
            required
          />

          <div class="leading-tight">
            <div class="text-sm font-medium">{{ option.label }}</div>

            <div
              v-if="option.description"
              class="text-xs mt-0.5"
              :class="
                addPermissionObject.permission === option.value
                  ? 'bg-gray-800 text-white dark:bg-gray-700 border-gray-200'
                  : 'hover:bg-gray-50 dark:hover:bg-gray-800'
              "
            >
              {{ option.description }}
            </div>
          </div>
        </label>
      </div>
    </FormField>
  </CardBoxModal>

  <!-- Modal: Edit permission -->
  <CardBoxModal
    v-model="modals.editObjectPermission.value"
    form
    :title="$t('components.tablePermissions.permissionEdit')"
    button="success"
    has-cancel
    button-:label="$t('components.tablePermissions.permissionSave')"
    :disabled="isPermissionUnchanged"
    @form-submitted="editObjectPermission(objToRemove, editPermission)"
  >
    <!-- Entity display (read-only) -->
    <FormField :label="$t('components.tablePermissions.assignedTo')">
      <FormControl
        :model-value="
          editUserDisplay.entity + ' (' + editUserDisplay.entity_label + ')'
        "
        :icon="
          editUserDisplay.entity_type === 'User'
            ? mdiAccount
            : mdiAccountMultipleOutline
        "
        disabled
      />
    </FormField>

    <!-- Permission selection (read, update, delete, full or actions)-->
    <FormField :label="$t('components.tablePermissions.permission')">
      <div class="space-y-2">
        <label
          v-for="option in objectPermissionsOptions"
          :key="option.value"
          class="flex items-start gap-3 p-2 rounded-lg cursor-pointer border border-transparent hover:border-gray-200"
          :class="
            editPermission === option.value
              ? 'bg-gray-800 text-white dark:bg-gray-700 border-gray-200'
              : 'hover:bg-gray-50 dark:hover:bg-gray-800'
          "
        >
          <input
            v-model="editPermission"
            type="radio"
            class="mt-1 form-radio"
            :value="option.value"
            required
          />

          <div class="leading-tight">
            <div class="text-sm font-medium">{{ option.label }}</div>

            <div
              v-if="option.description"
              class="text-xs mt-0.5"
              :class="
                editPermission === option.value
                  ? 'bg-gray-800 text-white dark:bg-gray-700 border-gray-200'
                  : 'hover:bg-gray-50 dark:hover:bg-gray-800'
              "
            >
              {{ option.description }}
            </div>
          </div>
        </label>
      </div>
    </FormField>
  </CardBoxModal>

  <!-- Modal: Delete permission -->
  <CardBoxDeleteModal
    v-model="modals.deleteObjectPermission.value"
    :name="deleteConfirmLabel(objToRemove.id)"
    :checkvalue="$t('common.confirmation')"
    @form-submitted="deleteObjectPermission(objToRemove.id)"
  />

  <SectionTitleLineWithButton
    :icon="mdiKey"
    :title="$t('components.tablePermissions.permissions')"
    :reload="fetchPermissions"
  >
    <BaseButton
      v-if="permissionRefs.canCreate"
      :icon="mdiPlus"
      color="success"
      rounded-full
      small
      @click="showModal('addObjectPermission')"
    />
  </SectionTitleLineWithButton>

  <NotificationBar :dismissable="false" color="info" :icon="mdiInformation">
    <p>
      {{ $t('components.tablePermissions.infoText') }}
    </p>
  </NotificationBar>

  <BaseTable
    v-if="permissions"
    :current-page="pagination.currentPage"
    :per-page="pagination.perPage"
    :items-total="permissions.permissionsCount"
    :data="permissions"
    :sort-column-key="pagination.sortColumnKey"
    :sort-direction="pagination.sortDirection"
    :loading="dataLoading"
    object-model="objectPermission"
    :buttons="buttons"
    :emit-edit-object="true"
    :search-bar-fields="searchBarFields"
    :search-bar-max-filters="1"
    :columns="[
      {
        label: $t('components.tablePermissions.columnType'),
        key: props.runMode === 'object' ? 'entity_label' : 'object_type',
        sortKey: props.runMode === 'object' ? 'entity_type' : 'object_type',
        formatter: ['', ''],
        ...(props.runMode === 'object'
          ? {
              icon: (value) =>
                value === t('components.tablePermissions.person')
                  ? mdiAccount
                  : mdiAccountMultipleOutline,
              color: (value) =>
                value === t('components.tablePermissions.person')
                  ? 'info'
                  : 'contrast',
              tooltip: (value) =>
                value === t('components.tablePermissions.person')
                  ? t('components.tablePermissions.tooltipPerson')
                  : t('components.tablePermissions.tooltipRole'),
            }
          : {}),
        width: '100px',
      },
      {
        label:
          props.runMode === 'object'
            ? $t('components.tablePermissions.columnAssignedTo')
            : $t('components.tablePermissions.columnObject'),
        key: props.runMode === 'object' ? 'entity' : 'object_id',
        sortKey: props.runMode === 'object' ? 'entity_id' : 'object_id',
        width: '190px',
      },
      {
        label: $t('components.tablePermissions.columnPermission'),
        key: 'permission',
        sortKey: 'permission_key',
        width: '210px',
      },
      {
        label: $t('components.tablePermissions.columnScope'),
        key: 'object_id',
        sortKey: 'object_id',
        icon: (value) => (value ? mdiNumeric1Circle : mdiEarth),
        color: (value) => (value ? 'info' : 'warning'),
        tooltip: (value) =>
          value
            ? t('components.tablePermissions.tooltipObjectScope')
            : t('components.tablePermissions.tooltipGlobalScope'),
        formatter: (value) =>
          value
            ? t('components.tablePermissions.scopeObject')
            : t('components.tablePermissions.scopeGlobal'),
        width: '130px',
      },
      {
        label: $t('components.tablePermissions.columnAssignedBy'),
        key: 'createdBy',
        sortKey: 'createdById',
        width: '160px',
      },
    ]"
    @edit-object="handleEditObject"
    @delete-object="handleDeleteObject"
    @sort-order-changed="handleSortOrderChanged"
    @pagination-changed="handlePaginationChanged"
    @search-triggered="handleSearch"
  />
</template>
