import { defineStore } from 'pinia'
import axios from 'axios'

export type ModelUsage = {
  model: String
  prompt_tokens: Number
  completion_tokens: Number
  cost: Number
}

type KeyData = {
  key: String
  name: String
  prompt_tokens: Number
  completion_tokens: Number
  cost: Number
  usage: ModelUsage[]
}
type KeyInformation = {
  total_use: number
  keys: KeyData[]
}

export const useKeyStore = defineStore({
  id: 'keyStore',
  state: () => ({
    keyInfo: {} as KeyInformation
  }),
  actions: {
    async fetchKeyInfo(forceUpdate = false) {
      console.log('Fetching models in store')
      console.log(this.keyInfo)
      try {
        console.log('Requesting models')
        const result = await axios.post('/selfservice/usage', {
          method: 'post'
        })
        this.keyInfo = result.data
      } catch (err) {
        console.error(err)
        axios.defaults.headers.common['Authorization'] = undefined
      }
    },
    async deleteKey(key: String) {
      try {
        console.log('Deleting Key')
        const answer = await axios.post('/selfservice/deletekey', { key: key })
        await this.fetchKeyInfo(true)
        return true
      } catch (err) {
        console.error(err)
        axios.defaults.headers.common['Authorization'] = undefined
        return false
      }
    },
    async createKey(name: string) {
      try {
        console.log('Requesting models')
        axios.post('/selfservice/createkey', { name: name }).then((result) => {
          this.fetchKeyInfo(true)
        })
      } catch (err) {
        console.error(err)
        axios.defaults.headers.common['Authorization'] = undefined
      }
    }
  }
})
