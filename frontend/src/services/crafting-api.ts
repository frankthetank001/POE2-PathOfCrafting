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

  simulateCraftingWithOmens: async (
    item: CraftableItem,
    currencyName: string,
    omenNames: string[]
  ): Promise<CraftingSimulationResult> => {
    const response = await api.post<CraftingSimulationResult>('/simulate-with-omens', {
      item,
      currency_name: currencyName,
      omen_names: omenNames,
    })
    return response.data
  },

  getAvailableOmensForCurrency: async (currencyName: string): Promise<string[]> => {
    const response = await api.get<string[]>(`/omens/${currencyName}`)
    return response.data
  },

  getCategorizedCurrencies: async (): Promise<{
    orbs: { implemented: string[], disabled: string[] }
    essences: { implemented: string[], disabled: string[] }
    bones: { implemented: string[], disabled: string[] }
    omens: string[]
    total: number
    implemented_count: number
    disabled_count: number
  }> => {
    const response = await api.get('/currencies/categorized')
    return response.data
  },

  calculateProbability: async (
    item: CraftableItem,
    goalModGroup: string,
    currencyName: string
  ): Promise<{ goal_mod_group: string; currency_name: string; probability: number }> => {
    // Note: Backend expects item in request body, but currently using query params
    // This is a pre-existing pattern that should be refactored
    const response = await api.post('/probability', item, {
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
    essence_prefixes: ItemModifier[]
    essence_suffixes: ItemModifier[]
    desecrated_prefixes: ItemModifier[]
    desecrated_suffixes: ItemModifier[]
    total_prefixes: number
    total_suffixes: number
    total_essence_prefixes: number
    total_essence_suffixes: number
    total_desecrated_prefixes: number
    total_desecrated_suffixes: number
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

  getCurrencyTooltip: async (currencyName: string): Promise<{
    name: string
    description: string
    mechanics?: string
    tier?: string
    type?: string
  }> => {
    const response = await api.get(`/currency-tooltip/${encodeURIComponent(currencyName)}`)
    return response.data
  },
}

export default craftingApi