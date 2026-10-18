import { clsx, type ClassValue } from 'clsx'
import { format, formatDistanceToNow, parseISO } from 'date-fns'
import type { OrderPriority, OrderStatus, VehicleStatus } from '@/types'

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

// ── Dates ─────────────────────────────────────────────────────────────────────
export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  try { return format(parseISO(iso), 'dd MMM yyyy') } catch { return iso }
}

export function fmtDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  try { return format(parseISO(iso), 'dd MMM yyyy, HH:mm') } catch { return iso }
}

export function timeAgo(iso: string | null | undefined): string {
  if (!iso) return '—'
  try { return formatDistanceToNow(parseISO(iso), { addSuffix: true }) } catch { return iso }
}

// ── Numbers ───────────────────────────────────────────────────────────────────
export function fmtNum(n: number | null | undefined, decimals = 1): string {
  if (n == null) return '—'
  return n.toLocaleString('en-IN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

// ── Status badge class mapping ─────────────────────────────────────────────────
export function orderStatusClass(status: OrderStatus): string {
  const map: Record<OrderStatus, string> = {
    pending:    'badge-yellow',
    assigned:   'badge-blue',
    picked_up:  'badge-purple',
    in_transit: 'badge-orange',
    delivered:  'badge-green',
    failed:     'badge-red',
    cancelled:  'badge-gray',
  }
  return map[status] ?? 'badge-gray'
}

export function priorityClass(p: OrderPriority): string {
  const map: Record<OrderPriority, string> = {
    low:    'badge-gray',
    normal: 'badge-blue',
    high:   'badge-orange',
    urgent: 'badge-red',
  }
  return map[p] ?? 'badge-gray'
}

export function vehicleStatusClass(s: VehicleStatus): string {
  const map: Record<VehicleStatus, string> = {
    available:   'badge-green',
    in_use:      'badge-blue',
    maintenance: 'badge-yellow',
    retired:     'badge-gray',
  }
  return map[s] ?? 'badge-gray'
}

export function congestionClass(level: string): string {
  const map: Record<string, string> = {
    low:    'badge-green',
    medium: 'badge-yellow',
    high:   'badge-orange',
    severe: 'badge-red',
  }
  return map[level.toLowerCase()] ?? 'badge-gray'
}

// ── Misc ──────────────────────────────────────────────────────────────────────
export function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1).replace(/_/g, ' ')
}

export function truncate(s: string, n = 40): string {
  return s.length > n ? s.slice(0, n) + '…' : s
}
