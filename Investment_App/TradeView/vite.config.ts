import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [vue()],

    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
      },
    },

    server: {
      port: 3000,
      host: true,
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },

    build: {
      target: 'es2020',
      rollupOptions: {
        output: {
          manualChunks: {
            echarts: ['echarts', 'vue-echarts'],
            vendor: ['vue', 'vue-router', 'pinia'],
            utils: ['axios', 'date-fns', 'lodash-es'],
          },
        },
      },
    },
  }
})
