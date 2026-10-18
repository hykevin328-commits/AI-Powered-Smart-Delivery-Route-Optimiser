import { useState, useCallback } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { MapContainer, TileLayer, Marker, Polyline, Popup, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import { Plus, Trash2, Play, RotateCcw, Route } from 'lucide-react'
import toast from 'react-hot-toast'
import { routesService } from '@/services/routes.service'
import type { DeliveryLocation, OptimizeRouteResponse, WaypointResult } from '@/types'
import { fmtNum } from '@/lib/utils'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

// Fix leaflet default icons
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl:       'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl:     'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const depotIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34],
})

const stopIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34],
})

const optimizedIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34],
})

function MapClickHandler({ onMapClick }: { onMapClick: (lat: number, lon: number) => void }) {
  useMapEvents({ click: e => onMapClick(e.latlng.lat, e.latlng.lng) })
  return null
}

export default function RouteOptimizerPage() {
  const [depot,     setDepot]     = useState({ lat: 12.9716, lon: 77.5946 })
  const [locations, setLocations] = useState<DeliveryLocation[]>([])
  const [clickMode, setClickMode] = useState<'depot' | 'stop' | null>(null)
  const [result,    setResult]    = useState<OptimizeRouteResponse | null>(null)

  const optimizeMutation = useMutation({
    mutationFn: () =>
      routesService.optimize({
        depot_latitude:  depot.lat,
        depot_longitude: depot.lon,
        locations,
        return_to_depot: true,
        time_limit_seconds: 30,
      }),
    onSuccess: (data) => {
      setResult(data)
      toast.success(`Route optimised! ${data.solver_status} — ${fmtNum(data.total_distance_km)} km`)
    },
    onError: () => toast.error('Optimization failed. Need at least 1 stop.'),
  })

  const handleMapClick = useCallback((lat: number, lon: number) => {
    if (clickMode === 'depot') {
      setDepot({ lat, lon })
      setClickMode(null)
      toast.success('Depot location set')
    } else if (clickMode === 'stop') {
      const label = `Stop ${locations.length + 1}`
      setLocations(prev => [...prev, { latitude: lat, longitude: lon, label }])
      toast.success(`${label} added`)
    }
  }, [clickMode, locations.length])

  const removeLocation = (i: number) => setLocations(prev => prev.filter((_, idx) => idx !== i))
  const reset = () => { setLocations([]); setResult(null) }

  const routePolyline: [number, number][] = result
    ? result.vehicle_routes[0]?.waypoints.map(w => [w.latitude, w.longitude] as [number, number])
    : []

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Route Optimizer</h1>
          <p className="text-sm text-gray-500">Click the map to set depot and add delivery stops</p>
        </div>
        <div className="flex gap-2">
          <button onClick={reset} className="btn-secondary btn-sm"><RotateCcw className="h-4 w-4" /> Reset</button>
          <button onClick={() => optimizeMutation.mutate()} className="btn-primary btn-sm" disabled={locations.length === 0 || optimizeMutation.isPending}>
            {optimizeMutation.isPending ? <LoadingSpinner size="sm" /> : <><Play className="h-4 w-4" /> Optimize</>}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Map */}
        <div className="xl:col-span-2 h-[500px] rounded-xl overflow-hidden border border-gray-200 shadow-card">
          <MapContainer center={[depot.lat, depot.lon]} zoom={12} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://osm.org/copyright">OpenStreetMap</a>'
            />
            <MapClickHandler onMapClick={handleMapClick} />

            {/* Depot marker */}
            <Marker position={[depot.lat, depot.lon]} icon={depotIcon}>
              <Popup>🏭 Depot (Start)</Popup>
            </Marker>

            {/* Stop markers */}
            {locations.map((loc, i) => (
              <Marker key={i} position={[loc.latitude, loc.longitude]} icon={result ? optimizedIcon : stopIcon}>
                <Popup>{loc.label ?? `Stop ${i + 1}`}</Popup>
              </Marker>
            ))}

            {/* Optimized route polyline */}
            {routePolyline.length > 1 && (
              <Polyline positions={routePolyline} color="#2563eb" weight={3} dashArray="8 4" />
            )}
          </MapContainer>
        </div>

        {/* Controls & Results */}
        <div className="space-y-4">
          {/* Map controls */}
          <div className="card card-body space-y-3">
            <h2 className="font-semibold text-gray-800">Map Controls</h2>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setClickMode(clickMode === 'depot' ? null : 'depot')}
                className={clickMode === 'depot' ? 'btn-primary btn-sm' : 'btn-secondary btn-sm'}>
                📍 Set Depot
              </button>
              <button
                onClick={() => setClickMode(clickMode === 'stop' ? null : 'stop')}
                className={clickMode === 'stop' ? 'btn-primary btn-sm' : 'btn-secondary btn-sm'}>
                <Plus className="h-4 w-4" /> Add Stop
              </button>
            </div>
            {clickMode && (
              <p className="text-xs text-blue-600 bg-blue-50 rounded p-2">
                Click on the map to {clickMode === 'depot' ? 'set the depot location' : 'add a delivery stop'}
              </p>
            )}
            <div className="text-xs text-gray-500">
              <p>Depot: {depot.lat.toFixed(5)}, {depot.lon.toFixed(5)}</p>
              <p>{locations.length} stop(s) added</p>
            </div>
          </div>

          {/* Stop list */}
          {locations.length > 0 && (
            <div className="card card-body space-y-2">
              <h2 className="font-semibold text-gray-800">Stops ({locations.length})</h2>
              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {locations.map((loc, i) => (
                  <div key={i} className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2 text-sm">
                    <span className="font-medium">{loc.label ?? `Stop ${i + 1}`}</span>
                    <button onClick={() => removeLocation(i)} className="text-red-400 hover:text-red-600 ml-2">
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Result */}
          {result && (
            <div className="card card-body space-y-3">
              <div className="flex items-center gap-2">
                <Route className="h-4 w-4 text-primary-600" />
                <h2 className="font-semibold text-gray-800">Result — {result.algorithm}</h2>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { label: 'Distance',   value: `${fmtNum(result.total_distance_km)} km` },
                  { label: 'Time',       value: `${fmtNum(result.total_travel_time_minutes)} min` },
                  { label: 'Fuel',       value: `${fmtNum(result.total_fuel_litres)} L` },
                  { label: 'CO₂',        value: `${fmtNum(result.total_co2_kg)} kg` },
                  { label: 'Fuel Saved', value: `${fmtNum(result.fuel_saved_litres)} L` },
                  { label: 'Efficiency', value: `${fmtNum(result.route_efficiency_pct)}%` },
                ].map(m => (
                  <div key={m.label} className="bg-gray-50 rounded-lg p-2 text-center">
                    <p className="text-xs text-gray-400">{m.label}</p>
                    <p className="font-bold text-gray-900 text-sm">{m.value}</p>
                  </div>
                ))}
              </div>

              {/* Waypoint sequence */}
              {result.vehicle_routes[0]?.waypoints && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 mb-1.5">Optimized Sequence</p>
                  <div className="space-y-1 max-h-48 overflow-y-auto">
                    {result.vehicle_routes[0].waypoints.map((wp: WaypointResult, i: number) => (
                      <div key={i} className="flex items-center gap-2 text-xs bg-gray-50 rounded px-2 py-1.5">
                        <span className="bg-primary-600 text-white rounded-full h-5 w-5 flex items-center justify-center font-bold flex-shrink-0">{wp.sequence}</span>
                        <span className="flex-1 truncate">{wp.label ?? `Stop ${wp.sequence}`}</span>
                        {wp.estimated_arrival_minutes != null && (
                          <span className="text-gray-400 flex-shrink-0">+{Math.round(wp.estimated_arrival_minutes)} min</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
