// ─────────────────────────────────────────────────────────────────────────────
// Shared API envelope
// ─────────────────────────────────────────────────────────────────────────────

export interface ApiResponse<T = unknown> {
  success: boolean
  message: string
  data: T
  meta?: PaginationMeta
}

export interface PaginationMeta {
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  meta: PaginationMeta
}

// ─────────────────────────────────────────────────────────────────────────────
// Auth
// ─────────────────────────────────────────────────────────────────────────────

export type UserRole = 'admin' | 'delivery_partner'

export interface User {
  id: string
  full_name: string
  email: string
  phone: string | null
  role: UserRole
  is_active: boolean
  is_verified: boolean
  avatar_url: string | null
  address: string | null
  licence_number: string | null
  last_login_at: string | null
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  full_name: string
  email: string
  password: string
  phone?: string
  role?: UserRole
}

// ─────────────────────────────────────────────────────────────────────────────
// Customer
// ─────────────────────────────────────────────────────────────────────────────

export interface Customer {
  id: string
  full_name: string
  email: string | null
  phone: string
  address: string
  city: string | null
  state: string | null
  postal_code: string | null
  country: string
  latitude: number | null
  longitude: number | null
  is_active: boolean
  notes: string | null
  created_at: string
  updated_at: string
}

export interface CustomerCreate {
  full_name: string
  email?: string
  phone: string
  address: string
  city?: string
  state?: string
  postal_code?: string
  country?: string
  latitude?: number
  longitude?: number
  notes?: string
}

// ─────────────────────────────────────────────────────────────────────────────
// Vehicle
// ─────────────────────────────────────────────────────────────────────────────

export type VehicleType = 'bike' | 'scooter' | 'car' | 'van' | 'truck'
export type VehicleStatus = 'available' | 'in_use' | 'maintenance' | 'retired'

export interface Vehicle {
  id: string
  registration_number: string
  make: string | null
  model: string | null
  year: number | null
  color: string | null
  vehicle_type: VehicleType
  status: VehicleStatus
  max_capacity_kg: number
  fuel_efficiency_l_per_100km: number
  is_electric: boolean
  odometer_km: number
  created_at: string
  updated_at: string
}

// ─────────────────────────────────────────────────────────────────────────────
// Delivery Order
// ─────────────────────────────────────────────────────────────────────────────

export type OrderStatus =
  | 'pending'
  | 'assigned'
  | 'picked_up'
  | 'in_transit'
  | 'delivered'
  | 'failed'
  | 'cancelled'

export type OrderPriority = 'low' | 'normal' | 'high' | 'urgent'

export interface CustomerSummary {
  id: string
  full_name: string
  phone: string
  email: string | null
}

export interface DeliveryOrder {
  id: string
  order_number: string
  status: OrderStatus
  priority: OrderPriority
  customer_id: string
  customer: CustomerSummary | null
  delivery_address: string
  delivery_city: string | null
  delivery_postal_code: string | null
  delivery_latitude: number | null
  delivery_longitude: number | null
  pickup_address: string | null
  pickup_latitude: number | null
  pickup_longitude: number | null
  package_description: string | null
  weight_kg: number | null
  special_instructions: string | null
  scheduled_date: string | null
  delivery_window_start: string | null
  delivery_window_end: string | null
  delivered_at: string | null
  predicted_delay_minutes: number | null
  predicted_priority_score: number | null
  estimated_delivery_time_minutes: number | null
  created_at: string
  updated_at: string
}

export interface OrderCreate {
  customer_id: string
  delivery_address: string
  delivery_city?: string
  delivery_postal_code?: string
  delivery_latitude?: number
  delivery_longitude?: number
  pickup_address?: string
  pickup_latitude?: number
  pickup_longitude?: number
  package_description?: string
  weight_kg?: number
  special_instructions?: string
  priority?: OrderPriority
  scheduled_date?: string
  delivery_window_start?: string
  delivery_window_end?: string
}

export interface AssignOrderRequest {
  order_ids: string[]
  delivery_partner_id: string
  vehicle_id?: string
}

export interface StatusLog {
  id: string
  from_status: OrderStatus | null
  to_status: OrderStatus
  changed_by: string | null
  notes: string | null
  latitude: number | null
  longitude: number | null
  timestamp: string
}

// ─────────────────────────────────────────────────────────────────────────────
// Delivery Assignment
// ─────────────────────────────────────────────────────────────────────────────

export type AssignmentStatus = 'active' | 'completed' | 'cancelled' | 'reassigned'

export interface DeliveryAssignment {
  id: string
  order_id: string
  delivery_partner_id: string
  vehicle_id: string | null
  status: AssignmentStatus
  assigned_at: string
  completed_at: string | null
  sequence_number: number
  actual_distance_km: number | null
  actual_fuel_litres: number | null
  actual_travel_time_minutes: number | null
  notes: string | null
  order: DeliveryOrder | null
  vehicle: Vehicle | null
  created_at: string
  updated_at: string
}

// ─────────────────────────────────────────────────────────────────────────────
// Route Optimization
// ─────────────────────────────────────────────────────────────────────────────

export interface DeliveryLocation {
  order_id?: string
  label?: string
  latitude: number
  longitude: number
  service_time_minutes?: number
}

export interface VehicleConfig {
  vehicle_id?: string
  delivery_partner_id?: string
  max_capacity_kg?: number
  start_latitude?: number
  start_longitude?: number
}

export interface OptimizeRouteRequest {
  depot_latitude: number
  depot_longitude: number
  locations: DeliveryLocation[]
  vehicles?: VehicleConfig[]
  consider_traffic?: boolean
  return_to_depot?: boolean
  time_limit_seconds?: number
}

export interface WaypointResult {
  sequence: number
  order_id: string | null
  label: string | null
  latitude: number
  longitude: number
  estimated_arrival_minutes: number | null
  distance_from_prev_km: number | null
}

export interface VehicleRouteResult {
  vehicle_index: number
  vehicle_id: string | null
  delivery_partner_id: string | null
  waypoints: WaypointResult[]
  total_distance_km: number
  total_travel_time_minutes: number
  estimated_fuel_litres: number
  estimated_co2_kg: number
  stop_count: number
}

export interface OptimizeRouteResponse {
  algorithm: string
  solver_status: string
  optimization_time_ms: number
  total_distance_km: number
  total_travel_time_minutes: number
  total_fuel_litres: number
  total_co2_kg: number
  fuel_saved_litres: number | null
  co2_saved_kg: number | null
  route_efficiency_pct: number | null
  vehicle_routes: VehicleRouteResult[]
  route_coordinates: [number, number][] | null
}

// ─────────────────────────────────────────────────────────────────────────────
// Analytics
// ─────────────────────────────────────────────────────────────────────────────

export interface KPISummary {
  total_deliveries: number
  completed_deliveries: number
  failed_deliveries: number
  completion_rate_pct: number
  total_distance_km: number
  total_fuel_consumed_litres: number
  total_fuel_saved_litres: number
  total_co2_emitted_kg: number
  total_co2_saved_kg: number
  avg_delivery_time_minutes: number
  avg_route_efficiency_pct: number
  routes_optimised: number
}

export interface DailyDataPoint {
  date: string
  total_deliveries: number
  completed_deliveries: number
  total_distance_km: number
  fuel_consumed_litres: number
  fuel_saved_litres: number
  co2_emitted_kg: number
  co2_saved_kg: number
  avg_delivery_time_minutes: number | null
  route_efficiency_pct: number | null
}

export interface PartnerPerformance {
  delivery_partner_id: string
  partner_name: string
  total_deliveries: number
  completed_deliveries: number
  completion_rate_pct: number
  total_distance_km: number
  avg_delivery_time_minutes: number | null
  fuel_consumed_litres: number
  co2_emitted_kg: number
}

export interface DashboardData {
  kpi: KPISummary
  time_series: DailyDataPoint[]
  partner_performance: PartnerPerformance[] | null
}

// ─────────────────────────────────────────────────────────────────────────────
// AI Predictions
// ─────────────────────────────────────────────────────────────────────────────

export interface DelayPrediction {
  predicted_delay_minutes: number
  delay_probability: number
  base_estimated_minutes: number
  adjusted_estimated_minutes: number
  contributing_factors: {
    traffic: boolean
    weather: boolean
    peak_hours: boolean
  }
}

export interface FuelPrediction {
  is_electric: boolean
  fuel_litres: number
  co2_kg: number
  baseline_fuel_litres?: number
  fuel_saved_litres?: number
  energy_kwh?: number
}

export interface OrderAIPrediction {
  order_id: string
  predicted_delay_minutes: number
  delay_probability: number
  predicted_priority_score: number
  estimated_delivery_time_minutes: number
  predicted_fuel_litres: number
  predicted_co2_kg: number
  traffic_congestion_level: string
  weather_impact: string
  recommendation: string
}

// ─────────────────────────────────────────────────────────────────────────────
// Traffic
// ─────────────────────────────────────────────────────────────────────────────

export interface TrafficSegment {
  distance_km: number
  duration_minutes: number
  duration_in_traffic_minutes: number
  congestion_level: string
  traffic_factor: number
}

export interface TrafficResponse {
  origin: { latitude: number; longitude: number }
  destination: { latitude: number; longitude: number }
  segment: TrafficSegment
  provider: string
  cached: boolean
  fetched_at: string
}
