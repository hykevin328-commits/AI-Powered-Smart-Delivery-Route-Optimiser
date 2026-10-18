import apiClient from '@/lib/axios'
import type { ApiResponse, Customer, CustomerCreate, DeliveryOrder, PaginatedResponse } from '@/types'

export const customersService = {
  async list(params: { page?: number; page_size?: number; search?: string; is_active?: boolean } = {}) {
    const res = await apiClient.get<PaginatedResponse<Customer>>('/customers', { params })
    return { customers: res.data.data, total: res.data.meta?.total ?? 0 }
  },

  async get(id: string): Promise<Customer> {
    const res = await apiClient.get<ApiResponse<Customer>>(`/customers/${id}`)
    return res.data.data
  },

  async create(data: CustomerCreate): Promise<Customer> {
    const res = await apiClient.post<ApiResponse<Customer>>('/customers', data)
    return res.data.data
  },

  async update(id: string, data: Partial<CustomerCreate>): Promise<Customer> {
    const res = await apiClient.put<ApiResponse<Customer>>(`/customers/${id}`, data)
    return res.data.data
  },

  async deactivate(id: string): Promise<void> {
    await apiClient.delete(`/customers/${id}`)
  },

  async getOrders(id: string, page = 1): Promise<{ orders: DeliveryOrder[]; total: number }> {
    const res = await apiClient.get<PaginatedResponse<DeliveryOrder>>(`/customers/${id}/orders`, {
      params: { page },
    })
    return { orders: res.data.data, total: res.data.meta?.total ?? 0 }
  },

  async getStats(id: string) {
    const res = await apiClient.get<ApiResponse<{
      total_orders: number
      delivered: number
      cancelled: number
      failed: number
      completion_rate: number
    }>>(`/customers/${id}/stats`)
    return res.data.data
  },
}
