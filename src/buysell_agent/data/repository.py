"""
repository.py — V5: Real SQL queries replacing all in-memory mock data.
"""
import re
from typing import List, Optional

from sqlmodel import Session, select, col

from buysell_agent.data.database import get_session
from buysell_agent.data.models import Order, OrderStatus, Product, Supplier


# ---------------------------------------------------------------------------
# Product Repository
# ---------------------------------------------------------------------------
class ProductRepository:
    """All product and supplier queries against the SQLite database."""

    def search_by_name(self, query: str) -> List[Product]:
        with get_session() as session:
            statement = select(Product).where(
                col(Product.name).contains(query.lower())
            )
            return session.exec(statement).all()

    def get_by_exact_name(self, name: str) -> Optional[Product]:
        with get_session() as session:
            # Try exact match first
            statement = select(Product).where(
                col(Product.name).ilike(name)
            )
            result = session.exec(statement).first()
            if result:
                return result
            # Fallback: partial match
            statement = select(Product).where(
                col(Product.name).contains(name.lower())
            )
            return session.exec(statement).first()

    def update_stock(self, product_id: int, new_stock: int) -> None:
        with get_session() as session:
            product = session.get(Product, product_id)
            if product:
                product.stock = new_stock
                session.add(product)
                session.commit()

    def get_suppliers_for_product(self, product_name: str) -> List[Supplier]:
        with get_session() as session:
            statement = select(Supplier).where(
                col(Supplier.product_name).contains(product_name.lower())
            )
            return session.exec(statement).all()


# ---------------------------------------------------------------------------
# Order Repository
# ---------------------------------------------------------------------------
class OrderRepository:
    """All order persistence queries against the SQLite database."""

    _counter_cache: Optional[int] = None

    def _next_order_id(self, session: Session) -> str:
        # Find the highest existing order number
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
