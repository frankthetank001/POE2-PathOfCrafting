import { useState, useEffect } from 'react'
import { craftingApi } from '@/services/crafting-api'

interface CurrencyTooltipData {
  name: string
  description: string
  mechanics?: string
  tier?: string
  type?: string
}

export function useCurrencyTooltip(currencyName: string | null) {
  const [tooltipData, setTooltipData] = useState<CurrencyTooltipData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!currencyName) {
      setTooltipData(null)
      return
    }

    const fetchTooltipData = async () => {
      setLoading(true)
      setError(null)

      try {
        const data = await craftingApi.getCurrencyTooltip(currencyName)
        setTooltipData(data)
      } catch (err) {
        console.error('Failed to fetch currency tooltip:', err)
        setError('Failed to load tooltip')
        // Fallback to basic data
        setTooltipData({
          name: currencyName,
          description: currencyName,
          mechanics: undefined
        })
      } finally {
        setLoading(false)
      }
    }

    fetchTooltipData()
  }, [currencyName])

  return { tooltipData, loading, error }
}