import React from 'react'
import type { ItemModifier } from '@/types/crafting'
import './PoE2ModLine.css'

interface PoE2ModLineProps {
  mod: ItemModifier
  showTier?: boolean
  showName?: boolean
  onClick?: () => void
  onRemove?: () => void
  children?: React.ReactNode
}

export function PoE2ModLine({
  mod,
  showTier = true,
  showName = true,
  onClick,
  onRemove,
  children,
}: PoE2ModLineProps) {
  const modClasses = [
    'poe2-mod-line',
    mod.mod_type === 'prefix' ? 'prefix' : '',
    mod.mod_type === 'suffix' ? 'suffix' : '',
    mod.mod_type === 'implicit' ? 'implicit' : '',
    mod.is_fractured ? 'fractured' : '',
    mod.is_desecrated ? 'desecrated' : '',
    mod.is_unrevealed ? 'unrevealed' : '',
    onClick ? 'clickable' : '',
  ].filter(Boolean).join(' ')

  // Format mod text with values
  const formatModText = (): string => {
    let text = mod.stat_text

    if (mod.current_values && mod.current_values.length > 0) {
      let valueIndex = 0
      text = text.replace(/#/g, () => {
        const value = mod.current_values?.[valueIndex] ?? mod.current_value ?? '#'
        valueIndex++
        return String(value)
      })
    } else if (mod.current_value !== undefined && mod.current_value !== null && text.includes('#')) {
      text = text.replace('#', String(mod.current_value))
    }

    return text
  }

  return (
    <div
      className={modClasses}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <div className="poe2-mod-content">
        <span className="poe2-mod-text">{formatModText()}</span>
        {showTier && mod.tier && !mod.is_unrevealed && (
          <span className="poe2-mod-tier">T{mod.tier}</span>
        )}
        {showName && mod.name && !mod.is_unrevealed && (
          <span className="poe2-mod-name">{mod.name}</span>
        )}
        {children}
      </div>
      {onRemove && (
        <button
          className="poe2-mod-remove"
          onClick={(e) => {
            e.stopPropagation()
            onRemove()
          }}
          title="Remove modifier"
        >
          ✕
        </button>
      )}
    </div>
  )
}

// Simple section separator
export function PoE2Separator() {
  return <div className="poe2-separator" />
}

// Section with title
interface PoE2SectionProps {
  title?: string
  children: React.ReactNode
}

export function PoE2Section({ title, children }: PoE2SectionProps) {
  return (
    <div className="poe2-section">
      {title && <div className="poe2-section-title">{title}</div>}
      {children}
    </div>
  )
}

// Property line (for stats like Armour, Evasion, etc.)
interface PoE2PropertyProps {
  label: string
  value: string | number
  augmented?: boolean
  highlight?: boolean  // For DPS stats - golden color
}

export function PoE2Property({ label, value, augmented = false, highlight = false }: PoE2PropertyProps) {
  const valueClass = highlight ? 'highlight' : augmented ? 'augmented' : ''
  return (
    <div className="poe2-property">
      <span className="poe2-property-label">{label}:</span>
      <span className={`poe2-property-value ${valueClass}`}>{value}</span>
    </div>
  )
}

// Two-column layout (for weapon stats, etc.)
interface PoE2TwoColumnProps {
  children: React.ReactNode
  gap?: 'small' | 'medium' | 'large'
}

export function PoE2TwoColumn({ children, gap = 'medium' }: PoE2TwoColumnProps) {
  return (
    <div className={`poe2-two-column poe2-two-column-gap-${gap}`}>
      {children}
    </div>
  )
}

// Column wrapper for PoE2TwoColumn
interface PoE2ColumnProps {
  children: React.ReactNode
  align?: 'left' | 'right'
}

export function PoE2Column({ children, align = 'left' }: PoE2ColumnProps) {
  return (
    <div className={`poe2-column poe2-column-${align}`}>
      {children}
    </div>
  )
}
