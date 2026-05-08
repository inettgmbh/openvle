import { includeIgnoreFile } from '@eslint/compat'
import ESLint from '@eslint/js'
import prettierConfig from 'eslint-config-prettier'
import docusaurus from '@docusaurus/eslint-plugin'
import globals from 'globals'

import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const gitignorePath = path.resolve(__dirname, '.gitignore')

export default [
  ESLint.configs.recommended,
  prettierConfig,

  includeIgnoreFile(gitignorePath),
  {
    ignores: ['{build}/**/*', '**/*.config.js', '!**/eslint.config.js'],
  },
  {
    plugins: {
      docusaurus: docusaurus,
    },

    files: ['**/*.{js,mjs,cjs,jsx,vue}'],

    linterOptions: {
      reportUnusedDisableDirectives: true,
    },

    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
      globals: {
        ...globals.node,
        ...globals.browser,
        ...globals.es2022,
        process: 'readonly',
        global: 'readonly',
      },
    },

    rules: {
      'docusaurus/no-untranslated-text': [
        'warn',
        { ignoredStrings: ['·', '—', '×'] },
      ],
      'docusaurus/no-html-links': 'warn',
      'docusaurus/string-literal-i18n-messages': 'warn',
      'no-unused-vars': 'off',
      'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
      'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    },

    settings: {},
  },
]
