import React from 'react'
import { PoE2ItemFrame } from './PoE2ItemFrame'
import { PoE2Separator, PoE2Section, PoE2Property } from './PoE2ModLine'
import type { PriceListing } from '@/services/market-api'
import './PoE2ModLine.css'

interface PoE2TradeListingPreviewProps {
  listing: PriceListing
  className?: string
}

export function PoE2TradeListingPreview({ listing, className = '' }: PoE2TradeListingPreviewProps) {
  const hasPrefixSuffixSplit = (listing.prefix_mods && listing.prefix_mods.length > 0) ||
                               (listing.suffix_mods && listing.suffix_mods.length > 0)

  return (
    <PoE2ItemFrame
      rarity="rare"
      itemName={listing.item_name || 'Rare Item'}
      itemBase={listing.item_base}
      className={className}
    >
      {/* Properties section */}
      <PoE2Section>
        {listing.quality != null && listing.quality > 0 && (
          <PoE2Property label="Quality" value={`+${listing.quality}%`} augmented />
        )}
        {listing.armour != null && listing.armour > 0 && (
          <PoE2Property label="Armour" value={listing.armour} />
        )}
        {listing.evasion != null && listing.evasion > 0 && (
          <PoE2Property label="Evasion Rating" value={listing.evasion} />
        )}
        {listing.energy_shield != null && listing.energy_shield > 0 && (
          <PoE2Property label="Energy Shield" value={listing.energy_shield} />
        )}
        <PoE2Property label="Item Level" value={listing.item_level} />
      </PoE2Section>

      {/* Implicit mods */}
      {listing.implicit_mods && listing.implicit_mods.length > 0 && (
        <>
          <PoE2Separator />
          <PoE2Section>
            {listing.implicit_mods.map((mod, i) => (
              <div key={i} className="poe2-mod-line implicit">
                <div className="poe2-mod-content">
                  <span className="poe2-mod-text">{mod}</span>
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
                  <span className="poe2-mod-text">{mod}</span>
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
                {listing.prefix_mods.map((mod, i) => (
                  <div
                    key={i}
                    className={`poe2-mod-line prefix ${mod.is_desecrated ? 'desecrated' : ''}`}
                    title={`${mod.name} (${mod.tier})`}
                  >
                    <div className="poe2-mod-content">
                      <span className="poe2-mod-text">{mod.text}</span>
                      <span className="poe2-mod-tier">{mod.tier}</span>
                    </div>
                  </div>
                ))}
              </PoE2Section>
            </>
          )}
          {listing.suffix_mods && listing.suffix_mods.length > 0 && (
            <>
              {!listing.prefix_mods?.length && <PoE2Separator />}
              <PoE2Section title="Suffixes">
                {listing.suffix_mods.map((mod, i) => (
                  <div
                    key={i}
                    className={`poe2-mod-line suffix ${mod.is_desecrated ? 'desecrated' : ''}`}
                    title={`${mod.name} (${mod.tier})`}
                  >
                    <div className="poe2-mod-content">
                      <span className="poe2-mod-text">{mod.text}</span>
                      <span className="poe2-mod-tier">{mod.tier}</span>
                    </div>
                  </div>
                ))}
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
                    <span className="poe2-mod-text">{mod}</span>
                  </div>
                </div>
              ))}
            </PoE2Section>
          </>
        )
      )}

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
