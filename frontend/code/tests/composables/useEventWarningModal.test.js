import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick, ref } from 'vue'

import { useEventWarningModal } from '@/composables/useEventWarningModal'
import backend from '@/services'

// Mock vue-toastification
vi.mock('vue-toastification', () => ({
  useToast: () => ({
    error: vi.fn(),
    success: vi.fn(),
  }),
}))

// Mock mainStore
vi.mock('@/stores/main', () => ({
  useMainStore: () => ({
    settings: {
      roles: {
        students: 'student-role-id',
      },
      events: {
        create: {
          participants: {
            students: 1,
            teachers: 1,
          },
        },
      },
    },
  }),
}))

describe('useEventWarningModal', () => {
  let modelValue
  let object
  let emit

  beforeEach(() => {
    modelValue = ref(false)
    object = ref({
      id: 'event-123',
      name: 'Test Event',
      course: 'Test Course',
      courseId: 'course-456',
      dateStart: '2024-01-01T00:00:00Z',
      dateEnd: '2024-01-31T00:00:00Z',
    })
    emit = vi.fn()

    // Reset mocks
    vi.clearAllMocks()
  })

  describe('Initialization', () => {
    it('initializes with loading as true', () => {
      const { loading } = useEventWarningModal({ modelValue, object, emit })
      expect(loading.value).toBe(true)
    })

    it('initializes with modalVisible synced to modelValue', () => {
      modelValue.value = true
      const { modalVisible } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })
      expect(modalVisible.value).toBe(true)
    })

    it('initializes participants with zero values', () => {
      const { participants } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })
      expect(participants.total).toBe(0)
      expect(participants.students).toBe(0)
      expect(participants.teachers).toBe(0)
    })

    it('exposes event computed from object', () => {
      const { event } = useEventWarningModal({ modelValue, object, emit })
      expect(event.value.id).toBe('event-123')
      expect(event.value.name).toBe('Test Event')
    })
  })

  describe('onFormSubmit', () => {
    it('emits confirmed event with true', () => {
      const { onFormSubmit } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })

      onFormSubmit()

      expect(emit).toHaveBeenCalledWith('confirmed', true)
    })

    it('emits update:modelValue with false', () => {
      const { onFormSubmit } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })

      onFormSubmit()

      expect(emit).toHaveBeenCalledWith('update:modelValue', false)
    })
  })

  describe('closeModal', () => {
    it('sets modalVisible to false', () => {
      modelValue.value = true
      const { closeModal, modalVisible } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })

      closeModal()

      expect(modalVisible.value).toBe(false)
    })
  })

  describe('textUsersCount', () => {
    it('returns "Keine Teilnehmende" when no participants', () => {
      const { textUsersCount } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })
      expect(textUsersCount.value).toBe('Keine Teilnehmende')
    })

    it('returns student and teacher count when both exist', () => {
      const { textUsersCount, participants } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })

      participants.total = 5
      participants.students = 3
      participants.teachers = 2

      expect(textUsersCount.value).toBe('3 Studierende, 2 Lehrende')
    })

    it('returns only students when no teachers', () => {
      const { textUsersCount, participants } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })

      participants.total = 3
      participants.students = 3
      participants.teachers = 0

      expect(textUsersCount.value).toBe('3 Studierende')
    })

    it('returns only teachers when no students', () => {
      const { textUsersCount, participants } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })

      participants.total = 2
      participants.students = 0
      participants.teachers = 2

      expect(textUsersCount.value).toBe('2 Lehrende')
    })
  })

  describe('duration', () => {
    it('calculates duration in days', () => {
      object.value = {
        ...object.value,
        dateStart: '2024-01-01T00:00:00Z',
        dateEnd: '2024-01-10T00:00:00Z',
      }

      const { duration } = useEventWarningModal({ modelValue, object, emit })

      expect(duration.value).toBe('9 Tage')
    })

    it('returns singular "Tag" for one day', () => {
      object.value = {
        ...object.value,
        dateStart: '2024-01-01T00:00:00Z',
        dateEnd: '2024-01-02T00:00:00Z',
      }

      const { duration } = useEventWarningModal({ modelValue, object, emit })

      expect(duration.value).toBe('1 Tag')
    })

    it('returns "Unbegrenzt" when no end date', () => {
      object.value = {
        ...object.value,
        dateStart: '2024-01-01T00:00:00Z',
        dateEnd: null,
      }

      const { duration } = useEventWarningModal({ modelValue, object, emit })

      expect(duration.value).toBe('Unbegrenzt')
    })

    it('returns "Ungültiges Datum" when start date is invalid', () => {
      object.value = {
        ...object.value,
        dateStart: null,
        dateEnd: '2024-01-10T00:00:00Z',
      }

      const { duration } = useEventWarningModal({ modelValue, object, emit })

      expect(duration.value).toBe('Ungültiges Datum')
    })
  })

  describe('actualDuration', () => {
    it('calculates duration from start until now', () => {
      // Freeze time to avoid flaky ceil() rounding from millisecond drift
      const now = new Date('2026-02-15T12:00:00.000Z')
      vi.useFakeTimers()
      vi.setSystemTime(now)

      const startDate = new Date('2026-02-10T12:00:00.000Z')

      object.value = {
        ...object.value,
        dateStart: startDate.toISOString(),
      }

      const { actualDuration } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })

      expect(actualDuration.value).toBe('5 Tage')

      vi.useRealTimers()
    })

    it('returns "Ungültiges Datum" when start date is invalid', () => {
      object.value = {
        ...object.value,
        dateStart: null,
      }

      const { actualDuration } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })

      expect(actualDuration.value).toBe('Ungültiges Datum')
    })
  })

  describe('loadAllData', () => {
    beforeEach(() => {
      backend.events.getUsers.mockResolvedValue({
        pageDetails: { totalCount: 10 },
      })
    })

    it('sets loading to true then false', async () => {
      const { loadAllData, loading } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })

      const promise = loadAllData()
      expect(loading.value).toBe(true)

      await promise
      expect(loading.value).toBe(false)
    })

    it('loads participant data', async () => {
      backend.events.getUsers
        .mockResolvedValueOnce({ pageDetails: { totalCount: 10 } })
        .mockResolvedValueOnce({ pageDetails: { totalCount: 6 } })

      const { loadAllData, participants } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })

      await loadAllData()

      expect(participants.total).toBe(10)
      expect(participants.students).toBe(6)
      expect(participants.teachers).toBe(4)
    })

    it('sets loadError on failure', async () => {
      backend.events.getUsers.mockRejectedValue({
        response: { data: { detail: 'Test error' } },
      })

      const { loadAllData, loadError } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })

      await loadAllData()

      expect(loadError.value).toBe('Test error')
    })

    it('accepts additional loaders', async () => {
      const additionalLoader = vi.fn().mockResolvedValue('done')

      const { loadAllData } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })

      await loadAllData([additionalLoader()])

      expect(additionalLoader).toHaveBeenCalled()
    })
  })

  describe('v-model sync', () => {
    it('updates modalVisible when modelValue changes', async () => {
      const { modalVisible } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })

      expect(modalVisible.value).toBe(false)

      modelValue.value = true
      await nextTick()

      expect(modalVisible.value).toBe(true)
    })

    it('emits update:modelValue when modalVisible changes', async () => {
      const { modalVisible } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })

      modalVisible.value = true
      await nextTick()

      expect(emit).toHaveBeenCalledWith('update:modelValue', true)
    })
  })

  describe('onOpen callback', () => {
    it('calls onOpen with loadAllData when modal opens', async () => {
      const onOpen = vi.fn()

      useEventWarningModal({
        modelValue,
        object,
        emit,
        onOpen,
      })

      modelValue.value = true
      await nextTick()

      expect(onOpen).toHaveBeenCalled()
    })

    it('does not call onOpen when object has no id', async () => {
      const onOpen = vi.fn()
      object.value = { name: 'No ID Event' }

      useEventWarningModal({
        modelValue,
        object,
        emit,
        onOpen,
      })

      modelValue.value = true
      await nextTick()

      expect(onOpen).not.toHaveBeenCalled()
    })
  })

  describe('Participant counts', () => {
    it('exposes userStudentsCount computed', () => {
      const { userStudentsCount, participants } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })

      participants.students = 5
      expect(userStudentsCount.value).toBe(5)
    })

    it('exposes userTeachersCount computed', () => {
      const { userTeachersCount, participants } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })

      participants.teachers = 3
      expect(userTeachersCount.value).toBe(3)
    })

    it('exposes totalParticipantsCount computed', () => {
      const { totalParticipantsCount, participants } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })

      participants.total = 8
      expect(totalParticipantsCount.value).toBe(8)
    })

    it('exposes hasParticipants computed', () => {
      const { hasParticipants, participants } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })

      expect(hasParticipants.value).toBe(false)

      participants.total = 1
      expect(hasParticipants.value).toBe(true)
    })
  })

  describe('Edge cases', () => {
    it('handles null object gracefully', () => {
      object.value = null

      const { event, duration } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })

      expect(event.value).toBe(null)
      expect(duration.value).toBe('Ungültiges Datum')
    })

    it('handles missing dates gracefully', () => {
      object.value = { id: 'test', name: 'Test' }

      const { duration, actualDuration } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })

      expect(duration.value).toBe('Ungültiges Datum')
      expect(actualDuration.value).toBe('Ungültiges Datum')
    })

    it('returns default error message when API error has no detail', async () => {
      backend.events.getUsers.mockRejectedValue(new Error('Network error'))

      const { loadAllData, loadError } = useEventWarningModal({
        modelValue,
        object,
        emit,
      })

      await loadAllData()

      expect(loadError.value).toBe('Daten konnten nicht geladen werden.')
    })
  })
})
