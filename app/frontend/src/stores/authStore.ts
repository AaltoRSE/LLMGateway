import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'

type authedUser = {
  username: String
  token: String
}

const AGREEMENT_ACCEPTED_VERSION = '1.0'
const AGREEMENT_ACCEPTED_FIELD = 'llm-agreement-accepted'

export const useAuthStore = defineStore({
  id: 'authStore',
  state: () => ({
    user: null as null | authedUser,
    loggedIn: false as Boolean,
    isAdmin: false as undefined | Boolean,
    agreementOk: localStorage.getItem(AGREEMENT_ACCEPTED_FIELD) === AGREEMENT_ACCEPTED_VERSION
  }),
  actions: {
    async login(token: String) {
      if (token) {
        axios.defaults.headers.common['Authorization'] = 'Bearer ' + token
        try {
          const result = await axios.post('/auth/test', {
            method: 'POST'
          })
          if (result.data.authed) {
            this.user = { username: result.data.user, token: token }
            this.loggedIn = true
            this.isAdmin = result.data.isAdmin
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
    },
    acceptAgreement() {
      this.agreementOk = true
      localStorage.setItem(AGREEMENT_ACCEPTED_FIELD, AGREEMENT_ACCEPTED_VERSION)
    }
  }
})
