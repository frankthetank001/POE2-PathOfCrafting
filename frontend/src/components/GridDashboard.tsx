import { useState, useEffect, ReactNode } from 'react'
import GridLayout, { Layout, WidthProvider } from 'react-grid-layout'
import 'react-grid-layout/css/styles.css'
import './GridDashboard.css'

const ResponsiveGridLayout = WidthProvider(GridLayout)

export interface GridPanel {
  id: string
  title: string
  content: ReactNode
  defaultLayout: {
    x: number
    y: number
    w: number
    h: number
    minW?: number
    minH?: number
    maxW?: number
    maxH?: number
  }
}

interface GridDashboardProps {
  panels: GridPanel[]
  onLayoutChange?: (layout: Layout[]) => void
  className?: string
}

interface SavedLayout {
  name: string
  layout: Layout[]
  timestamp: number
}

export function GridDashboard({ panels, onLayoutChange, className = '' }: GridDashboardProps) {
  const [layout, setLayout] = useState<Layout[]>([])
  const [savedLayouts, setSavedLayouts] = useState<SavedLayout[]>([])
  const [showLayoutControls, setShowLayoutControls] = useState(false)
  const [newLayoutName, setNewLayoutName] = useState('')

  // Load layout from localStorage on mount
  useEffect(() => {
    if (panels.length === 0) return // Wait for panels to be available

    const savedLayout = localStorage.getItem('grid-dashboard-layout')
    const savedLayoutsList = localStorage.getItem('grid-dashboard-saved-layouts')

    if (savedLayout) {
      try {
        const parsedLayout = JSON.parse(savedLayout)
        // Validate that all panels exist in the saved layout
        const validLayout = parsedLayout.filter((item: Layout) =>
          panels.some(panel => panel.id === item.i)
        )
        if (validLayout.length === panels.length) {
          setLayout(validLayout)
        } else {
          // If saved layout is incomplete or invalid, use default
          setDefaultLayout()
        }
      } catch (e) {
        console.warn('Failed to parse saved layout:', e)
        setDefaultLayout()
      }
    } else {
      setDefaultLayout()
    }

    if (savedLayoutsList) {
      try {
        const parsedLayouts = JSON.parse(savedLayoutsList)
        setSavedLayouts(parsedLayouts)
      } catch (e) {
        console.warn('Failed to parse saved layouts list:', e)
      }
    }
  }, [panels])

  const setDefaultLayout = () => {
    const defaultLayout = panels.map(panel => ({
      i: panel.id,
      x: panel.defaultLayout.x,
      y: panel.defaultLayout.y,
      w: panel.defaultLayout.w,
      h: panel.defaultLayout.h,
      minW: panel.defaultLayout.minW || 2,
      minH: panel.defaultLayout.minH || 2,
      maxW: panel.defaultLayout.maxW,
      maxH: panel.defaultLayout.maxH,
    }))
    setLayout(defaultLayout)
  }

  const handleLayoutChange = (newLayout: Layout[]) => {
    setLayout(newLayout)
    localStorage.setItem('grid-dashboard-layout', JSON.stringify(newLayout))
    onLayoutChange?.(newLayout)
  }

  const saveCurrentLayout = () => {
    if (!newLayoutName.trim()) {
      alert('Please enter a layout name')
      return
    }

    const newSavedLayout: SavedLayout = {
      name: newLayoutName.trim(),
      layout: [...layout],
      timestamp: Date.now()
    }

    const updatedLayouts = [...savedLayouts.filter(l => l.name !== newLayoutName.trim()), newSavedLayout]
    setSavedLayouts(updatedLayouts)
    localStorage.setItem('grid-dashboard-saved-layouts', JSON.stringify(updatedLayouts))
    setNewLayoutName('')
    alert(`Layout "${newLayoutName.trim()}" saved!`)
  }

  const loadLayout = (savedLayout: SavedLayout) => {
    setLayout(savedLayout.layout)
    localStorage.setItem('grid-dashboard-layout', JSON.stringify(savedLayout.layout))
    onLayoutChange?.(savedLayout.layout)
  }

  const deleteLayout = (layoutName: string) => {
    if (confirm(`Delete layout "${layoutName}"?`)) {
      const updatedLayouts = savedLayouts.filter(l => l.name !== layoutName)
      setSavedLayouts(updatedLayouts)
      localStorage.setItem('grid-dashboard-saved-layouts', JSON.stringify(updatedLayouts))
    }
  }

  const resetToDefault = () => {
    if (confirm('Reset to default layout?')) {
      localStorage.removeItem('grid-dashboard-layout')
      setDefaultLayout()
    }
  }

  // Force default layout on first visit (temporary)
  useEffect(() => {
    if (panels.length > 0 && layout.length === 0) {
      console.log('Setting default layout - panels available:', panels.length)
      setDefaultLayout()
    }
  }, [panels, layout.length])

  return (
    <div className={`grid-dashboard ${className}`}>
      {/* Layout Controls */}
      <div className="layout-controls">
        <button
          className="layout-controls-toggle"
          onClick={() => setShowLayoutControls(!showLayoutControls)}
        >
          ⚙️ Layout
        </button>

        {showLayoutControls && (
          <div className="layout-controls-panel">
            <div className="layout-controls-section">
              <h4>Save Current Layout</h4>
              <div className="save-layout-row">
                <input
                  type="text"
                  placeholder="Layout name..."
                  value={newLayoutName}
                  onChange={(e) => setNewLayoutName(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && saveCurrentLayout()}
                />
                <button onClick={saveCurrentLayout}>Save</button>
              </div>
            </div>

            {savedLayouts.length > 0 && (
              <div className="layout-controls-section">
                <h4>Saved Layouts</h4>
                <div className="saved-layouts-list">
                  {savedLayouts.map(savedLayout => (
                    <div key={savedLayout.name} className="saved-layout-item">
                      <span>{savedLayout.name}</span>
                      <div className="saved-layout-actions">
                        <button
                          className="load-btn"
                          onClick={() => loadLayout(savedLayout)}
                        >
                          Load
                        </button>
                        <button
                          className="delete-btn"
                          onClick={() => deleteLayout(savedLayout.name)}
                        >
                          ×
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="layout-controls-section">
              <button className="reset-btn" onClick={resetToDefault}>
                Reset to Default
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Grid Layout */}
      <ResponsiveGridLayout
        className="grid-layout"
        layout={layout}
        onLayoutChange={handleLayoutChange}
        cols={12}
        rowHeight={60}
        isDraggable={true}
        isResizable={true}
        margin={[12, 12]}
        containerPadding={[0, 0]}
        useCSSTransforms={true}
        preventCollision={false}
        compactType={null}
        verticalCompact={false}
        autoSize={true}
        resizeHandles={['se']}
      >
        {panels.map(panel => (
          <div key={panel.id} className="grid-panel">
            <div className="grid-panel-header">
              <h3>{panel.title}</h3>
              <div className="grid-panel-drag-handle">⋮⋮</div>
            </div>
            <div className="grid-panel-content">
              {panel.content}
            </div>
          </div>
        ))}
      </ResponsiveGridLayout>
    </div>
  )
}