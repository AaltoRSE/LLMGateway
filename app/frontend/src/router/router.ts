import AppView from '@/views/AppView.vue'
import { useAuthStore } from '@/stores/authStore'
import { createRouter, createWebHistory, type RouteLocationNormalized } from 'vue-router'

// 2. Define some routes
// Each route should map to a component.
// We'll talk about nested routes later.
const routes = [
  { path: '/', component: AppView },
  {
    name: 'login',
    path: '/login',
    redirect: (to: RouteLocationNormalized) => {
      console.log('rerouting to login')
      const authStore = useAuthStore()
      authStore.rerouting = true
      window.location.href = 'http://127.0.0.1:3000/saml/login'
      return { path: '' }
    }
  }
]

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  linkActiveClass: 'active',
  routes: routes
})

router.beforeEach(async (to) => {
  // redirect to login page if not logged in and trying to access a restricted page
  const authStore = useAuthStore()
  if (!authStore.loggedIn && to.name !== 'login' && !authStore.rerouting) {
    console.log('Updating route')
    const token = to.query.token
    if (!token) {
      return { name: 'login' }
    } else {
      await authStore.login(token.toString())
      router.replace('/')
    }
  }
})
