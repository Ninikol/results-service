from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ParseSessionCreate(BaseModel):
    site_id: int
    user_id: int
    status: str = Field(min_length=1, max_length=50)
    started_at: datetime
    ended_at: datetime | None = None
    processed_items: int | None = None


class ParseSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    site_id: int
    user_id: int
    status: str
    started_at: datetime
    ended_at: datetime | None
    processed_items: int | None


class ResultItemIn(BaseModel):
    external_id: str | None = None
    name: str = Field(min_length=1, max_length=500)
    brand: str | None = None
    category: str | None = None
    url: str | None = None

    price: str | float | Decimal
    currency: str | None = None
    unit: str | None = None
    in_stock: bool | str | int | None = None

    attributes: dict[str, Any] = Field(default_factory=dict)


class BulkIngestRequest(BaseModel):
    items: list[ResultItemIn] = Field(default_factory=list)


class BulkIngestResponse(BaseModel):
    session_id: int
    total_received: int
    inserted: int
    duplicates_skipped: int


class ResultItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    site_id: int
    external_id: str | None

    name: str
    category: str | None
    price: Decimal
    old_price: Decimal | None
    currency: str
    description: str | None
    in_stock: bool
    updated_at: datetime


class ResultFilters(BaseModel):
    in_stock: bool | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    category: str | None = None
    name_query: str | None = None
    external_id: str | None = None
    currency: str | None = None


class PaginatedResults(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ResultItemOut]
