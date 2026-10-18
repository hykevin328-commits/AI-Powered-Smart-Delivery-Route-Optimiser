import { useQuery } from '@tanstack/react-query'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Legend,
} from 'recharts'
import { Package, CheckCircle, Fuel, Leaf, Route, Clock, TrendingUp, Users } from 'lucide-react'
import { subDays, format, subDays as sub } from 'date-fns'
import { analyticsService } from '@/services/analytics.service'
import StatsCard from '@/components/ui/StatsCard'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { fmtNum, fmtDate } from '@/lib/utils'
import { useAuthStore } from '@/store/authStore'
import type { DashboardData } from '@/types'

const today = format(new Date(), 'yyyy-MM-dd')
const start = format(subDays(new Date(), 29), 'yyyy-MM-dd')

// ── Mock data for guest / offline mode ────────────────────────────────────────
function buildMockTimeSeries() {
  return Array.from({ length: 30 }, (_, i) => {
    const d = format(sub(new Date(), 29 - i), 'yyyy-MM-dd')
    const total = Math.floor(Math.random() * 20) + 8
    const completed = Math.floor(total * (0.75 + Math.random() * 0.2))
    return {
      date: d,
      total_deliveries: total,
      completed_deliveries: completed,
      total_distance_km: +(total * (4 + Math.random() * 3)).toFixed(1),
      fuel_consumed_litres: +(total * 0.8 + Math.random() * 2).toFixed(2),
      fuel_saved_litres: +(total * 0.2 + Math.random()).toFixed(2),
      co2_emitted_kg: +(total * 1.8 + Math.random() * 2).toFixed(2),
      co2_saved_kg: +(total * 0.4 + Math.random()).toFixed(2),
      avg_delivery_time_minutes: +(28 + Math.random() * 12).toFixed(1),
      route_efficiency_pct: +(18 + Math.random() * 15).toFixed(1),
    }
  })
}

const MOCK_DATA: DashboardData = (() => {
  const ts = buildMockTimeSeries()
  const totalDel = ts.reduce((s, r) => s + r.total_deliveries, 0)
  const completedDel = ts.reduce((s, r) => s + r.completed_deliveries, 0)
  return {
    kpi: {
      total_deliveries: totalDel,
      completed_deliveries: completedDel,
      failed_deliveries: Math.floor(totalDel * 0.04),
      completion_rate_pct: +((completedDel / totalDel) * 100).toFixed(1),
      total_distance_km: +ts.reduce((s, r) => s + r.total_distance_km, 0).toFixed(1),
      total_fuel_consumed_litres: +ts.reduce((s, r) => s + r.fuel_consumed_litres, 0).toFixed(2),
      total_fuel_saved_litres: +ts.reduce((s, r) => s + r.fuel_saved_litres, 0).toFixed(2),
      total_co2_emitted_kg: +ts.reduce((s, r) => s + r.co2_emitted_kg, 0).toFixed(2),
      total_co2_saved_kg: +ts.reduce((s, r) => s + r.co2_saved_kg, 0).toFixed(2),
      avg_delivery_time_minutes: 34.5,
      avg_route_efficiency_pct: 24.3,
      routes_optimised: Math.floor(totalDel / 5),
    },
    time_series: ts,
    partner_performance: [
      { delivery_partner_id: '1', partner_name: 'Ravi Kumar',   total_deliveries: 142, completed_deliveries: 131, completion_rate_pct: 92.3, total_distance_km: 684, avg_delivery_time_minutes: 31, fuel_consumed_litres: 58.1, co2_emitted_kg: 134.3 },
      { delivery_partner_id: '2', partner_name: 'Priya Singh',  total_deliveries: 128, completed_deliveries: 114, completion_rate_pct: 89.1, total_distance_km: 612, avg_delivery_time_minutes: 35, fuel_consumed_litres: 52.0, co2_emitted_kg: 120.1 },
      { delivery_partner_id: '3', partner_name: 'Amit Sharma',  total_deliveries: 115, completed_deliveries:  98, completion_rate_pct: 85.2, total_distance_km: 549, avg_delivery_time_minutes: 38, fuel_consumed_litres: 46.7, co2_emitted_kg: 107.8 },
    ],
  }
})()

export default function DashboardPage() {
  const { isGuest } = useAuthStore()

  const { data, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => analyticsService.getDashboard({ start_date: start, end_date: today }),
    staleTime: 2 * 60 * 1000,
    // In guest mode, always return mock data without hitting the network
    enabled: !isGuest,
  })

  // Use mock data for guest, real data otherwise
  const display: DashboardData = isGuest ? MOCK_DATA : (data ?? MOCK_DATA)

  if (!isGuest && isLoading)
    return <div className="flex justify-center py-20"><LoadingSpinner size="lg" text="Loading dashboard…" /></div>

  const kpi = display.kpi
  const ts  = display.time_series ?? []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500">
          {isGuest ? 'Demo data — connect backend for live metrics' : 'Last 30 days overview'}
        </p>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard title="Total Deliveries"  value={kpi.total_deliveries}                             icon={<Package     className="h-5 w-5 text-primary-600" />} iconBg="bg-primary-100" subtitle={`${kpi.completed_deliveries} completed`} />
        <StatsCard title="Completion Rate"   value={`${fmtNum(kpi.completion_rate_pct)}%`}            icon={<CheckCircle className="h-5 w-5 text-green-600"   />} iconBg="bg-green-100"   subtitle="Delivered vs total" />
        <StatsCard title="Fuel Saved"        value={`${fmtNum(kpi.total_fuel_saved_litres)} L`}       icon={<Fuel        className="h-5 w-5 text-orange-600"  />} iconBg="bg-orange-100"  subtitle="vs unoptimised routes" />
        <StatsCard title="CO₂ Saved"         value={`${fmtNum(kpi.total_co2_saved_kg)} kg`}           icon={<Leaf        className="h-5 w-5 text-emerald-600" />} iconBg="bg-emerald-100" subtitle="Carbon reduction" />
        <StatsCard title="Distance Covered"  value={`${fmtNum(kpi.total_distance_km)} km`}            icon={<Route       className="h-5 w-5 text-blue-600"    />} iconBg="bg-blue-100" />
        <StatsCard title="Avg Delivery Time" value={`${fmtNum(kpi.avg_delivery_time_minutes)} min`}   icon={<Clock       className="h-5 w-5 text-purple-600"  />} iconBg="bg-purple-100" />
        <StatsCard title="Route Efficiency"  value={`${fmtNum(kpi.avg_route_efficiency_pct)}%`}       icon={<TrendingUp  className="h-5 w-5 text-indigo-600"  />} iconBg="bg-indigo-100" />
        <StatsCard title="Routes Optimised"  value={kpi.routes_optimised}                             icon={<Users       className="h-5 w-5 text-pink-600"    />} iconBg="bg-pink-100" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="card card-body">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Deliveries Trend</h2>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={ts} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="totalGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#3b82f6" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="completedGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#22c55e" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={d => format(new Date(d), 'dd MMM')} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip labelFormatter={l => fmtDate(l as string)} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Area type="monotone" dataKey="total_deliveries"     name="Total"     stroke="#3b82f6" fill="url(#totalGrad)"     strokeWidth={2} dot={false} />
              <Area type="monotone" dataKey="completed_deliveries" name="Completed" stroke="#22c55e" fill="url(#completedGrad)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="card card-body">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Fuel Consumed vs Saved (L)</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={ts.slice(-14)} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={d => format(new Date(d), 'dd')} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip labelFormatter={l => fmtDate(l as string)} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="fuel_consumed_litres" name="Consumed" fill="#f97316" radius={[3, 3, 0, 0]} />
              <Bar dataKey="fuel_saved_litres"    name="Saved"    fill="#22c55e" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Partner performance */}
      {display.partner_performance && display.partner_performance.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2 className="text-sm font-semibold text-gray-700">Partner Performance</h2>
          </div>
          <div className="table-container border-0 rounded-none rounded-b-xl">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Partner</th><th>Deliveries</th><th>Completion</th>
                  <th>Distance</th><th>Avg Time</th><th>Fuel (L)</th><th>CO₂ (kg)</th>
                </tr>
              </thead>
              <tbody>
                {display.partner_performance.map(p => (
                  <tr key={p.delivery_partner_id}>
                    <td className="font-medium">{p.partner_name}</td>
                    <td>{p.total_deliveries}</td>
                    <td><span className={p.completion_rate_pct >= 80 ? 'badge badge-green' : 'badge badge-yellow'}>{fmtNum(p.completion_rate_pct)}%</span></td>
                    <td>{fmtNum(p.total_distance_km)} km</td>
                    <td>{p.avg_delivery_time_minutes ? `${fmtNum(p.avg_delivery_time_minutes)} min` : '—'}</td>
                    <td>{fmtNum(p.fuel_consumed_litres)}</td>
                    <td>{fmtNum(p.co2_emitted_kg)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
