import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { execSync } from 'child_process'

// Get version from environment (Docker build), git tag (local dev), or fallback
function getVersion() {
  // First check if version is provided via environment variable (Docker builds)
  if (process.env.VITE_APP_VERSION) {
    return process.env.VITE_APP_VERSION
  }

  // Try to get from git tag (local development)
  try {
    const gitTag = execSync('git describe --tags --abbrev=0', { encoding: 'utf8' }).trim()
    // Remove 'v' prefix if present
    return gitTag.startsWith('v') ? gitTag.slice(1) : gitTag
  } catch (error) {
    console.warn('Could not get version from environment or git tag, using fallback')
    return '0.3.0' // fallback version
  }
}

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  define: {
    '__APP_VERSION__': JSON.stringify(getVersion()),
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})