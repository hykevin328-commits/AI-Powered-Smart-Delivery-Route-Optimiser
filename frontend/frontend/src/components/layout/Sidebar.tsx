import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  PackageSearch,
  Users,
  Truck,
  Route,
  BarChart3,
  BrainCircuit,
  Car,
  LogOut,
  X,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/store/authStore'
import { authService } from '@/services/auth.service'

interface Props {
  open: boolean
  onClose: () => void
}

const navItems = [
  { to: '/dashboard',  label: 'Dashboard',      icon: LayoutDashboard },
  { to: '/orders',     label: 'Orders',          icon: PackageSearch },
  { to: '/customers',  label: 'Customers',       icon: Users },
  { to: '/vehicles',   label: 'Vehicles',        icon: Car },
  { to: '/routes',     label: 'Route Optimizer', icon: Route },
  { to: '/analytics',  label: 'Analytics',       icon: BarChart3 },
  { to: '/ai',         label: 'AI Predictions',  icon: BrainCircuit },
]

export default function Sidebar({ open, onClose }: Props) {
  const { user, logout } = useAuthStore()

  async function handleLogout() {
    try { await authService.logout() } catch { /* ignore */ }
    logout()
  }

  const sidebarContent = (
    <div className="flex flex-col h-full bg-sidebar text-white">
      {/* Logo */}
      <div className="flex items-center justify-between px-5 py-5 border-b border-white/10">
        <div className="flex items-center gap-2.5">
          <div className="bg-primary-500 rounded-lg p-1.5">
            <Truck className="h-5 w-5 text-white" />
          </div>
          <span className="font-bold text-sm leading-tight">
            Smart Route<br />
            <span className="text-primary-400 font-semibold text-xs">Optimizer</span>
          </span>
        </div>
        <button onClick={onClose} className="lg:hidden text-white/60 hover:text-white">
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onClose}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary-600 text-white'
                  : 'text-white/70 hover:bg-white/10 hover:text-white',
              )
            }
          >
            <Icon className="h-4 w-4 flex-shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* User footer */}
      <div className="px-3 py-4 border-t border-white/10">
        <div className="flex items-center gap-3 px-3 py-2 mb-2">
          <div className="h-8 w-8 rounded-full bg-primary-500 flex items-center justify-center text-sm font-bold flex-shrink-0">
            {user?.full_name?.charAt(0).toUpperCase() ?? 'U'}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium truncate">{user?.full_name ?? 'User'}</p>
            <p className="text-xs text-white/50 capitalize">{user?.role?.replace('_', ' ')}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm text-white/70 hover:bg-white/10 hover:text-white transition-colors"
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </div>
    </div>
  )

  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Desktop sidebar */}
      <aside className="hidden lg:flex flex-col w-60 flex-shrink-0 fixed inset-y-0 left-0 z-20">
        {sidebarContent}
      </aside>

      {/* Mobile drawer */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-40 w-64 transition-transform duration-200 lg:hidden',
          open ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        {sidebarContent}
      </aside>
    </>
  )
}
