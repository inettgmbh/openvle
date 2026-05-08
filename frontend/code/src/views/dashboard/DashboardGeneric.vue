<script setup>
import {
  mdiAccountBoxOutline,
  mdiAlert,
  mdiCalendarClock,
  mdiCardTextOutline,
  mdiChartTimelineVariant,
  mdiCpu64Bit,
  mdiDatabase,
  mdiHelpBoxOutline,
  mdiMemory,
  mdiMonitor,
  mdiRemoteDesktop,
  mdiSchoolOutline,
} from '@mdi/js'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'vue-toastification'

import CardBox from '@/components/CardBox.vue'
import CardBoxComponentBody from '@/components/CardBoxComponentBody.vue'
import CardBoxComponentHeader from '@/components/CardBoxComponentHeader.vue'
import CardBoxWidget from '@/components/CardBoxWidget.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import TableProxmoxNodes from '@/components/Tables/TableProxmoxNodes.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { useMainStore } from '@/stores/main.js'

const { t } = useI18n()
const mainStore = useMainStore()
const toast = useToast()

const userRole = computed(() => mainStore.getUserRole)
const appLabel = computed(() => mainStore.settings?.branding?.app?.name)
const appContactSupport = computed(
  () => mainStore.settings?.branding?.support?.email,
)
const appContactURL = computed(() => mainStore.settings?.branding?.support?.url)
const appDocsLabel = computed(() => mainStore.settings?.branding?.docs?.label)
const appDocsURL = computed(() => mainStore.settings?.branding?.docs?.url)

const dataLoading = ref(true)

const stats = ref({
  vms: {
    own_total: 0,
    own_running: 0,
    all_total: 0,
    all_running: 0,
    all_error: 0,
  },
  courses: {
    own_total: 0,
  },
  events: {
    own_total: 0,
    own_running: 0,
    all_total: 0,
    all_running: 0,
  },
  connections: {
    own_total: 0,
    all_total: 0,
  },
  users: {
    all_total: 0,
    all_active: 0,
    all_locked: 0,
  },
  resources: {
    ram: {
      used: 0.0,
      unit: '',
      usable: 0,
    },
    cpu: {
      used: 0,
      unit: '',
      usable: 0,
    },
    storage: {
      used: 0,
      unit: '',
      total: 0,
    },
  },
  nodes: {},
})

async function fetchStats() {
  try {
    dataLoading.value = true
    await backend.statistics.getDashboard().then((response) => {
      stats.value = response
      dataLoading.value = false
    })
  } catch (error) {
    toast.error(t('views.dashboard.loadError'))
  }
}

onMounted(() => {
  fetchStats()
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiChartTimelineVariant"
        :title="$t('objectTypes.dashboard.singular')"
        main
      />

      <div v-if="userRole === 'admin' || userRole === 'verwaltende'">
        <!-- Stats Header -->
        <SectionTitleLineWithButton
          :icon="mdiCardTextOutline"
          :title="$t('views.dashboard.statistics')"
          :reload="fetchStats"
        />

        <!-- Admins: CPU / Ram / Storage -->
        <div
          v-if="userRole === 'admin'"
          class="grid grid-cols-1 gap-6 lg:grid-cols-3 mb-6"
        >
          <CardBoxWidget
            color="text-blue-500"
            :icon="mdiCpu64Bit"
            :number="
              stats?.resources?.cpu?.usable
                ? parseFloat(
                    (
                      ((stats?.resources?.cpu?.used ?? 0) /
                        (stats?.resources?.cpu?.usable || 1)) *
                      100
                    ).toFixed(2),
                  )
                : 0
            "
            suffix=" %"
            label="CPU"
            :sub-string="
              parseFloat(stats?.resources?.cpu?.used?.toFixed(0) ?? 0) +
              ' / ' +
              parseFloat(stats?.resources?.cpu?.usable?.toFixed(0) ?? 0) +
              ' Cores'
            "
          />

          <CardBoxWidget
            color="text-red-500"
            :icon="mdiMemory"
            :number="
              stats?.resources?.ram?.usable
                ? parseFloat(
                    (
                      ((stats?.resources?.ram?.used ?? 0) /
                        (stats?.resources?.ram?.usable || 1)) *
                      100
                    ).toFixed(2),
                  )
                : 0
            "
            suffix=" %"
            :label="$t('views.dashboard.memory')"
            :sub-string="
              parseFloat(stats?.resources?.ram?.used?.toFixed(0) ?? 0) +
              ' / ' +
              parseFloat(stats?.resources?.ram?.usable?.toFixed(0) ?? 0) +
              ' ' +
              (stats?.resources?.ram?.unit ?? 'GB')
            "
          />

          <CardBoxWidget
            color="text-emerald-500"
            :icon="mdiDatabase"
            :number="
              stats?.resources?.storage?.total
                ? parseFloat(
                    (
                      ((stats?.resources?.storage?.used ?? 0) /
                        (stats?.resources?.storage?.total || 1)) *
                      100
                    ).toFixed(2),
                  )
                : 0
            "
            suffix=" %"
            :label="$t('views.dashboard.storageLocal')"
            :sub-string="
              parseFloat(stats?.resources?.storage?.used?.toFixed(0) ?? 0) +
              ' / ' +
              parseFloat(stats?.resources?.storage?.total?.toFixed(0) ?? 0) +
              ' ' +
              (stats?.resources?.storage?.unit ?? 'GB')
            "
          />
        </div>

        <!-- Admins / Verwaltende: VMs / Connections / Events -->
        <div
          v-if="userRole === 'admin' || userRole === 'verwaltende'"
          class="grid grid-cols-1 gap-6 lg:grid-cols-3 mb-6"
        >
          <CardBoxWidget
            color="text-emerald-500"
            :icon="mdiMonitor"
            :number="stats?.vms?.all_total ?? stats?.vms?.own_total ?? 0"
            :label="$t('views.dashboard.virtualMachines')"
            :sub-string="
              (stats?.vms?.all_running ?? stats?.vms?.own_running ?? 0) +
              ` ${t('views.dashboard.running')}`
            "
          />

          <CardBoxWidget
            color="text-blue-500"
            :icon="mdiRemoteDesktop"
            :number="stats?.connections?.all_total ?? 0"
            :label="$t('views.dashboard.connections')"
            :sub-string="
              (stats?.connections?.own_total ?? 0) +
              ` ${t('views.dashboard.own')}`
            "
          />

          <CardBoxWidget
            color="text-red-500"
            :icon="mdiCalendarClock"
            :number="stats?.events?.all_total ?? 0"
            :label="$t('views.dashboard.events')"
            :sub-string="
              (stats?.events?.all_running ?? 0) +
              ` ${t('views.dashboard.running')}`
            "
          />
        </div>

        <!-- Admins / Verwaltende: Users / Courses / Errors -->
        <div
          v-if="userRole === 'admin' || userRole === 'verwaltende'"
          class="grid grid-cols-1 gap-6 lg:grid-cols-3 mb-6"
        >
          <CardBoxWidget
            color="text-red-500"
            :icon="mdiAccountBoxOutline"
            :number="stats?.users?.all_total ?? 0"
            :label="$t('views.dashboard.users')"
            :sub-string="
              (stats?.users?.all_active ?? 0) +
              ` ${t('views.dashboard.activated')}`
            "
          />

          <CardBoxWidget
            color="text-emerald-500"
            :icon="mdiSchoolOutline"
            :number="stats?.courses?.all_total ?? 0"
            :label="$t('views.dashboard.courses')"
            :sub-string="
              (stats?.courses?.own_total ?? 0) + ` ${t('views.dashboard.own')}`
            "
          />

          <CardBoxWidget
            color="text-blue-500"
            :icon="mdiAlert"
            :number="stats?.vms?.all_error ?? 0"
            :label="$t('views.dashboard.errors')"
            :sub-string="
              (stats?.vms?.all_error ?? 0) +
              ` ${t('views.dashboard.faultyObjects')}`
            "
          />
        </div>
      </div>

      <!-- Proxmox VE Nodes -->
      <div v-if="userRole === 'admin'">
        <SectionTitleLineWithButton
          :icon="mdiCardTextOutline"
          :title="$t('views.dashboard.proxmoxServers')"
          :reload="fetchStats"
        />

        <CardBox class="grid mb-6">
          <TableProxmoxNodes
            :data="stats?.nodes ?? {}"
            :loading="dataLoading"
          />
        </CardBox>
      </div>

      <!-- Welcome infos -->
      <CardBox class="grid mb-6">
        <CardBoxComponentHeader
          :icon="mdiCardTextOutline"
          :title="$t('views.dashboard.welcomeTitle', { appLabel })"
        ></CardBoxComponentHeader>

        <CardBoxComponentBody>
          <p class="pb-1.5 text-justify">
            {{ $t('views.dashboard.welcomeParagraph1', { appLabel }) }}
          </p>

          <p class="pb-1.5 text-justify">
            {{ $t('views.dashboard.welcomeParagraph2') }}
          </p>

          <p class="pb-1.5 text-justify">
            {{ $t('views.dashboard.welcomeParagraph3') }}
          </p>

          <p class="pb-1.5 text-justify">
            {{ $t('views.dashboard.welcomeParagraph4') }}
          </p>

          <p class="text-justify">
            {{ $t('views.dashboard.welcomeParagraph5') }}
          </p>
        </CardBoxComponentBody>
      </CardBox>

      <!-- Stats Header -->
      <SectionTitleLineWithButton
        v-if="userRole !== 'admin' && userRole !== 'verwaltende'"
        :icon="mdiCardTextOutline"
        :title="$t('views.dashboard.statistics')"
        :reload="fetchStats"
      />

      <!-- Students: VMs / Connections / Events -->
      <div
        v-if="userRole !== 'admin' && userRole !== 'verwaltende'"
        class="grid grid-cols-1 gap-6 lg:grid-cols-3 mb-6"
      >
        <CardBoxWidget
          color="text-emerald-500"
          :icon="mdiMonitor"
          :number="stats?.vms?.own_total"
          :label="$t('views.dashboard.virtualMachines')"
          :sub-string="
            stats?.vms?.own_running + ` ${t('views.dashboard.running')}`
          "
        />

        <CardBoxWidget
          color="text-blue-500"
          :icon="mdiRemoteDesktop"
          :number="stats?.connections?.own_total"
          :label="$t('views.dashboard.connections')"
        />

        <CardBoxWidget
          color="text-red-500"
          :icon="mdiCalendarClock"
          :number="stats?.events?.own_total"
          :label="$t('views.dashboard.events')"
          :sub-string="
            stats?.events?.own_running + ` ${t('views.dashboard.running')}`
          "
        />
      </div>

      <!-- Documentation & Help-->
      <CardBox>
        <CardBoxComponentHeader
          :icon="mdiHelpBoxOutline"
          :title="$t('views.dashboard.docsAndHelp')"
        />

        <CardBoxComponentBody>
          <p class="pb-1.5 text-justify">
            {{ $t('views.dashboard.docsText1') }}
            <a target="_blank" :href="appDocsURL" class="underline">{{
              appDocsLabel
            }}</a
            >.
          </p>

          <p class="text-justify">
            {{ $t('views.dashboard.docsText2') }}
            <a target="_blank" :href="appContactURL" class="underline">{{
              $t('views.dashboard.supportCenter')
            }}</a
            >.

            <br />
            {{ $t('views.dashboard.feedbackNote') }}
          </p>
        </CardBoxComponentBody>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
