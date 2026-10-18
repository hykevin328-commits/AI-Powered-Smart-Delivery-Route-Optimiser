import apiClient from '@/lib/axios'
import type { ApiResponse, DashboardData, DailyDataPoint, KPISummary, PartnerPerformance } from '@/types'

export const analyticsService = {
  async getDashboard(params: {
    start_date?: string
    end_date?: string
    period_type?: 'daily' | 'weekly' | 'monthly'
    partner_id?: string
  } = {}): Promise<DashboardData> {
    const res = await apiClient.get<ApiResponse<DashboardData>>('/analytics/dashboard', { params })
    return res.data.data
  },

  async getKPI(params: { start_date?: string; end_date?: string; partner_id?: string } = {}): Promise<KPISummary> {
    const res = await apiClient.get<ApiResponse<KPISummary>>('/analytics/summary', { params })
    return res.data.data
  },

  async getTimeSeries(params: {
    start_date?: string
    end_date?: string
    period_type?: string
    partner_id?: string
  } = {}): Promise<DailyDataPoint[]> {
    const res = await apiClient.get<ApiResponse<DailyDataPoint[]>>('/analytics/time-series', { params })
    return res.data.data
  },

  async getPartnerPerformance(params: { start_date?: string; end_date?: string } = {}): Promise<PartnerPerformance[]> {
    const res = await apiClient.get<ApiResponse<PartnerPerformance[]>>('/analytics/partners', { params })
    return res.data.data
  },
}
