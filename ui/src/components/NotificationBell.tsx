import { useState } from 'react'
import { Bell, Check, CheckCircle, XCircle } from 'lucide-react'
import { Button, Popover, PopoverContent, PopoverTrigger, Badge } from '@/components/ui'
import { api } from '@/lib/api'
import { type Notification } from '@/lib/types'
import { useIsMobile, useNotifications } from '@/hooks'
import { formatDistanceToNow } from 'date-fns'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'

const NOTIFICATION_QUERIES = {
  list: ['notifications'] as const,
  unreadCount: ['notifications', 'unread-count'] as const
}

const NOTIFICATION_CONFIG = {
  success: { icon: CheckCircle, className: 'text-primary' },
  failed: { icon: XCircle, className: 'text-destructive' }
} as const

export const NotificationBell = () => {
  const isMobile = useIsMobile()
  const [isOpen, setIsOpen] = useState(false)
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const queryClient = useQueryClient()

  useNotifications()

  const { data: notifications = [] } = useQuery({
    queryKey: NOTIFICATION_QUERIES.list,
    queryFn: () => api.notifications.list(10)
  })

  const { data: unreadCountData } = useQuery({
    queryKey: NOTIFICATION_QUERIES.unreadCount,
    queryFn: () => api.notifications.getUnreadCount()
  })

  const unreadCount = unreadCountData?.count ?? 0

  const markAsReadMutation = useMutation({
    mutationFn: api.notifications.markAsRead,
    onMutate: async notificationId => {
      await queryClient.cancelQueries({ queryKey: NOTIFICATION_QUERIES.list })
      await queryClient.cancelQueries({ queryKey: NOTIFICATION_QUERIES.unreadCount })

      const previousNotifications = queryClient.getQueryData<Notification[]>(
        NOTIFICATION_QUERIES.list
      )
      const previousCount = queryClient.getQueryData<{ count: number }>(
        NOTIFICATION_QUERIES.unreadCount
      )

      queryClient.setQueryData<Notification[]>(NOTIFICATION_QUERIES.list, (old = []) =>
        old.map(n => (n.id === notificationId ? { ...n, is_read: true } : n))
      )

      queryClient.setQueryData<{ count: number }>(
        NOTIFICATION_QUERIES.unreadCount,
        (old = { count: 0 }) => ({
          count: Math.max(0, old.count - 1)
        })
      )

      return { previousNotifications, previousCount }
    },
    onError: (_, __, context) => {
      if (context?.previousNotifications) {
        queryClient.setQueryData(NOTIFICATION_QUERIES.list, context.previousNotifications)
      }
      if (context?.previousCount) {
        queryClient.setQueryData(NOTIFICATION_QUERIES.unreadCount, context.previousCount)
      }
    }
  })

  const getNotificationConfig = (type: Notification['type']) => {
    const typeKey = type === 'BOOKING_SUCCESS' ? 'success' : 'failed'
    return NOTIFICATION_CONFIG[typeKey]
  }

  const handleMarkAsRead = (notificationId: number) => {
    if (notifications.find(n => n.id === notificationId)?.is_read) return
    markAsReadMutation.mutate(notificationId)
  }

  const NotificationItem = ({ notification }: { notification: Notification }) => {
    const config = getNotificationConfig(notification.type)
    const IconComponent = config.icon

    return (
      <div
        className={`p-3 border-b border-border/30 last:border-b-0 cursor-pointer hover:bg-muted/50 transition-colors ${
          !notification.is_read
            ? `bg-muted/30 border-l-2 ${
                notification.type === 'BOOKING_SUCCESS'
                  ? 'border-l-primary'
                  : 'border-l-destructive'
              }`
            : expandedId === notification.id
            ? 'bg-background'
            : 'bg-background opacity-40'
        }`}
        onClick={() => {
          if (!notification.is_read) handleMarkAsRead(notification.id)
          setExpandedId(expandedId === notification.id ? null : notification.id)
        }}
      >
        <div className="flex items-start gap-2">
          <IconComponent className={`h-4 w-4 mt-0.5 flex-shrink-0 ${config.className}`} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h4 className={`font-medium text-sm ${config.className}`}>{notification.title}</h4>
            </div>
            {expandedId === notification.id ? (
              <p className="text-xs text-foreground">{notification.message}</p>
            ) : (
              <p className="text-xs text-foreground">Click to view details</p>
            )}
            <p className="text-xs text-muted-foreground mt-1">
              {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
            </p>
          </div>
          {!notification.is_read && (
            <Button
              variant="ghost"
              size="sm"
              onClick={e => {
                e.stopPropagation()
                handleMarkAsRead(notification.id)
              }}
              className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <Check className="h-3 w-3" />
            </Button>
          )}
        </div>
      </div>
    )
  }

  return (
    <Popover
      open={isOpen}
      onOpenChange={open => {
        setIsOpen(open)
        if (!open) setExpandedId(null)
      }}
    >
      <PopoverTrigger asChild>
        <Button variant="ghost" size={isMobile ? 'sm' : 'default'} className="relative">
          <Bell className="h-4 w-4" />
          {unreadCount > 0 && (
            <Badge
              variant="destructive"
              className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 text-xs flex items-center justify-center"
            >
              {unreadCount > 99 ? '99+' : unreadCount}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-64 p-0" align="end">
        <div className="max-h-96 overflow-y-auto">
          {notifications.length === 0 ? (
            <div className="p-4 text-center text-muted-foreground text-sm">
              No notifications yet
            </div>
          ) : (
            notifications.map(notification => (
              <NotificationItem key={notification.id} notification={notification} />
            ))
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
}
