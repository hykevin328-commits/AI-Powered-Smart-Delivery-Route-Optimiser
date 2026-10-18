import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Search, Eye, Pencil, Trash2, MapPin } from 'lucide-react'
import toast from 'react-hot-toast'
import { customersService } from '@/services/customers.service'
import { fmtDate, cn } from '@/lib/utils'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import Pagination from '@/components/ui/Pagination'
import EmptyState from '@/components/ui/EmptyState'
import Modal from '@/components/ui/Modal'

export default function CustomersPage() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [deleteId, setDeleteId] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['customers', page, search],
    queryFn: () => customersService.list({ page, page_size: 20, search: search || undefined }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => customersService.deactivate(id),
    onSuccess: () => {
      toast.success('Customer deactivated')
      qc.invalidateQueries({ queryKey: ['customers'] })
      setDeleteId(null)
    },
  })

  const customers = data?.customers ?? []
  const total     = data?.total ?? 0

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Customers</h1>
          <p className="text-sm text-gray-500">{total} total customers</p>
        </div>
        <Link to="/customers/new" className="btn-primary btn-sm">
          <Plus className="h-4 w-4" /> Add Customer
        </Link>
      </div>

      {/* Search */}
      <div className="card card-body">
        <div className="relative max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            className="input pl-9"
            placeholder="Search name, phone, email…"
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
          />
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16"><LoadingSpinner size="lg" /></div>
      ) : customers.length === 0 ? (
        <div className="card">
          <EmptyState
            title="No customers found"
            description="Add your first customer to start creating delivery orders."
            action={<Link to="/customers/new" className="btn-primary btn-sm">Add Customer</Link>}
          />
        </div>
      ) : (
        <div className="card">
          <div className="table-container border-0 rounded-xl">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Phone</th>
                  <th>Email</th>
                  <th>City</th>
                  <th>Coordinates</th>
                  <th>Status</th>
                  <th>Since</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {customers.map(c => (
                  <tr key={c.id}>
                    <td className="font-medium">{c.full_name}</td>
                    <td>{c.phone}</td>
                    <td className="text-gray-500">{c.email ?? '—'}</td>
                    <td className="text-gray-500">{c.city ?? '—'}</td>
                    <td>
                      {c.latitude && c.longitude ? (
                        <span className="flex items-center gap-1 text-xs text-green-600">
                          <MapPin className="h-3 w-3" />
                          {c.latitude.toFixed(4)}, {c.longitude.toFixed(4)}
                        </span>
                      ) : <span className="text-xs text-gray-400">Not geocoded</span>}
                    </td>
                    <td>
                      <span className={cn('badge', c.is_active ? 'badge-green' : 'badge-gray')}>
                        {c.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="text-gray-500">{fmtDate(c.created_at)}</td>
                    <td>
                      <div className="flex items-center gap-1">
                        <Link to={`/customers/${c.id}`} className="btn-ghost p-1.5 rounded-lg" title="View">
                          <Eye className="h-4 w-4" />
                        </Link>
                        <Link to={`/customers/${c.id}/edit`} className="btn-ghost p-1.5 rounded-lg" title="Edit">
                          <Pencil className="h-4 w-4" />
                        </Link>
                        <button
                          onClick={() => setDeleteId(c.id)}
                          className="btn-ghost p-1.5 rounded-lg text-red-500 hover:bg-red-50"
                          title="Deactivate"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
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

      <Modal
        open={!!deleteId}
        onClose={() => setDeleteId(null)}
        title="Deactivate Customer"
        footer={
          <>
            <button className="btn-secondary btn-sm" onClick={() => setDeleteId(null)}>Cancel</button>
            <button className="btn-danger btn-sm"
              onClick={() => deleteId && deleteMutation.mutate(deleteId)}
              disabled={deleteMutation.isPending}>
              {deleteMutation.isPending ? 'Deactivating…' : 'Deactivate'}
            </button>
          </>
        }
      >
        <p className="text-sm text-gray-600">This will deactivate the customer. Their delivery history will be preserved.</p>
      </Modal>
    </div>
  )
}
