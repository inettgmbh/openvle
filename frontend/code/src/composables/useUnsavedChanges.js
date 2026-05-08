import {
  computed,
  getCurrentInstance,
  onBeforeUnmount,
  onMounted,
  ref,
} from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

/**
 * Composable for detecting unsaved changes in forms.
 *
 * @param {Object} options - Configuration options.
 * @param {import('vue').Ref<Object>} options.formData - Reactive form data reference.
 * @param {Function} [options.onNavigateAway] - Callback when user confirms discarding changes.
 * @returns {Object} Unsaved changes state and methods.
 */
export function useUnsavedChanges(options = {}) {
  const { formData, onNavigateAway } = options

  const originalSnapshot = ref(null)
  const isSaved = ref(false)
  const showDiscardModal = ref(false)
  const pendingNavigation = ref(null)

  /**
   * Checks if the form data has been modified from the original state.
   */
  const hasChanges = computed(() => {
    if (!originalSnapshot.value || isSaved.value) return false
    return JSON.stringify(formData.value) !== originalSnapshot.value
  })

  /**
   * Stores the original form data state for comparison.
   * Call this after fetching data and any necessary transformations.
   */
  function setOriginal() {
    originalSnapshot.value = JSON.stringify(formData.value)
    isSaved.value = false
  }

  /**
   * Marks the form as saved, disabling change detection.
   * Call this after successful form submission.
   */
  function markAsSaved() {
    isSaved.value = true
  }

  /**
   * Handles cancel button click.
   * Shows modal if there are unsaved changes, otherwise returns true for direct navigation.
   *
   * @returns {boolean} True if navigation should proceed immediately.
   */
  function handleCancel() {
    if (hasChanges.value) {
      showDiscardModal.value = true
      return false
    }
    return true
  }

  /**
   * Confirms discarding changes and navigates away.
   */
  function confirmDiscard() {
    showDiscardModal.value = false
    isSaved.value = true
    if (pendingNavigation.value) {
      // Route guard case - allow the pending navigation to proceed
      pendingNavigation.value(true)
      pendingNavigation.value = null
    } else if (onNavigateAway) {
      // Manual cancel button case - use callback
      onNavigateAway()
    }
  }

  /**
   * Cancels the discard action and continues editing.
   */
  function cancelDiscard() {
    showDiscardModal.value = false
    if (pendingNavigation.value) {
      // Block the pending navigation
      pendingNavigation.value(false)
      pendingNavigation.value = null
    }
  }

  /**
   * Handles browser beforeunload event.
   *
   * @param {BeforeUnloadEvent} event - The beforeunload event.
   */
  function handleBeforeUnload(event) {
    if (hasChanges.value) {
      event.preventDefault()
      // Chrome requires returnValue to be set
      event.returnValue = ''
    }
  }

  // Only register lifecycle hooks when used within a component context
  if (getCurrentInstance()) {
    onMounted(() => {
      window.addEventListener('beforeunload', handleBeforeUnload)
    })

    onBeforeUnmount(() => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
    })

    // Route navigation guard - intercepts all route changes (navbar, links, etc.)
    onBeforeRouteLeave(() => {
      if (hasChanges.value) {
        showDiscardModal.value = true
        // Return a Promise that resolves based on user's modal choice
        return new Promise((resolve) => {
          pendingNavigation.value = resolve
        })
      }
      return true
    })
  }

  return {
    hasChanges,
    showDiscardModal,
    setOriginal,
    markAsSaved,
    handleCancel,
    confirmDiscard,
    cancelDiscard,
  }
}
