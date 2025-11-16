import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: '../static/react',
    emptyOutDir: true,
    sourcemap: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/files': {
        target: 'ws://localhost:3000',
        ws: true,
      },
      '/rename': 'http://localhost:3000',
      '/manage': 'http://localhost:3000',
      '/zip': 'http://localhost:3000',
      '/file': 'http://localhost:3000',
      '/uploads': 'http://localhost:3000',
    },
  },
})
