import axios from 'axios'
import type { ItemParseRequest, ItemParseResponse } from '@/types/item'
import type { BuildsResponse, LeaguesResponse } from '@/types/build'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

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

export const buildsApi = {
  getLeagues: async (): Promise<LeaguesResponse> => {
    const response = await api.get<LeaguesResponse>('/builds/leagues')
    return response.data
  },

  getBuilds: async (params?: {
    league?: string
    class?: string
    limit?: number
  }): Promise<BuildsResponse> => {
    const response = await api.get<BuildsResponse>('/builds', { params })
    return response.data
  },
}

export default api