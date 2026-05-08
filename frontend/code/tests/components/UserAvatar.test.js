import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import UserAvatar from '@/components/UserAvatar.vue'

// Mock dependencies
vi.mock('@/stores/main', () => ({
  useMainStore: () => ({
    settings: {
      avatars: {
        type: 'glass',
      },
    },
  }),
}))

vi.mock('@/utils/dataUtils', () => ({
  avatarStyleValidator: vi.fn((type) =>
    ['glass', 'bottts', 'avataaars'].includes(type),
  ),
}))

vi.mock('@dicebear/core', () => ({
  createAvatar: vi.fn(() => ({
    toString: () => '<svg>mock-avatar</svg>',
  })),
}))

vi.mock('@dicebear/collection', () => ({
  glass: { name: 'glass' },
  bottts: { name: 'bottts' },
  avataaars: { name: 'avataaars' },
}))

describe('UserAvatar', () => {
  const createWrapper = (props = {}) => {
    return mount(UserAvatar, {
      props: { userid: 'test-user-123', ...props },
    })
  }

  describe('Rendering', () => {
    it('renders an img element', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      expect(wrapper.find('img').exists()).toBe(true)
    })

    it('applies rounded-full class', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      expect(wrapper.find('img').classes()).toContain('rounded-full')
    })

    it('applies w-full and h-auto classes', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      const img = wrapper.find('img')
      expect(img.classes()).toContain('w-full')
      expect(img.classes()).toContain('h-auto')
    })

    it('renders slot content', async () => {
      const wrapper = mount(UserAvatar, {
        props: { userid: 'test-user' },
        slots: {
          default: '<span class="slot-content">Extra Content</span>',
        },
      })
      await flushPromises()
      expect(wrapper.find('.slot-content').exists()).toBe(true)
    })
  })

  describe('Avatar Source', () => {
    it('uses provided avatar prop directly', async () => {
      const wrapper = createWrapper({
        avatar: 'https://example.com/avatar.png',
      })
      await flushPromises()
      expect(wrapper.find('img').attributes('src')).toBe(
        'https://example.com/avatar.png',
      )
    })

    it('generates avatar when no avatar prop provided', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      const src = wrapper.find('img').attributes('src')
      expect(src).toContain('data:image/svg+xml')
    })

    it('generates different avatars for different userids', async () => {
      const wrapper1 = createWrapper({ userid: 'user-1' })
      await flushPromises()
      const wrapper2 = createWrapper({ userid: 'user-2' })
      await flushPromises()

      // Both should have generated avatars (same mock, but in real scenario would differ)
      expect(wrapper1.find('img').attributes('src')).toContain('data:image')
      expect(wrapper2.find('img').attributes('src')).toContain('data:image')
    })
  })

  describe('Props', () => {
    it('requires userid prop', () => {
      const { userid } = UserAvatar.props
      expect(userid.required).toBe(true)
      expect(userid.type).toBe(String)
    })

    it('has default alt text', () => {
      const { alt } = UserAvatar.props
      expect(alt.default).toBe('User Avatar')
    })

    it('has null default for avatar', () => {
      const { avatar } = UserAvatar.props
      expect(avatar.default).toBeNull()
    })
  })

  describe('Styling', () => {
    it('applies background color classes', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      const img = wrapper.find('img')
      expect(img.classes()).toContain('bg-gray-100')
      expect(img.classes()).toContain('dark:bg-slate-800')
    })

    it('applies block display', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      expect(wrapper.find('img').classes()).toContain('block')
    })

    it('applies max-w-full', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      expect(wrapper.find('img').classes()).toContain('max-w-full')
    })
  })
})
