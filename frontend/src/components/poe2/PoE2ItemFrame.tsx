import React from 'react'
import type { ItemRarity } from '@/types/crafting'
import './PoE2ItemFrame.css'

interface PoE2ItemFrameProps {
  rarity: ItemRarity | string
  itemName: string
  itemBase?: string
  children: React.ReactNode
  className?: string
  headerActions?: React.ReactNode
  onDrop?: (e: React.DragEvent) => void
  onDragOver?: (e: React.DragEvent) => void
}

export function PoE2ItemFrame({
  rarity,
  itemName,
  itemBase,
  children,
  className = '',
  headerActions,
  onDrop,
  onDragOver,
}: PoE2ItemFrameProps) {
  const rarityLower = typeof rarity === 'string' ? rarity.toLowerCase() : rarity.toLowerCase()

  return (
    <div
      className={`poe2-frame rarity-${rarityLower} ${className}`}
      onDrop={onDrop}
      onDragOver={onDragOver}
    >
      {/* Header */}
      <div className="poe2-frame-header">
        <div className="poe2-frame-header-content">
          <h2 className={`poe2-frame-name rarity-${rarityLower}`}>{itemName}</h2>
          {itemBase && <div className="poe2-frame-base">{itemBase}</div>}
        </div>
        {headerActions && (
          <div className="poe2-frame-actions">{headerActions}</div>
        )}
      </div>

      {/* Content */}
      <div className="poe2-frame-content">
        {children}
      </div>
    </div>
  )
}
