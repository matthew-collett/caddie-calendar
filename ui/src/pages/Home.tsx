import { useState } from 'react'
import { Nav, BookingForm, BookingsView } from '@/components'

const Home = () => {
  const [currentView, setCurrentView] = useState<'booking' | 'bookings'>(() => {
    const saved = localStorage.getItem('currentView')
    return (saved as 'booking' | 'bookings') || 'booking'
  })

  const handleViewChange = (view: 'booking' | 'bookings') => {
    setCurrentView(view)
    localStorage.setItem('currentView', view)
  }

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <Nav currentView={currentView} onViewChange={handleViewChange} />
      <main className="flex-1 overflow-y-auto">
        {currentView === 'booking' ? (
          <BookingForm />
        ) : (
          <BookingsView onViewChange={handleViewChange} />
        )}
      </main>
    </div>
  )
}

export default Home
