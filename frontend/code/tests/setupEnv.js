/**
 * Environment setup that runs BEFORE any modules are loaded.
 * This ensures browser APIs are available for modules that access them
 * during initialization.
 */

// Mock localStorage for jsdom environment (needed by @vue/devtools-kit)
if (
  typeof globalThis.localStorage === 'undefined' ||
  !globalThis.localStorage.getItem
) {
  const store = {}
  globalThis.localStorage = {
    getItem: (key) => store[key] ?? null,
    setItem: (key, value) => {
      store[key] = String(value)
    },
    removeItem: (key) => {
      delete store[key]
    },
    clear: () => {
      Object.keys(store).forEach((key) => delete store[key])
    },
    get length() {
      return Object.keys(store).length
    },
    key: (index) => Object.keys(store)[index] ?? null,
  }
}

// Mock sessionStorage
if (typeof globalThis.sessionStorage === 'undefined') {
  const store = {}
  globalThis.sessionStorage = {
    getItem: (key) => store[key] ?? null,
    setItem: (key, value) => {
      store[key] = String(value)
    },
    removeItem: (key) => {
      delete store[key]
    },
    clear: () => {
      Object.keys(store).forEach((key) => delete store[key])
    },
    get length() {
      return Object.keys(store).length
    },
    key: (index) => Object.keys(store)[index] ?? null,
  }
}
