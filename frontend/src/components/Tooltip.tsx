import { useState, useRef, useEffect } from 'react'
import './Tooltip.css'

interface TooltipProps {
  children: React.ReactNode
  content: React.ReactNode
  delay?: number
  position?: 'top' | 'bottom' | 'left' | 'right'
  maxWidth?: number
}

export function Tooltip({
  children,
  content,
  delay = 0,
  position = 'top',
  maxWidth = 300
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 })
  const triggerRef = useRef<HTMLDivElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)
  const timeoutRef = useRef<number>()

  const showTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    timeoutRef.current = setTimeout(() => {
      setIsVisible(true)
      updatePosition()
    }, delay)
  }

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setIsVisible(false)
  }

  const updatePosition = () => {
    if (!triggerRef.current || !tooltipRef.current) return

    const triggerRect = triggerRef.current.getBoundingClientRect()
    const tooltipRect = tooltipRef.current.getBoundingClientRect()
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight

    let top = 0
    let left = 0

    // Calculate position based on preferred position and available space
    switch (position) {
      case 'top':
        top = triggerRect.top - tooltipRect.height - 8
        left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2

        // Flip to bottom if not enough space above
        if (top < 0) {
          top = triggerRect.bottom + 8
        }
        break

      case 'bottom':
        top = triggerRect.bottom + 8
        left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2

        // Flip to top if not enough space below
        if (top + tooltipRect.height > viewportHeight) {
          top = triggerRect.top - tooltipRect.height - 8
        }
        break

      case 'left':
        top = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2
        left = triggerRect.left - tooltipRect.width - 8

        // Flip to right if not enough space to the left
        if (left < 0) {
          left = triggerRect.right + 8
        }
        break

      case 'right':
        top = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2
        left = triggerRect.right + 8

        // Flip to left if not enough space to the right
        if (left + tooltipRect.width > viewportWidth) {
          left = triggerRect.left - tooltipRect.width - 8
        }
        break
    }

    // Ensure tooltip stays within viewport horizontally
    if (left < 8) {
      left = 8
    } else if (left + tooltipRect.width > viewportWidth - 8) {
      left = viewportWidth - tooltipRect.width - 8
    }

    // Ensure tooltip stays within viewport vertically
    if (top < 8) {
      top = 8
    } else if (top + tooltipRect.height > viewportHeight - 8) {
      top = viewportHeight - tooltipRect.height - 8
    }

    setTooltipPosition({ top, left })
  }

  useEffect(() => {
    if (isVisible) {
      updatePosition()
    }
  }, [isVisible])

  useEffect(() => {
    const handleResize = () => {
      if (isVisible) {
        updatePosition()
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [isVisible])

  return (
    <div className="tooltip-wrapper">
      <div
        ref={triggerRef}
        className="tooltip-trigger"
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
        onFocus={showTooltip}
        onBlur={hideTooltip}
      >
        {children}
      </div>

      {isVisible && (
        <div
          ref={tooltipRef}
          className="tooltip-content"
          style={{
            position: 'fixed',
            top: tooltipPosition.top,
            left: tooltipPosition.left,
            maxWidth: `${maxWidth}px`,
            zIndex: 10000
          }}
        >
          {content}
        </div>
      )}
    </div>
  )
}

interface CurrencyTooltipProps {
  name: string
  description: string
  mechanics?: string
  statRanges?: string
}

export function CurrencyTooltip({ name, description, mechanics, statRanges }: CurrencyTooltipProps) {
  return (
    <div className="currency-tooltip">
      <div className="tooltip-header">
        <h4 className="tooltip-title">{name}</h4>
      </div>

      <div className="tooltip-body">
        <p className="tooltip-description">{description}</p>

        {statRanges && (
          <div className="tooltip-stat-ranges">
            <h5>Modifier Added:</h5>
            <div className="stat-ranges-content">
              {statRanges.split('\n').map((line, i) => (
                <div key={i} className="stat-range-line">
                  {line.startsWith('•') ? (
                    <span className="stat-range-item">{line}</span>
                  ) : (
                    <span className="stat-range-value">{line}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {mechanics && (
          <div className="tooltip-mechanics">
            <h5>Mechanics:</h5>
            <div className="mechanics-content">
              {mechanics.split('\n').map((line, i) => (
                <div key={i} className="mechanics-line">
                  {line.startsWith('•') ? (
                    <span className="mechanics-item">{line}</span>
                  ) : (
                    <span className="mechanics-text">{line}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}