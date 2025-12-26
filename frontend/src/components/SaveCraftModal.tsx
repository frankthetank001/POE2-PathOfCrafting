import { useState } from 'react'
import { CraftSnapshot } from '@/types/saved-craft'
import { localCraftsService } from '@/services/local-crafts'
import { craftsApi } from '@/services/crafts-api'
import './SaveCraftModal.css'

interface SaveCraftModalProps {
  isOpen: boolean
  onClose: () => void
  snapshot: CraftSnapshot
  onSaved?: () => void
}

export function SaveCraftModal({ isOpen, onClose, snapshot, onSaved }: SaveCraftModalProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [submitterName, setSubmitterName] = useState('')
  const [saveMode, setSaveMode] = useState<'local' | 'submit'>('local')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<{ type: 'local' | 'submit', shortId?: string } | null>(null)

  if (!isOpen) return null

  const handleSave = async () => {
    if (!name.trim()) {
      setError('Please enter a name for your craft')
      return
    }

    setLoading(true)
    setError(null)

    try {
      if (saveMode === 'local') {
        localCraftsService.save(name.trim(), snapshot, description.trim() || undefined)
        setSuccess({ type: 'local' })
      } else {
        const result = await craftsApi.submitCraft({
          name: name.trim(),
          description: description.trim() || undefined,
          submitterName: submitterName.trim() || undefined,
          snapshot,
        })
        setSuccess({ type: 'submit', shortId: result.shortId })
      }
      onSaved?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save craft')
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setName('')
    setDescription('')
    setSubmitterName('')
    setError(null)
    setSuccess(null)
    setSaveMode('local')
    onClose()
  }

  const craftCount = localCraftsService.count()
  const isAtLimit = localCraftsService.isAtLimit()

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="save-craft-modal" onClick={e => e.stopPropagation()}>
        <h3>Save Craft</h3>

        {success ? (
          <div className="save-success">
            {success.type === 'local' ? (
              <>
                <p className="success-message">Craft saved locally!</p>
                <p className="success-detail">
                  You can find it in your saved crafts ({craftCount}/{localCraftsService.MAX_CRAFTS})
                </p>
              </>
            ) : (
              <>
                <p className="success-message">Craft submitted for review!</p>
                <p className="success-detail">
                  Once approved, it will be available at:<br />
                  <code>/craft/{success.shortId}</code>
                </p>
              </>
            )}
            <button className="close-modal-btn" onClick={handleClose}>
              Close
            </button>
          </div>
        ) : (
          <>
            <div className="save-mode-tabs">
              <button
                className={`save-mode-tab ${saveMode === 'local' ? 'active' : ''}`}
                onClick={() => setSaveMode('local')}
                disabled={isAtLimit}
                title={isAtLimit ? 'Local storage limit reached' : 'Save to browser'}
              >
                Save Locally
              </button>
              <button
                className={`save-mode-tab ${saveMode === 'submit' ? 'active' : ''}`}
                onClick={() => setSaveMode('submit')}
              >
                Submit for Review
              </button>
            </div>

            <div className="save-form">
              <div className="form-group">
                <label htmlFor="craft-name">Name *</label>
                <input
                  id="craft-name"
                  type="text"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="e.g., Budget Phys Weapon"
                  maxLength={255}
                  autoFocus
                />
              </div>

              <div className="form-group">
                <label htmlFor="craft-description">Description</label>
                <textarea
                  id="craft-description"
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  placeholder="Optional notes about this craft..."
                  maxLength={2000}
                  rows={3}
                />
              </div>

              {saveMode === 'submit' && (
                <div className="form-group">
                  <label htmlFor="submitter-name">Your Name (optional)</label>
                  <input
                    id="submitter-name"
                    type="text"
                    value={submitterName}
                    onChange={e => setSubmitterName(e.target.value)}
                    placeholder="Credit name (shown publicly)"
                    maxLength={255}
                  />
                </div>
              )}

              {saveMode === 'local' && (
                <p className="save-info">
                  Saved crafts are stored in your browser ({craftCount}/{localCraftsService.MAX_CRAFTS}).
                </p>
              )}

              {saveMode === 'submit' && (
                <p className="save-info">
                  Submitted crafts will be reviewed by an admin before being made public.
                </p>
              )}

              {error && <p className="error-message">{error}</p>}

              <div className="modal-buttons">
                <button
                  className="save-btn"
                  onClick={handleSave}
                  disabled={loading || !name.trim()}
                >
                  {loading ? 'Saving...' : saveMode === 'local' ? 'Save' : 'Submit'}
                </button>
                <button className="cancel-btn" onClick={handleClose} disabled={loading}>
                  Cancel
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
