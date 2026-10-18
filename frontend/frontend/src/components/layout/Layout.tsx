import { useState } from 'react'
import { Outlet, useNavigate } from 'react-router-dom'
import { AlertTriangle } from 'lucide-react'
import Sidebar from './Sidebar'
import Navbar from './Navbar'
import { useAuthStore } from '@/store/authStore'

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { isGuest, logout } = useAuthStore()
  const navigate = useNavigate()

  function exitGuest() {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex flex-col flex-1 min-w-0 lg:ml-60">

        {/* Guest mode banner */}
        {isGuest && (
          <div className="bg-amber-400 text-amber-900 px-4 py-2 flex items-center justify-between text-xs font-medium z-20 flex-shrink-0">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-3.5 w-3.5 flex-shrink-0" />
              <span>
                <strong>Demo Mode</strong> — You are browsing as a guest.
                API calls are disabled. Start the backend and sign in to use live data.
              </span>
            </div>
            <button
              onClick={exitGuest}
              className="ml-4 underline hover:no-underline whitespace-nowrap flex-shrink-0"
            >
              Sign in
            </button>
          </div>
        )}

        <Navbar onMenuClick={() => setSidebarOpen(true)} />

        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
