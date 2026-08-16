"""
Domain models — V6: Aligned with Supabase PostgreSQL B2B Marketplace Schema.
Maps directly to `products`, `organizations`, and `orders`.
"""
import uuid
from enum import Enum
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON


# ---------------------------------------------------------------------------
# Organization (Suppliers / Buyers in Supabase)
# ---------------------------------------------------------------------------
class Organization(SQLModel, table=True):
    __tablename__ = "organizations"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True
    )
    company_name: str = Field(index=True)
    legal_registration_number: Optional[str] = None
    tax_id_vat: Optional[str] = None
    organization_type: str = Field(default="supplier")  # 'supplier', 'buyer', 'both'
    country_code: str = Field(default="NG")
    base_currency: str = Field(default="USD")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# ---------------------------------------------------------------------------
# Product (B2B Products with Tiered Pricing in Supabase)
# ---------------------------------------------------------------------------
class Product(SQLModel, table=True):
    __tablename__ = "products"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True
    )
    supplier_organization_id: Optional[str] = Field(
        default=None, foreign_key="organizations.id", index=True
    )
    category_id: Optional[str] = None
    title: str = Field(index=True)
    description: Optional[str] = None
    hs_code: Optional[str] = None
    unit_of_measure: str = Field(default="unit")
    min_order_quantity: int = Field(default=1)
    
    # Tiered pricing JSONB array: [{"min_qty": 100, "max_qty": 500, "unit_price": 12.50}]
    tiered_pricing: Any = Field(default_factory=list, sa_column=Column(JSON))
    custom_specifications: Optional[Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # ── Helper methods & Backward-compatible properties ──
    @property
    def name(self) -> str:
        """Alias for title to maintain compatibility with existing tools."""
        return self.title

    def get_unit_price(self, quantity: int = 1) -> float:
        """
        Extract the applicable unit price from the tiered_pricing array
        based on the requested order quantity.
        """
        tiers = self.tiered_pricing
        if isinstance(tiers, list) and len(tiers) > 0:
            for tier in tiers:
                if isinstance(tier, dict):
                    min_q = tier.get("min_qty", 1)
                    max_q = tier.get("max_qty")
                    if max_q is None or max_q == 0:
                        max_q = float("inf")
                    if min_q <= quantity <= max_q:
                        return float(tier.get("unit_price", 0.0))
            
            # If quantity is lower than minimum tier, return base/first tier price
            first_tier = tiers[0]
            if isinstance(first_tier, dict):
                return float(first_tier.get("unit_price", 0.0))
        
        return 0.0

    @property
    def base_price(self) -> float:
        """Baseline unit price (for qty = min_order_quantity)."""
        return self.get_unit_price(self.min_order_quantity)

    @property
    def price(self) -> float:
        """Alias for base_price."""
        return self.base_price

    @property
    def stock(self) -> int:
        """Default available stock if unconstrained."""
        return 999999


# ---------------------------------------------------------------------------
# Structured DTO for Supplier Comparison
# ---------------------------------------------------------------------------
class SupplierInfo:
    def __init__(
        self,
        name: str,
        product_title: str,
        unit_price: float,
        min_order_qty: int,
        unit_of_measure: str = "unit",
        currency: str = "USD",
        lead_time_days: int = 2,
        tiered_pricing: Optional[List[Dict[str, Any]]] = None,
    ):
        self.name = name
        self.product_name = product_title
        self.unit_price = unit_price
        self.min_order_qty = min_order_qty
        self.unit_of_measure = unit_of_measure
        self.currency = currency
        self.lead_time_days = lead_time_days
        self.tiered_pricing = tiered_pricing or []


# ---------------------------------------------------------------------------
# Order Model
# ---------------------------------------------------------------------------
class OrderStatus(str, Enum):
    PENDING   = "Pending"
    CONFIRMED = "Confirmed"
    SHIPPED   = "Shipped"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: str = Field(index=True, unique=True)
    product_name: str
    quantity: int
    unit_price: float
    currency: str = Field(default="USD")
    supplier: str
    total_amount: float
    status: OrderStatus = OrderStatus.CONFIRMED
    payment_reference: Optional[str] = None          # Paystack reference
    payment_url: Optional[str] = None                # Paystack checkout URL
    created_at: datetime = Field(default_factory=datetime.now)
