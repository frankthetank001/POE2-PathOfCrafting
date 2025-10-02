import { useState, useEffect, useMemo } from 'react'
import { craftingApi } from '@/services/crafting-api'
import { UnifiedCurrencyStash } from '@/components/UnifiedCurrencyStash'
import type { CraftableItem, ItemModifier, ItemRarity, ItemBasesBySlot } from '@/types/crafting'
import { CURRENCY_DESCRIPTIONS } from '@/data/currency-descriptions'
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

function ItemTab({ setItem, onHistoryReset, setMessage, onItemCreated }: TabContentProps) {
  const [itemBases, setItemBases] = useState<ItemBasesBySlot>({})
  const [selectedSlot, setSelectedSlot] = useState<string>('body_armour')
  const [selectedCategory, setSelectedCategory] = useState<string>('int_armour')
  const [availableBases, setAvailableBases] = useState<Array<{name: string, description: string, default_ilvl: number, base_stats: Record<string, number>}>>([])
  const [selectedBase, setSelectedBase] = useState<string>('Vile Robe')
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
      // Calculate initial stats with quality (no mods yet)
      const initialStats = { ...baseData.base_stats }
      for (const [stat, value] of Object.entries(initialStats)) {
        if (['armour', 'evasion', 'energy_shield'].includes(stat)) {
          initialStats[stat] = Math.floor(value * 1.2) // 20% quality
        }
      }

      const newItem: CraftableItem = {
        base_name: selectedBase,
        base_category: selectedCategory,
        rarity: 'Normal' as ItemRarity,
        item_level: selectedItemLevel,
        quality: 20,
        implicit_mods: [],
        prefix_mods: [],
        suffix_mods: [],
        corrupted: false,
        base_stats: baseData.base_stats,
        calculated_stats: initialStats,
      }

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

  const [availableCurrencies, setAvailableCurrencies] = useState<string[]>([])
  // const [selectedEssence] = useState<string>('') // Unused for now
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
  const [searchQuery, setSearchQuery] = useState<string>('')

  // Panel collapse state
  const [leftPanelCollapsed, setLeftPanelCollapsed] = useState(false)
  const [rightPanelCollapsed, setRightPanelCollapsed] = useState(false)

  // Item creation state - track if user has created/selected an item
  const [itemCreated, setItemCreated] = useState(false)

  // Drag and drop state
  const [draggedMod, setDraggedMod] = useState<ItemModifier | null>(null)
  const [draggedCurrency, setDraggedCurrency] = useState<string | null>(null)

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

    // Add to history before making changes
    setHistory([...history, `Manually added ${draggedMod.name}`])
    setItemHistory([...itemHistory, item])

    // Add the mod to the item - support hybrid mods
    const newItem = { ...item }

    // Roll values for hybrid modifiers (multiple stat ranges)
    let modWithValue: ItemModifier
    if (draggedMod.stat_ranges && draggedMod.stat_ranges.length > 0) {
      // Roll one value per stat range
      const rolledValues = draggedMod.stat_ranges.map(range =>
        Math.random() * (range.max - range.min) + range.min
      )
      modWithValue = {
        ...draggedMod,
        current_values: rolledValues,
        current_value: rolledValues[0] // Legacy compatibility
      }
    } else {
      // Legacy single value rolling
      const randomValue = Math.floor(Math.random() * (draggedMod.stat_max! - draggedMod.stat_min! + 1)) + draggedMod.stat_min!
      modWithValue = { ...draggedMod, current_value: randomValue }
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

  // Load available mods and currencies when item changes
  useEffect(() => {
    if (item.base_name && item.base_name !== "Int Armour Body Armour") {
      loadAvailableMods()
      loadCategorizedCurrencies()
      loadAvailableCurrencies()
    }
  }, [item])

  // Recalculate stats whenever mods change
  useEffect(() => {
    if (item.base_stats && Object.keys(item.base_stats).length > 0) {
      const allMods = [...item.prefix_mods, ...item.suffix_mods]
      const newCalculatedStats = calculateItemStats(item.base_stats, item.quality, allMods)

      // Only update if stats actually changed to avoid infinite loop
      if (JSON.stringify(newCalculatedStats) !== JSON.stringify(item.calculated_stats)) {
        setItem(prev => ({
          ...prev,
          calculated_stats: newCalculatedStats
        }))
      }
    }
  }, [item.prefix_mods, item.suffix_mods, item.quality, item.base_stats])

  const calculateItemStats = (baseStats: Record<string, number>, quality: number, mods: ItemModifier[] = []): Record<string, number> => {
    const calculated = { ...baseStats }

    // Step 1: Collect flat modifiers
    let flatArmour = 0
    let flatEvasion = 0
    let flatEnergyShield = 0

    for (const mod of mods) {
      const statText = mod.stat_text.toLowerCase()

      // For multi-stat mods, current_values[0] is the flat component
      const flatValue = (mod.current_values && mod.current_values.length > 0)
        ? mod.current_values[0]
        : (mod.current_value || 0)

      // Hybrid mods with flat + % (e.g., "+X to ES, X% increased ES")
      if (statText.includes('to maximum energy shield') && statText.includes('% increased energy shield')) {
        flatEnergyShield += flatValue
        // The % part is handled in step 2
      }
      else if (statText.includes('to armour') && statText.includes('% increased armour') && !statText.includes('energy shield') && !statText.includes('evasion')) {
        flatArmour += flatValue
      }
      else if (statText.includes('to evasion') && statText.includes('% increased evasion') && !statText.includes('armour') && !statText.includes('energy shield')) {
        flatEvasion += flatValue
      }
      // Pure flat modifiers
      else if (statText.includes('to maximum energy shield') && !statText.includes('%')) {
        flatEnergyShield += flatValue
      }
      else if (statText.includes('to armour') && !statText.includes('%') && !statText.includes('energy shield')) {
        flatArmour += flatValue
      }
      else if (statText.includes('to evasion') && !statText.includes('%')) {
        flatEvasion += flatValue
      }
    }

    // Step 2: Collect percentage modifiers (quality + increased stack additively)
    let armourIncrease = quality
    let evasionIncrease = quality
    let energyShieldIncrease = quality

    for (const mod of mods) {
      const statText = mod.stat_text.toLowerCase()

      // For hybrid mods with flat + %, current_values[1] is the % component
      const percentValue = (mod.current_values && mod.current_values.length > 1)
        ? mod.current_values[1]
        : (mod.current_value || 0)

      // Hybrid flat + % mods (e.g., "+X to ES, X% increased ES")
      if (statText.includes('to maximum energy shield') && statText.includes('% increased energy shield')) {
        energyShieldIncrease += percentValue
      }
      else if (statText.includes('to armour') && statText.includes('% increased armour') && !statText.includes('energy shield') && !statText.includes('evasion')) {
        armourIncrease += percentValue
      }
      else if (statText.includes('to evasion') && statText.includes('% increased evasion') && !statText.includes('armour') && !statText.includes('energy shield')) {
        evasionIncrease += percentValue
      }
      // Pure % increased mods (use first value since they only have one stat)
      else if (statText.includes('% increased energy shield') &&
          !statText.includes('armour') && !statText.includes('evasion') && !statText.includes('to maximum')) {
        energyShieldIncrease += percentValue
      }
      else if (statText.includes('% increased armour') &&
               !statText.includes('energy shield') && !statText.includes('evasion') && !statText.includes('to ')) {
        armourIncrease += percentValue
      }
      else if (statText.includes('% increased evasion') &&
               !statText.includes('armour') && !statText.includes('energy shield') && !statText.includes('to ')) {
        evasionIncrease += percentValue
      }
      // Dual defence % mods (e.g., "% increased Armour and Energy Shield")
      else if (statText.includes('% increased armour and energy shield')) {
        armourIncrease += percentValue
        energyShieldIncrease += percentValue
      }
      else if (statText.includes('% increased armour and evasion')) {
        armourIncrease += percentValue
        evasionIncrease += percentValue
      }
      else if (statText.includes('% increased evasion and energy shield')) {
        evasionIncrease += percentValue
        energyShieldIncrease += percentValue
      }
    }

    // Step 3: Apply formula: (Base + Flat) × (1 + Quality% + Increased%)
    if (calculated.armour !== undefined) {
      calculated.armour = Math.floor((baseStats.armour + flatArmour) * (1 + armourIncrease / 100))
    }
    if (calculated.evasion !== undefined) {
      calculated.evasion = Math.floor((baseStats.evasion + flatEvasion) * (1 + evasionIncrease / 100))
    }
    if (calculated.energy_shield !== undefined) {
      calculated.energy_shield = Math.floor((baseStats.energy_shield + flatEnergyShield) * (1 + energyShieldIncrease / 100))
    }

    return calculated
  }

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

      // Add to history before updating item
      setHistory([...history, `Applied ${currencyType}${selectedOmens.length > 0 ? ` with ${selectedOmens.join(', ')}` : ''}`])
      setItemHistory([...itemHistory, item])

      // Update currency spent
      setCurrencySpent(prev => ({
        ...prev,
        [currencyType]: (prev[currencyType] || 0) + 1
      }))

      // Check if item state changed during the async operation (race condition protection)
      const currentItemState = JSON.stringify(item)
      if (currentItemState !== initialItemState) {
        setMessage(`Warning: Item changed during crafting. Operation may have been interrupted.`)
        setLoading(false)
        return
      }

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

  // Auto-dismiss message after 3 seconds
  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => {
        setMessage('')
      }, 3000)
      return () => clearTimeout(timer)
    }
  }, [message])

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
      const placeholderCount = (mod.stat_text.match(/\{\}/g) || []).length
      values.push(...Array(placeholderCount).fill(roundedValue))
    } else if (mod.stat_ranges && mod.stat_ranges.length > 0) {
      // Show ranges for each stat
      values.push(...mod.stat_ranges.map(r => `${r.min}-${r.max}`))
    } else if (mod.stat_min !== undefined && mod.stat_max !== undefined) {
      // Legacy: single range, duplicate for all placeholders
      const rangeText = `${mod.stat_min}-${mod.stat_max}`
      const placeholderCount = (mod.stat_text.match(/\{\}/g) || []).length
      values.push(...Array(placeholderCount).fill(rangeText))
    } else {
      values.push('?')
    }

    // Replace {} placeholders with corresponding values
    let statText = mod.stat_text
    for (const value of values) {
      statText = statText.replace('{}', value.toString())
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

    // Get currency description data
    const currencyData = CURRENCY_DESCRIPTIONS[currencyName]

    // Build searchable text from name + description + mechanics
    const searchableText = [
      currencyName,
      currencyData?.description || '',
      currencyData?.mechanics || ''
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
        mod.tags.forEach((tag: string) => tagSet.add(tag))
      }
    })
    return Array.from(tagSet).sort()
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
                <h4 className="column-title">Prefixes ({Object.keys(getGroupedMods('prefix')).length + availableMods.essence_prefixes.length + availableMods.desecrated_prefixes.length} total)</h4>
                <div className="mods-pool-list">
                  {/* Normal Prefixes */}
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
                          draggable={!allUnavailable && itemCreated}
                          onDragStart={() => handleDragStart(bestTier, 'prefix')}
                          onDragEnd={handleDragEnd}
                          title="Click to expand/collapse, double-click to filter by all tags, drag to add to item"
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
                              // Format the value range for this tier - support hybrid mods
                              let valueText = ''
                              if (mod.stat_ranges && mod.stat_ranges.length > 0) {
                                // Hybrid mods: show all ranges
                                if (mod.stat_ranges.length > 1) {
                                  valueText = mod.stat_ranges.map(r =>
                                    r.min === r.max ? `${r.min}` : `${r.min}-${r.max}`
                                  ).join(', ')
                                } else {
                                  const r = mod.stat_ranges[0]
                                  valueText = r.min === r.max ? `${r.min}` : `${r.min}-${r.max}`
                                }
                              } else if (mod.stat_min !== undefined && mod.stat_max !== undefined) {
                                // Legacy single range
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

                  {/* Essence Prefixes */}
                  {availableMods.essence_prefixes.map((mod, idx) => {
                    const isTagFiltered = activeTagFilters.size > 0 && !isModMatchingTagFilters(mod)
                    const isSearchFiltered = searchQuery.trim() && !isModMatchingSearch(mod)
                    const isFiltered = isTagFiltered || isSearchFiltered
                    return (
                      <div key={`essence-prefix-${idx}`} className={`pool-mod-group essence-only ${isFiltered ? 'tag-filtered' : ''}`}>
                        <div
                          className="pool-mod-group-header prefix compact-single-line mod-group-clickable"
                          onDoubleClick={() => applyAllModTags(mod)}
                          draggable={itemCreated}
                          onDragStart={() => handleDragStart(mod, 'prefix')}
                          onDragEnd={handleDragEnd}
                          title="Essence-only mod - Double-click to filter by all tags, drag to add to item"
                        >
                          <span className="pool-mod-stat-main">{mod.stat_text}</span>
                        </div>
                      </div>
                    )
                  })}

                  {/* Desecrated Prefixes */}
                  {availableMods.desecrated_prefixes.map((mod, idx) => {
                    const isTagFiltered = activeTagFilters.size > 0 && !isModMatchingTagFilters(mod)
                    return (
                      <div key={`desecrated-prefix-${idx}`} className={`pool-mod-group desecrated-only ${isTagFiltered ? 'tag-filtered' : ''}`}>
                        <div
                          className="pool-mod-group-header prefix compact-single-line mod-group-clickable"
                          onDoubleClick={() => applyAllModTags(mod)}
                          draggable={itemCreated}
                          onDragStart={() => handleDragStart(mod, 'prefix')}
                          onDragEnd={handleDragEnd}
                          title="Desecrated-only mod - Double-click to filter by all tags, drag to add to item"
                        >
                          <span className="pool-mod-stat-main">{mod.stat_text}</span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              <div className="mods-pool-column">
                <h4 className="column-title">Suffixes ({Object.keys(getGroupedMods('suffix')).length + availableMods.essence_suffixes.length + availableMods.desecrated_suffixes.length} total)</h4>
                <div className="mods-pool-list">
                  {/* Normal Suffixes */}
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
                          draggable={!allUnavailable && itemCreated}
                          onDragStart={() => handleDragStart(bestTier, 'suffix')}
                          onDragEnd={handleDragEnd}
                          title="Click to expand/collapse, double-click to filter by all tags, drag to add to item"
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
                              // Format the value range for this tier - support hybrid mods
                              let valueText = ''
                              if (mod.stat_ranges && mod.stat_ranges.length > 0) {
                                // Hybrid mods: show all ranges
                                if (mod.stat_ranges.length > 1) {
                                  valueText = mod.stat_ranges.map(r =>
                                    r.min === r.max ? `${r.min}` : `${r.min}-${r.max}`
                                  ).join(', ')
                                } else {
                                  const r = mod.stat_ranges[0]
                                  valueText = r.min === r.max ? `${r.min}` : `${r.min}-${r.max}`
                                }
                              } else if (mod.stat_min !== undefined && mod.stat_max !== undefined) {
                                // Legacy single range
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

                  {/* Essence Suffixes */}
                  {availableMods.essence_suffixes.map((mod, idx) => {
                    const isTagFiltered = activeTagFilters.size > 0 && !isModMatchingTagFilters(mod)
                    return (
                      <div key={`essence-suffix-${idx}`} className={`pool-mod-group essence-only ${isTagFiltered ? 'tag-filtered' : ''}`}>
                        <div
                          className="pool-mod-group-header suffix compact-single-line mod-group-clickable"
                          onDoubleClick={() => applyAllModTags(mod)}
                          draggable={itemCreated}
                          onDragStart={() => handleDragStart(mod, 'suffix')}
                          onDragEnd={handleDragEnd}
                          title="Essence-only mod - Double-click to filter by all tags, drag to add to item"
                        >
                          <span className="pool-mod-stat-main">{mod.stat_text}</span>
                        </div>
                      </div>
                    )
                  })}

                  {/* Desecrated Suffixes */}
                  {availableMods.desecrated_suffixes.map((mod, idx) => {
                    const isTagFiltered = activeTagFilters.size > 0 && !isModMatchingTagFilters(mod)
                    return (
                      <div key={`desecrated-suffix-${idx}`} className={`pool-mod-group desecrated-only ${isTagFiltered ? 'tag-filtered' : ''}`}>
                        <div
                          className="pool-mod-group-header suffix compact-single-line mod-group-clickable"
                          onDoubleClick={() => applyAllModTags(mod)}
                          draggable={itemCreated}
                          onDragStart={() => handleDragStart(mod, 'suffix')}
                          onDragEnd={handleDragEnd}
                          title="Desecrated-only mod - Double-click to filter by all tags, drag to add to item"
                        >
                          <span className="pool-mod-stat-main">{mod.stat_text}</span>
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
                            draggable={itemCreated}
                            onDragStart={() => handleDragStart(mod, 'suffix')}
                            onDragEnd={handleDragEnd}
                            title="Double-click to filter by all tags, drag to add to item"
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
                            draggable={itemCreated}
                            onDragStart={() => handleDragStart(mod, 'prefix')}
                            onDragEnd={handleDragEnd}
                            title="Double-click to filter by all tags, drag to add to item"
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
                            draggable={itemCreated}
                            onDragStart={() => handleDragStart(mod, 'suffix')}
                            onDragEnd={handleDragEnd}
                            title="Double-click to filter by all tags, drag to add to item"
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
                    <div
                      className={`item-display rarity-${item.rarity.toLowerCase()}`}
                      onDrop={handleDrop}
                      onDragOver={handleDragOver}
                    >
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
                            const isDesecrated = mod.tags && (mod.tags.includes('desecrated') || mod.tags.includes('desecrated_only'))
                            const modClasses = `mod-line prefix ${isTagFiltered ? 'tag-filtered' : ''} ${isDesecrated ? 'desecrated' : ''}`
                            return (
                              <div key={idx} className={modClasses}>
                                <div className="mod-content">
                                  <div className="mod-stat">{renderModifier(mod)}</div>
                                  <div className="mod-metadata">
                                    <span className="mod-tier">T{mod.tier}</span>
                                    <span className="mod-name">{mod.name}</span>
                                  </div>
                                </div>
                                <button
                                  className="mod-remove-btn"
                                  onClick={() => handleRemoveMod(idx, 'prefix')}
                                  title="Remove this modifier"
                                >
                                  ✕
                                </button>
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
                            const isDesecrated = mod.tags && (mod.tags.includes('desecrated') || mod.tags.includes('desecrated_only'))
                            const modClasses = `mod-line suffix ${isTagFiltered ? 'tag-filtered' : ''} ${isDesecrated ? 'desecrated' : ''}`
                            return (
                              <div key={idx} className={modClasses}>
                                <div className="mod-content">
                                  <div className="mod-stat">{renderModifier(mod)}</div>
                                  <div className="mod-metadata">
                                    <span className="mod-tier">T{mod.tier}</span>
                                    <span className="mod-name">{mod.name}</span>
                                  </div>
                                </div>
                                <button
                                  className="mod-remove-btn"
                                  onClick={() => handleRemoveMod(idx, 'suffix')}
                                  title="Remove this modifier"
                                >
                                  ✕
                                </button>
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
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default GridCraftingSimulator
