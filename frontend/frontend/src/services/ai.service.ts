import apiClient from '@/lib/axios'
import type { ApiResponse, DelayPrediction, FuelPrediction, OrderAIPrediction } from '@/types'

export const aiService = {
  async predictDelay(data: {
    distance_km: number
    num_stops: number
    traffic_factor?: number
    congestion_level?: string
    weather_condition?: string
    priority?: string
  }): Promise<DelayPrediction> {
    const res = await apiClient.post<ApiResponse<DelayPrediction>>('/ai/predict/delay', data)
    return res.data.data
  },

  async predictFuel(data: {
    distance_km: number
    vehicle_efficiency_l_per_100km?: number
    traffic_factor?: number
    load_kg?: number
    is_electric?: boolean
  }): Promise<FuelPrediction> {
    const res = await apiClient.post<ApiResponse<FuelPrediction>>('/ai/predict/fuel', data)
    return res.data.data
  },

  async predictTraffic(data: {
    hour: number
    day_of_week: number
    latitude: number
    longitude: number
    current_factor?: number
  }) {
    const res = await apiClient.post<ApiResponse<{
      predicted_traffic_factor: number
      congestion_level: string
      best_departure_hour: number
      avoid_hours: number[]
    }>>('/ai/predict/traffic', data)
    return res.data.data
  },

  async analyzeOrder(
    orderId: string,
    params: { weather_condition?: string; traffic_factor?: number; congestion_level?: string } = {},
  ): Promise<OrderAIPrediction> {
    const res = await apiClient.get<ApiResponse<OrderAIPrediction>>(`/ai/predict/order/${orderId}`, {
      params,
    })
    return res.data.data
  },

  async weatherRoute(data: { weather_condition: string; distance_km: number; num_stops: number }) {
    const res = await apiClient.post<ApiResponse<{
      weather_condition: string
      impact_severity: string
      adjusted_eta_minutes: number
      delay_factor: number
      advice: string
    }>>('/ai/predict/weather-route', data)
    return res.data.data
  },
}
