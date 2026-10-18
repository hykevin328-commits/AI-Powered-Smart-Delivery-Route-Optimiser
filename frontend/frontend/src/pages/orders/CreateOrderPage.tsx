import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import toast from 'react-hot-toast'
import { ordersService } from '@/services/orders.service'
import { customersService } from '@/services/customers.service'
import type { OrderCreate, OrderPriority } from '@/types'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

const PRIORITIES: OrderPriority[] = ['low', 'normal', 'high', 'urgent']

export default function CreateOrderPage() {
  const { id } = useParams<{ id: string }>()
  const isEdit  = !!id
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<OrderCreate>()

  // Load customers for dropdown
  const { data: custData } = useQuery({
    queryKey: ['customers-all'],
    queryFn: () => customersService.list({ page_size: 200 }),
  })

  // Load existing order when editing
  const { data: order, isLoading: loadingOrder } = useQuery({
    queryKey: ['order', id],
    queryFn: () => ordersService.get(id!),
    enabled: isEdit,
  })

  useEffect(() => {
    if (order) {
      reset({
        customer_id: order.customer_id,
        delivery_address: order.delivery_address,
        delivery_city: order.delivery_city ?? '',
        delivery_postal_code: order.delivery_postal_code ?? '',
        pickup_address: order.pickup_address ?? '',
        package_description: order.package_description ?? '',
        weight_kg: order.weight_kg ?? undefined,
        special_instructions: order.special_instructions ?? '',
        priority: order.priority,
        scheduled_date: order.scheduled_date ? order.scheduled_date.slice(0, 16) : '',
      })
    }
  }, [order, reset])

  const mutation = useMutation({
    mutationFn: (data: OrderCreate) =>
      isEdit ? ordersService.update(id!, data) : ordersService.create(data),
    onSuccess: (saved) => {
      toast.success(isEdit ? 'Order updated!' : 'Order created!')
      qc.invalidateQueries({ queryKey: ['orders'] })
      navigate(`/orders/${saved.id}`)
    },
  })

  if (isEdit && loadingOrder) return <div className="flex justify-center py-20"><LoadingSpinner size="lg" /></div>

  const customers = custData?.customers ?? []

  return (
    <div className="max-w-2xl space-y-5">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="btn-ghost p-2 rounded-lg">
          <ArrowLeft className="h-4 w-4" />
        </button>
        <h1 className="text-xl font-bold text-gray-900">{isEdit ? 'Edit Order' : 'New Delivery Order'}</h1>
      </div>

      <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="card card-body space-y-4">
        {/* Customer */}
        <div>
          <label className="label">Customer *</label>
          <select className={`input ${errors.customer_id ? 'input-error' : ''}`}
            {...register('customer_id', { required: 'Customer is required' })}>
            <option value="">Select customer…</option>
            {customers.map(c => <option key={c.id} value={c.id}>{c.full_name} — {c.phone}</option>)}
          </select>
          {errors.customer_id && <p className="error-text">{errors.customer_id.message}</p>}
        </div>

        {/* Delivery address */}
        <div>
          <label className="label">Delivery Address *</label>
          <input className={`input ${errors.delivery_address ? 'input-error' : ''}`}
            placeholder="123 Main St, Bengaluru"
            {...register('delivery_address', { required: 'Address is required' })} />
          {errors.delivery_address && <p className="error-text">{errors.delivery_address.message}</p>}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">City</label>
            <input className="input" placeholder="Bengaluru" {...register('delivery_city')} />
          </div>
          <div>
            <label className="label">Postal Code</label>
            <input className="input" placeholder="560001" {...register('delivery_postal_code')} />
          </div>
        </div>

        {/* Pickup */}
        <div>
          <label className="label">Pickup Address</label>
          <input className="input" placeholder="Warehouse / origin address"
            {...register('pickup_address')} />
        </div>

        {/* Package */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Package Description</label>
            <input className="input" placeholder="Electronics, fragile…"
              {...register('package_description')} />
          </div>
          <div>
            <label className="label">Weight (kg)</label>
            <input type="number" step="0.1" min="0" className="input"
              {...register('weight_kg', { valueAsNumber: true })} />
          </div>
        </div>

        {/* Priority & schedule */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Priority</label>
            <select className="input" {...register('priority')}>
              {PRIORITIES.map(p => <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Scheduled Date & Time</label>
            <input type="datetime-local" className="input" {...register('scheduled_date')} />
          </div>
        </div>

        {/* Special instructions */}
        <div>
          <label className="label">Special Instructions</label>
          <textarea className="input" rows={3} placeholder="Leave at door, call before delivery…"
            {...register('special_instructions')} />
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" className="btn-secondary" onClick={() => navigate(-1)}>Cancel</button>
          <button type="submit" className="btn-primary" disabled={isSubmitting || mutation.isPending}>
            {mutation.isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Create Order'}
          </button>
        </div>
      </form>
    </div>
  )
}
