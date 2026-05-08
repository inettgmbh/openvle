import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { computed, h, nextTick, ref, watch } from 'vue'

/**
 * Focused test for the add-users modal role reset behavior in EventDetail.
 *
 * The actual watcher under test (EventDetail.vue):
 *   watch(
 *     () => modals.addUsers.value,
 *     (isOpen) => { if (!isOpen) resetForm() },
 *   )
 */

const DEFAULT_ROLE_ID = 'role-student-default'
const OTHER_ROLE_ID = 'role-teacher'

/**
 * Mounts a minimal component that runs the given setup callback inside
 * a real Vue component context. Returns whatever the callback returns.
 */
function mountSetup(setupCb) {
  let result
  const wrapper = mount({
    setup() {
      result = setupCb()
      return () => h('div')
    },
  })
  return { ...result, wrapper }
}

function withSetup() {
  return mountSetup(() => {
    const modalOpen = ref(false)
    const objToAdd = ref({ roleId: DEFAULT_ROLE_ID })
    const resetForm = vi.fn(() => {
      objToAdd.value.roleId = DEFAULT_ROLE_ID
    })

    watch(
      () => modalOpen.value,
      (isOpen) => {
        if (!isOpen) resetForm()
      },
    )

    return { modalOpen, objToAdd, resetForm }
  })
}

describe('EventDetail – Add Users Modal', () => {
  it('resets role to default when modal closes', async () => {
    const { modalOpen, objToAdd, resetForm } = withSetup()

    // Open modal
    modalOpen.value = true
    await nextTick()

    // Simulate user selecting a different role
    objToAdd.value.roleId = OTHER_ROLE_ID
    expect(objToAdd.value.roleId).toBe(OTHER_ROLE_ID)

    // Close modal
    modalOpen.value = false
    await nextTick()

    expect(resetForm).toHaveBeenCalledTimes(1)
    expect(objToAdd.value.roleId).toBe(DEFAULT_ROLE_ID)
  })

  it('does not call resetForm when modal opens', async () => {
    const { modalOpen, resetForm } = withSetup()

    modalOpen.value = true
    await nextTick()

    expect(resetForm).not.toHaveBeenCalled()
  })

  it('resets role on every close cycle', async () => {
    const { modalOpen, objToAdd, resetForm } = withSetup()

    // First cycle
    modalOpen.value = true
    await nextTick()
    objToAdd.value.roleId = OTHER_ROLE_ID

    modalOpen.value = false
    await nextTick()
    expect(objToAdd.value.roleId).toBe(DEFAULT_ROLE_ID)

    // Second cycle
    modalOpen.value = true
    await nextTick()
    objToAdd.value.roleId = 'role-something-else'

    modalOpen.value = false
    await nextTick()
    expect(resetForm).toHaveBeenCalledTimes(2)
    expect(objToAdd.value.roleId).toBe(DEFAULT_ROLE_ID)
  })
})

/**
 * Moodle enrollment warning visibility tests.
 *
 * The warnings in EventDetail.vue are conditionally rendered via:
 *   v-if="moodleEnabled && event.moodleCourseId != null"
 *
 * where moodleEnabled is:
 *   computed(() => !!mainStore.settings?.moodle?.enabled)
 *
 * These tests verify the computed condition without mounting EventDetail.
 */

function withMoodleSetup({ settings = {}, event = {} } = {}) {
  return mountSetup(() => {
    const mainStore = ref({ settings })
    const eventRef = ref(event)

    const moodleEnabled = computed(
      () => !!mainStore.value.settings?.moodle?.enabled,
    )

    const showAddUserMoodleWarning = computed(
      () =>
        moodleEnabled.value &&
        eventRef.value.moodleCourseId != null &&
        eventRef.value.status === 'Aktiv',
    )

    const showDeleteUserMoodleWarning = computed(
      () => moodleEnabled.value && eventRef.value.moodleCourseId != null,
    )

    return {
      mainStore,
      eventRef,
      moodleEnabled,
      showAddUserMoodleWarning,
      showDeleteUserMoodleWarning,
    }
  })
}

describe('EventDetail – Moodle Enrollment Warnings', () => {
  it('shows Moodle hint in add-users warning when moodleEnabled and event has moodleCourseId and event is active', () => {
    const { showAddUserMoodleWarning } = withMoodleSetup({
      settings: { moodle: { enabled: true } },
      event: { moodleCourseId: 'course-123', status: 'Aktiv' },
    })

    expect(showAddUserMoodleWarning.value).toBe(true)
  })

  it('does not show Moodle hint in add-users warning when moodleEnabled but event.moodleCourseId is null', () => {
    const { showAddUserMoodleWarning } = withMoodleSetup({
      settings: { moodle: { enabled: true } },
      event: { moodleCourseId: null, status: 'Aktiv' },
    })

    expect(showAddUserMoodleWarning.value).toBe(false)
  })

  it('does not show Moodle hint in add-users warning when moodle is disabled', () => {
    const { showAddUserMoodleWarning } = withMoodleSetup({
      settings: { moodle: { enabled: false } },
      event: { moodleCourseId: 'course-123', status: 'Aktiv' },
    })

    expect(showAddUserMoodleWarning.value).toBe(false)
  })

  it('does not show Moodle hint in add-users warning when moodle settings are absent', () => {
    const { showAddUserMoodleWarning } = withMoodleSetup({
      settings: {},
      event: { moodleCourseId: 'course-123', status: 'Aktiv' },
    })

    expect(showAddUserMoodleWarning.value).toBe(false)
  })

  it('does not show Moodle hint in add-users warning when event is not active', () => {
    const { showAddUserMoodleWarning } = withMoodleSetup({
      settings: { moodle: { enabled: true } },
      event: { moodleCourseId: 'course-123', status: 'Entwurf' },
    })

    expect(showAddUserMoodleWarning.value).toBe(false)
  })

  it('shows Moodle hint in delete-user warning when moodleEnabled and event has moodleCourseId', () => {
    const { showDeleteUserMoodleWarning } = withMoodleSetup({
      settings: { moodle: { enabled: true } },
      event: { moodleCourseId: 'course-456' },
    })

    expect(showDeleteUserMoodleWarning.value).toBe(true)
  })

  it('does not show Moodle hint in delete-user warning when event.moodleCourseId is null', () => {
    const { showDeleteUserMoodleWarning } = withMoodleSetup({
      settings: { moodle: { enabled: true } },
      event: { moodleCourseId: null },
    })

    expect(showDeleteUserMoodleWarning.value).toBe(false)
  })

  it('does not show Moodle hint in delete-user warning when moodle is disabled', () => {
    const { showDeleteUserMoodleWarning } = withMoodleSetup({
      settings: { moodle: { enabled: false } },
      event: { moodleCourseId: 'course-456' },
    })

    expect(showDeleteUserMoodleWarning.value).toBe(false)
  })

  it('reacts to moodle settings changing at runtime', async () => {
    const { mainStore, showAddUserMoodleWarning } = withMoodleSetup({
      settings: { moodle: { enabled: false } },
      event: { moodleCourseId: 'course-123', status: 'Aktiv' },
    })

    expect(showAddUserMoodleWarning.value).toBe(false)

    // Enable moodle at runtime
    mainStore.value.settings = { moodle: { enabled: true } }
    await nextTick()

    expect(showAddUserMoodleWarning.value).toBe(true)
  })
})
