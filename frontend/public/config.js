// Runtime configuration for PoE2 PathOfCrafting
// This file can be overridden by mounting a custom config.js via Docker volume
window.APP_CONFIG = {
  // API URL configuration
  // Options:
  // 1. Absolute URL: 'http://your-server:8000' (for separate frontend/backend hosts)
  // 2. Relative URL: '/api' (when using nginx proxy - see nginx.conf)
  // 3. Auto-detect: Uses localhost for development, relative for production
  API_BASE_URL: window.location.origin.includes('localhost')
    ? 'http://localhost:8000'  // Development: direct to backend
    : window.location.protocol + '//' + window.location.hostname + ':8000'  // Production: same host, port 8000
}
