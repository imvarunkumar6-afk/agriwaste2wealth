from __future__ import annotations

from typing import Any


def estimate_residue_value(inputs: dict[str, Any]) -> dict[str, Any]:
    """Return a transparent baseline estimate. This is intentionally label-ready as a preliminary estimate."""
    area_acres = float(inputs.get("area_acres", 0))
    yield_per_acre_t = float(inputs.get("yield_per_acre_t", 0))
    residue_factor = float(inputs.get("residue_factor", 0.2))
    recovery_ratio = float(inputs.get("recovery_ratio", 0.65))
    expected_price_per_kg = float(inputs.get("expected_price_per_kg", 0))
    season = str(inputs.get("season", "kharif")).lower()

    residue_generated = area_acres * yield_per_acre_t * residue_factor
    recoverable = residue_generated * recovery_ratio
    marketable_quantity = recoverable * 0.74
    selling_value = marketable_quantity * 1000 * expected_price_per_kg
    collection_cost = recoverable * 140
    transport_cost = area_acres * 260
    net_income = selling_value - collection_cost - transport_cost
    confidence = min(92, max(58, 78 + (recovery_ratio * 18) - (5 if season == "kharif" else 0)))

    return {
        "model_version": "baseline-v1.0",
        "label": "preliminary_estimate",
        "assumptions": {
            "residue_factor": residue_factor,
            "recovery_ratio": recovery_ratio,
            "collection_cost_per_t": 140,
            "transport_cost_per_acre": 260,
            "marketable_share": 0.74,
            "season": season,
        },
        "result": {
            "residue_generated_t": round(residue_generated, 2),
            "recoverable_t": round(recoverable, 2),
            "marketable_t": round(marketable_quantity, 2),
            "potential_selling_value_inr": round(selling_value, 2),
            "net_income_inr": round(net_income, 2),
            "confidence_percent": round(confidence, 1),
        },
    }
