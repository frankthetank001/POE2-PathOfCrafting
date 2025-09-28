import type { CraftableItem } from '@/types/crafting'

interface HistoryPanelProps {
  itemHistory: CraftableItem[]
  history: string[]
  currencySpent: Record<string, number>
  onRevertToStep: (stepIndex: number) => void
  onClearHistory: () => void
}

export function HistoryPanel({
  itemHistory,
  history,
  currencySpent,
  onRevertToStep,
  onClearHistory
}: HistoryPanelProps) {
  const formatModText = (mod: any): string => {
    if (mod.current_value !== undefined && mod.stat_text.includes('{}')) {
      return mod.stat_text.replace('{}', mod.current_value.toString())
    }
    return mod.stat_text
  }

  const getTotalSpent = (): number => {
    return Object.values(currencySpent).reduce((sum, count) => sum + count, 0)
  }

  const getItemSummary = (item: CraftableItem): string => {
    const totalMods = (item.prefix_mods?.length || 0) + (item.suffix_mods?.length || 0)
    return `${item.base_name} (${totalMods} mods)`
  }

  const getItemModsSummary = (item: CraftableItem): string[] => {
    const mods: string[] = []

    // Add prefixes
    item.prefix_mods?.forEach(mod => {
      mods.push(`• ${formatModText(mod)}`)
    })

    // Add suffixes
    item.suffix_mods?.forEach(mod => {
      mods.push(`• ${formatModText(mod)}`)
    })

    return mods
  }

  return (
    <div className="history-panel">
      {/* Currency Spending Summary */}
      {getTotalSpent() > 0 && (
        <div className="spending-summary">
          <h4>Currency Spent</h4>
          <div className="spending-list">
            {Object.entries(currencySpent)
              .filter(([, count]) => count > 0)
              .sort(([, a], [, b]) => b - a)
              .map(([currency, count]) => (
                <div key={currency} className="spending-item">
                  <span className="currency-name">{currency}</span>
                  <span className="currency-count">×{count}</span>
                </div>
              ))}
          </div>
          <div className="spending-total">
            <strong>Total: {getTotalSpent()} operations</strong>
          </div>
        </div>
      )}

      {/* Craft History */}
      <div className="craft-history">
        <div className="history-header">
          <h4>Craft History ({history.length} steps)</h4>
          {history.length > 0 && (
            <button
              onClick={onClearHistory}
              className="clear-history-btn"
              title="Clear all history"
            >
              Clear
            </button>
          )}
        </div>

        {history.length === 0 ? (
          <div className="no-history">
            No crafting history yet. Start crafting to see your progress!
          </div>
        ) : (
          <div className="history-list">
            {history.map((step, index) => (
              <div key={index} className="history-step">
                <div className="step-header">
                  <span className="step-number">#{index + 1}</span>
                  <span className="step-action">{step}</span>
                  {index < itemHistory.length && (
                    <button
                      onClick={() => onRevertToStep(index)}
                      className="revert-btn"
                      title="Revert to this step"
                    >
                      ↶
                    </button>
                  )}
                </div>

                {index < itemHistory.length && (
                  <div className="step-item-summary">
                    <div className="item-name">
                      {getItemSummary(itemHistory[index])}
                    </div>
                    {getItemModsSummary(itemHistory[index]).length > 0 && (
                      <div className="item-mods">
                        {getItemModsSummary(itemHistory[index]).map((mod, modIndex) => (
                          <div key={modIndex} className="mod-summary">
                            {mod}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Stats */}
      {itemHistory.length > 0 && (
        <div className="quick-stats">
          <h4>Quick Stats</h4>
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-label">Total Crafts:</span>
              <span className="stat-value">{history.length}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Current Mods:</span>
              <span className="stat-value">
                {(itemHistory[itemHistory.length - 1]?.prefix_mods?.length || 0) +
                 (itemHistory[itemHistory.length - 1]?.suffix_mods?.length || 0)}
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Success Rate:</span>
              <span className="stat-value">
                {history.length > 0 ? Math.round((history.filter(h => !h.includes('Failed')).length / history.length) * 100) : 0}%
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}