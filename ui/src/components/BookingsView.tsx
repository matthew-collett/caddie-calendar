import { useState } from 'react'
import { isFuture, isPast, parseISO } from 'date-fns'
import { useAuth } from '@/context'
import {
  Calendar,
  Clock,
  Users,
  MapPin,
  Filter,
  Crown,
  User,
  Trash2,
  MoreHorizontal,
  Loader2
} from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, type Booking } from '@/lib'

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Badge,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Button,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Popover,
  PopoverContent,
  PopoverTrigger
} from '@/components/ui'
import { formatDate, formatDateTime, formatOptionalTime, formatTime } from '@/lib/utils'
import { toast } from 'sonner'

interface BookingsViewProps {
  onViewChange: (view: 'booking' | 'bookings') => void
}

export const BookingsView = ({ onViewChange }: BookingsViewProps) => {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<'all' | 'PENDING' | 'COMPLETE' | 'FAILED'>('all')

  const {
    data: bookings = [],
    isLoading,
    error
  } = useQuery({
    queryKey: ['bookings'],
    queryFn: api.bookings.list,
    staleTime: 2 * 60 * 1000
  })

  const deleteBookingMutation = useMutation({
    mutationFn: api.bookings.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings'] })
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      toast.success('Booking deleted successfully')
    },
    onError: () => {
      toast.error('Failed to delete booking. Please try again.')
    }
  })

  if (isLoading) {
    return (
      <div className="bg-gradient-to-br from-background to-muted/30 p-4 sm:p-6 min-h-full flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-gradient-to-br from-background to-muted/30 p-4 sm:p-6 min-h-full">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-4">
            <h1 className="text-2xl sm:text-4xl font-bold text-foreground mb-2">Your Bookings</h1>
            <p className="text-base sm:text-lg text-destructive">
              Error loading bookings. Please try again.
            </p>
          </div>
        </div>
      </div>
    )
  }
  const filterByStatus = (bookings: Booking[]) => {
    if (statusFilter === 'all') return bookings
    return bookings.filter(booking => booking.status === statusFilter)
  }

  const futureBookings = filterByStatus(
    bookings.filter(booking => isFuture(parseISO(booking.booking_date)))
  )

  const pastBookings = filterByStatus(
    bookings.filter(booking => isPast(parseISO(booking.booking_date)))
  )

  const BookingCard = ({ booking }: { booking: Booking }) => {
    const [infoOpen, setInfoOpen] = useState(false)

    return (
      <Card className="bg-gradient-card shadow-soft border-border/50 hover:shadow-elegant transition-all duration-300">
        <CardHeader className="pb-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <Calendar className="h-5 w-5 text-primary" />
              {formatDate(booking.booking_date)}
            </CardTitle>
            <div className="flex items-center gap-2 flex-wrap">
              <Badge
                variant={booking.role === 'host' ? 'default' : 'secondary'}
                className={
                  booking.role === 'host'
                    ? 'bg-blue-600 text-white'
                    : 'bg-muted text-muted-foreground'
                }
              >
                {booking.role === 'host' ? (
                  <>
                    <Crown className="h-3 w-3" />
                    Host
                  </>
                ) : (
                  <>
                    <User className="h-3 w-3" />
                    Guest
                  </>
                )}
              </Badge>
              <Badge
                variant="default"
                className={
                  booking.status === 'COMPLETE'
                    ? 'bg-primary text-primary-foreground'
                    : booking.status === 'PENDING'
                    ? 'bg-yellow-600 text-white'
                    : 'bg-destructive text-white'
                }
              >
                {booking.status}
              </Badge>
            </div>
          </div>
          <CardDescription className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 text-sm">
            <span className="flex items-center gap-1">
              <Clock className="h-4 w-4" />
              Target: {formatTime(booking.target_time)}
            </span>
            <span className="flex items-center gap-1 text-muted-foreground">
              <Clock className="h-4 w-4" />
              Actual: {formatOptionalTime(booking.actual_time)}
            </span>
            <span className="flex items-center gap-1">
              <MapPin className="h-4 w-4" />
              {booking.holes} holes
            </span>
          </CardDescription>
        </CardHeader>

        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium text-sm">Playing Partners:</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {booking.players
                .filter(player => player.user_id !== user?.id)
                .map(player => (
                  <div
                    key={player.user_id}
                    className="flex items-center justify-between p-2 bg-muted/30 rounded-md"
                  >
                    <span className="text-sm font-medium">
                      {player.first_name} {player.last_name}
                      {player.note?.startsWith('Guest: ') &&
                        ` (${player.note.replace('Guest: ', '')})`}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      HC: {player.handicap ?? '--'}
                    </span>
                  </div>
                ))}
            </div>

            {booking.players.filter(player => player.user_id !== user?.id).length === 0 && (
              <p className="text-sm text-muted-foreground italic">Playing solo</p>
            )}

            <div className="pt-4 border-t border-border/50">
              {booking.error_details && (
                <div className="mb-3">
                  <span className="text-sm font-medium text-destructive">Error Details:</span>{' '}
                  <span className="text-sm text-muted-foreground break-words">
                    {booking.error_details}
                  </span>
                </div>
              )}
              <div className="flex items-center justify-end gap-2">
                <Popover open={infoOpen} onOpenChange={setInfoOpen}>
                  <PopoverTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-fit p-3" align="end">
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">
                        Created: {formatDateTime(booking.created_at)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Updated: {formatDateTime(booking.updated_at)}
                      </p>
                    </div>
                  </PopoverContent>
                </Popover>
                {booking.role === 'host' && isFuture(parseISO(booking.booking_date)) && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteBookingMutation.mutate(booking.id)}
                    disabled={deleteBookingMutation.isPending}
                    className="text-destructive hover:text-destructive/80 h-8 w-8 p-0"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="bg-gradient-to-br from-background to-muted/30 p-4 sm:p-6 min-h-full">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-4">
          <h1 className="text-2xl sm:text-4xl font-bold text-foreground mb-2">Your Bookings</h1>
          <p className="text-muted-foreground text-base sm:text-lg">
            View your past and upcoming bookings
          </p>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-0 mb-4">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium text-muted-foreground">Filter by status</span>
          </div>
          <Select
            value={statusFilter}
            onValueChange={value => setStatusFilter(value as typeof statusFilter)}
          >
            <SelectTrigger className="w-full sm:w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="PENDING">Pending</SelectItem>
              <SelectItem value="COMPLETE">Complete</SelectItem>
              <SelectItem value="FAILED">Failed</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Tabs defaultValue="upcoming" className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-4">
            <TabsTrigger value="past" className="flex items-center gap-2">
              <Filter className="h-4 w-4" />
              Past ({pastBookings.length})
            </TabsTrigger>
            <TabsTrigger value="upcoming" className="flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Upcoming ({futureBookings.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="past" className="space-y-4">
            {pastBookings.length > 0 ? (
              <div className="grid gap-4">
                {pastBookings
                  .sort(
                    (a, b) =>
                      parseISO(b.booking_date).getTime() - parseISO(a.booking_date).getTime()
                  )
                  .map(booking => (
                    <BookingCard key={booking.id} booking={booking} />
                  ))}
              </div>
            ) : (
              <Card className="bg-gradient-card shadow-soft border-border/50">
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Filter className="h-12 w-12 text-primary mb-4" />
                  <h3 className="text-lg font-semibold mb-2">
                    {statusFilter === 'all'
                      ? 'No past bookings'
                      : `No past ${statusFilter.toLowerCase()} bookings`}
                  </h3>
                  <p className="text-muted-foreground text-center">
                    {statusFilter === 'all'
                      ? 'Your booking history will appear here.'
                      : `No past bookings with ${statusFilter.toLowerCase()} status found.`}
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="upcoming" className="space-y-4">
            {futureBookings.length > 0 ? (
              <div className="grid gap-4">
                {futureBookings
                  .sort(
                    (a, b) =>
                      parseISO(b.booking_date).getTime() - parseISO(a.booking_date).getTime()
                  )
                  .map(booking => (
                    <BookingCard key={booking.id} booking={booking} />
                  ))}
              </div>
            ) : (
              <Card className="bg-gradient-card shadow-soft border-border/50">
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Calendar className="h-12 w-12 text-primary mb-4" />
                  <h3 className="text-lg font-semibold mb-2">
                    {statusFilter === 'all'
                      ? 'No upcoming bookings'
                      : `No upcoming ${statusFilter.toLowerCase()} bookings`}
                  </h3>
                  <p className="text-muted-foreground text-center mb-4">
                    {statusFilter === 'all'
                      ? "You haven't made any bookings yet."
                      : `No upcoming bookings with ${statusFilter.toLowerCase()} status found.`}
                  </p>
                  {statusFilter === 'all' && (
                    <Button
                      className="bg-primary hover:bg-primary/90 text-primary-foreground transition-all duration-300"
                      onClick={() => onViewChange('booking')}
                    >
                      Book a Tee Time
                    </Button>
                  )}
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
