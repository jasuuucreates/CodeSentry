import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// During development the React app runs on the Vite dev server (port 5173) while the Flask
// API runs on port 5000. Proxying /api lets the frontend always call the relative URL "/api",
// exactly as it does in production where Flask serves both the built SPA and the API.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
})
