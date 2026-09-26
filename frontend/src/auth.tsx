import { useCallback, useEffect, useState, type ReactNode } from 'react'
import * as api from './api'
import { AuthContext } from './useAuth'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<api.User | null>(null)
  const [loading, setLoading] = useState(true)

  // The session lives in an HttpOnly cookie, so ask the server who is logged in.
  useEffect(() => {
    api
      .getMe()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const u = await api.login(email, password)
    setUser(u)
    return u
  }, [])

  const register = useCallback(async (input: api.RegisterInput) => {
    const u = await api.register(input)
    setUser(u)
    return u
  }, [])

  const logout = useCallback(async () => {
    await api.logout().catch(() => undefined)
    setUser(null)
  }, [])

  return <AuthContext.Provider value={{ user, loading, login, register, logout }}>{children}</AuthContext.Provider>
}

