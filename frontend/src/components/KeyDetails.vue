<template>
  <div>
    <DataTable
      :value="keyData"
      :frozenValue="totalData"
      scrollable
      scrollHeight="400px"
      :pt="{
        bodyrow: ({ props }: any) => ({
          class: [{ 'font-bold': props.frozenRow }]
        })
      }"
    >
      <Column header="Model" field="model"></Column>
      <Column header="Prompt tokens" field="prompt_tokens"></Column>
      <Column header="Completion tokens" field="completion_tokens"></Column>
      <Column header="Cost" field="cost"></Column>
    </DataTable>
  </div>
</template>

<script lang="ts">
import { useKeyStore } from '@/stores/keyStore'
import { type ModelUsage } from '@/stores/keyStore'
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
        var usage: Array<ModelUsage> = []
        if (currentData) usage = currentData.usage
        return usage
      } else {
        return []
      }
    },
    totalData() {
      if (this.selectedKey) {
        const currentData = this.keyInfo.keys.find((x) => x.key == this.selectedKey)
        if (currentData)
          return [
            {
              model: 'Total',
              prompt_tokens: currentData.prompt_tokens,
              completion_tokens: currentData.completion_tokens,
              cost: currentData.cost
            }
          ]
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
