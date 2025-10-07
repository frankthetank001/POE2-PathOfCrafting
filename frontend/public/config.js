// Runtime configuration for PoE2 PathOfCrafting
// This file can be overridden by mounting a custom config.js via Docker volume
window.APP_CONFIG = {
  // API URL configuration - auto-detects based on deployment environment
  API_BASE_URL: (() => {
    const hostname = window.location.hostname

    // Development: localhost
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8000'
    }

    // Fly.io deployment: frontend at poe2-pathofcrafting-frontend.fly.dev
    // Backend at poe2-pathofcrafting-backend.fly.dev
    if (hostname.includes('fly.dev')) {
      return 'https://poe2-pathofcrafting-backend.fly.dev'
    }

    // Default: same host, port 8000 (Docker, TrueNAS, etc)
    return window.location.protocol + '//' + hostname + ':8000'
  })()
}
