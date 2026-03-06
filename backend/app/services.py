from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models import ParseSession, Product as ResultItem
from app.normalization import (
    normalize_currency,
    parse_bool,
    parse_price,
)
from app.schemas import ResultFilters, ResultItemIn


class IngestStats(dict):
    total_received: int
    inserted: int
    duplicates_skipped: int


def create_session(
    db: Session,
    *,
    site_id: int,
    user_id: int,
    status: str,
    started_at,
    ended_at,
    processed_items,
) -> ParseSession:
    session = ParseSession(
        site_id=site_id,
        user_id=user_id,
        status=status,
        started_at=started_at,
        ended_at=ended_at,
        processed_items=processed_items,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session_or_404(db: Session, session_id: int) -> ParseSession:
    session = db.get(ParseSession, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сессия парсинга не найдена",
        )
    return session


def ingest_results(db: Session, session_id: int, items: list[ResultItemIn]) -> IngestStats:
    session = get_session_or_404(db, session_id)

    inserted = 0
    duplicates_skipped = 0
    seen_in_request: set[tuple[str, str]] = set()

    for item in items:
        name = item.name.strip()
        if not name:
            duplicates_skipped += 1
            continue

        dedupe_key = (item.external_id or "", name.lower())
        if dedupe_key in seen_in_request:
            duplicates_skipped += 1
            continue
        seen_in_request.add(dedupe_key)

        existing = None
        if item.external_id:
            existing = db.execute(
                select(ResultItem).where(
                    ResultItem.site_id == session.site_id,
                    ResultItem.external_id == item.external_id,
                )
            ).scalar_one_or_none()

        if existing is None:
            existing = db.execute(
                select(ResultItem).where(
                    ResultItem.site_id == session.site_id,
                    ResultItem.name == name,
                )
            ).scalar_one_or_none()

        price = parse_price(item.price)
        currency = normalize_currency(item.currency)
        in_stock = parse_bool(item.in_stock)
        category = item.category.strip() if item.category else None

        if existing is not None:
            existing.old_price = existing.price
            existing.price = price
            existing.currency = currency
            existing.category = category
            existing.in_stock = in_stock
            existing.updated_at = datetime.now(timezone.utc)
            duplicates_skipped += 1
            continue

        product = ResultItem(
            site_id=session.site_id,
            external_id=item.external_id,
            name=name,
            price=price,
            old_price=None,
            currency=currency,
            description=None,
            category=category,
            in_stock=in_stock,
            updated_at=datetime.now(timezone.utc),
        )
        db.add(product)
        inserted += 1

    db.commit()

    return {
        "total_received": len(items),
        "inserted": inserted,
        "duplicates_skipped": duplicates_skipped,
    }


def _apply_filters(stmt, filters: ResultFilters):
    conditions = []

    if filters.in_stock is not None:
        conditions.append(ResultItem.in_stock == filters.in_stock)
    if filters.min_price is not None:
        conditions.append(ResultItem.price >= filters.min_price)
    if filters.max_price is not None:
        conditions.append(ResultItem.price <= filters.max_price)
    if filters.category:
        conditions.append(ResultItem.category == filters.category)
    if filters.name_query:
        q = f"%{filters.name_query}%"
        conditions.append(ResultItem.name.ilike(q))
    if filters.external_id:
        conditions.append(ResultItem.external_id == filters.external_id)
    if filters.currency:
        conditions.append(ResultItem.currency == filters.currency.upper())

    if conditions:
        stmt = stmt.where(and_(*conditions))
    return stmt


def query_results(
    db: Session,
    session_id: int,
    filters: ResultFilters,
    *,
    limit: int,
    offset: int,
    sort_by: str,
    sort_order: str,
):
    session = get_session_or_404(db, session_id)

    base_stmt = select(ResultItem).where(ResultItem.site_id == session.site_id)
    base_stmt = _apply_filters(base_stmt, filters)

    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = db.execute(count_stmt).scalar_one()

    sort_column = {
        "price": ResultItem.price,
        "updated_at": ResultItem.updated_at,
        "name": ResultItem.name,
    }.get(sort_by, ResultItem.updated_at)

    order_expr = sort_column.desc() if sort_order.lower() == "desc" else sort_column.asc()

    data_stmt = base_stmt.order_by(order_expr).limit(limit).offset(offset)
    items = list(db.execute(data_stmt).scalars())

    return total, items
