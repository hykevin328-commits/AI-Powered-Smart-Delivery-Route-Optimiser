import apiClient from '@/lib/axios'
import type {
  ApiResponse,
  AssignOrderRequest,
  DeliveryOrder,
  OrderCreate,
  OrderPriority,
  OrderStatus,
  PaginatedResponse,
  StatusLog,
} from '@/types'

export const ordersService = {
  async list(params: {
    page?: number
    page_size?: number
    status?: OrderStatus
    priority?: OrderPriority
    customer_id?: string
    partner_id?: string
    scheduled_date?: string
  } = {}): Promise<{ orders: DeliveryOrder[]; total: number }> {
    const res = await apiClient.get<PaginatedResponse<DeliveryOrder>>('/orders', { params })
    return { orders: res.data.data, total: res.data.meta?.total ?? 0 }
  },

  async getToday(): Promise<DeliveryOrder[]> {
    const res = await apiClient.get<ApiResponse<DeliveryOrder[]>>('/orders/today')
    return res.data.data
  },

  async get(id: string): Promise<DeliveryOrder> {
    const res = await apiClient.get<ApiResponse<DeliveryOrder>>(`/orders/${id}`)
    return res.data.data
  },

  async create(data: OrderCreate): Promise<DeliveryOrder> {
    const res = await apiClient.post<ApiResponse<DeliveryOrder>>('/orders', data)
    return res.data.data
  },

  async update(id: string, data: Partial<OrderCreate>): Promise<DeliveryOrder> {
    const res = await apiClient.put<ApiResponse<DeliveryOrder>>(`/orders/${id}`, data)
    return res.data.data
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/orders/${id}`)
  },

  async assign(data: AssignOrderRequest): Promise<{ assigned_count: number }> {
    const res = await apiClient.post<ApiResponse<{ assigned_count: number }>>('/orders/assign', data)
    return res.data.data
  },

  async updateStatus(id: string, status: OrderStatus, notes?: string): Promise<DeliveryOrder> {
    const res = await apiClient.patch<ApiResponse<DeliveryOrder>>(`/orders/${id}/status`, {
      status,
      notes,
    })
    return res.data.data
  },

  async complete(id: string): Promise<DeliveryOrder> {
    const res = await apiClient.post<ApiResponse<DeliveryOrder>>(`/orders/${id}/complete`)
    return res.data.data
  },

  async getStatusHistory(id: string): Promise<StatusLog[]> {
    const res = await apiClient.get<ApiResponse<StatusLog[]>>(`/orders/${id}/status-history`)
    return res.data.data
  },
}
