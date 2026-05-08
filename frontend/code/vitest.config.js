import { fileURLToPath } from 'node:url'
import { mergeConfig } from 'vite'
import { configDefaults, defineConfig } from 'vitest/config'
import viteConfig from './vite.config'

export default defineConfig((configEnv) =>
  mergeConfig(
    viteConfig(configEnv),
    defineConfig({
      test: {
        environment: 'jsdom',
        exclude: [...configDefaults.exclude, 'e2e/*'],
        root: fileURLToPath(new URL('./', import.meta.url)),
        transformMode: {
          web: [/\.[jt]sx$/],
        },
        coverage: {
          provider: 'v8',
          reporter: ['text', 'lcov', 'cobertura'],
          reportsDirectory: './coverage',
        },
        setupFiles: ['./tests/setupEnv.js', './tests/setup.js'],
      },
    }),
  ),
)
