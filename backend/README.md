# Smart Delivery Route Optimizer — Backend

Production-ready FastAPI backend for an AI-Powered Smart Delivery Route Optimizer.  
Built with **FastAPI**, **Supabase PostgreSQL**, **Google OR-Tools**, and a full AI prediction engine.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Project Structure](#2-project-structure)
3. [Tech Stack](#3-tech-stack)
4. [Prerequisites](#4-prerequisites)
5. [Quick Start (Local)](#5-quick-start-local)
6. [Environment Variables](#6-environment-variables)
7. [Database Setup & Migrations](#7-database-setup--migrations)
8. [Running the Server](#8-running-the-server)
9. [Docker Deployment](#9-docker-deployment)
10. [API Reference](#10-api-reference)
11. [WebSocket Protocol](#11-websocket-protocol)
12. [Route Optimization](#12-route-optimization)
13. [AI Predictions](#13-ai-predictions)
14. [Testing](#14-testing)
15. [Deploying to Cloud](#15-deploying-to-cloud)

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                     FastAPI Backend                       │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │  Auth    │  │ Delivery │  │  Route   │  │  AI    │  │
│  │  Module  │  │ Orders   │  │ Optimize │  │ Engine │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘  │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │ Analytics│  │ Traffic  │  │Geocoding │  │  WS    │  │
│  │ Service  │  │ Service  │  │ Service  │  │ Server │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘  │
│                                                          │
│  ┌──────────────────────┐   ┌──────────────────────┐    │
│  │  SQLAlchemy (async)  │   │   Redis (cache/TTL)  │    │
│  │  Supabase PostgreSQL │   │                      │    │
│  └──────────────────────┘   └──────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Project Structure

```
backend/
├── app/
│   ├── api/                    # REST route handlers
│   │   ├── orders.py           # Delivery order CRUD + assignment
│   │   ├── assignments.py      # Delivery assignment management
│   │   ├── customers.py        # Customer management
│   │   ├── vehicles.py         # Fleet management
│   │   ├── routes.py           # Route optimization endpoints
│   │   ├── maps.py             # Geocoding endpoints
│   │   ├── predictions.py      # AI prediction endpoints
│   │   ├── traffic.py          # Live traffic endpoints
│   │   └── analytics.py        # Dashboard & analytics
│   │
│   ├── auth/                   # Authentication module
│   │   ├── jwt_handler.py      # JWT create / decode / rotate
│   │   ├── password.py         # bcrypt hashing
│   │   ├── service.py          # Auth business logic
│   │   └── router.py           # Auth API routes
│   │
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── customer.py
│   │   ├── vehicle.py
│   │   ├── delivery_order.py
│   │   ├── delivery_assignment.py
│   │   ├── route_history.py
│   │   ├── delivery_status.py
│   │   ├── traffic_cache.py
│   │   └── route_analytics.py
│   │
│   ├── schemas/                # Pydantic v2 request/response schemas
│   │
│   ├── services/               # Business logic services
│   │   ├── order_service.py
│   │   ├── customer_service.py
│   │   ├── traffic_service.py
│   │   ├── analytics_service.py
│   │   └── geocoding_service.py
│   │
│   ├── optimization/           # OR-Tools route optimization
│   │   ├── distance_matrix.py  # Haversine + traffic matrix builder
│   │   ├── tsp_solver.py       # Single-vehicle TSP solver
│   │   ├── vrp_solver.py       # Multi-vehicle VRP solver
│   │   └── route_optimizer.py  # High-level orchestrator
│   │
│   ├── ai/                     # AI prediction engine
│   │   ├── feature_engineering.py
│   │   └── predictor.py        # Delay / traffic / fuel / carbon / priority
│   │
│   ├── websocket/              # Live WebSocket updates
│   │   ├── connection_manager.py
│   │   └── router.py
│   │
│   ├── config/                 # App configuration
│   │   ├── settings.py         # Pydantic Settings (env-driven)
│   │   ├── database.py         # Async SQLAlchemy engine + get_db
│   │   ├── redis_client.py     # Redis async client
│   │   └── logging.py          # Structlog setup
│   │
│   ├── utils/                  # Shared utilities
│   │   ├── exceptions.py       # Exception hierarchy
│   │   ├── exception_handlers.py
│   │   ├── response.py         # Standardised response envelope
│   │   ├── dependencies.py     # FastAPI deps (auth, pagination)
│   │   ├── helpers.py          # Haversine, fuel/CO2 calc, etc.
│   │   └── pagination.py       # Async paginate helper
│   │
│   └── main.py                 # App factory + lifespan + middleware
│
├── alembic/                    # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial_schema.py
│
├── tests/                      # Pytest test suite
├── alembic.ini
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 3. Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.111 + Uvicorn |
| Database | Supabase PostgreSQL + SQLAlchemy 2 (async) |
| Migrations | Alembic |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Route Optimization | Google OR-Tools 9.10 |
| Cache | Redis 7 (redis-py async) |
| Geocoding | Google Maps / OpenRouteService / Nominatim |
| Traffic | Google Distance Matrix API / OpenRouteService |
| AI Engine | Pure Python + scikit-learn (optional upgrade) |
| WebSocket | FastAPI native + starlette |
| Logging | structlog (JSON in production) |
| Validation | Pydantic v2 |
| Containerisation | Docker + docker-compose |

---

## 4. Prerequisites

- Python 3.11+
- PostgreSQL 14+ (or a Supabase project)
- Redis 7+ (optional but recommended)
- Google Maps API key (optional — falls back to Nominatim/Haversine)

---

## 5. Quick Start (Local)

```bash
# 1. Clone and enter the backend directory
cd backend

# 2. Create a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment template and fill in values
copy .env.example .env       # Windows
cp .env.example .env         # macOS / Linux

# 5. Run database migrations
alembic upgrade head

# 6. Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000/docs** for the Swagger UI.

---

## 6. Environment Variables

Copy `.env.example` to `.env` and set the following:

### Required

| Variable | Description |
|---|---|
| `SECRET_KEY` | Min 32-char random string for JWT signing |
| `DATABASE_URL` | asyncpg URL: `postgresql+asyncpg://user:pass@host:5432/db` |
| `SYNC_DATABASE_URL` | psycopg2 URL for Alembic: `postgresql://user:pass@host:5432/db` |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anonymous key |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key |

### Optional (enables richer features)

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_MAPS_API_KEY` | — | Enables real traffic + geocoding |
| `OPENROUTESERVICE_API_KEY` | — | Alternative routing provider |
| `REDIS_URL` | `redis://localhost:6379/0` | Cache + Celery broker |
| `GEOCODING_PROVIDER` | `nominatim` | `google` / `openrouteservice` / `nominatim` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | JWT refresh token TTL |
| `TRAFFIC_CACHE_TTL` | `300` | Traffic cache TTL in seconds |
| `APP_ENV` | `development` | `development` / `production` / `testing` |

---

## 7. Database Setup & Migrations

### Using Supabase

1. Create a project at [supabase.com](https://supabase.com)
2. Copy the **Connection String** (Transaction mode) into `DATABASE_URL`
3. Copy the **Direct Connection** into `SYNC_DATABASE_URL`
4. Run migrations:

```bash
alembic upgrade head
```

### Common Alembic Commands

```bash
# Apply all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1

# Roll back all migrations
alembic downgrade base

# Auto-generate a new migration after model changes
alembic revision --autogenerate -m "add_new_column"

# View migration history
alembic history --verbose

# Show current revision
alembic current
```

---

## 8. Running the Server

### Development (with auto-reload)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production (multi-worker)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Health checks

```
GET /health   →  liveness probe
GET /ready    →  readiness probe (checks DB + Redis)
```

---

## 9. Docker Deployment

### Build and run with Docker Compose

```bash
# Copy and configure environment
cp .env.example .env

# Build and start all services (API + Redis + Nginx)
docker-compose up --build -d

# View logs
docker-compose logs -f api

# Stop all services
docker-compose down
```

Services started:
- **api** — FastAPI on port 8000
- **redis** — Redis on port 6379
- **celery_worker** — Background task worker
- **nginx** — Reverse proxy on ports 80/443

### Build image only

```bash
docker build -t route-optimizer-api:latest .
docker run -p 8000:8000 --env-file .env route-optimizer-api:latest
```

---

## 10. API Reference

All REST endpoints are prefixed with `/api/v1`.  
Full interactive documentation: **http://localhost:8000/docs**

### Authentication `/api/v1/auth`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | — | Create new account |
| POST | `/auth/login` | — | Login, receive JWT tokens |
| POST | `/auth/refresh` | — | Refresh access token |
| POST | `/auth/logout` | Bearer | Invalidate refresh token |
| GET | `/auth/me` | Bearer | Get own profile |
| PUT | `/auth/me` | Bearer | Update profile |
| POST | `/auth/me/change-password` | Bearer | Change password |
| GET | `/auth/users` | Admin | List all users |
| PUT | `/auth/users/{id}/deactivate` | Admin | Deactivate user |
| PUT | `/auth/users/{id}/activate` | Admin | Activate user |

**Register example:**
```json
POST /api/v1/auth/register
{
  "full_name": "Ravi Kumar",
  "email": "ravi@example.com",
  "password": "Secure123",
  "role": "delivery_partner"
}
```

**Login response:**
```json
{
  "success": true,
  "data": {
    "tokens": {
      "access_token": "eyJ...",
      "refresh_token": "eyJ...",
      "token_type": "bearer",
      "expires_in": 1800
    },
    "user": { "id": "...", "role": "delivery_partner", ... }
  }
}
```

---

### Delivery Orders `/api/v1/orders`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/orders` | Partner+ | List orders (paginated, filterable) |
| POST | `/orders` | Admin | Create order |
| GET | `/orders/today` | Partner+ | Today's scheduled orders |
| GET | `/orders/{id}` | Partner+ | Get order detail |
| PUT | `/orders/{id}` | Admin | Update order |
| DELETE | `/orders/{id}` | Admin | Delete order (PENDING only) |
| POST | `/orders/assign` | Admin | Assign orders to partner |
| PATCH | `/orders/{id}/status` | Partner+ | Update delivery status |
| POST | `/orders/{id}/complete` | Partner+ | Mark as delivered |
| GET | `/orders/{id}/status-history` | Partner+ | Full audit trail |

**Status transition rules:**
```
PENDING → ASSIGNED → PICKED_UP → IN_TRANSIT → DELIVERED
                                             ↘ FAILED → PENDING
Any state → CANCELLED
```

**Assign orders example:**
```json
POST /api/v1/orders/assign
{
  "order_ids": ["uuid-1", "uuid-2", "uuid-3"],
  "delivery_partner_id": "partner-uuid",
  "vehicle_id": "vehicle-uuid"
}
```

---

### Customer Management `/api/v1/customers`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/customers` | Partner+ | List customers (search by name/phone/email) |
| POST | `/customers` | Admin | Create customer |
| GET | `/customers/{id}` | Partner+ | Customer detail |
| PUT | `/customers/{id}` | Admin | Update customer |
| DELETE | `/customers/{id}` | Admin | Soft-delete (deactivate) |
| DELETE | `/customers/{id}/permanent` | Admin | Hard-delete (no orders) |
| GET | `/customers/{id}/orders` | Partner+ | Delivery history |
| GET | `/customers/{id}/stats` | Partner+ | Delivery statistics |

---

### Vehicles `/api/v1/vehicles`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/vehicles` | Partner+ | List fleet |
| POST | `/vehicles` | Admin | Add vehicle |
| GET | `/vehicles/{id}` | Partner+ | Vehicle detail |
| PUT | `/vehicles/{id}` | Admin | Update vehicle |
| DELETE | `/vehicles/{id}` | Admin | Remove vehicle |

---

### Route Optimization `/api/v1/routes`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/routes/optimize` | Partner+ | Optimize delivery route (TSP/VRP) |
| POST | `/routes/recalculate` | Partner+ | Live route recalculation |
| GET | `/routes/history` | Partner+ | Route history (paginated) |
| GET | `/routes/history/{id}` | Partner+ | Single route history |

**Optimize route (TSP — single vehicle):**
```json
POST /api/v1/routes/optimize
{
  "depot_latitude": 12.9716,
  "depot_longitude": 77.5946,
  "locations": [
    {"order_id": "...", "latitude": 12.9352, "longitude": 77.6245, "label": "Stop 1"},
    {"order_id": "...", "latitude": 12.9698, "longitude": 77.7500, "label": "Stop 2"},
    {"order_id": "...", "latitude": 13.0195, "longitude": 77.5989, "label": "Stop 3"}
  ],
  "return_to_depot": true,
  "time_limit_seconds": 30
}
```

**Optimize route (VRP — multiple vehicles):**
```json
POST /api/v1/routes/optimize
{
  "depot_latitude": 12.9716,
  "depot_longitude": 77.5946,
  "locations": [...],
  "vehicles": [
    {"delivery_partner_id": "p1-uuid", "max_capacity_kg": 300},
    {"delivery_partner_id": "p2-uuid", "max_capacity_kg": 500}
  ]
}
```

**Response:**
```json
{
  "algorithm": "TSP",
  "solver_status": "OPTIMAL",
  "optimization_time_ms": 142,
  "total_distance_km": 38.7,
  "total_travel_time_minutes": 58.1,
  "total_fuel_litres": 3.29,
  "total_co2_kg": 7.6,
  "fuel_saved_litres": 1.12,
  "co2_saved_kg": 2.59,
  "route_efficiency_pct": 25.4,
  "vehicle_routes": [
    {
      "vehicle_index": 0,
      "waypoints": [
        {"sequence": 0, "label": "Depot", "latitude": 12.9716, "longitude": 77.5946, "estimated_arrival_minutes": 0},
        {"sequence": 1, "label": "Stop 1", "distance_from_prev_km": 7.2, "estimated_arrival_minutes": 10.8},
        ...
      ],
      "total_distance_km": 38.7,
      "stop_count": 3
    }
  ]
}
```

---

### Maps & Geocoding `/api/v1/maps`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/maps/geocode` | Partner+ | Address → coordinates |
| POST | `/maps/reverse` | Partner+ | Coordinates → address |
| POST | `/maps/bulk-geocode` | Admin | Batch geocode |
| PUT | `/maps/geocode-order/{id}` | Admin | Geocode and store order address |
| PUT | `/maps/geocode-customer/{id}` | Admin | Geocode and store customer address |

---

### AI Predictions `/api/v1/ai`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/ai/predict/delay` | Partner+ | Predict delivery delay |
| POST | `/ai/predict/traffic` | Partner+ | Predict traffic congestion |
| POST | `/ai/predict/priority` | Partner+ | Recommend delivery priority |
| POST | `/ai/predict/fuel` | Partner+ | Predict fuel consumption |
| POST | `/ai/predict/carbon` | Partner+ | Estimate carbon emissions |
| POST | `/ai/predict/weather-route` | Partner+ | Weather-aware routing advice |
| GET | `/ai/predict/order/{id}` | Partner+ | Full AI analysis for an order |

**Delay prediction example:**
```json
POST /api/v1/ai/predict/delay
{
  "distance_km": 25.0,
  "num_stops": 8,
  "traffic_factor": 1.4,
  "congestion_level": "high",
  "weather_condition": "rain",
  "priority": "high"
}
```

---

### Traffic `/api/v1/traffic`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/traffic/segment` | Partner+ | Live traffic for a segment |
| POST | `/traffic/matrix` | Partner+ | Traffic matrix for locations |
| GET | `/traffic/cache` | Admin | View active cache entries |
| DELETE | `/traffic/cache` | Admin | Purge expired cache |

---

### Analytics `/api/v1/analytics`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/analytics/summary` | Partner+ | KPI dashboard cards |
| GET | `/analytics/time-series` | Partner+ | Trend charts (daily/weekly/monthly) |
| GET | `/analytics/partners` | Admin | Per-partner leaderboard |
| GET | `/analytics/dashboard` | Partner+ | Full dashboard (KPI + charts + partners) |
| POST | `/analytics/aggregate` | Admin | Trigger aggregation job |

**Query parameters for analytics:**
- `start_date` — ISO date (default: 30 days ago)
- `end_date` — ISO date (default: today)
- `period_type` — `daily` | `weekly` | `monthly`
- `partner_id` — filter by delivery partner (Admin only)

---

## 11. WebSocket Protocol

Connect with a valid JWT access token as a query parameter:

```
ws://localhost:8000/ws/partner/{partner_id}?token=<access_token>
ws://localhost:8000/ws/admin?token=<access_token>
ws://localhost:8000/ws/order/{order_id}?token=<access_token>
```

### Client → Server messages

```json
// Keepalive
{"event": "ping"}

// Send current GPS location (partner channel)
{"event": "location_update", "payload": {"lat": 12.97, "lon": 77.59, "speed_kmh": 35}}

// Subscribe to a specific order's updates
{"event": "subscribe_order", "payload": {"order_id": "uuid"}}
```

### Server → Client messages

```json
// Keepalive response
{"event": "pong"}

// Route was recalculated due to cancellation / new order
{"event": "route_update", "payload": {"assignment_id": "...", "updated_waypoints": [...]}}

// Order status changed
{"event": "order_status_changed", "payload": {"order_id": "...", "new_status": "delivered"}}

// New order assigned to partner
{"event": "order_assigned", "payload": {"order_id": "...", "order_number": "ORD-A3X9F2"}}

// Partner location update (admin channel)
{"event": "partner_location", "payload": {"delivery_partner_id": "...", "lat": 12.97, "lon": 77.59}}
```

---

## 12. Route Optimization

The optimization engine uses **Google OR-Tools** with two solver modes:

### TSP (1 vehicle)
Selected automatically when `vehicles` array is empty or has 1 entry.  
Uses `PATH_CHEAPEST_ARC` first solution + `GUIDED_LOCAL_SEARCH` metaheuristic.

### VRP (multi-vehicle)
Selected when `vehicles` array has 2+ entries. Supports:
- Per-vehicle capacity constraints (`max_capacity_kg`)
- Time-window constraints (`time_window_start` / `time_window_end` in minutes)
- Optional return-to-depot
- Penalty-based dropped-node handling when constraints cannot be satisfied

### Distance calculation
1. **With traffic API** — uses Google Distance Matrix or ORS durations
2. **Haversine fallback** — great-circle distance when no API key configured

### Fuel & CO₂ estimates
- Baseline: 8.5 L/100 km (configurable per vehicle)
- Traffic penalty: +50% of excess traffic factor applied to fuel
- Load penalty: +2% per 100 kg above 500 kg baseline
- CO₂: 2.31 kg per litre burned (petrol); 0.82 kg CO₂/kWh (India grid, EV)

---

## 13. AI Predictions

All AI predictions run as **stateless calculations** — no model training files required.  
The engine uses calibrated heuristics + cyclic time features that are accurate enough for production use and upgrade transparently to sklearn models when historical data accumulates.

### Delay Prediction
- Inputs: distance, stops, traffic factor, congestion, weather, priority, scheduled time
- Algorithm: base ETA × (traffic × weather × peak-hour) multipliers
- Output: `predicted_delay_minutes`, `delay_probability` (0–1)

### Traffic Prediction
- Inputs: hour, day-of-week, current traffic factor
- Algorithm: urban India peak-hour matrix + weighted blend with observed factor
- Output: `predicted_traffic_factor`, `congestion_level`, `best_departure_hour`

### Priority Recommendation
- Inputs: distance, weight, time-window, current priority, delay probability, hour
- Algorithm: weighted scoring (0–100) → label mapping
- Output: `priority_score`, `recommended_priority`

### Fuel & Carbon
- Inputs: distance, vehicle efficiency, traffic factor, load, electric flag
- Output: fuel litres / kWh, CO₂ kg, savings vs baseline, tree equivalent

---

## 14. Testing

```bash
# Install test dependencies (included in requirements.txt)
pip install pytest pytest-asyncio pytest-cov httpx

# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

Test structure:
```
tests/
├── conftest.py          # Fixtures: test DB, async client, test users
├── test_auth.py         # Register, login, refresh, logout
├── test_orders.py       # Order CRUD, assignment, status transitions
├── test_customers.py    # Customer CRUD, delivery history
├── test_optimization.py # TSP / VRP solver tests
└── test_ai.py           # AI prediction module tests
```

---

## 15. Deploying to Cloud

### Render

1. Create a new **Web Service** pointing to this repo
2. Set **Build Command**: `pip install -r requirements.txt`
3. Set **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add all environment variables from `.env.example`
5. Add a **Redis** add-on from the Render dashboard
6. Run migrations as a one-off job: `alembic upgrade head`

### Railway

```bash
railway login
railway init
railway add --plugin postgresql
railway add --plugin redis
railway up
```

Set `DATABASE_URL` and `REDIS_URL` from the Railway-provided values.

### Fly.io

```bash
fly launch
fly secrets set SECRET_KEY=your-key DATABASE_URL=postgresql://...
fly deploy
```

### Environment Notes for Production

- Set `APP_ENV=production` — hides `/docs`, `/redoc`, `/openapi.json`
- Set `DEBUG=false`
- Use a strong random `SECRET_KEY` (32+ chars)
- Configure `ALLOWED_ORIGINS` with your frontend domain
- Redis is optional but strongly recommended for traffic caching and performance

---

## Response Envelope

All API responses follow a consistent structure:

```json
{
  "success": true,
  "message": "Success",
  "data": { ... }
}
```

Paginated responses include a `meta` field:
```json
{
  "success": true,
  "message": "Success",
  "data": [...],
  "meta": {
    "total": 150,
    "page": 1,
    "page_size": 20,
    "total_pages": 8
  }
}
```

Error responses:
```json
{
  "success": false,
  "error_code": "NOT_FOUND",
  "message": "Order not found"
}
```

---

## License

MIT — see [LICENSE](LICENSE) for details.
