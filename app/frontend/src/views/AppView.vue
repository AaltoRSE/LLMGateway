<script setup lang="ts">
import { useAuthStore } from '@/stores/authStore'
import ProgressSpinner from 'primevue/progressspinner'
import Button from 'primevue/button'
import axios from 'axios'
import { ref } from 'vue'
const authStore = useAuthStore()

const userData = ref({})

async function loadData() {
  axios
    .get('/data')
    .then((response) => {
      userData.value = response.data
    })
    .catch((err) => {
      userData.value = {}
    })
}
</script>

<template>
  <div>Hello</div>
  <div v-if="userData">
    Your Data:
    <div v-for="(element, key) of userData">{{ key }} : {{ element }}</div>
  </div>
  <Button @click="loadData">Load Data</Button>
</template>
