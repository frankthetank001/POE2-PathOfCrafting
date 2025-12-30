import { useState, useRef, useEffect, forwardRef, useImperativeHandle } from 'react'
import { marketApi, ExchangeRates, ItemPriceEstimate } from '@/services/market-api'
import { PoE2TradeListingPreview } from '@/components/poe2'
import type { CraftableItem } from '@/types/crafting'
import './TradePriceFlyout.css'

// Helper function to format defence values
function getDefenceDisplay(listing: { armour?: number | null; evasion?: number | null; energy_shield?: number | null }): string {
  const parts: string[] = [];
  if (listing.armour && listing.armour > 0) parts.push(`${listing.armour} AR`);
  if (listing.evasion && listing.evasion > 0) parts.push(`${listing.evasion} EV`);
  if (listing.energy_shield && listing.energy_shield > 0) parts.push(`${listing.energy_shield} ES`);
  return parts.join(' / ') || '-';
}

// Determine slot type from base_category or item base name
function getSlotFromCategory(baseCategory: string, baseName?: string): string {
  const directSlots = ['boots', 'helmet', 'gloves', 'shield', 'ring', 'amulet', 'belt', 'quiver', 'focus'];
  const lowerCat = baseCategory.toLowerCase();

  for (const slot of directSlots) {
    if (lowerCat === slot) return slot;
  }

  if (lowerCat.includes('armour') || lowerCat === 'body' || lowerCat === 'body_armour') {
    if (baseName) {
      const nameL = baseName.toLowerCase();
      if (nameL.includes('sandal') || nameL.includes('slipper') || nameL.includes('boot') ||
          nameL.includes('greave') || nameL.includes('sole') || nameL.includes('tread')) {
        return 'boots';
      }
      if (nameL.includes('helm') || nameL.includes('mask') || nameL.includes('hood') ||
          nameL.includes('crown') || nameL.includes('circlet') || nameL.includes('cap')) {
        return 'helmet';
      }
      if (nameL.includes('glove') || nameL.includes('gauntlet') || nameL.includes('mitt') ||
          nameL.includes('hand') || nameL.includes('wrap')) {
        return 'gloves';
      }
    }
    return 'body_armour';
  }

  if (lowerCat.includes('weapon') || ['wand', 'staff', 'bow', 'crossbow', 'mace', 'sceptre',
      'sword', 'axe', 'dagger', 'claw', 'flail', 'spear', 'talisman'].includes(lowerCat)) {
    return 'weapon';
  }

  return lowerCat;
}

// Determine which columns to show based on item slot
function getListingColumns(slot: string): Array<{ key: string; label: string; width?: string }> {
  const baseColumns = [
    { key: 'preview', label: '', width: '24px' },
    { key: 'price', label: 'Price', width: '70px' },
  ];

  if (['boots', 'helmet', 'gloves', 'body', 'body_armour', 'shield'].includes(slot)) {
    return [
      ...baseColumns,
      { key: 'defence', label: 'Defence' },
      ...(slot === 'boots' ? [{ key: 'ms', label: 'MS', width: '40px' }] : []),
      { key: 'eleRes', label: 'Ele', width: '40px' },
      { key: 'chaosRes', label: 'Chaos', width: '45px' },
      { key: 'age', label: 'Age', width: '50px' },
    ];
  }

  if (['ring', 'amulet', 'belt'].includes(slot)) {
    return [
      ...baseColumns,
      { key: 'life', label: 'Life', width: '45px' },
      { key: 'eleRes', label: 'Ele', width: '40px' },
      { key: 'chaosRes', label: 'Chaos', width: '45px' },
      { key: 'age', label: 'Age', width: '50px' },
    ];
  }

  if (slot === 'weapon' || ['wand', 'staff', 'bow', 'crossbow', 'mace', 'sceptre', 'sword', 'axe', 'dagger', 'claw', 'flail', 'spear', 'talisman'].includes(slot)) {
    return [
      ...baseColumns,
      { key: 'pDps', label: 'pDPS', width: '55px' },
      { key: 'tDps', label: 'tDPS', width: '55px' },
      { key: 'aps', label: 'APS', width: '45px' },
      { key: 'age', label: 'Age', width: '50px' },
    ];
  }

  return [
    ...baseColumns,
    { key: 'ilvl', label: 'iLvl', width: '40px' },
    { key: 'account', label: 'Account' },
    { key: 'age', label: 'Age', width: '50px' },
  ];
}

export interface TradePriceFlyoutHandle {
  handlePriceCheck: (useFilters?: boolean) => void
  priceCheckLoading: boolean
}

interface TradePriceFlyoutProps {
  item: CraftableItem
  exchangeRates: ExchangeRates | null
  isOpen: boolean
  onClose: () => void
  onMessage?: (message: string) => void
  onPriceResult?: (price: ItemPriceEstimate | null) => void
  // Selected mods for pricing (controlled by parent for highlighting in item display)
  selectedMods: Set<string>
  onSelectedModsChange: (mods: Set<string>) => void
  // Controlled filter states from parent (for mod display interactivity)
  priceRarityEnabled: boolean
  onPriceRarityEnabledChange: (value: boolean) => void
  priceIlvlEnabled: boolean
  onPriceIlvlEnabledChange: (value: boolean) => void
  priceModMinValues: Record<string, number>
  onPriceModMinValuesChange: (value: Record<string, number> | ((prev: Record<string, number>) => Record<string, number>)) => void
  usePseudoStats: Record<string, boolean>
  onUsePseudoStatsChange: (value: Record<string, boolean> | ((prev: Record<string, boolean>) => Record<string, boolean>)) => void
  enabledHiddenMods: Set<string>
  onEnabledHiddenModsChange: (value: Set<string> | ((prev: Set<string>) => Set<string>)) => void
  filtersChanged: boolean
  onFiltersChangedChange: (value: boolean) => void
}

export const TradePriceFlyout = forwardRef<TradePriceFlyoutHandle, TradePriceFlyoutProps>(({
  item,
  exchangeRates,
  isOpen,
  onClose,
  onMessage,
  onPriceResult,
  selectedMods,
  onSelectedModsChange: _onSelectedModsChange,  // Parent manages this
  priceRarityEnabled,
  onPriceRarityEnabledChange: _onPriceRarityEnabledChange,  // Changed in parent's item display
  priceIlvlEnabled,
  onPriceIlvlEnabledChange: _onPriceIlvlEnabledChange,  // Changed in parent's item display
  priceModMinValues,
  onPriceModMinValuesChange,
  usePseudoStats,
  onUsePseudoStatsChange,
  enabledHiddenMods,
  onEnabledHiddenModsChange,
  filtersChanged: _filtersChanged,  // Used for refresh button state
  onFiltersChangedChange: _onFiltersChangedChange,  // Set by parent when filters change
}, ref) => {
  // Suppress unused variable warnings for passed-through props
  void _onSelectedModsChange
  void _onPriceRarityEnabledChange
  void _onPriceIlvlEnabledChange
  void _filtersChanged
  void _onFiltersChangedChange
  // Price check state
  const [itemPrice, setItemPrice] = useState<ItemPriceEstimate | null>(null)
  const [priceCheckLoading, setPriceCheckLoading] = useState(false)
  const [priceCheckStatus, setPriceCheckStatus] = useState<string>('')
  const priceCheckAbortRef = useRef<AbortController | null>(null)
  const [pinnedListingTooltip, setPinnedListingTooltip] = useState<number | null>(null)
  const [hoveredListingTooltip, setHoveredListingTooltip] = useState<number | null>(null)
  // Use ref to track pseudo_stats synchronously (avoid stale closure issues)
  const pseudoStatsRef = useRef<ItemPriceEstimate['pseudo_stats'] | null>(null)

  // Filter states that are internal to the flyout (not used in parent mod display)
  const [priceEquipmentFilters, setPriceEquipmentFilters] = useState<Record<string, number>>({})
  const [priceEquipmentEnabled, setPriceEquipmentEnabled] = useState<Record<string, boolean>>({})
  const [priceStrictness, setPriceStrictness] = useState(80)
  const [purchaseType, setPurchaseType] = useState<string>(() => {
    return sessionStorage.getItem('tradePurchaseType') || 'any'
  })

  const handlePurchaseTypeChange = (newType: string) => {
    setPurchaseType(newType)
    sessionStorage.setItem('tradePurchaseType', newType)
  }

  // Format price in best currency
  const formatPriceDisplay = (chaosValue: number): string => {
    if (!exchangeRates) return `${chaosValue.toFixed(0)}c`

    const chaosInExalt = exchangeRates.rates['chaos']?.exalted_value || 0.003
    const divineInExalt = exchangeRates.rates['divine']?.exalted_value || 2
    const mirrorInExalt = exchangeRates.rates['mirror']?.exalted_value || 100

    const exaltedValue = chaosValue * chaosInExalt
    const divineValue = exaltedValue / divineInExalt
    const mirrorValue = exaltedValue / mirrorInExalt

    if (mirrorValue >= 1) return `${mirrorValue.toFixed(1)} mir`
    if (divineValue >= 1) return `${divineValue.toFixed(1)} div`
    return `${exaltedValue.toFixed(1)} ex`
  }

  // Format age from indexed_time
  const formatAge = (indexedTime: string | null): string => {
    if (!indexedTime) return '?'
    const indexed = new Date(indexedTime)
    const now = new Date()
    const diffMs = now.getTime() - indexed.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffDays > 0) return `${diffDays}d`
    if (diffHours > 0) return `${diffHours}h`
    return `${diffMins}m`
  }

  // Cancel ongoing price check
  const cancelPriceCheck = () => {
    if (priceCheckAbortRef.current) {
      priceCheckAbortRef.current.abort()
      priceCheckAbortRef.current = null
    }
    setPriceCheckLoading(false)
    setPriceCheckStatus('')
  }

  // Handle price check
  const handlePriceCheck = async (useFilters = false) => {
    if (priceCheckLoading) return

    const selectedPrefixes = item.prefix_mods.filter((_, idx) => selectedMods.has(`prefix-${idx}`))
    const selectedSuffixes = item.suffix_mods.filter((_, idx) => selectedMods.has(`suffix-${idx}`))

    if (selectedPrefixes.length === 0 && selectedSuffixes.length === 0) {
      onMessage?.('Select at least one mod to price')
      return
    }

    if (priceCheckAbortRef.current) {
      priceCheckAbortRef.current.abort()
    }
    priceCheckAbortRef.current = new AbortController()

    setPriceCheckLoading(true)
    setPriceCheckStatus('Searching trade site...')
    setItemPrice(null)
    setPinnedListingTooltip(null)

    try {
      const filteredItem = {
        ...item,
        prefix_mods: selectedPrefixes,
        suffix_mods: selectedSuffixes,
      }

      const hiddenModIndices = new Set<string>()
      // Use ref for synchronous access to pseudo_stats (avoids stale closure)
      if (pseudoStatsRef.current) {
        pseudoStatsRef.current.forEach(ps => {
          const isEnabled = usePseudoStats[ps.stat_id] ?? true
          if (isEnabled) {
            ps.contributing_mod_indices.forEach(i => {
              if (i < item.prefix_mods.length) {
                hiddenModIndices.add(`prefix-${i}`)
              } else {
                hiddenModIndices.add(`suffix-${i - item.prefix_mods.length}`)
              }
            })
          }
        })
      }

      const modMinValuesForApi: Record<string, number> = {}
      selectedPrefixes.forEach((_, newIdx) => {
        let origIdx = -1
        let count = 0
        for (let i = 0; i < item.prefix_mods.length; i++) {
          if (selectedMods.has(`prefix-${i}`)) {
            if (count === newIdx) {
              origIdx = i
              break
            }
            count++
          }
        }
        if (origIdx === -1) return

        const modKey = `prefix-${origIdx}`
        const isHidden = hiddenModIndices.has(modKey)
        const isExplicitlyEnabled = enabledHiddenMods.has(modKey)

        const minVal = priceModMinValues[modKey]
        if (minVal !== undefined) {
          if (isHidden && isExplicitlyEnabled) {
            modMinValuesForApi[`hidden-${origIdx}`] = minVal
          } else if (!isHidden) {
            modMinValuesForApi[String(newIdx)] = minVal
          }
        }
      })

      selectedSuffixes.forEach((_, newIdx) => {
        let origIdx = -1
        let count = 0
        for (let i = 0; i < item.suffix_mods.length; i++) {
          if (selectedMods.has(`suffix-${i}`)) {
            if (count === newIdx) {
              origIdx = i
              break
            }
            count++
          }
        }
        if (origIdx === -1) return

        const modKey = `suffix-${origIdx}`
        const isHidden = hiddenModIndices.has(modKey)
        const isExplicitlyEnabled = enabledHiddenMods.has(modKey)

        const minVal = priceModMinValues[modKey]
        if (minVal !== undefined) {
          if (isHidden && isExplicitlyEnabled) {
            const combinedIdx = item.prefix_mods.length + origIdx
            modMinValuesForApi[`hidden-${combinedIdx}`] = minVal
          } else if (!isHidden) {
            modMinValuesForApi[String(selectedPrefixes.length + newIdx)] = minVal
          }
        }
      })

      Object.entries(priceModMinValues).forEach(([key, value]) => {
        if (key.startsWith('pseudo-')) {
          modMinValuesForApi[key] = value
        }
      })

      const estimate = await marketApi.priceItem(
        filteredItem,
        undefined,
        useFilters ? priceEquipmentFilters : undefined,
        useFilters ? priceEquipmentEnabled : undefined,
        priceRarityEnabled,
        priceIlvlEnabled,
        modMinValuesForApi,
        usePseudoStats,
        purchaseType
      )

      // Always use fresh results from API
      console.log('[TradePriceFlyout] API estimate received:', {
        num_listings: estimate.num_listings,
        pseudo_stats: estimate.pseudo_stats,
        pseudo_stats_length: estimate.pseudo_stats?.length ?? 0
      })
      setItemPrice(estimate)
      onPriceResult?.(estimate)

      // Update ref synchronously for next check
      pseudoStatsRef.current = estimate.pseudo_stats || null

      // Initialize pseudo stats from fresh results
      if (estimate.pseudo_stats && estimate.pseudo_stats.length > 0) {
        const initialPseudoState: Record<string, boolean> = {}
        estimate.pseudo_stats.forEach(ps => {
          initialPseudoState[ps.stat_id] = true
        })
        console.log('[TradePriceFlyout] Initializing usePseudoStats:', initialPseudoState)
        onUsePseudoStatsChange(initialPseudoState)
      } else {
        console.log('[TradePriceFlyout] No pseudo_stats in estimate, skipping usePseudoStats init')
      }
      onEnabledHiddenModsChange(new Set())

      // Check if rate limited
      if (estimate.rate_limited) {
        const waitTime = estimate.rate_limit_wait || 60
        setPriceCheckStatus(`Rate limited (wait ${waitTime}s) - showing mod aggregations only`)
      } else {
        setPriceCheckStatus('')
      }
    } catch (error: any) {
      if (error.name === 'AbortError' || error.name === 'CanceledError') {
        return
      }
      console.error('Price check failed:', error)
      if (error.response?.status === 429) {
        const detail = error.response?.data?.detail || ''
        const waitMatch = detail.match(/(\d+)\s+seconds/)
        const waitSeconds = waitMatch ? parseInt(waitMatch[1]) : 60
        const waitMinutes = Math.ceil(waitSeconds / 60)
        setPriceCheckStatus(`Rate limited. Wait ${waitMinutes > 1 ? `~${waitMinutes} min` : `${waitSeconds}s`}`)
      } else if (error.response?.status === 404) {
        const emptyEstimate: ItemPriceEstimate = {
          min_price: 0,
          max_price: 0,
          median_price: 0,
          average_price: 0,
          currency: 'chaos',
          num_listings: 0,
          confidence: 'low',
          exalted_value: null,
          divine_value: null,
          search_criteria: {},
          pseudo_stats: [],
          trade_url: null,
          listings: [],
          outliers_removed: 0,
          avg_similarity: null,
          price_spread: null,
          unmatched_mods: []
        }
        setItemPrice(emptyEstimate)
        onPriceResult?.(emptyEstimate)
      } else {
        setPriceCheckStatus('Search failed - try again')
      }
    } finally {
      setPriceCheckLoading(false)
      priceCheckAbortRef.current = null
    }
  }

  // Expose handlePriceCheck and priceCheckLoading to parent via ref
  useImperativeHandle(ref, () => ({
    handlePriceCheck,
    priceCheckLoading,
  }), [handlePriceCheck, priceCheckLoading])

  // Clear internal state when item changes (to avoid stale pseudo_stats)
  useEffect(() => {
    setItemPrice(null)
    setPinnedListingTooltip(null)
    setHoveredListingTooltip(null)
    pseudoStatsRef.current = null  // Clear synchronously

    // Initialize equipment filters from calculated stats
    const equipFilters: Record<string, number> = {}
    const equipEnabled: Record<string, boolean> = {}
    if (item.calculated_stats) {
      for (const [stat, value] of Object.entries(item.calculated_stats)) {
        if (['Armour', 'Evasion'].includes(stat) && value > 0) {
          equipFilters[stat] = Math.floor(value * 0.5)
          equipEnabled[stat] = true
        }
      }
    }
    setPriceEquipmentFilters(equipFilters)
    setPriceEquipmentEnabled(equipEnabled)
  }, [item])

  // Start search when flyout opens with selected mods
  useEffect(() => {
    console.log('[TradePriceFlyout] Auto-start effect:', {
      isOpen,
      selectedModsSize: selectedMods.size,
      priceCheckLoading,
      conditionsMet: isOpen && selectedMods.size > 0 && !priceCheckLoading
    })
    if (isOpen && selectedMods.size > 0 && !priceCheckLoading) {
      // Always start a new search when opening (acts as refresh too)
      console.log('[TradePriceFlyout] Auto-starting price check NOW')
      handlePriceCheck(false)
    } else {
      console.log('[TradePriceFlyout] NOT auto-starting, conditions:', {
        isOpenCheck: isOpen,
        selectedModsCheck: selectedMods.size > 0,
        loadingCheck: !priceCheckLoading
      })
    }
  }, [isOpen])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (priceCheckAbortRef.current) {
        priceCheckAbortRef.current.abort()
      }
    }
  }, [])

  if (!isOpen) return null

  return (
    <div className="trade-price-flyout">
      <div className="trade-flyout-header">
        <h3>Price Check</h3>
        <button className="trade-flyout-close" onClick={() => { onClose(); cancelPriceCheck(); setPinnedListingTooltip(null); }}>✕</button>
      </div>

      <div className="trade-flyout-content">
        {/* Loading State */}
        {priceCheckLoading && (
          <div className="trade-loading-state">
            <div className="trade-loading-spinner"></div>
            <div className="trade-loading-status">{priceCheckStatus}</div>
            <button className="trade-loading-cancel" onClick={cancelPriceCheck}>
              Cancel
            </button>
          </div>
        )}

        {/* Filter Controls - Always visible */}
        {!priceCheckLoading && (
          <div className="trade-filter-controls">
            {/* Global Strictness Slider */}
            <div className="trade-strictness-compact">
              <span className="strictness-label">Min %</span>
              <input
                type="range"
                min={0}
                max={100}
                value={priceStrictness}
                onChange={(e) => {
                  const newStrictness = parseInt(e.target.value)
                  setPriceStrictness(newStrictness)

                  const newMinValues: Record<string, number> = {}
                  item.prefix_mods.forEach((mod, idx) => {
                    const value = mod.current_values?.[0] ?? mod.current_value ?? mod.stat_min ?? 0
                    newMinValues[`prefix-${idx}`] = Math.floor(value * newStrictness / 100)
                  })
                  item.suffix_mods.forEach((mod, idx) => {
                    const value = mod.current_values?.[0] ?? mod.current_value ?? mod.stat_min ?? 0
                    newMinValues[`suffix-${idx}`] = Math.floor(value * newStrictness / 100)
                  })
                  if (itemPrice?.pseudo_stats) {
                    itemPrice.pseudo_stats.forEach(ps => {
                      newMinValues[`pseudo-${ps.stat_id}`] = Math.floor(ps.total_value * newStrictness / 100)
                    })
                  }
                  onPriceModMinValuesChange(newMinValues)
                }}
                onMouseUp={() => handlePriceCheck(true)}
                onTouchEnd={() => handlePriceCheck(true)}
                className="strictness-slider-compact"
              />
              <span className="strictness-value">{priceStrictness}%</span>
            </div>

            {/* Purchase Type Dropdown */}
            <div className="trade-purchase-type">
              <label className="purchase-type-label">Listing:</label>
              <select
                value={purchaseType}
                onChange={(e) => {
                  handlePurchaseTypeChange(e.target.value)
                  setTimeout(() => handlePriceCheck(true), 50)
                }}
                className="purchase-type-select"
              >
                <option value="any">Any</option>
                <option value="securable">Instant Buyout Only</option>
                <option value="available">Buyout + In Person</option>
                <option value="online">In Person (Online)</option>
                <option value="onlineleague">In Person (Online in League)</option>
              </select>
            </div>
          </div>
        )}

        {/* Error State */}
        {!priceCheckLoading && !itemPrice && priceCheckStatus && (
          <div className="trade-error-state">
            <div className="trade-error-message">{priceCheckStatus}</div>
            <button className="trade-retry-btn" onClick={() => handlePriceCheck(true)}>
              Retry
            </button>
          </div>
        )}

        {/* Results */}
        {itemPrice && (
          <>
            {/* Rate Limited Notice */}
            {itemPrice.rate_limited && (
              <div className="trade-rate-limited-notice">
                <span className="rate-limit-icon">⏳</span>
                <span>Rate limited - wait {itemPrice.rate_limit_wait || 60}s to search</span>
                <button
                  className="trade-retry-btn"
                  onClick={() => handlePriceCheck(true)}
                  disabled={priceCheckLoading}
                >
                  Retry
                </button>
              </div>
            )}

            {/* Price Summary */}
            <div className="trade-summary">
              <div className="trade-summary-main">
                <span className="trade-summary-value">{formatPriceDisplay(itemPrice.median_price)}</span>
              </div>
              <span className={`trade-confidence ${itemPrice.confidence}`}>{itemPrice.confidence}</span>
            </div>

            {/* Enhanced Stats */}
            <div className="trade-enhanced-stats">
              <div className="enhanced-stat">
                <span className="enhanced-stat-label">Listings</span>
                <span className="enhanced-stat-value">{itemPrice.num_listings}</span>
              </div>
              {itemPrice.avg_similarity !== null && (
                <div className="enhanced-stat">
                  <span className="enhanced-stat-label">Similarity</span>
                  <span className={`enhanced-stat-value ${itemPrice.avg_similarity >= 0.7 ? 'good' : itemPrice.avg_similarity >= 0.5 ? 'medium' : 'low'}`}>
                    {Math.round(itemPrice.avg_similarity * 100)}%
                  </span>
                </div>
              )}
              {itemPrice.price_spread !== null && (
                <div className="enhanced-stat">
                  <span className="enhanced-stat-label">Spread</span>
                  <span className={`enhanced-stat-value ${itemPrice.price_spread < 30 ? 'good' : itemPrice.price_spread < 60 ? 'medium' : 'low'}`}>
                    ±{itemPrice.price_spread}%
                  </span>
                </div>
              )}
              {itemPrice.outliers_removed > 0 && (
                <div className="enhanced-stat outliers">
                  <span className="enhanced-stat-label">Outliers</span>
                  <span className="enhanced-stat-value warning">-{itemPrice.outliers_removed}</span>
                </div>
              )}
            </div>

            {/* Unmatched mods warning */}
            {itemPrice.unmatched_mods && itemPrice.unmatched_mods.length > 0 && (
              <div className="trade-unmatched-warning">
                <span className="warning-icon">⚠</span>
                <span className="warning-text">
                  {itemPrice.unmatched_mods.length} mod{itemPrice.unmatched_mods.length > 1 ? 's' : ''} not searchable:
                </span>
                <div className="unmatched-mods-list">
                  {itemPrice.unmatched_mods.map((mod, i) => (
                    <div key={i} className="unmatched-mod" title={mod.stat_text}>
                      {mod.name}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Equipment Stat Filters */}
            {Object.keys(priceEquipmentFilters).length > 0 && (
              <div className="trade-equipment-filters">
                <div className="trade-filters-header">
                  <span>Equipment Filters</span>
                  <button
                    className="trade-refresh-btn"
                    onClick={() => handlePriceCheck(true)}
                    disabled={priceCheckLoading}
                    title="Refresh search with current filters"
                  >
                    {priceCheckLoading ? '...' : '↻'}
                  </button>
                </div>
                {Object.entries(priceEquipmentFilters).map(([stat, minValue]) => {
                  const maxValue = item.calculated_stats?.[stat] || minValue
                  const displayName = stat.replace(/([A-Z])/g, ' $1').trim()
                  const isEnabled = priceEquipmentEnabled[stat] ?? true

                  return (
                    <div key={stat} className={`trade-filter-row ${!isEnabled ? 'disabled' : ''}`}>
                      <label className="trade-filter-checkbox">
                        <input
                          type="checkbox"
                          checked={isEnabled}
                          onChange={(e) => setPriceEquipmentEnabled(prev => ({
                            ...prev,
                            [stat]: e.target.checked
                          }))}
                        />
                        <span className="trade-filter-label">{displayName}</span>
                      </label>
                      <div className="trade-filter-slider">
                        <input
                          type="range"
                          min={0}
                          max={maxValue}
                          value={minValue}
                          disabled={!isEnabled}
                          onChange={(e) => setPriceEquipmentFilters(prev => ({
                            ...prev,
                            [stat]: parseInt(e.target.value)
                          }))}
                        />
                        <span className="trade-filter-value">{minValue}</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}

            {/* Listings Table */}
            {itemPrice.listings && itemPrice.listings.length > 0 ? (() => {
              const itemSlot = getSlotFromCategory(item.base_category, item.base_name);
              const columns = getListingColumns(itemSlot);

              return (
                <table className="trade-listings-table">
                  <thead>
                    <tr>
                      {columns.map(col => (
                        <th key={col.key} style={col.width ? { width: col.width } : undefined}>
                          {col.label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {itemPrice.listings.slice(0, 20).map((listing, idx) => {
                      const eleRes = listing.total_ele_res ?? 0;
                      const chaosRes = listing.total_chaos_res ?? 0;
                      const ms = listing.movement_speed ?? 0;
                      const life = listing.total_life ?? 0;

                      const rowClasses = [
                        'listing-row',
                        listing.is_outlier ? 'listing-outlier' : '',
                        listing.is_stale_cheap ? 'listing-stale-cheap' : '',
                        listing.value_comparison === 'better' ? 'listing-better' : '',
                        listing.value_comparison === 'worse' ? 'listing-worse' : '',
                      ].filter(Boolean).join(' ');

                      return (
                        <tr key={idx} className={rowClasses}>
                          {columns.map(col => {
                            switch (col.key) {
                              case 'preview':
                                const showPreview = pinnedListingTooltip === idx || hoveredListingTooltip === idx
                                return (
                                  <td key={col.key}>
                                    <button
                                      className={`listing-preview-btn ${pinnedListingTooltip === idx ? 'pinned' : ''}`}
                                      title={pinnedListingTooltip === idx ? "Click to unpin preview" : "Hover to preview, click to pin"}
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        setPinnedListingTooltip(pinnedListingTooltip === idx ? null : idx)
                                      }}
                                      onMouseEnter={() => setHoveredListingTooltip(idx)}
                                      onMouseLeave={() => setHoveredListingTooltip(null)}
                                    >
                                      👁
                                    </button>
                                    {showPreview && (
                                      <div
                                        className="item-preview-tooltip"
                                        style={{
                                          top: '50px',
                                          right: '430px',
                                        }}
                                      >
                                        <PoE2TradeListingPreview listing={listing} />
                                      </div>
                                    )}
                                  </td>
                                );
                              case 'price':
                                const priceVal = listing.price_amount || 0;
                                const priceCurr = listing.price_currency || 'chaos';
                                const compPct = listing.comparison_pct ?? 0;
                                const compSign = compPct >= 0 ? '+' : '';
                                const compClass = compPct < -10 ? 'comparison-better' : compPct > 10 ? 'comparison-worse' : 'comparison-similar';

                                return (
                                  <td key={col.key} className="listing-price-cell">
                                    <div className="price-with-comparison">
                                      <span className="listing-price-amount">{priceVal}</span>
                                      <span className="listing-price-currency">
                                        <img src={`/currency/${priceCurr}.png`} alt={priceCurr} />
                                      </span>
                                      {listing.comparison_pct !== undefined && listing.comparison_pct !== null && (
                                        <span
                                          className={`listing-comparison ${compClass}`}
                                          title={listing.stat_comparisons ? Object.entries(listing.stat_comparisons).map(([stat, data]) =>
                                            `${stat}: ${data.listing} vs ${data.user} (${data.diff_pct > 0 ? '+' : ''}${data.diff_pct}%)`
                                          ).join('\n') : ''}
                                        >
                                          {compSign}{Math.round(compPct)}%
                                        </span>
                                      )}
                                    </div>
                                  </td>
                                );
                              case 'defence':
                                return <td key={col.key} className="listing-defence">{getDefenceDisplay(listing)}</td>;
                              case 'ms':
                                return <td key={col.key} className="listing-ms">{ms > 0 ? `${ms}%` : '-'}</td>;
                              case 'eleRes':
                                return <td key={col.key} className="listing-res listing-ele-res">{eleRes > 0 ? `+${eleRes}%` : '-'}</td>;
                              case 'chaosRes':
                                return <td key={col.key} className="listing-res listing-chaos-res">{chaosRes > 0 ? `+${chaosRes}%` : '-'}</td>;
                              case 'life':
                                return <td key={col.key} className="listing-life">{life > 0 ? `+${life}` : '-'}</td>;
                              case 'ilvl':
                                return <td key={col.key} className="listing-ilvl">{listing.item_level}</td>;
                              case 'account':
                                return <td key={col.key} className="listing-account">{listing.account_name}</td>;
                              case 'pDps':
                                return <td key={col.key} className="listing-dps">{listing.physical_dps ? Math.round(listing.physical_dps) : '-'}</td>;
                              case 'tDps':
                                return <td key={col.key} className="listing-dps">{listing.total_dps ? Math.round(listing.total_dps) : '-'}</td>;
                              case 'aps':
                                return <td key={col.key} className="listing-aps">{listing.attacks_per_second?.toFixed(2) ?? '-'}</td>;
                              case 'age':
                                return <td key={col.key} className="listing-age">{formatAge(listing.indexed_time)}</td>;
                              default:
                                return <td key={col.key}>-</td>;
                            }
                          })}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              );
            })() : (
              <div className="trade-no-listings">No comparable listings found</div>
            )}
          </>
        )}
      </div>

      {/* Footer with trade link */}
      {itemPrice && itemPrice.trade_url && (
        <div className="trade-flyout-footer">
          <a
            href={itemPrice.trade_url}
            target="_blank"
            rel="noopener noreferrer"
            className="trade-site-link"
          >
            View on Trade Site ↗
          </a>
        </div>
      )}
    </div>
  )
})
