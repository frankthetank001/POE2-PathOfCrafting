import { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
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

    // If tooltip hasn't rendered yet (zero dimensions), schedule another update
    if (tooltipRect.height === 0 || tooltipRect.width === 0) {
      requestAnimationFrame(updatePosition)
      return
    }

    let top = 0
    let left = 0

    // Calculate available space in each direction
    const spaceAbove = triggerRect.top
    const spaceBelow = viewportHeight - triggerRect.bottom
    const spaceLeft = triggerRect.left
    const spaceRight = viewportWidth - triggerRect.right

    // Calculate position based on preferred position and available space
    switch (position) {
      case 'top':
        // Default to top, flip to bottom if not enough space
        if (spaceAbove >= tooltipRect.height + 8 || spaceAbove > spaceBelow) {
          top = triggerRect.top - tooltipRect.height - 8
        } else {
          top = triggerRect.bottom + 8
        }
        left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2
        break

      case 'bottom':
        // Default to bottom, flip to top if not enough space
        if (spaceBelow >= tooltipRect.height + 8 || spaceBelow > spaceAbove) {
          top = triggerRect.bottom + 8
        } else {
          top = triggerRect.top - tooltipRect.height - 8
        }
        left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2
        break

      case 'left':
        top = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2
        if (spaceLeft >= tooltipRect.width + 8 || spaceLeft > spaceRight) {
          left = triggerRect.left - tooltipRect.width - 8
        } else {
          left = triggerRect.right + 8
        }
        break

      case 'right':
        top = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2
        if (spaceRight >= tooltipRect.width + 8 || spaceRight > spaceLeft) {
          left = triggerRect.right + 8
        } else {
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
  }, [isVisible, content])

  // Watch for tooltip size changes (e.g., when async content loads)
  useEffect(() => {
    if (!isVisible || !tooltipRef.current) return

    const resizeObserver = new ResizeObserver(() => {
      updatePosition()
    })

    resizeObserver.observe(tooltipRef.current)
    return () => resizeObserver.disconnect()
  }, [isVisible])

  useEffect(() => {
    const handleResize = () => {
      if (isVisible) {
        updatePosition()
      }
    }

    window.addEventListener('resize', handleResize)
    window.addEventListener('scroll', handleResize, true) // Capture scroll events
    return () => {
      window.removeEventListener('resize', handleResize)
      window.removeEventListener('scroll', handleResize, true)
    }
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

      {isVisible && createPortal(
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
        </div>,
        document.body
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