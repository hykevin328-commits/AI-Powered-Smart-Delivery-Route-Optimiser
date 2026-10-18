"""
Import all models here so Alembic's autogenerate can discover them.
"""
from app.models.user import User, UserRole                          # noqa: F401
from app.models.customer import Customer                            # noqa: F401
from app.models.vehicle import Vehicle, VehicleType, VehicleStatus  # noqa: F401
from app.models.delivery_order import DeliveryOrder, OrderStatus, OrderPriority  # noqa: F401
from app.models.delivery_assignment import DeliveryAssignment, AssignmentStatus  # noqa: F401
from app.models.route_history import RouteHistory                   # noqa: F401
from app.models.delivery_status import DeliveryStatusLog            # noqa: F401
from app.models.traffic_cache import TrafficCache                   # noqa: F401
from app.models.route_analytics import RouteAnalytics               # noqa: F401
