<script setup lang="ts">
import { useAuthStore } from '@/stores/authStore'
import Button from 'primevue/button'
const authStore = useAuthStore()
</script>

<template>
  <router-link to="/keys">
    <Button>Go To Key Management</Button>
  </router-link>
  <router-link v-if="authStore.isAdmin" to="/admin">
    <Button>Go to Admin Management</Button>
  </router-link>
  <router-link to="/logout">
    <Button>Log out</Button>
  </router-link>
</template>
