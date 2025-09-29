import React, { useState, useEffect, useMemo } from 'react'
import { craftingApi } from '@/services/crafting-api'
import { getOmenDescription } from '@/data/currency-descriptions'
import { CurrencyTooltipWrapper } from '@/components/CurrencyTooltipWrapper'
import { Tooltip, CurrencyTooltip } from '@/components/Tooltip'
import type { CraftableItem, ItemModifier, ItemRarity, ItemBasesBySlot } from '@/types/crafting'
import './CraftingSimulator.css'


function CraftingSimulator() {
  const [item, setItem] = useState<CraftableItem>({
    base_name: "Int Armour Body Armour",
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
  const [selectedCurrency, setSelectedCurrency] = useState<string>('')
  const [selectedEssence, setSelectedEssence] = useState<string>('')
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
  const [itemBases, setItemBases] = useState<ItemBasesBySlot>({})
  const [selectedSlot, setSelectedSlot] = useState<string>('body_armour')
  const [selectedCategory, setSelectedCategory] = useState<string>('int_armour')
  const [availableBases, setAvailableBases] = useState<Array<{name: string, description: string, default_ilvl: number, base_stats: Record<string, number>}>>([])
  const [selectedBase, setSelectedBase] = useState<string>('')
  const [modsPoolCollapsed, setModsPoolCollapsed] = useState(false)
  const [itemPasteText, setItemPasteText] = useState('')
  const [pasteExpanded, setPasteExpanded] = useState(false)
  const [pasteMessage, setPasteMessage] = useState('')
  const [essencesModalOpen, setEssencesModalOpen] = useState(false)
  const [modsPoolWidth, setModsPoolWidth] = useState<number>(() => {
    const saved = localStorage.getItem('modsPoolWidth')
    return saved ? parseInt(saved) : 600
  })
  const [isResizing, setIsResizing] = useState(false)

  // Vertical resize state
  const [verticalSizes, setVerticalSizes] = useState(() => {
    const saved = localStorage.getItem('verticalSizes')
    return saved ? JSON.parse(saved) : {
      currencyCompact: 100,
      itemDisplay: 350,
      currencySection: 150,
      historySection: 200
    }
  })
  const [verticalResizing, setVerticalResizing] = useState<{
    active: boolean
    section: string
    startY: number
    startHeight: number
  }>({
    active: false,
    section: '',
    startY: 0,
    startHeight: 0
  })

  useEffect(() => {
    loadCurrencies()
    loadItemBases()
  }, [])

  useEffect(() => {
    loadAvailableBases()
  }, [selectedSlot, selectedCategory])

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

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return

      const newWidth = e.clientX - 32
      const maxWidth = Math.floor(window.innerWidth * 0.8) // 80% of screen width
      if (newWidth >= 300 && newWidth <= maxWidth) {
        setModsPoolWidth(newWidth)
      }
    }

    const handleMouseUp = () => {
      if (isResizing) {
        setIsResizing(false)
        localStorage.setItem('modsPoolWidth', modsPoolWidth.toString())
      }
    }

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
  }, [isResizing, modsPoolWidth])

  // Vertical resize handlers
  useEffect(() => {
    const handleVerticalMouseMove = (e: MouseEvent) => {
      if (!verticalResizing.active) return

      const deltaY = e.clientY - verticalResizing.startY
      const newHeight = Math.max(150, verticalResizing.startHeight + deltaY)

      setVerticalSizes((prev: typeof verticalSizes) => ({
        ...prev,
        [verticalResizing.section]: newHeight
      }))
    }

    const handleVerticalMouseUp = () => {
      if (verticalResizing.active) {
        setVerticalResizing({
          active: false,
          section: '',
          startY: 0,
          startHeight: 0
        })
        localStorage.setItem('verticalSizes', JSON.stringify(verticalSizes))
      }
    }

    if (verticalResizing.active) {
      document.addEventListener('mousemove', handleVerticalMouseMove)
      document.addEventListener('mouseup', handleVerticalMouseUp)
      document.body.style.cursor = 'row-resize'
      document.body.style.userSelect = 'none'
    }

    return () => {
      document.removeEventListener('mousemove', handleVerticalMouseMove)
      document.removeEventListener('mouseup', handleVerticalMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
  }, [verticalResizing, verticalSizes])

  const handleVerticalResizeStart = (section: string, e: React.MouseEvent): void => {
    setVerticalResizing({
      active: true,
      section: section,
      startY: e.clientY,
      startHeight: verticalSizes[section]
    })
  }

  const loadCurrencies = async () => {
    try {
      const categorized = await craftingApi.getCategorizedCurrencies()
      setCategorizedCurrencies(categorized)

      if (categorized.orbs.implemented.length > 0) {
        setSelectedCurrency(categorized.orbs.implemented[0])
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
        essence_prefixes: data.essence_prefixes || [],
        essence_suffixes: data.essence_suffixes || [],
        desecrated_prefixes: data.desecrated_prefixes || [],
        desecrated_suffixes: data.desecrated_suffixes || [],
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

  const loadAvailableBases = async () => {
    try {
      const bases = await craftingApi.getBasesForSlotCategory(selectedSlot, selectedCategory)
      setAvailableBases(bases)

      // Set default selected base (first one) and create item
      if (bases.length > 0) {
        const firstBase = bases[0]
        setSelectedBase(firstBase.name)
        const baseStats = firstBase.base_stats || {}
        setItem({
          base_name: firstBase.name,
          base_category: selectedCategory,
          rarity: 'Normal' as ItemRarity,
          item_level: 65,
          quality: 20,
          implicit_mods: [],
          prefix_mods: [],
          suffix_mods: [],
          corrupted: false,
          base_stats: baseStats,
          calculated_stats: calculateItemStats(baseStats, 20),
        })
      }
    } catch (err) {
      console.error('Failed to load available bases:', err)
    }
  }

  // Helper function to calculate stats with quality
  const calculateItemStats = (baseStats: Record<string, number>, quality: number): Record<string, number> => {
    const calculated = { ...baseStats }

    // Apply quality bonuses to armor, evasion, and energy_shield
    for (const [stat, value] of Object.entries(calculated)) {
      if (['armour', 'evasion', 'energy_shield'].includes(stat)) {
        calculated[stat] = Math.floor(value * (1 + quality / 100))
      }
    }

    return calculated
  }


  const loadAvailableOmens = async (currencyName: string) => {
    try {
      const omens = await craftingApi.getAvailableOmensForCurrency(currencyName)
      setAvailableOmens(omens)
    } catch (err) {
      console.error('Failed to load available omens:', err)
      setAvailableOmens([])
    }
  }

  const toggleOmen = (omen: string) => {
    // Only allow toggling if omen is compatible with selected currency
    if (selectedCurrency === '' || !availableOmens.includes(omen)) {
      return
    }

    setSelectedOmens(prev =>
      prev.includes(omen)
        ? prev.filter(o => o !== omen)
        : [...prev, omen]
    )
  }

  const handleCraft = async (currencyName: string) => {
    setLoading(true)
    setMessage('')

    try {
      let result
      if (selectedOmens.length > 0) {
        result = await craftingApi.simulateCraftingWithOmens(item, currencyName, selectedOmens)
      } else {
        result = await craftingApi.simulateCrafting({
          item,
          currency_name: currencyName,
        })
      }

      if (result.success && result.result_item) {
        setItemHistory([...itemHistory, item])
        setItem(result.result_item)
        const omenText = selectedOmens.length > 0 ? ` with omens [${selectedOmens.join(', ')}]` : ''
        setMessage(`✓ ${result.message}`)
        setHistory([...history, `Used ${currencyName}${omenText}: ${result.message}`])

        setCurrencySpent(prev => ({
          ...prev,
          [currencyName]: (prev[currencyName] || 0) + 1
        }))

        // Clear selected omens after use
        setSelectedOmens([])
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
      base_name: selectedBase || getDisplayName(selectedSlot, selectedCategory),
      base_category: selectedCategory,
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

  // Function to check if a mod should be greyed out (incompatible)
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

  // Function to check if a mod group should be greyed out
  const shouldGreyOutModGroup = (groupMods: ItemModifier[], modType: 'prefix' | 'suffix'): boolean => {
    // Check if group should be greyed out due to omen incompatibility or tag filtering
    const omentIncompatible = groupMods.every(mod => shouldGreyOutMod(mod, modType))
    const tagFiltered = activeTagFilters.size > 0 && !groupMods.some(mod => isModMatchingTagFilters(mod))
    return omentIncompatible || tagFiltered
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



  const getDisplayName = (slot: string, category: string) => {
    return `${category.replace('_', ' ')} ${slot.replace('_', ' ')}`
  }

  const formatSlotName = (slot: string) => {
    return slot.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
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

  const isModMatchingTagFilters = (mod: any) => {
    if (activeTagFilters.size === 0) return true
    if (!mod.tags) return false
    return Array.from(activeTagFilters).every(filter => mod.tags.includes(filter))
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

  const formatCategoryName = (category: string) => {
    return category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  const formatStatName = (statName: string) => {
    const statNames: Record<string, string> = {
      'armour': 'Armour',
      'evasion': 'Evasion Rating',
      'energy_shield': 'Energy Shield',
    }
    return statNames[statName] || statName
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

    // Handle Essences - based on poe2wiki.net/wiki/Essence
    if (currency.includes('Essence of')) {
      // Map essence names to actual PoE2 wiki icon URLs - Complete list from poe2wiki.net
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

      // Check which essence this is (works for Greater/Perfect variants too)
      for (const [key, url] of Object.entries(essenceIconMap)) {
        if (currency.includes(key)) {
          return url
        }
      }
    }

    // Handle Abyssal Bones
    if (currency.includes('Bone') || currency.includes('bone') || currency.startsWith('Abyssal') || currency.startsWith('Ancient')) {
      const boneIconMap: Record<string, string> = {
        // Ancient bones
        'Ancient Collarbone': 'https://www.poe2wiki.net/images/2/29/Ancient_Collarbone_inventory_icon.png',
        'Ancient Jawbone': 'https://www.poe2wiki.net/images/7/79/Ancient_Jawbone_inventory_icon.png',
        'Ancient Rib': 'https://www.poe2wiki.net/images/9/9d/Ancient_Rib_inventory_icon.png',

        // Preserved bones
        'Preserved Collarbone': 'https://www.poe2wiki.net/images/7/7a/Preserved_Collarbone_inventory_icon.png',
        'Preserved Jawbone': 'https://www.poe2wiki.net/images/4/47/Preserved_Jawbone_inventory_icon.png',

        // Abyssal bones (fallback to Ancient variants)
        'Abyssal Collarbone': 'https://www.poe2wiki.net/images/2/29/Ancient_Collarbone_inventory_icon.png',
        'Abyssal Jawbone': 'https://www.poe2wiki.net/images/7/79/Ancient_Jawbone_inventory_icon.png',
        'Abyssal Rib': 'https://www.poe2wiki.net/images/9/9d/Ancient_Rib_inventory_icon.png',
      }

      // Check for exact match first
      if (boneIconMap[currency]) {
        return boneIconMap[currency]
      }

      // Fallback for any unmatched bone - check if it contains key terms
      if (currency.includes('Collarbone')) return 'https://www.poe2wiki.net/images/2/29/Ancient_Collarbone_inventory_icon.png'
      if (currency.includes('Jawbone')) return 'https://www.poe2wiki.net/images/7/79/Ancient_Jawbone_inventory_icon.png'
      if (currency.includes('Rib')) return 'https://www.poe2wiki.net/images/9/9d/Ancient_Rib_inventory_icon.png'

      // Default bone icon
      return 'https://www.poe2wiki.net/images/2/29/Ancient_Collarbone_inventory_icon.png'
    }

    return iconMap[currency] || "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
  }


  const getOmenIconUrl = (omen: string): string => {
    // Based on poe2wiki.net/wiki/Category:Omen_icons - Correct URLs verified from wiki
    const omenIconMap: Record<string, string> = {
      "Omen of Whittling": "https://www.poe2wiki.net/images/8/81/Omen_of_Whittling_inventory_icon.png",
      "Omen of Greater Exaltation": "https://www.poe2wiki.net/images/6/6b/Omen_of_Greater_Exaltation_inventory_icon.png",
      "Omen of Sinistral Exaltation": "https://www.poe2wiki.net/images/0/06/Omen_of_Sinistral_Exaltation_inventory_icon.png",
      "Omen of Dextral Exaltation": "https://www.poe2wiki.net/images/4/4d/Omen_of_Dextral_Exaltation_inventory_icon.png",
      "Omen of Homogenising Exaltation": "https://www.poe2wiki.net/images/6/60/Omen_of_Homogenising_Exaltation_inventory_icon.png",
      "Omen of Catalysing Exaltation": "https://www.poe2wiki.net/images/9/9b/Omen_of_Catalysing_Exaltation_inventory_icon.png",
      "Omen of Sinistral Erasure": "https://www.poe2wiki.net/images/4/47/Omen_of_Sinistral_Erasure_inventory_icon.png",
      "Omen of Dextral Erasure": "https://www.poe2wiki.net/images/0/0b/Omen_of_Dextral_Erasure_inventory_icon.png",
      "Omen of Greater Annulment": "https://www.poe2wiki.net/images/d/df/Omen_of_Greater_Annulment_inventory_icon.png",
      "Omen of Sinistral Annulment": "https://www.poe2wiki.net/images/4/45/Omen_of_Sinistral_Annulment_inventory_icon.png",
      "Omen of Dextral Annulment": "https://www.poe2wiki.net/images/e/ef/Omen_of_Dextral_Annulment_inventory_icon.png",
      "Omen of Sinistral Coronation": "https://www.poe2wiki.net/images/6/66/Omen_of_Sinistral_Coronation_inventory_icon.png",
      "Omen of Dextral Coronation": "https://www.poe2wiki.net/images/1/1c/Omen_of_Dextral_Coronation_inventory_icon.png",
      "Omen of Homogenising Coronation": "https://www.poe2wiki.net/images/0/0b/Omen_of_Homogenising_Coronation_inventory_icon.png",
      "Omen of Sinistral Alchemy": "https://www.poe2wiki.net/images/b/b6/Omen_of_Sinistral_Alchemy_inventory_icon.png",
      "Omen of Dextral Alchemy": "https://www.poe2wiki.net/images/2/2c/Omen_of_Dextral_Alchemy_inventory_icon.png",
      "Omen of Corruption": "https://www.poe2wiki.net/images/a/a2/Omen_of_Corruption_inventory_icon.png"
    }
    return omenIconMap[omen] || "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
  }


  const handlePasteItem = async () => {
    if (!itemPasteText.trim()) {
      setPasteMessage('Please paste item text')
      return
    }

    setLoading(true)
    setPasteMessage('')

    try {
      const result = await craftingApi.parseItem(itemPasteText)

      if (result.success && result.item) {
        setItem(result.item)
        setSelectedSlot(result.parsed_info.base_type.includes('Body Armour') || result.parsed_info.base_type.includes('Robe') || result.parsed_info.base_type.includes('Vest') || result.parsed_info.base_type.includes('Plate') ? 'body_armour' : 'body_armour')
        setSelectedCategory(result.item.base_category)
        setPasteMessage(`✓ Loaded ${result.parsed_info.rarity} ${result.parsed_info.base_type}`)
        setHistory([])
        setItemHistory([])
        setCurrencySpent({})
        setPasteExpanded(false)
        setItemPasteText('')
      }
    } catch (err: any) {
      setPasteMessage(`✗ Error: ${err.response?.data?.detail || 'Failed to parse item'}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="crafting-simulator">
      <h2 className="page-title">Crafting Simulator</h2>
      <p className="page-subtitle">Experiment with crafting currencies on items</p>

      <div className="item-paste-section">
        <div className="paste-header" onClick={() => setPasteExpanded(!pasteExpanded)}>
          <h3>Paste Item from Game {pasteExpanded ? '▼' : '▶'}</h3>
        </div>
        {pasteExpanded && (
          <div className="paste-content">
            <p className="paste-instructions">
              Copy an item from PoE2 (Ctrl+C in-game) and paste it here. Both simple and detailed formats are supported.
            </p>
            <textarea
              className="item-paste-textarea"
              value={itemPasteText}
              onChange={(e) => setItemPasteText(e.target.value)}
              placeholder="Item Class: Body Armours&#10;Rarity: Rare&#10;Viper Coat&#10;Vile Robe&#10;--------&#10;Quality: +20% (augmented)&#10;..."
              rows={12}
            />
            <div className="paste-actions">
              <button
                className="paste-button"
                onClick={handlePasteItem}
                disabled={loading || !itemPasteText.trim()}
              >
                Load Item
              </button>
              <button
                className="clear-button"
                onClick={() => { setItemPasteText(''); setPasteMessage('') }}
                disabled={!itemPasteText}
              >
                Clear
              </button>
            </div>
            {pasteMessage && (
              <div className={`paste-message ${pasteMessage.startsWith('✓') ? 'success' : 'error'}`}>
                {pasteMessage}
              </div>
            )}
          </div>
        )}
      </div>

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
                // Reset bases when slot changes
                setAvailableBases([])
                setSelectedBase('')
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
                // Don't update the item here, wait for base selection
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

          <div className="base-selector">
            <label htmlFor="base-select">Base:</label>
            <select
              id="base-select"
              value={selectedBase}
              onChange={(e) => {
                const selectedBaseName = e.target.value
                const selectedBaseData = availableBases.find(base => base.name === selectedBaseName)
                const baseStats = selectedBaseData?.base_stats || {}

                setSelectedBase(selectedBaseName)
                setItem({
                  base_name: selectedBaseName,
                  base_category: selectedCategory,
                  rarity: 'Normal' as ItemRarity,
                  item_level: 65,
                  quality: 20,
                  implicit_mods: [],
                  prefix_mods: [],
                  suffix_mods: [],
                  corrupted: false,
                  base_stats: baseStats,
                  calculated_stats: calculateItemStats(baseStats, 20),
                })
                setMessage('')
                setHistory([])
                setItemHistory([])
                setCurrencySpent({})
              }}
              disabled={availableBases.length === 0}
            >
              {availableBases.map((base, index) => {
                const statsText = Object.entries(base.base_stats || {})
                  .map(([stat, value]) => `${value} ${formatStatName(stat)}`)
                  .join(', ')

                return (
                  <option
                    key={`${base.name}-${index}-${JSON.stringify(base.base_stats)}`}
                    value={base.name}
                    title={`${base.description}${statsText ? ` - ${statsText}` : ''}`}
                  >
                    {base.name}{statsText ? ` (${statsText})` : ''}
                  </option>
                )
              })}
            </select>
          </div>

          <div className="ilvl-selector">
            <label htmlFor="ilvl-input">Item Level:</label>
            <input
              id="ilvl-input"
              type="number"
              min="1"
              max="100"
              value={item.item_level}
              onChange={(e) => {
                const newIlvl = parseInt(e.target.value) || 1
                setItem({ ...item, item_level: Math.max(1, Math.min(100, newIlvl)) })
              }}
            />
          </div>

          <div className="base-info">
            <span className="base-category">{selectedCategory}</span>
            <span className="base-ilvl">ilvl {item.item_level}</span>
            <span className="base-slot">{formatSlotName(selectedSlot)}</span>
          </div>
        </div>
      </div>


      <div className={`simulator-layout ${modsPoolCollapsed ? 'mods-collapsed' : ''}`}>
        <div
          className="mods-pool-panel"
          style={{ width: modsPoolCollapsed ? '60px' : `${modsPoolWidth}px` }}
        >
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

                {/* Tag Filters */}
                <div className="tag-filters">
                  <span className="tag-filters-label">Filter by tags:</span>
                  <button
                    className={`clear-filters-btn ${activeTagFilters.size === 0 ? 'disabled' : ''}`}
                    onClick={clearTagFilters}
                    disabled={activeTagFilters.size === 0}
                    title={activeTagFilters.size > 0 ? `Clear ${activeTagFilters.size} active filters` : 'No active filters'}
                  >
                    ↺
                  </button>
                  {allAvailableTags.map(tag => (
                    <span
                      key={tag}
                      className={`legend-tag-text ${activeTagFilters.has(tag) ? 'active-filter' : ''}`}
                      data-tag={tag}
                      onClick={() => toggleTagFilter(tag)}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
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
                  const availableMods = groupMods.filter(m => !m.required_ilvl || m.required_ilvl <= item.item_level)
                  const bestAvailableTier = availableMods.length > 0 ? Math.min(...availableMods.map(m => m.tier)) : null
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
                          <span className={`group-tier-range ${allUnavailable ? 'all-unavailable' : ''}`}>{tierRangeText}</span>
                          <span className="group-max-ilvl">ilvl {maxIlvl}</span>
                          <span className="expand-indicator">{isExpanded ? '▼' : '▶'}</span>
                          {bestTier.tags && bestTier.tags.length > 0 && (
                            <div className="mod-tags-line" title="Click individual tags to filter, or double-click the mod to apply all tags">
                              {bestTier.tags.map((tag, i) => (
                                <span
                                  key={i}
                                  className={`mod-tag-text ${activeTagFilters.has(tag) ? 'active-filter' : ''}`}
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
                  const availableMods = groupMods.filter(m => !m.required_ilvl || m.required_ilvl <= item.item_level)
                  const bestAvailableTier = availableMods.length > 0 ? Math.min(...availableMods.map(m => m.tier)) : null
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
                          <span className={`group-tier-range ${allUnavailable ? 'all-unavailable' : ''}`}>{tierRangeText}</span>
                          <span className="group-max-ilvl">ilvl {maxIlvl}</span>
                          <span className="expand-indicator">{isExpanded ? '▼' : '▶'}</span>
                          {bestTier.tags && bestTier.tags.length > 0 && (
                            <div className="mod-tags-line" title="Click individual tags to filter, or double-click the mod to apply all tags">
                              {bestTier.tags.map((tag, i) => (
                                <span
                                  key={i}
                                  className={`mod-tag-text ${activeTagFilters.has(tag) ? 'active-filter' : ''}`}
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
            </>
          )}
        </div>
        {!modsPoolCollapsed && (
          <div
            className="resize-handle"
            onMouseDown={() => setIsResizing(true)}
          >
            <div className="resize-line" />
          </div>
        )}
        <div className="center-panel">
          {/* Currency Section - moved above item preview */}
          <div
            className="currency-section-compact"
            style={{ height: `${verticalSizes.currencyCompact}px`, overflow: 'auto' }}
          >
            {/* All currencies and omens in five tables */}
            <div className="currency-five-tables">
              {/* Table 1: All orb families */}
              <div className="currency-table">
                <h5 className="currency-table-title">Orbs</h5>
                <div className="currency-horizontal-rows">
                  {/* Transmutation family */}
                  <div className="currency-family-row">
                    {['Orb of Transmutation', 'Greater Orb of Transmutation', 'Perfect Orb of Transmutation'].map((currency) => {
                      const isImplemented = categorizedCurrencies.orbs.implemented.includes(currency)
                      const isAvailable = availableCurrencies.includes(currency) && isImplemented
                      const isSelected = selectedCurrency === currency
                      const additionalMechanics = !isImplemented
                        ? "Not implemented yet - coming soon!"
                        : isAvailable
                          ? "Double-click to apply"
                          : "Not available for this item"

                      return (
                        <Tooltip
                          key={currency}
                          content={
                            <CurrencyTooltipWrapper
                              currencyName={currency}
                              additionalMechanics={additionalMechanics}
                            />
                          }
                          delay={0}
                          position="top"
                        >
                          <div
                            className={`currency-icon-button has-tooltip ${!isAvailable ? 'currency-disabled' : ''} ${isSelected ? 'currency-selected' : ''}`}
                            onClick={() => {
                              if (isAvailable) {
                                if (selectedCurrency === currency) {
                                  // Deselect if same currency is clicked
                                  setSelectedCurrency('')
                                  setAvailableOmens([])
                                  setSelectedOmens([])
                                } else {
                                  setSelectedCurrency(currency)
                                  loadAvailableOmens(currency)
                                  setSelectedOmens([]) // Clear omens when switching currency
                                }
                              }
                            }}
                            onDoubleClick={() => isAvailable && handleCraft(currency)}
                          >
                            <img
                              src={getCurrencyIconUrl(currency)}
                              alt={currency}
                              className="currency-icon-img"
                              onError={(e) => {
                                (e.target as HTMLImageElement).src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
                              }}
                            />
                          </div>
                        </Tooltip>
                      )
                    })}
                  </div>
                  {/* Augmentation family */}
                  <div className="currency-family-row">
                    {['Orb of Augmentation', 'Greater Orb of Augmentation', 'Perfect Orb of Augmentation'].map((currency) => {
                      const isImplemented = categorizedCurrencies.orbs.implemented.includes(currency)
                      const isAvailable = availableCurrencies.includes(currency) && isImplemented
                      const isSelected = selectedCurrency === currency
                      const additionalMechanics = !isImplemented
                        ? "Not implemented yet - coming soon!"
                        : isAvailable
                          ? "Double-click to apply"
                          : "Not available for this item"

                      return (
                        <Tooltip
                          key={currency}
                          content={
                            <CurrencyTooltipWrapper
                              currencyName={currency}
                              additionalMechanics={additionalMechanics}
                            />
                          }
                          delay={0}
                          position="top"
                        >
                          <div
                            className={`currency-icon-button has-tooltip ${!isAvailable ? 'currency-disabled' : ''} ${isSelected ? 'currency-selected' : ''}`}
                            onClick={() => {
                              if (isAvailable) {
                                if (selectedCurrency === currency) {
                                  // Deselect if same currency is clicked
                                  setSelectedCurrency('')
                                  setAvailableOmens([])
                                  setSelectedOmens([])
                                } else {
                                  setSelectedCurrency(currency)
                                  loadAvailableOmens(currency)
                                  setSelectedOmens([]) // Clear omens when switching currency
                                }
                              }
                            }}
                            onDoubleClick={() => isAvailable && handleCraft(currency)}
                          >
                            <img
                              src={getCurrencyIconUrl(currency)}
                              alt={currency}
                              className="currency-icon-img"
                              onError={(e) => {
                                (e.target as HTMLImageElement).src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
                              }}
                            />
                          </div>
                        </Tooltip>
                      )
                    })}
                  </div>
                  {/* Regal family */}
                  <div className="currency-family-row">
                    {['Regal Orb', 'Greater Regal Orb', 'Perfect Regal Orb'].map((currency) => {
                      const isImplemented = categorizedCurrencies.orbs.implemented.includes(currency)
                      const isAvailable = availableCurrencies.includes(currency) && isImplemented
                      const isSelected = selectedCurrency === currency
                      const additionalMechanics = !isImplemented
                        ? "Not implemented yet - coming soon!"
                        : isAvailable
                          ? "Double-click to apply"
                          : "Not available for this item"

                      return (
                        <Tooltip
                          key={currency}
                          content={
                            <CurrencyTooltipWrapper
                              currencyName={currency}
                              additionalMechanics={additionalMechanics}
                            />
                          }
                          delay={0}
                          position="top"
                        >
                          <div
                            className={`currency-icon-button has-tooltip ${!isAvailable ? 'currency-disabled' : ''} ${isSelected ? 'currency-selected' : ''}`}
                            onClick={() => {
                              if (isAvailable) {
                                if (selectedCurrency === currency) {
                                  // Deselect if same currency is clicked
                                  setSelectedCurrency('')
                                  setAvailableOmens([])
                                  setSelectedOmens([])
                                } else {
                                  setSelectedCurrency(currency)
                                  loadAvailableOmens(currency)
                                  setSelectedOmens([]) // Clear omens when switching currency
                                }
                              }
                            }}
                            onDoubleClick={() => isAvailable && handleCraft(currency)}
                          >
                            <img
                              src={getCurrencyIconUrl(currency)}
                              alt={currency}
                              className="currency-icon-img"
                              onError={(e) => {
                                (e.target as HTMLImageElement).src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
                              }}
                            />
                          </div>
                        </Tooltip>
                      )
                    })}
                  </div>
                  {/* Exalted family */}
                  <div className="currency-family-row">
                    {['Exalted Orb', 'Greater Exalted Orb', 'Perfect Exalted Orb'].map((currency) => {
                      const isImplemented = categorizedCurrencies.orbs.implemented.includes(currency)
                      const isAvailable = availableCurrencies.includes(currency) && isImplemented
                      const isSelected = selectedCurrency === currency
                      const additionalMechanics = !isImplemented
                        ? "Not implemented yet - coming soon!"
                        : isAvailable
                          ? "Double-click to apply"
                          : "Not available for this item"

                      return (
                        <Tooltip
                          key={currency}
                          content={
                            <CurrencyTooltipWrapper
                              currencyName={currency}
                              additionalMechanics={additionalMechanics}
                            />
                          }
                          delay={0}
                          position="top"
                        >
                          <div
                            className={`currency-icon-button has-tooltip ${!isAvailable ? 'currency-disabled' : ''} ${isSelected ? 'currency-selected' : ''}`}
                            onClick={() => {
                              if (isAvailable) {
                                if (selectedCurrency === currency) {
                                  // Deselect if same currency is clicked
                                  setSelectedCurrency('')
                                  setAvailableOmens([])
                                  setSelectedOmens([])
                                } else {
                                  setSelectedCurrency(currency)
                                  loadAvailableOmens(currency)
                                  setSelectedOmens([]) // Clear omens when switching currency
                                }
                              }
                            }}
                            onDoubleClick={() => isAvailable && handleCraft(currency)}
                          >
                            <img
                              src={getCurrencyIconUrl(currency)}
                              alt={currency}
                              className="currency-icon-img"
                              onError={(e) => {
                                (e.target as HTMLImageElement).src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
                              }}
                            />
                          </div>
                        </Tooltip>
                      )
                    })}
                  </div>
                  {/* Chaos family */}
                  <div className="currency-family-row">
                    {['Chaos Orb', 'Greater Chaos Orb', 'Perfect Chaos Orb'].map((currency) => {
                      const isImplemented = categorizedCurrencies.orbs.implemented.includes(currency)
                      const isAvailable = availableCurrencies.includes(currency) && isImplemented
                      const isSelected = selectedCurrency === currency
                      const additionalMechanics = !isImplemented
                        ? "Not implemented yet - coming soon!"
                        : isAvailable
                          ? "Double-click to apply"
                          : "Not available for this item"

                      return (
                        <Tooltip
                          key={currency}
                          content={
                            <CurrencyTooltipWrapper
                              currencyName={currency}
                              additionalMechanics={additionalMechanics}
                            />
                          }
                          delay={0}
                          position="top"
                        >
                          <div
                            className={`currency-icon-button has-tooltip ${!isAvailable ? 'currency-disabled' : ''} ${isSelected ? 'currency-selected' : ''}`}
                            onClick={() => {
                              if (isAvailable) {
                                if (selectedCurrency === currency) {
                                  // Deselect if same currency is clicked
                                  setSelectedCurrency('')
                                  setAvailableOmens([])
                                  setSelectedOmens([])
                                } else {
                                  setSelectedCurrency(currency)
                                  loadAvailableOmens(currency)
                                  setSelectedOmens([]) // Clear omens when switching currency
                                }
                              }
                            }}
                            onDoubleClick={() => isAvailable && handleCraft(currency)}
                          >
                            <img
                              src={getCurrencyIconUrl(currency)}
                              alt={currency}
                              className="currency-icon-img"
                              onError={(e) => {
                                (e.target as HTMLImageElement).src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
                              }}
                            />
                          </div>
                        </Tooltip>
                      )
                    })}
                  </div>
                </div>
              </div>

              {/* Table 2: Special orbs */}
              <div className="currency-table">
                <h5 className="currency-table-title">Special Orbs</h5>
                <div className="currency-horizontal-rows">
                  <div className="currency-family-row">
                    {['Orb of Alchemy', 'Vaal Orb', 'Orb of Annulment', 'Orb of Fracturing', 'Divine Orb'].map((currency) => {
                      const isImplemented = categorizedCurrencies.orbs.implemented.includes(currency)
                      const isAvailable = availableCurrencies.includes(currency) && isImplemented
                      const isSelected = selectedCurrency === currency
                      const additionalMechanics = !isImplemented
                        ? "Not implemented yet - coming soon!"
                        : isAvailable
                          ? "Double-click to apply"
                          : "Not available for this item"

                      return (
                        <Tooltip
                          key={currency}
                          content={
                            <CurrencyTooltipWrapper
                              currencyName={currency}
                              additionalMechanics={additionalMechanics}
                            />
                          }
                          delay={0}
                          position="top"
                        >
                          <div
                            className={`currency-icon-button has-tooltip ${!isAvailable ? 'currency-disabled' : ''} ${isSelected ? 'currency-selected' : ''}`}
                            onClick={() => {
                              if (isAvailable) {
                                if (selectedCurrency === currency) {
                                  // Deselect if same currency is clicked
                                  setSelectedCurrency('')
                                  setAvailableOmens([])
                                  setSelectedOmens([])
                                } else {
                                  setSelectedCurrency(currency)
                                  loadAvailableOmens(currency)
                                  setSelectedOmens([]) // Clear omens when switching currency
                                }
                              }
                            }}
                            onDoubleClick={() => isAvailable && handleCraft(currency)}
                          >
                            <img
                              src={getCurrencyIconUrl(currency)}
                              alt={currency}
                              className="currency-icon-img"
                              onError={(e) => {
                                (e.target as HTMLImageElement).src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
                              }}
                            />
                          </div>
                        </Tooltip>
                      )
                    })}
                  </div>
                </div>
              </div>

              {/* Table 3: Bones */}
              <div className="currency-table">
                <h5 className="currency-table-title">Abyssal Bones</h5>
                <div className="currency-horizontal-rows">
                  <div className="currency-family-row">
                    {categorizedCurrencies.bones.implemented.concat(categorizedCurrencies.bones.disabled).map((currency) => {
                      const isImplemented = categorizedCurrencies.bones.implemented.includes(currency)
                      const isAvailable = availableCurrencies.includes(currency) && isImplemented
                      const isSelected = selectedCurrency === currency
                      const additionalMechanics = !isImplemented
                        ? "Not implemented yet - coming soon!"
                        : isAvailable
                          ? "Double-click to apply"
                          : "Not available for this item"

                      return (
                        <Tooltip
                          key={currency}
                          content={
                            <CurrencyTooltipWrapper
                              currencyName={currency}
                              additionalMechanics={additionalMechanics}
                            />
                          }
                          delay={0}
                          position="top"
                        >
                          <div
                            className={`currency-icon-button has-tooltip ${!isAvailable ? 'currency-disabled' : ''} ${isSelected ? 'currency-selected' : ''}`}
                            onClick={() => {
                              if (isAvailable) {
                                if (selectedCurrency === currency) {
                                  // Deselect if same currency is clicked
                                  setSelectedCurrency('')
                                  setAvailableOmens([])
                                  setSelectedOmens([])
                                } else {
                                  setSelectedCurrency(currency)
                                  loadAvailableOmens(currency)
                                  setSelectedOmens([]) // Clear omens when switching currency
                                }
                              }
                            }}
                            onDoubleClick={() => isAvailable && handleCraft(currency)}
                          >
                            <img
                              src={getCurrencyIconUrl(currency)}
                              alt={currency}
                              className="currency-icon-img"
                              onError={(e) => {
                                (e.target as HTMLImageElement).src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
                              }}
                            />
                          </div>
                        </Tooltip>
                      )
                    })}
                  </div>
                </div>
              </div>

              {/* Table 5: Essences */}
              <div className="currency-table">
                <h5 className="currency-table-title">Essences</h5>
                <div className="currency-horizontal-rows">
                  <div className="currency-family-row essence-selector-row">
                    {selectedEssence ? (
                      <Tooltip
                        content={
                          <CurrencyTooltipWrapper
                            currencyName={selectedEssence}
                            additionalMechanics="Click to select as active currency, Double-click to apply, Click arrow for more essences"
                          />
                        }
                        delay={0}
                        position="top"
                      >
                        <div
                          className={`currency-icon-button has-tooltip ${selectedCurrency === selectedEssence ? 'currency-selected' : ''}`}
                          onClick={() => {
                            if (selectedCurrency === selectedEssence) {
                              setSelectedCurrency('')
                              setAvailableOmens([])
                              setSelectedOmens([])
                            } else {
                              setSelectedCurrency(selectedEssence)
                              loadAvailableOmens(selectedEssence)
                              setSelectedOmens([])
                            }
                          }}
                          onDoubleClick={() => handleCraft(selectedEssence)}
                          style={{ position: 'relative' }}
                        >
                          <img
                            src={getCurrencyIconUrl(selectedEssence)}
                            alt={selectedEssence}
                            className="currency-icon-img"
                          />
                          <button
                            className="essence-expand-arrow"
                            onClick={(e) => {
                              e.stopPropagation()
                              setEssencesModalOpen(true)
                            }}
                            title="Choose different essence"
                          >
                            ▼
                          </button>
                        </div>
                      </Tooltip>
                    ) : (
                      <div className="essence-placeholder-button" title={`Click arrow to choose Essence (${categorizedCurrencies.essences.implemented.length + categorizedCurrencies.essences.disabled.length} available)`}>
                        <span className="essences-icon">💎</span>
                        <span className="essence-placeholder-text">Select</span>
                        <button
                          className="essence-expand-arrow"
                          onClick={(e) => {
                            e.preventDefault()
                            setEssencesModalOpen(true)
                          }}
                          title="Choose Essence"
                        >
                          ▼
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Essences Modal */}
              {essencesModalOpen && (
                <div className="essence-modal-overlay" onClick={() => setEssencesModalOpen(false)}>
                  <div className="essence-modal" onClick={(e) => e.stopPropagation()}>
                    <div className="essence-modal-header">
                      <h2>Essences</h2>
                      <button className="essence-modal-close" onClick={() => setEssencesModalOpen(false)}>×</button>
                    </div>
                    <div className="essence-modal-content">
                <div className="essence-stash-layout">
                  {(() => {
                    // Group essences by type
                    const groupedEssences: Record<string, string[]> = {}

                    categorizedCurrencies.essences.implemented.concat(categorizedCurrencies.essences.disabled).forEach(essence => {
                      let baseType = ''
                      if (essence.includes('the Body')) baseType = 'the Body'
                      else if (essence.includes('the Mind')) baseType = 'the Mind'
                      else if (essence.includes('Enhancement')) baseType = 'Enhancement'
                      else if (essence.includes('Flames')) baseType = 'Flames'
                      else if (essence.includes('Insulation')) baseType = 'Insulation'
                      else if (essence.includes('Ice')) baseType = 'Ice'
                      else if (essence.includes('Thawing')) baseType = 'Thawing'
                      else if (essence.includes('Electricity')) baseType = 'Electricity'
                      else if (essence.includes('Grounding')) baseType = 'Grounding'
                      else if (essence.includes('Ruin')) baseType = 'Ruin'
                      else if (essence.includes('Command')) baseType = 'Command'
                      else if (essence.includes('Abrasion')) baseType = 'Abrasion'
                      else if (essence.includes('Sorcery')) baseType = 'Sorcery'
                      else if (essence.includes('Haste')) baseType = 'Haste'
                      else if (essence.includes('Alacrity')) baseType = 'Alacrity'
                      else if (essence.includes('Seeking')) baseType = 'Seeking'
                      else if (essence.includes('Battle')) baseType = 'Battle'
                      else if (essence.includes('the Infinite')) baseType = 'the Infinite'
                      else if (essence.includes('Opulence')) baseType = 'Opulence'
                      else if (essence.includes('Hysteria') || essence.includes('Delirium') || essence.includes('Horror') || essence.includes('Insanity') || essence.includes('the Abyss')) baseType = 'Corrupted'
                      else {
                        console.log('Unmatched essence:', essence)
                        baseType = 'Other'
                      }

                      if (!groupedEssences[baseType]) {
                        groupedEssences[baseType] = []
                      }
                      groupedEssences[baseType].push(essence)
                    })

                    // Sort each group by tier
                    Object.keys(groupedEssences).forEach(baseType => {
                      groupedEssences[baseType].sort((a, b) => {
                        const getTierOrder = (name: string) => {
                          if (name.startsWith('Lesser Essence')) return 1
                          if (name.startsWith('Essence of')) return 2
                          if (name.startsWith('Greater Essence')) return 3
                          if (name.startsWith('Perfect Essence')) return 4
                          return 5
                        }
                        return getTierOrder(a) - getTierOrder(b)
                      })
                    })

                    const renderEssenceRow = (baseType: string) => {
                      if (!groupedEssences[baseType] || groupedEssences[baseType].length === 0) return null

                      return (
                        <div key={baseType} className="essence-type-row">
                          {groupedEssences[baseType].map((currency) => {
                            const isImplemented = categorizedCurrencies.essences.implemented.includes(currency)
                            const isAvailable = availableCurrencies.includes(currency) && isImplemented
                            const isSelected = selectedEssence === currency
                            const additionalMechanics = !isImplemented
                              ? "Not implemented yet - coming soon!"
                              : isAvailable
                                ? "Double-click to apply"
                                : "Not available for this item"

                            return (
                              <Tooltip
                                key={currency}
                                content={
                                  <div className="essence-tooltip">
                                    <CurrencyTooltipWrapper
                                      currencyName={currency}
                                      additionalMechanics={additionalMechanics}
                                    />
                                  </div>
                                }
                                delay={0}
                                position="top"
                              >
                                <div
                                  className={`currency-icon-button has-tooltip ${!isAvailable ? 'currency-disabled' : ''} ${isSelected ? 'currency-selected' : ''}`}
                                  onClick={() => {
                                    if (isAvailable) {
                                      setSelectedEssence(currency)
                                      setEssencesModalOpen(false)
                                    }
                                  }}
                                  onDoubleClick={() => {
                                    if (isAvailable) {
                                      handleCraft(currency)
                                      setEssencesModalOpen(false)
                                    }
                                  }}
                                >
                                  <img
                                    src={getCurrencyIconUrl(currency)}
                                    alt={currency}
                                    className="currency-icon-img"
                                    onError={(e) => {
                                      (e.target as HTMLImageElement).src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
                                    }}
                                  />
                                </div>
                              </Tooltip>
                            )
                          })}
                        </div>
                      )
                    }

                    return (
                      <>
                        {/* Column 1: Main essences */}
                        <div className="essence-column-1">
                          {renderEssenceRow('the Body')}
                          {renderEssenceRow('the Mind')}
                          {renderEssenceRow('Enhancement')}
                          {renderEssenceRow('Flames')}
                          {renderEssenceRow('Insulation')}
                          {renderEssenceRow('Ice')}
                          {renderEssenceRow('Thawing')}
                          {renderEssenceRow('Electricity')}
                          {renderEssenceRow('Grounding')}
                          {renderEssenceRow('Ruin')}
                        </div>

                        {/* Column 2: Corrupted essences */}
                        <div className="essence-column-2">
                          <div className="corrupted-essences">
                            <div className="corrupted-row">
                              {groupedEssences['Corrupted']?.filter(e => e.includes('Hysteria')).map(currency => (
                                <Tooltip
                                  key={currency}
                                  content={
                                    <div className="essence-tooltip">
                                      <CurrencyTooltipWrapper currencyName={currency} />
                                    </div>
                                  }
                                >
                                  <div
                                    className={`currency-icon-button ${selectedEssence === currency ? 'currency-selected' : ''}`}
                                    onClick={() => {
                                      setSelectedEssence(currency)
                                      setEssencesModalOpen(false)
                                    }}
                                    onDoubleClick={() => {
                                      handleCraft(currency)
                                      setEssencesModalOpen(false)
                                    }}
                                  >
                                    <img src={getCurrencyIconUrl(currency)} alt={currency} className="currency-icon-img" />
                                  </div>
                                </Tooltip>
                              ))}
                              {groupedEssences['Corrupted']?.filter(e => e.includes('Horror')).map(currency => (
                                <Tooltip
                                  key={currency}
                                  content={
                                    <div className="essence-tooltip">
                                      <CurrencyTooltipWrapper currencyName={currency} />
                                    </div>
                                  }
                                >
                                  <div
                                    className={`currency-icon-button ${selectedEssence === currency ? 'currency-selected' : ''}`}
                                    onClick={() => {
                                      setSelectedEssence(currency)
                                      setEssencesModalOpen(false)
                                    }}
                                    onDoubleClick={() => {
                                      handleCraft(currency)
                                      setEssencesModalOpen(false)
                                    }}
                                  >
                                    <img src={getCurrencyIconUrl(currency)} alt={currency} className="currency-icon-img" />
                                  </div>
                                </Tooltip>
                              ))}
                            </div>
                            <div className="corrupted-row">
                              {groupedEssences['Corrupted']?.filter(e => e.includes('Delirium')).map(currency => (
                                <Tooltip
                                  key={currency}
                                  content={
                                    <div className="essence-tooltip">
                                      <CurrencyTooltipWrapper currencyName={currency} />
                                    </div>
                                  }
                                >
                                  <div
                                    className={`currency-icon-button ${selectedEssence === currency ? 'currency-selected' : ''}`}
                                    onClick={() => {
                                      setSelectedEssence(currency)
                                      setEssencesModalOpen(false)
                                    }}
                                    onDoubleClick={() => {
                                      handleCraft(currency)
                                      setEssencesModalOpen(false)
                                    }}
                                  >
                                    <img src={getCurrencyIconUrl(currency)} alt={currency} className="currency-icon-img" />
                                  </div>
                                </Tooltip>
                              ))}
                              {groupedEssences['Corrupted']?.filter(e => e.includes('Insanity')).map(currency => (
                                <Tooltip
                                  key={currency}
                                  content={
                                    <div className="essence-tooltip">
                                      <CurrencyTooltipWrapper currencyName={currency} />
                                    </div>
                                  }
                                >
                                  <div
                                    className={`currency-icon-button ${selectedEssence === currency ? 'currency-selected' : ''}`}
                                    onClick={() => {
                                      setSelectedEssence(currency)
                                      setEssencesModalOpen(false)
                                    }}
                                    onDoubleClick={() => {
                                      handleCraft(currency)
                                      setEssencesModalOpen(false)
                                    }}
                                  >
                                    <img src={getCurrencyIconUrl(currency)} alt={currency} className="currency-icon-img" />
                                  </div>
                                </Tooltip>
                              ))}
                            </div>
                            <div className="corrupted-row abyss-row">
                              {groupedEssences['Corrupted']?.filter(e => e.includes('the Abyss')).map(currency => (
                                <Tooltip
                                  key={currency}
                                  content={
                                    <div className="essence-tooltip">
                                      <CurrencyTooltipWrapper currencyName={currency} />
                                    </div>
                                  }
                                >
                                  <div
                                    className={`currency-icon-button ${selectedEssence === currency ? 'currency-selected' : ''}`}
                                    onClick={() => {
                                      setSelectedEssence(currency)
                                      setEssencesModalOpen(false)
                                    }}
                                    onDoubleClick={() => {
                                      handleCraft(currency)
                                      setEssencesModalOpen(false)
                                    }}
                                  >
                                    <img src={getCurrencyIconUrl(currency)} alt={currency} className="currency-icon-img" />
                                  </div>
                                </Tooltip>
                              ))}
                            </div>
                          </div>
                        </div>

                        {/* Column 3: Remaining essences */}
                        <div className="essence-column-3">
                          {renderEssenceRow('Command')}
                          {renderEssenceRow('Abrasion')}
                          {renderEssenceRow('Sorcery')}
                          {renderEssenceRow('Haste')}
                          {renderEssenceRow('Alacrity')}
                          {renderEssenceRow('Seeking')}
                          {renderEssenceRow('Battle')}
                          {renderEssenceRow('the Infinite')}
                          {renderEssenceRow('Opulence')}
                        </div>
                      </>
                    )
                  })()}
                </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Table 5: Omens */}
              <div className="currency-table omen-table">
                <h5 className="currency-table-title">Omens</h5>
                <div className="currency-horizontal-rows">
                  {/* Exalted Orb Omens */}
                  <div className="omen-group">
                    <span className="omen-group-label">Exalted</span>
                    <div className="currency-family-row">
                      {['Omen of Greater Exaltation', 'Omen of Sinistral Exaltation', 'Omen of Dextral Exaltation', 'Omen of Homogenising Exaltation', 'Omen of Catalysing Exaltation'].map((omen) => {
                        const isActive = selectedOmens.includes(omen)
                        const isCompatible = selectedCurrency !== '' && availableOmens.includes(omen)
                        const description = getOmenDescription(omen)

                        return (
                          <Tooltip
                            key={omen}
                            content={
                              <div className="omen-tooltip">
                                <CurrencyTooltip
                                  name={omen}
                                  description={description}
                                  mechanics={isCompatible ? (isActive ? "Click to deselect" : "Click to select") : "Not compatible with selected currency"}
                                />
                              </div>
                            }
                            delay={0}
                            position="top"
                          >
                            <div
                              className={`currency-icon-button-small has-tooltip ${isActive ? 'omen-active' : ''} ${!isCompatible ? 'omen-incompatible' : ''}`}
                              onClick={() => isCompatible ? toggleOmen(omen) : undefined}
                            >
                              <img
                                src={getOmenIconUrl(omen)}
                                alt={omen}
                                className="currency-icon-img-small"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
                                }}
                              />
                            </div>
                          </Tooltip>
                        )
                      })}
                    </div>
                  </div>

                  {/* Regal Orb Omens */}
                  <div className="omen-group">
                    <span className="omen-group-label">Regal</span>
                    <div className="currency-family-row">
                      {['Omen of Sinistral Coronation', 'Omen of Dextral Coronation', 'Omen of Homogenising Coronation'].map((omen) => {
                        const isActive = selectedOmens.includes(omen)
                        const isCompatible = selectedCurrency !== '' && availableOmens.includes(omen)
                        const description = getOmenDescription(omen)

                        return (
                          <Tooltip
                            key={omen}
                            content={
                              <div className="omen-tooltip">
                                <CurrencyTooltip
                                  name={omen}
                                  description={description}
                                  mechanics={isCompatible ? (isActive ? "Click to deselect" : "Click to select") : "Not compatible with selected currency"}
                                />
                              </div>
                            }
                            delay={0}
                            position="top"
                          >
                            <div
                              className={`currency-icon-button-small has-tooltip ${isActive ? 'omen-active' : ''} ${!isCompatible ? 'omen-incompatible' : ''}`}
                              onClick={() => isCompatible ? toggleOmen(omen) : undefined}
                            >
                              <img
                                src={getOmenIconUrl(omen)}
                                alt={omen}
                                className="currency-icon-img-small"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
                                }}
                              />
                            </div>
                          </Tooltip>
                        )
                      })}
                    </div>
                  </div>

                  {/* Chaos/Removal Omens */}
                  <div className="omen-group">
                    <span className="omen-group-label">Chaos</span>
                    <div className="currency-family-row">
                      {['Omen of Whittling', 'Omen of Sinistral Erasure', 'Omen of Dextral Erasure'].map((omen) => {
                        const isActive = selectedOmens.includes(omen)
                        const isCompatible = selectedCurrency !== '' && availableOmens.includes(omen)
                        const description = getOmenDescription(omen)

                        return (
                          <Tooltip
                            key={omen}
                            content={
                              <div className="omen-tooltip">
                                <CurrencyTooltip
                                  name={omen}
                                  description={description}
                                  mechanics={isCompatible ? (isActive ? "Click to deselect" : "Click to select") : "Not compatible with selected currency"}
                                />
                              </div>
                            }
                            delay={0}
                            position="top"
                          >
                            <div
                              className={`currency-icon-button-small has-tooltip ${isActive ? 'omen-active' : ''} ${!isCompatible ? 'omen-incompatible' : ''}`}
                              onClick={() => isCompatible ? toggleOmen(omen) : undefined}
                            >
                              <img
                                src={getOmenIconUrl(omen)}
                                alt={omen}
                                className="currency-icon-img-small"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
                                }}
                              />
                            </div>
                          </Tooltip>
                        )
                      })}
                    </div>
                  </div>

                  {/* Annulment Omens */}
                  <div className="omen-group">
                    <span className="omen-group-label">Annulment</span>
                    <div className="currency-family-row">
                      {['Omen of Greater Annulment', 'Omen of Sinistral Annulment', 'Omen of Dextral Annulment'].map((omen) => {
                        const isActive = selectedOmens.includes(omen)
                        const isCompatible = selectedCurrency !== '' && availableOmens.includes(omen)
                        const description = getOmenDescription(omen)

                        return (
                          <Tooltip
                            key={omen}
                            content={
                              <div className="omen-tooltip">
                                <CurrencyTooltip
                                  name={omen}
                                  description={description}
                                  mechanics={isCompatible ? (isActive ? "Click to deselect" : "Click to select") : "Not compatible with selected currency"}
                                />
                              </div>
                            }
                            delay={0}
                            position="top"
                          >
                            <div
                              className={`currency-icon-button-small has-tooltip ${isActive ? 'omen-active' : ''} ${!isCompatible ? 'omen-incompatible' : ''}`}
                              onClick={() => isCompatible ? toggleOmen(omen) : undefined}
                            >
                              <img
                                src={getOmenIconUrl(omen)}
                                alt={omen}
                                className="currency-icon-img-small"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
                                }}
                              />
                            </div>
                          </Tooltip>
                        )
                      })}
                    </div>
                  </div>

                  {/* Alchemy & Other Omens */}
                  <div className="omen-group">
                    <span className="omen-group-label">Other</span>
                    <div className="currency-family-row">
                      {['Omen of Sinistral Alchemy', 'Omen of Dextral Alchemy', 'Omen of Corruption'].map((omen) => {
                        const isActive = selectedOmens.includes(omen)
                        const isCompatible = selectedCurrency !== '' && availableOmens.includes(omen)
                        const description = getOmenDescription(omen)

                        return (
                          <Tooltip
                            key={omen}
                            content={
                              <div className="omen-tooltip">
                                <CurrencyTooltip
                                  name={omen}
                                  description={description}
                                  mechanics={isCompatible ? (isActive ? "Click to deselect" : "Click to select") : "Not compatible with selected currency"}
                                />
                              </div>
                            }
                            delay={0}
                            position="top"
                          >
                            <div
                              className={`currency-icon-button-small has-tooltip ${isActive ? 'omen-active' : ''} ${!isCompatible ? 'omen-incompatible' : ''}`}
                              onClick={() => isCompatible ? toggleOmen(omen) : undefined}
                            >
                              <img
                                src={getOmenIconUrl(omen)}
                                alt={omen}
                                className="currency-icon-img-small"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png"
                                }}
                              />
                            </div>
                          </Tooltip>
                        )
                      })}
                    </div>
                  </div>
                </div>
              </div>

              {/* Selected omens info */}
              {selectedOmens.length > 0 && (
                <div className="selected-omens-info">
                  <h6>Selected Omens:</h6>
                  <div className="selected-omens-list">
                    {selectedOmens.map((omen) => (
                      <span key={omen} className="selected-omen-tag">
                        {omen}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {message && (
              <div className={`message-inline ${message.startsWith('✓') ? 'success' : 'error'}`}>
                {message}
              </div>
            )}
          </div>

          {/* Vertical resize handle after currency section */}
          <div
            className="resize-handle-vertical"
            onMouseDown={(e) => handleVerticalResizeStart('currencyCompact', e)}
          >
            <div className="resize-line-vertical" />
          </div>

          <div
            className="item-display"
            style={{ height: `${verticalSizes.itemDisplay}px`, overflow: 'auto' }}
          >
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

              {/* Display base/calculated stats */}
              {Object.keys(item.calculated_stats || {}).length > 0 && (
                <div className="stats-section">
                  <h4 className="stats-title">Defence</h4>
                  {Object.entries(item.calculated_stats).map(([statName, value]) => (
                    <div key={statName} className="stat-row">
                      <span className="stat-label">{formatStatName(statName)}:</span>
                      <span className="stat-value">{value}</span>
                    </div>
                  ))}
                </div>
              )}
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

          {/* Vertical resize handle after item display */}
          <div
            className="resize-handle-vertical"
            onMouseDown={(e) => handleVerticalResizeStart('itemDisplay', e)}
          >
            <div className="resize-line-vertical" />
          </div>

          <button className="reset-button" onClick={handleReset}>
            Reset Item
          </button>

          {Object.keys(currencySpent).length > 0 && (
            <>
              <div
                className="currency-tracker"
                style={{ height: `${verticalSizes.currencySection}px`, overflow: 'auto' }}
              >
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
              {/* Vertical resize handle after currency section */}
              <div
                className="resize-handle-vertical"
                onMouseDown={(e) => handleVerticalResizeStart('currencySection', e)}
              >
                <div className="resize-line-vertical" />
              </div>
            </>
          )}

          {/* Vertical resize handle before history section */}
          <div
            className="resize-handle-vertical"
            onMouseDown={(e) => handleVerticalResizeStart('historySection', e)}
          >
            <div className="resize-line-vertical" />
          </div>

          <div
            className="history-section"
            style={{ height: `${verticalSizes.historySection}px`, overflow: 'auto' }}
          >
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