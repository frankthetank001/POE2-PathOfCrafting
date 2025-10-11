import { useState, useEffect } from 'react'
import { craftingApi } from '@/services/crafting-api'

interface CurrencyTooltipData {
  name: string
  description: string
  mechanics?: string
  tier?: string
  type?: string
}

// In-memory cache for tooltip data
// Cache persists for the entire session
const tooltipCache = new Map<string, CurrencyTooltipData>()

// Optional: TTL (time to live) cache with expiration
// Uncomment if you want cache to expire after a certain time
// const tooltipCacheWithTTL = new Map<string, { data: CurrencyTooltipData, timestamp: number }>()
// const CACHE_TTL_MS = 5 * 60 * 1000 // 5 minutes

export function useCurrencyTooltip(currencyName: string | null) {
  const [tooltipData, setTooltipData] = useState<CurrencyTooltipData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!currencyName) {
      setTooltipData(null)
      return
    }

    // Check cache first
    const cachedData = tooltipCache.get(currencyName)
    if (cachedData) {
      setTooltipData(cachedData)
      setLoading(false)
      setError(null)
      return
    }

    const fetchTooltipData = async () => {
      setLoading(true)
      setError(null)

      try {
        const data = await craftingApi.getCurrencyTooltip(currencyName)

        // Store in cache
        tooltipCache.set(currencyName, data)

        setTooltipData(data)
      } catch (err) {
        console.error('Failed to fetch currency tooltip:', err)
        setError('Failed to load tooltip')
        // Fallback to basic data
        const fallbackData = {
          name: currencyName,
          description: currencyName,
          mechanics: undefined
        }

        // Cache the fallback to avoid repeated failed requests
        tooltipCache.set(currencyName, fallbackData)

        setTooltipData(fallbackData)
      } finally {
        setLoading(false)
      }
    }

    fetchTooltipData()
  }, [currencyName])

  return { tooltipData, loading, error }
}

// Optional: Export function to clear cache if needed
export function clearTooltipCache() {
  tooltipCache.clear()
}