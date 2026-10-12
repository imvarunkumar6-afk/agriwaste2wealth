from __future__ import annotations

import csv
import os
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal

import bcrypt
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, SessionLocal, engine, get_db
from app.dependencies import create_access_token, get_current_user, require_roles
from app.models import (
    AiPrediction,
    AuditLog,
    BuyerRequirement,
    Enquiry,
    Listing,
    Notification,
    Order,
    ResearchExport,
    ResearchRecord,
    RoleEnum,
    User,
)
from app.schemas import (
    AiEstimateInput,
    AiMatchInput,
    BuyerRequirementCreate,
    BuyerRequirementOut,
    DashboardSummary,
    EnquiryCreate,
    EnquiryOut,
    ListingCreate,
    ListingOut,
    NotificationOut,
    OrderCreate,
    OrderOut,
    ResearchRecordCreate,
    ResearchRecordOut,
    Token,
    UserCreate,
    UserLogin,
    UserOut,
)
from app.services.estimation import estimate_residue_value
from app.services.matching import calculate_match_score
from app.services.recommendations import build_recommendations

app = FastAPI(title=settings.app_name, version="0.1.0", description="AgriWaste2Wealth backend API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def add_audit(db: Session, user_id: int | None, action: str, details: dict[str, Any] | None = None):
    db.add(AuditLog(user_id=user_id, action=action, details=details or {}))
    db.commit()


def ensure_upload_dir():
    os.makedirs(settings.upload_dir, exist_ok=True)


def convert_to_tonnes(quantity: float, unit: str) -> float:
    unit_l = (unit or "t").lower()
    if unit_l == "kg":
        return quantity / 1000
    if unit_l == "tonne" or unit_l == "tonnes":
        return quantity
    if unit_l == "quintal":
        return quantity / 10
    return quantity


def format_listing_response(listing: Listing) -> dict[str, Any]:
    return {
        "id": listing.id,
        "seller_id": listing.seller_id,
        "seller_name": listing.seller.name if listing.seller else "Unknown",
        "title": listing.title,
        "residue_type": listing.residue_type,
        "source_crop": listing.source_crop,
        "quantity_available": listing.quantity_available,
        "unit": listing.unit,
        "quality": listing.quality,
        "moisture_content": listing.moisture_content,
        "district": listing.district,
        "village": listing.village,
        "location": listing.location,
        "availability_date": listing.availability_date.isoformat(),
        "price_per_unit": listing.price_per_unit,
        "status": listing.status,
        "photo_url": listing.photo_url,
        "pickup_or_delivery": listing.pickup_or_delivery,
        "created_at": listing.created_at.isoformat() if listing.created_at else None,
        "updated_at": listing.updated_at.isoformat() if listing.updated_at else None,
    }


def ensure_demo_users_and_data(db: Session):
    legacy_demo_emails = {
        "admin@agriwaste2wealth.local": "admin@agriwaste2wealth.example.com",
        "farmer@agriwaste2wealth.local": "farmer@agriwaste2wealth.example.com",
        "buyer@agriwaste2wealth.local": "buyer@agriwaste2wealth.example.com",
        "researcher@agriwaste2wealth.local": "researcher@agriwaste2wealth.example.com",
    }
    for legacy_email, valid_email in legacy_demo_emails.items():
        legacy_user = db.query(User).filter(User.email == legacy_email).first()
        if legacy_user and not db.query(User).filter(User.email == valid_email).first():
            legacy_user.email = valid_email
    db.flush()

    if db.query(User).count() > 0:
        db.commit()
        return

    admin = User(
        email="admin@agriwaste2wealth.example.com",
        password_hash=hash_password("AdminPass123!"),
        name="Platform Administrator",
        role=RoleEnum.ADMIN.value,
        is_active=True,
        is_verified=True,
    )
    db.add(admin)
    db.flush()

    farmer = User(
        email="farmer@agriwaste2wealth.example.com",
        password_hash=hash_password("FarmerPass123!"),
        name="Aadhavan Farmer",
        role=RoleEnum.FARMER.value,
        is_active=True,
        is_verified=True,
    )
    buyer = User(
        email="buyer@agriwaste2wealth.example.com",
        password_hash=hash_password("BuyerPass123!"),
        name="Coimbatore Buyer",
        role=RoleEnum.BUYER.value,
        is_active=True,
        is_verified=True,
    )
    researcher = User(
        email="researcher@agriwaste2wealth.example.com",
        password_hash=hash_password("ResearchPass123!"),
        name="Agronomy Researcher",
        role=RoleEnum.RESEARCHER.value,
        is_active=True,
        is_verified=True,
    )
    db.add_all([farmer, buyer, researcher])
    db.flush()

    listing = Listing(
        seller_id=farmer.id,
        title="Rice Straw Availability",
        residue_type="Rice Straw",
        source_crop="Rice",
        quantity_available=4.5,
        unit="t",
        quality="Dry and clean",
        moisture_content=12,
        district="Thanjavur",
        village="Muthupettai",
        location="Thanjavur district",
        availability_date=date.today(),
        price_per_unit=1600,
        status="active",
        photo_url="https://images.unsplash.com/photo-1501004318641-b39e6451bec6?auto=format&fit=crop&w=900&q=80",
        pickup_or_delivery="pickup",
    )
    db.add(listing)
    db.flush()

    requirement = BuyerRequirement(
        buyer_id=buyer.id,
        business_category="Biomass distributor",
        residue_type="Rice Straw",
        quantity_required=3.0,
        unit="t",
        quality_spec="Dry",
        acceptable_price=1700,
        delivery_location="Coimbatore",
        district="Coimbatore",
        status="open",
    )
    db.add(requirement)

    enquiry = Enquiry(
        buyer_id=buyer.id,
        listing_id=listing.id,
        message="Interested in a dry rice straw lot within 5 days.",
        status="new",
    )
    db.add(enquiry)

    research_record = ResearchRecord(
        user_id=researcher.id,
        respondent_category="Farmer",
        district="Tiruchirappalli",
        locality="Anbil",
        main_crop="Rice",
        residue_type="Rice straw",
        quantity_generated=5.4,
        quantity_reused=1.6,
        quantity_sold=2.4,
        quantity_burned=0.5,
        disposal_cost=1200,
        sale_price=6800,
        awareness_level="moderate",
        consent_given=True,
    )
    db.add(research_record)
    db.commit()


@app.on_event("startup")
def startup_event():
    ensure_upload_dir()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if settings.seed_demo_data:
            ensure_demo_users_and_data(db)
    finally:
        db.close()


@app.get("/")
def serve_index() -> FileResponse:
    return FileResponse("index.html")


@app.get("/style.css")
def serve_css() -> FileResponse:
    return FileResponse("style.css")


@app.get("/script.js")
def serve_script() -> FileResponse:
    return FileResponse("script.js")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "app": settings.app_name, "synthetic_data_flag": settings.seed_demo_data}


@app.post("/api/auth/register", response_model=UserOut)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    allowed_self_registration_roles = {
        RoleEnum.FARMER.value,
        RoleEnum.BUYER.value,
        RoleEnum.RESEARCHER.value,
    }
    if payload.role.lower() not in allowed_self_registration_roles:
        raise HTTPException(status_code=400, detail="This role cannot be self-registered")
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        name=payload.name,
        role=payload.role.lower(),
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    add_audit(db, user.id, "user_register", {"email": user.email, "role": user.role})
    return user


@app.post("/api/auth/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/api/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    total_users = db.query(User).count()
    total_listings = db.query(Listing).count()
    total_orders = db.query(Order).count()
    total_research_records = db.query(ResearchRecord).count()
    total_value = db.query(func.coalesce(func.sum(Order.total_amount), 0)).scalar() or 0
    return {
        "total_users": total_users,
        "total_listings": total_listings,
        "total_orders": total_orders,
        "total_research_records": total_research_records,
        "total_value": float(total_value),
        "role": current_user.role,
        "synthetic_data": settings.seed_demo_data,
    }


@app.get("/api/listings", response_model=list[ListingOut])
def list_listings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    listings = db.query(Listing).join(User, Listing.seller_id == User.id).all()
    return listings


@app.post("/api/listings", response_model=ListingOut)
def create_listing(payload: ListingCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if payload.quantity_available <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero")
    listing = Listing(
        seller_id=current_user.id,
        title=payload.title,
        residue_type=payload.residue_type,
        source_crop=payload.source_crop,
        quantity_available=float(payload.quantity_available),
        unit=payload.unit,
        quality=payload.quality,
        moisture_content=payload.moisture_content,
        district=payload.district,
        village=payload.village,
        location=payload.location,
        availability_date=payload.availability_date,
        price_per_unit=float(payload.price_per_unit),
        status=payload.status,
        photo_url=payload.photo_url,
        pickup_or_delivery=payload.pickup_or_delivery,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    add_audit(db, current_user.id, "listing_created", {"listing_id": listing.id})
    return listing


@app.get("/api/listings/{listing_id}", response_model=ListingOut)
def get_listing(listing_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@app.put("/api/listings/{listing_id}", response_model=ListingOut)
def update_listing(listing_id: int, payload: ListingCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if current_user.role != RoleEnum.ADMIN.value and listing.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own listings")
    for field, value in payload.model_dump().items():
        setattr(listing, field, value)
    db.commit()
    db.refresh(listing)
    add_audit(db, current_user.id, "listing_updated", {"listing_id": listing.id})
    return listing


@app.delete("/api/listings/{listing_id}")
def delete_listing(listing_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if current_user.role != RoleEnum.ADMIN.value and listing.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own listings")
    db.delete(listing)
    db.commit()
    add_audit(db, current_user.id, "listing_deleted", {"listing_id": listing_id})
    return {"deleted": True}


@app.post("/api/requirements", response_model=BuyerRequirementOut)
def create_requirement(payload: BuyerRequirementCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    requirement = BuyerRequirement(
        buyer_id=current_user.id,
        business_category=payload.business_category,
        residue_type=payload.residue_type,
        quantity_required=payload.quantity_required,
        unit=payload.unit,
        quality_spec=payload.quality_spec,
        acceptable_price=payload.acceptable_price,
        delivery_location=payload.delivery_location,
        district=payload.district,
        status=payload.status,
    )
    db.add(requirement)
    db.commit()
    db.refresh(requirement)
    add_audit(db, current_user.id, "buyer_requirement_created", {"requirement_id": requirement.id})
    return requirement


@app.get("/api/requirements", response_model=list[BuyerRequirementOut])
def list_requirements(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(BuyerRequirement).filter(BuyerRequirement.buyer_id == current_user.id).all()


@app.post("/api/enquiries", response_model=EnquiryOut)
def create_enquiry(payload: EnquiryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    listing = db.get(Listing, payload.listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    enquiry = Enquiry(buyer_id=current_user.id, listing_id=payload.listing_id, message=payload.message)
    db.add(enquiry)
    db.commit()
    db.refresh(enquiry)
    notification = Notification(
        user_id=listing.seller_id,
        title="New buyer enquiry",
        message=f"A buyer has sent an enquiry for {listing.residue_type}.",
    )
    db.add(notification)
    db.commit()
    add_audit(db, current_user.id, "enquiry_created", {"enquiry_id": enquiry.id})
    return enquiry


@app.get("/api/enquiries", response_model=list[EnquiryOut])
def list_enquiries(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == RoleEnum.ADMIN.value:
        return db.query(Enquiry).all()
    return db.query(Enquiry).filter(Enquiry.buyer_id == current_user.id).all()


@app.post("/api/orders", response_model=OrderOut)
def create_order(payload: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    listing = db.get(Listing, payload.listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.status not in {"active", "pending"}:
        raise HTTPException(status_code=400, detail="Listing is not available for order")

    requested_quantity_t = convert_to_tonnes(float(payload.quantity), payload.unit)
    available_quantity_t = convert_to_tonnes(float(listing.quantity_available), listing.unit)

    if requested_quantity_t > available_quantity_t:
        raise HTTPException(status_code=400, detail="Requested quantity exceeds available stock")

    order = Order(
        buyer_id=current_user.id,
        seller_id=listing.seller_id,
        listing_id=listing.id,
        quantity=float(payload.quantity),
        unit=payload.unit,
        price_per_unit=listing.price_per_unit,
        status="reserved",
        total_amount=float(payload.quantity) * listing.price_per_unit,
        notes=payload.notes,
    )
    db.add(order)
    listing.quantity_available = max(0.0, available_quantity_t - requested_quantity_t)
    if listing.quantity_available <= 0:
        listing.status = "sold"
    db.flush()

    notification = Notification(
        user_id=listing.seller_id,
        title="Order reserved",
        message=f"An order has been placed for {requested_quantity_t:.2f} t of {listing.residue_type}.",
    )
    db.add(notification)
    db.commit()
    add_audit(db, current_user.id, "order_created", {"order_id": order.id, "listing_id": listing.id})
    return order


@app.get("/api/orders", response_model=list[OrderOut])
def list_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == RoleEnum.ADMIN.value:
        return db.query(Order).all()
    return db.query(Order).filter((Order.buyer_id == current_user.id) | (Order.seller_id == current_user.id)).all()


@app.post("/api/orders/{order_id}/confirm")
def confirm_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.seller_id != current_user.id and current_user.role != RoleEnum.ADMIN.value:
        raise HTTPException(status_code=403, detail="Only the seller or admin can confirm an order")
    order.status = "confirmed"
    db.commit()
    add_audit(db, current_user.id, "order_confirmed", {"order_id": order.id})
    return {"message": "Order confirmed", "order_id": order.id}


@app.post("/api/ai/estimate")
def estimate_ai(payload: AiEstimateInput, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    result = estimate_residue_value(payload.model_dump())
    prediction = AiPrediction(
        user_id=current_user.id,
        prediction_type="waste_estimation",
        inputs=payload.model_dump(),
        assumptions=result["assumptions"],
        result=result["result"],
        model_version=result["model_version"],
        annotation=result["label"],
    )
    db.add(prediction)
    db.commit()
    return result


@app.post("/api/ai/recommendations")
def get_recommendations(payload: dict[str, Any], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    residue_type = payload.get("residue_type", "")
    quantity_t = float(payload.get("quantity_t", 0) or 0)
    quality = payload.get("quality")
    recommendations = build_recommendations(residue_type=residue_type, quantity_t=quantity_t, quality=quality)
    prediction = AiPrediction(
        user_id=current_user.id,
        prediction_type="recommendation",
        inputs=payload,
        assumptions={"residue_type": residue_type, "quantity_t": quantity_t, "quality": quality},
        result={"recommendations": recommendations},
        model_version=settings.model_version,
        annotation="recommendation_engine",
    )
    db.add(prediction)
    db.commit()
    return {"recommendations": recommendations}


@app.post("/api/matches")
def get_matches(payload: AiMatchInput, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    listings = db.query(Listing).filter(Listing.status == "active").all()
    match_rows = []
    for listing in listings:
        listing_payload = {
            "residue_type": listing.residue_type,
            "quantity_available": float(listing.quantity_available),
            "price_per_unit": float(listing.price_per_unit),
            "quality": listing.quality or "standard",
            "distance_km": 30,
        }
        score, reasons = calculate_match_score(listing_payload, payload.model_dump())
        match_rows.append({
            "listing_id": listing.id,
            "seller_name": listing.seller.name if listing.seller else "Unknown",
            "residue_type": listing.residue_type,
            "score": score,
            "reasons": reasons,
            "price_per_unit": listing.price_per_unit,
            "quantity_available": listing.quantity_available,
        })
    match_rows.sort(key=lambda r: r["score"], reverse=True)
    result = {"matches": match_rows[:5], "weights": {"residue_match": 0.35, "quantity_fit": 0.2, "price_fit": 0.2, "distance_fit": 0.15, "quality_fit": 0.1}}
    db.add(
        AiPrediction(
            user_id=current_user.id,
            prediction_type="matching",
            inputs=payload.model_dump(),
            assumptions={"weights": result["weights"]},
            result={"matches": match_rows[:5]},
            model_version=settings.model_version,
            annotation="buyer_seller_match",
        )
    )
    db.commit()
    return result


@app.post("/api/research", response_model=ResearchRecordOut)
def create_research_record(payload: ResearchRecordCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not payload.consent_given:
        raise HTTPException(status_code=400, detail="Consent is required to store a research record")
    record = ResearchRecord(
        user_id=current_user.id,
        respondent_category=payload.respondent_category,
        district=payload.district,
        locality=payload.locality,
        main_crop=payload.main_crop,
        residue_type=payload.residue_type,
        quantity_generated=payload.quantity_generated,
        quantity_reused=payload.quantity_reused,
        quantity_sold=payload.quantity_sold,
        quantity_burned=payload.quantity_burned,
        disposal_cost=payload.disposal_cost,
        sale_price=payload.sale_price,
        awareness_level=payload.awareness_level,
        consent_given=payload.consent_given,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    add_audit(db, current_user.id, "research_record_created", {"record_id": record.id})
    return record


@app.get("/api/research", response_model=list[ResearchRecordOut])
def list_research_records(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in {RoleEnum.RESEARCHER.value, RoleEnum.ADMIN.value}:
        raise HTTPException(status_code=403, detail="Researchers and administrators can access research data")
    return db.query(ResearchRecord).all()


@app.get("/api/research/export")
def export_research(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in {RoleEnum.RESEARCHER.value, RoleEnum.ADMIN.value}:
        raise HTTPException(status_code=403, detail="Only authorized research or admin roles can export data")
    records = db.query(ResearchRecord).all()
    export_dir = Path(settings.upload_dir)
    export_dir.mkdir(exist_ok=True)
    export_name = f"research_export_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    file_path = export_dir / export_name
    with file_path.open("w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["id", "respondent_category", "district", "main_crop", "residue_type", "quantity_generated", "consent_given"])
        for record in records:
            writer.writerow([
                record.id,
                record.respondent_category,
                record.district,
                record.main_crop,
                record.residue_type,
                record.quantity_generated,
                record.consent_given,
            ])

    export_record = ResearchExport(
        created_by=current_user.id,
        export_version=settings.model_version,
        record_count=len(records),
        file_path=str(file_path),
    )
    db.add(export_record)
    db.commit()
    add_audit(db, current_user.id, "research_exported", {"file_path": str(file_path)})
    return {"file_path": str(file_path), "record_count": len(records), "version": settings.model_version}


@app.get("/api/notifications", response_model=list[NotificationOut])
def list_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.id.desc()).all()


@app.post("/api/uploads")
async def upload_file(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(exist_ok=True)
    file_id = uuid.uuid4().hex
    file_path = upload_dir / f"{file_id}_{file.filename}"
    with file_path.open("wb") as destination:
        while chunk := await file.read(1024 * 1024):
            destination.write(chunk)
    url = f"/uploads/{file_path.name}"
    add_audit(db := SessionLocal(), current_user.id, "file_uploaded", {"file_name": file_path.name})
    return {"file_url": url, "filename": file_path.name}


@app.get("/uploads/{file_name}")
def serve_upload(file_name: str):
    file_path = Path(settings.upload_dir) / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


@app.get("/api/admin/report")
def admin_report(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != RoleEnum.ADMIN.value:
        raise HTTPException(status_code=403, detail="Administrative access required")
    total_users = db.query(User).count()
    active_listings = db.query(Listing).filter(Listing.status == "active").count()
    pending_orders = db.query(Order).filter(Order.status == "reserved").count()
    total_value = db.query(func.coalesce(func.sum(Order.total_amount), 0)).scalar() or 0
    return {
        "registered_users_by_role": {
            "farmer": db.query(User).filter(User.role == RoleEnum.FARMER.value).count(),
            "buyer": db.query(User).filter(User.role == RoleEnum.BUYER.value).count(),
            "researcher": db.query(User).filter(User.role == RoleEnum.RESEARCHER.value).count(),
            "admin": db.query(User).filter(User.role == RoleEnum.ADMIN.value).count(),
        },
        "active_listings": active_listings,
        "pending_orders": pending_orders,
        "total_value": float(total_value),
        "total_users": total_users,
        "synthetic_data": settings.seed_demo_data,
    }


@app.get("/api/public/bootstrap")
def public_bootstrap() -> dict[str, Any]:
    result: dict[str, Any] = {
        "app_name": settings.app_name,
        "version": "0.1.0",
        "synthetic_data": settings.seed_demo_data,
    }
    if settings.seed_demo_data:
        result["demo_users"] = [
            {"email": "admin@agriwaste2wealth.example.com", "password": "AdminPass123!"},
            {"email": "farmer@agriwaste2wealth.example.com", "password": "FarmerPass123!"},
            {"email": "buyer@agriwaste2wealth.example.com", "password": "BuyerPass123!"},
            {"email": "researcher@agriwaste2wealth.example.com", "password": "ResearchPass123!"},
        ]
    return result
