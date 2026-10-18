import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Plus, Search, Filter, MoreVertical, Eye, Pencil, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { ordersService } from '@/services/orders.service'
import type { OrderPriority, OrderStatus } from '@/types'
import { orderStatusClass, priorityClass, fmtDate, capitalize } from '@/lib/utils'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import Pagination from '@/components/ui/Pagination'
import EmptyState from '@/components/ui/EmptyState'
import Modal from '@/components/ui/Modal'

const STATUS_OPTIONS: OrderStatus[] = ['pending', 'assigned', 'picked_up', 'in_transit', 'delivered', 'failed', 'cancelled']
const PRIORITY_OPTIONS: OrderPriority[] = ['low', 'normal', 'high', 'urgent']

export default function OrdersPage() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState<OrderStatus | ''>('')
  const [priority, setPriority] = useState<OrderPriority | ''>('')
  const [deleteId, setDeleteId] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['orders', page, status, priority],
    queryFn: () => ordersService.list({ page, page_size: 20, status: status || undefined, priority: priority || undefined }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => ordersService.delete(id),
    onSuccess: () => {
      toast.success('Order deleted')
      qc.invalidateQueries({ queryKey: ['orders'] })
      setDeleteId(null)
    },
  })

  const orders = data?.orders ?? []
  const total = data?.total ?? 0

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Delivery Orders</h1>
          <p className="text-sm text-gray-500">{total} total orders</p>
        </div>
        <Link to="/orders/new" className="btn-primary btn-sm">
          <Plus className="h-4 w-4" /> New Order
        </Link>
      </div>

      {/* Filters */}
      <div className="card card-body flex flex-wrap gap-3">
        <select className="input w-auto text-sm" value={status} onChange={e => { setStatus(e.target.value as OrderStatus | ''); setPage(1) }}>
          <option value="">All Statuses</option>
          {STATUS_OPTIONS.map(s => <option key={s} value={s}>{capitalize(s)}</option>)}
        </select>
        <select className="input w-auto text-sm" value={priority} onChange={e => { setPriority(e.target.value as OrderPriority | ''); setPage(1) }}>
          <option value="">All Priorities</option>
          {PRIORITY_OPTIONS.map(p => <option key={p} value={p}>{capitalize(p)}</option>)}
        </select>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="flex justify-center py-16"><LoadingSpinner size="lg" /></div>
      ) : orders.length === 0 ? (
        <div className="card"><EmptyState title="No orders found" description="Create your first delivery order." action={<Link to="/orders/new" className="btn-primary btn-sm">New Order</Link>} /></div>
      ) : (
        <div className="card">
          <div className="table-container border-0 rounded-none rounded-xl">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Order #</th>
                  <th>Customer</th>
                  <th>Address</th>
                  <th>Status</th>
                  <th>Priority</th>
                  <th>Scheduled</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {orders.map(order => (
                  <tr key={order.id}>
                    <td className="font-mono font-medium text-primary-700">{order.order_number}</td>
                    <td className="font-medium">{order.customer?.full_name ?? '—'}</td>
                    <td className="max-w-xs truncate text-gray-500">{order.delivery_address}</td>
                    <td><span className={orderStatusClass(order.status)}>{capitalize(order.status)}</span></td>
                    <td><span className={priorityClass(order.priority)}>{capitalize(order.priority)}</span></td>
                    <td className="text-gray-500">{fmtDate(order.scheduled_date)}</td>
                    <td>
                      <div className="flex items-center gap-1">
                        <Link to={`/orders/${order.id}`} className="btn-ghost p-1.5 rounded-lg" title="View">
                          <Eye className="h-4 w-4" />
                        </Link>
                        <Link to={`/orders/${order.id}/edit`} className="btn-ghost p-1.5 rounded-lg" title="Edit">
                          <Pencil className="h-4 w-4" />
                        </Link>
                        {(order.status === 'pending' || order.status === 'cancelled') && (
                          <button onClick={() => setDeleteId(order.id)} className="btn-ghost p-1.5 rounded-lg text-red-500 hover:bg-red-50" title="Delete">
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-4 pb-4">
            <Pagination page={page} totalPages={Math.ceil(total / 20)} onPageChange={setPage} />
          </div>
        </div>
      )}

      {/* Delete confirm modal */}
      <Modal
        open={!!deleteId}
        onClose={() => setDeleteId(null)}
        title="Delete Order"
        footer={
          <>
            <button className="btn-secondary btn-sm" onClick={() => setDeleteId(null)}>Cancel</button>
            <button className="btn-danger btn-sm" onClick={() => deleteId && deleteMutation.mutate(deleteId)} disabled={deleteMutation.isPending}>
              {deleteMutation.isPending ? 'Deleting…' : 'Delete'}
            </button>
          </>
        }
      >
        <p className="text-sm text-gray-600">Are you sure you want to permanently delete this order? This action cannot be undone.</p>
      </Modal>
    </div>
  )
}
