import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, CheckCircle, BrainCircuit } from 'lucide-react'
import toast from 'react-hot-toast'
import { ordersService } from '@/services/orders.service'
import { aiService } from '@/services/ai.service'
import { orderStatusClass, priorityClass, fmtDateTime, capitalize, fmtNum } from '@/lib/utils'
import type { OrderStatus } from '@/types'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import Modal from '@/components/ui/Modal'

const NEXT_STATUSES: Record<OrderStatus, OrderStatus[]> = {
  pending:    ['assigned', 'cancelled'],
  assigned:   ['picked_up', 'cancelled'],
  picked_up:  ['in_transit', 'cancelled'],
  in_transit: ['delivered', 'failed', 'cancelled'],
  failed:     ['pending', 'cancelled'],
  delivered:  [],
  cancelled:  [],
}

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>()
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [statusModal, setStatusModal] = useState(false)
  const [newStatus, setNewStatus] = useState<OrderStatus | null>(null)
  const [notes, setNotes] = useState('')

  const { data: order, isLoading } = useQuery({
    queryKey: ['order', id],
    queryFn: () => ordersService.get(id!),
    enabled: !!id,
  })

  const { data: logs } = useQuery({
    queryKey: ['order-logs', id],
    queryFn: () => ordersService.getStatusHistory(id!),
    enabled: !!id,
  })

  const { data: aiData, isLoading: aiLoading, refetch: runAI } = useQuery({
    queryKey: ['ai-order', id],
    queryFn: () => aiService.analyzeOrder(id!),
    enabled: false,
  })

  const statusMutation = useMutation({
    mutationFn: () => ordersService.updateStatus(id!, newStatus!, notes),
    onSuccess: () => {
      toast.success(`Status updated to ${newStatus}`)
      qc.invalidateQueries({ queryKey: ['order', id] })
      qc.invalidateQueries({ queryKey: ['order-logs', id] })
      setStatusModal(false)
      setNotes('')
    },
  })

  if (isLoading) return <div className="flex justify-center py-20"><LoadingSpinner size="lg" /></div>
  if (!order) return <div className="text-center py-20 text-gray-500">Order not found.</div>

  const nextStatuses = NEXT_STATUSES[order.status] ?? []

  return (
    <div className="space-y-5 max-w-4xl">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="btn-ghost p-2 rounded-lg"><ArrowLeft className="h-4 w-4" /></button>
        <div>
          <h1 className="text-xl font-bold text-gray-900">{order.order_number}</h1>
          <span className={`${orderStatusClass(order.status)} mt-0.5`}>{capitalize(order.status)}</span>
        </div>
        <div className="ml-auto flex gap-2">
          <button onClick={() => runAI()} className="btn-secondary btn-sm" disabled={aiLoading}>
            <BrainCircuit className="h-4 w-4" /> {aiLoading ? 'Analyzing…' : 'AI Analysis'}
          </button>
          {nextStatuses.length > 0 && (
            <button onClick={() => setStatusModal(true)} className="btn-primary btn-sm">
              <CheckCircle className="h-4 w-4" /> Update Status
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Order details */}
        <div className="card card-body space-y-3">
          <h2 className="font-semibold text-gray-800">Order Details</h2>
          <Row label="Priority"><span className={priorityClass(order.priority)}>{capitalize(order.priority)}</span></Row>
          <Row label="Customer">{order.customer?.full_name ?? '—'}</Row>
          <Row label="Phone">{order.customer?.phone ?? '—'}</Row>
          <Row label="Package">{order.package_description ?? '—'}</Row>
          <Row label="Weight">{order.weight_kg ? `${order.weight_kg} kg` : '—'}</Row>
          <Row label="Scheduled">{fmtDateTime(order.scheduled_date)}</Row>
          <Row label="Delivered">{fmtDateTime(order.delivered_at)}</Row>
        </div>

        {/* Delivery location */}
        <div className="card card-body space-y-3">
          <h2 className="font-semibold text-gray-800">Delivery Location</h2>
          <Row label="Address">{order.delivery_address}</Row>
          <Row label="City">{order.delivery_city ?? '—'}</Row>
          <Row label="Coordinates">
            {order.delivery_latitude && order.delivery_longitude
              ? `${order.delivery_latitude.toFixed(5)}, ${order.delivery_longitude.toFixed(5)}`
              : '—'}
          </Row>
          {order.pickup_address && <Row label="Pickup">{order.pickup_address}</Row>}
          {order.special_instructions && <Row label="Instructions">{order.special_instructions}</Row>}
        </div>
      </div>

      {/* AI Analysis */}
      {aiData && (
        <div className="card card-body">
          <h2 className="font-semibold text-gray-800 mb-3">AI Analysis</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <Metric label="Delay" value={`${fmtNum(aiData.predicted_delay_minutes)} min`} />
            <Metric label="Delay Prob." value={`${Math.round(aiData.delay_probability * 100)}%`} />
            <Metric label="ETA" value={`${aiData.estimated_delivery_time_minutes} min`} />
            <Metric label="Fuel" value={`${fmtNum(aiData.predicted_fuel_litres)} L`} />
          </div>
          <div className="bg-blue-50 rounded-lg p-3 text-sm text-blue-800">
            <strong>Recommendation:</strong> {aiData.recommendation}
          </div>
        </div>
      )}

      {/* Status history */}
      {logs && logs.length > 0 && (
        <div className="card card-body">
          <h2 className="font-semibold text-gray-800 mb-3">Status History</h2>
          <div className="space-y-3">
            {logs.map((log) => (
              <div key={log.id} className="flex items-start gap-3">
                <div className="h-2 w-2 rounded-full bg-primary-500 mt-1.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-gray-800">
                    {log.from_status ? `${capitalize(log.from_status)} → ` : ''}{capitalize(log.to_status)}
                  </p>
                  <p className="text-xs text-gray-400">{fmtDateTime(log.timestamp)} {log.changed_by ? `· by ${log.changed_by}` : ''}</p>
                  {log.notes && <p className="text-xs text-gray-500 mt-0.5">{log.notes}</p>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Status update modal */}
      <Modal
        open={statusModal}
        onClose={() => setStatusModal(false)}
        title="Update Delivery Status"
        footer={
          <>
            <button className="btn-secondary btn-sm" onClick={() => setStatusModal(false)}>Cancel</button>
            <button className="btn-primary btn-sm" onClick={() => statusMutation.mutate()} disabled={!newStatus || statusMutation.isPending}>
              {statusMutation.isPending ? 'Updating…' : 'Update'}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="label">New Status</label>
            <select className="input" value={newStatus ?? ''} onChange={e => setNewStatus(e.target.value as OrderStatus)}>
              <option value="">Select status</option>
              {nextStatuses.map(s => <option key={s} value={s}>{capitalize(s)}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Notes (optional)</label>
            <textarea className="input" rows={3} placeholder="Add notes…" value={notes} onChange={e => setNotes(e.target.value)} />
          </div>
        </div>
      </Modal>
    </div>
  )
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex gap-2 text-sm">
      <span className="text-gray-400 w-28 flex-shrink-0">{label}</span>
      <span className="text-gray-800">{children}</span>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-50 rounded-lg p-3 text-center">
      <p className="text-xs text-gray-400">{label}</p>
      <p className="text-lg font-bold text-gray-900 mt-0.5">{value}</p>
    </div>
  )
}
