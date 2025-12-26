import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { craftsApi, ListCraftsParams } from '@/services/crafts-api'
import { CraftListItem, CraftListResponse } from '@/types/saved-craft'
import './CraftLibrary.css'

function CraftLibrary() {
  const [crafts, setCrafts] = useState<CraftListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const pageSize = 12

  useEffect(() => {
    loadCrafts()
  }, [page, search])

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
