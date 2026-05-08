<script setup>
import { mdiCpu64Bit, mdiDatabase, mdiMemory, mdiServer } from '@mdi/js'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'vue-toastification'

import CardBox from '@/components/CardBox.vue'
import CardBoxWidget from '@/components/CardBoxWidget.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import TableProxmoxNodes from '@/components/Tables/TableProxmoxNodes.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { checkObjectPermissions, usePermissionRefs } from '@/utils/dataUtils.js'

const permissionRefs = usePermissionRefs()
const toast = useToast()
const { t } = useI18n()

/* PAGINATION ONLY */
const dataLoading = ref(true)
/**/

const permissionsLoaded = ref(false)

const stats = ref({ nodes: {} })

async function fetchStats() {
  try {
    dataLoading.value = true
    await backend.statistics.getDashboard().then((response) => {
      stats.value = response
      dataLoading.value = false
    })
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', { entities: t('common.statistics') }),
    )
  }
}

onMounted(async () => {
  await fetchStats()

  await checkObjectPermissions('system', '*', permissionRefs, [], [])

  permissionsLoaded.value = true
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiServer"
        :title="$t('views.proxmox.nodeList.proxmoxVeNodes')"
        main
        docs-path="/docs/usage/openvle/proxmox/"
        :reload="fetchStats"
      >
      </SectionTitleLineWithButton>

      <div class="grid grid-cols-1 gap-6 lg:grid-cols-3 mb-6">
        <CardBoxWidget
          color="text-blue-500"
          :icon="mdiCpu64Bit"
          :number="
            stats?.resources?.cpu?.usable
              ? parseFloat(
                  (
                    ((stats.resources.cpu.used ?? 0) /
                      (stats.resources.cpu.usable || 1)) *
                    100
                  ).toFixed(2),
                )
              : 0
          "
          suffix=" %"
          :label="$t('views.proxmox.nodeList.cpu')"
          :sub-string="
            parseFloat(stats?.resources?.cpu?.used?.toFixed(0) ?? 0) +
            ' ' +
            t('common.of') +
            ' ' +
            parseFloat(stats?.resources?.cpu?.usable?.toFixed(0) ?? 0) +
            ' ' +
            t('views.proxmox.nodeList.cores')
          "
        />

        <CardBoxWidget
          color="text-red-500"
          :icon="mdiMemory"
          :number="
            stats?.resources?.ram?.usable
              ? parseFloat(
                  (
                    ((stats.resources.ram.used ?? 0) /
                      (stats.resources.ram.usable || 1)) *
                    100
                  ).toFixed(2),
                )
              : 0
          "
          suffix=" %"
          :label="$t('views.proxmox.nodeList.memory')"
          :sub-string="
            parseFloat(stats?.resources?.ram?.used?.toFixed(0) ?? 0) +
            ' ' +
            t('common.of') +
            ' ' +
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
                    ((stats.resources.storage.used ?? 0) /
                      (stats.resources.storage.total || 1)) *
                    100
                  ).toFixed(2),
                )
              : 0
          "
          suffix=" %"
          :label="$t('views.proxmox.nodeList.storageLokal')"
          :sub-string="
            parseFloat(stats?.resources?.storage?.used?.toFixed(0) ?? 0) +
            ' ' +
            t('common.of') +
            ' ' +
            parseFloat(stats?.resources?.storage?.total?.toFixed(0) ?? 0) +
            ' ' +
            (stats?.resources?.storage?.unit ?? 'GB')
          "
        />
      </div>

      <CardBox class="mb-6" has-table>
        <TableProxmoxNodes :data="stats.nodes ?? {}" :loading="dataLoading" />
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
