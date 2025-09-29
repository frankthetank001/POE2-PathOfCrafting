import { useState, useRef, useEffect } from 'react'
import { ItemDisplayPanel } from '@/components/panels/ItemDisplayPanel'
import { CraftingControlsPanel } from '@/components/panels/CraftingControlsPanel'
import { AvailableModsPanel } from '@/components/panels/AvailableModsPanel'
import { craftingApi } from '@/services/crafting-api'
import type { CraftableItem, ItemRarity } from '@/types/crafting'
import './ResizableCraftingSimulator.css'

function ResizableCraftingSimulator() {
  const [item, setItem] = useState<CraftableItem>({
    base_name: "Int Armour Body Armour",
    base_category: 'int_armour',
    rarity: 'Normal' as ItemRarity,
    item_level: 65,
    quality: 20,
    implicit_mods: [],
    prefix_mods: [],
    suffix_mods: [],
    corrupted: false,
    base_stats: {},
    calculated_stats: {},
  })

  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [history, setHistory] = useState<string[]>([])
  const [itemHistory, setItemHistory] = useState<CraftableItem[]>([])
  const [currencySpent, setCurrencySpent] = useState<Record<string, number>>({})

  // Panel widths
  const [leftPanelWidth, setLeftPanelWidth] = useState(50) // percentage
  const [rightPanelWidth, setRightPanelWidth] = useState(25) // percentage of remaining space

  // Resize refs
  const containerRef = useRef<HTMLDivElement>(null)
  const isDraggingLeft = useRef(false)
  const isDraggingRight = useRef(false)

  const handleHistoryAdd = (item: CraftableItem) => {
    setItemHistory([...itemHistory, item])
  }

  const handleHistoryReset = () => {
    setHistory([])
    setItemHistory([])
    setCurrencySpent({})
  }

  const handleRevertToStep = (stepIndex: number) => {
    if (stepIndex < itemHistory.length) {
      setItem(itemHistory[stepIndex])
      setItemHistory(itemHistory.slice(0, stepIndex + 1))
      setHistory(history.slice(0, stepIndex + 1))
    }
  }

  const handleClearHistory = () => {
    setHistory([])
    setItemHistory([])
    setCurrencySpent({})
    setMessage('History cleared')
  }

  // Handle keyboard shortcut for paste
  useEffect(() => {
    const handleKeyDown = async (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'v') {
        e.preventDefault()
        try {
          const text = await navigator.clipboard.readText()
          if (text && text.includes('--------')) {
            // Parse the item using the API
            const result = await craftingApi.parseItem(text)
            if (result.item) {
              setItem(result.item)
              handleHistoryReset()
              setMessage('Item loaded from clipboard!')
              setTimeout(() => setMessage(''), 3000)
            }
          }
        } catch (err) {
          console.error('Failed to parse item from clipboard:', err)
          setMessage('Failed to parse item from clipboard')
          setTimeout(() => setMessage(''), 3000)
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  // Mouse move handler for resizing
  const handleMouseMove = (e: MouseEvent) => {
    if (!containerRef.current) return

    const containerRect = containerRef.current.getBoundingClientRect()
    const containerWidth = containerRect.width

    if (isDraggingLeft.current) {
      const newWidth = ((e.clientX - containerRect.left) / containerWidth) * 100
      setLeftPanelWidth(Math.min(Math.max(newWidth, 20), 70)) // Min 20%, Max 70%
    }

    if (isDraggingRight.current) {
      const remainingWidth = containerWidth - (containerWidth * leftPanelWidth / 100)
      const rightOffset = e.clientX - containerRect.left - (containerWidth * leftPanelWidth / 100)
      const newRightWidth = (rightOffset / remainingWidth) * 100
      setRightPanelWidth(Math.min(Math.max(newRightWidth, 15), 60)) // Min 15%, Max 60%
    }
  }

  const handleMouseUp = () => {
    isDraggingLeft.current = false
    isDraggingRight.current = false
    document.body.style.cursor = 'default'
    document.body.style.userSelect = 'auto'
  }

  useEffect(() => {
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [leftPanelWidth])

  const startLeftResize = () => {
    isDraggingLeft.current = true
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }

  const startRightResize = () => {
    isDraggingRight.current = true
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }

  return (
    <div className="resizable-crafting-simulator" ref={containerRef}>
      {/* Left Panel - Item Display */}
      <div
        className="panel left-panel"
        style={{ width: `${leftPanelWidth}%` }}
      >
        <div className="panel-content">
          <ItemDisplayPanel
            item={item}
            onItemChange={setItem}
            onHistoryReset={handleHistoryReset}
            itemHistory={itemHistory}
            history={history}
            currencySpent={currencySpent}
            onRevertToStep={handleRevertToStep}
            onClearHistory={handleClearHistory}
          />
        </div>

        {/* Left Resize Handle */}
        <div
          className="resize-handle resize-handle-vertical"
          onMouseDown={startLeftResize}
        >
          <div className="resize-grip"></div>
        </div>
      </div>

      {/* Middle Section */}
      <div className="middle-section" style={{ flex: 1 }}>
        {/* Crafting Controls Panel */}
        <div
          className="panel middle-panel"
          style={{ width: `${rightPanelWidth}%` }}
        >
          <div className="panel-header">
            <h3>Crafting Orbs</h3>
          </div>
          <div className="panel-content">
            <CraftingControlsPanel
              item={item}
              onItemChange={setItem}
              message={message}
              onMessage={setMessage}
              loading={loading}
              onLoadingChange={setLoading}
              currencySpent={currencySpent}
              onCurrencySpentChange={setCurrencySpent}
              onHistoryAdd={handleHistoryAdd}
            />
          </div>

          {/* Right Resize Handle */}
          <div
            className="resize-handle resize-handle-vertical"
            onMouseDown={startRightResize}
          >
            <div className="resize-grip"></div>
          </div>
        </div>

        {/* Available Mods Panel */}
        <div className="panel right-panel" style={{ flex: 1 }}>
          <div className="panel-header">
            <h3>Available Mods</h3>
          </div>
          <div className="panel-content">
            <AvailableModsPanel item={item} />
          </div>
        </div>
      </div>
    </div>
  )
}

export default ResizableCraftingSimulator