import apiClient from '@/lib/axios'
import type { ApiResponse, PaginatedResponse, Vehicle, VehicleStatus } from '@/types'

export const vehiclesService = {
  async list(params: { page?: number; page_size?: number; status?: VehicleStatus } = {}) {
    const res = await apiClient.get<PaginatedResponse<Vehicle>>('/vehicles', { params })
    return { vehicles: res.data.data, total: res.data.meta?.total ?? 0 }
  },

  async get(id: string): Promise<Vehicle> {
    const res = await apiClient.get<ApiResponse<Vehicle>>(`/vehicles/${id}`)
    return res.data.data
  },

  async create(data: Partial<Vehicle>): Promise<Vehicle> {
    const res = await apiClient.post<ApiResponse<Vehicle>>('/vehicles', data)
    return res.data.data
  },

  async update(id: string, data: Partial<Vehicle>): Promise<Vehicle> {
    const res = await apiClient.put<ApiResponse<Vehicle>>(`/vehicles/${id}`, data)
    return res.data.data
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/vehicles/${id}`)
  },
}
