import './setupMocks'

import { createTestingPinia } from '@pinia/testing'
import { config } from '@vue/test-utils'
import { afterAll, beforeAll, beforeEach, vi } from 'vitest'

import i18n, { setLocale } from '@/i18n'
import router from '@/router'

// Mock `window.scrollTo`
global.scrollTo = vi.fn()

// Configure the global setup for Vue Test Utils
config.global.plugins = []

// Add Pinia with the `createSpy` function
export const testingPinia = createTestingPinia({
  createSpy: vi.fn,
})
config.global.plugins.push(testingPinia)

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

/**
 * Opt the calling test file out of the shared global testing pinia above.
 *
 * Vue Test Utils concatenates `config.global.plugins` with a mount's own
 * `global.plugins`, so a test that installs its own pinia (e.g. to run real,
 * non-stubbed actions via `stubActions: false`) ends up providing pinia twice
 * on the same app and triggers:
 *   [Vue warn]: App already provides property with key "Symbol(pinia)".
 *
 * Call this once at the top of such a file. It removes the shared pinia for
 * that file only (identity match) and restores it afterwards, so the file's
 * own pinia is the single provider.
 */
export function useLocalPinia() {
  let savedPlugins
  beforeAll(() => {
    savedPlugins = config.global.plugins
    config.global.plugins = savedPlugins.filter(
      (plugin) => plugin !== testingPinia,
    )
  })
  afterAll(() => {
    config.global.plugins = savedPlugins
  })
}
