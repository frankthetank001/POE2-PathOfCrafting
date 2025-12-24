import type { CraftableItem } from '@/types/crafting'
import { PoE2ItemTooltip } from '@/components/PoE2ItemTooltip'

interface ItemDisplayPanelProps {
  item: CraftableItem
  showTiers?: boolean
}

export function ItemDisplayPanel({ item, showTiers = false }: ItemDisplayPanelProps) {
  return (
    <div className="item-display-panel">
      <div className="item-preview">
        <PoE2ItemTooltip item={item} showTiers={showTiers} />
      </div>

      {/* Item Info - Mod Counts */}
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