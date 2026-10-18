import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from '@/components/layout/Layout'
import ProtectedRoute from '@/components/layout/ProtectedRoute'

// Auth
import LoginPage    from '@/pages/auth/LoginPage'
import RegisterPage from '@/pages/auth/RegisterPage'

// App pages
import DashboardPage    from '@/pages/DashboardPage'
import OrdersPage       from '@/pages/orders/OrdersPage'
import OrderDetailPage  from '@/pages/orders/OrderDetailPage'
import CreateOrderPage  from '@/pages/orders/CreateOrderPage'
import CustomersPage    from '@/pages/customers/CustomersPage'
import CustomerDetail   from '@/pages/customers/CustomerDetailPage'
import CreateCustomerPage from '@/pages/customers/CreateCustomerPage'
import VehiclesPage     from '@/pages/VehiclesPage'
import RouteOptimizerPage from '@/pages/RouteOptimizerPage'
import AnalyticsPage    from '@/pages/AnalyticsPage'
import AIPredictionsPage from '@/pages/AIPredictionsPage'

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login"    element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Protected */}
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard"  element={<DashboardPage />} />

          <Route path="orders"         element={<OrdersPage />} />
          <Route path="orders/new"     element={<CreateOrderPage />} />
          <Route path="orders/:id"     element={<OrderDetailPage />} />
          <Route path="orders/:id/edit" element={<CreateOrderPage />} />

          <Route path="customers"      element={<CustomersPage />} />
          <Route path="customers/new"  element={<CreateCustomerPage />} />
          <Route path="customers/:id"  element={<CustomerDetail />} />
          <Route path="customers/:id/edit" element={<CreateCustomerPage />} />

          <Route path="vehicles"   element={<VehiclesPage />} />
          <Route path="routes"     element={<RouteOptimizerPage />} />
          <Route path="analytics"  element={<AnalyticsPage />} />
          <Route path="ai"         element={<AIPredictionsPage />} />
        </Route>
      </Route>

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
