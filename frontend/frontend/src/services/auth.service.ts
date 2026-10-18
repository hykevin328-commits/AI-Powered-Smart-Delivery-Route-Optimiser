import apiClient from '@/lib/axios'
import type {
  ApiResponse,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
} from '@/types'

export const authService = {
  async register(data: RegisterRequest): Promise<User> {
    const res = await apiClient.post<ApiResponse<User>>('/auth/register', data)
    return res.data.data
  },

  async login(data: LoginRequest): Promise<{ tokens: TokenResponse; user: User }> {
    const res = await apiClient.post<ApiResponse<{ tokens: TokenResponse; user: User }>>(
      '/auth/login',
      data,
    )
    return res.data.data
  },

  async logout(): Promise<void> {
    await apiClient.post('/auth/logout')
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  },

  async getProfile(): Promise<User> {
    const res = await apiClient.get<ApiResponse<User>>('/auth/me')
    return res.data.data
  },

  async updateProfile(data: Partial<User>): Promise<User> {
    const res = await apiClient.put<ApiResponse<User>>('/auth/me', data)
    return res.data.data
  },

  async changePassword(current_password: string, new_password: string): Promise<void> {
    await apiClient.post('/auth/me/change-password', { current_password, new_password })
  },

  async listUsers(page = 1, page_size = 20): Promise<{ users: User[]; total: number }> {
    const res = await apiClient.get('/auth/users', { params: { page, page_size } })
    return { users: res.data.data, total: res.data.meta?.total ?? 0 }
  },

  async deactivateUser(id: string): Promise<User> {
    const res = await apiClient.put<ApiResponse<User>>(`/auth/users/${id}/deactivate`)
    return res.data.data
  },

  async activateUser(id: string): Promise<User> {
    const res = await apiClient.put<ApiResponse<User>>(`/auth/users/${id}/activate`)
    return res.data.data
  },
}
