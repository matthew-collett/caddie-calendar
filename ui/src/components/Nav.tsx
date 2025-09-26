import { useState } from 'react'
import { CalendarPlus, Calendar, CalendarCheck, LogOut, User, Moon, Sun } from 'lucide-react'
import { Button, Popover, PopoverContent, PopoverTrigger } from '@/components/ui'
import { useAuth, useTheme } from '@/context'
import { useIsMobile } from '@/hooks'
import { NotificationBell } from './NotificationBell'

interface NavigationProps {
  currentView: 'booking' | 'bookings'
  onViewChange: (view: 'booking' | 'bookings') => void
}

export const Nav = ({ currentView, onViewChange }: NavigationProps) => {
  const isMobile = useIsMobile()
  const { user, logout, isLoggingOut } = useAuth()
  const { theme, setTheme } = useTheme()
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <nav className="flex-shrink-0 bg-background/95 backdrop-blur-sm border-b border-border/50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
        <div className="flex items-center justify-between min-h-[48px] sm:min-h-[56px]">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 sm:w-8 sm:h-8 bg-primary rounded-full flex items-center justify-center">
              <CalendarCheck className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-white" />
            </div>
            <span className="text-lg sm:text-xl font-bold text-foreground">Caddie Calendar</span>
          </div>

          <div className="flex items-center gap-1 sm:gap-2">
            <Button
              variant={currentView === 'booking' ? 'default' : 'ghost'}
              onClick={() => onViewChange('booking')}
              className={currentView === 'booking' ? 'bg-primary hover:bg-primary/90' : ''}
              size={isMobile ? 'sm' : 'default'}
            >
              <CalendarPlus className="h-4 w-4" />
              {isMobile ? '' : 'Book Time'}
            </Button>

            <Button
              variant={currentView === 'bookings' ? 'default' : 'ghost'}
              onClick={() => onViewChange('bookings')}
              className={currentView === 'bookings' ? 'bg-primary hover:bg-primary/90' : ''}
              size={isMobile ? 'sm' : 'default'}
            >
              <Calendar className="h-4 w-4" />
              {isMobile ? '' : 'My Bookings'}
            </Button>

            <NotificationBell />

            <Popover open={menuOpen} onOpenChange={setMenuOpen}>
              <PopoverTrigger asChild>
                <Button variant="ghost" size={isMobile ? 'sm' : 'default'}>
                  <User className="h-4 w-4" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-40 p-2" align="end">
                <div className="space-y-1">
                  <div className="p-2 font-semibold text-sm text-muted-foreground border-b border-border/50 mb-1">
                    Hi {user?.full_name?.split(' ')[0] || user?.email}!
                  </div>
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setTheme(theme === 'dark' ? 'light' : 'dark')
                    }}
                    className="w-full justify-start text-muted-foreground hover:text-foreground"
                    size="sm"
                  >
                    {theme === 'dark' ? (
                      <>
                        <Sun className="h-4 w-4" />
                        Light mode
                      </>
                    ) : (
                      <>
                        <Moon className="h-4 w-4" />
                        Dark mode
                      </>
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => {
                      logout()
                      setMenuOpen(false)
                    }}
                    disabled={isLoggingOut}
                    className="w-full justify-start text-muted-foreground hover:text-foreground"
                    size="sm"
                  >
                    <LogOut className="h-4 w-4" />
                    {isLoggingOut ? 'Logging out...' : 'Log out'}
                  </Button>
                </div>
              </PopoverContent>
            </Popover>
          </div>
        </div>
      </div>
    </nav>
  )
}
