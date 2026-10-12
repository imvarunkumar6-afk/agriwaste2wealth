from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class RoleEnum(str, PyEnum):
    FARMER = "farmer"
    BUYER = "buyer"
    ADMIN = "admin"
    RESEARCHER = "researcher"


class ListingStatus(str, PyEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    SOLD = "sold"
    REJECTED = "rejected"
    PENDING = "pending"


class OrderStatus(str, PyEnum):
    CREATED = "created"
    RESERVED = "reserved"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default=RoleEnum.FARMER.value)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    listings = relationship("Listing", back_populates="seller")
    requirements = relationship("BuyerRequirement", back_populates="buyer")
    enquiries = relationship("Enquiry", back_populates="buyer")
    orders = relationship("Order", foreign_keys="[Order.buyer_id]", back_populates="buyer")
    seller_orders = relationship("Order", foreign_keys="[Order.seller_id]", back_populates="seller")
    notifications = relationship("Notification", back_populates="user")
    ai_predictions = relationship("AiPrediction", back_populates="user")
    research_records = relationship("ResearchRecord", back_populates="user")


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    residue_type = Column(String(150), nullable=False)
    source_crop = Column(String(150), nullable=False)
    quantity_available = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False, default="t")
    quality = Column(String(150), nullable=True)
    moisture_content = Column(Float, nullable=True)
    district = Column(String(150), nullable=False)
    village = Column(String(150), nullable=True)
    location = Column(String(255), nullable=True)
    availability_date = Column(Date, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    status = Column(String(50), nullable=False, default=ListingStatus.ACTIVE.value)
    photo_url = Column(String(500), nullable=True)
    pickup_or_delivery = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    seller = relationship("User", back_populates="listings")
    enquiries = relationship("Enquiry", back_populates="listing")
    orders = relationship("Order", back_populates="listing")


class BuyerRequirement(Base):
    __tablename__ = "buyer_requirements"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    business_category = Column(String(150), nullable=True)
    residue_type = Column(String(150), nullable=False)
    quantity_required = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False, default="t")
    quality_spec = Column(String(255), nullable=True)
    acceptable_price = Column(Float, nullable=False)
    delivery_location = Column(String(255), nullable=True)
    district = Column(String(150), nullable=True)
    status = Column(String(50), nullable=False, default="open")
    created_at = Column(DateTime, default=datetime.utcnow)

    buyer = relationship("User", back_populates="requirements")


class Enquiry(Base):
    __tablename__ = "enquiries"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="new")
    created_at = Column(DateTime, default=datetime.utcnow)

    buyer = relationship("User", back_populates="enquiries")
    listing = relationship("Listing", back_populates="enquiries")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False, default="t")
    price_per_unit = Column(Float, nullable=False)
    status = Column(String(50), nullable=False, default=OrderStatus.CREATED.value)
    total_amount = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="orders")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="seller_orders")
    listing = relationship("Listing", back_populates="orders")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class AiPrediction(Base):
    __tablename__ = "ai_predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    prediction_type = Column(String(150), nullable=False)
    inputs = Column(JSON, nullable=False)
    assumptions = Column(JSON, nullable=False)
    result = Column(JSON, nullable=False)
    model_version = Column(String(100), nullable=False)
    annotation = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="ai_predictions")


class ResearchRecord(Base):
    __tablename__ = "research_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    respondent_category = Column(String(100), nullable=False)
    district = Column(String(150), nullable=False)
    locality = Column(String(150), nullable=True)
    main_crop = Column(String(150), nullable=False)
    residue_type = Column(String(150), nullable=False)
    quantity_generated = Column(Float, nullable=False)
    quantity_reused = Column(Float, nullable=True)
    quantity_sold = Column(Float, nullable=True)
    quantity_burned = Column(Float, nullable=True)
    disposal_cost = Column(Float, nullable=True)
    sale_price = Column(Float, nullable=True)
    awareness_level = Column(String(100), nullable=True)
    consent_given = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="research_records")


class ResearchExport(Base):
    __tablename__ = "research_exports"

    id = Column(Integer, primary_key=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    export_version = Column(String(100), nullable=False)
    record_count = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(255), nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
