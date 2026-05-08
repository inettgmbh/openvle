<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'vue-toastification'

import CardBoxModal from '@/components/CardBoxModal.vue'
import TablePagination from '@/components/Tables/TablePagination.vue'
import backend from '@/services'

const toast = useToast()
const { t } = useI18n()

const items = ref([])

async function fetchObjects() {
  try {
    const response = await backend.proxmox.getClusterLog()
    items.value = response.items
    items.value.count = response.pageDetails.totalCount
  } catch (error) {
    toast.error(t('common.loadErrorPlural', { entities: 'Proxmox Logs' }))
  }
}
fetchObjects()

const isModalActive = ref(false)

// const handlePagination = (page, perPage) => {emit('paginationChanged', page, perPage, objectModel)}

const perPage = ref(25)

const currentPage = ref(0)

const itemsPaginated = computed(() =>
  items.value.slice(
    perPage.value * currentPage.value,
    perPage.value * currentPage.value,
  ),
)
</script>

<template>
  <CardBoxModal
    v-model="isModalActive"
    :title="$t('components.tableProxmoxLogs.sampleModal')"
  >
    <p>Lorem ipsum dolor sit amet <b>adipiscing elit</b></p>

    <p>This is sample modal</p>
  </CardBoxModal>

  <table>
    <thead>
      <tr>
        <th>Start Time</th>

        <th>End Time</th>

        <th>Node</th>

        <th>Username</th>

        <th>Description</th>

        <th>Status</th>
      </tr>
    </thead>

    <tbody>
      <tr v-for="client in itemsPaginated" :key="client.id">
        <td
          data-:label="$t('components.tableProxmoxLogs.startTime')"
          class="lg:w-1 whitespace-nowrap"
        >
          {{ client.time }}
        </td>

        <td
          data-:label="$t('components.tableProxmoxLogs.endTime')"
          class="lg:w-1 whitespace-nowrap"
        >
          {{ client.company }}
        </td>

        <td
          data-:label="$t('components.tableProxmoxLogs.node')"
          class="lg:w-1 whitespace-nowrap"
        >
          {{ client.city }}
        </td>

        <td
          data-:label="$t('components.tableProxmoxLogs.username')"
          class="lg:w-1 whitespace-nowrap"
        >
          {{ client.city }}
        </td>

        <td data-:label="$t('components.tableProxmoxLogs.description')">
          {{ client.city }}
        </td>

        <td data-:label="$t('common.status')" class="lg:w-1 whitespace-nowrap">
          {{ client.city }}
        </td>
      </tr>
    </tbody>
  </table>

  <TablePagination
    :current-page="currentPage"
    :items-total="itemsTotal"
    :per-page="perPage"
  />
</template>
