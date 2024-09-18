import { defineStore } from 'pinia'
import axios from 'axios'

export const useModelStore = defineStore({
  id: 'modelStore',
  state: () => ({
    models: [] as Array<String>
  }),
  actions: {
    async fetchModels(forceUpdate = false) {
      console.log('Fetching models in store')
      console.log(this.models)
      if (this.models.length == 0 || forceUpdate) {
        try {
          console.log('Requesting models')
          const result = await axios.get('/v1/models', {
            method: 'GET'
          })
          this.models = []
          if (result.data) {
            console.log(result.data)
            for (const model of result.data.data) {
              this.models.push(model.id)
            }
          }
        } catch (err) {
          console.error(err)
          axios.defaults.headers.common['Authorization'] = undefined
        }
      }
    }
  }
})
