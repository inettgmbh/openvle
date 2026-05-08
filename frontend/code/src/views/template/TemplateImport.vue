<script setup>
import {
  mdiApplicationBrackets,
  mdiInformation,
  mdiNumeric,
  mdiRename,
  mdiVectorArrangeAbove,
} from '@mdi/js'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseDivider from '@/components/BaseDivider.vue'
import BaseMarkdown from '@/components/BaseMarkdown.vue'
import CardBox from '@/components/CardBox.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import SearchControl from '@/components/SearchControl.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import TemplateCreateWarning from '@/components/TemplateCreateWarning.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import router from '@/router'
import backend from '@/services'

const { t } = useI18n()
const route = useRoute()
const toast = useToast()
const template = ref({
  pveId: null,
  name: '',
  description: '',
  cpu: 0,
  ram: 0,
  os: null,
})
const templateLoaded = ref(false)
const showInfos = computed(() => templateLoaded.value)
const disablePVEID = computed(() => templateLoaded.value)
const showCreateWarning = ref(false)

async function fetchTemplateDetails() {
  try {
    const pveId = template.value.pveId
    backend.beginSilent()
    const details = await backend.templates.loadPVEDetails(pveId)
    template.value = {
      ...details,
      pveId,
      cpu: details.cores * details.sockets,
      ram: details.memory / 1024,
    }
    templateLoaded.value = true
    toast.success(
      t('common.loadSuccess', { entity: t('objectTypes.template.singular') }),
    )
  } catch (error) {
    handleError(
      error,
      t('common.loadErrorPlural', {
        entities: t('objectTypes.template.plural'),
      }),
    )
  } finally {
    backend.endSilent()
  }
}

async function importTemplate() {
  if (!templateLoaded.value) {
    await fetchTemplateDetails()
    return
  } else {
    showCreateWarning.value = true
  }
}

async function confirmed() {
  try {
    backend.beginSilent()
    const res = await backend.templates.importFromPVE(template.value.pveId)
    updateTemplate(res.id)
    toast.success(
      t('common.importSuccess', { entity: t('objectTypes.template.singular') }),
    )
    router.push({ path: `/templates/${res.id}` })
  } catch (error) {
    handleError(
      error,
      t('common.importError', { entity: t('objectTypes.template.singular') }),
    )
  } finally {
    backend.endSilent()
  }
}

function handleError(error, defaultMessage) {
  const message = error.response?.data?.detail || defaultMessage
  toast.error(message, { timeout: 4000 })
}

async function updateTemplate(id) {
  try {
    await backend.templates.update(id, {
      name: template.value.name,
      description: template.value.description,
      cpu: template.value.cpu,
      ram: template.value.ram * 1024,
      os: template.value.os,
    })
  } catch (error) {
    toast.error(t('views.templates.import.updateError'))
  }
}

onMounted(() => {
  template.value.pveId = route.query.pveId || ''
})
</script>

<template>
  <!-- Template Create Warning -->
  <TemplateCreateWarning
    v-model="showCreateWarning"
    :scrollable="true"
    @confirmed="confirmed"
  />

  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiVectorArrangeAbove"
        :title="
          $t('common.importTitle', {
            entity: $t('objectTypes.template.singular'),
          })
        "
        main
        docs-path="/docs/usage/openvle/vms/templates/"
      />

      <CardBox is-form @submit.prevent="importTemplate">
        <NotificationBar
          v-if="!templateLoaded"
          :dismissable="false"
          color="info"
          :icon="mdiInformation"
        >
          <p>
            <b>{{ $t('views.templates.import.enterProxmoxId') }}</b>
          </p>
        </NotificationBar>

        <NotificationBar
          v-if="templateLoaded"
          :dismissable="false"
          color="success"
          :icon="mdiInformation"
        >
          <p>
            <b>
              {{ $t('views.templates.import.valuesPrefilledInfo') }}
            </b>

            <br />
            {{ $t('views.templates.import.adjustIfNeeded') }}
            <br />

            <b>{{ $t('views.templates.import.osMustBeSet') }}</b>
          </p>
        </NotificationBar>

        <BaseDivider />

        <!-- Proxmox ID Input -->
        <FormField
          :label="$t('views.templates.import.proxmoxId')"
          :help="$t('views.templates.import.proxmoxIdHelp')"
        >
          <FormControl
            v-model="template.pveId"
            :icon="mdiNumeric"
            type="number"
            placeholder="100"
            required
            :min="100"
            :disabled="disablePVEID"
            :autofocus="true"
          />
        </FormField>

        <BaseDivider />

        <!-- VM Details -->
        <div v-if="showInfos">
          <FormField>
            <FormField
              :label="$t('common.name')"
              :help="$t('views.templates.form.nameHelp')"
            >
              <FormControl v-model="template.name" :icon="mdiRename" required />
            </FormField>

            <FormField
              :label="$t('views.templates.form.os')"
              :help="$t('views.templates.form.osHelp')"
              :tooltip="$t('views.templates.import.osRequired')"
            >
              <SearchControl
                v-model="template.os"
                :icon="mdiApplicationBrackets"
                :fetch-data="backend.os.search"
                :fetch-selected="backend.os.getName"
                required
              />
            </FormField>
          </FormField>

          <BaseDivider />

          <FormField>
            <FormField
              :label="$t('views.templates.form.cpuCores')"
              :help="$t('views.templates.form.cpuCoresHelp')"
            >
              <FormControl
                v-model="template.cpu"
                type="range"
                placeholder="2"
                :min="1"
                :max="12"
                :step="1"
                required
              />
            </FormField>

            <FormField
              :label="$t('views.templates.form.ram')"
              :help="$t('views.templates.form.ramHelp')"
            >
              <FormControl
                v-model="template.ram"
                type="range"
                placeholder="4"
                :min="1"
                :max="20"
                :step="1"
                required
              />
            </FormField>
          </FormField>

          <BaseDivider />

          <FormField
            :label="$t('common.description')"
            :help="$t('views.templates.form.descriptionHelp')"
          />

          <BaseMarkdown v-model="template.description" action="edit" />

          <BaseDivider />
        </div>

        <!-- Footer Buttons -->
        <template #footer>
          <BaseButtons>
            <BaseButton
              type="submit"
              color="info"
              :label="
                disablePVEID
                  ? $t('views.templates.import.importButton')
                  : $t('views.templates.import.loadInfoButton')
              "
            />

            <BaseButton
              type="reset"
              color="info"
              :label="$t('common.cancel')"
              outline
              @click="router.back()"
            />
          </BaseButtons>
        </template>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
