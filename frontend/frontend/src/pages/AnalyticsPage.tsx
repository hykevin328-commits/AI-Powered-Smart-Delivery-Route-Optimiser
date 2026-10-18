import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, BarChart, Bar, Legend,
} from 'recharts'
import { format, subDays } from 'date-fns'
import { analyticsService } from '@/services/analytics.service'
import StatsCard from '@/components/ui/StatsCard'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { fmtNum, fmtDate } from '@/lib/utils'
import { TrendingUp, Fuel, Leaf, Route, Clock, CheckCircle, Users } from 'lucide-react'

type Period = 'daily' | 'weekly' | 'monthly'

export default function AnalyticsPage() {
  const [period, setPeriod] = useState<Period>('daily')
  const [days,   setDays]   = useState(30)

  const start = format(subDays(new Date(), days - 1), 'yyyy-MM-dd')
  const end   = format(new Date(), 'yyyy-MM-dd')

  const { data, isLoading } = useQuery({
    queryKey: ['dashboard-analytics', start, end, period],
    queryFn: () => analyticsService.getDashboard({ start_date: start, end_date: end, period_type: period }),
    staleTime: 60_000,
  })

  if (isLoading) return <div className="flex justify-center py-20"><LoadingSpinner size="lg" text="Loading analytics…" /></div>

  const kpi = data?.kpi
  const ts  = data?.time_series ?? []
  const pp  = data?.partner_performance ?? []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Analytics</h1>
          <p className="text-sm text-gray-500">Performance metrics and trends</p>
        </div>
        <div className="flex gap-2">
          {([7, 30, 90] as const).map(d => (
            <button key={d} onClick={() => setDays(d)}
              className={`btn-sm ${days === d ? 'btn-primary' : 'btn-secondary'}`}>
              {d}d
            </button>
          ))}
          <select className="input w-auto text-sm" value={period} onChange={e => setPeriod(e.target.value as Period)}>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
        </div>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard title="Completion Rate"   value={`${fmtNum(kpi?.completion_rate_pct)}%`}       icon={<CheckCircle className="h-5 w-5 text-green-600" />}   iconBg="bg-green-100" />
        <StatsCard title="Distance Covered"  value={`${fmtNum(kpi?.total_distance_km)} km`}         icon={<Route className="h-5 w-5 text-blue-600" />}           iconBg="bg-blue-100" />
        <StatsCard title="Fuel Saved"        value={`${fmtNum(kpi?.total_fuel_saved_litres)} L`}    icon={<Fuel className="h-5 w-5 text-orange-600" />}          iconBg="bg-orange-100" />
        <StatsCard title="CO₂ Saved"         value={`${fmtNum(kpi?.total_co2_saved_kg)} kg`}        icon={<Leaf className="h-5 w-5 text-emerald-600" />}         iconBg="bg-emerald-100" />
        <StatsCard title="Avg Delivery Time" value={`${fmtNum(kpi?.avg_delivery_time_minutes)} min`} icon={<Clock className="h-5 w-5 text-purple-600" />}         iconBg="bg-purple-100" />
        <StatsCard title="Route Efficiency"  value={`${fmtNum(kpi?.avg_route_efficiency_pct)}%`}    icon={<TrendingUp className="h-5 w-5 text-indigo-600" />}    iconBg="bg-indigo-100" />
        <StatsCard title="Routes Optimised"  value={kpi?.routes_optimised ?? 0}                     icon={<Route className="h-5 w-5 text-pink-600" />}           iconBg="bg-pink-100" />
        <StatsCard title="Total Deliveries"  value={kpi?.total_deliveries ?? 0}                     icon={<Users className="h-5 w-5 text-gray-600" />}           iconBg="bg-gray-100" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Completion rate */}
        <div className="card card-body">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Delivery Completion Trend</h2>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={ts} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={d => format(new Date(d), 'dd MMM')} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip labelFormatter={l => fmtDate(l as string)} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line type="monotone" dataKey="total_deliveries"     name="Total"     stroke="#3b82f6" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="completed_deliveries" name="Completed" stroke="#22c55e" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Distance */}
        <div className="card card-body">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Distance Covered (km)</h2>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={ts} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="distGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={d => format(new Date(d), 'dd MMM')} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip labelFormatter={l => fmtDate(l as string)} />
              <Area type="monotone" dataKey="total_distance_km" name="Distance (km)" stroke="#6366f1" fill="url(#distGrad)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Fuel */}
        <div className="card card-body">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Fuel Consumed vs Saved (L)</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={ts} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={d => format(new Date(d), 'dd')} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip labelFormatter={l => fmtDate(l as string)} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="fuel_consumed_litres" name="Consumed" fill="#f97316" radius={[3,3,0,0]} />
              <Bar dataKey="fuel_saved_litres"    name="Saved"    fill="#22c55e" radius={[3,3,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* CO₂ */}
        <div className="card card-body">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Carbon Emitted vs Saved (kg CO₂)</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={ts} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={d => format(new Date(d), 'dd')} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip labelFormatter={l => fmtDate(l as string)} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="co2_emitted_kg" name="Emitted" fill="#ef4444" radius={[3,3,0,0]} />
              <Bar dataKey="co2_saved_kg"   name="Saved"   fill="#22c55e" radius={[3,3,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Partner performance table */}
      {pp.length > 0 && (
        <div className="card">
          <div className="card-header"><h2 className="text-sm font-semibold text-gray-700">Delivery Partner Leaderboard</h2></div>
          <div className="table-container border-0 rounded-b-xl">
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th><th>Partner</th><th>Deliveries</th><th>Completed</th><th>Rate</th><th>Distance (km)</th><th>Avg Time</th><th>Fuel (L)</th><th>CO₂ (kg)</th>
                </tr>
              </thead>
              <tbody>
                {pp.map((p, i) => (
                  <tr key={p.delivery_partner_id}>
                    <td className="text-gray-400 font-medium">{i + 1}</td>
                    <td className="font-medium">{p.partner_name}</td>
                    <td>{p.total_deliveries}</td>
                    <td>{p.completed_deliveries}</td>
                    <td><span className={p.completion_rate_pct >= 80 ? 'badge-green badge' : 'badge-yellow badge'}>{fmtNum(p.completion_rate_pct)}%</span></td>
                    <td>{fmtNum(p.total_distance_km)}</td>
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
