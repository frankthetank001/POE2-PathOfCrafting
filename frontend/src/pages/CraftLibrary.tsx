import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { craftsApi, ListCraftsParams } from '@/services/crafts-api'
import { CraftListItem, CraftListResponse, LocalCraft } from '@/types/saved-craft'
import { localCraftsService } from '@/services/local-crafts'
import './CraftLibrary.css'

function CraftLibrary() {
  const navigate = useNavigate()
  const [crafts, setCrafts] = useState<CraftListItem[]>([])
  const [localCrafts, setLocalCrafts] = useState<LocalCraft[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [showLocalCrafts, setShowLocalCrafts] = useState(true)
  const pageSize = 12

  useEffect(() => {
    loadCrafts()
    loadLocalCrafts()
  }, [page, search])

  const loadLocalCrafts = () => {
    const local = localCraftsService.getAll()
    setLocalCrafts(local)
  }

  const loadCrafts = async () => {
    setLoading(true)
    setError(null)

    try {
      const params: ListCraftsParams = {
        page,
        pageSize,
        search: search || undefined,
      }
      const response = await craftsApi.listCrafts(params)
      setCrafts(response.items)
      setTotal(response.total)
    } catch (err) {
      setError('Failed to load crafts')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    setSearch(searchInput)
  }

  const totalPages = Math.ceil(total / pageSize)

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  const handleLoadLocal = (craft: LocalCraft) => {
    // Navigate to simulator with craft loaded via query params or state
    navigate('/', { state: { loadCraft: craft } })
  }

  const handleDeleteLocal = (id: string) => {
    localCraftsService.remove(id)
    loadLocalCrafts()
  }

  const getTotalCurrency = (craft: LocalCraft) => {
    return Object.values(craft.snapshot.currencySpent).reduce((sum, n) => sum + n, 0)
  }

  return (
    <div className="craft-library">
      <div className="library-header">
        <h1>Craft Library</h1>
        <p>Browse community-submitted crafts</p>
      </div>

      <form className="search-form" onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Search crafts..."
          value={searchInput}
          onChange={e => setSearchInput(e.target.value)}
        />
        <button type="submit">Search</button>
      </form>

      {/* Local Crafts Section */}
      {localCrafts.length > 0 && (
        <div className="local-crafts-section">
          <div className="section-header" onClick={() => setShowLocalCrafts(!showLocalCrafts)}>
            <h2>My Saved Crafts ({localCrafts.length})</h2>
            <span className="toggle-icon">{showLocalCrafts ? '▼' : '▶'}</span>
          </div>
          {showLocalCrafts && (
            <div className="crafts-grid local-grid">
              {localCrafts.map(craft => (
                <div key={craft.id} className="craft-card local-card">
                  <div className="craft-card-header">
                    <span className="craft-name">{craft.name}</span>
                    <span className="badge local">Local</span>
                  </div>

                  <div className="craft-base">
                    {craft.snapshot.finalItem.base_name}
                  </div>

                  {craft.description && (
                    <p className="craft-description">{craft.description}</p>
                  )}

                  <div className="craft-stats">
                    <span>{craft.snapshot.history.length} steps</span>
                    <span>{getTotalCurrency(craft)} currency</span>
                  </div>

                  <div className="craft-footer">
                    <span className="craft-date">{formatDate(craft.createdAt)}</span>
                  </div>

                  <div className="local-craft-actions">
                    <button
                      className="load-local-btn"
                      onClick={() => handleLoadLocal(craft)}
                    >
                      Load
                    </button>
                    <button
                      className="delete-local-btn"
                      onClick={() => handleDeleteLocal(craft.id)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Community Crafts Section */}
      <div className="community-crafts-section">
        <h2>Community Crafts</h2>
      </div>

      {loading && (
        <div className="loading-state">Loading crafts...</div>
      )}

      {error && (
        <div className="error-state">{error}</div>
      )}

      {!loading && !error && crafts.length === 0 && (
        <div className="empty-state">
          <p>No crafts found.</p>
          {search && <p>Try a different search term.</p>}
        </div>
      )}

      {!loading && crafts.length > 0 && (
        <>
          <div className="crafts-grid">
            {crafts.map(craft => (
              <Link
                key={craft.shortId}
                to={`/craft/${craft.shortId}`}
                className="craft-card"
              >
                <div className="craft-card-header">
                  <span className="craft-name">{craft.name}</span>
                  {craft.isOfficial && <span className="badge official">Official</span>}
                  {craft.isFeatured && !craft.isOfficial && <span className="badge featured">Featured</span>}
                </div>

                <div className="craft-base">
                  {craft.baseName}
                </div>

                {craft.description && (
                  <p className="craft-description">{craft.description}</p>
                )}

                <div className="craft-stats">
                  <span>{craft.stepCount} steps</span>
                  <span>{craft.totalCurrencySpent} currency</span>
                </div>

                <div className="craft-footer">
                  {craft.submitterName && (
                    <span className="craft-author">by {craft.submitterName}</span>
                  )}
                  <span className="craft-date">{formatDate(craft.createdAt)}</span>
                </div>

                <div className="craft-metrics">
                  <span title="Views">{craft.viewCount} views</span>
                  <span title="Imports">{craft.importCount} imports</span>
                </div>
              </Link>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                Previous
              </button>
              <span>Page {page} of {totalPages}</span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default CraftLibrary
