"""
repository.py — V6: Supabase PostgreSQL & SQLModel queries.
Handles B2B products, tiered pricing, and organizations.
"""
import re
from typing import List, Optional

from sqlmodel import Session, select, col

from buysell_agent.data.database import get_session
from buysell_agent.data.models import (
    Order,
    OrderStatus,
    Organization,
    Product,
    SupplierInfo,
)


# ---------------------------------------------------------------------------
# Product Repository
# ---------------------------------------------------------------------------
class ProductRepository:
    """Queries for B2B products and organizations."""

    def search_by_name(self, query: str) -> List[Product]:
        """Search products by title or description."""
        with get_session() as session:
            term = f"%{query.lower()}%"
            statement = select(Product).where(
                col(Product.title).ilike(term) | col(Product.description).ilike(term)
            )
            return session.exec(statement).all()

    def get_by_exact_name(self, name: str) -> Optional[Product]:
        """Find product by exact or best-matching title."""
        with get_session() as session:
            # 1. Exact match (case-insensitive)
            statement = select(Product).where(col(Product.title).ilike(name))
            result = session.exec(statement).first()
            if result:
                return result

            # 2. Substring match
            term = f"%{name.lower()}%"
            statement = select(Product).where(col(Product.title).ilike(term))
            return session.exec(statement).first()

    def get_suppliers_for_product(self, product_name: str) -> List[SupplierInfo]:
        """
        Find all supplier organizations offering products matching product_name,
        including their tiered pricing and MOQ.
        """
        with get_session() as session:
            term = f"%{product_name.lower()}%"
            statement = select(Product).where(col(Product.title).ilike(term))
            products = session.exec(statement).all()

            results: List[SupplierInfo] = []
            for p in products:
                supplier_name = "BuySell Verified Supplier"
                currency = "USD"
                if p.supplier_organization_id:
                    org = session.get(Organization, p.supplier_organization_id)
                    if org:
                        supplier_name = org.company_name
                        currency = org.base_currency or "USD"

                results.append(
                    SupplierInfo(
                        name=supplier_name,
                        product_title=p.title,
                        unit_price=p.base_price,
                        min_order_qty=p.min_order_quantity,
                        unit_of_measure=p.unit_of_measure,
                        currency=currency,
                        lead_time_days=3,
                        tiered_pricing=p.tiered_pricing if isinstance(p.tiered_pricing, list) else [],
                    )
                )

            return results


# ---------------------------------------------------------------------------
# Order Repository
# ---------------------------------------------------------------------------
class OrderRepository:
    """Order persistence queries."""

    def _next_order_id(self, session: Session) -> str:
        orders = session.exec(select(Order)).all()
        if not orders:
            return "ORD-1001"
        nums = []
        for o in orders:
            match = re.search(r"(\d+)$", o.order_id)
            if match:
                nums.append(int(match.group(1)))
        next_num = max(nums) + 1 if nums else 1001
        return f"ORD-{next_num}"

    def place(self, order: Order) -> Order:
        with get_session() as session:
            if not order.order_id:
                order.order_id = self._next_order_id(session)
            session.add(order)
            session.commit()
            session.refresh(order)
            return order

    def get(self, order_id: str) -> Optional[Order]:
        with get_session() as session:
            statement = select(Order).where(
                col(Order.order_id) == order_id.upper()
            )
            return session.exec(statement).first()

    def all(self) -> List[Order]:
        with get_session() as session:
            statement = select(Order)
            orders = session.exec(statement).all()
            return sorted(orders, key=lambda o: o.created_at, reverse=True)

    def update_payment(self, order_id: str, reference: str, url: str) -> None:
        with get_session() as session:
            statement = select(Order).where(col(Order.order_id) == order_id.upper())
            order = session.exec(statement).first()
            if order:
                order.payment_reference = reference
                order.payment_url = url
                session.add(order)
                session.commit()

    def new_id(self) -> str:
        with get_session() as session:
            return self._next_order_id(session)
