import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface AuthContextType {
  token: string | null
  email: string | null
  login: (token: string, email: string) => void
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(localStorage.getItem('arb_token'))
  const [email, setEmail] = useState<string | null>(localStorage.getItem('arb_email'))

  useEffect(() => {
    if (token) {
      localStorage.setItem('arb_token', token)
    } else {
      localStorage.removeItem('arb_token')
    }
  }, [token])

  useEffect(() => {
    if (email) {
      localStorage.setItem('arb_email', email)
    } else {
      localStorage.removeItem('arb_email')
    }
  }, [email])

  const login = (newToken: string, newEmail: string) => {
    setToken(newToken)
    setEmail(newEmail)
  }

  const logout = () => {
    setToken(null)
    setEmail(null)
  }

  return (
    <AuthContext.Provider value={{ token, email, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
