import uuid

from fastapi.testclient import TestClient

from app.main import app



def make_email(prefix: str) -> str:
    return f"{prefix}{uuid.uuid4().hex[:8]}@example.com"


def test_public_registration_cannot_create_admin():
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/register",
            json={
                "email": make_email("admin_"),
                "password": "Secret123!",
                "name": "Untrusted Admin",
                "role": "admin",
            },
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "This role cannot be self-registered"


def test_auth_and_listing_and_order_flow():
    with TestClient(app) as client:
        farmer_email = make_email("farmer_")
        buyer_email = make_email("buyer_")

        reg1 = client.post("/api/auth/register", json={"email": farmer_email, "password": "Secret123!", "name": "Test Farmer", "role": "farmer"})
        assert reg1.status_code == 200, reg1.text

        reg2 = client.post("/api/auth/register", json={"email": buyer_email, "password": "Secret123!", "name": "Test Buyer", "role": "buyer"})
        assert reg2.status_code == 200, reg2.text

        farmer_login = client.post("/api/auth/login", json={"email": farmer_email, "password": "Secret123!"})
        assert farmer_login.status_code == 200, farmer_login.text
        farmer_token = farmer_login.json()["access_token"]

        buyer_login = client.post("/api/auth/login", json={"email": buyer_email, "password": "Secret123!"})
        assert buyer_login.status_code == 200, buyer_login.text
        buyer_token = buyer_login.json()["access_token"]

        listing_payload = {
            "title": "Rice Straw Listing",
            "residue_type": "Rice Straw",
            "source_crop": "Rice",
            "quantity_available": 5.0,
            "unit": "t",
            "quality": "Dry and clean",
            "moisture_content": 12.0,
            "district": "Thanjavur",
            "village": "Muthupettai",
            "location": "Near market yard",
            "availability_date": "2026-11-01",
            "price_per_unit": 1600,
            "status": "active",
            "photo_url": "https://example.com/rice.jpg",
            "pickup_or_delivery": "pickup",
        }

        listing_response = client.post("/api/listings", json=listing_payload, headers={"Authorization": f"Bearer {farmer_token}"})
        assert listing_response.status_code == 200, listing_response.text
        listing_id = listing_response.json()["id"]

        requirement_response = client.post(
            "/api/requirements",
            json={
                "business_category": "Biomass distributor",
                "residue_type": "Rice Straw",
                "quantity_required": 2.5,
                "unit": "t",
                "quality_spec": "Dry",
                "acceptable_price": 1700,
                "delivery_location": "Coimbatore",
                "district": "Coimbatore",
                "status": "open",
            },
            headers={"Authorization": f"Bearer {buyer_token}"},
        )
        assert requirement_response.status_code == 200, requirement_response.text

        order_response = client.post(
            "/api/orders",
            json={"listing_id": listing_id, "quantity": 2.0, "unit": "t", "notes": "As soon as possible"},
            headers={"Authorization": f"Bearer {buyer_token}"},
        )
        assert order_response.status_code == 200, order_response.text
        order_json = order_response.json()
        assert order_json["status"] == "reserved"
        assert order_json["total_amount"] > 0

        estimate_response = client.post(
            "/api/ai/estimate",
            json={"area_acres": 18, "yield_per_acre_t": 2.5, "residue_factor": 0.22, "recovery_ratio": 0.65, "expected_price_per_kg": 1.8, "season": "kharif", "residue_type": "rice_straw"},
            headers={"Authorization": f"Bearer {farmer_token}"},
        )
        assert estimate_response.status_code == 200, estimate_response.text
        estimate_body = estimate_response.json()
        assert "label" in estimate_body
        assert estimate_body["result"]["net_income_inr"] >= 0

        match_response = client.post(
            "/api/matches",
            json={"residue_type": "Rice Straw", "quantity_required": 2.5, "unit": "t", "acceptable_price": 1700, "district": "Thanjavur"},
            headers={"Authorization": f"Bearer {buyer_token}"},
        )
        assert match_response.status_code == 200, match_response.text
        assert len(match_response.json()["matches"]) >= 1

        research_response = client.post(
            "/api/research",
            json={"respondent_category": "Farmer", "district": "Trichy", "locality": "Thuvakudi", "main_crop": "Rice", "residue_type": "Rice straw", "quantity_generated": 4.8, "quantity_reused": 1.2, "quantity_sold": 2.0, "quantity_burned": 0.5, "disposal_cost": 1500, "sale_price": 7600, "awareness_level": "high", "consent_given": True},
            headers={"Authorization": f"Bearer {farmer_token}"},
        )
        assert research_response.status_code == 200, research_response.text

        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"
