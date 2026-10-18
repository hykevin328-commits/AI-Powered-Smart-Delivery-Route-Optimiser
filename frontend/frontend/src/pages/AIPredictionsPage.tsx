import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { BrainCircuit, Zap, CloudRain, Gauge } from 'lucide-react'
import { aiService } from '@/services/ai.service'
import { fmtNum, congestionClass, capitalize } from '@/lib/utils'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

export default function AIPredictionsPage() {
  const [delayForm, setDelayForm] = useState({ distance_km: 20, num_stops: 5, traffic_factor: 1.0, weather_condition: 'clear', priority: 'normal' })
  const [fuelForm,  setFuelForm]  = useState({ distance_km: 20, traffic_factor: 1.0, load_kg: 0, is_electric: false })
  const [trafficForm, setTrafficForm] = useState({ hour: 9, day_of_week: 1, latitude: 12.97, longitude: 77.59, current_factor: 1.0 })
  const [weatherForm, setWeatherForm] = useState({ weather_condition: 'clear', distance_km: 20, num_stops: 5 })

  const delayMut   = useMutation({ mutationFn: () => aiService.predictDelay(delayForm) })
  const fuelMut    = useMutation({ mutationFn: () => aiService.predictFuel(fuelForm) })
  const trafficMut = useMutation({ mutationFn: () => aiService.predictTraffic(trafficForm) })
  const weatherMut = useMutation({ mutationFn: () => aiService.weatherRoute(weatherForm) })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900">AI Predictions</h1>
        <p className="text-sm text-gray-500">Real-time AI analysis for delivery planning</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Delay Prediction */}
        <PredictionCard title="Delay Prediction" icon={<Zap className="h-5 w-5 text-yellow-600" />} iconBg="bg-yellow-100"
          onRun={() => delayMut.mutate()} isLoading={delayMut.isPending}>
          <div className="space-y-3">
            <Field label="Distance (km)">
              <input type="number" className="input" value={delayForm.distance_km} onChange={e => setDelayForm(p => ({ ...p, distance_km: +e.target.value }))} />
            </Field>
            <Field label="Number of Stops">
              <input type="number" className="input" value={delayForm.num_stops} onChange={e => setDelayForm(p => ({ ...p, num_stops: +e.target.value }))} />
            </Field>
            <Field label="Traffic Factor">
              <input type="number" step="0.1" min="0.5" max="5" className="input" value={delayForm.traffic_factor} onChange={e => setDelayForm(p => ({ ...p, traffic_factor: +e.target.value }))} />
            </Field>
            <Field label="Weather">
              <select className="input" value={delayForm.weather_condition} onChange={e => setDelayForm(p => ({ ...p, weather_condition: e.target.value }))}>
                {['clear', 'rain', 'fog', 'thunderstorm', 'snow'].map(w => <option key={w} value={w}>{capitalize(w)}</option>)}
              </select>
            </Field>
            <Field label="Priority">
              <select className="input" value={delayForm.priority} onChange={e => setDelayForm(p => ({ ...p, priority: e.target.value }))}>
                {['low', 'normal', 'high', 'urgent'].map(p => <option key={p} value={p}>{capitalize(p)}</option>)}
              </select>
            </Field>
            {delayMut.data && (
              <div className="bg-yellow-50 rounded-lg p-3 mt-2 space-y-2">
                <ResultRow label="Predicted Delay"     value={`${fmtNum(delayMut.data.predicted_delay_minutes)} min`} />
                <ResultRow label="Delay Probability"   value={`${Math.round(delayMut.data.delay_probability * 100)}%`} />
                <ResultRow label="Base ETA"            value={`${fmtNum(delayMut.data.base_estimated_minutes)} min`} />
                <ResultRow label="Adjusted ETA"        value={`${fmtNum(delayMut.data.adjusted_estimated_minutes)} min`} />
              </div>
            )}
          </div>
        </PredictionCard>

        {/* Fuel Prediction */}
        <PredictionCard title="Fuel Consumption" icon={<Gauge className="h-5 w-5 text-orange-600" />} iconBg="bg-orange-100"
          onRun={() => fuelMut.mutate()} isLoading={fuelMut.isPending}>
          <div className="space-y-3">
            <Field label="Distance (km)">
              <input type="number" className="input" value={fuelForm.distance_km} onChange={e => setFuelForm(p => ({ ...p, distance_km: +e.target.value }))} />
            </Field>
            <Field label="Traffic Factor">
              <input type="number" step="0.1" min="0.5" max="5" className="input" value={fuelForm.traffic_factor} onChange={e => setFuelForm(p => ({ ...p, traffic_factor: +e.target.value }))} />
            </Field>
            <Field label="Load (kg)">
              <input type="number" className="input" value={fuelForm.load_kg} onChange={e => setFuelForm(p => ({ ...p, load_kg: +e.target.value }))} />
            </Field>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" checked={fuelForm.is_electric} onChange={e => setFuelForm(p => ({ ...p, is_electric: e.target.checked }))} />
              <span>Electric Vehicle</span>
            </label>
            {fuelMut.data && (
              <div className="bg-orange-50 rounded-lg p-3 mt-2 space-y-2">
                {fuelMut.data.is_electric ? (
                  <ResultRow label="Energy (kWh)" value={`${fmtNum(fuelMut.data.energy_kwh)} kWh`} />
                ) : (
                  <>
                    <ResultRow label="Fuel Consumed"  value={`${fmtNum(fuelMut.data.fuel_litres)} L`} />
                    <ResultRow label="Fuel Saved"     value={`${fmtNum(fuelMut.data.fuel_saved_litres)} L`} />
                  </>
                )}
                <ResultRow label="CO₂ Emitted" value={`${fmtNum(fuelMut.data.co2_kg)} kg`} />
              </div>
            )}
          </div>
        </PredictionCard>

        {/* Traffic Prediction */}
        <PredictionCard title="Traffic Forecast" icon={<BrainCircuit className="h-5 w-5 text-blue-600" />} iconBg="bg-blue-100"
          onRun={() => trafficMut.mutate()} isLoading={trafficMut.isPending}>
          <div className="space-y-3">
            <Field label="Hour (0-23)">
              <input type="number" min="0" max="23" className="input" value={trafficForm.hour} onChange={e => setTrafficForm(p => ({ ...p, hour: +e.target.value }))} />
            </Field>
            <Field label="Day of Week (0=Mon)">
              <select className="input" value={trafficForm.day_of_week} onChange={e => setTrafficForm(p => ({ ...p, day_of_week: +e.target.value }))}>
                {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((d, i) => <option key={i} value={i}>{d}</option>)}
              </select>
            </Field>
            <Field label="Current Factor">
              <input type="number" step="0.1" className="input" value={trafficForm.current_factor} onChange={e => setTrafficForm(p => ({ ...p, current_factor: +e.target.value }))} />
            </Field>
            {trafficMut.data && (
              <div className="bg-blue-50 rounded-lg p-3 mt-2 space-y-2">
                <ResultRow label="Traffic Factor"     value={fmtNum(trafficMut.data.predicted_traffic_factor)} />
                <ResultRow label="Congestion">
                  <span className={congestionClass(trafficMut.data.congestion_level)}>{capitalize(trafficMut.data.congestion_level)}</span>
                </ResultRow>
                <ResultRow label="Best Departure"    value={`${trafficMut.data.best_departure_hour}:00`} />
                <ResultRow label="Avoid Hours"       value={trafficMut.data.avoid_hours.map(h => `${h}:00`).join(', ')} />
              </div>
            )}
          </div>
        </PredictionCard>

        {/* Weather Routing */}
        <PredictionCard title="Weather Routing" icon={<CloudRain className="h-5 w-5 text-indigo-600" />} iconBg="bg-indigo-100"
          onRun={() => weatherMut.mutate()} isLoading={weatherMut.isPending}>
          <div className="space-y-3">
            <Field label="Weather Condition">
              <select className="input" value={weatherForm.weather_condition} onChange={e => setWeatherForm(p => ({ ...p, weather_condition: e.target.value }))}>
                {['clear', 'rain', 'drizzle', 'fog', 'thunderstorm', 'snow'].map(w => <option key={w} value={w}>{capitalize(w)}</option>)}
              </select>
            </Field>
            <Field label="Distance (km)">
              <input type="number" className="input" value={weatherForm.distance_km} onChange={e => setWeatherForm(p => ({ ...p, distance_km: +e.target.value }))} />
            </Field>
            <Field label="Number of Stops">
              <input type="number" className="input" value={weatherForm.num_stops} onChange={e => setWeatherForm(p => ({ ...p, num_stops: +e.target.value }))} />
            </Field>
            {weatherMut.data && (
              <div className="bg-indigo-50 rounded-lg p-3 mt-2 space-y-2">
                <ResultRow label="Impact"       value={capitalize(weatherMut.data.impact_severity)} />
                <ResultRow label="Delay Factor" value={`×${weatherMut.data.delay_factor}`} />
                <ResultRow label="Adjusted ETA" value={`${fmtNum(weatherMut.data.adjusted_eta_minutes)} min`} />
                <p className="text-xs text-indigo-700 pt-1">{weatherMut.data.advice}</p>
              </div>
            )}
          </div>
        </PredictionCard>
      </div>
    </div>
  )
}

function PredictionCard({ title, icon, iconBg, onRun, isLoading, children }: {
  title: string; icon: React.ReactNode; iconBg: string
  onRun: () => void; isLoading: boolean; children: React.ReactNode
}) {
  return (
    <div className="card">
      <div className="card-header flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`rounded-lg p-1.5 ${iconBg}`}>{icon}</div>
          <h2 className="font-semibold text-gray-800">{title}</h2>
        </div>
        <button className="btn-primary btn-sm" onClick={onRun} disabled={isLoading}>
          {isLoading ? <LoadingSpinner size="sm" /> : 'Predict'}
        </button>
      </div>
      <div className="card-body">{children}</div>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="label">{label}</label>
      {children}
    </div>
  )
}

function ResultRow({ label, value, children }: { label: string; value?: string; children?: React.ReactNode }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium text-gray-900">{children ?? value}</span>
    </div>
  )
}
