"""
database.py — V5: SQLite engine, session factory, and initial data seeding.

In V6+, swap DATABASE_URL to postgresql://... and everything else stays the same.
"""
from sqlmodel import Session, SQLModel, create_engine, select
from buysell_agent.config import settings
from buysell_agent.data.models import Order, Product, Supplier

# ---------------------------------------------------------------------------
# Engine — single instance for the whole application
# ---------------------------------------------------------------------------
engine = create_engine(
    settings.database_url,
    echo=False,          # Set True to see raw SQL queries while debugging
    connect_args={"check_same_thread": False},  # Required for SQLite only
)


def get_session() -> Session:
    """Return a new database session. Always use as a context manager."""
    return Session(engine)


# ---------------------------------------------------------------------------
# Seed data — products and suppliers loaded on first run only
# ---------------------------------------------------------------------------
_SEED_PRODUCTS = [
    Product(name="Golden Penny Spaghetti", price=1200, stock=50),
    Product(name="Dangote Sugar 1kg",      price=2500, stock=30),
    Product(name="Indomie Noodles",        price=800,  stock=100),
]

_SEED_SUPPLIERS = [
    Supplier(name="Lagos Wholesale Ltd",   product_name="Golden Penny Spaghetti", unit_price=1050, lead_time_days=2, min_order_qty=50),
    Supplier(name="Abuja Foods Direct",    product_name="Golden Penny Spaghetti", unit_price=1100, lead_time_days=1, min_order_qty=20),
    Supplier(name="Kano Commodities Co.",  product_name="Dangote Sugar 1kg",      unit_price=2200, lead_time_days=3, min_order_qty=100),
    Supplier(name="Lagos Wholesale Ltd",   product_name="Dangote Sugar 1kg",      unit_price=2350, lead_time_days=2, min_order_qty=50),
    Supplier(name="Abuja Foods Direct",    product_name="Indomie Noodles",        unit_price=720,  lead_time_days=1, min_order_qty=100),
    Supplier(name="Port Harcourt Traders", product_name="Indomie Noodles",        unit_price=750,  lead_time_days=4, min_order_qty=200),
]


def init_db() -> None:
    """
    Create all tables and seed initial data if the database is empty.
    Safe to call multiple times — does nothing on subsequent runs.
    """
    SQLModel.metadata.create_all(engine)

    with get_session() as session:
        # Only seed if no products exist yet
        existing = session.exec(select(Product)).first()
        if existing:
            return

        for product in _SEED_PRODUCTS:
            session.add(product)
        for supplier in _SEED_SUPPLIERS:
            session.add(supplier)
        session.commit()
        print("[OK] Database initialised and seeded.")
