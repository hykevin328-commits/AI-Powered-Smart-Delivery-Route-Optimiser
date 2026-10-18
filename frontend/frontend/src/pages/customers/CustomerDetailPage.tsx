import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Pencil, MapPin, Package } from 'lucide-react'
import { customersService } from '@/services/customers.service'
import { fmtDate, fmtDateTime, orderStatusClass, capitalize, cn } from '@/lib/utils'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import Pagination from '@/components/ui/Pagination'

export default function CustomerDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [page, setPage] = useState(1)

  const { data: customer, isLoading } = useQuery({
    queryKey: ['customer', id],
    queryFn: () => customersService.get(id!),
    enabled: !!id,
  })

  const { data: stats } = useQuery({
    queryKey: ['customer-stats', id],
    queryFn: () => customersService.getStats(id!),
    enabled: !!id,
  })

  const { data: orderData } = useQuery({
    queryKey: ['customer-orders', id, page],
    queryFn: () => customersService.getOrders(id!, page),
    enabled: !!id,
  })

  if (isLoading) return <div className="flex justify-center py-20"><LoadingSpinner size="lg" /></div>
  if (!customer) return <div className="text-center py-20 text-gray-500">Customer not found.</div>

  return (
    <div className="space-y-5 max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="btn-ghost p-2 rounded-lg">
          <ArrowLeft className="h-4 w-4" />
        </button>
        <div className="flex-1">
          <h1 className="text-xl font-bold text-gray-900">{customer.full_name}</h1>
          <span className={cn('badge', customer.is_active ? 'badge-green' : 'badge-gray')}>
            {customer.is_active ? 'Active' : 'Inactive'}
          </span>
        </div>
        <Link to={`/customers/${id}/edit`} className="btn-secondary btn-sm">
          <Pencil className="h-4 w-4" /> Edit
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Info card */}
        <div className="card card-body space-y-3">
          <h2 className="font-semibold text-gray-800">Contact & Location</h2>
          <Row label="Phone">{customer.phone}</Row>
          <Row label="Email">{customer.email ?? '—'}</Row>
          <Row label="Address">{customer.address}</Row>
          <Row label="City">{[customer.city, customer.state, customer.postal_code].filter(Boolean).join(', ') || '—'}</Row>
          <Row label="Country">{customer.country}</Row>
          {customer.latitude && customer.longitude && (
            <Row label="Coordinates">
              <span className="flex items-center gap-1 text-green-600 text-xs">
                <MapPin className="h-3 w-3" />
                {customer.latitude.toFixed(5)}, {customer.longitude.toFixed(5)}
              </span>
            </Row>
          )}
          {customer.notes && <Row label="Notes">{customer.notes}</Row>}
          <Row label="Since">{fmtDate(customer.created_at)}</Row>
        </div>

        {/* Stats card */}
        {stats && (
          <div className="card card-body space-y-3">
            <h2 className="font-semibold text-gray-800">Delivery Stats</h2>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Total Orders',   value: stats.total_orders },
                { label: 'Delivered',      value: stats.delivered },
                { label: 'Cancelled',      value: stats.cancelled },
                { label: 'Failed',         value: stats.failed },
              ].map(s => (
                <div key={s.label} className="bg-gray-50 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-gray-900">{s.value}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{s.label}</p>
                </div>
              ))}
            </div>
            <div className="bg-primary-50 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-primary-700">{stats.completion_rate}%</p>
              <p className="text-xs text-primary-500">Completion Rate</p>
            </div>
          </div>
        )}
      </div>

      {/* Delivery history */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <Package className="h-4 w-4 text-gray-500" />
          <h2 className="font-semibold text-gray-800">Delivery History</h2>
        </div>
        {!orderData?.orders.length ? (
          <div className="p-8 text-center text-gray-400 text-sm">No orders yet.</div>
        ) : (
          <>
            <div className="table-container border-0 rounded-none rounded-b-xl">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Order #</th>
                    <th>Status</th>
                    <th>Address</th>
                    <th>Scheduled</th>
                    <th>Delivered</th>
                  </tr>
                </thead>
                <tbody>
                  {orderData.orders.map(o => (
                    <tr key={o.id}>
                      <td>
                        <Link to={`/orders/${o.id}`} className="font-mono text-primary-700 hover:underline">
                          {o.order_number}
                        </Link>
                      </td>
                      <td><span className={orderStatusClass(o.status)}>{capitalize(o.status)}</span></td>
                      <td className="max-w-xs truncate text-gray-500">{o.delivery_address}</td>
                      <td className="text-gray-500">{fmtDate(o.scheduled_date)}</td>
                      <td className="text-gray-500">{fmtDateTime(o.delivered_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="px-4 pb-4">
              <Pagination page={page} totalPages={Math.ceil((orderData.total) / 10)} onPageChange={setPage} />
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex gap-2 text-sm">
      <span className="text-gray-400 w-28 flex-shrink-0">{label}</span>
      <span className="text-gray-800">{children}</span>
    </div>
  )
}
