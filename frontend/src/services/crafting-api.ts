import axios from 'axios'
import type {
  CraftableItem,
  CraftingSimulationRequest,
  CraftingSimulationResult,
  ItemModifier,
  ItemBasesBySlot,
} from '@/types/crafting'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1/crafting`,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const craftingApi = {
  getCurrencies: async (): Promise<string[]> => {
    const response = await api.get<string[]>('/currencies')
    return response.data
  },

  getAvailableCurrenciesForItem: async (item: CraftableItem): Promise<string[]> => {
    const response = await api.post<string[]>('/currencies/available-for-item', item)
    return response.data
  },

  simulateCrafting: async (
    request: CraftingSimulationRequest
  ): Promise<CraftingSimulationResult> => {
    const response = await api.post<CraftingSimulationResult>('/simulate', request)
    return response.data
  },

  calculateProbability: async (
    item: CraftableItem,
    goalModGroup: string,
    currencyName: string
  ): Promise<{ goal_mod_group: string; currency_name: string; probability: number }> => {
    const response = await api.post('/probability', null, {
      params: {
        goal_mod_group: goalModGroup,
        currency_name: currencyName,
      },
    })
    return response.data
  },

  getAvailableMods: async (
    item: CraftableItem
  ): Promise<{
    prefixes: ItemModifier[]
    suffixes: ItemModifier[]
    total_prefixes: number
    total_suffixes: number
  }> => {
    const response = await api.post('/available-mods', item)
    return response.data
  },

  getItemBases: async (): Promise<ItemBasesBySlot> => {
    const response = await api.get<ItemBasesBySlot>('/item-bases')
    return response.data
  },

  getBasesForSlotCategory: async (
    slot: string,
    category: string
  ): Promise<Array<{name: string, description: string, default_ilvl: number, base_stats: Record<string, number>}>> => {
    const response = await api.get(`/item-bases/${slot}/${category}`)
    return response.data
  },

  parseItem: async (
    itemText: string
  ): Promise<{
    success: boolean
    item: CraftableItem
    parsed_info: {
      base_type: string
      rarity: string
      item_level: number
    }
  }> => {
    const response = await api.post('/parse-item', { item_text: itemText })
    return response.data
  },
}

export default craftingApi