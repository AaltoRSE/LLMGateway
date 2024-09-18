<template>
  <div>
    <DataTable :value="keyData">
      <Column header="Model" field="model"></Column>
      <Column header="Usage" field="tokencount"></Column>
    </DataTable>
  </div>
</template>

<script lang="ts">
import { useKeyStore } from '@/stores/keyStore'
import { storeToRefs } from 'pinia'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
export default {
  setup() {
    const keyStore = useKeyStore()
    const { keyInfo } = storeToRefs(keyStore)
    return { keyStore, keyInfo }
  },
  emits: ['showDetails'],
  props: {
    selectedKey: {
      type: String,
      required: false
    }
  },

  computed: {
    keyData() {
      if (this.selectedKey) {
        const currentData = this.keyInfo.keys.find((x) => x.key == this.selectedKey)
        if (currentData) return currentData.modeldata
        else return []
      } else {
        return []
      }
    }
  },
  async mounted() {
    this.keyStore.fetchKeyInfo()
  },
  components: { Column, DataTable, Button }
}
</script>
