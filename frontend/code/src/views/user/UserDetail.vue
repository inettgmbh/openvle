<script setup>
import {
  mdiAccount,
  mdiAccountLock,
  mdiAccountLockOpen,
  mdiAccountMultiple,
  mdiAccountMultipleOutline,
  mdiAccountOutline,
  mdiAccountQuestion,
  mdiCalendarOutline,
  mdiDelete,
  mdiEye,
  mdiFormTextboxPassword,
  mdiKey,
  mdiMail,
  mdiMailboxOutline,
  mdiMonitor,
  mdiPencil,
  mdiPlus,
  mdiRemoteDesktop,
  mdiRename,
  mdiTextBox,
  mdiTrashCan,
  mdiWebBox,
} from '@mdi/js'
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseDivider from '@/components/BaseDivider.vue'
import BaseTab from '@/components/BaseTab.vue'
import BaseTable from '@/components/BaseTable.vue'
import BaseTabs from '@/components/BaseTabs.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxDeleteModal from '@/components/CardBoxDeleteModal.vue'
import CardBoxDeleteRelationModal from '@/components/CardBoxDeleteRelationModal.vue'
import CardBoxDeleteUserModal from '@/components/CardBoxDeleteUserModal.vue'
import CardBoxModal from '@/components/CardBoxModal.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import ObjectMetadataDisplay from '@/components/ObjectMetadataDisplay.vue'
import PermissionsMatrix from '@/components/permissions/PermissionMatrix.vue'
import PillTag from '@/components/PillTag.vue'
import SearchModal from '@/components/SearchModal.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import {
  eventSearchBarFields,
  guacamoleSearchBarFields,
  vmSearchBarFields,
} from '@/components/Tables/searchBarFieldConfigs'
import TableChangelogs from '@/components/Tables/TableChangelogs.vue'
import TablePermissions from '@/components/Tables/TablePermissions.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { SYSTEM_USER_ID } from '@/services/UserService'
import { useMainStore } from '@/stores/main'
import {
  checkObjectPermissions,
  connectionProfileLabelFormatter,
  emailStatusFormatter,
  resolveFieldFromLookup,
  usePermissionRefs,
  userStatusLabel,
} from '@/utils/dataUtils'
import {
  emailStatusIcon,
  eventCreateTypeIcon,
  eventStatusIcon,
  methodHTTPIcon,
  responseCodeHTTPIcon,
  userAuthBackendIcon,
  vmStatusIcon,
} from '@/utils/icons'
import { getUserLocaleOptions } from '@/utils/localeData'
import {
  authBackendColorUser,
  createTypeColorConnection,
  responseCodeColorActivity,
  responseMethodColorActivity,
  statusColorEvent,
  statusColorMail,
  statusColorVM,
} from '@/utils/objectColors'
import { usePaginationChild } from '@/utils/pagination'
import { eventCreateTypeTooltip } from '@/utils/tooltips'
import { useAutofocusInput } from '@/utils/useAutofocusInput'

const { t } = useI18n()
const mainStore = useMainStore()
const permissionRefs = usePermissionRefs()

const modals = {
  addUserGuacamole: ref(false),
  addUserRole: ref(false),
  deleteUser: ref(false),
  deleteGuacamoles: ref(false),
  deleteUserRole: ref(false),
  lockUser: ref(false),
  setPassword: ref(false),
}
const { autoFocusInputRef } = useAutofocusInput(modals.addUserGuacamole)
const connections = ref([])
const dataLoading = ref(true)
const isInitial = ref(true)
const objectModel = 'User'
const objToAdd = ref('')
const objToAdd2 = ref('')
const objToRemove = ref({})
const permissionsLoaded = ref(false)
const router = useRouter()
const route = useRoute()
const toast = useToast()
const user = ref([])
const userActivities = ref([])
const userEvents = ref([])
const userMails = ref([])
const userVMs = ref([])
const passwordForm = reactive({
  password: null,
  password_confirmation: null,
})

/* PAGINATION ONLY */
const {
  childComponents,
  loadedTabs,
  handlePaginationChanged,
  handleSortOrderChanged,
  handleDeleteObject,
  handleSearch,
  handleTabChanged,
} = usePaginationChild({
  children: [
    {
      name: 'activities',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'timestamp',
      sortDirection: 'desc',
      fetchData: fetchUserActivities,
    },
    {
      name: 'events',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'name',
      sortDirection: 'asc',
      searchField: null,
      searchValue: null,
      fetchData: fetchUserEvents,
    },
    {
      name: 'guacamoles',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'name',
      sortDirection: 'asc',
      searchField: null,
      searchValue: null,
      fetchData: fetchUserGuacamole,
    },
    {
      name: 'mails',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'createdAt',
      sortDirection: 'desc',
      fetchData: fetchUserMails,
    },
    {
      name: 'vms',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'name',
      sortDirection: 'asc',
      searchField: null,
      searchValue: null,
      fetchData: fetchUserVMs,
    },
  ],
  fetchArgs: () => [route.params.id],
  modals,
  objToRemove,
  route,
})
/**/

const vmFields = vmSearchBarFields()
const guacamoleFields = guacamoleSearchBarFields({ exclude: ['userId'] })
const eventFields = eventSearchBarFields()

async function addRole(roleKey) {
  try {
    await backend.users.addRole(route.params.id, roleKey)
    fetchUser(route.params.id)
    toast.success(
      t('common.addSuccess', { entity: t('objectTypes.role.singular') }),
    )
  } catch (error) {
    toast.error(
      `${t('common.addError', { entity: t('objectTypes.role.singular') })}\n${error.response?.data?.detail}`,
    )
  } finally {
    resetSearchComponent()
  }
}

async function addGuacamole(userId, name, objectId) {
  try {
    await backend.guacamole.create({
      name,
      userId,
      connection_profile: objectId,
    })
    fetchUserGuacamole(userId)
    useMainStore().fetchPermissions()
    toast.success(
      t('common.addSuccess', { entity: t('objectTypes.guacamole.singular') }),
    )
  } catch (error) {
    toast.error(
      `${t('common.addError', { entity: t('objectTypes.guacamole.singular') })}\n${error.response?.data?.detail}`,
    )
  } finally {
    resetSearchComponent()
  }
}

async function deleteUser(userId) {
  try {
    user.value = await backend.users.delete(userId)
    if (user.value === undefined) {
      throw 'error'
    }
    router.push({ path: `/users` })
    toast.success(
      t('common.deleteSuccess', { entity: t('objectTypes.user.singular') }),
    )
  } catch (error) {
    fetchUser(route.params.id)
    toast.error(
      `${t('common.deleteError', { entity: t('objectTypes.user.singular') })}\n${error.response?.data?.detail}`,
    )
  }
}

async function deleteUserRole(userId, roleKey) {
  try {
    const newRoles = user.value.roles.filter((object) => {
      return object.key !== roleKey
    })
    await backend.users.updateRoles(userId, newRoles)
    fetchUser(userId)
    toast.success(
      t('common.removeSuccess', { entity: t('objectTypes.role.singular') }),
    )
  } catch (error) {
    toast.error(
      `${t('common.removeError', { entity: t('objectTypes.role.singular') })}\n${error.response?.data?.detail}`,
    )
  }
}

async function deleteConnection(id) {
  try {
    await backend.guacamole.delete(id)
    toast.success(
      t('common.deleteSuccess', {
        entity: t('objectTypes.guacamole.singular'),
      }),
    )
  } catch (error) {
    toast.error(
      `${t('common.deleteError', { entity: t('objectTypes.guacamole.singular') })}\n` +
        error?.response?.data?.detail,
    )
  } finally {
    resetSearchComponent()
    await fetchUserGuacamole(route.params.id)
  }
}

async function fetchUser(userId) {
  try {
    dataLoading.value = true

    if (userId === SYSTEM_USER_ID) {
      throw 'error'
    }
    await backend.users.get(userId).then(async (response) => {
      if (response.status === 'deleted') {
        throw 'deleted'
      }
      user.value = response
      await resolveFieldFromLookup(user.value, [
        { from: 'createdById', to: 'createdBy', keyspace: 'users' },
        { from: 'updatedById', to: 'updatedBy', keyspace: 'users' },
      ])
    })
  } catch (error) {
    toast.warning(
      t('common.notFound', { entity: t('objectTypes.user.singular') }),
    )
    router.push({ path: `/users`, replace: true })
  } finally {
    dataLoading.value = false
  }
}

async function fetchUserActivities() {
  try {
    dataLoading.value = true

    await backend.activities
      .list({
        page: childComponents.value.find(
          (component) => component.name === 'activities',
        )?.currentPage,
        limit: childComponents.value.find(
          (component) => component.name === 'activities',
        )?.perPage,
        sort_by: childComponents.value.find(
          (component) => component.name === 'activities',
        )?.sortColumnKey,
        sort_order: childComponents.value.find(
          (component) => component.name === 'activities',
        )?.sortDirection,
        search_field: 'requestUser',
        search_value: route.params.id,
      })
      .then((response) => {
        userActivities.value = response.items
        userActivities.value.count = response.pageDetails.totalCount
      })
  } catch (error) {
    toast.error(
      `${t('common.loadErrorPlural', { entities: t('objectTypes.activity.plural') })}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  } finally {
    dataLoading.value = false
  }
}

async function fetchUserEvents() {
  try {
    dataLoading.value = true

    const eventsComponent = childComponents.value.find(
      (component) => component.name === 'events',
    )
    await backend.users
      .getEvents(route.params.id, {
        page: eventsComponent?.currentPage,
        limit: eventsComponent?.perPage,
        sort_by: eventsComponent?.sortColumnKey,
        sort_order: eventsComponent?.sortDirection,
        search_field: eventsComponent?.searchField,
        search_value: eventsComponent?.searchValue,
      })
      .then((response) => {
        userEvents.value = response.items
        userEvents.value.count = response.pageDetails.totalCount
        resolveFieldFromLookup(userEvents.value, [
          { from: 'course', to: 'courseName', keyspace: 'courses' },
          { from: 'role_ids', to: 'roleName', keyspace: 'roles' },
          { from: 'status', to: 'statusName', keyspace: 'eventStatus' },
        ])
      })
  } catch (error) {
    toast.error(
      `${t('common.loadErrorPlural', { entities: t('objectTypes.event.plural') })}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  } finally {
    dataLoading.value = false
  }
}

async function fetchUserGuacamole() {
  try {
    dataLoading.value = true

    if (isInitial.value) {
      backend.connections.dropdownVMs().then(async (response) => {
        connections.value = response
        await resolveFieldFromLookup(connections.value, [
          {
            from: 'objectId',
            to: 'label',
            keyspace: 'vms',
            formatter: (obj) => ({
              label: connectionProfileLabelFormatter(
                obj,
                obj.protocol,
                obj.username,
                obj.label,
                obj.port,
              ),
            }),
          },
        ])
      })
      isInitial.value = false
    }

    const guacamolesComponent = childComponents.value.find(
      (component) => component.name === 'guacamoles',
    )
    await backend.users
      .getGuacamoles(route.params.id, {
        page: guacamolesComponent?.currentPage,
        limit: guacamolesComponent?.perPage,
        sort_by: guacamolesComponent?.sortColumnKey,
        sort_order: guacamolesComponent?.sortDirection,
        search_field: guacamolesComponent?.searchField,
        search_value: guacamolesComponent?.searchValue,
      })
      .then(async (response) => {
        user.value.guacamoles = response.items
        user.value.guacamolesCount = response.pageDetails.totalCount

        user.value.guacamoles.forEach((x) => {
          x.xm = x.vms[0].id
        })

        await resolveFieldFromLookup(user.value.guacamoles, [
          { from: 'createdById', to: 'createdBy', keyspace: 'users' },
          {
            from: 'xm',
            to: 'vm',
            keyspace: 'vms',
          },
        ])
      })
  } catch (error) {
    toast.warning(
      t('common.notFound', { entity: t('objectTypes.guacamole.singular') }),
    )
  } finally {
    dataLoading.value = false
  }
}

async function fetchUserMails() {
  try {
    dataLoading.value = true

    await backend.mails
      .listByUser(user.value.email ?? 'XXXXXXXXX-fixme', {
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
        userMails.value = response.items
        userMails.value.count = response.pageDetails.totalCount
      })
  } catch (error) {
    toast.error(
      `${t('common.loadErrorPlural', { entities: t('objectTypes.mail.plural') })}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  } finally {
    dataLoading.value = false
  }
}

async function fetchUserVMs() {
  try {
    dataLoading.value = true

    const vmsComponent = childComponents.value.find(
      (component) => component.name === 'vms',
    )
    await backend.users
      .getVMs(route.params.id, {
        page: vmsComponent?.currentPage,
        limit: vmsComponent?.perPage,
        sort_by: vmsComponent?.sortColumnKey,
        sort_order: vmsComponent?.sortDirection,
        search_field: vmsComponent?.searchField,
        search_value: vmsComponent?.searchValue,
      })
      .then(async (response) => {
        userVMs.value = response.items
        userVMs.value.count = response.pageDetails.totalCount
      })
  } catch (error) {
    toast.error(
      `${t('common.loadErrorPlural', { entities: t('objectTypes.virtualMachine.plural') })}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
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

async function updateStatus(userId, status) {
  try {
    await backend.users.update(userId, {
      status: status == 'Banned' ? 'Active' : 'Banned',
    })
    toast.success(
      status == 'Banned'
        ? t('common.unlockSuccess', { entity: t('objectTypes.user.singular') })
        : t('common.lockSuccess', { entity: t('objectTypes.user.singular') }),
    )
  } catch (error) {
    toast.error(
      `${
        status == 'Banned'
          ? t('common.unlockError', { entity: t('objectTypes.user.singular') })
          : t('common.lockError', { entity: t('objectTypes.user.singular') })
      }\n${error.response?.data?.detail}`,
    )
  }
  fetchUser(route.params.id)
}

const resetSearchComponent = () => {
  objToAdd.value = null
  objToAdd2.value = null
}

const userLocaleOptions = getUserLocaleOptions(t)

const userEdit = (userId) => {
  router.push({ path: `${userId}/edit` })
}

async function setPassword(id, passwordForm) {
  try {
    await backend.users.setPassword(
      id,
      passwordForm.password,
      passwordForm.password_confirmation,
    )
    toast.success(t('common.setSuccess', { entity: t('common.password') }))
  } catch (error) {
    toast.error(
      `${t('common.setError', { entity: t('common.password') })}\n${error.response?.data?.detail}`,
    )
  } finally {
    resetSetPasswordForm()
  }
}

const resetSetPasswordForm = () => {
  modals.setPassword.value = false
  passwordForm.password = null
  passwordForm.password_confirmation = null
}

const userDeleteEnabled = computed(() => {
  if (!user?.value?.id) {
    return false
  }
  if (mainStore.getUserId === route.params.id) {
    return false
  }
  return true
})

const userLockEnabled = computed(() => {
  if (!user?.value?.id) {
    return false
  }
  return true
})

const userEditEnabled = computed(() => {
  if (!user?.value?.id) {
    return false
  }
  // forbid change of external accounts
  if (user?.value?.user_type === 'external') {
    return false
  }
  return true
})

const userPasswordSetEnabled = computed(() => {
  if (!user?.value?.id) {
    return false
  }
  // forbid change of external accounts
  if (user?.value?.user_type === 'external') {
    return false
  }
  return true
})

const userSetPasswordSubmitTooltip = computed(() => {
  if (
    passwordForm.password == null ||
    passwordForm.password_confirmation == null
  ) {
    return undefined
  } else if (passwordForm.password != passwordForm.password_confirmation) {
    return t('views.users.detail.passwordsMismatch')
  }
  return undefined
})

const userSetPasswordSubmitDisabled = computed(() => {
  if (
    passwordForm.password == null ||
    passwordForm.password_confirmation == null
  ) {
    return true
  } else if (passwordForm.password != passwordForm.password_confirmation) {
    return true
  }
  return false
})

const buttonsEvents = computed(() => {
  if (permissionRefs.canReadEvents) return ['view']
  return []
})

const buttonsGuacamoles = computed(() => {
  if (permissionRefs.canDeleteGuacamoles) return ['view', 'delete']
  return ['view']
})

const viewRole = async (obj, model) => {
  const test = await backend.roles.list({
    search_field: 'key',
    search_value: obj.key,
  })
  if (test?.items[0]?.id)
    return router.push({ path: `/roles/${test.items[0].id}` })
  return null
}

const userAuthBackendTooltip = (authBackend) => {
  switch (authBackend.toLowerCase()) {
    case 'internal':
      return t('views.users.detail.authInternal')
    case 'external':
      return t('views.users.detail.authExternal')
  }
  return undefined
}

onMounted(async () => {
  fetchUser(route.params.id)
  await checkObjectPermissions('users', route.params.id, permissionRefs, [
    {
      key: 'canReadPermissions',
      objectType: 'object_permissions',
      objectPermission: 'read',
      objectPath: `/${route.params.id}`,
    },
    {
      key: 'canCreateGuacamoles',
      objectType: 'guacamoles',
      objectPermission: 'create',
      objectPath: '/*',
    },
    {
      key: 'canReadActivities',
      objectType: 'activities',
      objectPermission: 'read',
      objectPath: '/*',
    },
    {
      key: 'canReadEvents',
      objectType: 'events',
      objectPermission: 'read',
      objectPath: '/*',
    },
    {
      key: 'canDeleteGuacamoles',
      objectType: 'guacamoles',
      objectPermission: 'delete',
      objectPath: '/*',
    },
    {
      key: 'canReadMails',
      objectType: 'mails',
      objectPermission: 'read',
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
  ])

  permissionsLoaded.value = true
})
</script>

<template>
  <!-- Modal: Add user role association -->
  <SearchModal
    v-model="modals.addUserRole.value"
    :fetch-data="backend.roles.search"
    :icon="mdiAccountMultipleOutline"
    :label="$t('views.users.detail.searchRoleLabel')"
    :title="$t('views.users.detail.assignRoleTitle')"
    return-attribute="key"
    @submitted="addRole"
  />

  <!-- Modal: Add connection for user -->
  <CardBoxModal
    v-model="modals.addUserGuacamole.value"
    form
    :title="$t('views.users.detail.addConnectionTitle')"
    button="success"
    has-cancel
    :button-label="$t('common.add')"
    @cancel="resetSearchComponent"
    @form-submitted="addGuacamole(user.id, objToAdd, objToAdd2)"
  >
    <FormField
      :label="$t('common.name')"
      :tooltip="$t('views.users.detail.connectionNameTooltip')"
      :help="$t('views.users.detail.connectionNameHelp')"
    >
      <FormControl
        v-model="objToAdd"
        :icon="mdiRename"
        :placeholder="$t('views.users.detail.connectionNamePlaceholder')"
        required
        @set-ref="
          (ref) => {
            autoFocusInputRef = ref
          }
        "
      />
    </FormField>

    <FormField
      :label="$t('views.users.detail.connectionTemplate')"
      :tooltip="$t('views.users.detail.connectionTemplateTooltip')"
      :help="$t('views.users.detail.connectionTemplateHelp')"
    >
      <FormControl
        v-model="objToAdd2"
        :icon="mdiMonitor"
        :options="connections"
        required
      />
    </FormField>
  </CardBoxModal>

  <!-- Modal: Lock/Unlock user -->
  <CardBoxModal
    v-model="modals.lockUser.value"
    form
    :title="$t('views.users.detail.confirmActionTitle')"
    button="warning"
    has-cancel
    :button-label="
      user?.status == 'Banned'
        ? $t('views.users.detail.unlock')
        : $t('views.users.detail.lock')
    "
    @form-submitted="updateStatus(user.id, user.status)"
  >
    <p>
      {{
        user?.status == 'Banned'
          ? $t('views.users.detail.userWillBeUnlocked')
          : $t('views.users.detail.userWillBeLocked')
      }}
    </p>

    <p>
      <b>{{ user?.name }} ({{ user?.username }}) &lt;{{ user?.email }}></b>
    </p>

    <p v-if="user?.status == 'Banned'">
      {{ $t('views.users.detail.unlockInfo') }}
    </p>

    <p v-else>
      {{ $t('views.users.detail.lockInfo') }}
    </p>
    {{ $t('views.users.detail.areYouSure') }}
  </CardBoxModal>

  <!-- Modal: Delete user -->
  <CardBoxDeleteUserModal
    v-model="modals.deleteUser.value"
    :checkvalue="user?.username"
    :object="user"
    @form-submitted="deleteUser(user?.id)"
  />

  <!-- Modal: Delete user role association -->
  <CardBoxDeleteRelationModal
    v-model="modals.deleteUserRole.value"
    :parent-object="user.username"
    :related-object="objToRemove.name"
    :checkvalue="$t('views.users.detail.confirmationCheckvalue')"
    @form-submitted="deleteUserRole(user.id, objToRemove.key)"
  />

  <!-- Modal: Delete Connection -->
  <CardBoxDeleteModal
    v-model="modals.deleteGuacamoles.value"
    :name="objToRemove.name"
    :checkvalue="objToRemove.name"
    @form-submitted="deleteConnection(objToRemove.id)"
  />

  <!-- Modal: Set user password -->
  <CardBoxModal
    v-model="modals.setPassword.value"
    form
    has-search
    :has-button="false"
    :title="$t('views.users.detail.setPasswordTitle')"
    @cancel="resetSetPasswordForm()"
  >
    <p>{{ $t('views.users.detail.userWillBeEdited') }}</p>

    <p>
      <b>{{ user?.name }} ({{ user?.username }}) &lt;{{ user?.email }}></b>
    </p>

    <BaseDivider />

    <FormField
      :label="$t('views.users.detail.newPassword')"
      :help="$t('views.users.form.required')"
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
      :label="$t('views.users.detail.newPasswordConfirm')"
      :help="$t('views.users.form.required')"
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

    <BaseButtons>
      <BaseButton
        v-tooltip="userSetPasswordSubmitTooltip"
        :label="$t('views.users.detail.setBtn')"
        color="success"
        type="submit"
        :disabled="userSetPasswordSubmitDisabled"
        @click="setPassword(user.id, passwordForm)"
      />

      <BaseButton
        :label="$t('common.cancel')"
        color="success"
        outline
        @click="resetSetPasswordForm()"
      />
    </BaseButtons>
  </CardBoxModal>

  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiAccount"
        :title="
          user?.name ? user?.name + ' (' + user?.username + ')' : 'Loading...'
        "
        :object-model="$t('objectTypes.user.singular')"
        main
        docs-path="/docs/usage/openvle/access-control/users/"
      >
        <BaseButtons type="justify-start lg:justify-end">
          <PillTag
            v-if="user.id"
            v-tooltip="userAuthBackendTooltip(user.user_type)"
            :icon="userAuthBackendIcon(user.user_type)"
            :color="authBackendColorUser(user.user_type)"
            :disabled="true"
          />

          <BaseButton
            v-if="permissionRefs.canEdit && userPasswordSetEnabled"
            v-tooltip="
              userPasswordSetEnabled
                ? undefined
                : $t('views.users.detail.externalAccountDisabled')
            "
            :disabled="!userPasswordSetEnabled"
            target="_blank"
            :icon="mdiKey"
            :label="$t('views.users.detail.setPasswordBtn')"
            color="warning"
            rounded-full
            small
            @click="showModal('setPassword')"
          />

          <BaseButton
            v-if="permissionRefs.canEdit"
            :disabled="!userLockEnabled"
            target="_blank"
            :icon="
              user?.status == 'Banned' ? mdiAccountLockOpen : mdiAccountLock
            "
            :label="
              user?.status == 'Banned'
                ? $t('views.users.detail.unlock')
                : $t('views.users.detail.lock')
            "
            color="warning"
            rounded-full
            small
            @click="showModal('lockUser')"
          />

          <BaseButton
            v-if="permissionRefs.canEdit && userEditEnabled"
            v-tooltip="
              userEditEnabled
                ? undefined
                : $t('views.users.detail.externalAccountDisabled')
            "
            :disabled="!userEditEnabled"
            target="_blank"
            :icon="mdiPencil"
            :label="$t('common.edit')"
            color="contrast"
            rounded-full
            small
            @click="userEdit(user.id)"
          />

          <BaseButton
            v-if="permissionRefs.canDelete"
            target="_blank"
            :icon="mdiDelete"
            :label="$t('common.delete')"
            color="danger"
            rounded-full
            small
            :disabled="!userDeleteEnabled"
            @click="showModal('deleteUser')"
          />
        </BaseButtons>
      </SectionTitleLineWithButton>

      <CardBox>
        <BaseTabs v-if="permissionsLoaded" @tab-changed="handleTabChanged">
          <BaseTab id="user" :title="$t('objectTypes.user.singular')">
            <FormField>
              <FormField :label="$t('views.users.form.username')">
                <FormControl
                  v-model="user.username"
                  :icon="mdiAccount"
                  disabled
                />
              </FormField>

              <FormField :label="$t('views.users.form.emailAddress')">
                <FormControl
                  v-model="user.email"
                  type="email"
                  :icon="mdiMail"
                  disabled
                />
              </FormField>
            </FormField>

            <FormField>
              <FormField :label="$t('common.name')">
                <FormControl
                  v-model="user.name"
                  :icon="mdiAccountOutline"
                  :placeholder="$t('common.name')"
                  disabled
                />
              </FormField>
            </FormField>

            <FormField>
              <FormField :label="$t('views.users.detail.accountStatus')">
                <FormControl
                  :model-value="userStatusLabel(user.status)"
                  :icon="mdiAccountQuestion"
                  disabled
                />
              </FormField>

              <FormField :label="$t('views.users.form.language')">
                <FormControl
                  v-model="user.locale"
                  :icon="mdiWebBox"
                  :options="userLocaleOptions"
                  disabled
                />
              </FormField>
            </FormField>

            <ObjectMetadataDisplay
              v-if="loadedTabs.has('user') && user.id"
              :object="user"
              :object-type="objectModel"
              :object-id="route.params.id"
              :can-edit="permissionRefs.canEdit"
              :tags-help="$t('views.users.detail.tagsHelp')"
            />
          </BaseTab>

          <BaseTab
            id="roles-permissions"
            :title="$t('views.users.detail.rolesAndPermissions')"
          >
            <SectionTitleLineWithButton
              :icon="mdiAccountMultiple"
              :title="$t('objectTypes.role.plural')"
            >
              <BaseButton
                v-if="permissionRefs.canEdit"
                :icon="mdiPlus"
                color="success"
                rounded-full
                small
                @click="showModal('addUserRole')"
              />
            </SectionTitleLineWithButton>

            <table>
              <tbody>
                <tr v-for="role in user.roles" :key="role.key">
                  <td>{{ role.name }}</td>

                  <td>{{ role.key }}</td>

                  <td
                    v-if="permissionRefs.canEdit"
                    class="before:hidden lg:w-1 whitespace-nowrap"
                  >
                    <BaseButton
                      color="info"
                      :icon="mdiEye"
                      class="mr-2"
                      small
                      @click="viewRole(role)"
                    />

                    <BaseButton
                      color="danger"
                      :icon="mdiTrashCan"
                      small
                      @click="showModal('deleteUserRole', role)"
                    />
                  </td>
                </tr>
              </tbody>
            </table>

            <!-- Directly assigned permissions -->
            <template v-if="permissionRefs.canReadObjectPermissions">
              <BaseDivider />

              <SectionTitleLineWithButton
                :icon="mdiKey"
                :title="$t('views.users.detail.directPermissionsTitle')"
              />

              <p class="text-sm text-gray-500 dark:text-slate-400 mb-4">
                {{ $t('views.users.detail.directPermissionsDescription') }}
              </p>

              <PermissionsMatrix
                v-if="loadedTabs.has('roles-permissions')"
                :entity-id="route.params.id"
                :entity-type="objectModel"
              />
            </template>
          </BaseTab>

          <BaseTab id="vms" :title="$t('objectTypes.virtualMachine.plural')">
            <SectionTitleLineWithButton
              :icon="mdiMonitor"
              :title="$t('objectTypes.virtualMachine.plural')"
              :reload="fetchUserVMs"
            />

            <BaseTable
              v-if="userVMs"
              :current-page="
                childComponents.find((component) => component.name === 'vms')
                  ?.currentPage
              "
              :per-page="
                childComponents.find((component) => component.name === 'vms')
                  ?.perPage
              "
              :items-total="userVMs.count"
              :data="userVMs"
              :sort-column-key="
                childComponents.find((component) => component.name === 'vms')
                  ?.sortColumnKey
              "
              :sort-direction="
                childComponents.find((component) => component.name === 'vms')
                  ?.sortDirection
              "
              :loading="dataLoading"
              object-model="vms"
              :buttons="['view']"
              :search-bar-fields="vmFields"
              :search-bar-max-filters="1"
              search-bar-query-key="filter-vms"
              :columns="[
                {
                  label: null,
                  key: 'event',
                  sortable: true,
                  tooltip: (value) => eventCreateTypeTooltip(value),
                  color: createTypeColorConnection,
                  icon: (value) => eventCreateTypeIcon(value),
                  formatter: ['', ''],
                },
                {
                  label: $t('common.name'),
                  key: 'name',
                },
                {
                  label: $t('common.status'),
                  key: 'status',
                  color: statusColorVM,
                  icon: (value) => vmStatusIcon(value),
                },
              ]"
              @delete-object="handleDeleteObject"
              @sort-order-changed="handleSortOrderChanged"
              @pagination-changed="handlePaginationChanged"
              @search-triggered="handleSearch"
            />
          </BaseTab>

          <BaseTab id="guacamoles" :title="$t('objectTypes.guacamole.plural')">
            <SectionTitleLineWithButton
              :icon="mdiRemoteDesktop"
              :title="$t('objectTypes.guacamole.plural')"
              :reload="fetchUserGuacamole"
            >
              <BaseButton
                v-if="permissionRefs.canCreateGuacamoles"
                :icon="mdiPlus"
                color="success"
                rounded-full
                small
                @click="showModal('addUserGuacamole')"
              />
            </SectionTitleLineWithButton>

            <BaseTable
              v-if="loadedTabs.has('guacamoles')"
              :current-page="
                childComponents.find(
                  (component) => component.name === 'guacamoles',
                )?.currentPage
              "
              :per-page="
                childComponents.find(
                  (component) => component.name === 'guacamoles',
                )?.perPage
              "
              :items-total="user.guacamolesCount"
              :data="user.guacamoles"
              :sort-column-key="
                childComponents.find(
                  (component) => component.name === 'guacamoles',
                )?.sortColumnKey
              "
              :sort-direction="
                childComponents.find(
                  (component) => component.name === 'guacamoles',
                )?.sortDirection
              "
              :loading="dataLoading"
              object-model="guacamoles"
              :buttons="buttonsGuacamoles"
              :search-bar-fields="guacamoleFields"
              :search-bar-max-filters="1"
              search-bar-query-key="filter-guacamoles"
              :columns="[
                {
                  label: null,
                  key: 'eventId',
                  sortable: true,
                  tooltip: (value) => eventCreateTypeTooltip(value),
                  color: createTypeColorConnection,
                  icon: (value) => eventCreateTypeIcon(value),
                  formatter: ['', ''],
                  width: '70px',
                },
                {
                  label: $t('common.name'),
                  key: 'name',
                  width: '300px',
                },
                {
                  label: $t('objectTypes.virtualMachine.singular'),
                  key: 'vm',
                  sortable: false,
                  width: '190px',
                },
                {
                  label: $t('views.users.detail.createdBy'),
                  key: 'createdBy',
                  sortKey: 'createdById',
                  width: '110px',
                },
              ]"
              @delete-object="handleDeleteObject"
              @sort-order-changed="handleSortOrderChanged"
              @pagination-changed="handlePaginationChanged"
              @search-triggered="handleSearch"
            />
          </BaseTab>

          <BaseTab id="events" :title="$t('objectTypes.event.plural')">
            <SectionTitleLineWithButton
              :icon="mdiCalendarOutline"
              :title="$t('objectTypes.event.plural')"
              :reload="fetchUserEvents"
            />

            <BaseTable
              v-if="userEvents"
              :current-page="
                childComponents.find((component) => component.name === 'events')
                  ?.currentPage
              "
              :per-page="
                childComponents.find((component) => component.name === 'events')
                  ?.perPage
              "
              :items-total="userEvents.count"
              :data="userEvents"
              :sort-column-key="
                childComponents.find((component) => component.name === 'events')
                  ?.sortColumnKey
              "
              :sort-direction="
                childComponents.find((component) => component.name === 'events')
                  ?.sortDirection
              "
              :loading="dataLoading"
              object-model="events"
              :buttons="buttonsEvents"
              :created-column-enabled="false"
              :search-bar-fields="eventFields"
              :search-bar-max-filters="1"
              search-bar-query-key="filter-events"
              :columns="[
                { label: $t('common.name'), key: 'name' },
                {
                  label: $t('views.users.detail.slug'),
                  key: 'slug',
                },
                {
                  label: $t('views.users.detail.course'),
                  key: 'courseName',
                  sortKey: 'course',
                },
                {
                  label: $t('common.status'),
                  key: 'statusName',
                  sortKey: 'status',
                  color: statusColorEvent,
                  icon: (value) => eventStatusIcon(value),
                },
                {
                  label: $t('views.users.detail.role'),
                  key: 'roleName',
                  sortKey: 'role_ids',
                  sortable: false,
                },
              ]"
              @sort-order-changed="handleSortOrderChanged"
              @pagination-changed="handlePaginationChanged"
              @search-triggered="handleSearch"
            />
          </BaseTab>

          <BaseTab
            v-if="permissionRefs.canReadMails"
            id="mails"
            :title="$t('objectTypes.mail.plural')"
          >
            <SectionTitleLineWithButton
              :icon="mdiMailboxOutline"
              :title="$t('objectTypes.mail.plural')"
              :reload="fetchUserMails"
            />

            <BaseTable
              v-if="userMails"
              :current-page="
                childComponents.find((component) => component.name === 'mails')
                  ?.currentPage
              "
              :per-page="
                childComponents.find((component) => component.name === 'mails')
                  ?.perPage
              "
              :items-total="userMails.count"
              :data="userMails"
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
                  label: $t('views.users.detail.subject'),
                  key: 'subject',
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
            v-if="permissionRefs.canReadActivities"
            id="activities"
            :title="$t('objectTypes.activity.plural')"
          >
            <SectionTitleLineWithButton
              :icon="mdiTextBox"
              :title="$t('objectTypes.activity.plural')"
              :reload="fetchUserActivities"
            />

            <BaseTable
              v-if="userActivities"
              :current-page="
                childComponents.find(
                  (component) => component.name === 'activities',
                )?.currentPage
              "
              :per-page="
                childComponents.find(
                  (component) => component.name === 'activities',
                )?.perPage
              "
              :items-total="userActivities.count"
              :data="userActivities"
              created-column-key="timestamp"
              :sort-column-key="
                childComponents.find(
                  (component) => component.name === 'activities',
                )?.sortColumnKey
              "
              :sort-direction="
                childComponents.find(
                  (component) => component.name === 'activities',
                )?.sortDirection
              "
              :loading="dataLoading"
              object-model="activities"
              :buttons="['view']"
              :columns="[
                {
                  label: $t('views.users.detail.ipAddress'),
                  key: 'requestClientIP',
                },
                {
                  label: $t('views.users.detail.method'),
                  key: 'requestMethod',
                  color: responseMethodColorActivity,
                  icon: (value) => methodHTTPIcon(value),
                },
                {
                  label: $t('common.url'),
                  key: 'requestUrl',
                },
                {
                  label: $t('common.response'),
                  key: 'responseCode',
                  color: responseCodeColorActivity,
                  icon: (value) => responseCodeHTTPIcon(value),
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
              v-if="user.id && loadedTabs.has('changelogs')"
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
