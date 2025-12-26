import { useState, useEffect } from 'react'
import { LocalCraft, CraftSnapshot } from '@/types/saved-craft'
import { localCraftsService } from '@/services/local-crafts'
import { craftsApi } from '@/services/crafts-api'
import './LocalCraftsList.css'

interface LocalCraftsListProps {
  isOpen: boolean
  onClose: () => void
  onLoad: (snapshot: CraftSnapshot) => void
}

export function LocalCraftsList({ isOpen, onClose, onLoad }: LocalCraftsListProps) {
  const [crafts, setCrafts] = useState<LocalCraft[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState<string | null>(null)
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      setCrafts(localCraftsService.getAll())
      setSelectedId(null)
      setConfirmDelete(null)
      setSubmitSuccess(null)
    }
  }, [isOpen])

  if (!isOpen) return null

  const handleLoad = () => {
    if (!selectedId) return
    const craft = localCraftsService.get(selectedId)
    if (craft) {
      onLoad(craft.snapshot)
      onClose()
    }
  }

  const handleDelete = (id: string) => {
    if (confirmDelete === id) {
      localCraftsService.remove(id)
      setCrafts(localCraftsService.getAll())
      setConfirmDelete(null)
      if (selectedId === id) setSelectedId(null)
    } else {
      setConfirmDelete(id)
    }
  }

  const handleSubmit = async (craft: LocalCraft) => {
    setSubmitting(craft.id)
    try {
      await craftsApi.submitCraft({
        name: craft.name,
        description: craft.description,
        snapshot: craft.snapshot,
      })
      setSubmitSuccess(craft.id)
      setTimeout(() => setSubmitSuccess(null), 3000)
    } catch (err) {
      console.error('Failed to submit craft:', err)
    } finally {
      setSubmitting(null)
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getTotalCurrency = (craft: LocalCraft) => {
    const spent = craft.snapshot.currencySpent
    return Object.values(spent).reduce((sum, n) => sum + n, 0)
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="local-crafts-modal" onClick={e => e.stopPropagation()}>
        <h3>Saved Crafts</h3>

        {crafts.length === 0 ? (
          <div className="no-crafts">
            <p>No saved crafts yet.</p>
            <p className="no-crafts-hint">Use the Save button to save your crafting progress.</p>
          </div>
        ) : (
          <>
            <div className="crafts-list">
              {crafts.map(craft => (
                <div
                  key={craft.id}
                  className={`craft-item ${selectedId === craft.id ? 'selected' : ''}`}
                  onClick={() => setSelectedId(craft.id)}
                >
                  <div className="craft-header">
                    <span className="craft-name">{craft.name}</span>
                    <span className="craft-date">{formatDate(craft.createdAt)}</span>
                  </div>

                  <div className="craft-details">
                    <span className="craft-base">
                      {craft.snapshot.finalItem.base_name}
                    </span>
                    <span className="craft-stats">
                      {craft.snapshot.history.length} steps | {getTotalCurrency(craft)} currency
                    </span>
                  </div>

                  {craft.description && (
                    <p className="craft-description">{craft.description}</p>
                  )}

                  <div className="craft-actions">
                    <button
                      className="submit-btn"
                      onClick={e => {
                        e.stopPropagation()
                        handleSubmit(craft)
                      }}
                      disabled={submitting === craft.id || submitSuccess === craft.id}
                      title="Submit for public review"
                    >
                      {submitSuccess === craft.id
                        ? 'Submitted!'
                        : submitting === craft.id
                        ? 'Submitting...'
                        : 'Submit'}
                    </button>

                    <button
                      className={`delete-btn ${confirmDelete === craft.id ? 'confirm' : ''}`}
                      onClick={e => {
                        e.stopPropagation()
                        handleDelete(craft.id)
                      }}
                      title={confirmDelete === craft.id ? 'Click again to confirm' : 'Delete'}
                    >
                      {confirmDelete === craft.id ? 'Confirm?' : 'Delete'}
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="modal-buttons">
              <button
                className="load-btn"
                onClick={handleLoad}
                disabled={!selectedId}
              >
                Load Selected
              </button>
              <button className="cancel-btn" onClick={onClose}>
                Cancel
              </button>
            </div>
          </>
        )}

        {crafts.length === 0 && (
          <button className="cancel-btn solo" onClick={onClose}>
            Close
          </button>
        )}
      </div>
    </div>
  )
}
