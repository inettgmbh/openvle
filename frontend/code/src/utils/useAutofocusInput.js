import { nextTick, ref, watch } from 'vue'

/**
 * Automatically focuses an input element when a modal becomes visible.
 *
 * @param {import('vue').Ref<boolean>} modalVisibility - A reactive reference to the modal's visibility state.
 * @returns {{ autoFocusInputRef: import('vue').Ref<HTMLElement | null> }} An object containing a ref to bind to the input.
 */
export function useAutofocusInput(modalVisibility) {
  const autoFocusInputRef = ref(null)

  watch(modalVisibility, async (isOpen) => {
    if (isOpen) {
      await nextTick()
      autoFocusInputRef.value?.focus()
    }
  })

  return { autoFocusInputRef }
}
