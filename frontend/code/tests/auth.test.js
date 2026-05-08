import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import LoginView from '@/views/auth/AuthLogin.vue'

describe('LoginView', () => {
  it('renders the auth-disabled notice when no auth method is configured', () => {
    const wrapper = mount(LoginView)

    expect(wrapper.text()).toMatch(/Anmeldung vorübergehend deaktiviert/)
  })
})
