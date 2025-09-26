import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { type Notification } from '@/lib/types'

const NOTIFICATION_QUERIES = {
  list: ['notifications'] as const,
  unreadCount: ['notifications', 'unread-count'] as const
}

export const useNotifications = () => {
  const queryClient = useQueryClient()

  useEffect(() => {
    const connectSSE = async () => {
      try {
        const response = await api.notifications.connect()

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const reader = response.body!.getReader()
        const decoder = new TextDecoder()

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim()
              if (data) {
                const parsedData = JSON.parse(data)

                if (parsedData.type === 'notification') {
                  const notification = parsedData.data as Notification

                  queryClient.setQueryData<Notification[]>(
                    NOTIFICATION_QUERIES.list,
                    (old = []) => [notification, ...old]
                  )

                  if (!notification.is_read) {
                    queryClient.setQueryData<{ count: number }>(
                      NOTIFICATION_QUERIES.unreadCount,
                      (old = { count: 0 }) => ({ count: old.count + 1 })
                    )
                  }

                  queryClient.invalidateQueries({ queryKey: ['bookings'] })
                }
              }
            }
          }
        }
      } catch {
        setTimeout(connectSSE, 5000)
      }
    }

    connectSSE()
  }, [queryClient])
}
