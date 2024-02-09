import AppView from '@/views/AppView.vue'
import { useAuthStore } from '@/stores/authStore'
import { createRouter, createWebHistory, type RouteLocationNormalized } from 'vue-router'
import UserViewVue from '@/views/UserView.vue'

// 2. Define some routes
// Each route should map to a component.
// We'll talk about nested routes later.
const routes = [
  { path: '/keys', component: UserViewVue },
  { path: '/admin', component: UserViewVue },
  { path: '/', component: AppView },
  {
    name: 'login',
    path: '/login',
    redirect: (to: RouteLocationNormalized) => {
      console.log('rerouting to login')
      // This needs to be changed to your server address.
      const currentport = window.location.port ? `:${window.location.port}` : ''
      window.location.href = `${window.location.protocol}://${window.location.hostname}${currentport}/saml/login`
      return { path: '' }
    }
  },
  {
    name: 'logout',
    path: '/logout',
    redirect: (to: RouteLocationNormalized) => {
      console.log('rerouting to logout')
      // This needs to be changed to your server address.
      const currentport = window.location.port ? `:${window.location.port}` : ''
      window.location.href = `${window.location.protocol}://${window.location.hostname}${currentport}/saml/slo`
      return { path: '' }
    }
  }
]

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  linkActiveClass: 'active',
  routes: routes
})
