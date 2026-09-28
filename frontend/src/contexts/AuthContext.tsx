import React, { createContext, useContext, useState, useEffect } from 'react'

interface AuthContextType {
  token: string | null
  userId: string | null
  userEmail: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (token: string, userId: string, userEmail: string) => void
  logout: () => void
  getAuthHeader: () => { Authorization: string } | {}
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null)
  const [userId, setUserId] = useState<string | null>(null)
  const [userEmail, setUserEmail] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Initialize from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token')
    const storedUserId = localStorage.getItem('user_id')
    const storedEmail = localStorage.getItem('user_email')

    if (storedToken && storedUserId) {
      setToken(storedToken)
      setUserId(storedUserId)
      setUserEmail(storedEmail)
    }
    
    setIsLoading(false)
  }, [])

  const login = (newToken: string, newUserId: string, newUserEmail: string) => {
    setToken(newToken)
    setUserId(newUserId)
    setUserEmail(newUserEmail)
    localStorage.setItem('auth_token', newToken)
    localStorage.setItem('user_id', newUserId)
    localStorage.setItem('user_email', newUserEmail)
  }

  const logout = () => {
    setToken(null)
    setUserId(null)
    setUserEmail(null)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_id')
    localStorage.removeItem('user_email')
  }

  const getAuthHeader = () => {
    if (!token) return {}
    return { Authorization: `Bearer ${token}` }
  }

  const isAuthenticated = !!token && !!userId

  return (
    <AuthContext.Provider value={{ token, userId, userEmail, isAuthenticated, isLoading, login, logout, getAuthHeader }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
