import { includeIgnoreFile } from '@eslint/compat'
import ESLint from '@eslint/js'
import prettierConfig from '@vue/eslint-config-prettier'
import importPlugin from 'eslint-plugin-import'
import pluginVue from 'eslint-plugin-vue'
import globals from 'globals'

import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const gitignorePath = path.resolve(__dirname, '.gitignore')

export default [
  ESLint.configs.recommended,
  ...pluginVue.configs['flat/recommended'],
  prettierConfig,

  includeIgnoreFile(gitignorePath),
  {
    ignores: ['{dist,public}/**/*', '**/*.config.js', '!**/eslint.config.js'],
  },
  {
    plugins: {
      import: importPlugin,
    },

    files: ['**/*.{js,mjs,cjs,jsx,vue}'],

    linterOptions: {
      reportUnusedDisableDirectives: true,
    },

    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: {
        ...globals.node,
        ...globals.browser,
        ...globals.es2022,
        process: 'readonly',
        global: 'readonly',
      },
    },

    rules: {
      'import/order': [
        'warn',
        {
          'newlines-between': 'always',
          named: true,
          alphabetize: {
            order: 'asc',
            caseInsensitive: true,
          },
          warnOnUnassignedImports: true,
          groups: [
            'index',
            'sibling',
            'parent',
            'internal',
            'external',
            'builtin',
            'object',
            'type',
          ],
        },
      ],
      'vue/no-unused-vars': 'off',
      'no-unused-vars': 'off',
      'vue/padding-line-between-tags': 'warn',
      'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
      'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    },

    settings: {},
  },
]
