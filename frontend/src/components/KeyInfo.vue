<template>
  <div>
    <DataTable
      :value="keyInfo.keys"
      v-model:selection="selectedKey"
      selectionMode="single"
      @rowSelect="(event: any) => $emit('showDetails', event.data.key)"
      @rowUnselect="(event: any) => $emit('showDetails', undefined)"
    >
      <Column header="Name" field="name"></Column>
      <Column header="Key" field="key"></Column>
      <Column header="Cost" field="cost"></Column>
      <Column header="Delete" field="key">
        <template #body="slotProps">
          <Button @click="deleteKey(slotProps.data.key)">Delete</Button>
        </template>
      </Column>
    </DataTable>
    <div class="font-bold font-l">{{ keyInfo.total_use }}</div>
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
  data() {
    return {
      selectedKey: undefined
    }
  },
  computed: {
    keyGeneralData() {
      return this.keyInfo
    }
  },
  methods: {
    async deleteKey(key: String) {
      const done = await this.keyStore.deleteKey(key)
      //Clear any selection
      this.$emit('showDetails', undefined)
    }
  },

  async mounted() {
    this.keyStore.fetchKeyInfo()
  },
  components: { Column, DataTable, Button }
}
</script>
