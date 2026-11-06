<script setup>
import {
  mdiApplicationBrackets,
  mdiCalendarOutline,
  mdiContentCopy,
  mdiDelete,
  mdiInformation,
  mdiPencil,
  mdiPlus,
  mdiRename,
  mdiSchoolOutline,
  mdiTextBox,
  mdiVectorArrangeAbove,
} from '@mdi/js'
import { computed, onMounted, ref, toRaw, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
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
import SearchModal from '@/components/SearchModal.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import { templateSearchBarFields } from '@/components/Tables/searchBarFieldConfigs'
import TableChangelogs from '@/components/Tables/TableChangelogs.vue'
import TablePermissions from '@/components/Tables/TablePermissions.vue'
import { FIELD_LIMITS } from '@/config/fieldLimits'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { useMainStore } from '@/stores/main'
import {
  checkObjectPermissions,
  resolveFieldFromLookup,
  usePermissionRefs,
} from '@/utils/dataUtils'
import { eventStatusIcon } from '@/utils/icons'
import { statusColorEvent } from '@/utils/objectColors'
import { usePaginationChild } from '@/utils/pagination'

const { t } = useI18n()
const mainStore = useMainStore()
const permissionRefs = usePermissionRefs()
const moodleEnabled = computed(() => !!mainStore.settings?.moodle?.enabled)

const modals = {
  addTemplate: ref(false),
  cloneCourse: ref(false),
  deleteCourse: ref(false),
  deleteTemplates: ref(false),
}
const clonedCourse = ref({})
const objectModel = 'Course'
const objToAdd = ref('')
const dataLoading = ref(true)
const objToRemove = ref({})
const permissionsLoaded = ref(false)
const router = useRouter()
const route = useRoute()
const toast = useToast()
const course = ref([])
const courseEvents = ref([])
const courseTemplates = ref([])

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
      name: 'events',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'name',
      sortDirection: 'asc',
      fetchData: fetchCourseEvents,
    },
    {
      name: 'templates',
      perPage: 10,
      currentPage: 1,
      sortColumnKey: 'name',
      sortDirection: 'asc',
      searchField: null,
      searchValue: null,
      fetchData: fetchCourseTemplates,
    },
  ],
  fetchArgs: () => [route.params.id],
  modals,
  objToRemove,
  route,
})
/**/

const templateFields = templateSearchBarFields()

async function addTemplate(templateId) {
  try {
    await backend.courses.addTemplate(route.params.id, templateId)
    fetchCourseTemplates(route.params.id)
    toast.success(
      t('common.addSuccess', { entity: t('objectTypes.template.singular') }),
    )
  } catch (error) {
    toast.error(
      t('common.addError', { entity: t('objectTypes.template.singular') }),
    )
  }
  objToAdd.value = ''
}

async function cloneCourse(course) {
  try {
    const newCourse = await backend.courses.create({
      name: course.name,
      description: course.description,
    })

    if (courseTemplates.value.length <= 0) {
      loadedTabs.add('templates')
      await fetchCourseTemplates(route.params.id)
    }

    for (const t of courseTemplates.value) {
      await backend.courses.addTemplate(newCourse.id, t.id)
    }

    toast.success(
      t('common.cloneSuccess', { entity: t('objectTypes.course.singular') }),
    )
    useMainStore().fetchPermissions()
    router.push({ path: `/courses/${newCourse.id}` })
  } catch (error) {
    toast.error(
      t('common.cloneError', { entity: t('objectTypes.course.singular') }),
    )
  }
}

const BLOCKING_EVENTS_LIMIT = 5
const blockingEvents = ref([])
const blockingEventsTotal = ref(0)

async function openDeleteCourseModal(courseObj) {
  objToRemove.value = courseObj
  blockingEvents.value = []
  blockingEventsTotal.value = 0
  backend.beginSilent()
  try {
    const result = await backend.events.list({
      page: 1,
      limit: BLOCKING_EVENTS_LIMIT,
      search_field: 'course',
      search_value: courseObj.id,
    })
    blockingEvents.value = result?.items ?? []
    blockingEventsTotal.value =
      result?.pageDetails?.totalCount ?? blockingEvents.value.length
  } catch {
    // Fail open: without the pre-check the backend 409 still blocks the delete
  } finally {
    backend.endSilent()
  }
  modals.deleteCourse.value = true
}

const blockingEventItems = computed(() => {
  const items = blockingEvents.value.map((event) => ({
    label: event.name ?? event.id,
  }))
  const more = blockingEventsTotal.value - blockingEvents.value.length
  if (more > 0) {
    items.push({
      label: t('views.courses.delete.moreEvents', { count: more }, more),
    })
  }
  return items
})

async function deleteCourse(courseId) {
  backend.beginSilent()
  try {
    await backend.courses.delete(courseId)
    router.push({ path: `/courses` })
    toast.success(
      t('common.deleteSuccess', { entity: t('objectTypes.course.singular') }),
    )
  } catch (error) {
    const errorCode = error?.response?.data?.error_code
    if (
      errorCode === 'OBJECT_IN_USE' ||
      errorCode === 'OBJECT_DELETE_INTEGRITY_ERROR'
    ) {
      toast.error(t('views.courses.delete.blockedError'), { timeout: 8400 })
    } else {
      const detail = String(error?.response?.data?.detail || '')
      toast.error(
        `${t('common.deleteError', { entity: t('objectTypes.course.singular') })}${detail ? '\n' + detail : ''}`,
      )
    }
  } finally {
    backend.endSilent()
  }
}

async function deleteTemplate(courseId, templateId) {
  try {
    await backend.courses.deleteTemplate(courseId, templateId)
    fetchCourseTemplates(route.params.id)
    toast.success(
      t('common.removeSuccess', { entity: t('objectTypes.template.singular') }),
    )
  } catch (error) {
    toast.error(
      t('common.removeError', { entity: t('objectTypes.template.singular') }),
    )
  }
}

async function fetchCourse(courseId) {
  try {
    dataLoading.value = true

    await backend.courses.get(courseId).then(async (response) => {
      course.value = response
      clonedCourse.value = structuredClone(toRaw(response))
      clonedCourse.value.name = ''
      await resolveFieldFromLookup(course.value, [
        { from: 'createdById', to: 'createdBy', keyspace: 'users' },
        {
          from: 'moodleCourseId',
          to: 'moodleCourse',
          keyspace: 'moodleCourses',
        },
        { from: 'updatedById', to: 'updatedBy', keyspace: 'users' },
      ])
    })
  } catch (error) {
    toast.warning(
      t('common.notFound', { entity: t('objectTypes.course.singular') }),
    )
    router.push({ path: `/courses`, replace: true })
  } finally {
    dataLoading.value = false
  }
}

async function fetchCourseEvents() {
  try {
    dataLoading.value = true

    const eventsComponent = childComponents.value.find(
      (component) => component.name === 'events',
    )
    await backend.events
      .list({
        page: eventsComponent?.currentPage,
        limit: eventsComponent?.perPage,
        sort_by: eventsComponent?.sortColumnKey,
        sort_order: eventsComponent?.sortDirection,
        search_field: 'course',
        search_value: route.params.id,
      })
      .then(async (response) => {
        courseEvents.value = response.items
        courseEvents.value.count = response.pageDetails.totalCount
        await resolveFieldFromLookup(courseEvents.value, [
          { from: 'status', to: 'statusName', keyspace: 'eventStatus' },
        ])
      })
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', { entities: t('objectTypes.event.plural') }),
    )
  } finally {
    dataLoading.value = false
  }
}

async function fetchCourseTemplates() {
  try {
    dataLoading.value = true

    const templatesComponent = childComponents.value.find(
      (component) => component.name === 'templates',
    )
    await backend.courses
      .getTemplates(route.params.id, {
        page: templatesComponent?.currentPage,
        limit: templatesComponent?.perPage,
        sort_by: templatesComponent?.sortColumnKey,
        sort_order: templatesComponent?.sortDirection,
        search_field: templatesComponent?.searchField,
        search_value: templatesComponent?.searchValue,
      })
      .then((response) => {
        courseTemplates.value = response.items
        courseTemplates.value.count = response.pageDetails.totalCount
      })
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', {
        entities: t('objectTypes.template.plural'),
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

const addEvent = (course) => {
  router.push({
    path: `/events/create`,
    query: {
      course: course.id,
    },
  })
}

const courseEdit = (courseId) => {
  router.push({ path: `/courses/${courseId}/edit` })
}

const buttonsTemplate = computed(() => {
  if (permissionRefs.canEdit) return ['view', 'delete']
  return ['view']
})

async function loadCourseAndPermissions(id) {
  await fetchCourse(id)

  await checkObjectPermissions(
    'courses',
    id,
    permissionRefs,
    [
      {
        key: 'canReadPermissions',
        objectType: 'object_permissions',
        objectPermission: 'read',
        objectPath: `/${id}`,
      },
      {
        key: 'canCreateEvents',
        objectType: 'events',
        objectPermission: 'create',
        objectPath: '/*',
      },
      {
        key: 'canReadEvents',
        objectType: 'events',
        objectPermission: 'read',
        objectPath: '/*',
      },
      {
        key: 'canReadTemplates',
        objectType: 'templates',
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
}

onMounted(async () => {
  await loadCourseAndPermissions(route.params.id)
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
      await loadCourseAndPermissions(newId)
    } finally {
      permissionsLoaded.value = true
      dataLoading.value = false
    }
  },
)
</script>

<template>
  <!-- Modal: Add Template to Course -->
  <SearchModal
    v-model="modals.addTemplate.value"
    :fetch-data="backend.templates.search"
    :icon="mdiVectorArrangeAbove"
    :label="$t('views.courses.detail.searchTemplate')"
    :title="$t('views.courses.detail.assignTemplate')"
    @submitted="addTemplate"
  />

  <!-- Modal: Clone course -->
  <CardBoxCloneModal
    v-model="modals.cloneCourse.value"
    :name="course.name"
    :checkvalue="course.name"
    @form-submitted="cloneCourse(clonedCourse)"
  >
    <NotificationBar :dismissable="false" color="info" :icon="mdiInformation">
      {{ $t('views.courses.detail.cloneNotice') }}
    </NotificationBar>

    <FormField
      :label="$t('views.courses.detail.cloneNameLabel')"
      :help="$t('views.courses.form.nameHelp')"
    >
      <FormControl
        v-model="clonedCourse.name"
        :icon="mdiRename"
        :maxlength="FIELD_LIMITS.course.name"
        :placeholder="$t('views.courses.form.namePlaceholder')"
        required
      />
    </FormField>
  </CardBoxCloneModal>

  <!-- Modal: Delete Course -->
  <CardBoxDeleteModal
    v-model="modals.deleteCourse.value"
    :name="course.name"
    :checkvalue="course.name"
    :blocked="blockingEventsTotal > 0"
    :info="
      blockingEventsTotal > 0 ? null : $t('views.courses.delete.cascadeInfo')
    "
    :warning="
      blockingEventsTotal > 0
        ? $t(
            'views.courses.delete.relatedWarning',
            { count: blockingEventsTotal },
            blockingEventsTotal,
          )
        : null
    "
    :related-items="blockingEventItems"
    :related-label="$t('views.courses.delete.relatedLabel')"
    :related-count="blockingEventsTotal"
    @form-submitted="deleteCourse(objToRemove.id)"
  />

  <!-- Modal: Delete Template from Course -->
  <CardBoxDeleteRelationModal
    v-model="modals.deleteTemplates.value"
    :parent-object="course.name"
    :related-object="objToRemove.name"
    :checkvalue="$t('common.confirmation')"
    @form-submitted="deleteTemplate(course.id, objToRemove.id)"
  />

  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiSchoolOutline"
        :title="course.name ? course.name : 'Loading...'"
        :object-model="$t('objectTypes.course.singular')"
        main
        docs-path="/docs/usage/openvle/courses/"
      >
        <BaseButtons type="justify-start lg:justify-end">
          <BaseButton
            v-if="course.id && permissionRefs.canCreate"
            :icon="mdiContentCopy"
            :label="$t('common.clone')"
            color="info"
            rounded-full
            small
            @click="showModal('cloneCourse', course.id)"
          />

          <BaseButton
            v-if="permissionRefs.canEdit"
            target="_blank"
            :icon="mdiPencil"
            :label="$t('common.edit')"
            color="contrast"
            rounded-full
            small
            @click="courseEdit(course.id)"
          />

          <BaseButton
            v-if="permissionRefs.canDelete"
            target="_blank"
            :icon="mdiDelete"
            :label="$t('common.delete')"
            color="danger"
            rounded-full
            small
            @click="openDeleteCourseModal(course)"
          />
        </BaseButtons>
      </SectionTitleLineWithButton>

      <CardBox>
        <BaseTabs v-if="permissionsLoaded" @tab-changed="handleTabChanged">
          <BaseTab id="course" :title="$t('objectTypes.course.singular')">
            <FormField
              :label="$t('common.name')"
              :help="$t('views.courses.form.nameHelp')"
            >
              <FormControl v-model="course.name" :icon="mdiRename" disabled />
            </FormField>

            <FormField
              :label="$t('common.description')"
              :help="$t('views.courses.form.descriptionHelp')"
            >
              <FormControl
                v-model="course.description"
                :icon="mdiTextBox"
                disabled
              />
            </FormField>

            <!-- Moodle course (feature-gated, read-only) -->
            <FormField
              v-if="moodleEnabled"
              :label="$t('views.courses.form.moodleCourse')"
            >
              <FormControl
                :model-value="
                  course.moodleCourse ||
                  $t('views.courses.detail.noMoodleCourse')
                "
                :icon="mdiSchoolOutline"
                disabled
              />
            </FormField>

            <ObjectMetadataDisplay
              v-if="loadedTabs.has('course') && course.id"
              :object="course"
              :object-type="objectModel"
              :object-id="route.params.id"
              :can-edit="permissionRefs.canEdit"
              :tags-help="$t('views.courses.detail.tagsHelp')"
            />
          </BaseTab>

          <BaseTab
            v-if="permissionRefs.canReadEvents"
            id="events"
            :title="$t('objectTypes.event.plural')"
          >
            <SectionTitleLineWithButton
              :icon="mdiCalendarOutline"
              :title="$t('objectTypes.event.plural')"
              :reload="fetchCourseEvents"
            >
              <BaseButton
                v-if="permissionRefs.canCreateEvents"
                :icon="mdiPlus"
                color="success"
                rounded-full
                small
                @click="addEvent(course)"
              />
            </SectionTitleLineWithButton>

            <BaseTable
              v-if="courseEvents"
              :current-page="
                childComponents.find((component) => component.name === 'events')
                  ?.currentPage
              "
              :per-page="
                childComponents.find((component) => component.name === 'events')
                  ?.perPage
              "
              :items-total="courseEvents.count"
              :data="courseEvents"
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
              :buttons="['view']"
              :columns="[
                { label: $t('common.name'), key: 'name' },
                {
                  label: $t('common.description'),
                  key: 'description',
                  markdown: true,
                },
                {
                  label: $t('common.status'),
                  key: 'statusName',
                  sortKey: 'status',
                  color: statusColorEvent,
                  icon: (value) => eventStatusIcon(value),
                },
              ]"
              @sort-order-changed="handleSortOrderChanged"
              @pagination-changed="handlePaginationChanged"
            />
          </BaseTab>

          <BaseTab id="templates" :title="$t('objectTypes.template.plural')">
            <SectionTitleLineWithButton
              :icon="mdiApplicationBrackets"
              :title="$t('objectTypes.template.plural')"
              :reload="fetchCourseTemplates"
            >
              <BaseButton
                v-if="permissionRefs.canEdit"
                :icon="mdiPlus"
                color="success"
                rounded-full
                small
                @click="showModal('addTemplate')"
              />
            </SectionTitleLineWithButton>

            <BaseTable
              v-if="loadedTabs.has('templates')"
              :current-page="
                childComponents.find(
                  (component) => component.name === 'templates',
                )?.currentPage
              "
              :per-page="
                childComponents.find(
                  (component) => component.name === 'templates',
                )?.perPage
              "
              :items-total="courseTemplates.count"
              :data="courseTemplates"
              :sort-column-key="
                childComponents.find(
                  (component) => component.name === 'templates',
                )?.sortColumnKey
              "
              :sort-direction="
                childComponents.find(
                  (component) => component.name === 'templates',
                )?.sortDirection
              "
              :loading="dataLoading"
              object-model="templates"
              :buttons="buttonsTemplate"
              :search-bar-fields="templateFields"
              :search-bar-max-filters="1"
              search-bar-query-key="filter-templates"
              :columns="[
                { label: $t('common.name'), key: 'name' },
                {
                  label: $t('common.description'),
                  key: 'description',
                  markdown: true,
                },
              ]"
              @delete-object="handleDeleteObject"
              @sort-order-changed="handleSortOrderChanged"
              @pagination-changed="handlePaginationChanged"
              @search-triggered="handleSearch"
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
              v-if="course.id && loadedTabs.has('changelogs')"
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
