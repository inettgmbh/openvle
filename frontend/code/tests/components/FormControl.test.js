import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import FormControl from '@/components/FormControl.vue'

// Mock dependencies
vi.mock('@/components/BaseIcon.vue', () => ({
  default: {
    name: 'BaseIcon',
    template: '<span class="base-icon"></span>',
    props: ['path', 'size'],
  },
}))

vi.mock('@/components/FormControlIcon.vue', () => ({
  default: {
    name: 'FormControlIcon',
    template: '<span class="form-control-icon"></span>',
    props: ['icon', 'h'],
  },
}))

vi.mock('@/stores/main', () => ({
  useMainStore: () => ({
    isFieldFocusRegistered: false,
  }),
}))

const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

describe('FormControl', () => {
  const createWrapper = (props = {}, options = {}) => {
    return mount(FormControl, {
      props,
      global: {
        directives: {
          tooltip: () => {},
        },
        ...options.global,
      },
      ...options,
    })
  }

  describe('Input Type Rendering', () => {
    it('renders text input by default', () => {
      const wrapper = createWrapper()
      expect(wrapper.find('input[type="text"]').exists()).toBe(true)
    })

    it('renders password input when type is password', () => {
      const wrapper = createWrapper({ type: 'password' })
      expect(wrapper.find('input[type="password"]').exists()).toBe(true)
    })

    it('renders email input when type is email', () => {
      const wrapper = createWrapper({ type: 'email' })
      expect(wrapper.find('input[type="email"]').exists()).toBe(true)
    })

    it('renders number input when type is number', () => {
      const wrapper = createWrapper({ type: 'number' })
      expect(wrapper.find('input[type="number"]').exists()).toBe(true)
    })

    it('renders textarea when type is textarea', () => {
      const wrapper = createWrapper({ type: 'textarea' })
      expect(wrapper.find('textarea').exists()).toBe(true)
    })

    it('renders select when options are provided', () => {
      const wrapper = createWrapper({
        options: [
          { value: 'a', label: 'Option A' },
          { value: 'b', label: 'Option B' },
        ],
      })
      expect(wrapper.find('select').exists()).toBe(true)
    })

    it('renders range input when type is range', () => {
      const wrapper = createWrapper({ type: 'range', min: 0, max: 100 })
      expect(wrapper.find('input[type="range"]').exists()).toBe(true)
    })
  })

  describe('Select Options', () => {
    it('renders all options', () => {
      const wrapper = createWrapper({
        options: [
          { value: 'a', label: 'Option A' },
          { value: 'b', label: 'Option B' },
          { value: 'c', label: 'Option C' },
        ],
      })
      const options = wrapper.findAll('option')
      // +1 for the empty option when not required
      expect(options.length).toBe(4)
    })

    it('does not render empty option when required', () => {
      const wrapper = createWrapper({
        required: true,
        options: [
          { value: 'a', label: 'Option A' },
          { value: 'b', label: 'Option B' },
        ],
      })
      const options = wrapper.findAll('option')
      expect(options.length).toBe(2)
    })

    it('displays option labels', () => {
      const wrapper = createWrapper({
        options: [{ value: 'test', label: 'Test Label' }],
      })
      expect(wrapper.text()).toContain('Test Label')
    })

    it('disables individual options', () => {
      const wrapper = createWrapper({
        options: [
          { value: 'a', label: 'A', disabled: true },
          { value: 'b', label: 'B' },
        ],
      })
      const disabledOption = wrapper.find('option[disabled]')
      expect(disabledOption.exists()).toBe(true)
    })
  })

  describe('v-model', () => {
    it('emits update:modelValue on input change', async () => {
      const wrapper = createWrapper({ modelValue: '' })
      const input = wrapper.find('input')

      await input.setValue('new value')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')[0]).toEqual(['new value'])
    })

    it('emits update:modelValue on select change', async () => {
      const wrapper = createWrapper({
        modelValue: 'a',
        options: [
          { value: 'a', label: 'A' },
          { value: 'b', label: 'B' },
        ],
      })
      const select = wrapper.find('select')

      await select.setValue('b')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    })

    it('emits update:modelValue on textarea change', async () => {
      const wrapper = createWrapper({ type: 'textarea', modelValue: '' })
      const textarea = wrapper.find('textarea')

      await textarea.setValue('text content')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')[0]).toEqual(['text content'])
    })
  })

  describe('Attributes', () => {
    it('sets placeholder attribute', () => {
      const wrapper = createWrapper({ placeholder: 'Enter text...' })
      expect(wrapper.find('input').attributes('placeholder')).toBe(
        'Enter text...',
      )
    })

    it('sets name attribute', () => {
      const wrapper = createWrapper({ name: 'username' })
      expect(wrapper.find('input').attributes('name')).toBe('username')
    })

    it('sets id attribute', () => {
      const wrapper = createWrapper({ id: 'my-input' })
      expect(wrapper.find('input').attributes('id')).toBe('my-input')
    })

    it('sets maxlength attribute', () => {
      const wrapper = createWrapper({ maxlength: '50' })
      expect(wrapper.find('input').attributes('maxlength')).toBe('50')
    })

    it('sets autocomplete attribute', () => {
      const wrapper = createWrapper({ autocomplete: 'email' })
      expect(wrapper.find('input').attributes('autocomplete')).toBe('email')
    })

    it('sets required attribute', () => {
      const wrapper = createWrapper({ required: true })
      expect(wrapper.find('input').attributes('required')).toBeDefined()
    })

    it('sets disabled attribute', () => {
      const wrapper = createWrapper({ disabled: true })
      expect(wrapper.find('input').attributes('disabled')).toBeDefined()
    })

    it('sets readonly attribute', () => {
      const wrapper = createWrapper({ readonly: true })
      expect(wrapper.find('input').attributes('readonly')).toBeDefined()
    })

    it('sets min and max for number input', () => {
      const wrapper = createWrapper({ type: 'number', min: 0, max: 100 })
      expect(wrapper.find('input').attributes('min')).toBe('0')
      expect(wrapper.find('input').attributes('max')).toBe('100')
    })

    it('sets step for number input', () => {
      const wrapper = createWrapper({ type: 'number', step: 5 })
      expect(wrapper.find('input').attributes('step')).toBe('5')
    })
  })

  describe('Styling', () => {
    it('applies borderless class when borderless is true', () => {
      const wrapper = createWrapper({ borderless: true })
      expect(wrapper.find('input').classes()).toContain('border-0')
    })

    it('applies transparent background when transparent is true', () => {
      const wrapper = createWrapper({ transparent: true })
      expect(wrapper.find('input').classes()).toContain('bg-transparent')
    })

    it('applies h-24 for textarea', () => {
      const wrapper = createWrapper({ type: 'textarea' })
      expect(wrapper.find('textarea').classes()).toContain('h-24')
    })

    it('applies h-12 for regular input', () => {
      const wrapper = createWrapper()
      expect(wrapper.find('input').classes()).toContain('h-12')
    })

    it('applies pl-10 when icon is provided', () => {
      const wrapper = createWrapper({ icon: 'mdi-account' })
      expect(wrapper.find('input').classes()).toContain('pl-10')
    })
  })

  describe('Icon', () => {
    it('renders FormControlIcon when icon prop is provided', () => {
      const wrapper = createWrapper({ icon: 'mdi-account' })
      expect(wrapper.find('.form-control-icon').exists()).toBe(true)
    })

    it('does not render icon when not provided', () => {
      const wrapper = createWrapper()
      expect(wrapper.find('.form-control-icon').exists()).toBe(false)
    })
  })

  describe('Range Input', () => {
    it('displays min, max, and current value for range', () => {
      const wrapper = createWrapper({
        type: 'range',
        min: 0,
        max: 100,
        modelValue: 50,
      })
      expect(wrapper.text()).toContain('0')
      expect(wrapper.text()).toContain('100')
      expect(wrapper.text()).toContain('50')
    })
  })

  describe('Validation', () => {
    it('shows validation error for required field when empty', async () => {
      const wrapper = createWrapper({
        required: true,
        validate: true,
        modelValue: 'test',
      })
      const input = wrapper.find('input')

      await input.setValue('')

      expect(wrapper.emitted('update:validationError')).toBeTruthy()
    })

    it('shows validation error when maxlength exceeded', async () => {
      const wrapper = createWrapper({
        maxlength: '5',
        validate: true,
        modelValue: '',
      })
      const input = wrapper.find('input')

      await input.setValue('123456')

      expect(wrapper.emitted('update:validationError')).toBeTruthy()
    })

    it('calls custom validation function', async () => {
      const customValidate = vi.fn((value) =>
        value.length >= 3 ? true : 'Min 3 chars',
      )
      const wrapper = createWrapper({
        validate: customValidate,
        modelValue: '',
      })
      const input = wrapper.find('input')

      await input.setValue('ab')

      expect(customValidate).toHaveBeenCalledWith('ab')
    })

    it('applies error border class on validation error', async () => {
      const wrapper = createWrapper({
        required: true,
        validate: true,
        modelValue: 'test',
      })
      const input = wrapper.find('input')

      await input.setValue('')

      // Check if border-red-500 class is applied
      expect(input.classes().some((c) => c.includes('border-red'))).toBe(true)
    })
  })

  describe('Link Feature', () => {
    afterEach(() => {
      mockPush.mockClear()
      vi.restoreAllMocks()
    })

    it('renders link icon when link prop is provided', () => {
      const wrapper = createWrapper({ link: '/users/123', modelValue: 'test' })
      expect(wrapper.find('.base-icon').exists()).toBe(true)
    })

    it('does not render link icon for select', () => {
      const wrapper = createWrapper({
        link: '/users/123',
        options: [{ value: 'a', label: 'A' }],
      })
      // The link icon should not appear for select elements
      const linkDiv = wrapper.find('.absolute.right-2')
      expect(linkDiv.exists()).toBe(false)
    })

    it('opens external link in new tab on click', async () => {
      const openSpy = vi.spyOn(window, 'open').mockImplementation(() => {})
      const wrapper = createWrapper({
        link: 'https://example.com',
        modelValue: 'test',
      })
      const linkDiv = wrapper.find('.absolute.right-2')

      await linkDiv.trigger('click')

      expect(openSpy).toHaveBeenCalledWith('https://example.com', '_blank')
      expect(mockPush).not.toHaveBeenCalled()
      openSpy.mockRestore()
    })

    it('navigates via router.push for internal link on normal click', async () => {
      const openSpy = vi.spyOn(window, 'open').mockImplementation(() => {})
      const wrapper = createWrapper({
        link: '/users/123',
        modelValue: 'test',
      })
      const linkDiv = wrapper.find('.absolute.right-2')

      await linkDiv.trigger('click')

      expect(mockPush).toHaveBeenCalledWith({ path: '/users/123' })
      expect(openSpy).not.toHaveBeenCalled()
      openSpy.mockRestore()
    })

    it('opens internal link in new tab on ctrl+click', async () => {
      const openSpy = vi.spyOn(window, 'open').mockImplementation(() => {})
      const wrapper = createWrapper({
        link: '/users/123',
        modelValue: 'test',
      })
      const linkDiv = wrapper.find('.absolute.right-2')

      await linkDiv.trigger('click', { ctrlKey: true })

      expect(openSpy).toHaveBeenCalledWith('/#/users/123', '_blank')
      expect(mockPush).not.toHaveBeenCalled()
      openSpy.mockRestore()
    })
  })
})
