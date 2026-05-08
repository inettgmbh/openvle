<script setup>
import {
  mdiChartBar,
  mdiEarth,
  mdiFileTree,
  mdiIdentifier,
  mdiInformation,
  mdiIpNetwork,
  mdiLabel,
  mdiServer,
  mdiServerOff,
} from '@mdi/js'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseTab from '@/components/BaseTab.vue'
import BaseTable from '@/components/BaseTable.vue'
import BaseTabs from '@/components/BaseTabs.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxComponentHeader from '@/components/CardBoxComponentHeader.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import MetricsSelectionPanel from '@/components/MetricsSelectionPanel.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import PillTag from '@/components/PillTag.vue'
import ProxmoxRrdChart from '@/components/ProxmoxRrdChart.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { checkObjectPermissions, usePermissionRefs } from '@/utils/dataUtils.js'
import { usePaginationChild } from '@/utils/pagination'

const { t } = useI18n()
const permissionRefs = usePermissionRefs()

const customChartLoaded = ref(false)
const dataLoading = ref(true)
const node = ref({})
const nodeStatistics = ref([{}])
const nodeTasks = ref([{}])
const permissionsLoaded = ref(false)
const route = useRoute()
const selectedMetrics = ref([])
const selectedTimeframe = ref('hour')
const selectedCf = ref({})
const toast = useToast()

/* PAGINATION ONLY */
const { handleTabChanged } = usePaginationChild({
  children: [
    {
      name: 'statistics',
      perPage: 100,
      currentPage: 1,
      sortColumnKey: 'name',
      sortDirection: 'asc',
      fetchData: fetchNodeStatistics,
    },
    {
      name: 'tasks',
      perPage: 100,
      currentPage: 1,
      sortColumnKey: 'name',
      sortDirection: 'asc',
      fetchData: fetchNodeTasks,
    },
  ],
  fetchArgs: () => [route.params.id],
})
/**/

async function handleSubmit({
  hosts = [],
  metrics = [],
  timeframe = 'hour',
  cf = 'AVERAGE',
}) {
  selectedMetrics.value = metrics.map((item) => item.value)
  selectedTimeframe.value = timeframe
  selectedCf.value = cf

  fetchNodeStatistics()

  customChartLoaded.value = true
}

async function fetchNode() {
  try {
    dataLoading.value = true
    await backend.proxmox.getNode(route.params.id).then((response) => {
      node.value = response
    })
  } catch (error) {
    toast.error(t('views.proxmox.nodeDetail.loadError'))
  } finally {
    dataLoading.value = false
  }
}

async function fetchNodeStatistics() {
  try {
    dataLoading.value = true

    const data = await backend.proxmox.getNodeRRDData(
      route.params.id,
      selectedTimeframe.value,
      selectedCf.value,
    )
    nodeStatistics.value = data
  } catch (error) {
    toast.error(`${t('common.errorLoading')}: ${error?.code}`)
  } finally {
    dataLoading.value = false
  }
}

async function fetchNodeTasks() {
  try {
    dataLoading.value = true

    const data = await backend.proxmox.getClusterTasksByNode(route.params.id)
    nodeTasks.value = data
  } catch (error) {
    toast.error(error)
  } finally {
    dataLoading.value = false
  }
}

onMounted(async () => {
  await fetchNode()

  await checkObjectPermissions('system', '*', permissionRefs, [], [])

  permissionsLoaded.value = true
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiServer"
        :title="$t('views.proxmox.nodeDetail.title', { id: route.params.id })"
        main
        docs-path="/docs/usage/openvle/proxmox/"
        :reload="fetchNode"
      >
        <PillTag
          v-if="node.name"
          disabled
          :label="node.online == 1 ? 'Online' : 'Offline'"
          :color="node.online == 1 ? 'success' : 'danger'"
          :icon="node.online == 1 ? mdiServer : mdiServerOff"
        />
      </SectionTitleLineWithButton>

      <CardBox>
        <BaseTabs v-if="permissionsLoaded" @tab-changed="handleTabChanged">
          <BaseTab id="node" :title="$t('common.node')">
            <FormField>
              <FormField
                :label="$t('views.proxmox.nodeDetail.hostname')"
                :help="$t('views.proxmox.nodeDetail.hostnameHelp')"
              >
                <FormControl v-model="node.name" :icon="mdiLabel" disabled />
              </FormField>

              <FormField
                label="FQDN"
                :help="$t('views.proxmox.nodeDetail.fqdnHelp')"
              >
                <FormControl v-model="node.fqdn" :icon="mdiEarth" disabled />
              </FormField>
            </FormField>

            <FormField>
              <FormField
                :label="$t('views.proxmox.nodeDetail.ipv4Address')"
                :help="$t('views.proxmox.nodeDetail.ipv4AddressHelp')"
              >
                <FormControl v-model="node.ip" :icon="mdiIpNetwork" disabled />
              </FormField>

              <FormField
                label="Node ID"
                :help="$t('views.proxmox.nodeDetail.nodeIdHelp')"
              >
                <FormControl
                  v-model="node.node_id"
                  :icon="mdiIdentifier"
                  disabled
                />
              </FormField>
            </FormField>
          </BaseTab>

          <BaseTab id="statistics" :title="$t('common.statistics')">
            <SectionTitleLineWithButton
              :icon="mdiChartBar"
              :title="$t('common.statistics')"
              :reload="fetchNodeStatistics"
            />

            <!-- Charts: note -->
            <NotificationBar
              :dismissable="false"
              color="info"
              :icon="mdiInformation"
            >
              <b>{{ $t('views.proxmox.nodeDetail.chartsInfo') }}</b>
            </NotificationBar>

            <!-- Charts: metrics filter -->
            <MetricsSelectionPanel
              :hosts="[
                {
                  ...node,
                  value: node.name,
                },
              ]"
              :type="'node'"
              @submit="handleSubmit"
            />

            <!-- Charts: CPU and memory chart -->
            <CardBox class="mb-6">
              <ProxmoxRrdChart
                v-if="node.name && nodeStatistics"
                :rrd-data="nodeStatistics"
                :title="'Proxmox VE Node: ' + node.fqdn"
                :metrics="['cpu', 'mem']"
                :timeframe="selectedTimeframe"
              />
            </CardBox>

            <!-- Charts: netin and netout chart -->
            <CardBox class="mb-6">
              <ProxmoxRrdChart
                v-if="node.name && nodeStatistics"
                :rrd-data="nodeStatistics"
                :title="'Proxmox VE Node: ' + node.fqdn"
                :metrics="['netin', 'netout']"
                :timeframe="selectedTimeframe"
              />
            </CardBox>

            <!-- Charts: custom chart -->
            <CardBox
              v-if="node.name && nodeStatistics && customChartLoaded"
              class="mb-6"
            >
              <CardBoxComponentHeader
                :title="$t('views.proxmox.nodeDetail.customChart')"
              />

              <ProxmoxRrdChart
                :rrd-data="nodeStatistics"
                :title="'Proxmox VE Node: ' + node.fqdn"
                :metrics="selectedMetrics"
                :timeframe="selectedTimeframe"
              />
            </CardBox>
          </BaseTab>

          <BaseTab id="tasks" :title="$t('objectTypes.task.plural')">
            <SectionTitleLineWithButton
              :icon="mdiFileTree"
              :title="$t('objectTypes.task.plural')"
              :reload="fetchNodeTasks"
            />

            <BaseTable
              :current-page="1"
              :per-page="100"
              :items-total="nodeTasks.length ?? 0"
              :data="nodeTasks"
              :loading="dataLoading"
              :created-column-enabled="false"
              object-model="proxmox/tasks"
              :buttons="[]"
              :columns="[
                {
                  label: $t('views.proxmox.nodeDetail.columns.start'),
                  key: 'starttime',
                  sortable: false,
                  formatter: (value) => new Date(value * 1000).toLocaleString(),
                  width: '145px',
                },
                {
                  label: $t('views.proxmox.nodeDetail.columns.end'),
                  key: 'endtime',
                  sortable: false,
                  formatter: (value) => new Date(value * 1000).toLocaleString(),
                  width: '145px',
                },
                {
                  label: $t('objectTypes.user.singular'),
                  key: 'user',
                  sortable: false,
                  width: '100px',
                },
                {
                  label: $t('common.type'),
                  key: 'type',
                  sortable: false,
                  width: '80px',
                },
                {
                  label: 'ID',
                  key: 'id',
                  sortable: false,
                  width: '60px',
                },
                {
                  label: $t('common.status'),
                  key: 'status',
                  sortable: false,
                  width: '60px',
                },
                {
                  label: 'UPID',
                  key: 'upid',
                  sortable: false,
                  width: '220px',
                },
              ]"
            />
          </BaseTab>
        </BaseTabs>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
