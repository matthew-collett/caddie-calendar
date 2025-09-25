import { createContext, useContext, type ReactNode } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, type LoginRequest, type User } from '@/lib'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isCheckingAuth: boolean
  isLoggingIn: boolean
  isLoggingOut: boolean
  login: (credentials: LoginRequest) => Promise<void>
  logout: () => Promise<void>
  error: string | null
}

const AUTH_QUERIES = {
  status: ['auth', 'status'] as const,
  user: ['user'] as const
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const getUser = async (): Promise<User | null> => {
  const token = localStorage.getItem('auth_token')
  if (!token) return null

  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return await api.users.get(payload.user_id)
  } catch {
    return null
  }
}

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const queryClient = useQueryClient()

  const { data: authStatus, isLoading: isCheckingAuth } = useQuery({
    queryKey: AUTH_QUERIES.status,
    queryFn: api.auth.status,
    enabled: !!localStorage.getItem('auth_token'),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    refetchInterval: 5 * 60 * 1000,
    retry: 1
  })

  const { data: user, isLoading: isLoadingUser } = useQuery({
    queryKey: AUTH_QUERIES.user,
    queryFn: getUser,
    enabled: !!authStatus?.auth,
    staleTime: 10 * 60 * 1000
  })

  const loginMutation = useMutation({
    mutationFn: api.auth.login,
    onSuccess: (data) => {
      localStorage.setItem('auth_token', data.token)
      queryClient.invalidateQueries({ queryKey: AUTH_QUERIES.status })
    },
    onError: () => {
      localStorage.removeItem('auth_token')
    }
  })

  const logoutMutation = useMutation({
    mutationFn: api.auth.logout,
    onSettled: () => {
      localStorage.removeItem('auth_token')
      queryClient.removeQueries({ queryKey: ['auth'] })
      queryClient.clear()
    }
  })

  const login = async (credentials: LoginRequest) => {
    await loginMutation.mutateAsync(credentials)
  }

  const logout = async () => {
    await logoutMutation.mutateAsync()
  }

  const isAuthenticated = !!authStatus?.auth && (!!user || isLoadingUser)
  const error = loginMutation.error?.message || logoutMutation.error?.message || null

  const value: AuthContextType = {
    user: user ?? null,
    isAuthenticated,
    isCheckingAuth,
    isLoggingIn: loginMutation.isPending,
    isLoggingOut: logoutMutation.isPending,
    login,
    logout,
    error
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
