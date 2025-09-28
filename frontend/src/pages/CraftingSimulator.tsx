import { useState, useEffect } from 'react'
import { craftingApi } from '@/services/crafting-api'
import type { CraftableItem, ItemModifier, ItemRarity, ItemBasesBySlot, ItemBase } from '@/types/crafting'
import './CraftingSimulator.css'

function CraftingSimulator() {
  const [item, setItem] = useState<CraftableItem>({
    base_name: "Int Armour Body Armour",
    base_category: 'int_armour',
    rarity: 'Normal' as ItemRarity,
    item_level: 65,
    quality: 0,
    implicit_mods: [],
    prefix_mods: [],
    suffix_mods: [],
    corrupted: false,
  })

  const [currencies, setCurrencies] = useState<string[]>([])
  const [availableCurrencies, setAvailableCurrencies] = useState<string[]>([])
  const [selectedCurrency, setSelectedCurrency] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string>('')
  const [history, setHistory] = useState<string[]>([])
  const [itemHistory, setItemHistory] = useState<CraftableItem[]>([])
  const [currencySpent, setCurrencySpent] = useState<Record<string, number>>({})
  const [availableMods, setAvailableMods] = useState<{
    prefixes: ItemModifier[]
    suffixes: ItemModifier[]
  }>({ prefixes: [], suffixes: [] })
  const [modPoolFilter, setModPoolFilter] = useState<{
    search: string
    tags: string[]
    modType: 'all' | 'prefix' | 'suffix'
  }>({ search: '', tags: [], modType: 'all' })
  const [expandedModGroups, setExpandedModGroups] = useState<Set<string>>(new Set())
  const [itemBases, setItemBases] = useState<ItemBasesBySlot>({})
  const [selectedSlot, setSelectedSlot] = useState<string>('body_armour')
  const [selectedCategory, setSelectedCategory] = useState<string>('int_armour')

  useEffect(() => {
    loadCurrencies()
    loadItemBases()
  }, [])

  useEffect(() => {
    loadAvailableCurrencies()
    loadAvailableMods()
  }, [item])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
        e.preventDefault()
        handleUndo()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [itemHistory])

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
      const data = await craftingApi.getAvailableCurrenciesForItem(item)
      setAvailableCurrencies(data)
    } catch (err) {
      console.error('Failed to load available currencies:', err)
    }
  }

  const loadAvailableMods = async () => {
    try {
      const data = await craftingApi.getAvailableMods(item)
      setAvailableMods({
        prefixes: data.prefixes,
        suffixes: data.suffixes,
      })
    } catch (err) {
      console.error('Failed to load available mods:', err)
    }
  }

  const loadItemBases = async () => {
    try {
      const data = await craftingApi.getItemBases()
      setItemBases(data)

      // Set default selected category (int_armour for body_armour)
      if (data.body_armour && data.body_armour.includes('int_armour')) {
        setSelectedCategory('int_armour')
      }
    } catch (err) {
      console.error('Failed to load item bases:', err)
    }
  }

  const handleCraft = async (currencyName: string) => {
    setLoading(true)
    setMessage('')

    try {
      const result = await craftingApi.simulateCrafting({
        item,
        currency_name: currencyName,
      })

      if (result.success && result.result_item) {
        setItemHistory([...itemHistory, item])
        setItem(result.result_item)
        setMessage(`✓ ${result.message}`)
        setHistory([...history, `Used ${currencyName}: ${result.message}`])

        setCurrencySpent(prev => ({
          ...prev,
          [currencyName]: (prev[currencyName] || 0) + 1
        }))
      } else {
        setMessage(`✗ ${result.message}`)
      }
    } catch (err: any) {
      setMessage(`Error: ${err.response?.data?.detail || 'Failed to simulate'}`)
    } finally {
      setLoading(false)
    }
  }

  const handleUndo = () => {
    if (itemHistory.length === 0) return

    const previousItem = itemHistory[itemHistory.length - 1]
    const lastHistory = history[history.length - 1]

    const currencyMatch = lastHistory.match(/Used ([^:]+):/)
    if (currencyMatch) {
      const currencyName = currencyMatch[1]
      setCurrencySpent(prev => {
        const newSpent = { ...prev }
        if (newSpent[currencyName] > 1) {
          newSpent[currencyName]--
        } else {
          delete newSpent[currencyName]
        }
        return newSpent
      })
    }

    setItem(previousItem)
    setItemHistory(itemHistory.slice(0, -1))
    setHistory(history.slice(0, -1))
    setMessage('↶ Undone last action')
  }

  const handleReset = () => {
    setItem({
      base_name: getDisplayName(selectedSlot, selectedCategory),
      base_category: selectedCategory,
      rarity: 'Normal' as ItemRarity,
      item_level: 65,
      quality: 0,
      implicit_mods: [],
      prefix_mods: [],
      suffix_mods: [],
      corrupted: false,
    })
    setMessage('')
    setHistory([])
    setItemHistory([])
    setCurrencySpent({})
  }

  const getRarityColor = (rarity: string) => {
    switch (rarity) {
      case 'Normal': return '#c8c8c8'
      case 'Magic': return '#8888ff'
      case 'Rare': return '#ffff77'
      case 'Unique': return '#af6025'
      default: return '#c8c8c8'
    }
  }

  const renderModifier = (mod: ItemModifier) => {
    const value = mod.current_value !== undefined
      ? Math.round(mod.current_value)
      : mod.stat_min !== undefined && mod.stat_max !== undefined
        ? `${mod.stat_min}-${mod.stat_max}`
        : '?'

    const statText = mod.stat_text.replace('{}', value.toString())
    const modName = mod.name || 'Unknown'
    const rangeText = mod.stat_min !== undefined && mod.stat_max !== undefined
      ? `(${mod.stat_min}-${mod.stat_max})`
      : ''

    const tooltipText = [
      `Name: ${modName}`,
      `Tier: ${mod.tier}`,
      mod.required_ilvl ? `Required ilvl: ${mod.required_ilvl}` : null,
      mod.mod_group ? `Group: ${mod.mod_group}` : null,
      mod.stat_min !== undefined && mod.stat_max !== undefined
        ? `Range: ${mod.stat_min}-${mod.stat_max}`
        : null,
      mod.tags && mod.tags.length > 0 ? `Tags: ${mod.tags.join(', ')}` : null,
    ].filter(Boolean).join('\n')

    return (
      <span className="mod-with-info" title={tooltipText}>
        {statText} {rangeText && <span className="mod-range">{rangeText}</span>}
      </span>
    )
  }

  const getGroupedMods = (modType: 'prefix' | 'suffix') => {
    let mods = modType === 'prefix' ? availableMods.prefixes : availableMods.suffixes

    if (modPoolFilter.search) {
      const search = modPoolFilter.search.toLowerCase()
      mods = mods.filter(
        mod =>
          mod.name.toLowerCase().includes(search) ||
          mod.stat_text.toLowerCase().includes(search) ||
          mod.mod_group?.toLowerCase().includes(search)
      )
    }

    if (modPoolFilter.tags.length > 0) {
      mods = mods.filter(mod =>
        modPoolFilter.tags.some(tag => mod.tags?.includes(tag))
      )
    }

    // Group by mod_group and sort by tier (tier 1 is highest)
    const grouped = mods.reduce((acc, mod) => {
      const group = mod.mod_group || 'unknown'
      if (!acc[group]) acc[group] = []
      acc[group].push(mod)
      return acc
    }, {} as Record<string, ItemModifier[]>)


    // Sort each group by tier (ascending - tier 1 first)
    Object.keys(grouped).forEach(group => {
      grouped[group].sort((a, b) => a.tier - b.tier)
    })

    return grouped
  }

  const toggleModGroup = (groupKey: string) => {
    const newExpanded = new Set(expandedModGroups)
    if (newExpanded.has(groupKey)) {
      newExpanded.delete(groupKey)
    } else {
      newExpanded.add(groupKey)
    }
    setExpandedModGroups(newExpanded)
  }

  const allTags = Array.from(
    new Set([
      ...availableMods.prefixes.flatMap(m => m.tags || []),
      ...availableMods.suffixes.flatMap(m => m.tags || []),
    ])
  ).sort()

  const [modsPoolCollapsed, setModsPoolCollapsed] = useState(false)

  const getDisplayName = (slot: string, category: string) => {
    return `${category.replace('_', ' ')} ${slot.replace('_', ' ')}`
  }

  const formatSlotName = (slot: string) => {
    return slot.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  const formatCategoryName = (category: string) => {
    return category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  return (
    <div className="crafting-simulator">
      <h2 className="page-title">Crafting Simulator</h2>
      <p className="page-subtitle">Experiment with crafting currencies on items</p>

      <div className="item-base-selector">
        <h3>Item Base Selection</h3>
        <div className="base-selector-row">
          <div className="slot-selector">
            <label htmlFor="slot-select">Slot:</label>
            <select
              id="slot-select"
              value={selectedSlot}
              onChange={(e) => {
                setSelectedSlot(e.target.value)
                const categoriesForSlot = itemBases[e.target.value]
                if (categoriesForSlot && categoriesForSlot.length > 0) {
                  setSelectedCategory(categoriesForSlot[0])
                }
              }}
            >
              {Object.keys(itemBases).map(slot => (
                <option key={slot} value={slot}>
                  {formatSlotName(slot)}
                </option>
              ))}
            </select>
          </div>

          <div className="base-selector">
            <label htmlFor="category-select">Category:</label>
            <select
              id="category-select"
              value={selectedCategory}
              onChange={(e) => {
                setSelectedCategory(e.target.value)
                setItem({
                  base_name: getDisplayName(selectedSlot, e.target.value),
                  base_category: e.target.value,
                  rarity: 'Normal' as ItemRarity,
                  item_level: 65,
                  quality: 0,
                  implicit_mods: [],
                  prefix_mods: [],
                  suffix_mods: [],
                  corrupted: false,
                })
                setMessage('')
                setHistory([])
                setItemHistory([])
                setCurrencySpent({})
              }}
            >
              {(itemBases[selectedSlot] || []).map(category => (
                <option key={category} value={category}>
                  {formatCategoryName(category)}
                </option>
              ))}
            </select>
          </div>

          <div className="base-info">
            <span className="base-category">{selectedCategory}</span>
            <span className="base-ilvl">ilvl 65</span>
            <span className="base-slot">{formatSlotName(selectedSlot)}</span>
          </div>
        </div>
      </div>

      <div className="currency-bar">
        <div className="currency-bar-header">
          <h3>Available Currencies</h3>
          <button
            className="undo-button-top"
            onClick={handleUndo}
            disabled={itemHistory.length === 0}
            title="Undo last action (Ctrl+Z)"
          >
            ↶ Undo
          </button>
        </div>
        {availableCurrencies.length === 0 ? (
          <p className="no-currencies-bar">No currencies can be applied to this item</p>
        ) : (
          <div className="currency-buttons-row">
            {availableCurrencies.map((currency) => (
              <button
                key={currency}
                className="currency-button-compact"
                onClick={() => handleCraft(currency)}
                disabled={loading}
                title={currency}
              >
                {currency}
              </button>
            ))}
          </div>
        )}
        {message && (
          <div className={`message-compact ${message.startsWith('✓') ? 'success' : message.startsWith('↶') ? 'info' : 'error'}`}>
            {message}
          </div>
        )}
      </div>

      <div className={`simulator-layout ${modsPoolCollapsed ? 'mods-collapsed' : ''}`}>
        <div className="mods-pool-panel">
          <div className="mods-pool-header">
            <div className="mods-pool-title-row">
              <h3>Available Mods</h3>
              <button
                className="collapse-button"
                onClick={() => setModsPoolCollapsed(!modsPoolCollapsed)}
                title={modsPoolCollapsed ? "Expand" : "Collapse"}
              >
                {modsPoolCollapsed ? '→' : '←'}
              </button>
            </div>
            {!modsPoolCollapsed && (
              <div className="mods-pool-stats">
                <span className="stat-badge prefix-badge">
                  {availableMods.prefixes.length} Prefixes
                </span>
                <span className="stat-badge suffix-badge">
                  {availableMods.suffixes.length} Suffixes
                </span>
              </div>
            )}
          </div>

          {!modsPoolCollapsed && (
            <>
              <div className="mods-pool-filters">
                <input
                  type="text"
                  className="search-input"
                  placeholder="Search mods..."
                  value={modPoolFilter.search}
                  onChange={e => setModPoolFilter({ ...modPoolFilter, search: e.target.value })}
                />
              </div>

              <div className="mods-pool-columns">
            <div className="mods-pool-column">
              <h4 className="column-title">Prefixes ({Object.keys(getGroupedMods('prefix')).length} groups)</h4>
              <div className="mods-pool-list">
                {Object.entries(getGroupedMods('prefix')).map(([groupKey, groupMods]) => {
                  const bestTier = groupMods[0] // Tier 1 (highest)
                  const maxIlvl = Math.max(...groupMods.map(m => m.required_ilvl || 1))
                  const isExpanded = expandedModGroups.has(`prefix-${groupKey}`)

                  return (
                    <div key={groupKey} className="pool-mod-group">
                      <div
                        className="pool-mod-group-header prefix"
                        onClick={() => toggleModGroup(`prefix-${groupKey}`)}
                      >
                        <div className="group-main-info">
                          <span className="pool-mod-stat-main">{bestTier.stat_text}</span>
                          <div className="group-summary">
                            <span className="group-tier-range">T1-T{Math.max(...groupMods.map(m => m.tier))}</span>
                            <span className="group-max-ilvl">ilvl {maxIlvl}</span>
                          </div>
                        </div>
                        <span className="expand-indicator">{isExpanded ? '−' : '+'}</span>
                      </div>

                      {isExpanded && (
                        <div className="tier-breakdown">
                          {groupMods.map((mod, idx) => (
                            <div key={idx} className="tier-item">
                              <div className="tier-header">
                                <span className="tier-label">T{mod.tier}</span>
                                <span className="tier-ilvl">ilvl {mod.required_ilvl}</span>
                              </div>
                              {mod.stat_min !== undefined && mod.stat_max !== undefined && (
                                <div className="tier-range">{mod.stat_min}-{mod.stat_max}</div>
                              )}
                              {mod.tags && mod.tags.length > 0 && (
                                <div className="tier-tags">
                                  {mod.tags.slice(0, 3).map((tag, i) => (
                                    <span key={i} className="pool-tag">{tag}</span>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>

            <div className="mods-pool-column">
              <h4 className="column-title">Suffixes ({Object.keys(getGroupedMods('suffix')).length} groups)</h4>
              <div className="mods-pool-list">
                {Object.entries(getGroupedMods('suffix')).map(([groupKey, groupMods]) => {
                  const bestTier = groupMods[0] // Tier 1 (highest)
                  const maxIlvl = Math.max(...groupMods.map(m => m.required_ilvl || 1))
                  const isExpanded = expandedModGroups.has(`suffix-${groupKey}`)

                  return (
                    <div key={groupKey} className="pool-mod-group">
                      <div
                        className="pool-mod-group-header suffix"
                        onClick={() => toggleModGroup(`suffix-${groupKey}`)}
                      >
                        <div className="group-main-info">
                          <span className="pool-mod-stat-main">{bestTier.stat_text}</span>
                          <div className="group-summary">
                            <span className="group-tier-range">T1-T{Math.max(...groupMods.map(m => m.tier))}</span>
                            <span className="group-max-ilvl">ilvl {maxIlvl}</span>
                          </div>
                        </div>
                        <span className="expand-indicator">{isExpanded ? '−' : '+'}</span>
                      </div>

                      {isExpanded && (
                        <div className="tier-breakdown">
                          {groupMods.map((mod, idx) => (
                            <div key={idx} className="tier-item">
                              <div className="tier-header">
                                <span className="tier-label">T{mod.tier}</span>
                                <span className="tier-ilvl">ilvl {mod.required_ilvl}</span>
                              </div>
                              {mod.stat_min !== undefined && mod.stat_max !== undefined && (
                                <div className="tier-range">{mod.stat_min}-{mod.stat_max}</div>
                              )}
                              {mod.tags && mod.tags.length > 0 && (
                                <div className="tier-tags">
                                  {mod.tags.slice(0, 3).map((tag, i) => (
                                    <span key={i} className="pool-tag">{tag}</span>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
            </>
          )}
        </div>
        <div className="center-panel">
          <div className="item-display">
            <div className="item-header">
              <h3
                className="item-name"
                style={{ color: getRarityColor(item.rarity) }}
              >
                {item.base_name}
              </h3>
              <span className="item-rarity-badge">{item.rarity}</span>
            </div>

            <div className="item-details">
              <div className="detail-row">
                <span className="detail-label">Item Level:</span>
                <span className="detail-value">{item.item_level}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Quality:</span>
                <span className="detail-value">+{item.quality}%</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Affixes:</span>
                <span className="detail-value">
                  {item.prefix_mods.length + item.suffix_mods.length} / 6
                </span>
              </div>
            </div>

            {item.implicit_mods.length > 0 && (
              <div className="mods-section">
                <h4 className="mods-title">Implicit</h4>
                {item.implicit_mods.map((mod, idx) => (
                  <div key={idx} className="mod-line implicit">
                    {renderModifier(mod)}
                  </div>
                ))}
              </div>
            )}

            {item.prefix_mods.length > 0 && (
              <div className="mods-section">
                <h4 className="mods-title">Prefixes ({item.prefix_mods.length}/3)</h4>
                {item.prefix_mods.map((mod, idx) => (
                  <div key={idx} className="mod-line prefix">
                    <div className="mod-stat">
                      {renderModifier(mod)}
                    </div>
                    <div className="mod-metadata">
                      <span className="mod-tier">T{mod.tier}</span>
                      <span className="mod-name">{mod.name}</span>
                      {mod.tags && mod.tags.length > 0 && (
                        <div className="mod-tags">
                          {mod.tags.slice(0, 2).map((tag, i) => (
                            <span key={i} className="mod-tag">{tag}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {item.suffix_mods.length > 0 && (
              <div className="mods-section">
                <h4 className="mods-title">Suffixes ({item.suffix_mods.length}/3)</h4>
                {item.suffix_mods.map((mod, idx) => (
                  <div key={idx} className="mod-line suffix">
                    <div className="mod-stat">
                      {renderModifier(mod)}
                    </div>
                    <div className="mod-metadata">
                      <span className="mod-tier">T{mod.tier}</span>
                      <span className="mod-name">{mod.name}</span>
                      {mod.tags && mod.tags.length > 0 && (
                        <div className="mod-tags">
                          {mod.tags.slice(0, 2).map((tag, i) => (
                            <span key={i} className="mod-tag">{tag}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {item.prefix_mods.length === 0 && item.suffix_mods.length === 0 && (
              <div className="empty-mods">
                <p>No explicit modifiers yet</p>
              </div>
            )}

            {item.corrupted && (
              <div className="corrupted-tag">Corrupted</div>
            )}
          </div>

          <button className="reset-button" onClick={handleReset}>
            Reset Item
          </button>

          {Object.keys(currencySpent).length > 0 && (
            <div className="currency-tracker">
              <h3>Currency Spent</h3>
              <div className="currency-spent-list">
                {Object.entries(currencySpent).map(([currency, count]) => (
                  <div key={currency} className="currency-spent-item">
                    <span className="currency-spent-name">{currency}</span>
                    <span className="currency-spent-count">×{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="history-section">
            <h3>Crafting History</h3>
            {history.length === 0 ? (
              <p className="empty-history">No actions yet</p>
            ) : (
              <div className="history-list">
                {history.map((entry, idx) => (
                  <div key={idx} className="history-entry">
                    <span className="history-number">{idx + 1}.</span>
                    <span className="history-text">{entry}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default CraftingSimulator