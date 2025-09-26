import {
  type LoginRequest,
  type LoginResponse,
  type AuthStatus,
  type Member,
  type Booking,
  type BookingRequest,
  type User,
  type Notification
} from '@/lib'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
    this.name = 'ApiError'
  }
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem('auth_token')

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options?.headers
    },
    ...options
  })

  if (!response.ok) {
    const errorText = await response.text()
    let errorMessage = `HTTP ${response.status}`

    try {
      const errorJson = JSON.parse(errorText)
      errorMessage = errorJson.error || errorMessage
    } catch {
      errorMessage = errorText || errorMessage
    }

    throw new ApiError(response.status, errorMessage)
  }

  return response.json()
}

export const auth = {
  login: (credentials: LoginRequest) =>
    request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials)
    }),

  logout: () =>
    request<{ success: boolean }>('/auth/logout', {
      method: 'POST'
    }),

  status: () => request<AuthStatus>('/auth/status')
}

export const users = {
  get: (id: number) => request<User>(`/users/${id}`, { method: 'GET' }),

  searchMembers: (nameFilter: string) => {
    const params = new URLSearchParams({ name_filter: nameFilter })
    return request<Member[]>(`/users?${params}`)
  }
}

export const bookings = {
  create: (bookingData: BookingRequest) =>
    request<{ id: number }>('/bookings', {
      method: 'POST',
      body: JSON.stringify(bookingData)
    }),

  list: () => request<Booking[]>('/bookings'),

  listParticipating: () => request<Booking[]>('/bookings/participating'),

  delete: (id: number) =>
    request<{ message: string }>(`/bookings/${id}`, {
      method: 'DELETE'
    })
}

export const notifications = {
  list: (limit?: number) => {
    const params = limit ? `?limit=${limit}` : ''
    return request<Notification[]>(`/notifications${params}`)
  },

  getUnreadCount: () => request<{ count: number }>('/notifications/unread-count'),

  markAsRead: (id: number) =>
    request<{ message: string }>(`/notifications/${id}/read`, {
      method: 'POST'
    }),

  connect: async () => {
    const token = localStorage.getItem('auth_token')
    const response = await fetch(`${API_BASE_URL}/notifications/stream`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'text/event-stream'
      }
    })
    return response
  }
}

export const api = {
  auth,
  users,
  bookings,
  notifications
}
