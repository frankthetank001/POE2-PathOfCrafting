import { useState, useEffect } from 'react'
import { craftingApi } from '@/services/crafting-api'
import type { CraftableItem } from '@/types/crafting'

interface CraftingControlsPanelProps {
  item: CraftableItem
  onItemChange: (item: CraftableItem) => void
  message: string
  onMessage: (message: string) => void
  loading: boolean
  onLoadingChange: (loading: boolean) => void
  currencySpent: Record<string, number>
  onCurrencySpentChange: (spent: Record<string, number>) => void
  onHistoryAdd: (item: CraftableItem) => void
}

export function CraftingControlsPanel({
  item,
  onItemChange,
  message,
  onMessage,
  loading,
  onLoadingChange,
  currencySpent,
  onCurrencySpentChange,
  onHistoryAdd
}: CraftingControlsPanelProps) {
  const [currencies, setCurrencies] = useState<string[]>([])
  const [selectedCurrency, setSelectedCurrency] = useState<string>('')
  const [availableCurrencies, setAvailableCurrencies] = useState<string[]>([])

  useEffect(() => {
    loadCurrencies()
  }, [])

  useEffect(() => {
    if (item) {
      loadAvailableCurrencies()
    }
  }, [item])

  const loadCurrencies = async () => {
    try {
      const data = await craftingApi.getCurrencies()
      setCurrencies(data)
      if (data.length > 0) {
        setSelectedCurrency(data[0])
      }
    } catch (err) {
      console.error('Failed to load currencies:', err)
    }
  }

  const loadAvailableCurrencies = async () => {
    try {
      const available = await craftingApi.getAvailableCurrenciesForItem(item)
      setAvailableCurrencies(available)
    } catch (err) {
      console.error('Failed to load available currencies:', err)
    }
  }

  const handleCraft = async (currencyName: string) => {
    onLoadingChange(true)
    onMessage('')

    try {
      const result = await craftingApi.simulateCrafting({
        item,
        currency_name: currencyName,
      })

      if (result.success && result.result_item) {
        onHistoryAdd(item)
        onItemChange(result.result_item)
        onMessage(result.message || `Applied ${currencyName} successfully!`)

        // Update currency spending tracker
        const newSpent = { ...currencySpent }
        newSpent[currencyName] = (newSpent[currencyName] || 0) + 1
        onCurrencySpentChange(newSpent)
      } else {
        onMessage(result.message || 'Crafting failed')
      }
    } catch (error) {
      console.error('Crafting error:', error)
      onMessage('Failed to simulate crafting')
    } finally {
      onLoadingChange(false)
    }
  }

  const getTotalSpent = (): number => {
    return Object.values(currencySpent).reduce((sum, count) => sum + count, 0)
  }

  const isCurrencyAvailable = (currency: string): boolean => {
    return availableCurrencies.length === 0 || availableCurrencies.includes(currency)
  }

  return (
    <div className="crafting-controls-panel">
      {/* Currency Selection */}
      <div className="currency-selection">
        <label htmlFor="currency-select">Currency:</label>
        <select
          id="currency-select"
          value={selectedCurrency}
          onChange={(e) => setSelectedCurrency(e.target.value)}
          disabled={loading}
        >
          {currencies.map(currency => (
            <option
              key={currency}
              value={currency}
              disabled={!isCurrencyAvailable(currency)}
            >
              {currency} {!isCurrencyAvailable(currency) ? '(Not Available)' : ''}
            </option>
          ))}
        </select>
      </div>

      {/* Quick Craft Buttons */}
      <div className="quick-craft-buttons">
        <h4>Quick Craft</h4>
        <div className="currency-buttons">
          {currencies.filter(currency => isCurrencyAvailable(currency)).map(currency => (
            <button
              key={currency}
              onClick={() => handleCraft(currency)}
              disabled={loading}
              className={`currency-btn ${currency.toLowerCase().replace(/\s+/g, '-')}`}
              title={`Use ${currency}`}
            >
              {currency}
              {currencySpent[currency] && (
                <span className="usage-count">×{currencySpent[currency]}</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Main Craft Button */}
      <div className="main-craft-section">
        <button
          onClick={() => handleCraft(selectedCurrency)}
          disabled={loading || !selectedCurrency || !isCurrencyAvailable(selectedCurrency)}
          className="craft-btn"
        >
          {loading ? 'Crafting...' : `Use ${selectedCurrency}`}
        </button>
      </div>

      {/* Currency Spending Summary */}
      {getTotalSpent() > 0 && (
        <div className="spending-summary">
          <h4>Currency Spent</h4>
          <div className="spending-list">
            {Object.entries(currencySpent)
              .filter(([, count]) => count > 0)
              .map(([currency, count]) => (
                <div key={currency} className="spending-item">
                  <span className="currency-name">{currency}:</span>
                  <span className="currency-count">×{count}</span>
                </div>
              ))}
          </div>
          <div className="spending-total">
            Total operations: {getTotalSpent()}
          </div>
        </div>
      )}

      {/* Messages */}
      {message && (
        <div className={`message ${message.includes('Failed') || message.includes('Error') ? 'error' : 'success'}`}>
          {message}
        </div>
      )}
    </div>
  )
}