"""Backend-owned emission calculations.

AI never calculates or invents an emission value. This module is the single
place where quantity × factor becomes integer grams of CO2e.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from app.core.errors import ApiError
from app.modules.catalog.models import EmissionFactor


def calculate_emissions_grams(quantity: float | Decimal | str, factor_grams: int) -> int:
    """Multiply a positive quantity by an integer factor and round half-up."""
    try:
        qty = Decimal(str(quantity))
    except (InvalidOperation, ValueError) as exc:
        raise ApiError("validation_error", "quantity must be a number", 422) from exc
    if qty <= 0:
        raise ApiError("validation_error", "quantity must be greater than 0", 422)
    if factor_grams < 0:
        raise ApiError("validation_error", "emission factor cannot be negative", 422)
    grams = (qty * Decimal(factor_grams)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(grams)


def factor_source_text(factor: EmissionFactor) -> str:
    year = factor.source_year or "n.d."
    return f"{factor.source_name} ({year}), {factor.region}"


def validate_factor_for_record(
    factor: EmissionFactor,
    category_id: int,
    unit: str,
) -> None:
    if not factor.is_active:
        raise ApiError("validation_error", "This emission factor is inactive.", 422)
    if factor.category_id != category_id:
        raise ApiError(
            "validation_error",
            "The factor does not belong to the selected category.",
            422,
        )
    if (factor.unit or "").strip().lower() != (unit or "").strip().lower():
        raise ApiError(
            "validation_error",
            f"Unit must match the factor unit ({factor.unit}).",
            422,
        )
