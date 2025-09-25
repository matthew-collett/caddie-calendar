import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format, addMinutes, setHours, setMinutes, addDays } from 'date-fns'
import { CalendarIcon, Clock, Users, MapPin, Loader2 } from 'lucide-react'
import {
  Button,
  Calendar,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  Input,
  Popover,
  PopoverContent,
  PopoverTrigger,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui'

import { useForm } from 'react-hook-form'
import { cn, convertTo24Hour } from '@/lib/utils'
import { api, type Member, type BookingRequest } from '@/lib'
import { useAuth } from '@/context'
import { toast } from 'sonner'

interface BookingFormData {
  date: Date
  time: string
  holes: string
  members: number[]
  guestNames: Record<string, string>
}

const generateTimes = () => {
  const times = []
  let current = setMinutes(setHours(new Date(), 6), 0)
  const end = setMinutes(setHours(new Date(), 19), 0)

  while (current <= end) {
    times.push(format(current, 'h:mm a'))
    current = addMinutes(current, 15)
  }

  return times
}

const availableTimes = generateTimes()

export const BookingForm = () => {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [selectedMembers, setSelectedMembers] = useState<Member[]>([])
  const [memberSearchOpen, setMemberSearchOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('')

  const { data: currentBooker } = useQuery({
    queryKey: ['members', user?.full_name],
    queryFn: () => api.users.searchMembers(user!.full_name),
    enabled: !!user?.full_name,
    staleTime: 10 * 60 * 1000,
    select: data => data[0]
  })

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm)
    }, 500)
    return () => clearTimeout(timer)
  }, [searchTerm])

  const { data: members = [], isLoading } = useQuery({
    queryKey: ['members', debouncedSearchTerm],
    queryFn: () => api.users.searchMembers(debouncedSearchTerm),
    enabled: debouncedSearchTerm.length >= 2,
    staleTime: 5 * 60 * 1000
  })

  const form = useForm<BookingFormData>({
    defaultValues: {
      date: undefined,
      time: '',
      holes: '',
      members: [],
      guestNames: {}
    }
  })

  const createBookingMutation = useMutation({
    mutationFn: api.bookings.create,
    onSuccess: () => {
      toast.success('Booking created successfully!')
      queryClient.invalidateQueries({ queryKey: ['bookings'] })
      form.reset({
        date: undefined,
        time: '',
        holes: '',
        members: [],
        guestNames: {}
      })
      setSelectedMembers([])
    },
    onError: () => {
      toast.error('Failed to create booking. Please try again.')
    }
  })

  const onSubmit = (data: BookingFormData) => {
    const players = []

    if (currentBooker) {
      players.push({
        user_id: currentBooker.id,
        affiliation_id: currentBooker.affiliation_type_id,
        first_name: currentBooker.first_name,
        last_name: currentBooker.last_name,
        handicap: currentBooker.handicap?.value ?? null
      })
    }

    players.push(
      ...selectedMembers.map(member => {
        const isGuest = member.last_name.match(/^Guest \d+$/)
        const guestName = data.guestNames[member.id.toString()]

        return {
          user_id: member.id,
          affiliation_id: member.affiliation_type_id,
          first_name: member.first_name,
          last_name: member.last_name,
          handicap: member.handicap?.value ?? null,
          note: isGuest && guestName ? `Guest: ${guestName}` : null
        }
      })
    )

    const bookingData: BookingRequest = {
      booking_date: format(data.date, 'yyyy-MM-dd'),
      target_time: convertTo24Hour(data.time),
      holes: data.holes === '9 holes' ? 9 : 18,
      players
    }

    createBookingMutation.mutate(bookingData)
  }

  const addMember = (memberId: number) => {
    const member = members.find(m => m.id === memberId)
    if (member && !selectedMembers.find(m => m.id === memberId) && selectedMembers.length < 4) {
      setSelectedMembers([...selectedMembers, member])
    }
    setMemberSearchOpen(false)
  }

  const removeMember = (memberId: number) => {
    setSelectedMembers(selectedMembers.filter(member => member.id !== memberId))
    const currentGuestNames = { ...form.getValues('guestNames') }
    delete currentGuestNames[memberId.toString()]
    form.setValue('guestNames', currentGuestNames)
  }

  return (
    <div className="bg-gradient-to-br from-background to-muted/30 p-4 sm:p-6 min-h-full">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-4 sm:mb-8">
          <h1 className="text-2xl sm:text-4xl font-bold text-foreground mb-2">
            Book Your Tee Time
          </h1>
          <p className="text-muted-foreground text-base sm:text-lg">
            Your booking will be submitted automatically
          </p>
        </div>

        <Card className="bg-gradient-card shadow-elegant border-border/50">
          <CardHeader className="text-center">
            <CardTitle className="flex items-center justify-center gap-2 text-2xl">
              <MapPin className="h-6 w-6 text-primary" />
              Booking Details
            </CardTitle>
            <CardDescription>Choose your date, target time, and group members</CardDescription>
          </CardHeader>

          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                <FormField
                  control={form.control}
                  name="date"
                  rules={{ required: 'Please select a date' }}
                  render={({ field }) => (
                    <FormItem className="flex flex-col">
                      <FormLabel className="text-base font-medium">Date</FormLabel>
                      <Popover>
                        <PopoverTrigger asChild>
                          <FormControl>
                            <Button
                              variant="outline"
                              className={cn(
                                'w-full pl-3 text-left font-normal h-12',
                                !field.value && 'text-muted-foreground'
                              )}
                            >
                              {field.value ? format(field.value, 'PPP') : <span>Pick a date</span>}
                              <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                            </Button>
                          </FormControl>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0" align="start">
                          <Calendar
                            mode="single"
                            selected={field.value}
                            onSelect={field.onChange}
                            disabled={date => date < addDays(new Date(), 4)}
                            className="p-3 pointer-events-auto"
                          />
                        </PopoverContent>
                      </Popover>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="time"
                  rules={{ required: 'Please select a time' }}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-base font-medium">Target Time</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger className="h-12">
                            <div className="flex items-center gap-2">
                              <Clock className="h-4 w-4 text-muted-foreground" />
                              <SelectValue placeholder="Select target time" />
                            </div>
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {availableTimes.map(time => (
                            <SelectItem key={time} value={time}>
                              {time}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="holes"
                  rules={{ required: 'Please select number of holes' }}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-base font-medium">Number of Holes</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger className="h-12">
                            <SelectValue placeholder="Select holes" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="9 holes">9 Holes</SelectItem>
                          <SelectItem value="18 holes">18 Holes</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="space-y-3">
                  <FormLabel className="text-base font-medium">Playing Partners</FormLabel>
                  <div className="space-y-2">
                    {selectedMembers.map(member => {
                      const isGuest = member.last_name.match(/^Guest \d+$/)
                      return (
                        <div key={member.id} className="space-y-2">
                          <div className="flex items-center justify-between p-3 bg-muted/50 rounded-md">
                            <div className="flex items-center gap-2">
                              <Users className="h-4 w-4 text-muted-foreground" />
                              <span className="font-medium">
                                {member.first_name} {member.last_name}
                              </span>
                              <span className="text-sm text-muted-foreground">
                                (Handicap: {member.handicap?.value ?? '--'})
                              </span>
                            </div>
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              onClick={() => removeMember(member.id)}
                              className="text-destructive hover:text-destructive/80"
                            >
                              Remove
                            </Button>
                          </div>
                          {isGuest && (
                            <div className="ml-7 relative">
                              <div className="absolute left-0 top-0 w-4 h-6 border-l-2 border-b-2 border-border rounded-bl-md"></div>
                              <div className="ml-6">
                                <FormField
                                  control={form.control}
                                  name={`guestNames.${member.id}`}
                                  rules={{ required: 'Please specify the name of the guest' }}
                                  render={({ field }) => (
                                    <FormItem>
                                      <FormControl>
                                        <Input
                                          placeholder="Name of Guest"
                                          {...field}
                                          className="h-10"
                                        />
                                      </FormControl>
                                      <FormMessage />
                                    </FormItem>
                                  )}
                                />
                              </div>
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>

                  <Popover open={memberSearchOpen} onOpenChange={setMemberSearchOpen}>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        role="combobox"
                        aria-expanded={memberSearchOpen}
                        className="w-full justify-between h-12"
                        disabled={selectedMembers.length >= 4}
                      >
                        <div className="flex items-center gap-2">
                          <Users className="h-4 w-4 text-muted-foreground" />
                          {selectedMembers.length >= 4
                            ? 'Maximum 4 players selected'
                            : 'Add playing partner...'}
                        </div>
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-full p-0">
                      <Command shouldFilter={false}>
                        <CommandInput
                          placeholder="Search members..."
                          value={searchTerm}
                          onValueChange={setSearchTerm}
                        />
                        <CommandList>
                          <CommandEmpty>
                            {isLoading ||
                            (searchTerm !== debouncedSearchTerm && searchTerm.length >= 2)
                              ? 'Searching...'
                              : 'No members found.'}
                          </CommandEmpty>
                          <CommandGroup>
                            {members
                              .filter(
                                member =>
                                  member.id !== user?.id &&
                                  !selectedMembers.find(s => s.id === member.id)
                              )
                              .map(member => (
                                <CommandItem
                                  key={member.id}
                                  onSelect={() => addMember(member.id)}
                                  className="cursor-pointer"
                                >
                                  <div className="flex items-center justify-between w-full gap-2">
                                    <span className="flex-1 truncate">
                                      {member.first_name} {member.last_name}
                                    </span>
                                    <span className="text-sm text-muted-foreground flex-shrink-0">
                                      HC: {member.handicap?.value ?? '--'}
                                    </span>
                                  </div>
                                </CommandItem>
                              ))}
                          </CommandGroup>
                        </CommandList>
                      </Command>
                    </PopoverContent>
                  </Popover>
                  <p className="text-sm text-muted-foreground">
                    Selected: {selectedMembers.length}/4 players
                  </p>
                </div>

                <Button
                  type="submit"
                  className="w-full h-12 bg-primary hover:bg-primary/90 text-primary-foreground transition-all duration-300 shadow-soft"
                  disabled={createBookingMutation.isPending}
                >
                  {createBookingMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    'Submit'
                  )}
                </Button>
              </form>
            </Form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
