import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import dotenv from 'dotenv'
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'

dotenv.config()

export default defineConfig(({ mode }) => ({
  plugins: [vue(), vueJsx()],

  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },

  define: {
    'process.env': {
      VUE_APP_VERSION: process.env.VERSION ? 'v' + process.env.VERSION : 'dev',
      VUE_SENTRY_RELEASE: process.env.SENTRY_RELEASE || 'dev',
    },
  },

  build: {
    sourcemap: mode === 'development' ? 'inline' : 'hidden',
  },

  css: {
    devSourcemap: true,
    preprocessorOptions: {
      scss: {
        api: 'modern-compiler',
      },
    },
  },
}))
