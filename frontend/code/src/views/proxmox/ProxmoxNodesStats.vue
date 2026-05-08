<script setup>
import { mdiChartBar } from '@mdi/js'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'vue-toastification'

import CardBox from '@/components/CardBox.vue'
import MetricsSelectionPanel from '@/components/MetricsSelectionPanel.vue'
import ProxmoxRrdChart from '@/components/ProxmoxRrdChart.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { checkObjectPermissions, usePermissionRefs } from '@/utils/dataUtils.js'

const permissionRefs = usePermissionRefs()
const toast = useToast()
const { t } = useI18n()

/* PAGINATION ONLY */
const dataLoading = ref(true)
/**/

const nodesStats = ref([])

const permissionsLoaded = ref(false)

const proxmoxNodes = ref([])
const selectedHosts = ref([])
const selectedMetrics = ref([])
const selectedTimeframe = ref({})
const selectedCf = ref({})

async function fetchNodes() {
  try {
    dataLoading.value = true

    const response = await backend.proxmox.getNodes()

    proxmoxNodes.value = response
      .sort((a, b) => a.name.localeCompare(b.name))
      .map((node, index) => ({
        ...node,
        value: node.name,
        label: node.name,
        selected: index === 0,
      }))
  } catch (error) {
    toast.error(error)
  } finally {
    dataLoading.value = false
  }
}

async function fetchNodeStats() {
  try {
    dataLoading.value = true

    const fetches = selectedHosts.value.map(async (node) => {
      const data = await backend.proxmox.getNodeRRDData(
        node.name,
        selectedTimeframe.value,
        selectedCf.value,
      )
      nodesStats.value[node.name] = data
    })

    await Promise.all(fetches)
  } catch (error) {
    toast.error(t('views.proxmox.nodesStats.error', { code: error?.code }))
  } finally {
    dataLoading.value = false
  }
}

async function handleSubmit({
  hosts = [],
  metrics = [],
  timeframe = 'hour',
  cf = 'AVERAGE',
}) {
  selectedHosts.value = hosts
  selectedMetrics.value = metrics.map((item) => item.value)
  selectedTimeframe.value = timeframe
  selectedCf.value = cf

  fetchNodeStats()
}

onMounted(async () => {
  await fetchNodes()

  await checkObjectPermissions('system', '*', permissionRefs, [], [])

  permissionsLoaded.value = true
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiChartBar"
        :title="$t('views.proxmox.nodesStats.proxmoxVeStatistics')"
        main
        docs-path="/docs/usage/openvle/proxmox/"
        :reload="fetchNodeStats"
      >
      </SectionTitleLineWithButton>

      <MetricsSelectionPanel
        :hosts="proxmoxNodes"
        :type="'node'"
        @submit="handleSubmit"
      />

      <CardBox v-for="host in selectedHosts" :key="host.fqdn" class="mb-6">
        <ProxmoxRrdChart
          v-if="host.name && nodesStats && nodesStats[host.name]"
          :rrd-data="nodesStats[host.name]"
          :title="t('views.proxmox.nodesStats.chartTitle', { fqdn: host.fqdn })"
          :metrics="selectedMetrics"
          :timeframe="selectedTimeframe"
        />
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
