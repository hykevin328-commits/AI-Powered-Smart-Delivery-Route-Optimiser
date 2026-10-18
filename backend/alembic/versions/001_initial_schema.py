"""Initial schema – all tables

Revision ID: 001_initial
Revises:
Create Date: 2025-01-01 00:00:00.000000

Creates all application tables in dependency order:
  users → customers → vehicles → delivery_orders
  → delivery_assignments → delivery_status_logs
  → route_histories → route_analytics → traffic_cache
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── ENUM types ────────────────────────────────────────────────────────────
    op.execute("CREATE TYPE user_role AS ENUM ('admin', 'delivery_partner')")
    op.execute("CREATE TYPE vehicle_type AS ENUM ('bike', 'scooter', 'car', 'van', 'truck')")
    op.execute("CREATE TYPE vehicle_status AS ENUM ('available', 'in_use', 'maintenance', 'retired')")
    op.execute(
        "CREATE TYPE order_status AS ENUM "
        "('pending', 'assigned', 'picked_up', 'in_transit', 'delivered', 'failed', 'cancelled')"
    )
    op.execute("CREATE TYPE order_priority AS ENUM ('low', 'normal', 'high', 'urgent')")
    op.execute(
        "CREATE TYPE assignment_status AS ENUM "
        "('active', 'completed', 'cancelled', 'reassigned')"
    )

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("admin", "delivery_partner", name="user_role"), nullable=False,
                  server_default="delivery_partner"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("licence_number", sa.String(50), nullable=True),
        sa.Column("refresh_token", sa.String(500), nullable=True),
        sa.Column("last_login_at", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role_active", "users", ["role", "is_active"])

    # ── customers ─────────────────────────────────────────────────────────────
    op.create_table(
        "customers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("address", sa.Text, nullable=False),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("country", sa.String(80), nullable=False, server_default="India"),
        sa.Column("latitude", sa.Float, nullable=True),
        sa.Column("longitude", sa.Float, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_customers_email", "customers", ["email"])
    op.create_index("ix_customers_phone", "customers", ["phone"])
    op.create_index("ix_customers_active", "customers", ["is_active"])

    # ── vehicles ──────────────────────────────────────────────────────────────
    op.create_table(
        "vehicles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("registration_number", sa.String(30), nullable=False, unique=True),
        sa.Column("make", sa.String(60), nullable=True),
        sa.Column("model", sa.String(60), nullable=True),
        sa.Column("year", sa.Integer, nullable=True),
        sa.Column("color", sa.String(30), nullable=True),
        sa.Column("vehicle_type", sa.Enum("bike", "scooter", "car", "van", "truck", name="vehicle_type"),
                  nullable=False, server_default="van"),
        sa.Column("status", sa.Enum("available", "in_use", "maintenance", "retired", name="vehicle_status"),
                  nullable=False, server_default="available"),
        sa.Column("max_capacity_kg", sa.Float, nullable=False, server_default="500.0"),
        sa.Column("fuel_efficiency_l_per_100km", sa.Float, nullable=False, server_default="8.5"),
        sa.Column("is_electric", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("odometer_km", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_vehicles_status", "vehicles", ["status"])
    op.create_index("ix_vehicles_type_status", "vehicles", ["vehicle_type", "status"])

    # ── delivery_orders ───────────────────────────────────────────────────────
    op.create_table(
        "delivery_orders",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("order_number", sa.String(30), nullable=False, unique=True),
        sa.Column("status", sa.Enum("pending", "assigned", "picked_up", "in_transit", "delivered",
                                    "failed", "cancelled", name="order_status"),
                  nullable=False, server_default="pending"),
        sa.Column("priority", sa.Enum("low", "normal", "high", "urgent", name="order_priority"),
                  nullable=False, server_default="normal"),
        sa.Column("customer_id", UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="RESTRICT"),
                  nullable=False),
        sa.Column("delivery_address", sa.Text, nullable=False),
        sa.Column("delivery_city", sa.String(100), nullable=True),
        sa.Column("delivery_postal_code", sa.String(20), nullable=True),
        sa.Column("delivery_latitude", sa.Float, nullable=True),
        sa.Column("delivery_longitude", sa.Float, nullable=True),
        sa.Column("pickup_address", sa.Text, nullable=True),
        sa.Column("pickup_latitude", sa.Float, nullable=True),
        sa.Column("pickup_longitude", sa.Float, nullable=True),
        sa.Column("package_description", sa.String(255), nullable=True),
        sa.Column("weight_kg", sa.Float, nullable=True),
        sa.Column("special_instructions", sa.Text, nullable=True),
        sa.Column("scheduled_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivery_window_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivery_window_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("predicted_delay_minutes", sa.Float, nullable=True),
        sa.Column("predicted_priority_score", sa.Float, nullable=True),
        sa.Column("estimated_delivery_time_minutes", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_delivery_orders_order_number", "delivery_orders", ["order_number"])
    op.create_index("ix_delivery_orders_status", "delivery_orders", ["status"])
    op.create_index("ix_delivery_orders_customer_id", "delivery_orders", ["customer_id"])
    op.create_index("ix_orders_status_scheduled", "delivery_orders", ["status", "scheduled_date"])
    op.create_index("ix_orders_customer_status", "delivery_orders", ["customer_id", "status"])

    # ── delivery_assignments ──────────────────────────────────────────────────
    op.create_table(
        "delivery_assignments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("order_id", UUID(as_uuid=True), sa.ForeignKey("delivery_orders.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("delivery_partner_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"),
                  nullable=False),
        sa.Column("vehicle_id", UUID(as_uuid=True), sa.ForeignKey("vehicles.id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("status", sa.Enum("active", "completed", "cancelled", "reassigned",
                                    name="assignment_status"), nullable=False, server_default="active"),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sequence_number", sa.Integer, nullable=False, server_default="1"),
        sa.Column("actual_distance_km", sa.Float, nullable=True),
        sa.Column("actual_fuel_litres", sa.Float, nullable=True),
        sa.Column("actual_travel_time_minutes", sa.Integer, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_delivery_assignments_order_id", "delivery_assignments", ["order_id"])
    op.create_index("ix_delivery_assignments_delivery_partner_id", "delivery_assignments", ["delivery_partner_id"])
    op.create_index("ix_assignments_partner_status", "delivery_assignments", ["delivery_partner_id", "status"])
    op.create_index("ix_assignments_order_active", "delivery_assignments", ["order_id", "status"])

    # ── delivery_status_logs ──────────────────────────────────────────────────
    op.create_table(
        "delivery_status_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("order_id", UUID(as_uuid=True), sa.ForeignKey("delivery_orders.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("from_status", sa.Enum("pending", "assigned", "picked_up", "in_transit", "delivered",
                                         "failed", "cancelled", name="order_status"), nullable=True),
        sa.Column("to_status", sa.Enum("pending", "assigned", "picked_up", "in_transit", "delivered",
                                       "failed", "cancelled", name="order_status"), nullable=False),
        sa.Column("changed_by", sa.String(120), nullable=True),
        sa.Column("latitude", sa.Float, nullable=True),
        sa.Column("longitude", sa.Float, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_delivery_status_logs_order_id", "delivery_status_logs", ["order_id"])
    op.create_index("ix_status_logs_order_timestamp", "delivery_status_logs", ["order_id", "timestamp"])

    # ── route_histories ───────────────────────────────────────────────────────
    op.create_table(
        "route_histories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("delivery_partner_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"),
                  nullable=False),
        sa.Column("assignment_id", UUID(as_uuid=True),
                  sa.ForeignKey("delivery_assignments.id", ondelete="SET NULL"), nullable=True, unique=True),
        sa.Column("route_date", sa.Date, nullable=False),
        sa.Column("total_stops", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_distance_km", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("total_travel_time_minutes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("fuel_consumed_litres", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("fuel_saved_litres", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("co2_emitted_kg", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("co2_saved_kg", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("algorithm_used", sa.Text, nullable=True),
        sa.Column("optimisation_time_ms", sa.Integer, nullable=True),
        sa.Column("route_efficiency_pct", sa.Float, nullable=True),
        sa.Column("waypoints", JSONB, nullable=True),
        sa.Column("route_polyline", sa.Text, nullable=True),
        sa.Column("traffic_factor", sa.Float, nullable=True),
        sa.Column("weather_condition", sa.Text, nullable=True),
        sa.Column("deliveries_completed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("deliveries_failed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_route_histories_delivery_partner_id", "route_histories", ["delivery_partner_id"])
    op.create_index("ix_route_histories_date", "route_histories", ["route_date"])
    op.create_index("ix_route_histories_partner_date", "route_histories", ["delivery_partner_id", "route_date"])

    # ── route_analytics ───────────────────────────────────────────────────────
    op.create_table(
        "route_analytics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("analytics_date", sa.Date, nullable=False),
        sa.Column("delivery_partner_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("period_type", sa.String(10), nullable=False, server_default="daily"),
        sa.Column("total_distance_km", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("avg_distance_per_delivery_km", sa.Float, nullable=True),
        sa.Column("fuel_consumed_litres", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("fuel_saved_litres", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("co2_emitted_kg", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("co2_saved_kg", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("total_deliveries", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completed_deliveries", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failed_deliveries", sa.Integer, nullable=False, server_default="0"),
        sa.Column("on_time_deliveries", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completion_rate_pct", sa.Float, nullable=True),
        sa.Column("avg_delivery_time_minutes", sa.Float, nullable=True),
        sa.Column("total_travel_time_minutes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("route_efficiency_pct", sa.Float, nullable=True),
        sa.Column("routes_optimised", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("analytics_date", "delivery_partner_id", "period_type",
                            name="uq_analytics_date_partner_period"),
    )
    op.create_index("ix_route_analytics_analytics_date", "route_analytics", ["analytics_date"])
    op.create_index("ix_route_analytics_delivery_partner_id", "route_analytics", ["delivery_partner_id"])
    op.create_index("ix_analytics_date_period", "route_analytics", ["analytics_date", "period_type"])

    # ── traffic_cache ─────────────────────────────────────────────────────────
    op.create_table(
        "traffic_cache",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("cache_key", sa.String(255), nullable=False, unique=True),
        sa.Column("provider", sa.String(50), nullable=False, server_default="google"),
        sa.Column("origin_lat", sa.Float, nullable=False),
        sa.Column("origin_lon", sa.Float, nullable=False),
        sa.Column("dest_lat", sa.Float, nullable=False),
        sa.Column("dest_lon", sa.Float, nullable=False),
        sa.Column("distance_km", sa.Float, nullable=False),
        sa.Column("duration_minutes", sa.Float, nullable=False),
        sa.Column("duration_in_traffic_minutes", sa.Float, nullable=True),
        sa.Column("congestion_level", sa.String(20), nullable=True),
        sa.Column("traffic_factor", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("raw_data", JSONB, nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_traffic_cache_cache_key", "traffic_cache", ["cache_key"])
    op.create_index("ix_traffic_cache_expires_at", "traffic_cache", ["expires_at"])
    op.create_index("ix_traffic_cache_coords", "traffic_cache",
                    ["origin_lat", "origin_lon", "dest_lat", "dest_lon"])

    # ── updated_at trigger function (auto-update on row change) ───────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    for tbl in [
        "users", "customers", "vehicles", "delivery_orders",
        "delivery_assignments", "delivery_status_logs",
        "route_histories", "route_analytics", "traffic_cache",
    ]:
        op.execute(f"""
            CREATE TRIGGER trg_{tbl}_updated_at
            BEFORE UPDATE ON {tbl}
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    tables = [
        "traffic_cache", "route_analytics", "route_histories",
        "delivery_status_logs", "delivery_assignments",
        "delivery_orders", "vehicles", "customers", "users",
    ]
    for tbl in tables:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{tbl}_updated_at ON {tbl}")
        op.drop_table(tbl)

    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    for enum in [
        "assignment_status", "order_priority", "order_status",
        "vehicle_status", "vehicle_type", "user_role",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum}")
