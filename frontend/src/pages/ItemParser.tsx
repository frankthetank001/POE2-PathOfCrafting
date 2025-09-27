import { useState } from 'react'
import { itemsApi } from '@/services/api'
import type { ParsedItem } from '@/types/item'
import './ItemParser.css'

function ItemParser() {
  const [itemText, setItemText] = useState('')
  const [parsedItem, setParsedItem] = useState<ParsedItem | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleParse = async () => {
    if (!itemText.trim()) {
      setError('Please paste an item')
      return
    }

    setLoading(true)
    setError(null)
    setParsedItem(null)

    try {
      const response = await itemsApi.parseItem({ item_text: itemText })

      if (response.success && response.item) {
        setParsedItem(response.item)
      } else {
        setError(response.error || 'Failed to parse item')
      }
    } catch (err) {
      setError('Network error: Could not connect to API')
    } finally {
      setLoading(false)
    }
  }

  const getRarityColor = (rarity: string) => {
    switch (rarity) {
      case 'Normal': return '#c8c8c8'
      case 'Magic': return '#8888ff'
      case 'Rare': return '#ffff77'
      case 'Unique': return '#af6025'
      default: return '#c8c8c8'
    }
  }

  return (
    <div className="item-parser">
      <h2 className="page-title">Item Parser</h2>
      <p className="page-subtitle">Paste an item from Path of Exile 2 (Ctrl+C)</p>

      <div className="parser-container">
        <div className="input-section">
          <textarea
            className="item-input"
            value={itemText}
            onChange={(e) => setItemText(e.target.value)}
            placeholder="Rarity: Rare&#10;Doom Knuckle&#10;Bronze Gauntlets&#10;--------&#10;Quality: +20% (augmented)&#10;Armour: 45 (augmented)&#10;--------&#10;Requirements:&#10;Level: 15&#10;Str: 28&#10;--------&#10;Sockets: R-R&#10;--------&#10;Item Level: 28&#10;--------&#10;+18 to maximum Life&#10;+15% to Fire Resistance&#10;12% increased Rarity of Items found"
            rows={15}
          />
          <button
            className="parse-button"
            onClick={handleParse}
            disabled={loading}
          >
            {loading ? 'Parsing...' : 'Parse Item'}
          </button>
        </div>

        <div className="output-section">
          {error && (
            <div className="error-message">
              <strong>Error:</strong> {error}
            </div>
          )}

          {parsedItem && (
            <div className="parsed-item">
              <div className="item-header">
                <h3
                  className="item-name"
                  style={{ color: getRarityColor(parsedItem.rarity) }}
                >
                  {parsedItem.name}
                </h3>
                <p className="item-base">{parsedItem.base_type}</p>
                <span className="item-rarity">{parsedItem.rarity}</span>
              </div>

              <div className="item-details">
                {parsedItem.item_level && (
                  <div className="detail-row">
                    <span className="detail-label">Item Level:</span>
                    <span className="detail-value">{parsedItem.item_level}</span>
                  </div>
                )}

                {parsedItem.quality && (
                  <div className="detail-row">
                    <span className="detail-label">Quality:</span>
                    <span className="detail-value">+{parsedItem.quality}%</span>
                  </div>
                )}

                {parsedItem.sockets.length > 0 && (
                  <div className="detail-row">
                    <span className="detail-label">Sockets:</span>
                    <span className="detail-value">{parsedItem.sockets.length}</span>
                  </div>
                )}

                {Object.keys(parsedItem.requirements).length > 0 && (
                  <div className="detail-row">
                    <span className="detail-label">Requirements:</span>
                    <span className="detail-value">
                      {Object.entries(parsedItem.requirements).map(([key, val]) =>
                        `${key}: ${val}`
                      ).join(', ')}
                    </span>
                  </div>
                )}
              </div>

              {parsedItem.implicits.length > 0 && (
                <div className="mods-section">
                  <h4 className="mods-title">Implicits</h4>
                  {parsedItem.implicits.map((mod, idx) => (
                    <div key={idx} className="mod-line implicit">
                      {mod.text}
                    </div>
                  ))}
                </div>
              )}

              {parsedItem.explicits.length > 0 && (
                <div className="mods-section">
                  <h4 className="mods-title">Explicits</h4>
                  {parsedItem.explicits.map((mod, idx) => (
                    <div key={idx} className="mod-line explicit">
                      {mod.text}
                    </div>
                  ))}
                </div>
              )}

              {parsedItem.corrupted && (
                <div className="corrupted-tag">Corrupted</div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ItemParser