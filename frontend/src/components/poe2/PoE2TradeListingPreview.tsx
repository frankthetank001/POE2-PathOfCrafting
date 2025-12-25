import { PoE2ItemFrame } from './PoE2ItemFrame'
import { PoE2Separator, PoE2Section, PoE2Property } from './PoE2ModLine'
import type { PriceListing } from '@/services/market-api'
import './PoE2ModLine.css'

/**
 * Clean up mod text by extracting the second value from [A|B] patterns.
 * Example: "+34% to [Resistances|Lightning Resistance]" → "+34% to Lightning Resistance"
 */
function cleanModText(text: string): string {
  return text.replace(/\[([^\]|]+)\|([^\]]+)\]/g, '$2')
}

/** Render a comparison badge inline */
function ComparisonBadge({ diffPct }: { diffPct: number }) {
  const diffClass = diffPct > 5 ? 'better' : diffPct < -5 ? 'worse' : 'similar'
  const sign = diffPct > 0 ? '+' : ''
  return (
    <span className={`mod-comparison-badge ${diffClass}`}>
      {sign}{Math.round(diffPct)}%
    </span>
  )
}

interface PoE2TradeListingPreviewProps {
  listing: PriceListing
  className?: string
}

export function PoE2TradeListingPreview({ listing, className = '' }: PoE2TradeListingPreviewProps) {
  const hasPrefixSuffixSplit = (listing.prefix_mods && listing.prefix_mods.length > 0) ||
                               (listing.suffix_mods && listing.suffix_mods.length > 0)

  // Helper to get comparison for a stat_id
  const getComparison = (statId: string) => {
    if (!listing.stat_comparisons) return null
    return listing.stat_comparisons[statId] || null
  }

  // Get equipment stat comparison
  const getEquipComparison = (field: string) => {
    if (!listing.stat_comparisons) return null
    return listing.stat_comparisons[`equip.${field}`] || null
  }

  return (
    <PoE2ItemFrame
      rarity="rare"
      itemName={listing.item_name || 'Rare Item'}
      itemBase={listing.item_base}
      className={className}
    >
      {/* Properties section with comparison badges */}
      <PoE2Section>
        {listing.quality != null && listing.quality > 0 && (
          <PoE2Property label="Quality" value={`+${listing.quality}%`} augmented />
        )}
        {listing.armour != null && listing.armour > 0 && (
          <div className="poe2-property-with-comparison">
            <PoE2Property label="Armour" value={listing.armour} />
            {getEquipComparison('armour') && <ComparisonBadge diffPct={getEquipComparison('armour')!.diff_pct} />}
          </div>
        )}
        {listing.evasion != null && listing.evasion > 0 && (
          <div className="poe2-property-with-comparison">
            <PoE2Property label="Evasion Rating" value={listing.evasion} />
            {getEquipComparison('evasion') && <ComparisonBadge diffPct={getEquipComparison('evasion')!.diff_pct} />}
          </div>
        )}
        {listing.energy_shield != null && listing.energy_shield > 0 && (
          <div className="poe2-property-with-comparison">
            <PoE2Property label="Energy Shield" value={listing.energy_shield} />
            {getEquipComparison('energy_shield') && <ComparisonBadge diffPct={getEquipComparison('energy_shield')!.diff_pct} />}
          </div>
        )}
        <PoE2Property label="Item Level" value={listing.item_level} />
      </PoE2Section>

      {/* Weapon stats section */}
      {(listing.physical_dps || listing.total_dps || listing.attacks_per_second) && (
        <>
          <PoE2Separator />
          <PoE2Section>
            {listing.physical_damage && (
              <PoE2Property label="Physical Damage" value={listing.physical_damage} augmented />
            )}
            {listing.attacks_per_second != null && (
              <PoE2Property label="Attacks per Second" value={listing.attacks_per_second.toFixed(2)} augmented />
            )}
            {listing.crit_chance != null && (
              <PoE2Property label="Critical Hit Chance" value={`${listing.crit_chance.toFixed(2)}%`} />
            )}
            {listing.physical_dps != null && listing.physical_dps > 0 && (
              <PoE2Property label="Physical DPS" value={Math.round(listing.physical_dps)} highlight />
            )}
            {listing.elemental_dps != null && listing.elemental_dps > 0 && (
              <PoE2Property label="Elemental DPS" value={Math.round(listing.elemental_dps)} highlight />
            )}
            {listing.total_dps != null && listing.total_dps > 0 && listing.total_dps !== listing.physical_dps && (
              <PoE2Property label="Total DPS" value={Math.round(listing.total_dps)} highlight />
            )}
          </PoE2Section>
        </>
      )}

      {/* Implicit mods */}
      {listing.implicit_mods && listing.implicit_mods.length > 0 && (
        <>
          <PoE2Separator />
          <PoE2Section>
            {listing.implicit_mods.map((mod, i) => (
              <div key={i} className="poe2-mod-line implicit">
                <div className="poe2-mod-content">
                  <span className="poe2-mod-text">{cleanModText(mod)}</span>
                </div>
              </div>
            ))}
          </PoE2Section>
        </>
      )}

      {/* Rune mods */}
      {listing.rune_mods && listing.rune_mods.length > 0 && (
        <>
          <PoE2Separator />
          <PoE2Section title={listing.socketed_rune_name || 'Rune'}>
            {listing.rune_mods.map((mod, i) => (
              <div key={i} className="poe2-mod-line rune">
                <div className="poe2-mod-content">
                  <span className="poe2-mod-text">{cleanModText(mod)}</span>
                  <span className="poe2-mod-tier">rune</span>
                </div>
              </div>
            ))}
          </PoE2Section>
        </>
      )}

      {/* Prefix/suffix split if available */}
      {hasPrefixSuffixSplit ? (
        <>
          {listing.prefix_mods && listing.prefix_mods.length > 0 && (
            <>
              <PoE2Separator />
              <PoE2Section title="Prefixes">
                {listing.prefix_mods.map((mod, i) => {
                  const comparison = mod.stat_id ? getComparison(mod.stat_id) : null
                  return (
                    <div
                      key={i}
                      className={`poe2-mod-line prefix ${mod.is_desecrated ? 'desecrated' : ''}`}
                      title={`${mod.name} (${mod.tier})`}
                    >
                      <div className="poe2-mod-content">
                        <span className="poe2-mod-text">{cleanModText(mod.text)}</span>
                        <span className="poe2-mod-tier">{mod.tier}</span>
                        {comparison && <ComparisonBadge diffPct={comparison.diff_pct} />}
                      </div>
                    </div>
                  )
                })}
              </PoE2Section>
            </>
          )}
          {listing.suffix_mods && listing.suffix_mods.length > 0 && (
            <>
              {!listing.prefix_mods?.length && <PoE2Separator />}
              <PoE2Section title="Suffixes">
                {listing.suffix_mods.map((mod, i) => {
                  const comparison = mod.stat_id ? getComparison(mod.stat_id) : null
                  return (
                    <div
                      key={i}
                      className={`poe2-mod-line suffix ${mod.is_desecrated ? 'desecrated' : ''}`}
                      title={`${mod.name} (${mod.tier})`}
                    >
                      <div className="poe2-mod-content">
                        <span className="poe2-mod-text">{cleanModText(mod.text)}</span>
                        <span className="poe2-mod-tier">{mod.tier}</span>
                        {comparison && <ComparisonBadge diffPct={comparison.diff_pct} />}
                      </div>
                    </div>
                  )
                })}
              </PoE2Section>
            </>
          )}
        </>
      ) : (
        /* Fallback to explicit_mods list */
        listing.explicit_mods.length > 0 && (
          <>
            <PoE2Separator />
            <PoE2Section>
              {listing.explicit_mods.map((mod, i) => (
                <div key={i} className="poe2-mod-line prefix">
                  <div className="poe2-mod-content">
                    <span className="poe2-mod-text">{cleanModText(mod)}</span>
                  </div>
                </div>
              ))}
            </PoE2Section>
          </>
        )
      )}

      {/* Pseudo stat comparisons (resistances, life totals, etc.) */}
      {listing.stat_comparisons && (() => {
        const pseudoComparisons = Object.entries(listing.stat_comparisons)
          .filter(([key]) => key.startsWith('pseudo.'))
        if (pseudoComparisons.length === 0) return null
        return (
          <>
            <PoE2Separator />
            <PoE2Section title="Totals">
              {pseudoComparisons.map(([key, data]) => (
                <div key={key} className="poe2-pseudo-stat-row">
                  <span className="poe2-pseudo-stat-name">{data.name || key}</span>
                  <span className="poe2-pseudo-stat-value">{data.listing}</span>
                  <ComparisonBadge diffPct={data.diff_pct} />
                </div>
              ))}
            </PoE2Section>
          </>
        )
      })()}

      {/* Corrupted/Desecrated status */}
      {listing.is_corrupted && (
        <div className="poe2-status-text corrupted">Corrupted</div>
      )}
      {listing.is_desecrated && (
        <div className="poe2-status-text desecrated">Desecrated</div>
      )}
    </PoE2ItemFrame>
  )
}
