import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil, Trash2, Car } from 'lucide-react'
import toast from 'react-hot-toast'
import { useForm } from 'react-hook-form'
import { vehiclesService } from '@/services/vehicles.service'
import type { Vehicle, VehicleStatus, VehicleType } from '@/types'
import { vehicleStatusClass, capitalize, cn } from '@/lib/utils'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import Pagination from '@/components/ui/Pagination'
import EmptyState from '@/components/ui/EmptyState'
import Modal from '@/components/ui/Modal'

const TYPES: VehicleType[]   = ['bike', 'scooter', 'car', 'van', 'truck']
const STATUSES: VehicleStatus[] = ['available', 'in_use', 'maintenance', 'retired']

type VehicleForm = Pick<Vehicle, 'registration_number' | 'make' | 'model' | 'vehicle_type' | 'max_capacity_kg' | 'fuel_efficiency_l_per_100km' | 'is_electric'>

export default function VehiclesPage() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [filterStatus, setFilterStatus] = useState<VehicleStatus | ''>('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editVehicle, setEditVehicle] = useState<Vehicle | null>(null)
  const [deleteId, setDeleteId] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['vehicles', page, filterStatus],
    queryFn: () => vehiclesService.list({ page, page_size: 20, status: filterStatus || undefined }),
  })

  const { register, handleSubmit, reset, formState: { errors } } = useForm<VehicleForm>({
    defaultValues: { vehicle_type: 'van', max_capacity_kg: 500, fuel_efficiency_l_per_100km: 8.5, is_electric: false },
  })

  function openCreate() { setEditVehicle(null); reset({ vehicle_type: 'van', max_capacity_kg: 500, fuel_efficiency_l_per_100km: 8.5, is_electric: false }); setModalOpen(true) }
  function openEdit(v: Vehicle) { setEditVehicle(v); reset({ registration_number: v.registration_number, make: v.make ?? '', model: v.model ?? '', vehicle_type: v.vehicle_type, max_capacity_kg: v.max_capacity_kg, fuel_efficiency_l_per_100km: v.fuel_efficiency_l_per_100km, is_electric: v.is_electric }); setModalOpen(true) }

  const saveMutation = useMutation({
    mutationFn: (data: VehicleForm) =>
      editVehicle ? vehiclesService.update(editVehicle.id, data) : vehiclesService.create(data),
    onSuccess: () => {
      toast.success(editVehicle ? 'Vehicle updated!' : 'Vehicle added!')
      qc.invalidateQueries({ queryKey: ['vehicles'] })
      setModalOpen(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => vehiclesService.delete(id),
    onSuccess: () => { toast.success('Vehicle removed'); qc.invalidateQueries({ queryKey: ['vehicles'] }); setDeleteId(null) },
  })

  const vehicles = data?.vehicles ?? []
  const total    = data?.total ?? 0

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Fleet Vehicles</h1>
          <p className="text-sm text-gray-500">{total} vehicles</p>
        </div>
        <button onClick={openCreate} className="btn-primary btn-sm">
          <Plus className="h-4 w-4" /> Add Vehicle
        </button>
      </div>

      <div className="card card-body">
        <select className="input w-auto text-sm" value={filterStatus} onChange={e => { setFilterStatus(e.target.value as VehicleStatus | ''); setPage(1) }}>
          <option value="">All Statuses</option>
          {STATUSES.map(s => <option key={s} value={s}>{capitalize(s.replace('_', ' '))}</option>)}
        </select>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16"><LoadingSpinner size="lg" /></div>
      ) : vehicles.length === 0 ? (
        <div className="card">
          <EmptyState title="No vehicles found" icon={<Car className="h-10 w-10 text-gray-300" />} action={<button onClick={openCreate} className="btn-primary btn-sm">Add Vehicle</button>} />
        </div>
      ) : (
        <div className="card">
          <div className="table-container border-0 rounded-xl">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Registration</th>
                  <th>Type</th>
                  <th>Make / Model</th>
                  <th>Capacity</th>
                  <th>Efficiency</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {vehicles.map(v => (
                  <tr key={v.id}>
                    <td className="font-mono font-medium">{v.registration_number}</td>
                    <td><span className="badge badge-blue">{capitalize(v.vehicle_type)}</span></td>
                    <td className="text-gray-600">{[v.make, v.model].filter(Boolean).join(' ') || '—'}</td>
                    <td>{v.max_capacity_kg} kg</td>
                    <td>{v.is_electric ? <span className="badge badge-green">Electric</span> : `${v.fuel_efficiency_l_per_100km} L/100km`}</td>
                    <td><span className={vehicleStatusClass(v.status)}>{capitalize(v.status.replace('_', ' '))}</span></td>
                    <td>
                      <div className="flex items-center gap-1">
                        <button onClick={() => openEdit(v)} className="btn-ghost p-1.5 rounded-lg" title="Edit"><Pencil className="h-4 w-4" /></button>
                        <button onClick={() => setDeleteId(v.id)} className="btn-ghost p-1.5 rounded-lg text-red-500 hover:bg-red-50" title="Delete"><Trash2 className="h-4 w-4" /></button>
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

      {/* Create/Edit modal */}
      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editVehicle ? 'Edit Vehicle' : 'Add Vehicle'}
        footer={
          <>
            <button className="btn-secondary btn-sm" onClick={() => setModalOpen(false)}>Cancel</button>
            <button className="btn-primary btn-sm" onClick={handleSubmit(d => saveMutation.mutate(d))} disabled={saveMutation.isPending}>
              {saveMutation.isPending ? 'Saving…' : 'Save'}
            </button>
          </>
        }>
        <div className="space-y-4">
          <div>
            <label className="label">Registration Number *</label>
            <input className={`input ${errors.registration_number ? 'input-error' : ''}`} placeholder="KA-01-AB-1234" {...register('registration_number', { required: 'Required' })} />
            {errors.registration_number && <p className="error-text">{errors.registration_number.message}</p>}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Make</label>
              <input className="input" placeholder="Maruti" {...register('make')} />
            </div>
            <div>
              <label className="label">Model</label>
              <input className="input" placeholder="Eeco" {...register('model')} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Type</label>
              <select className="input" {...register('vehicle_type')}>
                {TYPES.map(t => <option key={t} value={t}>{capitalize(t)}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Capacity (kg)</label>
              <input type="number" className="input" {...register('max_capacity_kg', { valueAsNumber: true })} />
            </div>
          </div>
          <div>
            <label className="label">Fuel Efficiency (L/100km)</label>
            <input type="number" step="0.1" className="input" {...register('fuel_efficiency_l_per_100km', { valueAsNumber: true })} />
          </div>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input type="checkbox" className="rounded" {...register('is_electric')} />
            <span>Electric Vehicle</span>
          </label>
        </div>
      </Modal>

      {/* Delete confirm */}
      <Modal open={!!deleteId} onClose={() => setDeleteId(null)} title="Delete Vehicle"
        footer={
          <>
            <button className="btn-secondary btn-sm" onClick={() => setDeleteId(null)}>Cancel</button>
            <button className="btn-danger btn-sm" onClick={() => deleteId && deleteMutation.mutate(deleteId)} disabled={deleteMutation.isPending}>
              {deleteMutation.isPending ? 'Deleting…' : 'Delete'}
            </button>
          </>
        }>
        <p className="text-sm text-gray-600">Are you sure? This will permanently remove the vehicle from your fleet.</p>
      </Modal>
    </div>
  )
}
