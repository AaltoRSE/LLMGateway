<template>
  <div v-if="showFilters" class="filters">
    <label for="model">Model:</label>
    <Dropdown v-model="model" :options="models" placeholder="Select a model"></Dropdown>

    <label for="startDate">Start Date:</label>
    <Calendar v-model="start" :showIcon="true" :dateFormat="dateFormat"></Calendar>

    <label for="endDate">End Date:</label>
    <Calendar v-model="end" :showIcon="true" :dateFormat="dateFormat"></Calendar>
  </div>
  <div @click="toggleShowFilters">Filters</div>
</template>

<script lang="ts">
import Dropdown from 'primevue/dropdown'
import Calendar from 'primevue/calendar'
import { useModelStore } from '@/stores/modelStore'
import { storeToRefs } from 'pinia'
export default {
  name: 'KeyFilter',
  components: {
    Dropdown,
    Calendar
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
      showFilters: false
    }
  },
  methods: {
    toggleShowFilters() {
      this.showFilters = !this.showFilters
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
    const { models } = storeToRefs(modelStore)
    return { dateFormat, modelStore, models }
  },
  mounted() {
    console.log('Fetching models')
    this.modelStore.fetchModels()
  }
}
</script>
