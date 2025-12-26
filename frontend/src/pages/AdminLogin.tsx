import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAdmin } from '@/contexts/AdminContext'
import { adminApi } from '@/services/admin-api'
import './AdminLogin.css'

function AdminLogin() {
  const navigate = useNavigate()
  const { login, isAuthenticated } = useAdmin()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  // Redirect if already logged in
  if (isAuthenticated) {
    navigate('/admin')
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const response = await adminApi.login(username, password)
      const user = await adminApi.getMe(response.accessToken)
      login(response.accessToken, { id: user.id, username: user.username })
      navigate('/admin')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="admin-login">
      <div className="login-card">
        <h1>Admin Login</h1>
        <p className="login-subtitle">Sign in to manage crafts</p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
          </div>

          {error && <p className="error-message">{error}</p>}

          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default AdminLogin
