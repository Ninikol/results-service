from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit, urlunsplit

_SPACE_RE = re.compile(r"\s+")
_NUMBER_RE = re.compile(r"\d+(?:[\.,]\d+)?")
_UNIT_RE = re.compile(r"(?P<qty>\d+(?:[\.,]\d+)?)\s*(?P<unit>[a-zA-Zа-яА-Я\.]+)")


@dataclass(frozen=True)
class QuantityNormalization:
    value: Decimal
    base_unit: str


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = _SPACE_RE.sub(" ", value.strip().lower())
    return cleaned or None


def normalize_currency(value: str | None) -> str:
    if not value:
        return "RUB"
    v = value.strip().upper()
    mapping = {
        "₽": "RUB",
        "РУБ": "RUB",
        "RUR": "RUB",
        "$": "USD",
        "€": "EUR",
    }
    return mapping.get(v, v[:3])


def parse_price(raw: str | float | Decimal) -> Decimal:
    if isinstance(raw, Decimal):
        return raw.quantize(Decimal("0.01"))
    if isinstance(raw, (int, float)):
        return Decimal(str(raw)).quantize(Decimal("0.01"))

    cleaned = raw.replace("\xa0", " ").replace(" ", "")
    cleaned = cleaned.replace(",", ".")
    match = _NUMBER_RE.search(cleaned)
    if not match:
        raise ValueError(f"Не удалось распознать цену: {raw}")
    try:
        return Decimal(match.group(0)).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise ValueError(f"Некорректная цена: {raw}") from exc


def parse_bool(raw: bool | str | int | None) -> bool:
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, int):
        return raw > 0
    if raw is None:
        return False
    v = raw.strip().lower()
    truthy = {"1", "true", "yes", "y", "да", "в наличии", "available", "instock", "in stock"}
    falsy = {"0", "false", "no", "n", "нет", "нет в наличии", "out", "outofstock", "out of stock"}
    if v in truthy:
        return True
    if v in falsy:
        return False
    return False


def normalize_url(raw_url: str | None) -> str | None:
    if not raw_url:
        return None
    parts = urlsplit(raw_url.strip())
    normalized_path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), normalized_path, "", ""))


def parse_quantity(unit_raw: str | None) -> QuantityNormalization:
    if not unit_raw:
        return QuantityNormalization(value=Decimal("1"), base_unit="pcs")

    raw = unit_raw.strip().lower()
    match = _UNIT_RE.search(raw)

    qty = Decimal("1")
    unit = raw
    if match:
        qty = Decimal(match.group("qty").replace(",", "."))
        unit = match.group("unit").lower().strip(".")

    aliases = {
        "г": ("kg", Decimal("0.001")),
        "гр": ("kg", Decimal("0.001")),
        "g": ("kg", Decimal("0.001")),
        "kg": ("kg", Decimal("1")),
        "кг": ("kg", Decimal("1")),
        "мл": ("l", Decimal("0.001")),
        "ml": ("l", Decimal("0.001")),
        "л": ("l", Decimal("1")),
        "l": ("l", Decimal("1")),
        "шт": ("pcs", Decimal("1")),
        "штука": ("pcs", Decimal("1")),
        "pcs": ("pcs", Decimal("1")),
        "pc": ("pcs", Decimal("1")),
    }

    base_unit, factor = aliases.get(unit, ("pcs", Decimal("1")))
    return QuantityNormalization(value=(qty * factor), base_unit=base_unit)


def build_fingerprint(
    normalized_name: str,
    normalized_brand: str | None,
    normalized_url: str | None,
    price: Decimal,
    currency: str,
    quantity_value: Decimal,
    quantity_unit: str,
) -> str:
    payload = "|".join(
        [
            normalized_name,
            normalized_brand or "",
            normalized_url or "",
            f"{price:.2f}",
            currency,
            f"{quantity_value:.4f}",
            quantity_unit,
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
