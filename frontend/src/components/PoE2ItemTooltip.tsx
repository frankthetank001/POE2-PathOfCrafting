import React from 'react'
import type { CraftableItem, ItemModifier } from '@/types/crafting'
import './PoE2ItemTooltip.css'

interface PoE2ItemTooltipProps {
  item: CraftableItem
  showTiers?: boolean
  compact?: boolean
}

export function PoE2ItemTooltip({ item, showTiers = false, compact = false }: PoE2ItemTooltipProps) {
  const rarityClass = `rarity-${item.rarity.toLowerCase()}`

  const formatModText = (mod: ItemModifier): React.ReactNode => {
    let text = mod.stat_text

    // Replace {} placeholders with current values
    if (mod.current_values && mod.current_values.length > 0) {
      let valueIndex = 0
      text = text.replace(/\{\}/g, () => {
        const value = mod.current_values?.[valueIndex] ?? mod.current_value ?? '#'
        valueIndex++
        return `<span class="poe2-mod-value">${value}</span>`
      })
    } else if (mod.current_value !== undefined && text.includes('{}')) {
      text = text.replace('{}', `<span class="poe2-mod-value">${mod.current_value}</span>`)
    }

    return (
      <span dangerouslySetInnerHTML={{ __html: text }} />
    )
  }

  const getModClass = (mod: ItemModifier): string => {
    const classes = ['poe2-mod-line']

    if (mod.mod_type === 'implicit') {
      classes.push('implicit')
    } else {
      classes.push('explicit')
    }

    if (mod.is_fractured) {
      classes.push('fractured')
    }

    if (mod.is_desecrated || mod.is_unrevealed) {
      classes.push('desecrated')
    }

    return classes.join(' ')
  }

  const formatStatName = (stat: string): string => {
    const statNames: Record<string, string> = {
      'armour': 'Armour',
      'evasion': 'Evasion Rating',
      'energy_shield': 'Energy Shield',
      'block': 'Block',
      'ward': 'Ward',
    }
    return statNames[stat] || stat.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  const defenseStats = ['armour', 'evasion', 'energy_shield', 'ward', 'block']
  const hasDefenseStats = Object.keys(item.calculated_stats || {}).some(stat => defenseStats.includes(stat))

  const allExplicitMods = [
    ...(item.prefix_mods || []),
    ...(item.suffix_mods || [])
  ]

  return (
    <div className={`poe2-item-tooltip ${compact ? 'compact' : ''}`}>
      {/* Header */}
      <div className={`poe2-item-header ${rarityClass}`}>
        <h3 className={`poe2-item-name ${rarityClass}`}>
          {item.rarity === 'Rare' ? item.base_name : item.base_name}
        </h3>
        {item.rarity === 'Rare' && (
          <div className="poe2-item-base">
            {item.base_category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </div>
        )}
      </div>

      {/* Defense Stats */}
      {hasDefenseStats && (
        <>
          <div className="poe2-separator-simple" />
          <div className="poe2-item-properties">
            {Object.entries(item.calculated_stats || {})
              .filter(([stat]) => defenseStats.includes(stat))
              .map(([stat, value]) => (
                <div key={stat} className="poe2-property-line">
                  <span className="poe2-property-name">{formatStatName(stat)}:</span>
                  <span className="poe2-property-value">{value}</span>
                </div>
              ))}
          </div>
        </>
      )}

      {/* Quality & Item Level */}
      <div className="poe2-separator-simple" />
      <div className="poe2-item-properties">
        {item.quality > 0 && (
          <div className="poe2-property-line">
            <span className="poe2-property-name">Quality:</span>
            <span className="poe2-property-value augmented">+{item.quality}%</span>
          </div>
        )}
      </div>

      {/* Item Level */}
      <div className="poe2-item-level">
        Item Level: <span>{item.item_level}</span>
      </div>

      {/* Implicit Mods */}
      {item.implicit_mods && item.implicit_mods.length > 0 && (
        <>
          <div className="poe2-separator-simple" />
          <div className="poe2-mods-section">
            {item.implicit_mods.map((mod, index) => (
              <div key={`implicit-${index}`} className={getModClass(mod)}>
                {formatModText(mod)}
                {showTiers && mod.tier && (
                  <span className="poe2-mod-tier">T{mod.tier}</span>
                )}
              </div>
            ))}
          </div>
        </>
      )}

      {/* Explicit Mods */}
      {allExplicitMods.length > 0 && (
        <>
          <div className="poe2-separator-simple" />
          <div className="poe2-mods-section">
            {allExplicitMods.map((mod, index) => (
              <div key={`explicit-${index}`} className={getModClass(mod)}>
                {formatModText(mod)}
                {showTiers && mod.tier && (
                  <span className="poe2-mod-tier">T{mod.tier}</span>
                )}
              </div>
            ))}
          </div>
        </>
      )}

      {/* Corrupted Status */}
      {item.corrupted && (
        <>
          <div className="poe2-separator-simple" />
          <div className="poe2-corrupted-text">Corrupted</div>
        </>
      )}
    </div>
  )
}
