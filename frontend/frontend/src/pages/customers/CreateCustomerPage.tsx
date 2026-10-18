import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import toast from 'react-hot-toast'
import { customersService } from '@/services/customers.service'
import type { CustomerCreate } from '@/types'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

export default function CreateCustomerPage() {
  const { id }   = useParams<{ id: string }>()
  const isEdit   = !!id
  const navigate = useNavigate()
  const qc       = useQueryClient()

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } =
    useForm<CustomerCreate>({ defaultValues: { country: 'India' } })

  const { data: customer, isLoading } = useQuery({
    queryKey: ['customer', id],
    queryFn: () => customersService.get(id!),
    enabled: isEdit,
  })

  useEffect(() => {
    if (customer) reset({
      full_name: customer.full_name,
      email:     customer.email ?? '',
      phone:     customer.phone,
      address:   customer.address,
      city:      customer.city ?? '',
      state:     customer.state ?? '',
      postal_code: customer.postal_code ?? '',
      country:   customer.country,
      notes:     customer.notes ?? '',
    })
  }, [customer, reset])

  const mutation = useMutation({
    mutationFn: (data: CustomerCreate) =>
      isEdit ? customersService.update(id!, data) : customersService.create(data),
    onSuccess: (saved) => {
      toast.success(isEdit ? 'Customer updated!' : 'Customer created!')
      qc.invalidateQueries({ queryKey: ['customers'] })
      navigate(`/customers/${saved.id}`)
    },
  })

  if (isEdit && isLoading) return <div className="flex justify-center py-20"><LoadingSpinner size="lg" /></div>

  return (
    <div className="max-w-2xl space-y-5">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="btn-ghost p-2 rounded-lg">
          <ArrowLeft className="h-4 w-4" />
        </button>
        <h1 className="text-xl font-bold text-gray-900">{isEdit ? 'Edit Customer' : 'Add Customer'}</h1>
      </div>

      <form onSubmit={handleSubmit(d => mutation.mutate(d))} className="card card-body space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <label className="label">Full Name *</label>
            <input className={`input ${errors.full_name ? 'input-error' : ''}`} placeholder="Ravi Kumar"
              {...register('full_name', { required: 'Name is required', minLength: { value: 2, message: 'Min 2 chars' } })} />
            {errors.full_name && <p className="error-text">{errors.full_name.message}</p>}
          </div>

          <div>
            <label className="label">Phone *</label>
            <input className={`input ${errors.phone ? 'input-error' : ''}`} placeholder="+91 98765 43210"
              {...register('phone', { required: 'Phone is required' })} />
            {errors.phone && <p className="error-text">{errors.phone.message}</p>}
          </div>

          <div>
            <label className="label">Email</label>
            <input type="email" className="input" placeholder="ravi@example.com" {...register('email')} />
          </div>
        </div>

        <div>
          <label className="label">Delivery Address *</label>
          <input className={`input ${errors.address ? 'input-error' : ''}`} placeholder="123 MG Road, Bengaluru"
            {...register('address', { required: 'Address is required' })} />
          {errors.address && <p className="error-text">{errors.address.message}</p>}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">City</label>
            <input className="input" placeholder="Bengaluru" {...register('city')} />
          </div>
          <div>
            <label className="label">State</label>
            <input className="input" placeholder="Karnataka" {...register('state')} />
          </div>
          <div>
            <label className="label">Postal Code</label>
            <input className="input" placeholder="560001" {...register('postal_code')} />
          </div>
          <div>
            <label className="label">Country</label>
            <input className="input" {...register('country')} />
          </div>
        </div>

        <div>
          <label className="label">Notes</label>
          <textarea className="input" rows={3} placeholder="Delivery preferences, special notes…" {...register('notes')} />
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" className="btn-secondary" onClick={() => navigate(-1)}>Cancel</button>
          <button type="submit" className="btn-primary" disabled={mutation.isPending}>
            {mutation.isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Add Customer'}
          </button>
        </div>
      </form>
    </div>
  )
}
