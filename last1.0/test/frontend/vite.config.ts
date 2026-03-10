import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
    }),
    Components({
      resolvers: [ElementPlusResolver()],
    }),
  ],
  server: {
    port: 5173,
    proxy: {
      '/api/ip-studio/interview/live': {
        target: 'ws://localhost:8085',
        ws: true,
      },
      '/api': {
        target: 'http://localhost:8085',
        changeOrigin: true,
      },
      '/videos': {
        target: 'http://localhost:8085',
        changeOrigin: true,
      },
      '/outputs': {
        target: 'http://localhost:8085',
        changeOrigin: true,
      },
      '/comic-drama': {
        target: 'http://localhost:8085',
        changeOrigin: true,
      },
    },
  },
})
