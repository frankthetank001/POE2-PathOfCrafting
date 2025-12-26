import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface AdminUser {
  id: number
  username: string
}

interface AdminContextType {
  admin: AdminUser | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (token: string, user: AdminUser) => void
  logout: () => void
}

const AdminContext = createContext<AdminContextType | undefined>(undefined)

const STORAGE_KEY = 'admin_token'
const USER_KEY = 'admin_user'

export function AdminProvider({ children }: { children: ReactNode }) {
  const [admin, setAdmin] = useState<AdminUser | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Load saved auth state
    const savedToken = localStorage.getItem(STORAGE_KEY)
    const savedUser = localStorage.getItem(USER_KEY)

    if (savedToken && savedUser) {
      try {
        setToken(savedToken)
        setAdmin(JSON.parse(savedUser))
      } catch (err) {
        console.error('Failed to parse saved admin user:', err)
        localStorage.removeItem(STORAGE_KEY)
        localStorage.removeItem(USER_KEY)
      }
    }

    setIsLoading(false)
  }, [])

  const login = (newToken: string, user: AdminUser) => {
    setToken(newToken)
    setAdmin(user)
    localStorage.setItem(STORAGE_KEY, newToken)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  }

  const logout = () => {
    setToken(null)
    setAdmin(null)
    localStorage.removeItem(STORAGE_KEY)
    localStorage.removeItem(USER_KEY)
  }

  return (
    <AdminContext.Provider
      value={{
        admin,
        token,
        isAuthenticated: !!token && !!admin,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AdminContext.Provider>
  )
}

export function useAdmin() {
  const context = useContext(AdminContext)
  if (context === undefined) {
    throw new Error('useAdmin must be used within an AdminProvider')
  }
  return context
}
