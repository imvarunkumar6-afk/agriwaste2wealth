from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=2)
    role: str = "farmer"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ListingCreate(BaseModel):
    title: str
    residue_type: str
    source_crop: str
    quantity_available: float
    unit: str = "t"
    quality: Optional[str] = None
    moisture_content: Optional[float] = None
    district: str
    village: Optional[str] = None
    location: Optional[str] = None
    availability_date: date
    price_per_unit: float
    status: str = "active"
    photo_url: Optional[str] = None
    pickup_or_delivery: Optional[str] = None


class ListingOut(ListingCreate):
    id: int
    seller_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BuyerRequirementCreate(BaseModel):
    business_category: Optional[str] = None
    residue_type: str
    quantity_required: float
    unit: str = "t"
    quality_spec: Optional[str] = None
    acceptable_price: float
    delivery_location: Optional[str] = None
    district: Optional[str] = None
    status: str = "open"


class BuyerRequirementOut(BuyerRequirementCreate):
    id: int
    buyer_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class EnquiryCreate(BaseModel):
    listing_id: int
    message: str = Field(..., min_length=3)


class EnquiryOut(EnquiryCreate):
    id: int
    buyer_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    listing_id: int
    quantity: float
    unit: str = "t"
    notes: Optional[str] = None


class OrderOut(OrderCreate):
    id: int
    buyer_id: int
    seller_id: int
    status: str
    total_amount: float
    price_per_unit: float
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime


class AiEstimateInput(BaseModel):
    area_acres: float
    yield_per_acre_t: float
    residue_factor: float
    recovery_ratio: float
    expected_price_per_kg: float
    season: str = "kharif"
    residue_type: str = "rice_straw"


class AiMatchInput(BaseModel):
    residue_type: str
    quantity_required: float
    unit: str = "t"
    acceptable_price: float
    district: Optional[str] = None


class ResearchRecordCreate(BaseModel):
    respondent_category: str
    district: str
    locality: Optional[str] = None
    main_crop: str
    residue_type: str
    quantity_generated: float
    quantity_reused: Optional[float] = None
    quantity_sold: Optional[float] = None
    quantity_burned: Optional[float] = None
    disposal_cost: Optional[float] = None
    sale_price: Optional[float] = None
    awareness_level: Optional[str] = None
    consent_given: bool = False


class ResearchRecordOut(ResearchRecordCreate):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    total_users: int
    total_listings: int
    total_orders: int
    total_research_records: int
    total_value: float


class ErrorResponse(BaseModel):
    detail: str


class Recommendation(BaseModel):
    application: str
    reason: str
    quantity_hint: Optional[str] = None
    revenue_range: Optional[str] = None
    processing_requirements: Optional[str] = None
    uncertainty_note: str


class MatchScore(BaseModel):
    listing_id: int
    seller_name: str
    residue_type: str
    score: float
    reasons: list[str]
