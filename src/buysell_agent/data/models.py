"""
Domain models — V5: upgraded to SQLModel so they serve as both
Pydantic validation models AND SQLite database table definitions.
"""
from enum import Enum
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------
class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    price: int
    stock: int


# ---------------------------------------------------------------------------
# Supplier
# ---------------------------------------------------------------------------
class Supplier(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    product_name: str = Field(index=True)
    unit_price: int
    lead_time_days: int
    min_order_qty: int


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------
class OrderStatus(str, Enum):
    PENDING   = "Pending"
    CONFIRMED = "Confirmed"
    SHIPPED   = "Shipped"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: str = Field(index=True, unique=True)
    product_name: str
    quantity: int
    unit_price: int
    supplier: str
    total_amount: int
    status: OrderStatus = OrderStatus.CONFIRMED
    payment_reference: Optional[str] = None          # Paystack reference
    payment_url: Optional[str] = None                # Paystack checkout URL
    created_at: datetime = Field(default_factory=datetime.now)
