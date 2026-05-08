<script setup>
import {
  mdiAccountOutline,
  mdiClockPlusOutline,
  mdiHelpBoxOutline,
  mdiIpOutline,
  mdiKeyOutline,
  mdiNumeric,
  mdiSlashForwardBox,
  mdiTextBox,
} from '@mdi/js'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseTab from '@/components/BaseTab.vue'
import BaseTabs from '@/components/BaseTabs.vue'
import CardBox from '@/components/CardBox.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { resolveFieldFromLookup } from '@/utils/dataUtils'
import { httpStatusCodes } from '@/utils/httpStatusCodes'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const toast = useToast()

const activity = ref([])

function sortedEntries(obj) {
  if (!obj) return []
  return Object.entries(obj).sort(([a], [b]) =>
    a.localeCompare(b, undefined, { sensitivity: 'base' }),
  )
}

const sortedRequestParameter = computed(() =>
  sortedEntries(activity.value.requestParameter),
)
const sortedRequestHeaders = computed(() =>
  sortedEntries(activity.value.requestHeaders),
)
const sortedResponseHeaders = computed(() =>
  sortedEntries(activity.value.responseHeaders),
)

async function fetchObject(objectId) {
  try {
    await backend.activities.get(objectId).then(async (response) => {
      activity.value = response
      activity.value.responseCode = httpStatusCodes[activity.value.responseCode]
      if (activity.value.requestHeaders['x-forwarded-for']) {
        activity.value.requestClientIPAll =
          activity.value.requestHeaders['x-forwarded-for'] +
          ' (via ' +
          activity.value.requestClientIP +
          ')'
      } else {
        activity.value.requestClientIPAll = activity.value.requestClientIP
      }
      activity.value.timestamp = new Date(
        activity.value.timestamp,
      ).toLocaleString('de-DE', {
        timeZoneName: 'short',
        weekday: 'long',
        year: '2-digit',
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      })
      if (activity.value?.requestUser?.id) {
        activity.value.requestUserId = activity.value.requestUser.id
        await resolveFieldFromLookup(activity.value, [
          { from: 'requestUserId', to: 'requestUsername', keyspace: 'users' },
        ])
      } else {
        activity.value.requestUsername = activity.value?.requestUser?.username
      }
    })
  } catch (error) {
    toast.warning(
      t('common.notFound', { entity: t('objectTypes.activity.singular') }),
    )
    router.push({ path: `/activities`, replace: true })
  }
}

fetchObject(route.params.id)
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiTextBox"
        :title="activity.id ? activity.id : 'Loading...'"
        :object-model="$t('objectTypes.activity.singular')"
        main
        docs-path="/docs/usage/openvle/system/activities/"
      />

      <CardBox>
        <BaseTabs>
          <BaseTab id="activities" :title="$t('objectTypes.activity.singular')">
            <FormField :label="$t('views.activities.detail.timestamp')">
              <FormControl
                v-model="activity.timestamp"
                :icon="mdiClockPlusOutline"
                disabled
              />
            </FormField>

            <FormField>
              <FormField :label="$t('views.activities.detail.clientIp')">
                <FormControl
                  v-model="activity.requestClientIPAll"
                  :icon="mdiIpOutline"
                  disabled
                />
              </FormField>

              <FormField :label="$t('objectTypes.user.singular')">
                <FormControl
                  v-model="activity.requestUsername"
                  :icon="mdiAccountOutline"
                  :link="
                    activity?.requestUser?.id
                      ? `/users/${activity.requestUser.id}`
                      : null
                  "
                  disabled
                />
              </FormField>
            </FormField>

            <FormField>
              <FormField
                :label="$t('views.activities.detail.requestPermission')"
              >
                <FormControl
                  v-model="activity.requestPermission"
                  :icon="mdiKeyOutline"
                  disabled
                />
              </FormField>

              <FormField label="Response Code">
                <FormControl
                  v-model="activity.responseCode"
                  :icon="mdiNumeric"
                  disabled
                />
              </FormField>
            </FormField>

            <FormField>
              <FormField :label="$t('views.activities.detail.method')">
                <FormControl
                  v-model="activity.requestMethod"
                  :icon="mdiHelpBoxOutline"
                  disabled
                />
              </FormField>

              <FormField :label="$t('common.url')">
                <FormControl
                  v-model="activity.requestUrl"
                  :icon="mdiSlashForwardBox"
                  disabled
                />
              </FormField>
            </FormField>
          </BaseTab>

          <BaseTab
            id="request-params"
            :title="$t('views.activities.detail.requestParams')"
          >
            <table>
              <thead>
                <tr>
                  <th>{{ $t('views.activities.detail.parameter') }}</th>

                  <th>{{ $t('common.value') }}</th>
                </tr>
              </thead>

              <tbody>
                <tr
                  v-for="[key, parameter] in sortedRequestParameter"
                  :key="key"
                >
                  <td data-label="Parameter">{{ key }}</td>

                  <td :data-label="$t('common.value')">{{ parameter }}</td>
                </tr>
              </tbody>
            </table>
          </BaseTab>

          <BaseTab
            id="request-headers"
            :title="$t('views.activities.detail.requestHeaders')"
          >
            <table>
              <thead>
                <tr>
                  <th>{{ $t('views.activities.detail.parameter') }}</th>

                  <th>{{ $t('common.value') }}</th>
                </tr>
              </thead>

              <tbody>
                <tr v-for="[key, parameter] in sortedRequestHeaders" :key="key">
                  <td data-label="Parameter">{{ key }}</td>

                  <td :data-label="$t('common.value')">{{ parameter }}</td>
                </tr>
              </tbody>
            </table>
          </BaseTab>

          <BaseTab
            id="response-headers"
            :title="$t('views.activities.detail.responseHeaders')"
          >
            <table>
              <thead>
                <tr>
                  <th>{{ $t('views.activities.detail.parameter') }}</th>

                  <th>{{ $t('common.value') }}</th>
                </tr>
              </thead>

              <tbody>
                <tr
                  v-for="[key, parameter] in sortedResponseHeaders"
                  :key="key"
                >
                  <td data-label="Parameter">{{ key }}</td>

                  <td :data-label="$t('common.value')">{{ parameter }}</td>
                </tr>
              </tbody>
            </table>
          </BaseTab>
        </BaseTabs>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
