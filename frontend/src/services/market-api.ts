import axios from 'axios'
import type { CraftableItem } from '@/types/crafting'

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
  baseURL: `${API_BASE_URL}/api/v1/market`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types
export interface League {
  name: string
  divine_price: number
  chaos_divine_ratio: number
}

export interface CurrencyRate {
  id: string
  name: string
  exalted_value: number
  divine_value: number | null
  chaos_value: number | null
}

export interface ExchangeRates {
  league: string
  rates: Record<string, CurrencyRate>
  divine_per_exalted: number | null
  chaos_per_exalted: number | null
}

export interface CraftingCost {
  total_exalted: number
  total_divine: number
  total_chaos: number
  breakdown: Record<string, number>
}

export interface CurrencyAmount {
  currency: string
  count: number
}

export interface ConvertResult {
  amount: number
  from: string
  to: string
  result: number
}

export interface PriceListing {
  price_amount: number
  price_currency: string
  price_chaos: number
  item_name: string
  item_base: string
  item_level: number
  explicit_mods: string[]
  implicit_mods: string[]
  account_name: string
  indexed_time: string | null
}

export interface ItemPriceEstimate {
  min_price: number
  max_price: number
  median_price: number
  average_price: number
  currency: string
  num_listings: number
  confidence: 'high' | 'medium' | 'low'
  exalted_value: number | null
  divine_value: number | null
  search_criteria: Record<string, number>
  trade_url: string | null
  listings: PriceListing[]
}

// API client
export const marketApi = {
  /**
   * Get available leagues with price data
   */
  getLeagues: async (): Promise<League[]> => {
    const response = await api.get<League[]>('/leagues')
    return response.data
  },

  /**
   * Get exchange rates for all currencies
   * @param league Optional league name (defaults to current challenge league)
   */
  getExchangeRates: async (league?: string): Promise<ExchangeRates> => {
    const response = await api.get<ExchangeRates>('/rates', {
      params: league ? { league } : undefined,
    })
    return response.data
  },

  /**
   * Get exchange rate for a specific currency
   */
  getCurrencyRate: async (currencyId: string, league?: string): Promise<CurrencyRate> => {
    const response = await api.get<CurrencyRate>(`/rate/${encodeURIComponent(currencyId)}`, {
      params: league ? { league } : undefined,
    })
    return response.data
  },

  /**
   * Estimate total crafting cost from currencies spent
   */
  estimateCost: async (
    currencies: CurrencyAmount[],
    league?: string
  ): Promise<CraftingCost> => {
    const response = await api.post<CraftingCost>('/estimate-cost', {
      currencies,
      league,
    })
    return response.data
  },

  /**
   * Convert an amount from one currency to another
   */
  convert: async (
    amount: number,
    fromCurrency: string,
    toCurrency: string = 'exalted',
    league?: string
  ): Promise<ConvertResult> => {
    const response = await api.get<ConvertResult>('/convert', {
      params: {
        amount,
        from: fromCurrency,
        to: toCurrency,
        ...(league ? { league } : {}),
      },
    })
    return response.data
  },

  /**
   * Estimate the market value of an item
   * Note: This makes external API calls and may be rate limited
   */
  priceItem: async (
    item: CraftableItem,
    league?: string,
    equipmentFilters?: Record<string, number>,
    equipmentEnabled?: Record<string, boolean>
  ): Promise<ItemPriceEstimate> => {
    const response = await api.post<ItemPriceEstimate>('/price-item', {
      item,
      league,
      equipment_filters: equipmentFilters,
      equipment_enabled: equipmentEnabled,
    })
    return response.data
  },
}

export default marketApi
