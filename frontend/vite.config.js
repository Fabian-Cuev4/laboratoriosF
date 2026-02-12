import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,      // Permite que Docker acceda
    strictPort: true,
    port: 5173,
    watch: {
      usePolling: true, // Vital para que Windows detecte cambios en Docker
    }
  }
})