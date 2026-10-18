import apiClient from '@/lib/axios'
import type { ApiResponse, OptimizeRouteRequest, OptimizeRouteResponse } from '@/types'

export const routesService = {
  async optimize(data: OptimizeRouteRequest): Promise<OptimizeRouteResponse> {
    const res = await apiClient.post<ApiResponse<OptimizeRouteResponse>>('/routes/optimize', data)
    return res.data.data
  },

  async recalculate(data: {
    assignment_id: string
    current_latitude: number
    current_longitude: number
    cancelled_order_ids?: string[]
  }): Promise<OptimizeRouteResponse> {
    const res = await apiClient.post<ApiResponse<OptimizeRouteResponse>>('/routes/recalculate', data)
    return res.data.data
  },

  async getHistory(params: { page?: number; page_size?: number; partner_id?: string } = {}) {
    const res = await apiClient.get('/routes/history', { params })
    return { history: res.data.data, total: res.data.meta?.total ?? 0 }
  },
}
