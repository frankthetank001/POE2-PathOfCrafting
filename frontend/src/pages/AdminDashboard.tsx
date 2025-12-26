import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAdmin } from '@/contexts/AdminContext'
import { adminApi } from '@/services/admin-api'
import { CraftListItem, CraftStatus } from '@/types/saved-craft'
import './AdminDashboard.css'

type TabType = 'pending' | 'approved' | 'all'

function AdminDashboard() {
  const navigate = useNavigate()
  const { admin, token, isAuthenticated, isLoading, logout } = useAdmin()
  const [crafts, setCrafts] = useState<CraftListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<TabType>('pending')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [actionLoading, setActionLoading] = useState<number | null>(null)
  const pageSize = 20

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate('/admin/login')
    }
  }, [isLoading, isAuthenticated, navigate])

  useEffect(() => {
    if (token) {
      loadCrafts()
    }
  }, [token, activeTab, page])

  const loadCrafts = async () => {
    if (!token) return

    setLoading(true)
    setError(null)

    try {
      const statusMap: Record<TabType, string | undefined> = {
        pending: CraftStatus.PENDING,
        approved: CraftStatus.APPROVED,
        all: undefined,
      }

      const response = await adminApi.listCrafts(token, {
        page,
        pageSize,
        status: statusMap[activeTab],
      })

      setCrafts(response.items)
      setTotal(response.total)
    } catch (err: any) {
      if (err.response?.status === 401) {
        logout()
        navigate('/admin/login')
      } else {
        setError('Failed to load crafts')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (craftId: number) => {
    if (!token) return
    setActionLoading(craftId)
    try {
      await adminApi.approveCraft(token, craftId)
      loadCrafts()
    } catch (err) {
      console.error('Failed to approve:', err)
    } finally {
      setActionLoading(null)
    }
  }

  const handleReject = async (craftId: number) => {
    if (!token) return
    setActionLoading(craftId)
    try {
      await adminApi.rejectCraft(token, craftId)
      loadCrafts()
    } catch (err) {
      console.error('Failed to reject:', err)
    } finally {
      setActionLoading(null)
    }
  }

  const handleToggleFeatured = async (craftId: number) => {
    if (!token) return
    setActionLoading(craftId)
    try {
      await adminApi.toggleFeatured(token, craftId)
      loadCrafts()
    } catch (err) {
      console.error('Failed to toggle featured:', err)
    } finally {
      setActionLoading(null)
    }
  }

  const handleDelete = async (craftId: number) => {
    if (!token) return
    if (!confirm('Are you sure you want to delete this craft?')) return

    setActionLoading(craftId)
    try {
      await adminApi.deleteCraft(token, craftId)
      loadCrafts()
    } catch (err) {
      console.error('Failed to delete:', err)
    } finally {
      setActionLoading(null)
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const totalPages = Math.ceil(total / pageSize)

  if (isLoading) {
    return <div className="admin-dashboard"><div className="loading-state">Loading...</div></div>
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="admin-dashboard">
      <div className="dashboard-header">
        <div className="header-left">
          <h1>Admin Dashboard</h1>
          <span className="welcome">Welcome, {admin?.username}</span>
        </div>
        <button className="logout-btn" onClick={logout}>Logout</button>
      </div>

      <div className="tab-bar">
        <button
          className={`tab ${activeTab === 'pending' ? 'active' : ''}`}
          onClick={() => { setActiveTab('pending'); setPage(1) }}
        >
          Pending
        </button>
        <button
          className={`tab ${activeTab === 'approved' ? 'active' : ''}`}
          onClick={() => { setActiveTab('approved'); setPage(1) }}
        >
          Approved
        </button>
        <button
          className={`tab ${activeTab === 'all' ? 'active' : ''}`}
          onClick={() => { setActiveTab('all'); setPage(1) }}
        >
          All
        </button>
      </div>

      {loading && <div className="loading-state">Loading crafts...</div>}
      {error && <div className="error-state">{error}</div>}

      {!loading && !error && crafts.length === 0 && (
        <div className="empty-state">No crafts found.</div>
      )}

      {!loading && crafts.length > 0 && (
        <>
          <table className="crafts-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Base</th>
                <th>Submitter</th>
                <th>Status</th>
                <th>Stats</th>
                <th>Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {crafts.map(craft => (
                <tr key={craft.shortId}>
                  <td>
                    <Link to={`/craft/${craft.shortId}`} className="craft-link">
                      {craft.name}
                    </Link>
                    {craft.isOfficial && <span className="badge official">Official</span>}
                    {craft.isFeatured && <span className="badge featured">Featured</span>}
                  </td>
                  <td className="base-cell">{craft.baseName}</td>
                  <td className="submitter-cell">{craft.submitterName || '-'}</td>
                  <td>
                    <span className={`status-badge ${craft.status}`}>
                      {craft.status}
                    </span>
                  </td>
                  <td className="stats-cell">
                    <span>{craft.stepCount} steps</span>
                    <span>{craft.viewCount} views</span>
                  </td>
                  <td className="date-cell">{formatDate(craft.createdAt)}</td>
                  <td className="actions-cell">
                    {craft.status === CraftStatus.PENDING && (
                      <>
                        <button
                          className="action-btn approve"
                          onClick={() => handleApprove(parseInt(craft.shortId))}
                          disabled={actionLoading !== null}
                        >
                          Approve
                        </button>
                        <button
                          className="action-btn reject"
                          onClick={() => handleReject(parseInt(craft.shortId))}
                          disabled={actionLoading !== null}
                        >
                          Reject
                        </button>
                      </>
                    )}
                    {craft.status === CraftStatus.APPROVED && (
                      <button
                        className="action-btn feature"
                        onClick={() => handleToggleFeatured(parseInt(craft.shortId))}
                        disabled={actionLoading !== null}
                      >
                        {craft.isFeatured ? 'Unfeature' : 'Feature'}
                      </button>
                    )}
                    <button
                      className="action-btn delete"
                      onClick={() => handleDelete(parseInt(craft.shortId))}
                      disabled={actionLoading !== null}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

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

export default AdminDashboard
