import './setupMocks'

import { createTestingPinia } from '@pinia/testing'
import { config } from '@vue/test-utils'
import { beforeEach, vi } from 'vitest'

import i18n, { setLocale } from '@/i18n'
import router from '@/router'

// Mock `window.scrollTo`
global.scrollTo = vi.fn()

// Configure the global setup for Vue Test Utils
config.global.plugins = []

// Add Pinia with the `createSpy` function
config.global.plugins.push(
  createTestingPinia({
    createSpy: vi.fn,
  }),
)

// Use the existing router
config.global.plugins.push(router)

// Add i18n plugin for useI18n() in <script setup>
config.global.plugins.push(i18n)

// Register global directives as no-op stubs
config.global.directives = {
  tooltip: {},
}

// Global mocks (i18n $t is provided by the i18n plugin above)
config.global.mocks = {}

// Ensure German locale for all tests (jsdom defaults to en-US)
beforeEach(() => {
  setLocale('de')
})
