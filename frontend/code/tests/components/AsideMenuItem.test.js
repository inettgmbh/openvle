import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AsideMenuItem from '@/components/AsideMenuItem.vue'
import router from '@/router'

describe('AsideMenuItem', () => {
  let wrapper
  let openSpy
  let pushSpy

  beforeEach(() => {
    openSpy = vi.spyOn(window, 'open').mockImplementation(() => null)
    pushSpy = vi.spyOn(router, 'push').mockResolvedValue()
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
      wrapper = null
    }
    openSpy.mockRestore()
    pushSpy.mockRestore()
  })

  const createWrapper = (item) =>
    mount(AsideMenuItem, {
      props: { item },
      global: {
        stubs: {
          BaseIcon: true,
          AsideMenuList: true,
        },
      },
    })

  describe('middle-click (auxclick, button === 1)', () => {
    it('opens route link in a new tab', async () => {
      wrapper = createWrapper({ to: '/users', label: 'Users' })

      await wrapper.find('a').trigger('auxclick', { button: 1 })

      expect(openSpy).toHaveBeenCalledTimes(1)
      const [href, target] = openSpy.mock.calls[0]
      // Hash router resolves /users to a hash-prefixed href
      expect(href).toContain('/users')
      expect(target).toBe('_blank')
      expect(pushSpy).not.toHaveBeenCalled()
    })

    it('opens external href in a new tab', async () => {
      wrapper = createWrapper({
        href: 'https://example.com',
        label: 'External',
      })

      await wrapper.find('a').trigger('auxclick', { button: 1 })

      expect(openSpy).toHaveBeenCalledWith('https://example.com', '_blank')
    })

    it('does not open a new tab on right-click (button === 2)', async () => {
      wrapper = createWrapper({ to: '/users', label: 'Users' })

      await wrapper.find('a').trigger('auxclick', { button: 2 })

      expect(openSpy).not.toHaveBeenCalled()
    })

    it('does not open a new tab for items without to or href (dropdown trigger)', async () => {
      wrapper = createWrapper({
        label: 'Group',
        menu: [{ to: '/sub', label: 'Sub' }],
      })

      await wrapper.find('a').trigger('auxclick', { button: 1 })

      expect(openSpy).not.toHaveBeenCalled()
    })
  })

  describe('left-click (existing behavior, regression check)', () => {
    it('navigates via router.push for route links', async () => {
      wrapper = createWrapper({ to: '/users', label: 'Users' })

      await wrapper.find('a').trigger('click')

      expect(pushSpy).toHaveBeenCalledWith('/users')
      expect(openSpy).not.toHaveBeenCalled()
    })

    it('does not call router.push when Cmd is held (browser handles new tab)', async () => {
      wrapper = createWrapper({ to: '/users', label: 'Users' })

      await wrapper.find('a').trigger('click', { metaKey: true })

      expect(pushSpy).not.toHaveBeenCalled()
    })
  })
})
