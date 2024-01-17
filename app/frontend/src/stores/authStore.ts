import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'

type authedUser = {
  username: String
  token: String
}

export const useAuthStore = defineStore({
  id: 'authStore',
  state: () => ({
    user: null as null | authedUser,
    loggedIn: false as Boolean,
    rerouting: false
  }),
  actions: {
    async login(token: String) {
      if (token) {
        const claims = atob(token.split('.')[1])
        console.log(claims)
        this.user = { username: 'user', token: token }
        axios.defaults.headers.common['Authorization'] = 'Bearer ' + token
        try {
          const result = await axios.post('/auth/test', {
            method: 'POST'
          })
          if (result.data.authed) {
            this.user = { username: result.data.user, token: token }
            this.loggedIn = true
          } else {
            console.log('Not / no longer authed')
            axios.defaults.headers.common['Authorization'] = undefined
            this.loggedIn = false
            this.user = null
          }
        } catch (err) {
          console.error(err)
          axios.defaults.headers.common['Authorization'] = undefined
        }
      } else {
        this.user = null
        this.loggedIn = false
      }
    }
  }
})
