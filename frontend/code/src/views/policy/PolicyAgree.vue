<script setup>
import { mdiInformationOutline } from '@mdi/js'
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseMarkdown from '@/components/BaseMarkdown.vue'
import CardBox from '@/components/CardBox.vue'
import FormField from '@/components/FormField.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import SectionFullScreen from '@/components/SectionFullScreen.vue'
import LayoutGuest from '@/layouts/LayoutGuest.vue'
import backend from '@/services'
import { useMainStore } from '@/stores/main'

const { t } = useI18n()
const mainStore = useMainStore()
const router = useRouter()
const route = useRoute()
const policy = ref([])
const toast = useToast()
const isScrolledToBottom = ref(false)

async function fetchPolicy(id) {
  try {
    await backend.policies.get(id).then((response) => {
      policy.value = response
    })
  } catch (error) {
    toast.error(
      t('common.loadError', { entity: t('objectTypes.policy.singular') }),
    )
  }
}

const logout = async () => {
  try {
    mainStore.logout()
    toast.success(t('views.policies.agree.logoutSuccess'))
  } catch (error) {
    toast.error(t('views.policies.agree.logoutError'))
  }
}

const submit = async () => {
  try {
    let check = await backend.policies.agree(route.params.id)
    if (check) {
      toast.success(t('views.policies.agree.confirmSuccess'))

      // Remove agreed policy from local outstanding policy list
      mainStore.removeOutstandingPolicy(route.params.id)

      // Check if user has more outstanding policies
      let policyCheck = mainStore.getOutStandingPolicies

      // Redirect to other policies if required
      if (policyCheck) {
        toast.info(t('views.policies.agree.morePoliciesPending'), {
          timeout: 4200,
        })
        isScrolledToBottom.value = false
        policy.value = []
        return router.push('/policy/' + policyCheck)
      }

      // Re-auth the user so they get a valid access token
      let reauth = await backend.auth.reauth()
      mainStore.login({
        access_token: reauth.data.access_token,
        token_type: reauth.data.token_type,
        outstanding_policies: [],
      })

      if (router.currentRoute?.value?.query?.redirect) {
        router.push(router.currentRoute.value.query.redirect)
      } else {
        router.push('/')
      }
    }
  } catch (error) {
    toast.error(t('views.policies.agree.confirmError'))
  }
}

function handlePolicyScrolled() {
  isScrolledToBottom.value = true
}

onMounted(async () => {
  fetchPolicy(route.params.id)
})

watch(
  () => route.params.id,
  () => {
    fetchPolicy(route.params.id)
  },
)
</script>

<template>
  <LayoutGuest>
    <SectionFullScreen
      bg="blueGreen"
      class="flex items-center justify-center p-4"
    >
      <div
        class="w-full md:w-3/4 max-w-full mx-auto h-full md:h-[80vh] max-h-[90vh] overflow-auto my-auto"
      >
        <CardBox is-form @submit.prevent="submit">
          <NotificationBar
            color="warning"
            :dismissable="false"
            :icon="mdiInformationOutline"
          >
            <p>
              <b>{{ $t('views.policies.agree.mustAgree') }}</b>
            </p>
            {{ $t('views.policies.agree.scrollToEnd') }}
          </NotificationBar>

          <FormField :label="policy.name" />

          <BaseMarkdown
            v-model="policy.content"
            action="view"
            @scrolled="handlePolicyScrolled"
          />

          <template #footer>
            <BaseButtons>
              <BaseButton
                type="submit"
                color="info"
                :label="$t('common.confirm')"
                :disabled="!isScrolledToBottom"
              />

              <BaseButton
                type="reset"
                color="danger"
                :label="$t('views.policies.agree.logout')"
                @click="logout()"
              />
            </BaseButtons>
          </template>
        </CardBox>
      </div>
    </SectionFullScreen>
  </LayoutGuest>
</template>
