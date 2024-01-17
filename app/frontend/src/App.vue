<script setup lang="ts">
import { useAuthStore } from '@/stores/authStore'
import ProgressSpinner from 'primevue/progressspinner'
import Button from 'primevue/button'
const authStore = useAuthStore()
</script>

<template>
  <div v-if="authStore.loggedIn">
    <h1>Welcome {{ authStore.user?.username }}</h1>
    <p>
      <!-- use the router-link component for navigation. -->
      <!-- specify the link by passing the `to` prop. -->
      <!-- `<router-link>` will render an `<a>` tag with the correct `href` attribute -->
      <router-link to="/">Go to Home</router-link>
    </p>
    <!-- route outlet -->
    <!-- component matched by the route will render here -->
    <router-view></router-view>
  </div>
  <div v-else>
    <progress-spinner></progress-spinner>
  </div>
</template>

<style scoped></style>
