import { computed, reactive, ref, watch } from 'vue'
import { useToast } from 'vue-toastification'

import backend from '@/services'
import { useMainStore } from '@/stores/main'

/**
 * Composable for event warning modals (rollout/stop).
 * Provides shared state and logic for event confirmation dialogs.
 *
 * @param {Object} options - Configuration options.
 * @param {import('vue').Ref<boolean>} options.modelValue - v-model for modal visibility.
 * @param {import('vue').Ref<Object>} options.object - The event object.
 * @param {Function} options.emit - Component emit function.
 * @param {Function} [options.onOpen] - Callback when modal opens, receives loadAllData function.
 * @returns {Object} Modal state and methods.
 */
export function useEventWarningModal(options = {}) {
  const { modelValue, object, emit, onOpen } = options

  const mainStore = useMainStore()
  const toast = useToast()

  // Reactive state
  const loading = ref(true)
  const loadError = ref(null)
  const modalVisible = ref(modelValue.value)

  const participants = reactive({
    total: 0,
    students: 0,
    teachers: 0,
  })

  // Computed from props
  const event = computed(() => object.value)

  /**
   * Handles form submission - emits confirmed and closes modal.
   */
  function onFormSubmit() {
    emit('confirmed', true)
    emit('update:modelValue', false)
  }

  /**
   * Closes the modal.
   */
  function closeModal() {
    modalVisible.value = false
  }

  // Participant counts
  const userStudentsCount = computed(() => participants.students || 0)
  const userTeachersCount = computed(() => participants.teachers || 0)
  const totalParticipantsCount = computed(() => participants.total || 0)
  const hasParticipants = computed(() => totalParticipantsCount.value > 0)

  /**
   * Generates text describing participant counts.
   */
  const textUsersCount = computed(() => {
    if (!hasParticipants.value) {
      return 'Keine Teilnehmende'
    }

    const students = userStudentsCount.value
    const teachers = userTeachersCount.value

    if (students > 0 && teachers > 0) {
      return `${students} Studierende, ${teachers} Lehrende`
    }

    if (teachers > 0 && students === 0) {
      return `${teachers} Lehrende`
    }

    if (students > 0 && teachers === 0) {
      return `${students} Studierende`
    }

    return 'Keine Teilnehmende'
  })

  /**
   * Calculates event duration from start to end date.
   */
  const duration = computed(() => {
    const start = event.value?.dateStart
      ? new Date(event.value.dateStart)
      : null
    const end = event.value?.dateEnd ? new Date(event.value.dateEnd) : null

    if (!start || isNaN(start.getTime())) return 'Ungültiges Datum'
    if (!end || isNaN(end.getTime())) return 'Unbegrenzt'

    const diffInMs = end.getTime() - start.getTime()
    const diffInDays = Math.ceil(diffInMs / (1000 * 60 * 60 * 24))

    return `${diffInDays} Tag${diffInDays === 1 ? '' : 'e'}`
  })

  /**
   * Calculates actual duration from start date until now.
   */
  const actualDuration = computed(() => {
    const start = event.value?.dateStart
      ? new Date(event.value.dateStart)
      : null
    const end = new Date()

    if (!start || isNaN(start.getTime())) return 'Ungültiges Datum'

    const diffInMs = end.getTime() - start.getTime()
    const diffInDays = Math.ceil(diffInMs / (1000 * 60 * 60 * 24))

    return `${diffInDays} Tag${diffInDays === 1 ? '' : 'e'}`
  })

  /**
   * Loads event participants (total, students, teachers).
   */
  async function loadEventParticipants() {
    // Load total participants
    const totalResponse = await backend.events.getUsers(event.value?.id, {
      page: 1,
      limit: 1,
    })
    participants.total = totalResponse.pageDetails.totalCount

    // Load students count
    const studentsResponse = await backend.events.getUsers(event.value?.id, {
      page: 1,
      limit: 1,
      search_field: 'role_id',
      search_value: mainStore?.settings?.roles?.students,
    })
    participants.students = studentsResponse.pageDetails.totalCount
    participants.teachers = participants.total - participants.students
  }

  /**
   * Loads all modal data. Can be extended via onOpen callback.
   *
   * @param {Function} [additionalLoaders] - Additional async loaders to run.
   */
  async function loadAllData(additionalLoaders = []) {
    loading.value = true
    loadError.value = null

    try {
      const loaders = [loadEventParticipants(), ...additionalLoaders]
      await Promise.all(loaders)
    } catch (error) {
      loadError.value =
        error?.response?.data?.detail || 'Daten konnten nicht geladen werden.'
      toast.error(loadError.value)
    } finally {
      loading.value = false
    }
  }

  // Watchers for v-model sync
  watch(
    () => modalVisible.value,
    (newVal) => {
      emit('update:modelValue', newVal)
      if (newVal && event.value?.id) {
        if (onOpen) {
          onOpen(loadAllData)
        } else {
          loadAllData()
        }
      }
    },
  )

  watch(
    () => modelValue.value,
    (newVal) => {
      modalVisible.value = newVal
    },
  )

  // Watch for object changes while modal is open
  watch(
    () => event.value?.id,
    (newId) => {
      if (modalVisible.value && newId) {
        if (onOpen) {
          onOpen(loadAllData)
        } else {
          loadAllData()
        }
      }
    },
  )

  return {
    // State
    loading,
    loadError,
    modalVisible,
    participants,
    event,

    // Computed
    userStudentsCount,
    userTeachersCount,
    totalParticipantsCount,
    hasParticipants,
    textUsersCount,
    duration,
    actualDuration,

    // Methods
    onFormSubmit,
    closeModal,
    loadAllData,
    loadEventParticipants,

    // Stores
    mainStore,
    toast,
  }
}
