"""
Reusable async pagination helper for SQLAlchemy queries.
"""
from __future__ import annotations

from typing import Any, Generic, List, Optional, Tuple, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


async def paginate(
    db: AsyncSession,
    query: Select,
    page: int,
    page_size: int,
) -> Tuple[List[Any], int]:
    """
    Execute *query* with LIMIT/OFFSET and also run a COUNT query.

    Returns:
        (items, total_count)
    """
    # Count total matching rows
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total: int = total_result.scalar_one()

    # Fetch the requested page
    paginated_query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(paginated_query)
    items = result.scalars().all()

    return list(items), total
