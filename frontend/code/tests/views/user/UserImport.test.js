import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'

// Backend singleton — capture the create-user payload
const { mockCreateUser } = vi.hoisted(() => ({
  mockCreateUser: vi.fn().mockResolvedValue({}),
}))

vi.mock('@/services', () => ({
  default: {
    users: {
      create: mockCreateUser,
    },
  },
}))

// Drives the CSVUpload stub's exposed `currentStep` so tests can simulate the
// user having progressed past the upload step. 1 = nothing uploaded yet.
const stubStep = ref(1)

// Stub CSVUpload so we can read the required-mappings it receives, invoke the
// onImportConfirm callback directly, and expose a controllable `currentStep`
// (the real component exposes this via defineExpose).
const CSVUpload = {
  name: 'CSVUpload',
  props: ['requiredMappings', 'onImportConfirm', 'limit'],
  setup(_, { expose }) {
    expose({ currentStep: stubStep })
    return {}
  },
  template: '<div class="csv-upload" />',
}

const UnsavedChangesModal = {
  name: 'UnsavedChangesModal',
  props: ['modelValue'],
  emits: ['discard', 'continue', 'update:modelValue'],
  template: '<div class="unsaved-modal" />',
}

const stubs = {
  LayoutAuthenticated: { template: '<div><slot /></div>' },
  SectionMain: { template: '<div><slot /></div>' },
  SectionTitleLineWithButton: { template: '<div />' },
  CardBox: { template: '<div class="card-box"><slot /></div>' },
  FormField: { template: '<div class="form-field"><slot /></div>' },
  CSVUpload,
  UnsavedChangesModal,
}

import UserImport from '@/views/user/UserImport.vue'

describe('UserImport', () => {
  let wrapper

  const createWrapper = () => {
    wrapper = mount(UserImport, { global: { stubs } })
    return wrapper
  }

  const csv = () => wrapper.findComponent(CSVUpload)
  const mappingKeys = () =>
    csv()
      .props('requiredMappings')
      .map((m) => m.key)
  const runImport = (row) => csv().props('onImportConfirm')(row)
  const selectMode = (value) =>
    wrapper.find(`[data-mode="${value}"]`).trigger('click')
  const discardModal = () =>
    wrapper.findComponent({ name: 'UnsavedChangesModal' })

  afterEach(() => {
    mockCreateUser.mockClear()
    stubStep.value = 1
    if (wrapper) wrapper.unmount()
  })

  describe('split mode (default)', () => {
    it('requires separate firstname and lastname columns', () => {
      createWrapper()
      expect(mappingKeys()).toEqual([
        'email',
        'firstname',
        'lastname',
        'username',
      ])
    })

    it('combines firstname and lastname into the single name field', async () => {
      createWrapper()
      await runImport({
        email: 'john@example.com',
        firstname: 'John',
        lastname: 'Doe',
        username: 'jdoe',
      })
      expect(mockCreateUser).toHaveBeenCalledWith(
        expect.objectContaining({
          username: 'jdoe',
          email: 'john@example.com',
          name: 'John Doe',
        }),
      )
    })

    it('trims when one part is empty (no trailing space)', async () => {
      createWrapper()
      await runImport({
        email: 'john@example.com',
        firstname: 'John',
        lastname: '',
        username: 'jdoe',
      })
      expect(mockCreateUser).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'John' }),
      )
    })
  })

  describe('full mode', () => {
    it('requires a single fullname column instead of first/last', async () => {
      createWrapper()
      await selectMode('full')
      expect(mappingKeys()).toEqual(['email', 'fullname', 'username'])
    })

    it('uses the fullname column verbatim (trimmed)', async () => {
      createWrapper()
      await selectMode('full')
      await runImport({
        email: 'jane@example.com',
        fullname: '  Jane Roe  ',
        username: 'jroe',
      })
      expect(mockCreateUser).toHaveBeenCalledWith(
        expect.objectContaining({
          username: 'jroe',
          email: 'jane@example.com',
          name: 'Jane Roe',
        }),
      )
    })
  })

  it('rejects a row without a valid email and does not call the backend', async () => {
    createWrapper()
    await expect(
      runImport({
        email: 'not-an-email',
        firstname: 'A',
        lastname: 'B',
        username: 'ab',
      }),
    ).rejects.toThrow()
    expect(mockCreateUser).not.toHaveBeenCalled()
  })

  describe('switching format after the upload step', () => {
    it('switches immediately while still on the upload step (step 1)', async () => {
      createWrapper()
      stubStep.value = 1
      await selectMode('full')

      expect(discardModal().props('modelValue')).toBe(false)
      expect(mappingKeys()).toEqual(['email', 'fullname', 'username'])
    })

    it('asks for confirmation instead of switching once past step 1', async () => {
      createWrapper()
      stubStep.value = 2 // a file has been uploaded
      await selectMode('full')

      // Still in split mode; the discard overlay is shown.
      expect(mappingKeys()).toEqual([
        'email',
        'firstname',
        'lastname',
        'username',
      ])
      expect(discardModal().props('modelValue')).toBe(true)
    })

    it('applies the pending switch when the user confirms discarding', async () => {
      createWrapper()
      stubStep.value = 2
      await selectMode('full')

      discardModal().vm.$emit('discard')
      await wrapper.vm.$nextTick()

      expect(mappingKeys()).toEqual(['email', 'fullname', 'username'])
    })

    it('keeps the current format when the user continues editing', async () => {
      createWrapper()
      stubStep.value = 2
      await selectMode('full')

      discardModal().vm.$emit('continue')
      await wrapper.vm.$nextTick()

      expect(mappingKeys()).toEqual([
        'email',
        'firstname',
        'lastname',
        'username',
      ])
    })

    it('re-opens the overlay when the other option is clicked again after "continue"', async () => {
      createWrapper()
      stubStep.value = 2

      await selectMode('full')
      discardModal().vm.$emit('continue')
      await wrapper.vm.$nextTick()
      expect(discardModal().props('modelValue')).toBe(false)

      // Clicking the same other option again must trigger the confirm anew.
      await selectMode('full')
      expect(discardModal().props('modelValue')).toBe(true)
    })
  })
})
