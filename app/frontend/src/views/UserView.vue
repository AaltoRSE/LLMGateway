<template>
  <div class="flex flex-column">
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
</template>
<script lang="ts">
import KeyInfo from '@/components/KeyInfo.vue'
import { useModelStore } from '@/stores/modelStore'
import { useKeyStore } from '@/stores/keyStore'
import { storeToRefs } from 'pinia'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import KeyDetails from '@/components/KeyDetails.vue'
export default {
  name: 'UserView',
  components: {
    KeyInfo,
    Button,
    InputText,
    KeyDetails
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
      selectedKey: undefined
    }
  },
  methods: {
    toggleShowFilters() {
      this.showFilters = !this.showFilters
    },
    updateKey(newKey: string) {
      return
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
    const keyStore = useKeyStore()
    const { models } = storeToRefs(modelStore)
    return { dateFormat, modelStore, models, keyStore }
  },
  mounted() {
    console.log('Fetching models')
    this.modelStore.fetchModels()
  }
}
</script>
