import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    headers: {
      // this is for vite-only, for prod see public/staticwebapp.config.json
      //'Content-Security-Policy':
      //  "default-src 'self'; style-src 'self' 'unsafe-inline'; connect-src https://login.microsoftonline.com https://aalto-openai-apigw.azure-api.net https://localhost:5173 http://localhost:8000 https://scicomp-docs-search.k8s-test.cs.aalto.fi/ ws:"
    },
    proxy: {
      '/auth': {
        target: 'http://127.0.0.1:3000',
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('proxy error', err)
          })
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log(
              'Sending Request:',
              req.method,
              req.url,
              ' => TO THE TARGET =>  ',
              proxyReq.method,
              proxyReq.protocol,
              proxyReq.host,
              proxyReq.path,
              JSON.stringify(proxyReq.getHeaders())
            )
          })
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log(
              'Received Response from the Target:',
              proxyRes.statusCode,
              req.url,
              JSON.stringify(proxyRes.headers)
            )
          })
        }
      }
    }
  }
})
