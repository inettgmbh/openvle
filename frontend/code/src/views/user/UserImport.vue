<script setup>
import { mdiAccount } from '@mdi/js'
import { useI18n } from 'vue-i18n'

import CardBox from '@/components/CardBox.vue'
import CSVUpload from '@/components/CSVUpload.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { DEFAULT_USER_LOCALE } from '@/utils/localeData'

const { t } = useI18n()

const userImportHeadersCSV = [
  { key: 'email', label: t('views.users.import.email') },
  { key: 'firstname', label: t('views.users.import.firstname') },
  { key: 'lastname', label: t('views.users.import.lastname') },
  { key: 'username', label: t('views.users.import.username') },
]

async function createUser(row) {
  if (!row.email?.includes('@'))
    throw new Error(t('views.users.import.invalidEmail'))

  try {
    await backend.users.create({
      username: row.username,
      email: row.email,
      name: row.firstname + ' ' + row.lastname,
      status: 'Active',
      locale: DEFAULT_USER_LOCALE,
    })
    return true
  } catch (error) {
    if (error?.response?.data?.detail) {
      throw new Error(error?.response?.data?.detail)
    } else {
      throw new Error(t('views.users.import.unknownError'))
    }
  }
}
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiAccount"
        :title="
          $t('common.importTitle', { entity: $t('objectTypes.user.singular') })
        "
        main
        docs-path="/docs/usage/openvle/access-control/users/"
      />

      <CardBox class="min-h-[500px]">
        <CSVUpload
          :required-mappings="userImportHeadersCSV"
          :on-import-confirm="createUser"
          :limit="5000"
        />
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
