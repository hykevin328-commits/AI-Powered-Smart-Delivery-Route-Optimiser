import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { Truck } from 'lucide-react'
import toast from 'react-hot-toast'
import { authService } from '@/services/auth.service'
import type { RegisterRequest } from '@/types'

export default function RegisterPage() {
  const navigate = useNavigate()
  const { register, handleSubmit, formState: { errors, isSubmitting }, watch } = useForm<RegisterRequest & { confirm_password: string }>()
  const password = watch('password')

  async function onSubmit(data: RegisterRequest) {
    try {
      await authService.register(data)
      toast.success('Account created! Please sign in.')
      navigate('/login')
    } catch { /* handled by interceptor */ }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-950 to-primary-800 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="bg-primary-500 rounded-2xl p-3 mb-3">
            <Truck className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">Create Account</h1>
          <p className="text-primary-300 text-sm mt-1">Join Smart Route Optimizer</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="bg-white rounded-2xl p-8 shadow-xl space-y-4">
          <div>
            <label className="label">Full Name</label>
            <input className={`input ${errors.full_name ? 'input-error' : ''}`} placeholder="John Doe"
              {...register('full_name', { required: 'Full name is required', minLength: { value: 2, message: 'Min 2 characters' } })} />
            {errors.full_name && <p className="error-text">{errors.full_name.message}</p>}
          </div>

          <div>
            <label className="label">Email</label>
            <input type="email" className={`input ${errors.email ? 'input-error' : ''}`} placeholder="you@example.com"
              {...register('email', { required: 'Email is required' })} />
            {errors.email && <p className="error-text">{errors.email.message}</p>}
          </div>

          <div>
            <label className="label">Phone</label>
            <input className="input" placeholder="+91 98765 43210"
              {...register('phone')} />
          </div>

          <div>
            <label className="label">Role</label>
            <select className="input" {...register('role')}>
              <option value="delivery_partner">Delivery Partner</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          <div>
            <label className="label">Password</label>
            <input type="password" className={`input ${errors.password ? 'input-error' : ''}`} placeholder="Min 8 chars, 1 uppercase, 1 digit"
              {...register('password', {
                required: 'Password is required',
                minLength: { value: 8, message: 'Min 8 characters' },
                validate: v => /[A-Z]/.test(v) && /[0-9]/.test(v) || 'Need 1 uppercase + 1 digit',
              })} />
            {errors.password && <p className="error-text">{errors.password.message}</p>}
          </div>

          <div>
            <label className="label">Confirm Password</label>
            <input type="password" className={`input ${errors.confirm_password ? 'input-error' : ''}`} placeholder="••••••••"
              {...register('confirm_password', {
                required: 'Please confirm your password',
                validate: v => v === password || 'Passwords do not match',
              })} />
            {errors.confirm_password && <p className="error-text">{errors.confirm_password.message}</p>}
          </div>

          <button type="submit" disabled={isSubmitting} className="btn-primary w-full btn-lg">
            {isSubmitting ? 'Creating account…' : 'Create account'}
          </button>

          <p className="text-center text-sm text-gray-500">
            Already have an account?{' '}
            <Link to="/login" className="text-primary-600 font-medium hover:underline">Sign in</Link>
          </p>
        </form>
      </div>
    </div>
  )
}
