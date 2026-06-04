import axios from 'axios'
import type { BuildsMeta, TrendingBase, TrendingMod, BaseDetail } from '@/types/builds'

// Same runtime-config pattern as the other API services (config.js -> env -> localhost).
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
  baseURL: `${API_BASE_URL}/api/v1/builds`,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const buildsApi = {
  getMeta: async (): Promise<BuildsMeta> => {
    const response = await api.get<BuildsMeta>('/meta')
    return response.data
  },

  getTrendingBases: async (slot?: string, limit = 150): Promise<TrendingBase[]> => {
    const response = await api.get<TrendingBase[]>('/trending-bases', {
      params: { slot: slot || undefined, limit },
    })
    return response.data
  },

  getTrendingMods: async (
    base?: string,
    origin?: string,
    limit = 100
  ): Promise<TrendingMod[]> => {
    const response = await api.get<TrendingMod[]>('/trending-mods', {
      params: { base: base || undefined, origin: origin || undefined, limit },
    })
    return response.data
  },

  getBaseDetail: async (baseName: string): Promise<BaseDetail> => {
    const response = await api.get<BaseDetail>(`/base/${encodeURIComponent(baseName)}`)
    return response.data
  },
}
