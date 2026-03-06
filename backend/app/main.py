from __future__ import annotations

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, get_db
from app.models import Base, ParseSession
from app.schemas import (
    BulkIngestRequest,
    BulkIngestResponse,
    PaginatedResults,
    ParseSessionCreate,
    ParseSessionOut,
    ResultFilters,
)
from app.services import create_session, get_session_or_404, ingest_results, query_results

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "service": settings.app_name}


@app.get("/sessions", response_model=list[ParseSessionOut])
def list_parse_sessions(
    status: str | None = None,
    site_id: int | None = None,
    user_id: int | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[ParseSessionOut]:
    stmt = select(ParseSession)

    if status is not None:
        stmt = stmt.where(ParseSession.status == status)
    if site_id is not None:
        stmt = stmt.where(ParseSession.site_id == site_id)
    if user_id is not None:
        stmt = stmt.where(ParseSession.user_id == user_id)

    sessions = list(
        db.execute(
            stmt.order_by(ParseSession.started_at.desc()).limit(limit).offset(offset)
        ).scalars()
    )

    return sessions


@app.post("/sessions", response_model=ParseSessionOut, status_code=201)
def create_parse_session(payload: ParseSessionCreate, db: Session = Depends(get_db)) -> ParseSessionOut:
    return create_session(
        db,
        site_id=payload.site_id,
        user_id=payload.user_id,
        status=payload.status,
        started_at=payload.started_at,
        ended_at=payload.ended_at,
        processed_items=payload.processed_items,
    )


@app.get("/sessions/{session_id}", response_model=ParseSessionOut)
def get_parse_session(session_id: int, db: Session = Depends(get_db)) -> ParseSessionOut:
    return get_session_or_404(db, session_id)


@app.post(
    "/sessions/{session_id}/results/bulk",
    response_model=BulkIngestResponse,
)
def bulk_ingest_results(
    session_id: int,
    payload: BulkIngestRequest,
    db: Session = Depends(get_db),
) -> BulkIngestResponse:
    stats = ingest_results(db, session_id=session_id, items=payload.items)
    return BulkIngestResponse(session_id=session_id, **stats)


@app.get("/sessions/{session_id}/results", response_model=PaginatedResults)
def list_results(
    session_id: int,
    in_stock: bool | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    category: str | None = None,
    name_query: str | None = None,
    external_id: str | None = None,
    currency: str | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    sort_by: str = Query(default="updated_at"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
) -> PaginatedResults:
    filters = ResultFilters(
        in_stock=in_stock,
        min_price=min_price,
        max_price=max_price,
        category=category,
        name_query=name_query,
        external_id=external_id,
        currency=currency,
    )

    total, items = query_results(
        db,
        session_id=session_id,
        filters=filters,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return PaginatedResults(total=total, limit=limit, offset=offset, items=items)


@app.post("/sessions/{session_id}/results/filter", response_model=PaginatedResults)
def filter_results(
    session_id: int,
    filters: ResultFilters,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    sort_by: str = Query(default="updated_at"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
) -> PaginatedResults:
    total, items = query_results(
        db,
        session_id=session_id,
        filters=filters,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return PaginatedResults(total=total, limit=limit, offset=offset, items=items)


@app.get("/")
def root() -> dict:
    return {
        "service": settings.app_name,
        "docs": "/docs",
        "health": "/health",
    }
