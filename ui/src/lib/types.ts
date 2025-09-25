export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  token: string
  expires_in: number
}

export interface AuthStatus {
  auth: boolean
}

export interface User {
  id: number
  full_name: string
  email: string
}

export interface Member {
  id: number
  first_name: string
  last_name: string
  affiliation_type_id: number
  club_id: number
  handicap: { value: number } | null
  current_affiliation: unknown
  phone: string
}

export interface BookingRequest {
  booking_date: string
  target_time: string
  holes: number
  players: Array<{
    user_id: number
    affiliation_id: number
    first_name: string
    last_name: string
    handicap: number | null
  }>
}

export interface Booking {
  id: number
  user_id: number
  booking_date: string
  target_time: string
  holes: number
  players: Array<{
    user_id: number
    affiliation_id: number
    first_name: string
    last_name: string
    handicap: number | null
    note?: string
  }>
  status: 'PENDING' | 'FAILED' | 'COMPLETE'
  booking_id: string | null
  actual_time: string | null
  error_details: string | null
  created_at: string
  updated_at: string
  role: 'host' | 'guest'
}

export interface Notification {
  id: number
  user_id: number
  booking_id: number
  type: 'BOOKING_SUCCESS' | 'BOOKING_FAILED'
  title: string
  message: string
  is_read: boolean
  created_at: string
}
