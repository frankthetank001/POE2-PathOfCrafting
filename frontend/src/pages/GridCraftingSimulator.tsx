import { useState } from 'react'
import { GridDashboard, GridPanel } from '@/components/GridDashboard'
import { ItemCreationPanel } from '@/components/panels/ItemCreationPanel'
import { ItemDisplayPanel } from '@/components/panels/ItemDisplayPanel'
import { CraftingControlsPanel } from '@/components/panels/CraftingControlsPanel'
import { AvailableModsPanel } from '@/components/panels/AvailableModsPanel'
import { HistoryPanel } from '@/components/panels/HistoryPanel'
import type { CraftableItem, ItemRarity } from '@/types/crafting'
import './CraftingSimulator.css'

function GridCraftingSimulator() {
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

  // Define the panels for the grid dashboard
  const panels: GridPanel[] = [
    {
      id: 'item-creation',
      title: 'Item Creation',
      defaultLayout: { x: 0, y: 0, w: 3, h: 8, minW: 3, minH: 6 },
      content: (
        <ItemCreationPanel
          item={item}
          onItemChange={setItem}
          onMessage={setMessage}
          onHistoryReset={handleHistoryReset}
        />
      ),
    },
    {
      id: 'item-display',
      title: 'Current Item',
      defaultLayout: { x: 3, y: 0, w: 4, h: 12, minW: 3, minH: 8 },
      content: <ItemDisplayPanel item={item} />,
    },
    {
      id: 'crafting-controls',
      title: 'Crafting Controls',
      defaultLayout: { x: 0, y: 8, w: 3, h: 8, minW: 3, minH: 6 },
      content: (
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
      ),
    },
    {
      id: 'available-mods',
      title: 'Available Mods',
      defaultLayout: { x: 7, y: 0, w: 5, h: 16, minW: 4, minH: 10 },
      content: <AvailableModsPanel item={item} />,
    },
    {
      id: 'history',
      title: 'Craft History',
      defaultLayout: { x: 0, y: 16, w: 7, h: 8, minW: 4, minH: 6 },
      content: (
        <HistoryPanel
          itemHistory={itemHistory}
          history={history}
          currencySpent={currencySpent}
          onRevertToStep={handleRevertToStep}
          onClearHistory={handleClearHistory}
        />
      ),
    },
  ]

  return (
    <div className="grid-crafting-simulator">
      <GridDashboard
        panels={panels}
        className="crafting-grid"
      />
    </div>
  )
}

export default GridCraftingSimulator