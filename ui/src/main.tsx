import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { TooltipProvider, Toaster } from '@/components/ui'
import { ThemeProvider, AuthProvider } from '@/context'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/lib'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ProtectedRoute } from '@/components'
import Home from '@/pages/Home'
import Login from '@/pages/Login'
import NotFound from '@/pages/NotFound'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider defaultTheme="dark" storageKey="ui-theme">
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <TooltipProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="*" element={<NotFound />} />
                <Route element={<ProtectedRoute />}>
                  <Route path="/" element={<Home />} />
                </Route>
              </Routes>
            </BrowserRouter>
            <Toaster 
              position="top-center"
              richColors
              expand
            />
          </TooltipProvider>
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>
  </StrictMode>
)
