import React from 'react'
import './PoE2Button.css'

interface PoE2ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon?: React.ReactNode
  active?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export function PoE2Button({
  children,
  icon,
  active,
  size = 'md',
  className = '',
  ...props
}: PoE2ButtonProps) {
  const sizeClass = size !== 'md' ? `poe2-button-${size}` : ''
  const activeClass = active ? 'active' : ''

  return (
    <button
      className={`poe2-button ${sizeClass} ${activeClass} ${className}`.trim()}
      {...props}
    >
      {icon && <span className="poe2-button-icon">{icon}</span>}
      {children}
    </button>
  )
}

interface PoE2ButtonGroupProps {
  children: React.ReactNode
  columns?: 2 | 3 | 4 | 5 | 6
  noBackground?: boolean
  className?: string
}

export function PoE2ButtonGroup({
  children,
  columns = 4,
  noBackground = false,
  className = ''
}: PoE2ButtonGroupProps) {
  return (
    <div
      className={`poe2-button-group ${noBackground ? 'no-background' : ''} ${className}`.trim()}
      data-columns={columns}
    >
      {children}
    </div>
  )
}
