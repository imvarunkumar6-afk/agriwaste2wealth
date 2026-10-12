from __future__ import annotations

from typing import Any


DEFAULT_WEIGHTS = {
    "residue_match": 0.35,
    "quantity_fit": 0.2,
    "price_fit": 0.2,
    "distance_fit": 0.15,
    "quality_fit": 0.1,
}


def calculate_match_score(listing: dict[str, Any], requirement: dict[str, Any], weights: dict[str, float] | None = None) -> tuple[float, list[str]]:
    weights = weights or DEFAULT_WEIGHTS
    residue_match = 1.0 if listing["residue_type"].lower() == requirement["residue_type"].lower() else 0.7
    quantity_need = float(requirement.get("quantity_required", 0) or 0)
    listing_qty = float(listing.get("quantity_available", 0) or 0)
    quantity_fit = min(1.0, listing_qty / max(quantity_need, 0.1)) if quantity_need else 1.0
    acceptable_price = float(requirement.get("acceptable_price", 0) or 0)
    listing_price = float(listing.get("price_per_unit", 0) or 0)
    price_fit = 1.0 if acceptable_price >= listing_price else max(0.2, acceptable_price / max(listing_price, 1))
    distance = float(listing.get("distance_km", 0) or 0)
    distance_fit = max(0.1, 1 - (distance / 150))
    quality = str(listing.get("quality") or "standard")
    quality_fit = 1.0 if "premium" in quality.lower() or "clean" in quality.lower() else 0.8
    score = (
        residue_match * weights["residue_match"]
        + quantity_fit * weights["quantity_fit"]
        + price_fit * weights["price_fit"]
        + distance_fit * weights["distance_fit"]
        + quality_fit * weights["quality_fit"]
    ) * 100

    reasons = [
        f"Residue type match: {residue_match * 100:.0f}%",
        f"Quantity fit: {quantity_fit * 100:.0f}%",
        f"Price fit: {price_fit * 100:.0f}%",
        f"Distance fit: {distance_fit * 100:.0f}%",
        f"Quality fit: {quality_fit * 100:.0f}%",
    ]
    return round(score, 2), reasons
