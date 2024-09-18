<template>
  <Dialog
    class="w-8"
    v-model:visible="dialogVisible"
    header="User Agreement for Scicomp LLM gateway Self Service"
    modal
  >
    <h2>Welcome to the LLM Web API self service portal provided by Aalto Science IT.</h2>
    <p>
      Please be aware, that this portal has not yet been through the security evaluation process.
      While all reasonable efforts have been made to ensure the security of the portal, and
      submitted data is not stored, please only use non confidential data for the moment. By
      clicking accept, you agree that you have read this and are aware of this limitation
    </p>
    <template #footer>
      <Button label="Disagree" icon="pi pi-times" @click="handleNoClick" text />
      <Button label="Agree" icon="pi pi-check" @click="handleYesClick" autofocus />
    </template>
  </Dialog>
</template>

<script lang="ts">
// PrimeVue components
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'

export default {
  name: 'AgreementDialog',
  components: {
    Dialog,
    Button
  },
  emits: ['confirm', 'reject', 'update:isVisible'],
  props: {
    isVisible: {
      type: Boolean,
      required: true
    }
  },
  data() {
    return {
      agreement: ''
    }
  },
  methods: {
    handleYesClick() {
      console.log('Confirm clicked')
      this.$emit('confirm')
    },

    handleNoClick() {
      this.$emit('reject')
    }
  },

  computed: {
    dialogVisible: {
      get() {
        return this.isVisible
      },
      set(value: boolean) {
        this.$emit('update:isVisible', value)
      }
    }
  },
  mounted() {
    fetch('/Agreement.md').then((data: any) => {
      data.text().then((text: string) => {
        this.agreement = text
      })
    })
  }
}
</script>
