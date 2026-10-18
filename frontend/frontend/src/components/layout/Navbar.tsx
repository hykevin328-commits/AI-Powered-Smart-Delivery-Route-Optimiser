import { Menu, Bell, RefreshCw } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'

interface Props { onMenuClick: () => void }

export default function Navbar({ onMenuClick }: Props) {
  const { user } = useAuthStore()

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center px-4 gap-3 sticky top-0 z-10">
      <button onClick={onMenuClick} className="btn-ghost p-2 lg:hidden">
        <Menu className="h-5 w-5" />
      </button>

      <div className="flex-1" />

      <button className="btn-ghost p-2 rounded-lg relative">
        <Bell className="h-5 w-5 text-gray-500" />
      </button>

      <div className="flex items-center gap-2 pl-2 border-l border-gray-200">
        <div className="h-8 w-8 rounded-full bg-primary-500 flex items-center justify-center text-sm font-bold text-white">
          {user?.full_name?.charAt(0).toUpperCase() ?? 'U'}
        </div>
        <div className="hidden sm:block">
          <p className="text-sm font-medium text-gray-800 leading-none">{user?.full_name}</p>
          <p className="text-xs text-gray-400 capitalize mt-0.5">{user?.role?.replace('_', ' ')}</p>
        </div>
      </div>
    </header>
  )
}
