<script setup>
import BaseTable from '../BaseTable.vue'

import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { formatGermanNumber } from '@/utils/dataUtils'

const props = defineProps({
  data: {
    type: [Array, Object],
    required: true,
  },
  loading: {
    type: Boolean,
    default: true,
  },
})

const router = useRouter()

const objects = computed(() => {
  let raw = props.data
  if (raw && typeof raw === 'object' && 'value' in raw) raw = raw.value
  let arr = []
  if (Array.isArray(raw)) arr = raw
  else if (raw && typeof raw === 'object') arr = Object.values(raw)
  return arr
    .slice()
    .sort((a, b) => (a.hostname || '').localeCompare(b.hostname || ''))
})

function getColor(used, total) {
  const percent = total > 0 ? (used / total) * 100 : 0
  if (percent < 75) return 'success'
  if (percent < 90) return 'warning'
  return 'danger'
}

const labels = computed(() => {
  return objects.value.map((node) => {
    const cpuUsed = parseFloat(node.resources?.cpu?.used ?? 0)
    const cpuUsable = parseFloat(node.resources?.cpu?.usable ?? 0)
    const ramUsed = parseFloat(node.resources?.ram?.used ?? 0)
    const ramUsable = parseFloat(node.resources?.ram?.usable ?? 0)
    const storageUsed = parseFloat(node.resources?.storage?.used ?? 0)
    const storageTotal = parseFloat(node.resources?.storage?.total ?? 0)

    return {
      ...node,
      cpuLabel: `${formatGermanNumber(cpuUsed.toFixed(2))} / ${formatGermanNumber(cpuUsable.toFixed(0))} Cores`,
      cpuColor: getColor(cpuUsed, cpuUsable),
      ramLabel: `${formatGermanNumber(ramUsed.toFixed(2))} / ${formatGermanNumber(ramUsable.toFixed(0))} GB`,
      ramColor: getColor(ramUsed, ramUsable),
      storageLabel: `${formatGermanNumber(storageUsed.toFixed(2))} / ${formatGermanNumber(storageTotal.toFixed(0))} GB`,
      storageColor: getColor(storageUsed, storageTotal),
    }
  })
})

const viewObjects = (obj, model) => {
  return router.push({ path: `/proxmox/nodes/${obj.hostname}` })
}
</script>

<template>
  <BaseTable
    :current-page="1"
    :per-page="100"
    :items-total="objects.length"
    :data="labels"
    :loading="false"
    :created-column-enabled="false"
    object-model="proxmox/nodes"
    :buttons="['view']"
    :emit-view-object="true"
    :pagination="false"
    :columns="[
      {
        label: $t('common.hostname'),
        key: 'fqdn',
        sortable: false,
        width: '200px',
      },
      {
        label: $t('common.status'),
        key: 'status',
        sortable: false,
        color: () => 'success',
        width: '100px',
      },
      {
        label: $t('common.cpuUsage'),
        key: 'cpuLabel',
        sortable: false,
        color: () => 'success',
        width: '180px',
      },
      {
        label: $t('common.memory'),
        key: 'ramLabel',
        sortable: false,
        color: () => 'success',
        width: '180px',
      },
      {
        label: $t('common.storageSpace'),
        key: 'storageLabel',
        sortable: false,
        color: () => 'success',
        width: '180px',
      },
    ]"
    @view-object="viewObjects"
  />
</template>
