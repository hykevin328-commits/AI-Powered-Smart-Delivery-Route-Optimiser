import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { Truck, UserCheck } from 'lucide-react'
import toast from 'react-hot-toast'
import { authService } from '@/services/auth.service'
import { useAuthStore } from '@/store/authStore'
import type { LoginRequest } from '@/types'

export default function LoginPage() {
  const navigate = useNavigate()
  const { setAuth, loginAsGuest } = useAuthStore()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginRequest>()

  // ── Real login ──────────────────────────────────────────────────────────────
  async function onSubmit(data: LoginRequest) {
    try {
      const { tokens, user } = await authService.login(data)
      setAuth(user, tokens)
      toast.success(`Welcome back, ${user.full_name}!`)
      navigate('/dashboard')
    } catch {
      // error toast handled by axios interceptor
    }
  }

  // ── Guest login (no backend needed) ────────────────────────────────────────
  function handleGuest() {
    loginAsGuest()
    toast.success('Browsing as Guest — backend not required')
    navigate('/dashboard')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-950 to-primary-800 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">

        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="bg-primary-500 rounded-2xl p-3 mb-3">
            <Truck className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">Smart Route Optimizer</h1>
          <p className="text-primary-300 text-sm mt-1">Sign in to your account</p>
        </div>

        <div className="bg-white rounded-2xl p-8 shadow-xl space-y-5">

          {/* Guest banner */}
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 text-center">
            <p className="text-xs text-blue-700 font-medium mb-2">
              🚀 No backend yet? Try the UI instantly
            </p>
            <button
              type="button"
              onClick={handleGuest}
              className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 px-4 rounded-lg transition-colors"
            >
              <UserCheck className="h-4 w-4" />
              Continue as Guest (Demo Mode)
            </button>
          </div>

          {/* Divider */}
          <div className="flex items-center gap-3">
            <div className="flex-1 border-t border-gray-200" />
            <span className="text-xs text-gray-400">or sign in with account</span>
            <div className="flex-1 border-t border-gray-200" />
          </div>

          {/* Email */}
          <div>
            <label className="label">Email address</label>
            <input
              type="email"
              placeholder="you@example.com"
              className={`input ${errors.email ? 'input-error' : ''}`}
              {...register('email', { required: 'Email is required' })}
            />
            {errors.email && <p className="error-text">{errors.email.message}</p>}
          </div>

          {/* Password */}
          <div>
            <label className="label">Password</label>
            <input
              type="password"
              placeholder="••••••••"
              className={`input ${errors.password ? 'input-error' : ''}`}
              {...register('password', { required: 'Password is required' })}
            />
            {errors.password && <p className="error-text">{errors.password.message}</p>}
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="btn-primary w-full btn-lg"
            onClick={handleSubmit(onSubmit)}
          >
            {isSubmitting ? 'Signing in…' : 'Sign in'}
          </button>

          <p className="text-center text-sm text-gray-500">
            Don't have an account?{' '}
            <Link to="/register" className="text-primary-600 font-medium hover:underline">
              Register
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
