import { useState, useEffect } from 'react'
import { craftingApi } from '@/services/crafting-api'
import type { CraftableItem, ItemRarity, ItemBasesBySlot, ItemBase } from '@/types/crafting'

interface ItemCreationPanelProps {
  item: CraftableItem
  onItemChange: (item: CraftableItem) => void
  onMessage: (message: string) => void
  onHistoryReset: () => void
}

export function ItemCreationPanel({ item, onItemChange, onMessage, onHistoryReset }: ItemCreationPanelProps) {
  const [availableSlots, setAvailableSlots] = useState<ItemBasesBySlot>({})
  const [selectedSlot, setSelectedSlot] = useState<string>('body_armour')
  const [selectedCategory, setSelectedCategory] = useState<string>('int_armour')
  const [availableBases, setAvailableBases] = useState<ItemBase[]>([])
  const [selectedBase, setSelectedBase] = useState<string>('')

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

  const formatStatName = (stat: string): string => {
    const statNames: Record<string, string> = {
      'armour': 'Armour',
      'evasion': 'Evasion',
      'energy_shield': 'Energy Shield',
    }
    return statNames[stat] || stat
  }

  useEffect(() => {
    loadAvailableSlots()
  }, [])

  useEffect(() => {
    if (selectedSlot && selectedCategory) {
      loadAvailableBases()
    }
  }, [selectedSlot, selectedCategory])

  const loadAvailableSlots = async () => {
    try {
      const data = await craftingApi.getItemBases()
      setAvailableSlots(data)

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
        onItemChange({
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

  return (
    <div className="item-creation-panel">
      <div className="base-selection">
        <div className="slot-selector">
          <label htmlFor="slot-select">Slot:</label>
          <select
            id="slot-select"
            value={selectedSlot}
            onChange={(e) => {
              setSelectedSlot(e.target.value)
              const categories = availableSlots[e.target.value] || []
              if (categories.length > 0) {
                setSelectedCategory(categories[0])
              }
            }}
          >
            {Object.keys(availableSlots).map(slot => (
              <option key={slot} value={slot}>
                {slot.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </option>
            ))}
          </select>
        </div>

        <div className="category-selector">
          <label htmlFor="category-select">Category:</label>
          <select
            id="category-select"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            disabled={!selectedSlot || (availableSlots[selectedSlot]?.length || 0) === 0}
          >
            {(availableSlots[selectedSlot] || []).map(category => (
              <option key={category} value={category}>
                {category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
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
              onItemChange({
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
              onMessage('')
              onHistoryReset()
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
              const newLevel = parseInt(e.target.value) || 65
              onItemChange({
                ...item,
                item_level: newLevel
              })
            }}
          />
        </div>

        <div className="quality-selector">
          <label htmlFor="quality-input">Quality:</label>
          <input
            id="quality-input"
            type="number"
            min="0"
            max="30"
            value={item.quality}
            onChange={(e) => {
              const newQuality = parseInt(e.target.value) || 0
              onItemChange({
                ...item,
                quality: newQuality,
                calculated_stats: calculateItemStats(item.base_stats, newQuality)
              })
            }}
          />
          <span>%</span>
        </div>
      </div>
    </div>
  )
}