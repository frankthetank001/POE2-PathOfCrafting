import { useState, useEffect, useMemo } from 'react'
import { craftingApi } from '@/services/crafting-api'
import { CurrencyTooltipWrapper } from '@/components/CurrencyTooltipWrapper'
import { UnifiedCurrencyStash } from '@/components/UnifiedCurrencyStash'
import { Tooltip, CurrencyTooltip } from '@/components/Tooltip'
import type { CraftableItem, ItemModifier, ItemRarity, ItemBasesBySlot } from '@/types/crafting'
import './GridCraftingSimulator.css'

interface TabContentProps {
  item: CraftableItem
  setItem: (item: CraftableItem) => void
  history: string[]
  itemHistory: CraftableItem[]
  currencySpent: Record<string, number>
  onRevertToStep: (stepIndex: number) => void
  onClearHistory: () => void
  onHistoryReset: () => void
  setMessage: (message: string) => void
  onItemCreated?: () => void
}

function ItemTab({ item, setItem, onHistoryReset, setMessage, onItemCreated }: TabContentProps) {
  const [itemBases, setItemBases] = useState<ItemBasesBySlot>({})
  const [selectedSlot, setSelectedSlot] = useState<string>('body_armour')
  const [selectedCategory, setSelectedCategory] = useState<string>('int_armour')
  const [availableBases, setAvailableBases] = useState<Array<{name: string, description: string, default_ilvl: number, base_stats: Record<string, number>}>>([])
  const [selectedBase, setSelectedBase] = useState<string>('Vile Robe')
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
      const bases = await craftingApi.getBasesForSlotCategory(selectedSlot, selectedCategory)
      setAvailableBases(bases)

      // Set Vile Robe as default if available
      const vileRobe = bases.find(base => base.name === 'Vile Robe')
      if (vileRobe && selectedBase !== 'Vile Robe') {
        setSelectedBase('Vile Robe')
      } else if (!selectedBase && bases.length > 0) {
        setSelectedBase(bases[0].name)
      }
    } catch (err) {
      console.error('Failed to load available bases:', err)
    }
  }

  const loadItemBases = async () => {
    try {
      const bases = await craftingApi.getItemBases()
      setItemBases(bases)
    } catch (err) {
      console.error('Failed to load item bases:', err)
    }
  }

  const handleBaseSelection = async () => {
    if (!selectedBase) return

    const baseData = availableBases.find(base => base.name === selectedBase)
    if (!baseData) return

    try {
      const newItem: CraftableItem = {
        base_name: selectedBase,
        base_category: selectedCategory,
        rarity: 'Normal' as ItemRarity,
        item_level: baseData.default_ilvl,
        quality: 20,
        implicit_mods: [],
        prefix_mods: [],
        suffix_mods: [],
        corrupted: false,
        base_stats: baseData.base_stats,
        calculated_stats: calculateItemStats(baseData.base_stats, 20),
      }

      setItem(newItem)
      onHistoryReset()
      setMessage(`Selected base: ${selectedBase}`)
      onItemCreated?.()
    } catch (err) {
      console.error('Failed to create item from base:', err)
      setMessage('Failed to create item from base')
    }
  }

  const calculateItemStats = (baseStats: Record<string, number>, quality: number): Record<string, number> => {
    const calculated = { ...baseStats }
    for (const [stat, value] of Object.entries(calculated)) {
      if (['armour', 'evasion', 'energy_shield'].includes(stat)) {
        calculated[stat] = Math.floor(value * (1 + quality / 100))
      }
    }
    return calculated
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
      setPasteMessage('Item parsed successfully!')
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
                  <div className={`paste-message ${pasteMessage.includes('success') ? 'success' : 'error'}`}>
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

function HistoryTab({ history, itemHistory, onRevertToStep, onClearHistory }: TabContentProps) {

  const getItemSummary = (item: CraftableItem): string => {
    const totalMods = (item.prefix_mods?.length || 0) + (item.suffix_mods?.length || 0)
    return `${item.base_name} (${totalMods} mods, iLvl ${item.item_level})`
  }

  return (
    <div className="tab-content">
      <div className="history-section">
        <div className="section-header">
          <h3>📜 Crafting History</h3>
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
              <div key={idx} className="history-entry">
                <div className="history-number">{idx + 1}.</div>
                <div className="history-text">
                  {step}
                  {itemHistory[idx] && (
                    <div className="history-item-summary">
                      {getItemSummary(itemHistory[idx])}
                    </div>
                  )}
                </div>
                <button
                  className="revert-button"
                  onClick={() => onRevertToStep(idx)}
                  title="Revert to this step"
                >
                  ↶
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function CurrencyTab({ currencySpent }: TabContentProps) {
  const getTotalSpent = (): number => {
    return Object.values(currencySpent).reduce((sum, count) => sum + count, 0)
  }

  return (
    <div className="tab-content">
      <div className="currency-tracker">
        <h3>💰 Currency Spent</h3>

        {Object.keys(currencySpent).length === 0 ? (
          <div className="empty-history">No currency spent yet</div>
        ) : (
          <>
            <div className="currency-spent-list">
              {Object.entries(currencySpent).map(([currency, count]) => (
                <div key={currency} className="currency-spent-item">
                  <span className="currency-spent-name">{currency}</span>
                  <span className="currency-spent-count">{count}</span>
                </div>
              ))}
            </div>
            <div className="currency-total">
              <strong>Total: {getTotalSpent()} currencies used</strong>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function GridCraftingSimulator() {
  const [item, setItem] = useState<CraftableItem>({
    base_name: "Vile Robe",
    base_category: 'int_armour',
    rarity: 'Normal' as ItemRarity,
    item_level: 65,
    quality: 20,
    implicit_mods: [],
    prefix_mods: [],
    suffix_mods: [],
    corrupted: false,
    base_stats: {},
    calculated_stats: {},
  })

  const [categorizedCurrencies, setCategorizedCurrencies] = useState<{
    orbs: { implemented: string[], disabled: string[] }
    essences: { implemented: string[], disabled: string[] }
    bones: { implemented: string[], disabled: string[] }
    omens: string[]
    total: number
    implemented_count: number
    disabled_count: number
  }>({
    orbs: { implemented: [], disabled: [] },
    essences: { implemented: [], disabled: [] },
    bones: { implemented: [], disabled: [] },
    omens: [],
    total: 0,
    implemented_count: 0,
    disabled_count: 0
  })

  const [, setAvailableCurrencies] = useState<string[]>([])
  const [selectedEssence] = useState<string>('')
  const [selectedOmens, setSelectedOmens] = useState<string[]>([])
  const [availableOmens, setAvailableOmens] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string>('')
  const [history, setHistory] = useState<string[]>([])
  const [itemHistory, setItemHistory] = useState<CraftableItem[]>([])
  const [currencySpent, setCurrencySpent] = useState<Record<string, number>>({})

  const [availableMods, setAvailableMods] = useState<{
    prefixes: ItemModifier[]
    suffixes: ItemModifier[]
    essence_prefixes: ItemModifier[]
    essence_suffixes: ItemModifier[]
    desecrated_prefixes: ItemModifier[]
    desecrated_suffixes: ItemModifier[]
  }>({ prefixes: [], suffixes: [], essence_prefixes: [], essence_suffixes: [], desecrated_prefixes: [], desecrated_suffixes: [] })

  const [modPoolFilter, setModPoolFilter] = useState<{
    search: string
    tags: string[]
    modType: 'all' | 'prefix' | 'suffix'
  }>({ search: '', tags: [], modType: 'all' })

  const [activeTagFilters, setActiveTagFilters] = useState<Set<string>>(new Set())
  const [expandedModGroups, setExpandedModGroups] = useState<Set<string>>(new Set())
  const [activeTab, setActiveTab] = useState<'item' | 'history' | 'currency'>('item')

  // Panel collapse state
  const [leftPanelCollapsed, setLeftPanelCollapsed] = useState(false)
  const [rightPanelCollapsed, setRightPanelCollapsed] = useState(false)

  // Item creation state - track if user has created/selected an item
  const [itemCreated, setItemCreated] = useState(false)

  function handleItemCreated() {
    setItemCreated(true)
  }

  function handleResetToCreate() {
    setItemCreated(false)
    handleHistoryReset()
    setMessage('Ready to create new item')
  }

  // Tab content props
  const tabContentProps: TabContentProps = {
    item,
    setItem,
    history,
    itemHistory,
    currencySpent,
    onRevertToStep: handleRevertToStep,
    onClearHistory: handleClearHistory,
    onHistoryReset: handleHistoryReset,
    setMessage,
    onItemCreated: handleItemCreated
  }

  function handleRevertToStep(stepIndex: number) {
    if (stepIndex < itemHistory.length) {
      setItem(itemHistory[stepIndex])
      setItemHistory(itemHistory.slice(0, stepIndex + 1))
      setHistory(history.slice(0, stepIndex + 1))
      setMessage(`Reverted to step ${stepIndex + 1}`)
    }
  }

  function handleClearHistory() {
    setHistory([])
    setItemHistory([])
    setCurrencySpent({})
    setMessage('History cleared')
  }

  function handleHistoryReset() {
    setHistory([])
    setItemHistory([])
    setCurrencySpent({})
  }

  // Load available mods when item changes
  useEffect(() => {
    if (item.base_name && item.base_name !== "Int Armour Body Armour") {
      loadAvailableMods()
      loadCategorizedCurrencies()
    }
  }, [item])

  const loadAvailableMods = async () => {
    try {
      const mods = await craftingApi.getAvailableMods(item)
      setAvailableMods(mods)
    } catch (err) {
      console.error('Failed to load available mods:', err)
    }
  }

  const loadCategorizedCurrencies = async () => {
    try {
      const currencies = await craftingApi.getCategorizedCurrencies()
      setCategorizedCurrencies(currencies)
      setAvailableCurrencies([...currencies.orbs.implemented, ...currencies.essences.implemented, ...currencies.bones.implemented])
      setAvailableOmens(currencies.omens)
    } catch (err) {
      console.error('Failed to load currencies:', err)
    }
  }

  const handleCraft = async (currencyType: string) => {
    if (loading) return

    setLoading(true)
    setMessage('')

    try {
      const craftParams: any = {
        currency: currencyType,
        omens: selectedOmens
      }

      if (currencyType.includes('Essence')) {
        craftParams.essence = selectedEssence || currencyType
      }

      const result = await craftingApi.simulateCrafting({
        item,
        currency_name: currencyType
      })

      // Add to history before updating item
      setHistory([...history, `Applied ${currencyType}${selectedOmens.length > 0 ? ` with ${selectedOmens.join(', ')}` : ''}`])
      setItemHistory([...itemHistory, item])

      // Update currency spent
      setCurrencySpent(prev => ({
        ...prev,
        [currencyType]: (prev[currencyType] || 0) + 1
      }))

      if (result.result_item) {
        setItem(result.result_item)
      }
      setMessage(`${currencyType} applied successfully!`)

      // Clear selected omens after use
      setSelectedOmens([])

    } catch (err: any) {
      setMessage(`Error: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleUndo = () => {
    if (itemHistory.length > 0) {
      const previousItem = itemHistory[itemHistory.length - 1]
      const previousHistory = history.slice(0, -1)
      const previousItemHistory = itemHistory.slice(0, -1)

      setItem(previousItem)
      setHistory(previousHistory)
      setItemHistory(previousItemHistory)
      setMessage('Undone last action')
    }
  }

  // Keyboard shortcut for undo
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey && event.key === 'z') {
        event.preventDefault()
        handleUndo()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [itemHistory])

  // Sophisticated mod filtering and grouping functions
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

    // Check prefix/suffix highlighting - if omen targets specific type, grey out the other
    if (highlighting.highlightPrefixes && modType === 'suffix') return true
    if (highlighting.highlightSuffixes && modType === 'prefix') return true

    // For same type highlighting (homogenising omens), grey out mods that don't match
    if (highlighting.highlightSameTypes) {
      const existingMods = [...item.prefix_mods, ...item.suffix_mods]
      const existingModGroups = existingMods.map(m => m.mod_group).filter(Boolean)

      // If mod doesn't match any existing group, grey it out
      if (existingModGroups.length > 0 && (!mod.mod_group || !existingModGroups.includes(mod.mod_group))) {
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
    if (!mod.tags) return false
    return Array.from(activeTagFilters).every(filter => mod.tags.includes(filter))
  }

  const shouldGreyOutModGroup = (groupMods: ItemModifier[], modType: 'prefix' | 'suffix'): boolean => {
    // Check if group should be greyed out due to omen incompatibility or tag filtering
    const omenIncompatible = groupMods.every(mod => shouldGreyOutMod(mod, modType))
    const tagFiltered = activeTagFilters.size > 0 && !groupMods.some(mod => isModMatchingTagFilters(mod))
    return omenIncompatible || tagFiltered
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

    // Handle Bones
    if (currency.includes('Bone') || currency.includes('bone') || currency.startsWith('Abyssal') || currency.startsWith('Ancient')) {
      const boneIconMap: Record<string, string> = {
        // Ancient Bones (Min Modifier Level: 40)
        'Ancient Collarbone': 'https://www.poe2wiki.net/images/2/29/Ancient_Collarbone_inventory_icon.png',
        'Ancient Jawbone': 'https://www.poe2wiki.net/images/7/79/Ancient_Jawbone_inventory_icon.png',
        'Ancient Rib': 'https://www.poe2wiki.net/images/9/9d/Ancient_Rib_inventory_icon.png',

        // Preserved Bones (Mid-tier)
        'Preserved Collarbone': 'https://www.poe2wiki.net/images/7/7a/Preserved_Collarbone_inventory_icon.png',
        'Preserved Jawbone': 'https://www.poe2wiki.net/images/4/47/Preserved_Jawbone_inventory_icon.png',
        'Preserved Rib': 'https://www.poe2wiki.net/images/c/ce/Preserved_Rib_inventory_icon.png',
        'Preserved Cranium': 'https://www.poe2wiki.net/images/6/69/Preserved_Cranium_inventory_icon.png',
        'Preserved Vertebrae': 'https://www.poe2wiki.net/images/7/78/Preserved_Vertebrae_inventory_icon.png',

        // Gnawed Bones (Max Item Level: 64)
        'Gnawed Collarbone': 'https://www.poe2wiki.net/images/b/bc/Gnawed_Collarbone_inventory_icon.png',
        'Gnawed Jawbone': 'https://www.poe2wiki.net/images/a/a8/Gnawed_Jawbone_inventory_icon.png',
        'Gnawed Rib': 'https://www.poe2wiki.net/images/8/81/Gnawed_Rib_inventory_icon.png',
      }

      if (boneIconMap[currency]) {
        return boneIconMap[currency]
      }

      // Fallback logic for bone types
      if (currency.includes('Collarbone')) return 'https://www.poe2wiki.net/images/2/29/Ancient_Collarbone_inventory_icon.png'
      if (currency.includes('Jawbone')) return 'https://www.poe2wiki.net/images/7/79/Ancient_Jawbone_inventory_icon.png'
      if (currency.includes('Rib')) return 'https://www.poe2wiki.net/images/9/9d/Ancient_Rib_inventory_icon.png'
      if (currency.includes('Cranium')) return 'https://www.poe2wiki.net/images/6/69/Preserved_Cranium_inventory_icon.png'
      if (currency.includes('Vertebrae')) return 'https://www.poe2wiki.net/images/7/78/Preserved_Vertebrae_inventory_icon.png'

      return 'https://www.poe2wiki.net/images/2/29/Ancient_Collarbone_inventory_icon.png'
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

      // Alchemy & Other Omens
      "Omen of Sinistral Alchemy": "https://www.poe2wiki.net/images/4/43/Omen_of_Sinistral_Alchemy_inventory_icon.png",
      "Omen of Dextral Alchemy": "https://www.poe2wiki.net/images/b/bc/Omen_of_Dextral_Alchemy_inventory_icon.png",
      "Omen of Corruption": "https://www.poe2wiki.net/images/f/f4/Omen_of_Corruption_inventory_icon.png",
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
        mod.tags.forEach((tag: string) => tagSet.add(tag))
      }
    })
    return Array.from(tagSet).sort()
  }, [availableMods])

  return (
    <div className="grid-crafting-simulator">
      {/* Global Tag Filters - Floating at Top */}
      <div className="global-tag-filters">
        <div className="global-tag-filters-content">
          <span className="global-tag-filters-label">🏷️ Global Tag Filters:</span>
          <button
            className={`clear-filters-btn ${activeTagFilters.size === 0 ? 'disabled' : ''}`}
            onClick={clearTagFilters}
            disabled={activeTagFilters.size === 0}
            title={activeTagFilters.size > 0 ? `Clear ${activeTagFilters.size} active filters` : 'No active filters'}
          >
            ↺ Clear
          </button>
          <div className="global-tag-list">
            {allAvailableTags.slice(0, 15).map(tag => (
              <span
                key={tag}
                className={`global-tag-item ${activeTagFilters.has(tag) ? 'active-filter' : ''}`}
                data-tag={tag}
                onClick={() => toggleTagFilter(tag)}
                title={`Toggle ${tag} filter`}
              >
                {tag}
              </span>
            ))}
            {allAvailableTags.length > 15 && (
              <span className="tag-count-indicator">
                +{allAvailableTags.length - 15} more
              </span>
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
                    const unavailableCount = groupMods.filter(m => m.required_ilvl && m.required_ilvl > item.item_level).length
                    const allUnavailable = unavailableCount === groupMods.length
                    const isGroupGreyedOut = shouldGreyOutModGroup(groupMods, 'prefix')
                    const isExpanded = expandedModGroups.has(`prefix-${groupKey}`)

                    // Calculate available tier range
                    const availableModsInGroup = groupMods.filter(m => !m.required_ilvl || m.required_ilvl <= item.item_level)
                    const bestAvailableTier = availableModsInGroup.length > 0 ? Math.min(...availableModsInGroup.map(m => m.tier)) : null
                    const worstTier = Math.max(...groupMods.map(m => m.tier))
                    const tierRangeText = bestAvailableTier ? `T${bestAvailableTier}-T${worstTier}` : `T1-T${worstTier}`

                    return (
                      <div key={groupKey} className={`pool-mod-group ${isGroupGreyedOut ? 'omen-incompatible' : ''}`}>
                        <div
                          className={`pool-mod-group-header prefix compact-single-line ${allUnavailable ? 'all-unavailable' : ''} mod-group-clickable`}
                          onClick={() => toggleModGroup(`prefix-${groupKey}`)}
                          onDoubleClick={() => applyAllModTags(bestTier)}
                          title="Click to expand/collapse, double-click to filter by all tags"
                        >
                          <span className="pool-mod-stat-main">{bestTier.stat_text}</span>
                          <div className="compact-mod-info">
                            {unavailableCount > 0 && (
                              <span
                                className="unavailable-indicator"
                                title={`${unavailableCount} unavailable tier${unavailableCount > 1 ? 's' : ''}`}
                              >
                                ⚠
                              </span>
                            )}
                            <span className="group-tier-range">{tierRangeText}</span>
                            <span className="group-max-ilvl">ilvl {maxIlvl}</span>
                            {bestTier.tags && bestTier.tags.length > 0 && (
                              <div className="mod-tags-line" title="Click individual tags to filter, or double-click the mod to apply all tags">
                                {bestTier.tags.slice(0, 3).map((tag, i) => (
                                  <span
                                    key={i}
                                    className="mod-tag-text"
                                    data-tag={tag}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      toggleTagFilter(tag);
                                    }}
                                    title={`Click to filter by "${tag}" tag`}
                                  >
                                    {tag}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>

                        {isExpanded && (
                          <div className="mod-tier-details">
                            {groupMods.map(mod => {
                              // Format the value range for this tier
                              let valueText = ''
                              if (mod.stat_min !== undefined && mod.stat_max !== undefined) {
                                if (mod.stat_min === mod.stat_max) {
                                  valueText = `${mod.stat_min}`
                                } else {
                                  valueText = `${mod.stat_min}-${mod.stat_max}`
                                }
                              }

                              return (
                                <div
                                  key={mod.tier}
                                  className={`tier-detail ${mod.required_ilvl && mod.required_ilvl > item.item_level ? 'unavailable' : ''}`}
                                >
                                  <span className="tier-label">T{mod.tier}</span>
                                  <span className="tier-stat">{mod.stat_text}</span>
                                  {valueText && <span className="tier-values">({valueText})</span>}
                                  <span className="tier-ilvl">ilvl {mod.required_ilvl || 1}</span>
                                </div>
                              )
                            })}
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
                    const unavailableCount = groupMods.filter(m => m.required_ilvl && m.required_ilvl > item.item_level).length
                    const allUnavailable = unavailableCount === groupMods.length
                    const isGroupGreyedOut = shouldGreyOutModGroup(groupMods, 'suffix')
                    const isExpanded = expandedModGroups.has(`suffix-${groupKey}`)

                    // Calculate available tier range
                    const availableModsInGroup = groupMods.filter(m => !m.required_ilvl || m.required_ilvl <= item.item_level)
                    const bestAvailableTier = availableModsInGroup.length > 0 ? Math.min(...availableModsInGroup.map(m => m.tier)) : null
                    const worstTier = Math.max(...groupMods.map(m => m.tier))
                    const tierRangeText = bestAvailableTier ? `T${bestAvailableTier}-T${worstTier}` : `T1-T${worstTier}`

                    return (
                      <div key={groupKey} className={`pool-mod-group ${isGroupGreyedOut ? 'omen-incompatible' : ''}`}>
                        <div
                          className={`pool-mod-group-header suffix compact-single-line ${allUnavailable ? 'all-unavailable' : ''} mod-group-clickable`}
                          onClick={() => toggleModGroup(`suffix-${groupKey}`)}
                          onDoubleClick={() => applyAllModTags(bestTier)}
                          title="Click to expand/collapse, double-click to filter by all tags"
                        >
                          <span className="pool-mod-stat-main">{bestTier.stat_text}</span>
                          <div className="compact-mod-info">
                            {unavailableCount > 0 && (
                              <span
                                className="unavailable-indicator"
                                title={`${unavailableCount} unavailable tier${unavailableCount > 1 ? 's' : ''}`}
                              >
                                ⚠
                              </span>
                            )}
                            <span className="group-tier-range">{tierRangeText}</span>
                            <span className="group-max-ilvl">ilvl {maxIlvl}</span>
                            {bestTier.tags && bestTier.tags.length > 0 && (
                              <div className="mod-tags-line" title="Click individual tags to filter, or double-click the mod to apply all tags">
                                {bestTier.tags.slice(0, 3).map((tag, i) => (
                                  <span
                                    key={i}
                                    className="mod-tag-text"
                                    data-tag={tag}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      toggleTagFilter(tag);
                                    }}
                                    title={`Click to filter by "${tag}" tag`}
                                  >
                                    {tag}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>

                        {isExpanded && (
                          <div className="mod-tier-details">
                            {groupMods.map(mod => {
                              // Format the value range for this tier
                              let valueText = ''
                              if (mod.stat_min !== undefined && mod.stat_max !== undefined) {
                                if (mod.stat_min === mod.stat_max) {
                                  valueText = `${mod.stat_min}`
                                } else {
                                  valueText = `${mod.stat_min}-${mod.stat_max}`
                                }
                              }

                              return (
                                <div
                                  key={mod.tier}
                                  className={`tier-detail ${mod.required_ilvl && mod.required_ilvl > item.item_level ? 'unavailable' : ''}`}
                                >
                                  <span className="tier-label">T{mod.tier}</span>
                                  <span className="tier-stat">{mod.stat_text}</span>
                                  {valueText && <span className="tier-values">({valueText})</span>}
                                  <span className="tier-ilvl">ilvl {mod.required_ilvl || 1}</span>
                                </div>
                              )
                            })}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>

            {/* Essence-Only Modifiers Section */}
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
                            title="Double-click to filter by all tags"
                          >
                            <span className="pool-mod-stat-main">{mod.stat_text}</span>
                            {mod.tags && mod.tags.length > 0 && (
                              <div className="mod-tags-line" title="Click individual tags to filter, or double-click the mod to apply all tags">
                                {mod.tags.map((tag, i) => (
                                  <span
                                    key={i}
                                    className="mod-tag-text"
                                    data-tag={tag}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      toggleTagFilter(tag);
                                    }}
                                    title={`Click to filter by "${tag}" tag`}
                                  >
                                    {tag}
                                  </span>
                                ))}
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
                            title="Double-click to filter by all tags"
                          >
                            <span className="pool-mod-stat-main">{mod.stat_text}</span>
                            {mod.tags && mod.tags.length > 0 && (
                              <div className="mod-tags-line" title="Click individual tags to filter, or double-click the mod to apply all tags">
                                {mod.tags.map((tag, i) => (
                                  <span
                                    key={i}
                                    className="mod-tag-text"
                                    data-tag={tag}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      toggleTagFilter(tag);
                                    }}
                                    title={`Click to filter by "${tag}" tag`}
                                  >
                                    {tag}
                                  </span>
                                ))}
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
                            title="Double-click to filter by all tags"
                          >
                            <span className="pool-mod-stat-main">{mod.stat_text}</span>
                            {mod.tags && mod.tags.length > 0 && (
                              <div className="mod-tags-line" title="Click individual tags to filter, or double-click the mod to apply all tags">
                                {mod.tags.map((tag, i) => (
                                  <span
                                    key={i}
                                    className="mod-tag-text"
                                    data-tag={tag}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      toggleTagFilter(tag);
                                    }}
                                    title={`Click to filter by "${tag}" tag`}
                                  >
                                    {tag}
                                  </span>
                                ))}
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
                            title="Double-click to filter by all tags"
                          >
                            <span className="pool-mod-stat-main">{mod.stat_text}</span>
                            {mod.tags && mod.tags.length > 0 && (
                              <div className="mod-tags-line" title="Click individual tags to filter, or double-click the mod to apply all tags">
                                {mod.tags.map((tag, i) => (
                                  <span
                                    key={i}
                                    className="mod-tag-text"
                                    data-tag={tag}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      toggleTagFilter(tag);
                                    }}
                                    title={`Click to filter by "${tag}" tag`}
                                  >
                                    {tag}
                                  </span>
                                ))}
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
                      <div className="current-item-display">
                    <div className="item-display">
                      <div className="item-header">
                        <h2 className={`item-name rarity-${item.rarity.toLowerCase()}`}>{item.base_name}</h2>
                        <div className="item-rarity-badge">{item.rarity}</div>
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
                          <span className="detail-label">Category:</span>
                          <span className="detail-value">{item.base_category?.replace('_', ' ')}</span>
                        </div>
                      </div>

                      {Object.keys(item.calculated_stats || {}).length > 0 && (
                        <div className="stats-section">
                          <h4 className="stats-title">Base Stats</h4>
                          {Object.entries(item.calculated_stats || {}).map(([statName, value]) => (
                            <div key={statName} className="stat-row">
                              <span className="stat-label">{statName}:</span>
                              <span className="stat-value">{value}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {item.prefix_mods.length > 0 && (
                        <div className="mods-section">
                          <h4 className="mods-title">Prefixes ({item.prefix_mods.length}/3)</h4>
                          {item.prefix_mods.map((mod, idx) => {
                            const isTagFiltered = activeTagFilters.size > 0 && !isModMatchingTagFilters(mod)
                            return (
                              <div key={idx} className={`mod-line prefix ${isTagFiltered ? 'tag-filtered' : ''}`}>
                                <div className="mod-stat">{renderModifier(mod)}</div>
                                <div className="mod-metadata">
                                  <span className="mod-tier">T{mod.tier}</span>
                                  <span className="mod-name">{mod.name}</span>
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      )}

                      {item.suffix_mods.length > 0 && (
                        <div className="mods-section">
                          <h4 className="mods-title">Suffixes ({item.suffix_mods.length}/3)</h4>
                          {item.suffix_mods.map((mod, idx) => {
                            const isTagFiltered = activeTagFilters.size > 0 && !isModMatchingTagFilters(mod)
                            return (
                              <div key={idx} className={`mod-line suffix ${isTagFiltered ? 'tag-filtered' : ''}`}>
                                <div className="mod-stat">{renderModifier(mod)}</div>
                                <div className="mod-metadata">
                                  <span className="mod-tier">T{mod.tier}</span>
                                  <span className="mod-name">{mod.name}</span>
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      )}

                      {item.prefix_mods.length === 0 && item.suffix_mods.length === 0 && (
                        <div className="empty-mods">
                          <p>No explicit modifiers yet</p>
                        </div>
                      )}
                    </div>

                    <div className="item-controls">
                      <button
                        className="reset-to-create-btn"
                        onClick={handleResetToCreate}
                        title="Go back to item creation"
                      >
                        🔄 Create New Item
                      </button>

                      <button
                        className="reset-button"
                        onClick={() => {
                          setItem({
                            ...item,
                            prefix_mods: [],
                            suffix_mods: [],
                            rarity: 'normal' as ItemRarity
                          })
                          handleHistoryReset()
                        }}
                      >
                        🔄 Reset Item
                      </button>

                      <button
                        className="undo-button"
                        onClick={handleUndo}
                        disabled={itemHistory.length === 0}
                        title="Ctrl+Z"
                      >
                        ↶ Undo
                      </button>
                    </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'history' && <HistoryTab {...tabContentProps} />}
              {activeTab === 'currency' && <CurrencyTab {...tabContentProps} />}
            </div>
          </div>

          {message && (
            <div className={`message ${message.includes('Error') ? 'error' : message.includes('success') ? 'success' : 'info'}`}>
              {message}
            </div>
          )}
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
              availableOmens={availableOmens}
              selectedOmens={selectedOmens}
              setSelectedOmens={setSelectedOmens}
              handleCraft={handleCraft}
              getCurrencyIconUrl={getCurrencyIconUrl}
              getOmenIconUrl={getOmenIconUrl}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default GridCraftingSimulator
