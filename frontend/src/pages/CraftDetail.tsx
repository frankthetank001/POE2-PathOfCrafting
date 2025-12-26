import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { craftsApi } from '@/services/crafts-api'
import { PublicCraft, CraftSnapshot } from '@/types/saved-craft'
import './CraftDetail.css'

function CraftDetail() {
  const { shortId } = useParams<{ shortId: string }>()
  const navigate = useNavigate()
  const [craft, setCraft] = useState<PublicCraft | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [selectedStep, setSelectedStep] = useState<number | null>(null)

  useEffect(() => {
    if (shortId) {
      loadCraft(shortId)
    }
  }, [shortId])

  const loadCraft = async (id: string) => {
    setLoading(true)
    setError(null)

    try {
      const data = await craftsApi.getCraft(id)
      setCraft(data)
    } catch (err) {
      setError('Craft not found')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleCopyLink = async () => {
    const url = window.location.href
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleImport = async () => {
    if (!craft || !shortId) return

    // Record the import
    try {
      await craftsApi.recordImport(shortId)
    } catch (err) {
      console.error('Failed to record import:', err)
    }

    // Create snapshot and store in sessionStorage for the simulator to pick up
    const snapshot: CraftSnapshot = {
      initialItem: craft.initialItem,
      finalItem: craft.finalItem,
      history: craft.history,
      itemHistory: craft.itemHistory,
      actionHistory: craft.actionHistory,
      currencySpent: craft.currencySpent,
      currencySpentHistory: craft.currencySpentHistory,
    }

    sessionStorage.setItem('importCraft', JSON.stringify(snapshot))
    navigate('/')
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString(undefined, {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    })
  }

  const getTotalCurrency = () => {
    if (!craft) return 0
    return Object.values(craft.currencySpent).reduce((sum, n) => sum + n, 0)
  }

  if (loading) {
    return (
      <div className="craft-detail">
        <div className="loading-state">Loading craft...</div>
      </div>
    )
  }

  if (error || !craft) {
    return (
      <div className="craft-detail">
        <div className="error-state">
          <p>{error || 'Craft not found'}</p>
          <Link to="/crafts">Back to Library</Link>
        </div>
      </div>
    )
  }

  const displayItem = selectedStep !== null && selectedStep < craft.itemHistory.length
    ? craft.itemHistory[selectedStep]
    : craft.finalItem

  return (
    <div className="craft-detail">
      <div className="detail-header">
        <div className="header-main">
          <h1>{craft.name}</h1>
          <div className="header-badges">
            {craft.isOfficial && <span className="badge official">Official</span>}
            {craft.isFeatured && !craft.isOfficial && <span className="badge featured">Featured</span>}
          </div>
        </div>

        <div className="header-meta">
          {craft.submitterName && <span>by {craft.submitterName}</span>}
          <span>{formatDate(craft.createdAt)}</span>
          <span>{craft.viewCount} views</span>
          <span>{craft.importCount} imports</span>
        </div>

        {craft.description && (
          <p className="craft-description">{craft.description}</p>
        )}

        <div className="header-actions">
          <button className="import-btn" onClick={handleImport}>
            Import to Simulator
          </button>
          <button className="copy-btn" onClick={handleCopyLink}>
            {copied ? 'Copied!' : 'Copy Link'}
          </button>
          <Link to="/crafts" className="back-link">Back to Library</Link>
        </div>
      </div>

      <div className="detail-content">
        <div className="craft-summary">
          <div className="summary-card">
            <span className="summary-label">Base Item</span>
            <span className="summary-value">{craft.finalItem.base_name}</span>
          </div>
          <div className="summary-card">
            <span className="summary-label">Category</span>
            <span className="summary-value">{craft.finalItem.base_category}</span>
          </div>
          <div className="summary-card">
            <span className="summary-label">Steps</span>
            <span className="summary-value">{craft.history.length}</span>
          </div>
          <div className="summary-card">
            <span className="summary-label">Total Currency</span>
            <span className="summary-value">{getTotalCurrency()}</span>
          </div>
        </div>

        <div className="craft-panels">
          <div className="history-panel">
            <h3>Crafting Steps</h3>
            <div className="history-list">
              <div
                className={`history-item ${selectedStep === null ? 'active' : ''}`}
                onClick={() => setSelectedStep(null)}
              >
                <span className="step-number">Final</span>
                <span className="step-description">Final Result</span>
              </div>
              {craft.history.map((step, index) => (
                <div
                  key={index}
                  className={`history-item ${selectedStep === index ? 'active' : ''}`}
                  onClick={() => setSelectedStep(index)}
                >
                  <span className="step-number">{index + 1}</span>
                  <span className="step-description">{step}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="item-panel">
            <h3>
              {selectedStep === null
                ? 'Final Item'
                : `After Step ${selectedStep + 1}`}
            </h3>
            <div className="item-display">
              <div className="item-header">
                <span className="item-name">{displayItem.base_name}</span>
                <span className="item-rarity">{displayItem.rarity}</span>
              </div>

              {displayItem.implicit_mods.length > 0 && (
                <div className="mod-section implicit">
                  {displayItem.implicit_mods.map((mod, i) => (
                    <div key={i} className="mod-line">{mod.stat_text}</div>
                  ))}
                </div>
              )}

              {(displayItem.prefix_mods.length > 0 || displayItem.suffix_mods.length > 0) && (
                <div className="mod-section explicit">
                  {displayItem.prefix_mods.map((mod, i) => (
                    <div key={`p${i}`} className="mod-line prefix">
                      <span className="mod-type">P</span>
                      {mod.stat_text}
                    </div>
                  ))}
                  {displayItem.suffix_mods.map((mod, i) => (
                    <div key={`s${i}`} className="mod-line suffix">
                      <span className="mod-type">S</span>
                      {mod.stat_text}
                    </div>
                  ))}
                </div>
              )}

              {displayItem.prefix_mods.length === 0 && displayItem.suffix_mods.length === 0 && (
                <div className="no-mods">No modifiers</div>
              )}
            </div>
          </div>
        </div>

        <div className="currency-breakdown">
          <h3>Currency Used</h3>
          <div className="currency-list">
            {Object.entries(craft.currencySpent)
              .filter(([, count]) => count > 0)
              .sort((a, b) => b[1] - a[1])
              .map(([currency, count]) => (
                <div key={currency} className="currency-item">
                  <span className="currency-name">{currency}</span>
                  <span className="currency-count">x{count}</span>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default CraftDetail
