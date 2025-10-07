import React from 'react'
import type { CraftableItem, ItemModifier } from '@/types/crafting'

interface ItemDisplayPanelProps {
  item: CraftableItem
}

export function ItemDisplayPanel({ item }: ItemDisplayPanelProps) {
  // Debug: Log fractured mods
  React.useEffect(() => {
    const allMods = [...(item.prefix_mods || []), ...(item.suffix_mods || [])]
    const fracturedMods = allMods.filter(mod => mod.is_fractured)
    if (fracturedMods.length > 0) {
      console.log('FRACTURED MODS DETECTED:', fracturedMods)
    }
  }, [item])

  const formatStatName = (stat: string): string => {
    const statNames: Record<string, string> = {
      'armour': 'Armour',
      'evasion': 'Evasion',
      'energy_shield': 'Energy Shield',
    }
    return statNames[stat] || stat
  }

  const getRarityClass = (rarity: string): string => {
    return `rarity-${rarity.toLowerCase()}`
  }

  const formatModText = (mod: ItemModifier): string => {
    let text = mod.stat_text
    if (mod.current_value !== undefined && text.includes('{}')) {
      text = text.replace('{}', mod.current_value.toString())
    }
    // Add (Fractured) indicator for fractured mods
    if (mod.is_fractured) {
      text = `${text} (Fractured)`
    }
    return text
  }

  const defenseStats = ['armour', 'evasion', 'energy_shield']
  const hasDefenseStats = Object.keys(item.calculated_stats || {}).some(stat => defenseStats.includes(stat))

  return (
    <div className="item-display-panel">
      <div className="item-preview">
        <div className={`item-tooltip ${getRarityClass(item.rarity)}`}>
          <div className="item-header">
            <h3 className="item-name">{item.base_name}</h3>
            <div className="item-level">Item Level: {item.item_level}</div>
            <div className="item-quality">Quality: +{item.quality}%</div>
          </div>

          {/* Defense Stats */}
          {hasDefenseStats && (
            <div className="item-stats-section">
              <div className="stats-header">Defense</div>
              <div className="item-stats">
                {Object.entries(item.calculated_stats || {})
                  .filter(([stat]) => defenseStats.includes(stat))
                  .map(([stat, value]) => (
                    <div key={stat} className="stat-line">
                      {value} {formatStatName(stat)}
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Implicit Mods */}
          {item.implicit_mods && item.implicit_mods.length > 0 && (
            <div className="item-stats-section">
              <div className="stats-separator"></div>
              <div className="item-stats implicit-mods">
                {item.implicit_mods.map((mod, index) => (
                  <div key={index} className="mod-line implicit">
                    {formatModText(mod)}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Explicit Mods */}
          {((item.prefix_mods && item.prefix_mods.length > 0) || (item.suffix_mods && item.suffix_mods.length > 0)) && (
            <div className="item-stats-section">
              <div className="stats-separator"></div>
              <div className="item-stats explicit-mods">
                {/* Prefix Mods */}
                {item.prefix_mods?.map((mod, index) => (
                  <div key={`prefix-${index}`} className={`mod-line explicit prefix ${mod.is_fractured ? 'fractured' : ''}`}>
                    {formatModText(mod)}
                  </div>
                ))}

                {/* Suffix Mods */}
                {item.suffix_mods?.map((mod, index) => (
                  <div key={`suffix-${index}`} className={`mod-line explicit suffix ${mod.is_fractured ? 'fractured' : ''}`}>
                    {formatModText(mod)}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Item Category */}
          <div className="item-stats-section">
            <div className="stats-separator"></div>
            <div className="item-category">
              {item.base_category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </div>
          </div>

          {/* Corruption Status */}
          {item.corrupted && (
            <div className="item-stats-section">
              <div className="corrupted-text">Corrupted</div>
            </div>
          )}
        </div>
      </div>

      {/* Item Info */}
      <div className="item-info">
        <div className="mod-counts">
          <div className="mod-count-item">
            <span className="mod-count-label">Prefixes:</span>
            <span className="mod-count-value">
              {item.prefix_mods?.length || 0}/3
            </span>
          </div>
          <div className="mod-count-item">
            <span className="mod-count-label">Suffixes:</span>
            <span className="mod-count-value">
              {item.suffix_mods?.length || 0}/3
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}