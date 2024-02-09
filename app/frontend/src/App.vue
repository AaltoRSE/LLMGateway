<script setup lang="ts">
import { useAuthStore } from '@/stores/authStore'
import ProgressSpinner from 'primevue/progressspinner'
import Button from 'primevue/button'
const authStore = useAuthStore()
authStore.login('testtoken')
</script>

<template>
  <div v-if="authStore.loggedIn">
    <h1>Welcome {{ authStore.user?.username }}</h1>
    <!-- route outlet -->
    <!-- component matched by the route will render here -->
    <router-view></router-view>
  </div>
  <div v-else>
    <h1>Welcome to the Aalto Scicomp LLM Self Service</h1>
    <router-link to="/login">
      <Button>Login</Button>
    </router-link>
  </div>
</template>

<style scoped></style>
