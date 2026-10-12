from __future__ import annotations


def build_recommendations(residue_type: str, quantity_t: float, quality: str | None = None) -> list[dict]:
    residue = (residue_type or "").lower()
    if "rice" in residue or "straw" in residue:
        recommendations = [
            {
                "application": "Compost and soil amendment",
                "reason": "High cellulose content and local demand from cereal growers for organic matter recovery.",
                "quantity_hint": "Minimum 1-2 t/month",
                "revenue_range": "₹4,000-₹9,000 per t",
                "processing_requirements": "Chopping, composting, curing, and moisture balancing.",
                "uncertainty_note": "Preliminary estimate; verify local market demand and composting standards.",
            },
            {
                "application": "Biomass briquettes",
                "reason": "Good calorific value when compacted and adequately dried.",
                "quantity_hint": "Preferred 3 t+ batches",
                "revenue_range": "₹6,000-₹11,000 per t",
                "processing_requirements": "Drying, grinding, densification, and packaging.",
                "uncertainty_note": "Depends on moisture and buyer specifications.",
            },
        ]
    elif "bagasse" in residue or "sugarcane" in residue:
        recommendations = [
            {
                "application": "Biomass fuel and industrial boiler feed",
                "reason": "Bagasse is commonly used for fuel and manufacturing support where moisture and contamination are controlled.",
                "quantity_hint": "Preferred 5 t+ batches",
                "revenue_range": "₹7,000-₹15,000 per t",
                "processing_requirements": "Drying, storage, and boiler-feed specification checks.",
                "uncertainty_note": "Fuel suitability requires end-user processing and emissions compliance.",
            },
            {
                "application": "Paper and fibre feedstock",
                "reason": "Cellulosic bagasse can be suitable for pulping under controlled processing conditions.",
                "quantity_hint": "Scale with mill demand",
                "revenue_range": "Variable",
                "processing_requirements": "Pulping, bleaching, and quality control tests.",
                "uncertainty_note": "Not suitable without processing compliance and material checks.",
            },
        ]
    elif "coconut" in residue or "husk" in residue:
        recommendations = [
            {
                "application": "Grow media and mulching",
                "reason": "Coconut husk is suitable for potting mixes and soil coverage when processed safely.",
                "quantity_hint": "2-4 t per batch",
                "revenue_range": "₹3,000-₹8,000 per t",
                "processing_requirements": "Cleaning, soaking, screening, and curing.",
                "uncertainty_note": "Demand may vary by region and nursery buyer requirements.",
            },
            {
                "application": "Biochar",
                "reason": "High lignocellulosic content supports conversion to carbon-rich soil amendment.",
                "quantity_hint": "3 t+ batches",
                "revenue_range": "₹8,000-₹16,000 per t",
                "processing_requirements": "Slow pyrolysis, cooling, sizing, and certification.",
                "uncertainty_note": "Requires kiln safety and process control.",
            },
        ]
    else:
        recommendations = [
            {
                "application": "Compost and soil amendment",
                "reason": "A flexible option for most dry, non-contaminated crop residues with nutrient cycling value.",
                "quantity_hint": "Depends on local demand",
                "revenue_range": "Variable",
                "processing_requirements": "Shredding, curing, screening, and compost quality control.",
                "uncertainty_note": "Application quality depends on chemistry, contamination risk, and moisture profile.",
            },
            {
                "application": "Biochar or pelletization",
                "reason": "Useful for dense, dry residues when conversion into durable value-added products is feasible.",
                "quantity_hint": "Preferred 2 t+ batches",
                "revenue_range": "Variable",
                "processing_requirements": "Drying, preprocessing, and process validation.",
                "uncertainty_note": "Requires feedstock and end-market checks before commitment.",
            },
        ]

    if quality and "wet" in quality.lower():
        recommendations[0]["reason"] += " Wet material should be dried before commercial valuation."

    for item in recommendations:
        item["quantity_hint"] = item.get("quantity_hint", "Batch dependent")
        item["revenue_range"] = item.get("revenue_range", "Variable")
    return recommendations
