import axios from 'axios'
import type { ItemParseRequest, ItemParseResponse } from '@/types/item'

// Get API URL from runtime config (loaded from config.js) or fall back to env/localhost
const getApiBaseUrl = () => {
  // @ts-ignore - window.APP_CONFIG is loaded from public/config.js
  if (window.APP_CONFIG?.API_BASE_URL) {
    // @ts-ignore
    return window.APP_CONFIG.API_BASE_URL
  }
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
}

const API_BASE_URL = getApiBaseUrl()

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const itemsApi = {
  parseItem: async (request: ItemParseRequest): Promise<ItemParseResponse> => {
    const response = await api.post<ItemParseResponse>('/items/parse', request)
    return response.data
  },
}

export default api