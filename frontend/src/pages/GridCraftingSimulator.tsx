import { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import { craftingApi, HiddenTagsConfig } from '@/services/crafting-api'
import { marketApi, ExchangeRates, ItemPriceEstimate } from '@/services/market-api'
import { TradePriceFlyout } from '@/components/TradePriceFlyout'
import { UnifiedCurrencyStash } from '@/components/UnifiedCurrencyStash'
import { SaveCraftModal } from '@/components/SaveCraftModal'
import { LocalCraftsList } from '@/components/LocalCraftsList'
import { PoE2ItemFrame, PoE2Separator, PoE2Section, PoE2Property, PoE2TwoColumn, PoE2Column } from '@/components/poe2'
import type { CraftableItem, ItemModifier, ItemRarity, ItemBasesBySlot, SocketedRune } from '@/types/crafting'
import type { CraftSnapshot } from '@/types/saved-craft'
import { CURRENCY_DESCRIPTIONS } from '@/data/currency-descriptions'
import './GridCraftingSimulator.css'

// Tag color mapping for consistent tag colors across the UI
const TAG_COLORS: Record<string, { bg: string; border: string; text: string; hover: string }> = {
  // Damage types
  physical: { bg: 'rgba(200, 150, 100, 0.15)', border: 'rgba(200, 150, 100, 0.4)', text: '#d4a574', hover: 'rgba(200, 150, 100, 0.25)' },
  fire: { bg: 'rgba(255, 100, 50, 0.15)', border: 'rgba(255, 100, 50, 0.4)', text: '#ff8866', hover: 'rgba(255, 100, 50, 0.25)' },
  cold: { bg: 'rgba(100, 180, 255, 0.15)', border: 'rgba(100, 180, 255, 0.4)', text: '#88ccff', hover: 'rgba(100, 180, 255, 0.25)' },
  lightning: { bg: 'rgba(150, 150, 255, 0.15)', border: 'rgba(150, 150, 255, 0.4)', text: '#a8a8ff', hover: 'rgba(150, 150, 255, 0.25)' },
  chaos: { bg: 'rgba(200, 100, 200, 0.15)', border: 'rgba(200, 100, 200, 0.4)', text: '#d888d8', hover: 'rgba(200, 100, 200, 0.25)' },
  elemental: { bg: 'rgba(150, 255, 200, 0.15)', border: 'rgba(150, 255, 200, 0.4)', text: '#99ffcc', hover: 'rgba(150, 255, 200, 0.25)' },

  // Defenses
  life: { bg: 'rgba(255, 80, 80, 0.15)', border: 'rgba(255, 80, 80, 0.4)', text: '#ff9999', hover: 'rgba(255, 80, 80, 0.25)' },
  mana: { bg: 'rgba(100, 120, 255, 0.15)', border: 'rgba(100, 120, 255, 0.4)', text: '#88aaff', hover: 'rgba(100, 120, 255, 0.25)' },
  energy_shield: { bg: 'rgba(120, 200, 255, 0.15)', border: 'rgba(120, 200, 255, 0.4)', text: '#99ddff', hover: 'rgba(120, 200, 255, 0.25)' },
  evasion: { bg: 'rgba(100, 200, 100, 0.15)', border: 'rgba(100, 200, 100, 0.4)', text: '#88cc88', hover: 'rgba(100, 200, 100, 0.25)' },
  armour: { bg: 'rgba(180, 180, 180, 0.15)', border: 'rgba(180, 180, 180, 0.4)', text: '#cccccc', hover: 'rgba(180, 180, 180, 0.25)' },

  // Resistances
  resistance: { bg: 'rgba(150, 220, 150, 0.15)', border: 'rgba(150, 220, 150, 0.4)', text: '#aaddaa', hover: 'rgba(150, 220, 150, 0.25)' },

  // Attributes
  attribute: { bg: 'rgba(220, 200, 150, 0.15)', border: 'rgba(220, 200, 150, 0.4)', text: '#ddcc99', hover: 'rgba(220, 200, 150, 0.25)' },
  strength: { bg: 'rgba(255, 100, 100, 0.15)', border: 'rgba(255, 100, 100, 0.4)', text: '#ff9999', hover: 'rgba(255, 100, 100, 0.25)' },
  dexterity: { bg: 'rgba(100, 255, 100, 0.15)', border: 'rgba(100, 255, 100, 0.4)', text: '#99ff99', hover: 'rgba(100, 255, 100, 0.25)' },
  intelligence: { bg: 'rgba(100, 150, 255, 0.15)', border: 'rgba(100, 150, 255, 0.4)', text: '#8899ff', hover: 'rgba(100, 150, 255, 0.25)' },

  // Skills & Gems
  gem: { bg: 'rgba(100, 255, 200, 0.15)', border: 'rgba(100, 255, 200, 0.4)', text: '#88ffcc', hover: 'rgba(100, 255, 200, 0.25)' },
  skill: { bg: 'rgba(150, 200, 255, 0.15)', border: 'rgba(150, 200, 255, 0.4)', text: '#aaccff', hover: 'rgba(150, 200, 255, 0.25)' },
  spell: { bg: 'rgba(180, 130, 255, 0.15)', border: 'rgba(180, 130, 255, 0.4)', text: '#bb99ff', hover: 'rgba(180, 130, 255, 0.25)' },
  attack: { bg: 'rgba(255, 150, 100, 0.15)', border: 'rgba(255, 150, 100, 0.4)', text: '#ffaa88', hover: 'rgba(255, 150, 100, 0.25)' },

  // Special mechanics
  critical: { bg: 'rgba(255, 200, 50, 0.15)', border: 'rgba(255, 200, 50, 0.4)', text: '#ffdd66', hover: 'rgba(255, 200, 50, 0.25)' },
  crit: { bg: 'rgba(255, 200, 50, 0.15)', border: 'rgba(255, 200, 50, 0.4)', text: '#ffdd66', hover: 'rgba(255, 200, 50, 0.25)' },
  ailment: { bg: 'rgba(200, 100, 255, 0.15)', border: 'rgba(200, 100, 255, 0.4)', text: '#cc88ff', hover: 'rgba(200, 100, 255, 0.25)' },
  curse: { bg: 'rgba(150, 50, 150, 0.15)', border: 'rgba(150, 50, 150, 0.4)', text: '#aa66aa', hover: 'rgba(150, 50, 150, 0.25)' },
  minion: { bg: 'rgba(150, 255, 150, 0.15)', border: 'rgba(150, 255, 150, 0.4)', text: '#aaffaa', hover: 'rgba(150, 255, 150, 0.25)' },

  // Item types
  jewellery: { bg: 'rgba(212, 175, 55, 0.15)', border: 'rgba(212, 175, 55, 0.4)', text: '#d4af37', hover: 'rgba(212, 175, 55, 0.25)' },
  weapon: { bg: 'rgba(200, 100, 100, 0.15)', border: 'rgba(200, 100, 100, 0.4)', text: '#cc8888', hover: 'rgba(200, 100, 100, 0.25)' },

  // Boss tags
  ulaman: { bg: 'rgba(255, 150, 50, 0.15)', border: 'rgba(255, 150, 50, 0.4)', text: '#ffaa66', hover: 'rgba(255, 150, 50, 0.25)' },
  kurgal: { bg: 'rgba(100, 150, 200, 0.15)', border: 'rgba(100, 150, 200, 0.4)', text: '#88aacc', hover: 'rgba(100, 150, 200, 0.25)' },
  amanamu: { bg: 'rgba(150, 100, 200, 0.15)', border: 'rgba(150, 100, 200, 0.4)', text: '#aa88cc', hover: 'rgba(150, 100, 200, 0.25)' },
}

// Generate a unique color for tags not in the predefined list
function getTagColor(tag: string): { bg: string; border: string; text: string; hover: string } {
  if (TAG_COLORS[tag.toLowerCase()]) {
    return TAG_COLORS[tag.toLowerCase()]
  }

  // Generate a color based on tag name hash
  let hash = 0
  for (let i = 0; i < tag.length; i++) {
    hash = tag.charCodeAt(i) + ((hash << 5) - hash)
  }

  const hue = Math.abs(hash % 360)
  const saturation = 60 + (Math.abs(hash) % 20) // 60-80%
  const lightness = 55 + (Math.abs(hash >> 8) % 15) // 55-70%

  return {
    bg: `hsla(${hue}, ${saturation}%, ${lightness}%, 0.15)`,
    border: `hsla(${hue}, ${saturation}%, ${lightness}%, 0.4)`,
    text: `hsl(${hue}, ${saturation}%, ${lightness}%)`,
    hover: `hsla(${hue}, ${saturation}%, ${lightness}%, 0.25)`
  }
}

// Generate a consistent color for exclusion group IDs
function getExclusionGroupColor(groupId: string): { bg: string; border: string; text: string } {
  let hash = 0
  for (let i = 0; i < groupId.length; i++) {
    hash = groupId.charCodeAt(i) + ((hash << 5) - hash)
  }

  const hue = Math.abs(hash % 360)
  return {
    bg: `hsla(${hue}, 70%, 60%, 0.2)`,
    border: `hsla(${hue}, 70%, 60%, 0.5)`,
    text: `hsl(${hue}, 70%, 70%)`
  }
}

// Map catalyst type IDs to their display names (matching in-game text)
const CATALYST_DISPLAY_NAMES: Record<string, string> = {
  flesh: 'Life Modifiers',
  neural: 'Mana Modifiers',
  carapace: 'Defence Modifiers',
  'uul-netol': 'Physical Modifiers',
  xoph: 'Fire Modifiers',
  tul: 'Cold Modifiers',
  esh: 'Lightning Modifiers',
  chayula: 'Chaos Modifiers',
  reaver: 'Attack Modifiers',
  sibilant: 'Caster Modifiers',
  skittering: 'Speed Modifiers',
  adaptive: 'Attribute Modifiers',
}

function getCatalystDisplayName(catalystType: string): string {
  return CATALYST_DISPLAY_NAMES[catalystType] || `${catalystType} Modifiers`
}

// Get defence display string from listing

interface TabContentProps {
  item: CraftableItem
  setItem: (item: CraftableItem) => void
  history: string[]
  itemHistory: CraftableItem[]
  currencySpent: Record<string, number>
  exchangeRates: ExchangeRates | null
  onRevertToStep: (stepIndex: number) => void
  onClearHistory: () => void
  onHistoryReset: () => void
  setMessage: (message: string) => void
  onItemCreated?: () => void
  getCurrencyIconUrl?: (currency: string) => string
  stepComments?: Record<number, string>
  onUpdateComment?: (stepIndex: number, comment: string) => void
  baseStepIndex?: number
  onSetBaseStep?: (stepIndex: number | null) => void
  basePriceEstimate?: { exalted: number; divine: number } | null
  onCheckBasePrice?: () => void
  basePriceLoading?: boolean
}

function ItemTab({ setItem, onHistoryReset, setMessage, onItemCreated }: TabContentProps) {
  const [itemBases, setItemBases] = useState<ItemBasesBySlot>({})
  const [selectedSlot, setSelectedSlot] = useState<string>('')
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [availableBases, setAvailableBases] = useState<Array<{name: string, description: string, default_ilvl: number, base_stats: Record<string, number>}>>([])
  const [selectedBase, setSelectedBase] = useState<string>('')
  const [selectedItemLevel, setSelectedItemLevel] = useState<number>(82)
  const [itemPasteText, setItemPasteText] = useState('')
  const [pasteExpanded, setPasteExpanded] = useState(false)
  const [pasteMessage, setPasteMessage] = useState('')
  const [mode, setMode] = useState<'paste' | 'base'>('base')

  useEffect(() => {
    loadItemBases()
  }, [])

  useEffect(() => {
    if (selectedSlot && itemBases[selectedSlot]) {
      const categories = itemBases[selectedSlot]
      if (Array.isArray(categories) && categories.length > 0 && !categories.includes(selectedCategory)) {
        setSelectedCategory(categories[0])
      }
    }
  }, [selectedSlot, itemBases, selectedCategory])

  useEffect(() => {
    if (selectedSlot && selectedCategory) {
      loadAvailableBases()
    }
  }, [selectedSlot, selectedCategory])

  const loadAvailableBases = async () => {
    try {
      console.log('[ItemTab] Loading available bases for:', selectedSlot, selectedCategory)
      const bases = await craftingApi.getBasesForSlotCategory(selectedSlot, selectedCategory)
      console.log('[ItemTab] Loaded bases:', bases.length, 'bases')
      setAvailableBases(bases)

      // Set default base selection in dropdown (doesn't create the item yet)
      // For body + int_armour, prefer Vile Robe
      if (selectedSlot === 'body' && selectedCategory === 'int_armour') {
        const vileRobe = bases.find(base => base.name === 'Vile Robe')
        if (vileRobe) {
          console.log('[ItemTab] Setting Vile Robe as default selection')
          setSelectedBase('Vile Robe')
          return
        }
      }

      // Otherwise use first available base
      if (bases.length > 0) {
        console.log('[ItemTab] Setting first base as default:', bases[0].name)
        setSelectedBase(bases[0].name)
      }
    } catch (err) {
      console.error('[ItemTab] Failed to load available bases:', err)
    }
  }

  const loadItemBases = async () => {
    try {
      console.log('[ItemTab] Loading item base slots...')
      const bases = await craftingApi.getItemBases()
      console.log('[ItemTab] Loaded slots:', Object.keys(bases))
      setItemBases(bases)

      // Set default slot and category on initial load
      if (!selectedSlot && !selectedCategory) {
        const preferredSlots = ['body', 'helmet', 'gloves', 'boots', 'weapon', 'jewellery']
        let defaultSlot = ''
        let defaultCategory = ''

        // Find first available slot from preferred list
        for (const slot of preferredSlots) {
          if (bases[slot] && bases[slot].length > 0) {
            defaultSlot = slot
            // For body armor, prefer int_armour if available
            if (slot === 'body' && bases[slot].includes('int_armour')) {
              defaultCategory = 'int_armour'
            } else {
              defaultCategory = bases[slot][0]
            }
            console.log('[ItemTab] Setting initial slot/category:', defaultSlot, defaultCategory)
            break
          }
        }

        if (defaultSlot && defaultCategory) {
          setSelectedSlot(defaultSlot)
          setSelectedCategory(defaultCategory)
        }
      }
    } catch (err) {
      console.error('[ItemTab] Failed to load item bases:', err)
    }
  }

  const handleBaseSelection = async () => {
    console.log('[ItemTab] handleBaseSelection called with:', selectedBase)
    if (!selectedBase) return

    const baseData = availableBases.find(base => base.name === selectedBase)
    if (!baseData) {
      console.log('[ItemTab] Base data not found for:', selectedBase)
      return
    }

    try {
      // Calculate initial stats with quality (no mods yet)
      // Keys match pob-data source of truth: Armour, Evasion, EnergyShield
      const initialStats = { ...baseData.base_stats }
      for (const [stat, value] of Object.entries(initialStats)) {
        if (['Armour', 'Evasion', 'EnergyShield'].includes(stat)) {
          initialStats[stat] = Math.floor(value * 1.2) // 20% quality
        }
      }

      const newItem: CraftableItem = {
        base_name: selectedBase,
        base_category: selectedCategory,
        slot: selectedSlot,
        rarity: 'Normal' as ItemRarity,
        item_level: selectedItemLevel,
        quality: 20,
        implicit_mods: [],
        prefix_mods: [],
        suffix_mods: [],
        unrevealed_mods: [],
        socketed_runes: [],
        corrupted: false,
        base_stats: baseData.base_stats,
        calculated_stats: initialStats,
      }

      console.log('[ItemTab] ✓ Item created successfully:', newItem)
      setItem(newItem)
      onHistoryReset()
      setMessage(`Selected base: ${selectedBase} (ilvl ${selectedItemLevel})`)
      onItemCreated?.()
    } catch (err) {
      console.error('Failed to create item from base:', err)
      setMessage('Failed to create item from base')
    }
  }

  const handlePasteItem = async () => {
    if (!itemPasteText.trim()) {
      setPasteMessage('Please paste an item first')
      return
    }

    try {
      const result = await craftingApi.parseItem(itemPasteText)
      setItem(result.item)
      onHistoryReset()

      // Show warnings if any mods failed to match
      if (result.warnings && result.warnings.length > 0) {
        setPasteMessage(`⚠️ Item imported with ${result.warnings.length} warning(s): ${result.warnings.join('; ')}`)
      } else {
        setPasteMessage('Item parsed successfully!')
      }
      onItemCreated?.()
    } catch (err: any) {
      setPasteMessage(err.message || 'Failed to parse item')
    }
  }

  return (
    <div className="tab-content">
      <div className="mode-selector">
        <button
          className={`mode-button ${mode === 'paste' ? 'active' : ''}`}
          onClick={() => setMode('paste')}
        >
          Paste Item (Ctrl+V)
        </button>
        <button
          className={`mode-button ${mode === 'base' ? 'active' : ''}`}
          onClick={() => setMode('base')}
        >
          Select Base
        </button>
      </div>

      {mode === 'paste' ? (
        <div className="paste-mode">
          <div className="item-paste-section">
            <div className="paste-header" onClick={() => setPasteExpanded(!pasteExpanded)}>
              <h3>📋 Paste Item Data</h3>
            </div>
            {pasteExpanded && (
              <div className="paste-content">
                <div className="paste-instructions">
                  Copy an item from Path of Exile 2 (Ctrl+C in-game) and paste it here:
                </div>
                <textarea
                  className="item-paste-textarea"
                  value={itemPasteText}
                  onChange={(e) => setItemPasteText(e.target.value)}
                  placeholder="Paste item data here..."
                />
                <div className="paste-actions">
                  <button
                    className="paste-button"
                    onClick={handlePasteItem}
                    disabled={!itemPasteText.trim()}
                  >
                    Parse Item
                  </button>
                  <button
                    className="clear-button"
                    onClick={() => setItemPasteText('')}
                  >
                    Clear
                  </button>
                </div>
                {pasteMessage && (
                  <div className={`paste-message ${
                    pasteMessage.includes('successfully') ? 'success' :
                    pasteMessage.includes('warning') ? 'warning' : 'error'
                  }`}>
                    {pasteMessage}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="base-mode">
          <div className="item-base-selector">
            <h3>🛠️ Create New Item</h3>
            <div className="base-selector-row">
              <div className="slot-selector">
                <label>Slot:</label>
                <select
                  value={selectedSlot}
                  onChange={(e) => setSelectedSlot(e.target.value)}
                >
                  {Object.keys(itemBases).map(slot => (
                    <option key={slot} value={slot}>{slot.replace('_', ' ')}</option>
                  ))}
                </select>
              </div>

              <div className="base-selector">
                <label>Category:</label>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                >
                  {selectedSlot && itemBases[selectedSlot] && Array.isArray(itemBases[selectedSlot]) ?
                    itemBases[selectedSlot].map(category => (
                      <option key={category} value={category}>{category.replace('_', ' ')}</option>
                    )) : []
                  }
                </select>
              </div>

              <div className="base-selector">
                <label>Base:</label>
                <select
                  value={selectedBase}
                  onChange={(e) => setSelectedBase(e.target.value)}
                >
                  {availableBases.map(base => (
                    <option key={base.name} value={base.name}>{base.name}</option>
                  ))}
                </select>
              </div>

              <div className="base-selector">
                <label>Item Level:</label>
                <input
                  type="number"
                  value={selectedItemLevel}
                  onChange={(e) => setSelectedItemLevel(Math.max(1, Math.min(100, parseInt(e.target.value) || 82)))}
                  min="1"
                  max="100"
                  style={{
                    padding: '0.5rem',
                    background: '#0a0a0a',
                    border: '2px solid #444',
                    borderRadius: '6px',
                    color: '#e0e0e0',
                    fontSize: '0.9rem',
                    width: '80px'
                  }}
                />
              </div>
            </div>

            <button className="paste-button" onClick={handleBaseSelection}>
              Create Item
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function HistoryTab({ history, itemHistory, onRevertToStep, onClearHistory, stepComments, onUpdateComment, baseStepIndex, onSetBaseStep, basePriceEstimate, onCheckBasePrice, basePriceLoading }: TabContentProps) {
  const [editingComment, setEditingComment] = useState<number | null>(null)
  const [commentText, setCommentText] = useState('')

  const getItemSummary = (item: CraftableItem): string => {
    const totalMods = (item.prefix_mods?.length || 0) + (item.suffix_mods?.length || 0)
    return `${item.base_name} (${totalMods} mods, iLvl ${item.item_level})`
  }

  const handleStartEdit = (idx: number) => {
    setEditingComment(idx)
    setCommentText(stepComments?.[idx] || '')
  }

  const handleSaveComment = (idx: number) => {
    if (onUpdateComment) {
      onUpdateComment(idx, commentText)
    }
    setEditingComment(null)
    setCommentText('')
  }

  const handleCancelEdit = () => {
    setEditingComment(null)
    setCommentText('')
  }

  const handleToggleBase = (idx: number) => {
    if (onSetBaseStep) {
      onSetBaseStep(baseStepIndex === idx ? null : idx)
    }
  }

  return (
    <div className="tab-content">
      <div className="history-section">
        <div className="section-header">
          <h3>Crafting History</h3>
          <button
            className="clear-button"
            onClick={onClearHistory}
            disabled={history.length === 0}
          >
            Clear History
          </button>
        </div>

        {history.length === 0 ? (
          <div className="empty-history">No crafting history yet</div>
        ) : (
          <div className="history-list">
            {history.map((step, idx) => (
              <div key={idx} className={`history-entry ${baseStepIndex === idx ? 'is-base' : ''}`}>
                <div className="history-number">{idx + 1}.</div>
                <div className="history-content">
                  <div className="history-text">
                    {step}
                    {baseStepIndex === idx && (
                      <span className="base-badge-group">
                        <span className="base-badge">Base</span>
                        {basePriceEstimate ? (
                          <span className="base-price">
                            ~{basePriceEstimate.exalted.toFixed(1)} ex
                            {basePriceEstimate.divine > 0 && ` / ${basePriceEstimate.divine.toFixed(1)} div`}
                          </span>
                        ) : (
                          <button
                            className="check-price-btn"
                            onClick={e => {
                              e.stopPropagation()
                              onCheckBasePrice?.()
                            }}
                            disabled={basePriceLoading}
                          >
                            {basePriceLoading ? '...' : 'Check Price'}
                          </button>
                        )}
                      </span>
                    )}
                    {itemHistory[idx] && (
                      <div className="history-item-summary">
                        {getItemSummary(itemHistory[idx])}
                      </div>
                    )}
                  </div>

                  {/* Comment display/edit */}
                  {editingComment === idx ? (
                    <div className="comment-edit">
                      <textarea
                        className="comment-input"
                        value={commentText}
                        onChange={e => setCommentText(e.target.value)}
                        placeholder="Add a note about this step..."
                        rows={2}
                        autoFocus
                      />
                      <div className="comment-actions">
                        <button className="comment-save" onClick={() => handleSaveComment(idx)}>Save</button>
                        <button className="comment-cancel" onClick={handleCancelEdit}>Cancel</button>
                      </div>
                    </div>
                  ) : (
                    <>
                      {stepComments?.[idx] && (
                        <div className="step-comment" onClick={() => handleStartEdit(idx)}>
                          <span className="comment-icon">📝</span>
                          {stepComments[idx]}
                        </div>
                      )}
                    </>
                  )}
                </div>

                <div className="history-actions">
                  <button
                    className={`base-button ${baseStepIndex === idx ? 'active' : ''}`}
                    onClick={() => handleToggleBase(idx)}
                    title={baseStepIndex === idx ? 'Unmark as base' : 'Mark as base item'}
                  >
                    🏷️
                  </button>
                  <button
                    className="comment-button"
                    onClick={() => handleStartEdit(idx)}
                    title="Add/edit comment"
                  >
                    💬
                  </button>
                  <button
                    className="revert-button"
                    onClick={() => onRevertToStep(idx)}
                    title="Revert to this step"
                  >
                    ↶
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function CurrencyTab({ currencySpent, exchangeRates, getCurrencyIconUrl }: TabContentProps) {
  const getTotalSpent = (): number => {
    return Object.values(currencySpent).reduce((sum, count) => sum + count, 0)
  }

  // Calculate total cost in exalted and divine
  const calculateCosts = () => {
    if (!exchangeRates) return null

    let totalExalted = 0
    const breakdown: Record<string, number> = {}

    for (const [currency, count] of Object.entries(currencySpent)) {
      // Normalize currency name to match API format
      // API stores by: normalized-id (e.g., "greater-essence-of-abrasion")
      // and also by lowercase display name (e.g., "greater essence of abrasion")
      const lowerCurrency = currency.toLowerCase()
      const dashName = lowerCurrency.replace(/ /g, '-')

      // For basic orbs, try without "Orb of" prefix
      const basicOrbName = lowerCurrency
        .replace(/^orb of /, '')
        .replace(/ orb$/, '')

      // Try to find matching rate using multiple strategies
      const rate = exchangeRates.rates[lowerCurrency]  // "greater essence of abrasion"
        || exchangeRates.rates[dashName]               // "greater-essence-of-abrasion"
        || exchangeRates.rates[basicOrbName]           // "exalted", "divine" etc
        || Object.values(exchangeRates.rates).find(r =>
            r.name.toLowerCase() === lowerCurrency
          )

      if (rate) {
        const exaltedValue = count * rate.exalted_value
        totalExalted += exaltedValue
        breakdown[currency] = exaltedValue
      }
    }

    // Calculate divine equivalent
    const divineRate = exchangeRates.rates['divine']
    const totalDivine = divineRate ? totalExalted / divineRate.exalted_value : 0

    return { totalExalted, totalDivine, breakdown, divineRate: divineRate?.exalted_value || 0 }
  }

  const costs = calculateCosts()

  // Format cost dynamically - show exalted until >= 1 divine, then show divine
  const formatDynamicCost = () => {
    if (!costs) return null

    // If we have >= 1 divine worth, show in divines
    if (costs.totalDivine >= 1) {
      return {
        value: costs.totalDivine.toFixed(2),
        unit: 'div',
        icon: 'https://www.poe2wiki.net/images/5/58/Divine_Orb_inventory_icon.png'
      }
    }
    // Otherwise show in exalted
    return {
      value: costs.totalExalted.toFixed(2),
      unit: 'ex',
      icon: 'https://www.poe2wiki.net/images/2/26/Exalted_Orb_inventory_icon.png'
    }
  }

  const dynamicCost = formatDynamicCost()

  return (
    <div className="tab-content">
      <div className="currency-tracker">
        <h3>Currency Spent</h3>

        {Object.keys(currencySpent).length === 0 ? (
          <div className="empty-history">No currency spent yet</div>
        ) : (
          <>
            <div className="currency-spent-list">
              {Object.entries(currencySpent).map(([currency, count]) => (
                <div key={currency} className="currency-spent-item">
                  {getCurrencyIconUrl && (
                    <img
                      src={getCurrencyIconUrl(currency)}
                      alt={currency}
                      className="currency-spent-icon"
                    />
                  )}
                  <span className="currency-spent-name">{currency}</span>
                  <span className="currency-spent-count">x{count}</span>
                </div>
              ))}
            </div>
            <div className="currency-total">
              <strong>Total: {getTotalSpent()} currencies used</strong>
            </div>

            {/* Market Value Section */}
            {dynamicCost && exchangeRates && (
              <div className="currency-value-section">
                <h4>Estimated Value</h4>
                <div className="currency-value-display">
                  <div className="value-row primary dynamic-cost">
                    <img
                      src={dynamicCost.icon}
                      alt={dynamicCost.unit}
                      className="cost-currency-icon"
                    />
                    <span className="value-amount">{dynamicCost.value} {dynamicCost.unit}</span>
                  </div>
                  {/* Show secondary currency for reference */}
                  <div className="value-row secondary">
                    {costs && costs.totalDivine >= 1 ? (
                      <span className="secondary-value">({costs.totalExalted.toFixed(0)} ex)</span>
                    ) : costs && costs.divineRate > 0 ? (
                      <span className="secondary-value">({costs.totalDivine.toFixed(4)} div)</span>
                    ) : null}
                  </div>
                </div>
                <div className="market-source">
                  <span className="source-label">League: {exchangeRates.league}</span>
                </div>
              </div>
            )}

            {!exchangeRates && (
              <div className="currency-value-section loading">
                <span className="loading-text">Loading market data...</span>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

function GridCraftingSimulator() {
  const location = useLocation()

  const [item, setItem] = useState<CraftableItem>({
    base_name: "Vile Robe",
    base_category: 'int_armour',
    slot: 'body',
    rarity: 'Normal' as ItemRarity,
    item_level: 65,
    quality: 20,
    implicit_mods: [],
    prefix_mods: [],
    suffix_mods: [],
    unrevealed_mods: [],
    socketed_runes: [],
    corrupted: false,
    base_stats: {},
    calculated_stats: {},
  })

  const [categorizedCurrencies, setCategorizedCurrencies] = useState<{
    orbs: { implemented: string[], disabled: string[] }
    essences: { implemented: string[], disabled: string[] }
    bones: { implemented: string[], disabled: string[] }
    catalysts: { implemented: string[], disabled: string[] }
    omens: string[]
    total: number
    implemented_count: number
    disabled_count: number
  }>({
    orbs: { implemented: [], disabled: [] },
    essences: { implemented: [], disabled: [] },
    bones: { implemented: [], disabled: [] },
    catalysts: { implemented: [], disabled: [] },
    omens: [],
    total: 0,
    implemented_count: 0,
    disabled_count: 0
  })

  const [availableCurrencies, setAvailableCurrencies] = useState<string[]>([])
  // const [selectedEssence] = useState<string>('') // Unused for now
  const [selectedOmens, setSelectedOmens] = useState<string[]>([])
  const [availableOmens, setAvailableOmens] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string>('')
  const [history, setHistory] = useState<string[]>([])
  const [itemHistory, setItemHistory] = useState<CraftableItem[]>([])
  const [currencySpent, setCurrencySpent] = useState<Record<string, number>>({})
  const [exchangeRates, setExchangeRates] = useState<ExchangeRates | null>(null)
  const [itemPrice, setItemPrice] = useState<ItemPriceEstimate | null>(null)
  const [priceModalOpen, setPriceModalOpen] = useState(false)
  // Track which mods are included in price search (by index and type)
  const [priceSearchMods, setPriceSearchMods] = useState<Set<string>>(new Set())

  // Price filter states (controlled by parent for mod display interactivity)
  const [priceRarityEnabled, setPriceRarityEnabled] = useState(true)
  const [priceIlvlEnabled, setPriceIlvlEnabled] = useState(false)
  const [priceModMinValues, setPriceModMinValues] = useState<Record<string, number>>({})
  const [usePseudoStats, setUsePseudoStats] = useState<Record<string, boolean>>({})
  const [enabledHiddenMods, setEnabledHiddenMods] = useState<Set<string>>(new Set())
  const [pseudoStatsExpanded, setPseudoStatsExpanded] = useState(false)
  const [filtersChanged, setFiltersChanged] = useState(false)

  // Ref to call price check from mini buttons
  const priceFlyoutRef = useRef<{ handlePriceCheck: (useFilters?: boolean) => void; priceCheckLoading: boolean } | null>(null)

  // Redo stacks for Ctrl+R and Ctrl+Y
  const [redoItemStack, setRedoItemStack] = useState<CraftableItem[]>([])
  const [redoHistoryStack, setRedoHistoryStack] = useState<string[]>([])
  const [redoCurrencyStack, setRedoCurrencyStack] = useState<string[]>([])
  const [redoOmensStack, setRedoOmensStack] = useState<string[][]>([])

  // Track action details for each history step (for Ctrl+Y)
  const [actionHistory, setActionHistory] = useState<Array<{currency: string, omens: string[]} | null>>([])

  // Track currency spent at each history step (for undo/redo)
  const [currencySpentHistory, setCurrencySpentHistory] = useState<Array<Record<string, number>>>([])
  const [redoCurrencySpentStack, setRedoCurrencySpentStack] = useState<Array<Record<string, number>>>([])

  // Step comments and base step tracking
  const [stepComments, setStepComments] = useState<Record<number, string>>({})
  const [baseStepIndex, setBaseStepIndex] = useState<number | undefined>(undefined)
  const [basePriceEstimate, setBasePriceEstimate] = useState<{ exalted: number; divine: number } | null>(null)
  const [basePriceLoading, setBasePriceLoading] = useState(false)

  const [availableMods, setAvailableMods] = useState<{
    prefixes: ItemModifier[]
    suffixes: ItemModifier[]
    essence_prefixes: ItemModifier[]
    essence_suffixes: ItemModifier[]
    desecrated_prefixes: ItemModifier[]
    desecrated_suffixes: ItemModifier[]
    essence_guarantees: Record<string, Array<{
      essence_name: string
      essence_tier: string
      item_type: string
      applicable_items: string[]
    }>>
  }>({ prefixes: [], suffixes: [], essence_prefixes: [], essence_suffixes: [], desecrated_prefixes: [], desecrated_suffixes: [], essence_guarantees: {} })

  // Calculate total weights for probability display
  const totalWeights = useMemo(() => {
    const calcTotal = (mods: ItemModifier[]) =>
      mods.reduce((sum, mod) => sum + (mod.weight || 0), 0)

    return {
      prefix: calcTotal(availableMods.prefixes),
      suffix: calcTotal(availableMods.suffixes),
      // No weights for essence mods - they're guaranteed outcomes
      desecrated_prefix: calcTotal(availableMods.desecrated_prefixes),
      desecrated_suffix: calcTotal(availableMods.desecrated_suffixes),
    }
  }, [availableMods])

  const [exclusionGroups, setExclusionGroups] = useState<Array<{
    id: string
    description: string
    patterns: string[]
    applicable_items: string[]
    tags?: string
  }>>([])

  // Hidden tags config (loaded from API)
  const [hiddenTagsConfig, setHiddenTagsConfig] = useState<HiddenTagsConfig>({
    hidden_tags: [],
    hidden_patterns: []
  })

  const [modPoolFilter, setModPoolFilter] = useState<{
    search: string
    tags: string[]
    modType: 'all' | 'prefix' | 'suffix'
  }>({ search: '', tags: [], modType: 'all' })

  const [activeTagFilters, setActiveTagFilters] = useState<Set<string>>(new Set())
  const [expandedModGroups, setExpandedModGroups] = useState<Set<string>>(new Set())
  const [activeTab, setActiveTab] = useState<'item' | 'history' | 'currency'>('item')
  const [searchQuery, setSearchQuery] = useState<string>('')

  // Currency tooltip cache for search functionality
  const [currencyTooltipCache, setCurrencyTooltipCache] = useState<Record<string, {
    name: string
    description: string
    mechanics?: string
  }>>({})

  // Panel collapse state
  const [leftPanelCollapsed, setLeftPanelCollapsed] = useState(false)
  const [rightPanelCollapsed, setRightPanelCollapsed] = useState(false)

  // Item creation state - track if user has created/selected an item
  const [itemCreated, setItemCreated] = useState(false)

  // Drag and drop state
  const [draggedMod, setDraggedMod] = useState<ItemModifier | null>(null)
  const [draggedCurrency, setDraggedCurrency] = useState<string | null>(null)

  // Reveal modal state
  const [revealModalOpen, setRevealModalOpen] = useState(false)
  const [revealingModId, setRevealingModId] = useState<string | null>(null)

  // Save/Load craft modal state
  const [saveModalOpen, setSaveModalOpen] = useState(false)
  const [loadModalOpen, setLoadModalOpen] = useState(false)
  const [revealChoices, setRevealChoices] = useState<ItemModifier[]>([])
  const [rerollUsed, setRerollUsed] = useState(false)

  // Global paste modal state
  const [pastePreviewOpen, setPastePreviewOpen] = useState(false)
  const [pastedItemText, setPastedItemText] = useState('')
  const [pastedItemPreview, setPastedItemPreview] = useState<CraftableItem | null>(null)
  const [pasteError, setPasteError] = useState('')
  const [pasteWarnings, setPasteWarnings] = useState<string[]>([])

  // Track the original import format for copying
  const [importFormat, setImportFormat] = useState<'detailed' | 'simple'>('simple')

  function handleItemCreated() {
    setItemCreated(true)
  }

  function handleResetToCreate() {
    setItemCreated(false)
    handleHistoryReset()
    setMessage('Ready to create new item')
  }

  // Callback to update step comment
  const handleUpdateComment = useCallback((stepIndex: number, comment: string) => {
    setStepComments(prev => {
      if (comment.trim()) {
        return { ...prev, [stepIndex]: comment }
      } else {
        const { [stepIndex]: removed, ...rest } = prev
        return rest
      }
    })
  }, [])

  // Callback to set base step
  const handleSetBaseStep = useCallback((stepIndex: number | null) => {
    setBaseStepIndex(stepIndex === null ? undefined : stepIndex)
    setBasePriceEstimate(null)  // Clear price when base step changes
  }, [])

  // Check price for base step item
  const handleCheckBasePrice = useCallback(async () => {
    if (baseStepIndex === undefined || !itemHistory[baseStepIndex]) return
    if (basePriceLoading) return

    const baseItem = itemHistory[baseStepIndex]
    if (baseItem.prefix_mods.length === 0 && baseItem.suffix_mods.length === 0) {
      setMessage('Base item has no mods to price')
      return
    }

    setBasePriceLoading(true)
    try {
      const estimate = await marketApi.priceItem(baseItem)
      if (estimate.estimate_exalted !== undefined) {
        setBasePriceEstimate({
          exalted: estimate.estimate_exalted,
          divine: estimate.estimate_divine || 0,
        })
      } else {
        setMessage('No price estimate available')
      }
    } catch (err) {
      console.error('Failed to check base price:', err)
      setMessage('Failed to check price')
    } finally {
      setBasePriceLoading(false)
    }
  }, [baseStepIndex, itemHistory, basePriceLoading, setMessage])

  // Tab content props
  const tabContentProps: TabContentProps = {
    item,
    setItem,
    history,
    itemHistory,
    currencySpent,
    exchangeRates,
    onRevertToStep: handleRevertToStep,
    onClearHistory: handleClearHistory,
    onHistoryReset: handleHistoryReset,
    setMessage,
    onItemCreated: handleItemCreated,
    stepComments,
    onUpdateComment: handleUpdateComment,
    baseStepIndex,
    onSetBaseStep: handleSetBaseStep,
    basePriceEstimate,
    onCheckBasePrice: handleCheckBasePrice,
    basePriceLoading,
    // Note: getCurrencyIconUrl is passed directly to CurrencyTab in JSX
  }

  function handleRevertToStep(stepIndex: number) {
    if (stepIndex < itemHistory.length) {
      setItem(itemHistory[stepIndex])
      setItemHistory(itemHistory.slice(0, stepIndex + 1))
      setHistory(history.slice(0, stepIndex + 1))
      setActionHistory(actionHistory.slice(0, stepIndex + 1))
      setCurrencySpentHistory(currencySpentHistory.slice(0, stepIndex + 1))
      // Restore currency spent to the state at that step
      const revertedCurrencySpent = stepIndex < currencySpentHistory.length
        ? currencySpentHistory[stepIndex]
        : {}
      setCurrencySpent(revertedCurrencySpent)
      // Clear redo stacks when jumping to a specific step
      setRedoItemStack([])
      setRedoHistoryStack([])
      setRedoCurrencyStack([])
      setRedoOmensStack([])
      setRedoCurrencySpentStack([])
      setMessage(`Reverted to step ${stepIndex + 1}`)
    }
  }

  function handleClearHistory() {
    setHistory([])
    setItemHistory([])
    setActionHistory([])
    setCurrencySpent({})
    setCurrencySpentHistory([])
    setRedoItemStack([])
    setRedoHistoryStack([])
    setRedoCurrencyStack([])
    setRedoOmensStack([])
    setRedoCurrencySpentStack([])
    setMessage('History cleared')
  }

  function handleHistoryReset() {
    setHistory([])
    setItemHistory([])
    setActionHistory([])
    setCurrencySpent({})
    setCurrencySpentHistory([])
    setRedoItemStack([])
    setRedoHistoryStack([])
    setRedoCurrencyStack([])
    setRedoOmensStack([])
    setRedoCurrencySpentStack([])
  }

  // Global paste handler
  const handleGlobalPaste = async (text: string) => {
    // Check if it looks like an item (must contain "Item Class:")
    if (!text.includes('Item Class:')) {
      return // Not an item, ignore
    }

    setPastedItemText(text)
    setPasteError('')
    setPasteWarnings([])
    setPastedItemPreview(null)

    // Detect format: detailed if it has "{ Prefix Modifier" or "{ Suffix Modifier"
    const isDetailed = text.includes('{ Prefix Modifier') || text.includes('{ Suffix Modifier') || text.includes('{ Implicit Modifier')
    setImportFormat(isDetailed ? 'detailed' : 'simple')

    try {
      const result = await craftingApi.parseItem(text)
      setPastedItemPreview(result.item)
      setPasteWarnings(result.warnings || [])
      setPastePreviewOpen(true)
    } catch (err: any) {
      setPasteError(err.message || 'Failed to parse item')
      setPastePreviewOpen(true)
    }
  }

  const handleImportPastedItem = () => {
    if (pastedItemPreview) {
      setItem(pastedItemPreview)
      handleHistoryReset()
      setItemCreated(true)
      setMessage('Item imported from clipboard')
      setPastePreviewOpen(false)
    }
  }

  const handleCancelPaste = () => {
    setPastePreviewOpen(false)
    setPastedItemText('')
    setPastedItemPreview(null)
    setPasteError('')
    setPasteWarnings([])
  }

  // Export item to clipboard with specified format
  const handleCopyItem = (format: 'simple' | 'detailed') => {
    const itemText = exportItemToText(item, format)
    navigator.clipboard.writeText(itemText).then(() => {
      setMessage(`Item copied to clipboard (${format} format)!`)
    }).catch(() => {
      setMessage('Failed to copy item to clipboard')
    })
  }

  // Filter out internal/system tags that shouldn't be displayed to users
  // Uses hidden_tags.json config loaded from API
  const filterInternalTags = useCallback((tags: string[] | undefined): string[] => {
    if (!tags || tags.length === 0) return []

    const shouldHideTag = (tag: string): boolean => {
      const tagLower = tag.toLowerCase()

      // Check exact matches from config
      if (hiddenTagsConfig.hidden_tags.includes(tagLower)) return true

      // Check wildcard patterns from config
      for (const pattern of hiddenTagsConfig.hidden_patterns) {
        // Convert glob pattern to regex: * -> .*, ? -> .
        const regexPattern = pattern
          .replace(/[.+^${}()|[\]\\]/g, '\\$&')  // Escape special regex chars
          .replace(/\*/g, '.*')
          .replace(/\?/g, '.')
        if (new RegExp(`^${regexPattern}$`, 'i').test(tagLower)) {
          return true
        }
      }

      return false
    }

    return tags.filter(tag => !shouldHideTag(tag))
  }, [hiddenTagsConfig])

  // Convert item to PoE2 text format (POB-compatible)
  const exportItemToText = (item: CraftableItem, format: 'detailed' | 'simple'): string => {
    const lines: string[] = []
    const separator = '--------'

    // Helper to get POB Item Class name from slot
    const getItemClass = (): string => {
      const slot = item.slot || ''
      const category = item.base_category

      // Armor slots
      if (slot === 'helmet') return 'Helmets'
      if (slot === 'body' || slot === 'body_armour') return 'Body Armours'
      if (slot === 'gloves') return 'Gloves'
      if (slot === 'boots') return 'Boots'

      // Weapons - need to determine 1h vs 2h
      if (slot === 'weapon - 1 hand' || slot === 'weapons - 1 hand') {
        const weaponClassMap: Record<string, string> = {
          'sword': 'One Hand Swords',
          'axe': 'One Hand Axes',
          'mace': 'One Hand Maces',
          'dagger': 'Daggers',
          'claw': 'Claws',
          'wand': 'Wands',
          'sceptre': 'Sceptres',
          'flail': 'Flails',
        }
        return weaponClassMap[category] || 'One Hand Weapons'
      }
      if (slot === 'weapon - 2 hand' || slot === 'weapons - 2 hand') {
        const weaponClassMap: Record<string, string> = {
          'sword': 'Two Hand Swords',
          'axe': 'Two Hand Axes',
          'mace': 'Two Hand Maces',
          'bow': 'Bows',
          'crossbow': 'Crossbows',
          'staff': 'Staves',
          'warstaff': 'Warstaves',
          'spear': 'Spears',
        }
        return weaponClassMap[category] || 'Two Hand Weapons'
      }

      // Offhand
      if (slot === 'offhand') {
        if (category === 'quiver') return 'Quivers'
        if (category === 'focus') return 'Foci'
        if (category.includes('shield')) return 'Shields'
        return 'Shields'
      }

      // Jewelry
      if (slot === 'jewellery' || category === 'amulet') return 'Amulets'
      if (category === 'ring') return 'Rings'
      if (category === 'belt') return 'Belts'

      // Fallback based on category patterns
      if (category.includes('armour')) return 'Body Armours'
      if (category.includes('shield')) return 'Shields'

      return 'Items'
    }

    // Generate a random rare name (simple version)
    const generateRareName = (): string => {
      const prefixes = ['Grim', 'Dusk', 'Storm', 'Doom', 'Rune', 'Soul', 'Blight', 'Havoc', 'Woe', 'Rage']
      const suffixes = ['Dome', 'Mark', 'Bane', 'Keep', 'Ward', 'Roar', 'Veil', 'Song', 'Bite', 'Edge']
      const prefix = prefixes[Math.floor(Math.random() * prefixes.length)]
      const suffix = suffixes[Math.floor(Math.random() * suffixes.length)]
      return `${prefix} ${suffix}`
    }

    // Item Class header
    lines.push(`Item Class: ${getItemClass()}`)
    lines.push(`Rarity: ${item.rarity}`)

    // Item name(s) - Rare items have generated name + base name
    if (item.rarity === 'Rare') {
      lines.push(generateRareName())
    }
    lines.push(item.base_name)

    // Quality and defense stats section
    lines.push(separator)
    const hasQuality = item.quality > 0
    const stats = item.calculated_stats || {}
    const baseStats = item.base_stats || {}

    if (hasQuality) {
      lines.push(`Quality: +${item.quality}% (augmented)`)
    }

    // Defense stats (Armour, Evasion, Energy Shield)
    if (stats.Armour != null && stats.Armour > 0) {
      const isAugmented = baseStats.Armour != null && stats.Armour > baseStats.Armour
      lines.push(`Armour: ${Math.floor(stats.Armour)}${isAugmented ? ' (augmented)' : ''}`)
    }
    if (stats.Evasion != null && stats.Evasion > 0) {
      const isAugmented = baseStats.Evasion != null && stats.Evasion > baseStats.Evasion
      lines.push(`Evasion Rating: ${Math.floor(stats.Evasion)}${isAugmented ? ' (augmented)' : ''}`)
    }
    if (stats.EnergyShield != null && stats.EnergyShield > 0) {
      const isAugmented = baseStats.EnergyShield != null && stats.EnergyShield > baseStats.EnergyShield
      lines.push(`Energy Shield: ${Math.floor(stats.EnergyShield)}${isAugmented ? ' (augmented)' : ''}`)
    }

    // Weapon stats
    if (stats.PhysicalMin != null && stats.PhysicalMax != null) {
      lines.push(`Physical Damage: ${Math.floor(stats.PhysicalMin)}-${Math.floor(stats.PhysicalMax)}`)
    }
    if (stats.CritChance != null) {
      lines.push(`Critical Hit Chance: ${stats.CritChance.toFixed(2)}%`)
    }
    if (stats.AttacksPerSecond != null) {
      lines.push(`Attacks per Second: ${stats.AttacksPerSecond.toFixed(2)}`)
    }

    // Requirements section (simplified - would need base data for accurate reqs)
    lines.push(separator)
    lines.push(`Requires: Level ${Math.max(1, item.item_level - 10)}`)

    // Sockets section
    if (item.socketed_runes && item.socketed_runes.length > 0) {
      lines.push(separator)
      lines.push(`Sockets: ${item.socketed_runes.map(() => 'S').join(' ')}`)
    }

    // Item Level
    lines.push(separator)
    lines.push(`Item Level: ${item.item_level}`)

    // Implicit mods section (no annotation in POB format)
    if (item.implicit_mods && item.implicit_mods.length > 0) {
      lines.push(separator)
      if (format === 'detailed') {
        lines.push('{ Implicit Modifier }')
      }
      item.implicit_mods.forEach(mod => {
        const modText = renderModifierAsText(mod, format === 'detailed')
        lines.push(modText)
      })
    }

    // Rune mods section (with (rune) annotation)
    if (item.socketed_runes && item.socketed_runes.length > 0) {
      lines.push(separator)
      item.socketed_runes.forEach(rune => {
        if (format === 'detailed') {
          lines.push(`{ Rune "${rune.name}" }`)
        }
        rune.mods.forEach(modText => {
          lines.push(`${modText} (rune)`)
        })
        if (rune.bonded_mods) {
          rune.bonded_mods.forEach(modText => {
            lines.push(`${modText} (bonded)`)
          })
        }
      })
    }

    // Explicit mods section
    lines.push(separator)
    const allMods: { mod: ItemModifier; type: 'prefix' | 'suffix' }[] = [
      ...item.prefix_mods.map(m => ({ mod: m, type: 'prefix' as const })),
      ...item.suffix_mods.map(m => ({ mod: m, type: 'suffix' as const }))
    ]

    allMods.forEach(({ mod, type }) => {
      if (format === 'detailed') {
        const modType = type === 'prefix' ? 'Prefix' : 'Suffix'
        const filteredTags = filterInternalTags(mod.tags)
        const tags = filteredTags.join(', ')
        lines.push(`{ ${modType} Modifier "${mod.name}" (Tier: ${mod.tier})${tags ? ' — ' + tags.split(',').map(t => t.trim().charAt(0).toUpperCase() + t.trim().slice(1)).join(', ') : ''} }`)
      }

      const modText = renderModifierAsText(mod, format === 'detailed')

      // Add annotations for special mod types
      if (mod.is_desecrated) {
        lines.push(`${modText} (desecrated)`)
      } else if (mod.is_fractured) {
        lines.push(`${modText} (fractured)`)
      } else {
        lines.push(modText)
      }
    })

    return lines.join('\n')
  }

  // Render modifier as text (similar to renderModifier but for plain text)
  const renderModifierAsText = (mod: ItemModifier, includeRange: boolean = false): string => {
    let text = mod.stat_text

    if (mod.current_values && mod.current_values.length > 0) {
      // Hybrid mod with multiple values
      mod.current_values.forEach((value, idx) => {
        const valueStr = Math.floor(value).toString()
        const rangeStr = includeRange && mod.stat_ranges && mod.stat_ranges[idx]
          ? `(${mod.stat_ranges[idx].min}-${mod.stat_ranges[idx].max})`
          : ''
        text = text.replace('#', valueStr + rangeStr)
      })
    } else if (mod.current_value !== undefined && mod.current_value !== null) {
      // Single value mod
      const valueStr = Math.floor(mod.current_value).toString()
      const rangeStr = includeRange && mod.stat_ranges && mod.stat_ranges.length > 0
        ? `(${mod.stat_ranges[0].min}-${mod.stat_ranges[0].max})`
        : ''
      text = text.replace('#', valueStr + rangeStr)
    } else {
      // No value, use range
      text = text.replace('#', `(${mod.stat_min}-${mod.stat_max})`)
    }

    return text
  }

  // Add global paste listener
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      // Don't intercept paste if user is typing in an input/textarea
      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
        return
      }

      const text = e.clipboardData?.getData('text')
      if (text) {
        handleGlobalPaste(text)
      }
    }

    document.addEventListener('paste', handlePaste)
    return () => document.removeEventListener('paste', handlePaste)
  }, [])

  // Fetch exchange rates on mount
  useEffect(() => {
    const fetchExchangeRates = async () => {
      try {
        const rates = await marketApi.getExchangeRates()
        setExchangeRates(rates)
      } catch (error) {
        console.error('Failed to fetch exchange rates:', error)
      }
    }
    fetchExchangeRates()
  }, [])

  // Clear price estimate when item changes and reset mod selection
  useEffect(() => {
    setItemPrice(null)
    // Reset pseudo stats state for fresh calculation
    setUsePseudoStats({})
    setEnabledHiddenMods(new Set())
    setPseudoStatsExpanded(false)
    // Initialize all mods as selected for price search
    const allMods = new Set<string>()
    const modMinValues: Record<string, number> = {}

    // Helper to get mod value - uses average for 2-value mods (like damage ranges)
    const getModValue = (mod: ItemModifier): number => {
      if (mod.current_values && mod.current_values.length === 2) {
        // For damage mods "Adds X to Y", use average
        return (mod.current_values[0] + mod.current_values[1]) / 2
      }
      return mod.current_values?.[0] ?? mod.current_value ?? mod.stat_min ?? 0
    }

    item.prefix_mods.forEach((mod, idx) => {
      allMods.add(`prefix-${idx}`)
      const value = getModValue(mod)
      modMinValues[`prefix-${idx}`] = Math.floor(value * 0.8) // Default to 80% of rolled value
    })
    item.suffix_mods.forEach((mod, idx) => {
      allMods.add(`suffix-${idx}`)
      const value = getModValue(mod)
      modMinValues[`suffix-${idx}`] = Math.floor(value * 0.8)
    })
    setPriceSearchMods(allMods)
    setPriceModMinValues(modMinValues)
  }, [item])


  // Toggle a mod's inclusion in price search
  const togglePriceSearchMod = (modType: 'prefix' | 'suffix', idx: number) => {
    const key = `${modType}-${idx}`
    setPriceSearchMods(prev => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }

  // Check if a mod is selected for price search
  const isModSelectedForPriceSearch = (modType: 'prefix' | 'suffix', idx: number) => {
    return priceSearchMods.has(`${modType}-${idx}`)
  }

  // Open price modal
  const openPriceModal = () => {
    setPriceModalOpen(true)
  }

  // Format price in best currency (exalted -> divine -> mirror)
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


  // Drag and drop handlers
  function handleDragStart(mod: ItemModifier, modType: 'prefix' | 'suffix') {
    setDraggedMod({ ...mod, mod_type: modType })
  }

  function handleDragEnd() {
    setDraggedMod(null)
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()

    // Handle currency drop
    if (draggedCurrency) {
      handleCraft(draggedCurrency)
      setDraggedCurrency(null)
      return
    }

    // Handle mod drop
    if (!draggedMod) return

    const modType = draggedMod.mod_type as 'prefix' | 'suffix'
    const currentMods = modType === 'prefix' ? item.prefix_mods : item.suffix_mods

    // Check if we can add more mods
    if (currentMods.length >= 3) {
      setMessage(`Cannot add more than 3 ${modType} mods`)
      setDraggedMod(null)
      return
    }

    // Check if this mod group already exists
    const existingModGroups = [...item.prefix_mods, ...item.suffix_mods].map(m => m.mod_group)
    if (draggedMod.mod_group && existingModGroups.includes(draggedMod.mod_group)) {
      setMessage(`Cannot add mod: ${draggedMod.mod_group} already exists on item`)
      setDraggedMod(null)
      return
    }

    // Check for exclusion group conflicts
    // First, ensure existing mods have exclusion_group_id annotations
    const existingMods = [...item.prefix_mods, ...item.suffix_mods].map(mod => {
      if (mod.exclusion_group_id) return mod

      // Find which group this mod belongs to
      for (const group of exclusionGroups) {
        if (!ruleApplesToItem(group, item.base_category)) continue
        const matchesGroup = group.patterns.some(pattern =>
          patternMatchesMod(pattern, mod.stat_text)
        )
        if (matchesGroup) {
          return { ...mod, exclusion_group_id: group.id }
        }
      }
      return mod
    })

    // Check if dragged mod conflicts with any existing mod
    for (const existingMod of existingMods) {
      if (draggedMod.exclusion_group_id &&
          existingMod.exclusion_group_id &&
          draggedMod.exclusion_group_id === existingMod.exclusion_group_id) {
        const groupInfo = getModExclusionGroupInfo(draggedMod)
        setMessage(`Cannot add: conflicts with "${existingMod.stat_text}" (${groupInfo?.description || 'same exclusion group'})`)
        setDraggedMod(null)
        return
      }
    }

    // Add to history before making changes
    setHistory([...history, `Manually added ${draggedMod.name}`])
    setItemHistory([...itemHistory, item])
    setActionHistory([...actionHistory, null]) // Manual actions can't be retried
    setCurrencySpentHistory([...currencySpentHistory, currencySpent])

    // Clear redo stacks on new action
    setRedoItemStack([])
    setRedoHistoryStack([])
    setRedoCurrencyStack([])
    setRedoOmensStack([])
    setRedoCurrencySpentStack([])

    // Add the mod to the item - support hybrid mods
    const newItem = { ...item }

    // Roll values for hybrid modifiers (multiple stat ranges)
    let modWithValue: ItemModifier
    if (draggedMod.stat_ranges && draggedMod.stat_ranges.length > 0) {
      // Roll one value per stat range
      const rolledValues = draggedMod.stat_ranges.map(range =>
        Math.random() * (range.max - range.min) + range.min
      )

      // Format stat_text with rolled values instead of ranges
      let formattedStatText = draggedMod.stat_text
      for (const rolledValue of rolledValues) {
        // Replace first range pattern with the rolled value
        const valueStr = Number.isInteger(rolledValue) ? String(Math.round(rolledValue)) : rolledValue.toFixed(1)
        formattedStatText = formattedStatText.replace(/\(\d+(?:\.\d+)?-\d+(?:\.\d+)?\)/, valueStr)
      }

      modWithValue = {
        ...draggedMod,
        stat_text: formattedStatText,
        current_values: rolledValues,
        current_value: rolledValues[0] // Legacy compatibility
      }
    } else if (draggedMod.stat_min !== undefined && draggedMod.stat_max !== undefined) {
      // Legacy single value rolling
      const randomValue = Math.floor(Math.random() * (draggedMod.stat_max - draggedMod.stat_min + 1)) + draggedMod.stat_min

      // Format stat_text with rolled value
      const valueStr = String(randomValue)
      const formattedStatText = draggedMod.stat_text.replace(/\(\d+(?:\.\d+)?-\d+(?:\.\d+)?\)/g, valueStr)

      modWithValue = { ...draggedMod, stat_text: formattedStatText, current_value: randomValue }
    } else {
      // No ranges available, use mod as-is
      modWithValue = { ...draggedMod }
    }

    if (modType === 'prefix') {
      newItem.prefix_mods = [...newItem.prefix_mods, modWithValue]
    } else {
      newItem.suffix_mods = [...newItem.suffix_mods, modWithValue]
    }

    // Update rarity if needed
    const totalMods = newItem.prefix_mods.length + newItem.suffix_mods.length
    if (totalMods === 1 && newItem.rarity === 'Normal') {
      newItem.rarity = 'Magic'
    } else if (totalMods >= 2 && newItem.rarity !== 'Rare') {
      newItem.rarity = 'Rare'
    }

    setItem(newItem)
    setMessage(`Added ${draggedMod.name} to item`)
    setDraggedMod(null)
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault()
  }

  function handleRemoveMod(modIndex: number, modType: 'prefix' | 'suffix') {
    // Add to history before making changes
    const modName = modType === 'prefix' ? item.prefix_mods[modIndex].name : item.suffix_mods[modIndex].name
    setHistory([...history, `Manually removed ${modName}`])
    setItemHistory([...itemHistory, item])
    setActionHistory([...actionHistory, null]) // Manual actions can't be retried
    setCurrencySpentHistory([...currencySpentHistory, currencySpent])

    // Clear redo stacks on new action
    setRedoItemStack([])
    setRedoHistoryStack([])
    setRedoCurrencyStack([])
    setRedoOmensStack([])
    setRedoCurrencySpentStack([])

    const newItem = { ...item }
    if (modType === 'prefix') {
      newItem.prefix_mods = newItem.prefix_mods.filter((_, idx) => idx !== modIndex)
    } else {
      newItem.suffix_mods = newItem.suffix_mods.filter((_, idx) => idx !== modIndex)
    }

    // Update rarity if needed
    const totalMods = newItem.prefix_mods.length + newItem.suffix_mods.length
    if (totalMods === 0) {
      newItem.rarity = 'Normal'
    } else if (totalMods === 1) {
      newItem.rarity = 'Magic'
    }

    setItem(newItem)
    setMessage(`Removed ${modName} from item`)
  }

  async function handleClickUnrevealedMod(unrevealedId: string) {
    try {
      setLoading(true)
      console.log('[Reveal] Selected omens:', selectedOmens)
      const response = await fetch('http://localhost:8000/api/v1/crafting/reveal-modifier', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          unrevealed_id: unrevealedId,
          item: item,
          omen_names: selectedOmens
        })
      })

      if (!response.ok) {
        throw new Error('Failed to reveal modifier')
      }

      const data = await response.json()
      console.log('[Reveal] Received choices:', data.choices.map((c: any) => ({ name: c.name, tags: c.tags })))
      setRevealingModId(unrevealedId)
      setRevealChoices(data.choices)
      setRerollUsed(!data.has_abyssal_echoes) // If no Abyssal Echoes, mark as used
      setRevealModalOpen(true)
    } catch (error) {
      console.error('Error revealing modifier:', error)
      setMessage('Error revealing modifier')
    } finally {
      setLoading(false)
    }
  }

  function handleSelectRevealChoice(choice: ItemModifier) {
    if (!revealingModId) return

    // Add to history
    setHistory([...history, `Revealed desecrated modifier: ${choice.name}`])
    setItemHistory([...itemHistory, item])
    setActionHistory([...actionHistory, null]) // Manual actions can't be retried
    setCurrencySpentHistory([...currencySpentHistory, currencySpent])

    // Clear redo stacks on new action
    setRedoItemStack([])
    setRedoHistoryStack([])
    setRedoCurrencyStack([])
    setRedoOmensStack([])
    setRedoCurrencySpentStack([])

    // Remove unrevealed mod and replace the placeholder with chosen revealed mod
    const newItem = { ...item }
    newItem.unrevealed_mods = newItem.unrevealed_mods.filter(mod => mod.id !== revealingModId)

    // Replace the placeholder modifier with the chosen modifier
    if (choice.mod_type === 'prefix') {
      newItem.prefix_mods = newItem.prefix_mods.map(mod =>
        mod.unrevealed_id === revealingModId ? choice : mod
      )
    } else {
      newItem.suffix_mods = newItem.suffix_mods.map(mod =>
        mod.unrevealed_id === revealingModId ? choice : mod
      )
    }

    setItem(newItem)

    // Consume Omen of Abyssal Echoes if it was used
    const hasAbyssalEchoes = selectedOmens.some(omen => omen.includes('Abyssal Echoes'))
    if (hasAbyssalEchoes) {
      const newOmens = selectedOmens.filter(omen => !omen.includes('Abyssal Echoes'))
      setSelectedOmens(newOmens)
      setMessage(`Revealed: ${choice.name} (Omen of Abyssal Echoes consumed)`)
    } else {
      setMessage(`Revealed: ${choice.name}`)
    }

    // Close modal
    setRevealModalOpen(false)
    setRevealingModId(null)
    setRevealChoices([])
    setRerollUsed(false)
  }

  function handleCloseRevealModal() {
    setRevealModalOpen(false)
    setRevealingModId(null)
    setRevealChoices([])
    setRerollUsed(false)
  }

  async function handleRerollRevealChoices() {
    if (!revealingModId || rerollUsed) return

    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/api/v1/crafting/reveal-modifier', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          unrevealed_id: revealingModId,
          item: item,
          omen_names: selectedOmens
        })
      })

      if (!response.ok) {
        throw new Error('Failed to reroll modifier choices')
      }

      const data = await response.json()
      setRevealChoices(data.choices)
      setRerollUsed(true)
      setMessage('Rerolled modifier choices (Omen of Abyssal Echoes consumed)')
    } catch (error) {
      console.error('Error rerolling choices:', error)
      setMessage('Error rerolling choices')
    } finally {
      setLoading(false)
    }
  }

  // Load exclusion groups and hidden tags config once on mount
  useEffect(() => {
    loadExclusionGroups()
    loadHiddenTags()
  }, [])

  const loadHiddenTags = async () => {
    try {
      const config = await craftingApi.getHiddenTags()
      setHiddenTagsConfig(config)
    } catch (error) {
      console.error('Failed to load hidden tags config:', error)
    }
  }

  // Load available mods and currencies when item changes or exclusion groups change
  useEffect(() => {
    if (item.base_name && item.base_name !== "Int Armour Body Armour" && exclusionGroups.length > 0) {
      loadAvailableMods()
      loadCategorizedCurrencies()
      loadAvailableCurrencies()
    }
  }, [item, exclusionGroups])

  // Pre-fetch all currency tooltips for search functionality
  useEffect(() => {
    const fetchAllTooltips = async () => {
      // Collect all unique currency names
      const allCurrencyNames = new Set<string>()

      // Add all orbs
      categorizedCurrencies.orbs.implemented.forEach(name => allCurrencyNames.add(name))
      categorizedCurrencies.orbs.disabled.forEach(name => allCurrencyNames.add(name))

      // Add all essences
      categorizedCurrencies.essences.implemented.forEach(name => allCurrencyNames.add(name))
      categorizedCurrencies.essences.disabled.forEach(name => allCurrencyNames.add(name))

      // Add all bones
      categorizedCurrencies.bones.implemented.forEach(name => allCurrencyNames.add(name))
      categorizedCurrencies.bones.disabled.forEach(name => allCurrencyNames.add(name))

      // Add all catalysts
      categorizedCurrencies.catalysts.implemented.forEach(name => allCurrencyNames.add(name))
      categorizedCurrencies.catalysts.disabled.forEach(name => allCurrencyNames.add(name))

      // Add all omens
      categorizedCurrencies.omens.forEach(name => allCurrencyNames.add(name))

      // Fetch tooltips for all currencies
      const tooltipPromises = Array.from(allCurrencyNames).map(async (currencyName) => {
        try {
          const tooltip = await craftingApi.getCurrencyTooltip(currencyName)
          return { currencyName, tooltip }
        } catch (err) {
          console.warn(`Failed to fetch tooltip for ${currencyName}:`, err)
          return { currencyName, tooltip: { name: currencyName, description: '', mechanics: '' } }
        }
      })

      const results = await Promise.all(tooltipPromises)
      const cache: Record<string, { name: string; description: string; mechanics?: string }> = {}
      results.forEach(({ currencyName, tooltip }) => {
        cache[currencyName] = tooltip
      })
      setCurrencyTooltipCache(cache)
      console.log(`[GridCraftingSimulator] Loaded ${Object.keys(cache).length} currency tooltips for search`)
    }

    if (categorizedCurrencies.total > 0) {
      fetchAllTooltips()
    }
  }, [categorizedCurrencies])

  // Stats are calculated by the backend's StatCalculator - no need to recalculate locally
  // The backend returns calculated_stats with all stats including weapon DPS and defense stats

  const loadAvailableMods = async () => {
    try {
      const mods = await craftingApi.getAvailableMods(item)
      // Annotate mods with exclusion group IDs
      const annotatedMods = annotateModsWithGroups(mods)
      setAvailableMods(annotatedMods)
    } catch (err) {
      console.error('Failed to load available mods:', err)
    }
  }

  const loadExclusionGroups = async () => {
    try {
      const groups = await craftingApi.getExclusionGroups()
      setExclusionGroups(groups)
    } catch (err) {
      console.error('Failed to load exclusion groups:', err)
    }
  }

  // Pattern matching function (mirrors backend logic)
  const patternMatchesMod = (pattern: string, modStatText: string): boolean => {
    // Handle exact match for mods with placeholders (e.g., "+# to Level of all Melee Skills")
    if (pattern === modStatText) {
      return true
    }

    // Escape special regex characters except #
    let patternRegex = pattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

    // Replace # placeholders with regex for numbers OR the literal #
    // This handles both "+2 to Level..." and "+# to Level..."
    patternRegex = patternRegex.replace(/#/g, '(#|[\\d\\-\\(\\)]+)')

    // Add anchors to match full string
    patternRegex = `^${patternRegex}$`

    try {
      return new RegExp(patternRegex, 'i').test(modStatText)
    } catch (e) {
      console.warn(`Invalid regex pattern '${patternRegex}':`, e)
      return false
    }
  }

  // Check if rule applies to item category
  const ruleApplesToItem = (rule: { applicable_items: string[] }, itemCategory: string): boolean => {
    const applicableItems = rule.applicable_items || []

    // If no specific items listed, rule applies to all
    if (applicableItems.length === 0) return true

    const categoryNormalized = itemCategory.toLowerCase()

    for (const itemType of applicableItems) {
      const itemTypeNormalized = itemType.toLowerCase()

      // Direct match or partial match (e.g., "axe" matches "one_hand_axe")
      if (categoryNormalized === itemTypeNormalized || categoryNormalized.includes(itemTypeNormalized)) {
        return true
      }
    }

    return false
  }

  // Get exclusion group info for a mod
  const getModExclusionGroupInfo = (mod: ItemModifier) => {
    if (!mod.exclusion_group_id) return null

    const group = exclusionGroups.find(g => g.id === mod.exclusion_group_id)
    return group || null
  }

  // Annotate mods with exclusion group IDs
  const annotateModsWithGroups = (mods: typeof availableMods) => {
    const annotate = (modList: ItemModifier[]) => {
      return modList.map(mod => {
        // Find which exclusion groups this mod belongs to
        const groupIds: string[] = []

        for (const group of exclusionGroups) {
          // Check if group applies to this item type
          if (!ruleApplesToItem(group, item.base_category)) continue

          // Check if mod matches any pattern in this group
          const matchesGroup = group.patterns.some(pattern =>
            patternMatchesMod(pattern, mod.stat_text)
          )

          if (matchesGroup) {
            groupIds.push(group.id)
          }
        }

        // Return mod with exclusion_group_id if it belongs to any groups
        if (groupIds.length > 0) {
          return {
            ...mod,
            exclusion_group_id: groupIds[0] // Use first group for simplicity
          }
        }

        return mod
      })
    }

    return {
      prefixes: annotate(mods.prefixes),
      suffixes: annotate(mods.suffixes),
      essence_prefixes: annotate(mods.essence_prefixes),
      essence_suffixes: annotate(mods.essence_suffixes),
      desecrated_prefixes: annotate(mods.desecrated_prefixes),
      desecrated_suffixes: annotate(mods.desecrated_suffixes),
      essence_guarantees: mods.essence_guarantees || {},
    }
  }

  const loadCategorizedCurrencies = async () => {
    try {
      const currencies = await craftingApi.getCategorizedCurrencies()
      setCategorizedCurrencies({
        ...currencies,
        catalysts: currencies.catalysts || { implemented: [], disabled: [] }
      })
      setAvailableOmens(currencies.omens)
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
      setAvailableCurrencies([]) // Set to empty on error
    }
  }

  const handleCraft = async (currencyType: string) => {
    if (loading) return

    setLoading(true)
    setMessage('')

    // Store the current item state to compare later
    const initialItemState = JSON.stringify(item)

    try {
      // Debug logging
      const initialModCount = item.prefix_mods.length + item.suffix_mods.length
      console.log(`[DEBUG] Crafting ${currencyType} on item with ${initialModCount} mods (${item.prefix_mods.length}P, ${item.suffix_mods.length}S)${selectedOmens.length > 0 ? ` with omens: ${selectedOmens.join(', ')}` : ''}`)

      let result

      // Use appropriate API based on whether omens are selected
      if (selectedOmens.length > 0) {
        result = await craftingApi.simulateCraftingWithOmens(
          item,
          currencyType,
          selectedOmens
        )
      } else {
        result = await craftingApi.simulateCrafting({
          item,
          currency_name: currencyType
        })
      }

      // Debug logging for result
      if (result.result_item) {
        const finalModCount = result.result_item.prefix_mods.length + result.result_item.suffix_mods.length
        const modDifference = finalModCount - initialModCount
        console.log(`[DEBUG] Result: ${finalModCount} mods (${result.result_item.prefix_mods.length}P, ${result.result_item.suffix_mods.length}S), difference: ${modDifference}`)

        if (currencyType === 'Chaos Orb' && Math.abs(modDifference) > 0) {
          console.warn(`[WARNING] Chaos Orb changed mod count by ${modDifference}! This should not happen.`)
        }
      }

      // Check if crafting was successful
      if (!result.success) {
        setMessage(result.message || `${currencyType} failed to apply`)
        setLoading(false)
        return
      }

      // Check if item state changed during the async operation (race condition protection)
      const currentItemState = JSON.stringify(item)
      if (currentItemState !== initialItemState) {
        setMessage(`Warning: Item changed during crafting. Operation may have been interrupted.`)
        setLoading(false)
        return
      }

      // Success! Update item, history, and currency counter
      if (result.result_item) {
        // DEBUG: Check for fractured mods
        const allMods = [...result.result_item.prefix_mods, ...result.result_item.suffix_mods]
        const fracturedMods = allMods.filter(mod => mod.is_fractured)
        if (fracturedMods.length > 0) {
          console.log('[DEBUG] FRACTURED MODS IN RESULT:', fracturedMods.map(m => ({ name: m.name, is_fractured: m.is_fractured })))
        } else {
          console.log('[DEBUG] No fractured mods in result. All mods:', allMods.map(m => ({ name: m.name, is_fractured: m.is_fractured })))
        }

        setItem(result.result_item)
      }

      // Add to history (save current state BEFORE changes)
      setHistory([...history, `Applied ${currencyType}${selectedOmens.length > 0 ? ` with ${selectedOmens.join(', ')}` : ''}`])
      setItemHistory([...itemHistory, item])
      setActionHistory([...actionHistory, { currency: currencyType, omens: [...selectedOmens] }])
      setCurrencySpentHistory([...currencySpentHistory, currencySpent])

      // Clear redo stacks on new action
      setRedoItemStack([])
      setRedoHistoryStack([])
      setRedoCurrencyStack([])
      setRedoOmensStack([])
      setRedoCurrencySpentStack([])

      // Update currency spent (including omens)
      setCurrencySpent(prev => {
        const updated = { ...prev, [currencyType]: (prev[currencyType] || 0) + 1 }
        // Also track omens used
        for (const omen of selectedOmens) {
          updated[omen] = (updated[omen] || 0) + 1
        }
        return updated
      })

      setMessage(`${currencyType} applied successfully!`)

      // Clear selected omens after use
      setSelectedOmens([])

    } catch (err: any) {
      setMessage(`Error: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  // Create a snapshot of the current craft state for saving
  const createCraftSnapshot = useCallback((): CraftSnapshot => {
    // Get the initial item (first in history, or current if no history)
    const initialItem = itemHistory.length > 0 ? itemHistory[0] : item

    return {
      initialItem,
      finalItem: item,
      history,
      itemHistory,
      actionHistory,
      currencySpent,
      currencySpentHistory,
      stepComments: Object.keys(stepComments).length > 0 ? stepComments : undefined,
      baseStepIndex,
    }
  }, [item, history, itemHistory, actionHistory, currencySpent, currencySpentHistory, stepComments, baseStepIndex])

  // Load a craft snapshot into the simulator
  const loadCraftSnapshot = useCallback((snapshot: CraftSnapshot) => {
    setItem(snapshot.finalItem)
    setHistory(snapshot.history)
    setItemHistory(snapshot.itemHistory)
    setActionHistory(snapshot.actionHistory)
    setCurrencySpent(snapshot.currencySpent)
    setCurrencySpentHistory(snapshot.currencySpentHistory)
    setStepComments(snapshot.stepComments || {})
    setBaseStepIndex(snapshot.baseStepIndex)
    setBasePriceEstimate(null)  // Clear price when loading new craft

    // Clear redo stacks
    setRedoItemStack([])
    setRedoHistoryStack([])
    setRedoCurrencyStack([])
    setRedoOmensStack([])
    setRedoCurrencySpentStack([])

    // Mark item as created so we show the crafting view
    setItemCreated(true)

    setMessage('Craft loaded successfully')
  }, [])

  // Handle loading craft from navigation state (from CraftLibrary)
  useEffect(() => {
    const state = location.state as { loadCraft?: { snapshot: CraftSnapshot } } | null
    if (state?.loadCraft?.snapshot) {
      loadCraftSnapshot(state.loadCraft.snapshot)
      // Clear the state to prevent reloading on subsequent renders
      window.history.replaceState({}, document.title)
    }
  }, [location.state, loadCraftSnapshot])

  const handleUndo = () => {
    if (itemHistory.length > 0) {
      const previousItem = itemHistory[itemHistory.length - 1]
      const previousHistory = history.slice(0, -1)
      const previousItemHistory = itemHistory.slice(0, -1)
      const previousActionHistory = actionHistory.slice(0, -1)
      const previousCurrencySpentHistory = currencySpentHistory.slice(0, -1)

      // Save current state to redo stacks
      setRedoItemStack([...redoItemStack, item])
      setRedoHistoryStack([...redoHistoryStack, history[history.length - 1]])
      setRedoCurrencySpentStack([...redoCurrencySpentStack, currencySpent])

      // Save action details if available (for Ctrl+Y)
      const lastAction = actionHistory[actionHistory.length - 1]
      if (lastAction) {
        setRedoCurrencyStack([...redoCurrencyStack, lastAction.currency])
        setRedoOmensStack([...redoOmensStack, lastAction.omens])
      } else {
        setRedoCurrencyStack([...redoCurrencyStack, ''])
        setRedoOmensStack([...redoOmensStack, []])
      }

      setItem(previousItem)
      setHistory(previousHistory)
      setItemHistory(previousItemHistory)
      setActionHistory(previousActionHistory)
      setCurrencySpentHistory(previousCurrencySpentHistory)

      // Restore currency spent from history (or empty if this was the first action)
      const previousCurrencySpent = currencySpentHistory.length > 0
        ? currencySpentHistory[currencySpentHistory.length - 1]
        : {}
      setCurrencySpent(previousCurrencySpent)

      setMessage('Undone last action')
    }
  }

  const handleRedo = () => {
    if (redoItemStack.length > 0) {
      const nextItem = redoItemStack[redoItemStack.length - 1]
      const nextHistoryEntry = redoHistoryStack[redoHistoryStack.length - 1]
      const nextCurrency = redoCurrencyStack[redoCurrencyStack.length - 1]
      const nextOmens = redoOmensStack[redoOmensStack.length - 1]
      const nextCurrencySpent = redoCurrencySpentStack[redoCurrencySpentStack.length - 1]

      // Add current state to history before redoing
      setItemHistory([...itemHistory, item])
      setHistory([...history, nextHistoryEntry])
      setCurrencySpentHistory([...currencySpentHistory, currencySpent])
      if (nextCurrency) {
        setActionHistory([...actionHistory, { currency: nextCurrency, omens: nextOmens }])
      } else {
        setActionHistory([...actionHistory, null])
      }

      // Pop from redo stacks
      setRedoItemStack(redoItemStack.slice(0, -1))
      setRedoHistoryStack(redoHistoryStack.slice(0, -1))
      setRedoCurrencyStack(redoCurrencyStack.slice(0, -1))
      setRedoOmensStack(redoOmensStack.slice(0, -1))
      setRedoCurrencySpentStack(redoCurrencySpentStack.slice(0, -1))

      setItem(nextItem)
      setCurrencySpent(nextCurrencySpent || {})
      setMessage('Redone last action')
    }
  }

  const handleRetryLastAction = async () => {
    // Retry the last action from history (doesn't require undo first)
    if (actionHistory.length > 0 && itemHistory.length > 0) {
      const lastAction = actionHistory[actionHistory.length - 1]

      if (lastAction && lastAction.currency) {
        if (loading) return

        setLoading(true)
        setMessage('')

        try {
          // Get the item state BEFORE the last action
          // IMPORTANT: Deep clone to ensure we get a fresh copy for each retry
          // This prevents any reference issues and ensures true RNG on each retry
          const previousItem = JSON.parse(JSON.stringify(itemHistory[itemHistory.length - 1]))

          // Debug logging
          console.log(`[DEBUG] Retrying ${lastAction.currency} on ${previousItem.rarity} item with ${previousItem.prefix_mods.length}P, ${previousItem.suffix_mods.length}S`)

          let result

          // Use appropriate API based on whether omens were used
          if (lastAction.omens.length > 0) {
            result = await craftingApi.simulateCraftingWithOmens(
              previousItem,
              lastAction.currency,
              lastAction.omens
            )
          } else {
            result = await craftingApi.simulateCrafting({
              item: previousItem,
              currency_name: lastAction.currency
            })
          }

          // Check if crafting was successful
          if (!result.success) {
            setMessage(result.message || `${lastAction.currency} failed to apply`)
            setLoading(false)
            return
          }

          // Update state: remove last action from history and add the new result
          if (result.result_item) {
            setItem(result.result_item)
          }

          // Replace the last history entry with the retry
          // Keep the same previous currency state since we're replacing the action
          const previousCurrencyState = currencySpentHistory.length > 0
            ? currencySpentHistory[currencySpentHistory.length - 1]
            : {}
          setHistory([...history.slice(0, -1), `Applied ${lastAction.currency}${lastAction.omens.length > 0 ? ` with ${lastAction.omens.join(', ')}` : ''} (retry)`])
          setItemHistory([...itemHistory.slice(0, -1), previousItem])
          setActionHistory([...actionHistory.slice(0, -1), { currency: lastAction.currency, omens: lastAction.omens }])
          setCurrencySpentHistory([...currencySpentHistory.slice(0, -1), previousCurrencyState])

          // Clear redo stacks
          setRedoItemStack([])
          setRedoHistoryStack([])
          setRedoCurrencyStack([])
          setRedoOmensStack([])
          setRedoCurrencySpentStack([])

          // Update currency spent (including omens)
          setCurrencySpent(prev => {
            const updated = { ...prev, [lastAction.currency]: (prev[lastAction.currency] || 0) + 1 }
            // Also track omens used
            for (const omen of lastAction.omens) {
              updated[omen] = (updated[omen] || 0) + 1
            }
            return updated
          })

          setMessage(`${lastAction.currency} retried successfully!`)

        } catch (err: any) {
          setMessage(`Error: ${err.message}`)
        } finally {
          setLoading(false)
        }
      } else {
        setMessage('Cannot retry manual action')
      }
    }
  }

  // Keyboard shortcuts for undo/redo/retry
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey && event.key === 'z') {
        event.preventDefault()
        handleUndo()
      } else if (event.ctrlKey && event.key === 'y') {
        event.preventDefault()
        handleRedo()
      } else if (event.ctrlKey && event.key === 'r') {
        event.preventDefault()
        handleRetryLastAction()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [itemHistory, redoItemStack, actionHistory, redoCurrencyStack, redoOmensStack, currencySpentHistory, redoCurrencySpentStack, currencySpent])

  // Auto-dismiss message after 3 seconds
  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => {
        setMessage('')
      }, 3000)
      return () => clearTimeout(timer)
    }
  }, [message])

  // Auto-apply tag filters when Homogenising or Catalysing omen is selected
  useEffect(() => {
    const hasHomogenising = selectedOmens.some(omen => omen.includes('Homogenising'))
    const hasCatalysing = selectedOmens.some(omen => omen.includes('Catalysing'))

    if (hasHomogenising || hasCatalysing) {
      // Get all tags from existing mods
      const existingMods = [...item.prefix_mods, ...item.suffix_mods]
      const existingTags = existingMods.flatMap(m => m.tags || [])

      if (existingTags.length > 0) {
        // Auto-apply all existing mod tags as filters
        setActiveTagFilters(new Set(existingTags.filter(tag => tag !== 'desecrated_only')))
      }
    } else {
      // Clear tag filters when omens are deselected
      // Only clear if there are active filters (to avoid unnecessary re-renders)
      if (activeTagFilters.size > 0) {
        setActiveTagFilters(new Set())
      }
    }
  }, [selectedOmens, item.prefix_mods, item.suffix_mods])

  // Sophisticated mod filtering and grouping functions
  const renderModifier = (mod: ItemModifier) => {
    // Get values for all stats (multi-stat mods have multiple values)
    const values: (number | string)[] = []

    if (mod.current_values && mod.current_values.length > 0) {
      // Use rolled values for each stat
      values.push(...mod.current_values.map(v => Math.round(v)))
    } else if (mod.current_value !== undefined) {
      // Legacy: single value, duplicate for all placeholders
      const roundedValue = Math.round(mod.current_value)
      const placeholderCount = (mod.stat_text.match(/#/g) || []).length
      values.push(...Array(placeholderCount).fill(roundedValue))
    } else if (mod.stat_ranges && mod.stat_ranges.length > 0) {
      // Show ranges for each stat
      values.push(...mod.stat_ranges.map(r => `${r.min}-${r.max}`))
    } else if (mod.stat_min !== undefined && mod.stat_max !== undefined) {
      // Legacy: single range, duplicate for all placeholders
      const rangeText = `${mod.stat_min}-${mod.stat_max}`
      const placeholderCount = (mod.stat_text.match(/#/g) || []).length
      values.push(...Array(placeholderCount).fill(rangeText))
    } else {
      values.push('?')
    }

    // Replace # placeholders with corresponding values
    let statText = mod.stat_text
    for (const value of values) {
      statText = statText.replace('#', value.toString())
    }
    const modName = mod.name || 'Unknown'

    // Build range text for display - support hybrid mods with multiple ranges
    let rangeText = ''
    if (mod.stat_ranges && mod.stat_ranges.length > 0) {
      // Hybrid mods: show all ranges
      if (mod.stat_ranges.length > 1) {
        rangeText = `(${mod.stat_ranges.map(r => `${r.min}-${r.max}`).join(', ')})`
      } else {
        rangeText = `(${mod.stat_ranges[0].min}-${mod.stat_ranges[0].max})`
      }
    } else if (mod.stat_min !== undefined && mod.stat_max !== undefined) {
      // Legacy single range
      rangeText = `(${mod.stat_min}-${mod.stat_max})`
    }

    // Build tooltip with all ranges
    const rangeTooltip = mod.stat_ranges && mod.stat_ranges.length > 0
      ? `Ranges: ${mod.stat_ranges.map(r => `${r.min}-${r.max}`).join(', ')}`
      : (mod.stat_min !== undefined && mod.stat_max !== undefined
        ? `Range: ${mod.stat_min}-${mod.stat_max}`
        : null)

    const tooltipText = [
      `Name: ${modName}`,
      `Tier: ${mod.tier}`,
      mod.required_ilvl ? `Required ilvl: ${mod.required_ilvl}` : null,
      mod.mod_group ? `Group: ${mod.mod_group}` : null,
      rangeTooltip,
      (() => {
        const visibleTags = filterInternalTags(mod.tags)
        return visibleTags.length > 0 ? `Tags: ${visibleTags.join(', ')}` : null
      })(),
    ].filter(Boolean).join('\n')

    return (
      <span className="mod-with-info" title={tooltipText}>
        {statText} {rangeText && <span className="mod-range">{rangeText}</span>}
        {mod.is_fractured && <span className="fractured-indicator"> (Fractured)</span>}
      </span>
    )
  }

  // Function to determine which mod types should be highlighted based on selected omens
  const getHighlightedModTypes = (): { highlightPrefixes: boolean, highlightSuffixes: boolean, highlightSameTypes: boolean, highlightSameTags: boolean } => {
    if (selectedOmens.length === 0) {
      return { highlightPrefixes: false, highlightSuffixes: false, highlightSameTypes: false, highlightSameTags: false }
    }

    let highlightPrefixes = false
    let highlightSuffixes = false
    let highlightSameTypes = false
    let highlightSameTags = false

    for (const omen of selectedOmens) {
      // Prefix-focused omens (Sinistral = left/prefix)
      if (omen.includes('Sinistral')) {
        highlightPrefixes = true
      }
      // Suffix-focused omens (Dextral = right/suffix)
      else if (omen.includes('Dextral')) {
        highlightSuffixes = true
      }
      // Homogenising omens - highlight mods of same type as existing mods
      else if (omen.includes('Homogenising')) {
        highlightSameTypes = true
      }
      // Catalysing omen - highlight mods with same tags as existing mods
      else if (omen.includes('Catalysing')) {
        highlightSameTags = true
      }
    }

    return { highlightPrefixes, highlightSuffixes, highlightSameTypes, highlightSameTags }
  }

  const shouldGreyOutMod = (mod: ItemModifier, modType: 'prefix' | 'suffix'): boolean => {
    const highlighting = getHighlightedModTypes()

    // If no omens are selected, don't grey out anything
    if (!highlighting.highlightPrefixes && !highlighting.highlightSuffixes &&
        !highlighting.highlightSameTypes && !highlighting.highlightSameTags) {
      return false
    }

    // Desecrated mods can only come from desecration (bones), not regular currency
    // Always grey them out when any highlighting omen is active
    if (mod.is_desecrated) {
      return true
    }

    // Check prefix/suffix highlighting - if omen targets specific type, grey out the other
    if (highlighting.highlightPrefixes && modType === 'suffix') return true
    if (highlighting.highlightSuffixes && modType === 'prefix') return true

    // Check for exclusion group conflicts with existing mods
    // When omens are active (allowing manual selection), grey out conflicting mods
    if (mod.exclusion_group_id) {
      const existingMods = [...item.prefix_mods, ...item.suffix_mods].map(existingMod => {
        if (existingMod.exclusion_group_id) return existingMod

        // Annotate existing mod if it doesn't have exclusion_group_id
        for (const group of exclusionGroups) {
          if (!ruleApplesToItem(group, item.base_category)) continue
          const matchesGroup = group.patterns.some(pattern =>
            patternMatchesMod(pattern, existingMod.stat_text)
          )
          if (matchesGroup) {
            return { ...existingMod, exclusion_group_id: group.id }
          }
        }
        return existingMod
      })

      // Check if this mod conflicts with any existing mod
      const hasConflict = existingMods.some(existingMod =>
        existingMod.exclusion_group_id === mod.exclusion_group_id
      )

      if (hasConflict) {
        return true
      }
    }

    // For same type highlighting (homogenising omens), grey out mods that don't match existing tags
    if (highlighting.highlightSameTypes) {
      const existingMods = [...item.prefix_mods, ...item.suffix_mods]
      const existingTags = existingMods.flatMap(m => m.tags || [])

      // If mod has no tags that match existing tags, grey it out
      if (existingTags.length > 0 && (!mod.tags || !mod.tags.some(tag => existingTags.includes(tag)))) {
        return true
      }
    }

    // For same tag highlighting (catalysing omens), grey out mods without matching tags
    if (highlighting.highlightSameTags && mod.tags && mod.tags.length > 0) {
      const existingMods = [...item.prefix_mods, ...item.suffix_mods]
      const existingTags = existingMods.flatMap(m => m.tags || [])

      // If mod has no tags that match existing tags, grey it out
      if (existingTags.length > 0 && !mod.tags.some(tag => existingTags.includes(tag))) {
        return true
      }
    }

    return false
  }

  const isModMatchingTagFilters = (mod: any) => {
    if (activeTagFilters.size === 0) return true

    // Exclude desecrated mods when Homogenising/Catalysing omens are active
    // (these omens only work with regular currency, not desecration bones)
    const hasTagBasedOmen = selectedOmens.some(omen =>
      omen.includes('Homogenising') || omen.includes('Catalysing')
    )
    if (hasTagBasedOmen && mod.is_desecrated) {
      return false
    }

    if (!mod.tags || mod.tags.length === 0) return false
    // OR logic: match if ANY selected tag is present
    return Array.from(activeTagFilters).some(filter => mod.tags.includes(filter))
  }

  const isModMatchingSearch = (mod: any) => {
    if (!searchQuery.trim()) return true

    const searchableText = [
      mod.name || '',
      mod.stat_text || '',
      ...(mod.tags || [])
    ].join(' ')

    // Check if query contains spaces (multiple keywords)
    const keywords = searchQuery.trim().split(/\s+/)
    if (keywords.length > 1) {
      // Multiple keywords: apply AND logic
      return keywords.every(keyword => {
        try {
          // Try each keyword as regex
          const regex = new RegExp(keyword, 'i')
          return regex.test(searchableText)
        } catch (err) {
          // Fall back to simple string search
          return searchableText.toLowerCase().includes(keyword.toLowerCase())
        }
      })
    } else {
      // Single keyword: try as regex first
      try {
        const regex = new RegExp(searchQuery, 'i')
        return regex.test(searchableText)
      } catch (e) {
        // Fall back to simple string search
        return searchableText.toLowerCase().includes(searchQuery.toLowerCase())
      }
    }
  }

  const isCurrencyMatchingSearch = (currencyName: string) => {
    if (!searchQuery.trim()) return true

    // Try to get tooltip data from cache first, fallback to static data
    const cachedTooltip = currencyTooltipCache[currencyName]
    const staticData = CURRENCY_DESCRIPTIONS[currencyName]

    // Build searchable text from name + description + mechanics
    const searchableText = [
      currencyName,
      cachedTooltip?.description || staticData?.description || '',
      cachedTooltip?.mechanics || staticData?.mechanics || ''
    ].join(' ')

    // Check if query contains spaces (multiple keywords)
    const keywords = searchQuery.trim().split(/\s+/)
    if (keywords.length > 1) {
      // Multiple keywords: apply AND logic
      return keywords.every(keyword => {
        try {
          // Try each keyword as regex
          const regex = new RegExp(keyword, 'i')
          return regex.test(searchableText)
        } catch (err) {
          // Fall back to simple string search
          return searchableText.toLowerCase().includes(keyword.toLowerCase())
        }
      })
    } else {
      // Single keyword: try as regex first
      try {
        const regex = new RegExp(searchQuery, 'i')
        return regex.test(searchableText)
      } catch (e) {
        // Fall back to simple string search
        return searchableText.toLowerCase().includes(searchQuery.toLowerCase())
      }
    }
  }

  const shouldGreyOutModGroup = (groupMods: ItemModifier[], modType: 'prefix' | 'suffix'): boolean => {
    // Check if group should be greyed out due to omen incompatibility, tag filtering, or search
    const omenIncompatible = groupMods.every(mod => shouldGreyOutMod(mod, modType))
    const tagFiltered = activeTagFilters.size > 0 && !groupMods.some(mod => isModMatchingTagFilters(mod))
    const searchFiltered = searchQuery.trim() && !groupMods.some(mod => isModMatchingSearch(mod))
    return omenIncompatible || tagFiltered || searchFiltered
  }

  // Format stat_text by replacing # placeholders with actual value ranges
  const formatStatTextWithRanges = (mod: ItemModifier): string => {
    if (!mod.stat_ranges || mod.stat_ranges.length === 0) {
      return mod.stat_text
    }

    let result = mod.stat_text
    let rangeIndex = 0

    // Replace each # with the corresponding range
    result = result.replace(/#/g, () => {
      if (rangeIndex < mod.stat_ranges!.length) {
        const range = mod.stat_ranges![rangeIndex]
        rangeIndex++
        // Format as "min-max" or just "value" if min equals max
        if (range.min === range.max) {
          return String(range.min)
        }
        return `${range.min}-${range.max}`
      }
      return '#'
    })

    return result
  }

  const getGroupedMods = (modType: 'prefix' | 'suffix') => {
    let mods = modType === 'prefix' ? availableMods.prefixes : availableMods.suffixes

    // Apply search filter
    if (searchQuery.trim()) {
      mods = mods.filter(mod => isModMatchingSearch(mod))
    }

    // Apply tag filters
    if (activeTagFilters.size > 0) {
      mods = mods.filter(mod => isModMatchingTagFilters(mod))
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

  // Count matching mods (for display in table titles)
  const countMatchingMods = (modType: 'prefix' | 'suffix') => {
    const groupedMods = getGroupedMods(modType)
    const specialMods = modType === 'prefix' ? availableMods.essence_prefixes.concat(availableMods.desecrated_prefixes) : availableMods.essence_suffixes.concat(availableMods.desecrated_suffixes)

    let matchingCount = 0
    let totalCount = 0

    // Count grouped regular mods (count groups, not individual tiers)
    Object.values(groupedMods).forEach(groupMods => {
      totalCount++ // Count the group, not individual tiers
      const hasMatch = groupMods.some(mod => {
        const tagMatch = isModMatchingTagFilters(mod)
        const searchMatch = isModMatchingSearch(mod)
        const notGreyedOut = !shouldGreyOutMod(mod, modType)
        return tagMatch && searchMatch && notGreyedOut
      })
      if (hasMatch) {
        matchingCount++
      }
    })

    // Count special mods (essence + desecrated are individual mods, not grouped)
    specialMods.forEach(mod => {
      totalCount++
      const tagMatch = isModMatchingTagFilters(mod)
      const searchMatch = isModMatchingSearch(mod)
      const notGreyedOut = !shouldGreyOutMod(mod, modType)
      if (tagMatch && searchMatch && notGreyedOut) {
        matchingCount++
      }
    })

    return { matching: matchingCount, total: totalCount }
  }

  // Tag filtering functions
  const toggleTagFilter = (tag: string) => {
    const newFilters = new Set(activeTagFilters)
    if (newFilters.has(tag)) {
      newFilters.delete(tag)
    } else {
      newFilters.add(tag)
    }
    setActiveTagFilters(newFilters)
  }

  const clearTagFilters = () => {
    setActiveTagFilters(new Set())
  }

  // Currency icon helpers
  const getCurrencyIconUrl = (currency: string): string => {
    const iconMap: Record<string, string> = {
      "Orb of Transmutation": "https://www.poe2wiki.net/images/6/67/Orb_of_Transmutation_inventory_icon.png",
      "Greater Orb of Transmutation": "https://www.poe2wiki.net/images/6/67/Orb_of_Transmutation_inventory_icon.png",
      "Perfect Orb of Transmutation": "https://www.poe2wiki.net/images/6/67/Orb_of_Transmutation_inventory_icon.png",
      "Orb of Augmentation": "https://www.poe2wiki.net/images/c/cb/Orb_of_Augmentation_inventory_icon.png",
      "Greater Orb of Augmentation": "https://www.poe2wiki.net/images/c/cb/Orb_of_Augmentation_inventory_icon.png",
      "Perfect Orb of Augmentation": "https://www.poe2wiki.net/images/c/cb/Orb_of_Augmentation_inventory_icon.png",
      "Orb of Alchemy": "https://www.poe2wiki.net/images/9/9f/Orb_of_Alchemy_inventory_icon.png",
      "Regal Orb": "https://www.poe2wiki.net/images/3/33/Regal_Orb_inventory_icon.png",
      "Greater Regal Orb": "https://www.poe2wiki.net/images/3/33/Regal_Orb_inventory_icon.png",
      "Perfect Regal Orb": "https://www.poe2wiki.net/images/3/33/Regal_Orb_inventory_icon.png",
      "Exalted Orb": "https://www.poe2wiki.net/images/2/26/Exalted_Orb_inventory_icon.png",
      "Greater Exalted Orb": "https://www.poe2wiki.net/images/2/26/Exalted_Orb_inventory_icon.png",
      "Perfect Exalted Orb": "https://www.poe2wiki.net/images/2/26/Exalted_Orb_inventory_icon.png",
      "Chaos Orb": "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png",
      "Greater Chaos Orb": "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png",
      "Perfect Chaos Orb": "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png",
      "Divine Orb": "https://www.poe2wiki.net/images/5/58/Divine_Orb_inventory_icon.png",
      "Orb of Annulment": "https://www.poe2wiki.net/images/4/4c/Orb_of_Annulment_inventory_icon.png",
      "Vaal Orb": "https://www.poe2wiki.net/images/2/2c/Vaal_Orb_inventory_icon.png",
      "Orb of Fracturing": "https://www.poe2wiki.net/images/7/70/Fracturing_Orb_inventory_icon.png"
    }

    // Handle Essences
    if (currency.includes('Essence of')) {
      const essenceIconMap: Record<string, string> = {
        // Basic damage essences
        'Flames': 'https://www.poe2wiki.net/images/d/d4/Essence_of_Flames_inventory_icon.png',
        'Fire': 'https://www.poe2wiki.net/images/d/d4/Essence_of_Flames_inventory_icon.png',
        'Ice': 'https://www.poe2wiki.net/images/d/df/Essence_of_Ice_inventory_icon.png',
        'Cold': 'https://www.poe2wiki.net/images/d/df/Essence_of_Ice_inventory_icon.png',
        'Electricity': 'https://www.poe2wiki.net/images/c/ca/Essence_of_Electricity_inventory_icon.png',
        'Lightning': 'https://www.poe2wiki.net/images/c/ca/Essence_of_Electricity_inventory_icon.png',

        // Defense essences
        'the Body': 'https://www.poe2wiki.net/images/b/b2/Essence_of_the_Body_inventory_icon.png',
        'Life': 'https://www.poe2wiki.net/images/b/b2/Essence_of_the_Body_inventory_icon.png',
        'the Mind': 'https://www.poe2wiki.net/images/6/62/Essence_of_the_Mind_inventory_icon.png',
        'Mana': 'https://www.poe2wiki.net/images/6/62/Essence_of_the_Mind_inventory_icon.png',
        'the Protector': 'https://www.poe2wiki.net/images/f/fc/Essence_of_the_Protector_inventory_icon.png',
        'Armor': 'https://www.poe2wiki.net/images/f/fc/Essence_of_the_Protector_inventory_icon.png',
        'Haste': 'https://www.poe2wiki.net/images/0/09/Essence_of_Haste_inventory_icon.png',
        'Evasion': 'https://www.poe2wiki.net/images/0/09/Essence_of_Haste_inventory_icon.png',
        'Warding': 'https://www.poe2wiki.net/images/d/d1/Essence_of_Warding_inventory_icon.png',
        'Energy Shield': 'https://www.poe2wiki.net/images/d/d1/Essence_of_Warding_inventory_icon.png',

        // Physical/Combat essences
        'Abrasion': 'https://www.poe2wiki.net/images/2/22/Essence_of_Abrasion_inventory_icon.png',
        'Battle': 'https://www.poe2wiki.net/images/2/28/Essence_of_Battle_inventory_icon.png',
        'Sorcery': 'https://www.poe2wiki.net/images/3/38/Essence_of_Sorcery_inventory_icon.png',

        // Support essences
        'Alacrity': 'https://www.poe2wiki.net/images/3/33/Essence_of_Alacrity_inventory_icon.png',
        'Command': 'https://www.poe2wiki.net/images/3/3a/Essence_of_Command_inventory_icon.png',
        'Enhancement': 'https://www.poe2wiki.net/images/3/3f/Essence_of_Enhancement_inventory_icon.png',
        'Grounding': 'https://www.poe2wiki.net/images/7/72/Essence_of_Grounding_inventory_icon.png',
        'Seeking': 'https://www.poe2wiki.net/images/d/d4/Essence_of_Seeking_inventory_icon.png',
        'Thawing': 'https://www.poe2wiki.net/images/2/21/Essence_of_Thawing_inventory_icon.png',
        'Insulation': 'https://www.poe2wiki.net/images/4/45/Essence_of_Insulation_inventory_icon.png',
        'Opulence': 'https://www.poe2wiki.net/images/d/d2/Essence_of_Opulence_inventory_icon.png',

        // Chaos/Special essences
        'Ruin': 'https://www.poe2wiki.net/images/5/54/Essence_of_Ruin_inventory_icon.png',
        'the Infinite': 'https://www.poe2wiki.net/images/a/a7/Essence_of_the_Infinite_inventory_icon.png',

        // Corrupted essences
        'Delirium': 'https://www.poe2wiki.net/images/9/9b/Essence_of_Delirium_inventory_icon.png',
        'Horror': 'https://www.poe2wiki.net/images/c/c2/Essence_of_Horror_inventory_icon.png',
        'Hysteria': 'https://www.poe2wiki.net/images/f/fc/Essence_of_Hysteria_inventory_icon.png',
        'Insanity': 'https://www.poe2wiki.net/images/a/aa/Essence_of_Insanity_inventory_icon.png',
        'the Abyss': 'https://www.poe2wiki.net/images/a/ac/Essence_of_the_Abyss_inventory_icon.png',
      }

      for (const [key, url] of Object.entries(essenceIconMap)) {
        if (currency.includes(key)) {
          return url
        }
      }
    }

    // Handle Bones - use wiki URLs with correct hash paths (verified)
    if (currency.includes('Bone') || currency.includes('bone') || currency.startsWith('Abyssal') || currency.startsWith('Ancient') || currency.includes('Cranium') || currency.includes('Vertebrae')) {
      const boneIconMap: Record<string, string> = {
        'Ancient Collarbone': 'https://www.poe2wiki.net/images/2/29/Ancient_Collarbone_inventory_icon.png',
        'Ancient Jawbone': 'https://www.poe2wiki.net/images/7/79/Ancient_Jawbone_inventory_icon.png',
        'Ancient Rib': 'https://www.poe2wiki.net/images/9/9d/Ancient_Rib_inventory_icon.png',
        'Gnawed Collarbone': 'https://www.poe2wiki.net/images/2/2f/Gnawed_Collarbone_inventory_icon.png',
        'Gnawed Jawbone': 'https://www.poe2wiki.net/images/7/75/Gnawed_Jawbone_inventory_icon.png',
        'Gnawed Rib': 'https://www.poe2wiki.net/images/6/61/Gnawed_Rib_inventory_icon.png?v=2',
        'Preserved Collarbone': 'https://www.poe2wiki.net/images/7/7a/Preserved_Collarbone_inventory_icon.png',
        'Preserved Jawbone': 'https://www.poe2wiki.net/images/4/47/Preserved_Jawbone_inventory_icon.png',
        'Preserved Rib': 'https://www.poe2wiki.net/images/e/e8/Preserved_Rib_inventory_icon.png?v=2',
        'Preserved Cranium': 'https://www.poe2wiki.net/images/5/50/Preserved_Cranium_inventory_icon.png',
        'Preserved Vertebrae': 'https://www.poe2wiki.net/images/e/e2/Preserved_Vertebrae_inventory_icon.png',
      }

      return boneIconMap[currency] || 'https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png'
    }

    return iconMap[currency] || "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
  }

  const getOmenIconUrl = (omen: string): string => {
    const omenIconMap: Record<string, string> = {
      // Exalted Omens
      "Omen of Greater Exaltation": "https://www.poe2wiki.net/images/6/6b/Omen_of_Greater_Exaltation_inventory_icon.png",
      "Omen of Sinistral Exaltation": "https://www.poe2wiki.net/images/0/06/Omen_of_Sinistral_Exaltation_inventory_icon.png",
      "Omen of Dextral Exaltation": "https://www.poe2wiki.net/images/4/4d/Omen_of_Dextral_Exaltation_inventory_icon.png",
      "Omen of Homogenising Exaltation": "https://www.poe2wiki.net/images/6/60/Omen_of_Homogenising_Exaltation_inventory_icon.png",
      "Omen of Catalysing Exaltation": "https://www.poe2wiki.net/images/9/9b/Omen_of_Catalysing_Exaltation_inventory_icon.png",

      // Regal Omens
      "Omen of Sinistral Coronation": "https://www.poe2wiki.net/images/6/66/Omen_of_Sinistral_Coronation_inventory_icon.png",
      "Omen of Dextral Coronation": "https://www.poe2wiki.net/images/1/1c/Omen_of_Dextral_Coronation_inventory_icon.png",
      "Omen of Homogenising Coronation": "https://www.poe2wiki.net/images/0/0b/Omen_of_Homogenising_Coronation_inventory_icon.png",

      // Chaos/Removal Omens
      "Omen of Whittling": "https://www.poe2wiki.net/images/8/81/Omen_of_Whittling_inventory_icon.png",
      "Omen of Sinistral Erasure": "https://www.poe2wiki.net/images/4/47/Omen_of_Sinistral_Erasure_inventory_icon.png",
      "Omen of Dextral Erasure": "https://www.poe2wiki.net/images/0/0b/Omen_of_Dextral_Erasure_inventory_icon.png",

      // Annulment Omens
      "Omen of Greater Annulment": "https://www.poe2wiki.net/images/d/df/Omen_of_Greater_Annulment_inventory_icon.png",
      "Omen of Sinistral Annulment": "https://www.poe2wiki.net/images/4/45/Omen_of_Sinistral_Annulment_inventory_icon.png",
      "Omen of Dextral Annulment": "https://www.poe2wiki.net/images/e/ef/Omen_of_Dextral_Annulment_inventory_icon.png",

      // Alchemy & Essence Omens (verified from wiki)
      "Omen of Sinistral Alchemy": "https://www.poe2wiki.net/images/1/1f/Omen_of_Sinistral_Alchemy_inventory_icon.png",
      "Omen of Dextral Alchemy": "https://www.poe2wiki.net/images/e/ee/Omen_of_Dextral_Alchemy_inventory_icon.png",
      "Omen of Sinistral Crystallisation": "https://www.poe2wiki.net/images/e/ec/Omen_of_Sinistral_Crystallisation_inventory_icon.png",
      "Omen of Dextral Crystallisation": "https://www.poe2wiki.net/images/7/7c/Omen_of_Dextral_Crystallisation_inventory_icon.png",

      // Desecration/Abyssal Omens (verified from wiki)
      "Omen of Abyssal Echoes": "https://www.poe2wiki.net/images/8/8a/Omen_of_Abyssal_Echoes_inventory_icon.png",
      "Omen of Sinistral Necromancy": "https://www.poe2wiki.net/images/2/2e/Omen_of_Sinistral_Necromancy_inventory_icon.png",
      "Omen of Dextral Necromancy": "https://www.poe2wiki.net/images/8/84/Omen_of_Dextral_Necromancy_inventory_icon.png",
      "Omen of the Sovereign": "https://www.poe2wiki.net/images/b/b5/Omen_of_the_Sovereign_inventory_icon.png",
      "Omen of the Liege": "https://www.poe2wiki.net/images/9/96/Omen_of_the_Liege_inventory_icon.png",
      "Omen of the Blackblooded": "https://www.poe2wiki.net/images/6/60/Omen_of_the_Blackblooded_inventory_icon.png",
      "Omen of Putrefaction": "https://www.poe2wiki.net/images/b/b8/Omen_of_Putrefaction_inventory_icon.png",
      "Omen of Light": "https://www.poe2wiki.net/images/1/12/Omen_of_Light_inventory_icon.png",

      // Corruption (verified from wiki)
      "Omen of Corruption": "https://www.poe2wiki.net/images/a/a2/Omen_of_Corruption_inventory_icon.png",
    }

    return omenIconMap[omen] || "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
  }

  // Mod group expansion
  const toggleModGroup = (groupKey: string) => {
    const newExpanded = new Set(expandedModGroups)
    if (newExpanded.has(groupKey)) {
      newExpanded.delete(groupKey)
    } else {
      newExpanded.add(groupKey)
    }
    setExpandedModGroups(newExpanded)
  }

  // Apply all tags from a mod group
  const applyAllModTags = (mod: any) => {
    if (mod.tags && mod.tags.length > 0) {
      const newFilters = new Set(activeTagFilters)
      mod.tags.forEach((tag: string) => newFilters.add(tag))
      setActiveTagFilters(newFilters)
    }
  }

  // Available tags from all mods
  const allAvailableTags = useMemo(() => {
    const tagSet = new Set<string>()
    const allMods = [
      ...availableMods.prefixes,
      ...availableMods.suffixes,
      ...availableMods.essence_prefixes,
      ...availableMods.essence_suffixes,
      ...availableMods.desecrated_prefixes,
      ...availableMods.desecrated_suffixes
    ]
    allMods.forEach(mod => {
      if (mod.tags) {
        // Filter out internal tags before adding to the set
        const visibleTags = filterInternalTags(mod.tags)
        visibleTags.forEach((tag: string) => tagSet.add(tag))
      }
    })
    return Array.from(tagSet).sort()
  }, [availableMods])

  // Create a mapping of exclusion group IDs to sequential display numbers (1, 2, 3...)
  const exclusionGroupDisplayMap = useMemo(() => {
    const allMods = [
      ...availableMods.prefixes,
      ...availableMods.suffixes,
      ...availableMods.essence_prefixes,
      ...availableMods.essence_suffixes,
      ...availableMods.desecrated_prefixes,
      ...availableMods.desecrated_suffixes
    ]

    const uniqueGroups = new Set<string>()
    allMods.forEach(mod => {
      if (mod.exclusion_group_id) {
        uniqueGroups.add(mod.exclusion_group_id)
      }
    })

    // Sort group IDs and create sequential mapping
    const sortedGroups = Array.from(uniqueGroups).sort()
    const mapping: Record<string, number> = {}
    sortedGroups.forEach((groupId, index) => {
      mapping[groupId] = index + 1
    })

    return mapping
  }, [availableMods])

  return (
    <div className="grid-crafting-simulator">
      {/* Toast Message */}
      {message && (
        <div className={`message ${message.includes('Error') ? 'error' : message.includes('success') ? 'success' : 'info'}`}>
          {message}
        </div>
      )}

      {/* Global Tag Filters - Floating at Top */}
      <div className="global-tag-filters">
        <div className="global-tag-filters-content">
          <button
            className={`clear-filters-btn ${activeTagFilters.size === 0 ? 'disabled' : ''}`}
            onClick={clearTagFilters}
            disabled={activeTagFilters.size === 0}
            title={activeTagFilters.size > 0 ? `Clear ${activeTagFilters.size} active filters` : 'No active filters'}
          >
            ↺ Clear
          </button>
          <div className="global-tag-list">
            {allAvailableTags.map(tag => {
              const tagColor = getTagColor(tag)
              const isActive = activeTagFilters.has(tag)
              return (
                <span
                  key={tag}
                  className={`global-tag-item ${isActive ? 'active-filter' : ''}`}
                  data-tag={tag}
                  onClick={() => toggleTagFilter(tag)}
                  title={`Toggle ${tag} filter`}
                  style={isActive ? undefined : {
                    background: tagColor.bg,
                    borderColor: tagColor.border,
                    color: tagColor.text
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.background = tagColor.hover
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.background = tagColor.bg
                    }
                  }}
                >
                  {tag}
                </span>
              )
            })}
          </div>
          <div className="search-container">
            <input
              type="text"
              className="mod-search-input"
              placeholder="🔍 Search mods (supports regex)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              title="Search mod names, stats, and tags. Supports regex patterns like 'fire|cold' or '^Adds.*to Attacks$'"
            />
            {searchQuery && (
              <button
                className="clear-search-btn"
                onClick={() => setSearchQuery('')}
                title="Clear search"
              >
                ✕
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="three-column-layout">
        {/* Left Panel - Available Mods */}
        <div className={`left-panel ${leftPanelCollapsed ? 'collapsed' : ''}`}>
          <button
            className={`panel-collapse-btn ${leftPanelCollapsed ? 'collapsed' : ''}`}
            onClick={() => setLeftPanelCollapsed(!leftPanelCollapsed)}
            title={leftPanelCollapsed ? "Expand mods panel" : "Collapse mods panel"}
          >
            {leftPanelCollapsed ? '▶' : '◀'}
          </button>
          <div className="mods-pool-panel">
            <div className="mods-pool-header">
              <h3>🎯 Available Mods</h3>
              <div className="mods-pool-stats">
                <span className="stat-badge prefix-badge">
                  {availableMods.prefixes.length} Prefixes
                </span>
                <span className="stat-badge suffix-badge">
                  {availableMods.suffixes.length} Suffixes
                </span>
                {(availableMods.essence_prefixes.length > 0 || availableMods.essence_suffixes.length > 0) && (
                  <span className="stat-badge essence-badge">
                    {availableMods.essence_prefixes.length + availableMods.essence_suffixes.length} Essence-Only
                  </span>
                )}
                {(availableMods.desecrated_prefixes.length > 0 || availableMods.desecrated_suffixes.length > 0) && (
                  <span className="stat-badge desecrated-badge">
                    {availableMods.desecrated_prefixes.length + availableMods.desecrated_suffixes.length} Desecrated-Only
                  </span>
                )}
              </div>
            </div>

            {/* Search bar removed - will be global instead */}

            <div className="mods-pool-columns">
              <div className="mods-pool-column">
                <h4 className="column-title">Prefixes ({(() => {
                  const counts = countMatchingMods('prefix')
                  return counts.matching === counts.total ? `${counts.total} total` : `${counts.matching}/${counts.total}`
                })()})</h4>
                <div className="mods-pool-list">
                  {/* Normal Prefixes */}
                  {Object.entries(getGroupedMods('prefix')).map(([groupKey, groupMods]) => {
                    const maxIlvl = Math.max(...groupMods.map(m => m.required_ilvl || 1))
                    const unavailableCount = groupMods.filter(m => m.required_ilvl && m.required_ilvl > item.item_level).length
                    const allUnavailable = unavailableCount === groupMods.length
                    const isGroupGreyedOut = shouldGreyOutModGroup(groupMods, 'prefix')
                    const isExpanded = expandedModGroups.has(`prefix-${groupKey}`)

                    // Calculate available tiers (filtered by ilvl)
                    const availableModsInGroup = groupMods.filter(m => !m.required_ilvl || m.required_ilvl <= item.item_level)
                    // Use best available tier for display, fallback to T1 if none available
                    const displayTier = availableModsInGroup.length > 0 ? availableModsInGroup[0] : groupMods[0]
                    const bestAvailableTierNum = availableModsInGroup.length > 0 ? Math.min(...availableModsInGroup.map(m => m.tier)) : null
                    const worstTier = Math.max(...groupMods.map(m => m.tier))
                    const tierRangeText = bestAvailableTierNum ? `T${bestAvailableTierNum}-T${worstTier}` : `T1-T${worstTier}`

                    // Check if any tier in this group has essence guarantees
                    const essenceGuaranteeTiers = groupMods.filter(m =>
                      m.mod_id && availableMods.essence_guarantees[m.mod_id]
                    )
                    const hasAnyEssenceGuarantee = essenceGuaranteeTiers.length > 0

                    return (
                      <div key={groupKey} className={`pool-mod-group ${isGroupGreyedOut ? 'omen-incompatible' : ''}`}>
                        <div
                          className={`pool-mod-group-header prefix compact-single-line ${allUnavailable ? 'all-unavailable' : ''} mod-group-clickable`}
                          onClick={() => toggleModGroup(`prefix-${groupKey}`)}
                          onDoubleClick={() => applyAllModTags(displayTier)}
                          draggable={!allUnavailable && itemCreated}
                          onDragStart={() => handleDragStart(displayTier, 'prefix')}
                          onDragEnd={handleDragEnd}
                          title="Click to expand/collapse, double-click to filter by all tags, drag to add to item"
                        >
                          <span className="pool-mod-stat-main">
                            {formatStatTextWithRanges(displayTier)}
                            {displayTier.exclusion_group_id && (() => {
                              const groupInfo = getModExclusionGroupInfo(displayTier)
                              const groupColor = getExclusionGroupColor(displayTier.exclusion_group_id)
                              const groupNum = exclusionGroupDisplayMap[displayTier.exclusion_group_id] || '?'
                              return (
                                <span
                                  className="exclusion-group-badge"
                                  style={{
                                    background: groupColor.bg,
                                    borderColor: groupColor.border,
                                    color: groupColor.text,
                                    marginLeft: '6px',
                                    padding: '2px 6px',
                                    borderRadius: '3px',
                                    fontSize: '11px',
                                    border: '1px solid',
                                    fontWeight: 'bold',
                                    display: 'inline-block',
                                    minWidth: '18px',
                                    textAlign: 'center'
                                  }}
                                  title={groupInfo?.description || 'Exclusion group'}
                                >
                                  {groupNum}
                                </span>
                              )
                            })()}
                          </span>
                          <div className="compact-mod-info">
                            {unavailableCount > 0 && (
                              <span
                                className="unavailable-indicator"
                                title={`${unavailableCount} unavailable tier${unavailableCount > 1 ? 's' : ''}`}
                              >
                                ⚠
                              </span>
                            )}
                            {hasAnyEssenceGuarantee && (
                              <span
                                className="essence-guarantee-group-indicator"
                                title={`${essenceGuaranteeTiers.length} tier${essenceGuaranteeTiers.length > 1 ? 's' : ''} can be guaranteed by essence`}
                              >
                                ◆
                              </span>
                            )}
                            <span className="group-tier-range">{tierRangeText}</span>
                            <span className="group-max-ilvl">ilvl {maxIlvl}</span>
                            {(() => {
                              // Calculate combined weight of available tiers only (filtered by ilvl)
                              const combinedWeight = availableModsInGroup.reduce((sum, mod) => sum + (mod.weight || 0), 0)
                              return combinedWeight > 0 && totalWeights.prefix > 0 && (
                                <span className="mod-weight" title={`Combined weight: ${combinedWeight} / ${totalWeights.prefix} total (${availableModsInGroup.length} available tiers)`}>
                                  {((combinedWeight / totalWeights.prefix) * 100).toFixed(2)}%
                                </span>
                              )
                            })()}
                            {displayTier.tags && displayTier.tags.length > 0 && (
                              <div className="mod-tags-line" title="Click individual tags to filter">
                                <button
                                  className="apply-all-tags-btn"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    applyAllModTags(displayTier);
                                  }}
                                  title="Apply all tags as filters"
                                >
                                  ✓✓
                                </button>
                                {displayTier.tags.map((tag, i) => {
                                  const tagColor = getTagColor(tag)
                                  return (
                                    <span
                                      key={i}
                                      className="mod-tag-text"
                                      data-tag={tag}
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        toggleTagFilter(tag);
                                      }}
                                      title={`Click to filter by "${tag}" tag`}
                                      style={{
                                        background: tagColor.bg,
                                        borderColor: tagColor.border,
                                        color: tagColor.text
                                      }}
                                      onMouseEnter={(e) => {
                                        e.currentTarget.style.background = tagColor.hover
                                      }}
                                      onMouseLeave={(e) => {
                                        e.currentTarget.style.background = tagColor.bg
                                      }}
                                    >
                                      {tag}
                                    </span>
                                  )
                                })}
                              </div>
                            )}
                          </div>
                        </div>

                        {isExpanded && (
                          <div className="mod-tier-details">
                            {groupMods.map(mod => {
                              // Format the mod text with embedded value ranges
                              let formattedText = mod.stat_text

                              if (mod.stat_ranges && mod.stat_ranges.length > 0) {
                                // Replace each # with the corresponding range in curly braces
                                mod.stat_ranges.forEach(range => {
                                  const rangeText = range.min === range.max
                                    ? `${range.min}`
                                    : `{${range.min}-${range.max}}`
                                  formattedText = formattedText.replace('#', rangeText)
                                })
                              } else if (mod.stat_min !== undefined && mod.stat_max !== undefined) {
                                // Legacy single range
                                const rangeText = mod.stat_min === mod.stat_max
                                  ? `${mod.stat_min}`
                                  : `{${mod.stat_min}-${mod.stat_max}}`
                                formattedText = formattedText.replace('#', rangeText)
                              }

                              const tierPct = mod.weight && totalWeights.prefix > 0
                                ? ((mod.weight / totalWeights.prefix) * 100).toFixed(2)
                                : null

                              // Check if this mod has essence guarantees
                              const essenceGuarantees = mod.mod_id ? availableMods.essence_guarantees[mod.mod_id] : null
                              const hasEssenceGuarantee = essenceGuarantees && essenceGuarantees.length > 0

                              const isUnavailable = mod.required_ilvl && mod.required_ilvl > item.item_level
                              const isDraggable = !isUnavailable && itemCreated

                              return (
                                <div
                                  key={mod.tier}
                                  className={`tier-detail ${isUnavailable ? 'unavailable' : ''} ${hasEssenceGuarantee ? 'has-essence-guarantee' : ''} ${isDraggable ? 'draggable-tier' : ''}`}
                                  draggable={isDraggable}
                                  onDragStart={() => isDraggable && handleDragStart(mod, 'prefix')}
                                  onDragEnd={handleDragEnd}
                                  title={isDraggable ? "Drag to add this specific tier to item" : undefined}
                                >
                                  <span className="tier-label">T{mod.tier}</span>
                                  {hasEssenceGuarantee && (
                                    <span
                                      className="essence-guarantee-indicator"
                                      title={`Guaranteed by: ${[...new Set(essenceGuarantees.map(g => g.essence_name))].join(', ')}`}
                                    >
                                      ◆
                                    </span>
                                  )}
                                  <span className="tier-stat">{formattedText}</span>
                                  <span className="tier-ilvl">ilvl {mod.required_ilvl || 1}</span>
                                  {tierPct && (
                                    <span className="tier-weight" title={`Weight: ${mod.weight} / ${totalWeights.prefix} total`}>
                                      {tierPct}%
                                    </span>
                                  )}
                                </div>
                              )
                            })}
                          </div>
                        )}
                      </div>
                    )
                  })}

                  {/* Essence Prefixes */}
                  {availableMods.essence_prefixes.map((mod, idx) => {
                    const isTagFiltered = activeTagFilters.size > 0 && !isModMatchingTagFilters(mod)
                    const isSearchFiltered = searchQuery.trim() && !isModMatchingSearch(mod)
                    const isOmenIncompatible = shouldGreyOutMod(mod, 'prefix')
                    const isFiltered = isTagFiltered || isSearchFiltered
                    return (
                      <div key={`essence-prefix-${idx}`} className={`pool-mod-group essence-only ${isFiltered ? 'tag-filtered' : ''} ${isOmenIncompatible ? 'omen-incompatible' : ''}`}>
                        <div
                          className="pool-mod-group-header prefix compact-single-line mod-group-clickable"
                          onDoubleClick={() => applyAllModTags(mod)}
                          draggable={itemCreated}
                          onDragStart={() => handleDragStart(mod, 'prefix')}
                          onDragEnd={handleDragEnd}
                          title="Essence-only mod - Double-click to filter by all tags, drag to add to item"
                        >
                          <span className="pool-mod-stat-main">
                            {mod.stat_text}
                            {mod.exclusion_group_id && (() => {
                              const groupInfo = getModExclusionGroupInfo(mod)
                              const groupColor = getExclusionGroupColor(mod.exclusion_group_id)
                              const groupNum = exclusionGroupDisplayMap[mod.exclusion_group_id] || '?'
                              return (
                                <span
                                  className="exclusion-group-badge"
                                  style={{
                                    background: groupColor.bg,
                                    borderColor: groupColor.border,
                                    color: groupColor.text,
                                    marginLeft: '6px',
                                    padding: '2px 6px',
                                    borderRadius: '3px',
                                    fontSize: '11px',
                                    border: '1px solid',
                                    fontWeight: 'bold',
                                    display: 'inline-block',
                                    minWidth: '18px',
                                    textAlign: 'center'
                                  }}
                                  title={groupInfo?.description || 'Exclusion group'}
                                >
                                  {groupNum}
                                </span>
                              )
                            })()}
                          </span>
                          <div className="compact-mod-info">
                            {/* No weight display for essence mods - they're guaranteed outcomes */}
                            {mod.tags && mod.tags.length > 0 && (
                              <div className="mod-tags-line" title="Click individual tags to filter">
                                <button
                                  className="apply-all-tags-btn"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    applyAllModTags(mod);
                                  }}
                                  title="Apply all tags as filters"
                                >
                                  ✓✓
                                </button>
                                {mod.tags.map((tag, i) => {
                                  const tagColor = getTagColor(tag)
                                  return (
                                    <span
                                      key={i}
                                      className="mod-tag-text"
                                      data-tag={tag}
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        toggleTagFilter(tag);
                                      }}
                                      title={`Click to filter by "${tag}" tag`}
                                      style={{
                                        background: tagColor.bg,
                                        borderColor: tagColor.border,
                                        color: tagColor.text
                                      }}
                                      onMouseEnter={(e) => {
                                        e.currentTarget.style.background = tagColor.hover
                                      }}
                                      onMouseLeave={(e) => {
                                        e.currentTarget.style.background = tagColor.bg
                                      }}
                                    >
                                      {tag}
                                    </span>
                                  )
                                })}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })}

                  {/* Desecrated Prefixes */}
                  {availableMods.desecrated_prefixes.map((mod, idx) => {
                    const isTagFiltered = activeTagFilters.size > 0 && !isModMatchingTagFilters(mod)
                    const isSearchFiltered = searchQuery.trim() && !isModMatchingSearch(mod)
                    const isOmenIncompatible = shouldGreyOutMod(mod, 'prefix')
                    const isFiltered = isTagFiltered || isSearchFiltered
                    return (
                      <div key={`desecrated-prefix-${idx}`} className={`pool-mod-group desecrated-only ${isFiltered ? 'tag-filtered' : ''} ${isOmenIncompatible ? 'omen-incompatible' : ''}`}>
                        <div
                          className="pool-mod-group-header prefix compact-single-line mod-group-clickable"
                          onDoubleClick={() => applyAllModTags(mod)}
                          draggable={itemCreated}
                          onDragStart={() => handleDragStart(mod, 'prefix')}
                          onDragEnd={handleDragEnd}
                          title="Desecrated-only mod - Double-click to filter by all tags, drag to add to item"
                        >
                          <span className="pool-mod-stat-main">
                            {mod.stat_text}
                            {mod.exclusion_group_id && (() => {
                              const groupInfo = getModExclusionGroupInfo(mod)
                              const groupColor = getExclusionGroupColor(mod.exclusion_group_id)
                              const groupNum = exclusionGroupDisplayMap[mod.exclusion_group_id] || '?'
                              return (
                                <span
                                  className="exclusion-group-badge"
                                  style={{
                                    background: groupColor.bg,
                                    borderColor: groupColor.border,
                                    color: groupColor.text,
                                    marginLeft: '6px',
                                    padding: '2px 6px',
                                    borderRadius: '3px',
                                    fontSize: '11px',
                                    border: '1px solid',
                                    fontWeight: 'bold',
                                    display: 'inline-block',
                                    minWidth: '18px',
                                    textAlign: 'center'
                                  }}
                                  title={groupInfo?.description || 'Exclusion group'}
                                >
                                  {groupNum}
                                </span>
                              )
                            })()}
                          </span>
                          <div className="compact-mod-info">
                            {mod.weight !== undefined && totalWeights.desecrated_prefix > 0 && (
                              <span className="mod-weight" title={`Weight: ${mod.weight} / ${totalWeights.desecrated_prefix} total`}>
                                {((mod.weight / totalWeights.desecrated_prefix) * 100).toFixed(2)}%
                              </span>
                            )}
                            {mod.tags && mod.tags.length > 0 && (
                              <div className="mod-tags-line" title="Click individual tags to filter">
                                <button
                                  className="apply-all-tags-btn"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    applyAllModTags(mod);
                                  }}
                                  title="Apply all tags as filters"
                                >
                                  ✓✓
                                </button>
                                {mod.tags.map((tag, i) => {
                                  const tagColor = getTagColor(tag)
                                  return (
                                    <span
                                      key={i}
                                      className="mod-tag-text"
                                      data-tag={tag}
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        toggleTagFilter(tag);
                                      }}
                                      title={`Click to filter by "${tag}" tag`}
                                      style={{
                                        background: tagColor.bg,
                                        borderColor: tagColor.border,
                                        color: tagColor.text
                                      }}
                                      onMouseEnter={(e) => {
                                        e.currentTarget.style.background = tagColor.hover
                                      }}
                                      onMouseLeave={(e) => {
                                        e.currentTarget.style.background = tagColor.bg
                                      }}
                                    >
                                      {tag}
                                    </span>
                                  )
                                })}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              <div className="mods-pool-column">
                <h4 className="column-title">Suffixes ({(() => {
                  const counts = countMatchingMods('suffix')
                  return counts.matching === counts.total ? `${counts.total} total` : `${counts.matching}/${counts.total}`
                })()})</h4>
                <div className="mods-pool-list">
                  {/* Normal Suffixes */}
                  {Object.entries(getGroupedMods('suffix')).map(([groupKey, groupMods]) => {
                    const maxIlvl = Math.max(...groupMods.map(m => m.required_ilvl || 1))
                    const unavailableCount = groupMods.filter(m => m.required_ilvl && m.required_ilvl > item.item_level).length
                    const allUnavailable = unavailableCount === groupMods.length
                    const isGroupGreyedOut = shouldGreyOutModGroup(groupMods, 'suffix')
                    const isExpanded = expandedModGroups.has(`suffix-${groupKey}`)

                    // Calculate available tiers (filtered by ilvl)
                    const availableModsInGroup = groupMods.filter(m => !m.required_ilvl || m.required_ilvl <= item.item_level)
                    // Use best available tier for display, fallback to T1 if none available
                    const displayTier = availableModsInGroup.length > 0 ? availableModsInGroup[0] : groupMods[0]
                    const bestAvailableTierNum = availableModsInGroup.length > 0 ? Math.min(...availableModsInGroup.map(m => m.tier)) : null
                    const worstTier = Math.max(...groupMods.map(m => m.tier))
                    const tierRangeText = bestAvailableTierNum ? `T${bestAvailableTierNum}-T${worstTier}` : `T1-T${worstTier}`

                    // Check if any tier in this group has essence guarantees
                    const essenceGuaranteeTiers = groupMods.filter(m =>
                      m.mod_id && availableMods.essence_guarantees[m.mod_id]
                    )
                    const hasAnyEssenceGuarantee = essenceGuaranteeTiers.length > 0

                    return (
                      <div key={groupKey} className={`pool-mod-group ${isGroupGreyedOut ? 'omen-incompatible' : ''}`}>
                        <div
                          className={`pool-mod-group-header suffix compact-single-line ${allUnavailable ? 'all-unavailable' : ''} mod-group-clickable`}
                          onClick={() => toggleModGroup(`suffix-${groupKey}`)}
                          onDoubleClick={() => applyAllModTags(displayTier)}
                          draggable={!allUnavailable && itemCreated}
                          onDragStart={() => handleDragStart(displayTier, 'suffix')}
                          onDragEnd={handleDragEnd}
                          title="Click to expand/collapse, double-click to filter by all tags, drag to add to item"
                        >
                          <span className="pool-mod-stat-main">
                            {formatStatTextWithRanges(displayTier)}
                            {displayTier.exclusion_group_id && (() => {
                              const groupInfo = getModExclusionGroupInfo(displayTier)
                              const groupColor = getExclusionGroupColor(displayTier.exclusion_group_id)
                              const groupNum = exclusionGroupDisplayMap[displayTier.exclusion_group_id] || '?'
                              return (
                                <span
                                  className="exclusion-group-badge"
                                  style={{
                                    background: groupColor.bg,
                                    borderColor: groupColor.border,
                                    color: groupColor.text,
                                    marginLeft: '6px',
                                    padding: '2px 6px',
                                    borderRadius: '3px',
                                    fontSize: '11px',
                                    border: '1px solid',
                                    fontWeight: 'bold',
                                    display: 'inline-block',
                                    minWidth: '18px',
                                    textAlign: 'center'
                                  }}
                                  title={groupInfo?.description || 'Exclusion group'}
                                >
                                  {groupNum}
                                </span>
                              )
                            })()}
                          </span>
                          <div className="compact-mod-info">
                            {unavailableCount > 0 && (
                              <span
                                className="unavailable-indicator"
                                title={`${unavailableCount} unavailable tier${unavailableCount > 1 ? 's' : ''}`}
                              >
                                ⚠
                              </span>
                            )}
                            {hasAnyEssenceGuarantee && (
                              <span
                                className="essence-guarantee-group-indicator"
                                title={`${essenceGuaranteeTiers.length} tier${essenceGuaranteeTiers.length > 1 ? 's' : ''} can be guaranteed by essence`}
                              >
                                ◆
                              </span>
                            )}
                            <span className="group-tier-range">{tierRangeText}</span>
                            <span className="group-max-ilvl">ilvl {maxIlvl}</span>
                            {(() => {
                              // Calculate combined weight of available tiers only (filtered by ilvl)
                              const combinedWeight = availableModsInGroup.reduce((sum, mod) => sum + (mod.weight || 0), 0)
                              return combinedWeight > 0 && totalWeights.suffix > 0 && (
                                <span className="mod-weight" title={`Combined weight: ${combinedWeight} / ${totalWeights.suffix} total (${availableModsInGroup.length} available tiers)`}>
                                  {((combinedWeight / totalWeights.suffix) * 100).toFixed(2)}%
                                </span>
                              )
                            })()}
                            {displayTier.tags && displayTier.tags.length > 0 && (
                              <div className="mod-tags-line" title="Click individual tags to filter">
                                <button
                                  className="apply-all-tags-btn"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    applyAllModTags(displayTier);
                                  }}
                                  title="Apply all tags as filters"
                                >
                                  ✓✓
                                </button>
                                {displayTier.tags.map((tag, i) => {
                                  const tagColor = getTagColor(tag)
                                  return (
                                    <span
                                      key={i}
                                      className="mod-tag-text"
                                      data-tag={tag}
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        toggleTagFilter(tag);
                                      }}
                                      title={`Click to filter by "${tag}" tag`}
                                      style={{
                                        background: tagColor.bg,
                                        borderColor: tagColor.border,
                                        color: tagColor.text
                                      }}
                                      onMouseEnter={(e) => {
                                        e.currentTarget.style.background = tagColor.hover
                                      }}
                                      onMouseLeave={(e) => {
                                        e.currentTarget.style.background = tagColor.bg
                                      }}
                                    >
                                      {tag}
                                    </span>
                                  )
                                })}
                              </div>
                            )}
                          </div>
                        </div>

                        {isExpanded && (
                          <div className="mod-tier-details">
                            {groupMods.map(mod => {
                              // Format the mod text with embedded value ranges
                              let formattedText = mod.stat_text

                              if (mod.stat_ranges && mod.stat_ranges.length > 0) {
                                // Replace each # with the corresponding range in curly braces
                                mod.stat_ranges.forEach(range => {
                                  const rangeText = range.min === range.max
                                    ? `${range.min}`
                                    : `{${range.min}-${range.max}}`
                                  formattedText = formattedText.replace('#', rangeText)
                                })
                              } else if (mod.stat_min !== undefined && mod.stat_max !== undefined) {
                                // Legacy single range
                                const rangeText = mod.stat_min === mod.stat_max
                                  ? `${mod.stat_min}`
                                  : `{${mod.stat_min}-${mod.stat_max}}`
                                formattedText = formattedText.replace('#', rangeText)
                              }

                              const tierPct = mod.weight && totalWeights.suffix > 0
                                ? ((mod.weight / totalWeights.suffix) * 100).toFixed(2)
                                : null

                              // Check if this mod has essence guarantees
                              const essenceGuarantees = mod.mod_id ? availableMods.essence_guarantees[mod.mod_id] : null
                              const hasEssenceGuarantee = essenceGuarantees && essenceGuarantees.length > 0

                              const isUnavailable = mod.required_ilvl && mod.required_ilvl > item.item_level
                              const isDraggable = !isUnavailable && itemCreated

                              return (
                                <div
                                  key={mod.tier}
                                  className={`tier-detail ${isUnavailable ? 'unavailable' : ''} ${hasEssenceGuarantee ? 'has-essence-guarantee' : ''} ${isDraggable ? 'draggable-tier' : ''}`}
                                  draggable={isDraggable}
                                  onDragStart={() => isDraggable && handleDragStart(mod, 'suffix')}
                                  onDragEnd={handleDragEnd}
                                  title={isDraggable ? "Drag to add this specific tier to item" : undefined}
                                >
                                  <span className="tier-label">T{mod.tier}</span>
                                  {hasEssenceGuarantee && (
                                    <span
                                      className="essence-guarantee-indicator"
                                      title={`Guaranteed by: ${[...new Set(essenceGuarantees.map(g => g.essence_name))].join(', ')}`}
                                    >
                                      ◆
                                    </span>
                                  )}
                                  <span className="tier-stat">{formattedText}</span>
                                  <span className="tier-ilvl">ilvl {mod.required_ilvl || 1}</span>
                                  {tierPct && (
                                    <span className="tier-weight" title={`Weight: ${mod.weight} / ${totalWeights.suffix} total`}>
                                      {tierPct}%
                                    </span>
                                  )}
                                </div>
                              )
                            })}
                          </div>
                        )}
                      </div>
                    )
                  })}

                  {/* Essence Suffixes */}
                  {availableMods.essence_suffixes.map((mod, idx) => {
                    const isTagFiltered = activeTagFilters.size > 0 && !isModMatchingTagFilters(mod)
                    const isSearchFiltered = searchQuery.trim() && !isModMatchingSearch(mod)
                    const isOmenIncompatible = shouldGreyOutMod(mod, 'suffix')
                    const isFiltered = isTagFiltered || isSearchFiltered
                    return (
                      <div key={`essence-suffix-${idx}`} className={`pool-mod-group essence-only ${isFiltered ? 'tag-filtered' : ''} ${isOmenIncompatible ? 'omen-incompatible' : ''}`}>
                        <div
                          className="pool-mod-group-header suffix compact-single-line mod-group-clickable"
                          onDoubleClick={() => applyAllModTags(mod)}
                          draggable={itemCreated}
                          onDragStart={() => handleDragStart(mod, 'suffix')}
                          onDragEnd={handleDragEnd}
                          title="Essence-only mod - Double-click to filter by all tags, drag to add to item"
                        >
                          <span className="pool-mod-stat-main">
                            {mod.stat_text}
                            {mod.exclusion_group_id && (() => {
                              const groupInfo = getModExclusionGroupInfo(mod)
                              const groupColor = getExclusionGroupColor(mod.exclusion_group_id)
                              const groupNum = exclusionGroupDisplayMap[mod.exclusion_group_id] || '?'
                              return (
                                <span
                                  className="exclusion-group-badge"
                                  style={{
                                    background: groupColor.bg,
                                    borderColor: groupColor.border,
                                    color: groupColor.text,
                                    marginLeft: '6px',
                                    padding: '2px 6px',
                                    borderRadius: '3px',
                                    fontSize: '11px',
                                    border: '1px solid',
                                    fontWeight: 'bold',
                                    display: 'inline-block',
                                    minWidth: '18px',
                                    textAlign: 'center'
                                  }}
                                  title={groupInfo?.description || 'Exclusion group'}
                                >
                                  {groupNum}
                                </span>
                              )
                            })()}
                          </span>
                          <div className="compact-mod-info">
                            {/* No weight display for essence mods - they're guaranteed outcomes */}
                            {mod.tags && mod.tags.length > 0 && (
                              <div className="mod-tags-line" title="Click individual tags to filter">
                                <button
                                  className="apply-all-tags-btn"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    applyAllModTags(mod);
                                  }}
                                  title="Apply all tags as filters"
                                >
                                  ✓✓
                                </button>
                                {mod.tags.map((tag, i) => {
                                  const tagColor = getTagColor(tag)
                                  return (
                                    <span
                                      key={i}
                                      className="mod-tag-text"
                                      data-tag={tag}
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        toggleTagFilter(tag);
                                      }}
                                      title={`Click to filter by "${tag}" tag`}
                                      style={{
                                        background: tagColor.bg,
                                        borderColor: tagColor.border,
                                        color: tagColor.text
                                      }}
                                      onMouseEnter={(e) => {
                                        e.currentTarget.style.background = tagColor.hover
                                      }}
                                      onMouseLeave={(e) => {
                                        e.currentTarget.style.background = tagColor.bg
                                      }}
                                    >
                                      {tag}
                                    </span>
                                  )
                                })}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })}

                  {/* Desecrated Suffixes */}
                  {availableMods.desecrated_suffixes.map((mod, idx) => {
                    const isTagFiltered = activeTagFilters.size > 0 && !isModMatchingTagFilters(mod)
                    const isSearchFiltered = searchQuery.trim() && !isModMatchingSearch(mod)
                    const isOmenIncompatible = shouldGreyOutMod(mod, 'suffix')
                    const isFiltered = isTagFiltered || isSearchFiltered
                    return (
                      <div key={`desecrated-suffix-${idx}`} className={`pool-mod-group desecrated-only ${isFiltered ? 'tag-filtered' : ''} ${isOmenIncompatible ? 'omen-incompatible' : ''}`}>
                        <div
                          className="pool-mod-group-header suffix compact-single-line mod-group-clickable"
                          onDoubleClick={() => applyAllModTags(mod)}
                          draggable={itemCreated}
                          onDragStart={() => handleDragStart(mod, 'suffix')}
                          onDragEnd={handleDragEnd}
                          title="Desecrated-only mod - Double-click to filter by all tags, drag to add to item"
                        >
                          <span className="pool-mod-stat-main">
                            {mod.stat_text}
                            {mod.exclusion_group_id && (() => {
                              const groupInfo = getModExclusionGroupInfo(mod)
                              const groupColor = getExclusionGroupColor(mod.exclusion_group_id)
                              const groupNum = exclusionGroupDisplayMap[mod.exclusion_group_id] || '?'
                              return (
                                <span
                                  className="exclusion-group-badge"
                                  style={{
                                    background: groupColor.bg,
                                    borderColor: groupColor.border,
                                    color: groupColor.text,
                                    marginLeft: '6px',
                                    padding: '2px 6px',
                                    borderRadius: '3px',
                                    fontSize: '11px',
                                    border: '1px solid',
                                    fontWeight: 'bold',
                                    display: 'inline-block',
                                    minWidth: '18px',
                                    textAlign: 'center'
                                  }}
                                  title={groupInfo?.description || 'Exclusion group'}
                                >
                                  {groupNum}
                                </span>
                              )
                            })()}
                          </span>
                          <div className="compact-mod-info">
                            {mod.weight !== undefined && totalWeights.desecrated_suffix > 0 && (
                              <span className="mod-weight" title={`Weight: ${mod.weight} / ${totalWeights.desecrated_suffix} total`}>
                                {((mod.weight / totalWeights.desecrated_suffix) * 100).toFixed(2)}%
                              </span>
                            )}
                            {mod.tags && mod.tags.length > 0 && (
                              <div className="mod-tags-line" title="Click individual tags to filter">
                                <button
                                  className="apply-all-tags-btn"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    applyAllModTags(mod);
                                  }}
                                  title="Apply all tags as filters"
                                >
                                  ✓✓
                                </button>
                                {mod.tags.map((tag, i) => {
                                  const tagColor = getTagColor(tag)
                                  return (
                                    <span
                                      key={i}
                                      className="mod-tag-text"
                                      data-tag={tag}
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        toggleTagFilter(tag);
                                      }}
                                      title={`Click to filter by "${tag}" tag`}
                                      style={{
                                        background: tagColor.bg,
                                        borderColor: tagColor.border,
                                        color: tagColor.text
                                      }}
                                      onMouseEnter={(e) => {
                                        e.currentTarget.style.background = tagColor.hover
                                      }}
                                      onMouseLeave={(e) => {
                                        e.currentTarget.style.background = tagColor.bg
                                      }}
                                    >
                                      {tag}
                                    </span>
                                  )
                                })}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>

            {/* Essence-Only Modifiers Section - HIDDEN NOW */}
            {(availableMods.essence_prefixes.length > 0 || availableMods.essence_suffixes.length > 0) && (
              <div className="special-mods-section essence-section">
                <h4 className="special-section-title">
                  Essence-Only Modifiers ({availableMods.essence_prefixes.length + availableMods.essence_suffixes.length} total)
                </h4>
                <div className="special-mods-columns">
                  <div className="special-mods-column">
                    <h5 className="special-column-title">Essence Prefixes ({availableMods.essence_prefixes.length})</h5>
                    <div className="mods-pool-list">
                      {availableMods.essence_prefixes.map((mod, idx) => {
                        const isTagFiltered = activeTagFilters.size > 0 && !isModMatchingTagFilters(mod)
                        return (
                        <div key={`essence-prefix-${idx}`} className={`pool-mod-group essence-only ${isTagFiltered ? 'tag-filtered' : ''}`}>
                          <div
                            className="pool-mod-group-header essence prefix compact-single-line mod-group-clickable"
                            onDoubleClick={() => applyAllModTags(mod)}
                            draggable={itemCreated}
                            onDragStart={() => handleDragStart(mod, 'prefix')}
                            onDragEnd={handleDragEnd}
                            title="Double-click to filter by all tags, drag to add to item"
                          >
                            <span className="pool-mod-stat-main">{mod.stat_text}</span>
                            {mod.tags && mod.tags.length > 0 && (
                              <div className="mod-tags-line" title="Click individual tags to filter">
                                <button
                                  className="apply-all-tags-btn"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    applyAllModTags(mod);
                                  }}
                                  title="Apply all tags as filters"
                                >
                                  ✓✓
                                </button>
                                {mod.tags.map((tag, i) => {
                                  const tagColor = getTagColor(tag)
                                  return (
                                    <span
                                      key={i}
                                      className="mod-tag-text"
                                      data-tag={tag}
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        toggleTagFilter(tag);
                                      }}
                                      title={`Click to filter by "${tag}" tag`}
                                      style={{
                                        background: tagColor.bg,
                                        borderColor: tagColor.border,
                                        color: tagColor.text
                                      }}
                                      onMouseEnter={(e) => {
                                        e.currentTarget.style.background = tagColor.hover
                                      }}
                                      onMouseLeave={(e) => {
                                        e.currentTarget.style.background = tagColor.bg
                                      }}
                                    >
                                      {tag}
                                    </span>
                                  )
                                })}
                              </div>
                            )}
                          </div>
                        </div>
                        )
                      })}
                    </div>
                  </div>

                  <div className="special-mods-column">
                    <h5 className="special-column-title">Essence Suffixes ({availableMods.essence_suffixes.length})</h5>
                    <div className="mods-pool-list">
                      {availableMods.essence_suffixes.map((mod, idx) => {
                        const isTagFiltered = activeTagFilters.size > 0 && !isModMatchingTagFilters(mod)
                        return (
                        <div key={`essence-suffix-${idx}`} className={`pool-mod-group essence-only ${isTagFiltered ? 'tag-filtered' : ''}`}>
                          <div
                            className="pool-mod-group-header essence suffix compact-single-line mod-group-clickable"
                            onDoubleClick={() => applyAllModTags(mod)}
                            draggable={itemCreated}
                            onDragStart={() => handleDragStart(mod, 'suffix')}
                            onDragEnd={handleDragEnd}
                            title="Double-click to filter by all tags, drag to add to item"
                          >
                            <span className="pool-mod-stat-main">{mod.stat_text}</span>
                            {mod.tags && mod.tags.length > 0 && (
                              <div className="mod-tags-line" title="Click individual tags to filter">
                                <button
                                  className="apply-all-tags-btn"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    applyAllModTags(mod);
                                  }}
                                  title="Apply all tags as filters"
                                >
                                  ✓✓
                                </button>
                                {mod.tags.map((tag, i) => {
                                  const tagColor = getTagColor(tag)
                                  return (
                                    <span
                                      key={i}
                                      className="mod-tag-text"
                                      data-tag={tag}
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        toggleTagFilter(tag);
                                      }}
                                      title={`Click to filter by "${tag}" tag`}
                                      style={{
                                        background: tagColor.bg,
                                        borderColor: tagColor.border,
                                        color: tagColor.text
                                      }}
                                      onMouseEnter={(e) => {
                                        e.currentTarget.style.background = tagColor.hover
                                      }}
                                      onMouseLeave={(e) => {
                                        e.currentTarget.style.background = tagColor.bg
                                      }}
                                    >
                                      {tag}
                                    </span>
                                  )
                                })}
                              </div>
                            )}
                          </div>
                        </div>
                        )
                      })}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Desecrated-Only Modifiers Section */}
            {(availableMods.desecrated_prefixes.length > 0 || availableMods.desecrated_suffixes.length > 0) && (
              <div className="special-mods-section desecrated-section">
                <h4 className="special-section-title">
                  Desecrated-Only Modifiers ({availableMods.desecrated_prefixes.length + availableMods.desecrated_suffixes.length} total)
                </h4>
                <div className="special-mods-columns">
                  <div className="special-mods-column">
                    <h5 className="special-column-title">Desecrated Prefixes ({availableMods.desecrated_prefixes.length})</h5>
                    <div className="mods-pool-list">
                      {availableMods.desecrated_prefixes.map((mod, idx) => {
                        const isTagFiltered = activeTagFilters.size > 0 && !isModMatchingTagFilters(mod)
                        return (
                        <div key={`desecrated-prefix-${idx}`} className={`pool-mod-group desecrated-only ${isTagFiltered ? 'tag-filtered' : ''}`}>
                          <div
                            className="pool-mod-group-header desecrated prefix compact-single-line mod-group-clickable"
                            onDoubleClick={() => applyAllModTags(mod)}
                            draggable={itemCreated}
                            onDragStart={() => handleDragStart(mod, 'prefix')}
                            onDragEnd={handleDragEnd}
                            title="Double-click to filter by all tags, drag to add to item"
                          >
                            <span className="pool-mod-stat-main">{mod.stat_text}</span>
                            {mod.tags && mod.tags.length > 0 && (
                              <div className="mod-tags-line" title="Click individual tags to filter">
                                <button
                                  className="apply-all-tags-btn"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    applyAllModTags(mod);
                                  }}
                                  title="Apply all tags as filters"
                                >
                                  ✓✓
                                </button>
                                {mod.tags.map((tag, i) => {
                                  const tagColor = getTagColor(tag)
                                  return (
                                    <span
                                      key={i}
                                      className="mod-tag-text"
                                      data-tag={tag}
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        toggleTagFilter(tag);
                                      }}
                                      title={`Click to filter by "${tag}" tag`}
                                      style={{
                                        background: tagColor.bg,
                                        borderColor: tagColor.border,
                                        color: tagColor.text
                                      }}
                                      onMouseEnter={(e) => {
                                        e.currentTarget.style.background = tagColor.hover
                                      }}
                                      onMouseLeave={(e) => {
                                        e.currentTarget.style.background = tagColor.bg
                                      }}
                                    >
                                      {tag}
                                    </span>
                                  )
                                })}
                              </div>
                            )}
                          </div>
                        </div>
                        )
                      })}
                    </div>
                  </div>

                  <div className="special-mods-column">
                    <h5 className="special-column-title">Desecrated Suffixes ({availableMods.desecrated_suffixes.length})</h5>
                    <div className="mods-pool-list">
                      {availableMods.desecrated_suffixes.map((mod, idx) => {
                        const isTagFiltered = activeTagFilters.size > 0 && !isModMatchingTagFilters(mod)
                        return (
                        <div key={`desecrated-suffix-${idx}`} className={`pool-mod-group desecrated-only ${isTagFiltered ? 'tag-filtered' : ''}`}>
                          <div
                            className="pool-mod-group-header desecrated suffix compact-single-line mod-group-clickable"
                            onDoubleClick={() => applyAllModTags(mod)}
                            draggable={itemCreated}
                            onDragStart={() => handleDragStart(mod, 'suffix')}
                            onDragEnd={handleDragEnd}
                            title="Double-click to filter by all tags, drag to add to item"
                          >
                            <span className="pool-mod-stat-main">{mod.stat_text}</span>
                            {mod.tags && mod.tags.length > 0 && (
                              <div className="mod-tags-line" title="Click individual tags to filter">
                                <button
                                  className="apply-all-tags-btn"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    applyAllModTags(mod);
                                  }}
                                  title="Apply all tags as filters"
                                >
                                  ✓✓
                                </button>
                                {mod.tags.map((tag, i) => {
                                  const tagColor = getTagColor(tag)
                                  return (
                                    <span
                                      key={i}
                                      className="mod-tag-text"
                                      data-tag={tag}
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        toggleTagFilter(tag);
                                      }}
                                      title={`Click to filter by "${tag}" tag`}
                                      style={{
                                        background: tagColor.bg,
                                        borderColor: tagColor.border,
                                        color: tagColor.text
                                      }}
                                      onMouseEnter={(e) => {
                                        e.currentTarget.style.background = tagColor.hover
                                      }}
                                      onMouseLeave={(e) => {
                                        e.currentTarget.style.background = tagColor.bg
                                      }}
                                    >
                                      {tag}
                                    </span>
                                  )
                                })}
                              </div>
                            )}
                          </div>
                        </div>
                        )
                      })}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Center Panel - Item Display with Tabs */}
        <div className="center-panel">
          <div className="tabbed-interface">
            <div className="tab-headers">
              <button
                className={`tab-header ${activeTab === 'item' ? 'active' : ''}`}
                onClick={() => setActiveTab('item')}
              >
                🛡️ Item
              </button>
              <button
                className={`tab-header ${activeTab === 'history' ? 'active' : ''}`}
                onClick={() => setActiveTab('history')}
              >
                📜 History ({history.length})
              </button>
              <button
                className={`tab-header ${activeTab === 'currency' ? 'active' : ''}`}
                onClick={() => setActiveTab('currency')}
              >
                💰 Currency ({Object.keys(currencySpent).length})
              </button>
            </div>

            <div className="tab-content-area">
              {activeTab === 'item' && (
                <div className="item-display-container">
                  {!itemCreated ? (
                    // Show creation options when no item has been created
                    <ItemTab {...tabContentProps} />
                  ) : (
                    // Show sophisticated item preview after creation
                    <div className="item-created-view">
                      {/* Compact Value Bar - Cost & Price */}
                      <div className="item-value-bar">
                        <div className="value-section cost-section">
                          <span className="value-label">Cost:</span>
                          {Object.keys(currencySpent).length > 0 ? (
                            <span className="value-amount cost-with-icon">
                              {(() => {
                                let totalExalted = 0
                                let unpricedCount = 0
                                for (const [currency, count] of Object.entries(currencySpent)) {
                                  // Try to find rate with various normalizations
                                  let rate = null
                                  if (exchangeRates) {
                                    // API stores by lowercase display name (e.g., "greater essence of abrasion")
                                    // and by dash-separated name (e.g., "greater-essence-of-abrasion")
                                    const lowerCurrency = currency.toLowerCase()
                                    const dashName = lowerCurrency.replace(/ /g, '-')
                                    // For basic orbs, try without "Orb of" prefix
                                    const basicOrbName = lowerCurrency
                                      .replace(/^orb of /, '')
                                      .replace(/ orb$/, '')

                                    rate = exchangeRates.rates[lowerCurrency]  // "greater essence of abrasion"
                                      || exchangeRates.rates[dashName]         // "greater-essence-of-abrasion"
                                      || exchangeRates.rates[basicOrbName]     // "exalted", "divine" etc
                                      || Object.values(exchangeRates.rates).find(r =>
                                          r.name.toLowerCase() === lowerCurrency
                                        )
                                  }
                                  if (rate) {
                                    totalExalted += count * rate.exalted_value
                                  } else {
                                    unpricedCount += count
                                  }
                                }

                                // Calculate divine equivalent
                                const divineRate = exchangeRates?.rates['divine']?.exalted_value || 0
                                const totalDivine = divineRate > 0 ? totalExalted / divineRate : 0

                                // Dynamic display: show divine if >= 1, else exalted
                                if (totalExalted > 0) {
                                  const suffix = unpricedCount > 0 ? ` + ${unpricedCount} other` : ''
                                  if (totalDivine >= 1) {
                                    return (
                                      <>
                                        <img
                                          src="https://www.poe2wiki.net/images/5/58/Divine_Orb_inventory_icon.png"
                                          alt="div"
                                          className="cost-inline-icon"
                                        />
                                        {totalDivine.toFixed(2)} div{suffix}
                                      </>
                                    )
                                  }
                                  return (
                                    <>
                                      <img
                                        src="https://www.poe2wiki.net/images/2/26/Exalted_Orb_inventory_icon.png"
                                        alt="ex"
                                        className="cost-inline-icon"
                                      />
                                      {totalExalted.toFixed(2)} ex{suffix}
                                    </>
                                  )
                                }
                                return `${Object.values(currencySpent).reduce((a, b) => a + b, 0)} items`
                              })()}
                            </span>
                          ) : (
                            <span className="value-amount dim">0 ex</span>
                          )}
                        </div>
                        <div className="value-section price-section">
                          <span className="value-label">Worth:</span>
                          {itemPrice ? (
                            <span
                              className={`value-amount clickable ${itemPrice.confidence}`}
                              onClick={openPriceModal}
                              title="Click to view price details"
                            >
                              {formatPriceDisplay(itemPrice.median_price)}
                            </span>
                          ) : (
                            <button
                              className="mini-price-btn"
                              onClick={openPriceModal}
                              disabled={item.prefix_mods.length === 0 && item.suffix_mods.length === 0}
                              title="Check market value"
                            >
                              ?
                            </button>
                          )}
                          {itemPrice && (
                            <>
                              <button
                                className="mini-price-btn refresh"
                                onClick={() => {
                                  if (priceModalOpen) {
                                    // Modal already open - trigger refresh directly
                                    priceFlyoutRef.current?.handlePriceCheck(true)
                                  } else {
                                    // Open modal (which auto-starts search)
                                    openPriceModal()
                                  }
                                }}
                                disabled={priceFlyoutRef.current?.priceCheckLoading}
                                title="Refresh price"
                              >
                                ↻
                              </button>
                              {itemPrice.num_listings > 0 && (
                                <button
                                  className="mini-price-btn view"
                                  onClick={openPriceModal}
                                  title="View price results"
                                >
                                  📋
                                </button>
                              )}
                            </>
                          )}
                        </div>
                      </div>

                      <div className="current-item-display">
                    <PoE2ItemFrame
                      rarity={item.rarity}
                      itemName={item.base_name}
                      itemBase={item.rarity === 'Rare' ? item.base_category?.replace('_', ' ') : undefined}
                      onDrop={handleDrop}
                      onDragOver={handleDragOver}
                      className="item-display-frame"
                      headerActions={
                        <>
                          <span className="poe2-rarity-badge">{item.rarity}</span>
                          <button
                            className="copy-item-btn"
                            onClick={(e) => handleCopyItem(e.ctrlKey ? 'detailed' : 'simple')}
                            title="Copy item to clipboard&#10;Click = Simple format&#10;Ctrl+Click = Detailed format (with mod info)"
                          >
                            Copy
                          </button>
                        </>
                      }
                    >
                      {/* Item Properties */}
                      <PoE2Section>
                        <div
                          className={`price-filter-property ${priceModalOpen ? (priceRarityEnabled ? 'filter-enabled' : 'filter-disabled') : ''}`}
                          onClick={() => priceModalOpen && setPriceRarityEnabled(prev => !prev)}
                          style={{ cursor: priceModalOpen ? 'pointer' : 'default' }}
                          title={priceModalOpen ? (priceRarityEnabled ? 'Click to exclude rarity from search' : 'Click to include rarity in search') : ''}
                        >
                          <PoE2Property label="Rarity" value={item.rarity} />
                        </div>
                        <div
                          className={`price-filter-property ${priceModalOpen ? (priceIlvlEnabled ? 'filter-enabled' : 'filter-disabled') : ''}`}
                          onClick={() => priceModalOpen && setPriceIlvlEnabled(prev => !prev)}
                          style={{ cursor: priceModalOpen ? 'pointer' : 'default' }}
                          title={priceModalOpen ? (priceIlvlEnabled ? 'Click to exclude item level from search' : 'Click to include item level in search (min ilvl)') : ''}
                        >
                          <PoE2Property label="Item Level" value={item.item_level} />
                        </div>
                        {item.quality > 0 && (
                          <PoE2Property label="Quality" value={`+${item.quality}%`} augmented />
                        )}
                        {item.catalyst_type && item.catalyst_quality && item.catalyst_quality > 0 && (
                          <PoE2Property
                            label={`Quality (${getCatalystDisplayName(item.catalyst_type)})`}
                            value={`+${item.catalyst_quality}%`}
                            augmented
                          />
                        )}
                      </PoE2Section>

                      {/* Weapon Stats - Two Column Layout */}
                      {item.calculated_stats?.PhysicalDPS != null && (
                        <>
                          <PoE2Separator />
                          <PoE2Section title="Weapon">
                            <PoE2TwoColumn gap="small">
                              <PoE2Column>
                                {item.calculated_stats.PhysicalMin != null && item.calculated_stats.PhysicalMax != null && (
                                  <PoE2Property
                                    label="Phys"
                                    value={`${item.calculated_stats.PhysicalMin}-${item.calculated_stats.PhysicalMax}`}
                                    augmented
                                  />
                                )}
                                {item.calculated_stats.CritChance != null && (
                                  <PoE2Property
                                    label="Crit"
                                    value={`${item.calculated_stats.CritChance}%`}
                                  />
                                )}
                                {item.calculated_stats.AttackRate != null && (
                                  <PoE2Property
                                    label="APS"
                                    value={item.calculated_stats.AttackRate}
                                    augmented
                                  />
                                )}
                              </PoE2Column>
                              <PoE2Column align="right">
                                <PoE2Property
                                  label="pDPS"
                                  value={item.calculated_stats.PhysicalDPS}
                                  highlight
                                />
                                {item.calculated_stats.ElementalDPS != null && item.calculated_stats.ElementalDPS > 0 && (
                                  <PoE2Property
                                    label="eDPS"
                                    value={item.calculated_stats.ElementalDPS}
                                    highlight
                                  />
                                )}
                                {item.calculated_stats.TotalDPS != null &&
                                 (item.calculated_stats.ElementalDPS > 0 || item.calculated_stats.ChaosDPS > 0) && (
                                  <PoE2Property
                                    label="Total"
                                    value={item.calculated_stats.TotalDPS}
                                    highlight
                                  />
                                )}
                              </PoE2Column>
                            </PoE2TwoColumn>
                          </PoE2Section>
                        </>
                      )}

                      {/* Defense Stats */}
                      {(item.calculated_stats?.Armour > 0 ||
                        item.calculated_stats?.Evasion > 0 ||
                        item.calculated_stats?.EnergyShield > 0) && (
                        <>
                          <PoE2Separator />
                          <PoE2Section title="Defense">
                            {item.calculated_stats?.Armour > 0 && (
                              <PoE2Property label="Armour" value={item.calculated_stats.Armour} />
                            )}
                            {item.calculated_stats?.Evasion > 0 && (
                              <PoE2Property label="Evasion Rating" value={item.calculated_stats.Evasion} />
                            )}
                            {item.calculated_stats?.EnergyShield > 0 && (
                              <PoE2Property label="Energy Shield" value={item.calculated_stats.EnergyShield} />
                            )}
                          </PoE2Section>
                        </>
                      )}

                      {/* Socketed Runes */}
                      {item.socketed_runes && item.socketed_runes.length > 0 && (
                        <>
                          <PoE2Separator />
                          <PoE2Section title={item.socketed_runes[0]?.name || 'Rune'}>
                            {item.socketed_runes.map((rune, runeIdx) => (
                              <div key={runeIdx}>
                                {/* Regular rune mods */}
                                {rune.mods.map((modText, modIdx) => (
                                  <div key={`rune-${runeIdx}-mod-${modIdx}`} className="mod-line rune">
                                    <div className="mod-content">
                                      <div className="mod-stat">{modText}</div>
                                      <div className="mod-metadata">
                                        <span className="mod-tier">rune</span>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                                {/* Bonded mods (class-specific) */}
                                {rune.bonded_mods && rune.bonded_mods.map((modText, modIdx) => (
                                  <div key={`rune-${runeIdx}-bonded-${modIdx}`} className="mod-line rune bonded">
                                    <div className="mod-content">
                                      <div className="mod-stat">{modText}</div>
                                      <div className="mod-metadata">
                                        <span className="mod-tier">bonded</span>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            ))}
                          </PoE2Section>
                        </>
                      )}

                      {/* Prefix Mods */}
                      {item.prefix_mods.length > 0 && (
                        <>
                        <PoE2Separator />
                        <div className="mods-section">
                          <h4 className="mods-title">Prefixes ({item.prefix_mods.length}/3)</h4>
                          {item.prefix_mods.map((mod, idx) => {
                            const isTagFiltered = activeTagFilters.size > 0 && !isModMatchingTagFilters(mod)
                            const isDesecrated = mod.is_desecrated === true
                            const isUnrevealed = mod.is_unrevealed === true
                            const isFractured = mod.is_fractured === true
                            const isPriceSelected = isModSelectedForPriceSearch('prefix', idx)
                            // Only show price selection styling when price panel is open
                            const priceClass = priceModalOpen ? (isPriceSelected ? 'price-selected' : 'price-excluded') : ''
                            // Check if this mod is part of a pseudo stat (prefix index = idx in combined array)
                            const isPseudoContributing = priceModalOpen && itemPrice?.pseudo_stats?.some(
                              ps => ps.contributing_mod_indices.includes(idx)
                            )
                            const modClasses = `mod-line prefix ${isTagFiltered ? 'tag-filtered' : ''} ${isDesecrated ? 'desecrated' : ''} ${isUnrevealed ? 'unrevealed' : ''} ${isFractured ? 'fractured' : ''} ${priceClass} ${isPseudoContributing ? 'pseudo-contributing' : ''}`

                            // Get unrevealed metadata if this is an unrevealed mod
                            const unrevealedMetadata = isUnrevealed && mod.unrevealed_id
                              ? item.unrevealed_mods.find(um => um.id === mod.unrevealed_id)
                              : null

                            const handleModClick = () => {
                              if (isUnrevealed && mod.unrevealed_id) {
                                handleClickUnrevealedMod(mod.unrevealed_id!)
                              } else if (priceModalOpen) {
                                // Only toggle price selection when panel is open
                                togglePriceSearchMod('prefix', idx)
                              }
                            }

                            // Only show price tooltip when panel is open
                            const getModTitle = () => {
                              if (isUnrevealed) return 'Click to reveal this modifier'
                              if (priceModalOpen) {
                                const minVal = priceModMinValues[`prefix-${idx}`] ?? 0
                                const currentVal = mod.current_values?.[0] ?? mod.current_value ?? 0
                                const minInfo = currentVal > 0 ? ` (searching min: ${minVal})` : ''
                                return isPriceSelected ? `Click to exclude${minInfo}` : 'Click to include in price search'
                              }
                              return ''
                            }

                            return (
                              <div
                                key={idx}
                                className={modClasses}
                                onClick={handleModClick}
                                style={{ cursor: priceModalOpen || isUnrevealed ? 'pointer' : 'default' }}
                                title={getModTitle()}
                              >
                                <div className="mod-content">
                                  {/* Tier indicator on the left - P for prefix */}
                                  <span className={`mod-tier-indicator ${isUnrevealed ? 'unrevealed-tier' : 'prefix-tier'}`}>
                                    {isUnrevealed ? '?' : `P${mod.tier}`}
                                  </span>
                                  <div className="mod-text-container">
                                    <span className="mod-stat">
                                      {renderModifier(mod)}
                                      {unrevealedMetadata?.required_boss_tag && (
                                        <span className="boss-tag-indicator">
                                          {unrevealedMetadata.required_boss_tag === 'ulaman' && ' 🔱'}
                                          {unrevealedMetadata.required_boss_tag === 'amanamu' && ' 👑'}
                                          {unrevealedMetadata.required_boss_tag === 'kurgal' && ' 🩸'}
                                        </span>
                                      )}
                                      {isUnrevealed && selectedOmens.some(omen => omen.includes('Abyssal Echoes')) && <span className="abyssal-indicator"> ✨</span>}
                                      {/* Tags inline after mod text - hidden by default, show on hover */}
                                      {!isUnrevealed && (() => {
                                        const visibleTags = filterInternalTags(mod.tags)
                                        return visibleTags.length > 0 && (
                                          <>
                                            <span className="mod-tags-collapsed" title={`Tags: ${visibleTags.join(', ')}`}>
                                              [{visibleTags.length}]
                                            </span>
                                            <span className="mod-tags-inline">
                                              {visibleTags.map((tag, i) => {
                                                const tagColor = getTagColor(tag)
                                                return (
                                                  <span
                                                    key={i}
                                                    className="mod-tag-badge"
                                                    onClick={(e) => {
                                                      e.stopPropagation();
                                                      toggleTagFilter(tag);
                                                    }}
                                                    title={`Click to filter by "${tag}" tag`}
                                                    style={{
                                                      background: tagColor.bg,
                                                      borderColor: tagColor.border,
                                                      color: tagColor.text
                                                    }}
                                                    onMouseEnter={(e) => {
                                                      e.currentTarget.style.background = tagColor.hover
                                                    }}
                                                    onMouseLeave={(e) => {
                                                      e.currentTarget.style.background = tagColor.bg
                                                    }}
                                                  >
                                                    {tag}
                                                  </span>
                                                )
                                              })}
                                            </span>
                                          </>
                                        )
                                      })()}
                                    </span>
                                    {isUnrevealed && (
                                      <div className="mod-metadata">
                                        <span className="mod-tier">{unrevealedMetadata?.bone_type} {unrevealedMetadata?.bone_part}</span>
                                      </div>
                                    )}
                                  </div>
                                </div>
                                {/* Min value slider for price search */}
                                {priceModalOpen && isPriceSelected && !isUnrevealed && (
                                  <div className="mod-min-slider" onClick={(e) => e.stopPropagation()}>
                                    <span className="slider-label">Min:</span>
                                    <input
                                      type="range"
                                      min={0}
                                      max={(() => {
                                        // For 2-value mods (damage ranges), use average of rolled values
                                        if (mod.current_values && mod.current_values.length === 2) {
                                          return Math.floor((mod.current_values[0] + mod.current_values[1]) / 2)
                                        }
                                        // For single value mods, use the rolled value
                                        return mod.current_values?.[0] ?? mod.current_value ?? mod.stat_max ?? 100
                                      })()}
                                      value={priceModMinValues[`prefix-${idx}`] ?? 0}
                                      onChange={(e) => {
                                        setPriceModMinValues(prev => ({
                                          ...prev,
                                          [`prefix-${idx}`]: parseInt(e.target.value)
                                        }))
                                      }}
                                      className="min-value-slider"
                                    />
                                    <span className="slider-value">{priceModMinValues[`prefix-${idx}`] ?? 0}</span>
                                  </div>
                                )}
                                <button
                                  className="mod-remove-btn"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleRemoveMod(idx, 'prefix')
                                  }}
                                  title="Remove this modifier"
                                >
                                  ✕
                                </button>
                              </div>
                            )
                          })}
                        </div>
                        </>
                      )}

                      {/* Suffix Mods */}
                      {item.suffix_mods.length > 0 && (
                        <>
                        <PoE2Separator />
                        <div className="mods-section">
                          <h4 className="mods-title">Suffixes ({item.suffix_mods.length}/3)</h4>

                          {/* Compute which suffix mods contribute to pseudo stats (for visual indication) */}
                          {(() => {
                            const suffixPseudoStats: NonNullable<typeof itemPrice>['pseudo_stats'] = []
                            if (priceModalOpen && itemPrice?.pseudo_stats) {
                              itemPrice.pseudo_stats.forEach(ps => {
                                // Check if this pseudo has suffix contributors
                                const suffixContributors = ps.contributing_mod_indices.filter(
                                  i => i >= item.prefix_mods.length
                                )
                                if (suffixContributors.length > 0) {
                                  suffixPseudoStats.push(ps)
                                }
                              })
                            }

                            return (
                              <>
                                {/* Show pseudo stats that replace hidden mods */}
                                {suffixPseudoStats.map((ps, psIdx) => {
                                  const isEnabled = usePseudoStats[ps.stat_id] ?? true
                                  const pseudoKey = `pseudo-${ps.stat_id}`
                                  const currentMinValue = priceModMinValues[pseudoKey] ?? Math.floor(ps.total_value * 0.8)
                                  return (
                                    <div
                                      key={`pseudo-${psIdx}`}
                                      className={`mod-line suffix pseudo-stat-row ${isEnabled ? 'price-selected' : 'price-excluded'}`}
                                    >
                                      <div
                                        className="mod-content"
                                        onClick={() => {
                                          setUsePseudoStats(prev => ({
                                            ...prev,
                                            [ps.stat_id]: !(prev[ps.stat_id] ?? true)
                                          }))
                                          setFiltersChanged(true)
                                        }}
                                        style={{ cursor: 'pointer' }}
                                        title={isEnabled ? 'Using aggregated total - click to use individual mods' : 'Using individual mods - click to use aggregated total'}
                                      >
                                        <span className={`mod-tier-indicator pseudo-tier`}>
                                          Σ
                                        </span>
                                        <div className="mod-text-container">
                                          <span className="mod-stat pseudo-stat-text">
                                            {Math.floor(ps.total_value)}% {ps.display_name}
                                          </span>
                                        </div>
                                      </div>
                                      {/* Min value slider for pseudo stat */}
                                      {isEnabled && (
                                        <div className="mod-min-slider" onClick={(e) => e.stopPropagation()}>
                                          <span className="slider-label">Min:</span>
                                          <input
                                            type="range"
                                            min={0}
                                            max={Math.floor(ps.total_value)}
                                            value={currentMinValue}
                                            onChange={(e) => {
                                              setPriceModMinValues(prev => ({
                                                ...prev,
                                                [pseudoKey]: parseInt(e.target.value)
                                              }))
                                            }}
                                            className="min-value-slider"
                                          />
                                          <span className="slider-value">{currentMinValue}</span>
                                        </div>
                                      )}
                                    </div>
                                  )
                                })}

                                {/* Compute hidden suffix indices (contributing to enabled pseudo stats) */}
                                {(() => {
                                  const hiddenSuffixIndices = new Set<number>()
                                  if (priceModalOpen && suffixPseudoStats.length > 0) {
                                    suffixPseudoStats.forEach(ps => {
                                      const isEnabled = usePseudoStats[ps.stat_id] ?? true
                                      if (isEnabled) {
                                        ps.contributing_mod_indices.forEach(i => {
                                          const suffixIdx = i - item.prefix_mods.length
                                          if (suffixIdx >= 0) {
                                            hiddenSuffixIndices.add(suffixIdx)
                                          }
                                        })
                                      }
                                    })
                                  }
                                  const hiddenModsCount = hiddenSuffixIndices.size

                                  return (
                                    <>
                                      {/* Show/Hide Hidden Mods toggle */}
                                      {hiddenModsCount > 0 && (
                                        <div
                                          className="hidden-mods-toggle"
                                          onClick={() => setPseudoStatsExpanded(!pseudoStatsExpanded)}
                                        >
                                          <span className="toggle-icon">{pseudoStatsExpanded ? '▼' : '▶'}</span>
                                          <span className="toggle-text">
                                            {pseudoStatsExpanded ? 'Hide' : 'Show'} {hiddenModsCount} hidden mod{hiddenModsCount > 1 ? 's' : ''}
                                          </span>
                                        </div>
                                      )}

                                      {/* Render suffix mods - hide those covered by enabled pseudo stats unless expanded */}
                                      {item.suffix_mods.map((mod, idx) => {
                                        const isHiddenMod = hiddenSuffixIndices.has(idx)
                                        const isHidden = isHiddenMod && !pseudoStatsExpanded
                                        if (isHidden) return null

                                        const isTagFiltered = activeTagFilters.size > 0 && !isModMatchingTagFilters(mod)
                                        const isDesecrated = mod.is_desecrated === true
                                        const isUnrevealed = mod.is_unrevealed === true
                                        const isFractured = mod.is_fractured === true
                                        const isPriceSelected = isModSelectedForPriceSearch('suffix', idx)
                                        // Hidden mods: show as crossed out unless user explicitly enabled them
                                        const modKey = `suffix-${idx}`
                                        const isHiddenModEnabled = enabledHiddenMods.has(modKey)
                                        const effectivelySelected = isHiddenMod ? isHiddenModEnabled : isPriceSelected
                                        const priceClass = priceModalOpen ? (effectivelySelected ? 'price-selected' : 'price-excluded') : ''
                                        const modClasses = `mod-line suffix ${isTagFiltered ? 'tag-filtered' : ''} ${isDesecrated ? 'desecrated' : ''} ${isUnrevealed ? 'unrevealed' : ''} ${isFractured ? 'fractured' : ''} ${priceClass} ${isHiddenMod ? 'hidden-mod-revealed' : ''}`

                            // Get unrevealed metadata if this is an unrevealed mod
                            const unrevealedMetadata = isUnrevealed && mod.unrevealed_id
                              ? item.unrevealed_mods.find(um => um.id === mod.unrevealed_id)
                              : null

                            const handleModClick = () => {
                              if (isUnrevealed && mod.unrevealed_id) {
                                handleClickUnrevealedMod(mod.unrevealed_id!)
                              } else if (priceModalOpen) {
                                if (isHiddenMod) {
                                  // Toggle in/out of enabledHiddenMods
                                  setEnabledHiddenMods(prev => {
                                    const newSet = new Set(prev)
                                    if (newSet.has(modKey)) {
                                      newSet.delete(modKey)
                                    } else {
                                      newSet.add(modKey)
                                    }
                                    return newSet
                                  })
                                  setFiltersChanged(true)
                                } else {
                                  // Regular mod - toggle price selection
                                  togglePriceSearchMod('suffix', idx)
                                }
                              }
                            }

                            // Only show price tooltip when panel is open
                            const getModTitle = () => {
                              if (isUnrevealed) return 'Click to reveal this modifier'
                              if (priceModalOpen) {
                                const minVal = priceModMinValues[modKey] ?? 0
                                const currentVal = mod.current_values?.[0] ?? mod.current_value ?? 0
                                const minInfo = currentVal > 0 ? ` (searching min: ${minVal})` : ''
                                if (isHiddenMod) {
                                  // Hidden mod - explain it's alongside pseudo
                                  return isHiddenModEnabled
                                    ? `Click to disable - currently searching WITH pseudo${minInfo}`
                                    : 'Click to also require this mod (in addition to pseudo total)'
                                }
                                return isPriceSelected ? `Click to exclude${minInfo}` : 'Click to include in price search'
                              }
                              return ''
                            }

                            return (
                              <div
                                key={idx}
                                className={modClasses}
                                onClick={handleModClick}
                                style={{ cursor: priceModalOpen || isUnrevealed ? 'pointer' : 'default' }}
                                title={getModTitle()}
                              >
                                <div className="mod-content">
                                  {/* Tier indicator on the left - S for suffix */}
                                  <span className={`mod-tier-indicator ${isUnrevealed ? 'unrevealed-tier' : 'suffix-tier'}`}>
                                    {isUnrevealed ? '?' : `S${mod.tier}`}
                                  </span>
                                  <div className="mod-text-container">
                                    <span className="mod-stat">
                                      {renderModifier(mod)}
                                      {unrevealedMetadata?.required_boss_tag && (
                                        <span className="boss-tag-indicator">
                                          {unrevealedMetadata.required_boss_tag === 'ulaman' && ' 🔱'}
                                          {unrevealedMetadata.required_boss_tag === 'amanamu' && ' 👑'}
                                          {unrevealedMetadata.required_boss_tag === 'kurgal' && ' 🩸'}
                                        </span>
                                      )}
                                      {isUnrevealed && selectedOmens.some(omen => omen.includes('Abyssal Echoes')) && <span className="abyssal-indicator"> ✨</span>}
                                      {/* Tags inline after mod text - hidden by default, show on hover */}
                                      {!isUnrevealed && (() => {
                                        const visibleTags = filterInternalTags(mod.tags)
                                        return visibleTags.length > 0 && (
                                          <>
                                            <span className="mod-tags-collapsed" title={`Tags: ${visibleTags.join(', ')}`}>
                                              [{visibleTags.length}]
                                            </span>
                                            <span className="mod-tags-inline">
                                              {visibleTags.map((tag, i) => {
                                                const tagColor = getTagColor(tag)
                                                return (
                                                  <span
                                                    key={i}
                                                    className="mod-tag-badge"
                                                    onClick={(e) => {
                                                      e.stopPropagation();
                                                      toggleTagFilter(tag);
                                                    }}
                                                    title={`Click to filter by "${tag}" tag`}
                                                    style={{
                                                      background: tagColor.bg,
                                                      borderColor: tagColor.border,
                                                      color: tagColor.text
                                                    }}
                                                    onMouseEnter={(e) => {
                                                      e.currentTarget.style.background = tagColor.hover
                                                    }}
                                                    onMouseLeave={(e) => {
                                                      e.currentTarget.style.background = tagColor.bg
                                                    }}
                                                  >
                                                    {tag}
                                                  </span>
                                                )
                                              })}
                                            </span>
                                          </>
                                        )
                                      })()}
                                    </span>
                                    {isUnrevealed && (
                                      <div className="mod-metadata">
                                        <span className="mod-tier">{unrevealedMetadata?.bone_type} {unrevealedMetadata?.bone_part}</span>
                                      </div>
                                    )}
                                  </div>
                                </div>
                                {/* Min value slider for price search - show when mod is effectively selected (for hidden mods, only when explicitly enabled) */}
                                {priceModalOpen && effectivelySelected && !isUnrevealed && (
                                  <div className="mod-min-slider" onClick={(e) => e.stopPropagation()}>
                                    <span className="slider-label">Min:</span>
                                    <input
                                      type="range"
                                      min={0}
                                      max={(() => {
                                        // For 2-value mods (damage ranges), use average of rolled values
                                        if (mod.current_values && mod.current_values.length === 2) {
                                          return Math.floor((mod.current_values[0] + mod.current_values[1]) / 2)
                                        }
                                        // For single value mods, use the rolled value
                                        return mod.current_values?.[0] ?? mod.current_value ?? mod.stat_max ?? 100
                                      })()}
                                      value={priceModMinValues[modKey] ?? 0}
                                      onChange={(e) => {
                                        setPriceModMinValues(prev => ({
                                          ...prev,
                                          [modKey]: parseInt(e.target.value)
                                        }))
                                      }}
                                      className="min-value-slider"
                                    />
                                    <span className="slider-value">{priceModMinValues[modKey] ?? 0}</span>
                                  </div>
                                )}
                                <button
                                  className="mod-remove-btn"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleRemoveMod(idx, 'suffix')
                                  }}
                                  title="Remove this modifier"
                                >
                                  ✕
                                </button>
                              </div>
                            )
                          })}
                                    </>
                                  )
                                })()}
                              </>
                            )
                          })()}
                        </div>
                        </>
                      )}

                      {item.prefix_mods.length === 0 && item.suffix_mods.length === 0 && (
                        <div className="empty-mods">
                          <p>No explicit modifiers yet</p>
                        </div>
                      )}
                    </PoE2ItemFrame>

                    <div className="item-controls">
                      <button
                        className="reset-to-create-btn"
                        onClick={handleResetToCreate}
                        title="New item"
                      >
                        <span className="btn-icon">✦</span>
                        New
                      </button>

                      <button
                        className="reset-button"
                        onClick={() => {
                          const resetItem = {
                            ...item,
                            prefix_mods: [],
                            suffix_mods: [],
                            rarity: 'Normal' as ItemRarity
                          }
                          setItem(resetItem)
                          handleHistoryReset()
                          setMessage('Item reset to Normal rarity')
                        }}
                        title="Reset to normal"
                      >
                        <span className="btn-icon">↺</span>
                        Reset
                      </button>

                      <button
                        className="undo-button"
                        onClick={handleUndo}
                        disabled={itemHistory.length === 0}
                        title="Undo (Ctrl+Z)"
                      >
                        <span className="btn-icon">◄</span>
                        Undo
                      </button>

                      <button
                        className="redo-button"
                        onClick={handleRedo}
                        disabled={redoItemStack.length === 0}
                        title="Redo (Ctrl+Y)"
                      >
                        <span className="btn-icon">►</span>
                        Redo
                      </button>

                      <button
                        className="redo-rerun-button"
                        onClick={handleRetryLastAction}
                        disabled={actionHistory.length === 0 || !actionHistory[actionHistory.length - 1]}
                        title="Retry with new RNG (Ctrl+R)"
                      >
                        <span className="btn-icon">⟳</span>
                        Retry
                      </button>

                      <button
                        className="save-craft-btn"
                        onClick={() => setSaveModalOpen(true)}
                        title="Save craft"
                      >
                        <span className="btn-icon">▼</span>
                        Save
                      </button>

                      <button
                        className="load-craft-btn"
                        onClick={() => setLoadModalOpen(true)}
                        title="Load craft"
                      >
                        <span className="btn-icon">▲</span>
                        Load
                      </button>
                    </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'history' && <HistoryTab {...tabContentProps} />}
              {activeTab === 'currency' && <CurrencyTab {...tabContentProps} getCurrencyIconUrl={getCurrencyIconUrl} />}
            </div>
          </div>
        </div>

        {/* Right Panel - Crafting Controls */}
        <div className={`right-panel ${rightPanelCollapsed ? 'collapsed' : ''}`}>
          <button
            className={`panel-collapse-btn ${rightPanelCollapsed ? 'collapsed' : ''}`}
            onClick={() => setRightPanelCollapsed(!rightPanelCollapsed)}
            title={rightPanelCollapsed ? "Expand currency panel" : "Collapse currency panel"}
          >
            {rightPanelCollapsed ? '◀' : '▶'}
          </button>
          <div className="crafting-controls-vertical">
            {/* Unified Currency Stash - Clean Grid Layout */}
            <UnifiedCurrencyStash
              categorizedCurrencies={categorizedCurrencies}
              availableCurrencies={availableCurrencies}
              availableOmens={availableOmens}
              selectedOmens={selectedOmens}
              setSelectedOmens={setSelectedOmens}
              handleCraft={handleCraft}
              getCurrencyIconUrl={getCurrencyIconUrl}
              getOmenIconUrl={getOmenIconUrl}
              onCurrencyDragStart={(currency) => setDraggedCurrency(currency)}
              onCurrencyDragEnd={() => setDraggedCurrency(null)}
              searchFilter={isCurrencyMatchingSearch}
              isJewelry={item.base_category === 'ring' || item.base_category === 'amulet'}
            />
          </div>
        </div>
      </div>

      {/* Paste Preview Modal */}
      {pastePreviewOpen && (
        <div className="modal-overlay" onClick={handleCancelPaste}>
          <div className="reveal-modal" onClick={(e) => e.stopPropagation()}>
            <h3>📋 Import Item from Clipboard</h3>
            {pasteError ? (
              <>
                <div className="reveal-modal-content">
                  <div className="paste-error">
                    <p style={{ color: '#ff6666' }}>❌ {pasteError}</p>
                  </div>
                </div>
                <div className="modal-buttons">
                  <button className="close-modal-btn" onClick={handleCancelPaste}>
                    Close
                  </button>
                </div>
              </>
            ) : pastedItemPreview ? (
              <>
                <div className="reveal-modal-content">
                  <p>Parsed item successfully! Import to crafting simulator?</p>
                  {pasteWarnings.length > 0 && (
                    <div className="paste-warnings" style={{
                      backgroundColor: 'rgba(255, 200, 100, 0.1)',
                      border: '1px solid rgba(255, 200, 100, 0.3)',
                      padding: '10px',
                      marginBottom: '10px',
                      borderRadius: '4px'
                    }}>
                      <p style={{ color: '#ffcc66', fontWeight: 'bold', marginBottom: '5px' }}>⚠️ Warnings:</p>
                      {pasteWarnings.map((warning, idx) => (
                        <p key={idx} style={{ color: '#ffcc66', fontSize: '0.9em', margin: '3px 0' }}>
                          • {warning}
                        </p>
                      ))}
                    </div>
                  )}
                  <div className="item-preview">
                    <div className="item-header">
                      <span className={`item-rarity ${pastedItemPreview.rarity.toLowerCase()}`}>
                        {pastedItemPreview.rarity}
                      </span>
                      <span className="item-name">{pastedItemPreview.base_name}</span>
                      <span className="item-level">iLvl {pastedItemPreview.item_level}</span>
                    </div>
                    {pastedItemPreview.prefix_mods.length > 0 && (
                      <div className="mods-section">
                        <h4>Prefix Mods ({pastedItemPreview.prefix_mods.length}/3)</h4>
                        {pastedItemPreview.prefix_mods.map((mod, idx) => (
                          <div key={idx} className="mod-preview">
                            {renderModifier(mod)}
                          </div>
                        ))}
                      </div>
                    )}
                    {pastedItemPreview.suffix_mods.length > 0 && (
                      <div className="mods-section">
                        <h4>Suffix Mods ({pastedItemPreview.suffix_mods.length}/3)</h4>
                        {pastedItemPreview.suffix_mods.map((mod, idx) => (
                          <div key={idx} className="mod-preview">
                            {renderModifier(mod)}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
                <div className="modal-buttons">
                  <button className="reroll-btn" onClick={handleImportPastedItem}>
                    ✓ Import Item
                  </button>
                  <button className="close-modal-btn" onClick={handleCancelPaste}>
                    Cancel
                  </button>
                </div>
              </>
            ) : (
              <div className="reveal-modal-content">
                <p>Parsing item...</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Trade Price Flyout */}
      <TradePriceFlyout
        ref={priceFlyoutRef}
        item={item}
        exchangeRates={exchangeRates}
        isOpen={priceModalOpen}
        onClose={() => setPriceModalOpen(false)}
        onMessage={setMessage}
        onPriceResult={(result) => {
          setItemPrice(result)
        }}
        selectedMods={priceSearchMods}
        onSelectedModsChange={setPriceSearchMods}
        priceRarityEnabled={priceRarityEnabled}
        onPriceRarityEnabledChange={setPriceRarityEnabled}
        priceIlvlEnabled={priceIlvlEnabled}
        onPriceIlvlEnabledChange={setPriceIlvlEnabled}
        priceModMinValues={priceModMinValues}
        onPriceModMinValuesChange={setPriceModMinValues}
        usePseudoStats={usePseudoStats}
        onUsePseudoStatsChange={setUsePseudoStats}
        enabledHiddenMods={enabledHiddenMods}
        onEnabledHiddenModsChange={setEnabledHiddenMods}
        filtersChanged={filtersChanged}
        onFiltersChangedChange={setFiltersChanged}
      />

      {/* Reveal Modifier Modal */}
      {revealModalOpen && (() => {
        const unrevealedMod = item.unrevealed_mods.find(mod => mod.id === revealingModId)
        // Check if Omen of Abyssal Echoes is currently selected
        const hasAbyssalEchoes = selectedOmens.some(omen => omen.includes('Abyssal Echoes'))
        const canReroll = hasAbyssalEchoes && !rerollUsed
        const requiredBossTag = unrevealedMod?.required_boss_tag

        return (
          <div className="modal-overlay" onClick={handleCloseRevealModal}>
            <div className="reveal-modal" onClick={(e) => e.stopPropagation()}>
              <h3>Choose a Desecrated Modifier</h3>
              <div className="reveal-modal-content">
                <p>Select one of the following modifiers to reveal:</p>
                {requiredBossTag === 'ulaman' && <p className="omen-hint">🔱 Filtered to Ulaman (Sovereign) mods only</p>}
                {requiredBossTag === 'amanamu' && <p className="omen-hint">👑 Filtered to Amanamu (Liege) mods only</p>}
                {requiredBossTag === 'kurgal' && <p className="omen-hint">🩸 Filtered to Kurgal (Blackblooded) mods only</p>}
                {hasAbyssalEchoes && (
                  <p className="omen-hint">
                    {canReroll ? '✨ Omen of Abyssal Echoes: You may reroll once' : '✨ Omen of Abyssal Echoes (used)'}
                  </p>
                )}
                <div className="reveal-choices">
                  {revealChoices.map((choice, idx) => (
                    <div
                      key={idx}
                      className="reveal-choice"
                      onClick={() => handleSelectRevealChoice(choice)}
                    >
                      <div className="choice-stat">{renderModifier(choice)}</div>
                      <div className="choice-metadata">
                        <span className="choice-tier">T{choice.tier}</span>
                        <span className="choice-name">{choice.name}</span>
                        {choice.tags && choice.tags.length > 0 && (
                          <div className="choice-tags">
                            {choice.tags.map((tag, i) => {
                              const tagColor = getTagColor(tag)
                              return (
                                <span
                                  key={i}
                                  className="choice-tag-badge"
                                  style={{
                                    background: tagColor.bg,
                                    borderColor: tagColor.border,
                                    color: tagColor.text
                                  }}
                                >
                                  {tag}
                                </span>
                              )
                            })}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="modal-buttons">
                {canReroll && (
                  <button className="reroll-btn" onClick={handleRerollRevealChoices}>
                    🔄 Reroll Choices
                  </button>
                )}
                <button className="close-modal-btn" onClick={handleCloseRevealModal}>
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )
      })()}

      {/* Save/Load Craft Modals */}
      <SaveCraftModal
        isOpen={saveModalOpen}
        onClose={() => setSaveModalOpen(false)}
        snapshot={createCraftSnapshot()}
      />

      <LocalCraftsList
        isOpen={loadModalOpen}
        onClose={() => setLoadModalOpen(false)}
        onLoad={loadCraftSnapshot}
      />
    </div>
  )
}

export default GridCraftingSimulator
