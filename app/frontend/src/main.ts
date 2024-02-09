import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import PrimeVue from 'primevue/config'
import ToastService from 'primevue/toastservice'
import Tooltip from 'primevue/tooltip'
import { router } from './router/router'

// PrimeVue theme (will probably need to be overwritten for Aalto Look and Feel)
import 'primevue/resources/themes/lara-light-indigo/theme.css'
// Primevue core css
import 'primevue/resources/primevue.min.css'

// Primeflex css
import 'primeflex/primeflex.css'
import axios from 'axios'
axios.defaults.headers.post['Content-Type'] = 'application/json'

const app = createApp(App)

app.use(createPinia())

app.directive('tooltip', Tooltip)

app.use(PrimeVue, { ripple: true })
app.use(ToastService)
app.use(router)
app.mount('#app')
