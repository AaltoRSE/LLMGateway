<template>
  <div v-if="agreementOk" class="flex flex-column">
    <div class="flex flex-row">
      <KeyInfo class="w-8 p-2" @showDetails="(event) => (selectedKey = event)"></KeyInfo>
      <KeyDetails class="w-4 p-2" :selectedKey="selectedKey"></KeyDetails>
    </div>
    <div class="flex flex-row justify-content-between">
      <div class="flex">
        <div class="flex flex-column">
          Add a New key, Maximum number of keys is 10 for now
          <div>
            <InputText class="mr-3" v-model="keyName"></InputText>
            <Button @click="keyStore.createKey(keyName)"> Add key </Button>
          </div>
        </div>
      </div>
      <router-link to="/">
        <Button> Back </Button>
      </router-link>
    </div>
  </div>
  <div
    v-else
    class="flex w-full h-full justify-content-center align-content-center align-items-center"
  >
    <UserAgreementDialog
      v-model:isVisible="showAgreementDialog"
      @confirm="confirmAgreement"
      @reject="showAgreementDialog = false"
    />
    <div class="flex flex-column">
      <span> You need to accept the Usage Agreement in order to use Aalto GPT </span>
      <Button label="Show User Agreement" @click="showAgreementDialog = true"></Button>
    </div>
  </div>
</template>
<script lang="ts">
// Stores
import { useModelStore } from '@/stores/modelStore'
import { useKeyStore } from '@/stores/keyStore'
import { useAuthStore } from '@/stores/authStore'
import { storeToRefs } from 'pinia'

// PrimeVue components
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'

// Local components
import KeyInfo from '@/components/KeyInfo.vue'
import KeyDetails from '@/components/KeyDetails.vue'
import UserAgreementDialog from '@/components/UserAgreementDialog.vue'

export default {
  name: 'UserView',
  components: {
    KeyInfo,
    Button,
    InputText,
    KeyDetails,
    UserAgreementDialog
  },
  props: {
    selectedModel: {
      type: String,
      required: true
    },
    startDate: {
      type: Date,
      required: true
    },
    endDate: {
      type: Date,
      required: true
    }
  },
  data() {
    return {
      showFilters: false,
      keyName: '',
      selectedKey: undefined,
      showAgreementDialog: true
    }
  },
  methods: {
    toggleShowFilters() {
      this.showFilters = !this.showFilters
    },
    updateKey(newKey: string) {
      return
    },
    confirmAgreement() {
      this.authStore.acceptAgreement()
      this.showAgreementDialog = false
    }
  },
  computed: {
    start: {
      get() {
        return this.startDate
      },
      set(newValue: Date) {
        this.$emit('update:startDate', newValue)
      }
    },
    end: {
      get() {
        return this.endDate
      },
      set(newValue: Date) {
        this.$emit('update:endDate', newValue)
      }
    },
    model: {
      get() {
        return this.selectedModel
      },
      set(newValue: Date) {
        this.$emit('update:selectedModel', newValue)
      }
    }
  },
  setup() {
    const dateFormat = 'dd-mm-yy' // Adjust the date format as needed
    const modelStore = useModelStore()
    const authStore = useAuthStore()
    const keyStore = useKeyStore()
    const { agreementOk } = storeToRefs(authStore)
    const { models } = storeToRefs(modelStore)
    return { dateFormat, modelStore, models, keyStore, authStore, agreementOk }
  },
  mounted() {
    console.log('Fetching models')
    this.modelStore.fetchModels()
  }
}
</script>
