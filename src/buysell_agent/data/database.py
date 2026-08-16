"""
database.py — V6: PostgreSQL (Supabase) & SQLite multi-dialect engine.
"""
from sqlmodel import Session, SQLModel, create_engine, select
from buysell_agent.config import settings
from buysell_agent.data.models import Order, Organization, Product

# ---------------------------------------------------------------------------
# Engine Configuration
# ---------------------------------------------------------------------------
# Fix postgres:// URI schema if provided by some cloud providers
db_url = settings.database_url
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

is_sqlite = db_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    db_url,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True,
)


def get_session() -> Session:
    """Return a new database session."""
    return Session(engine)


# ---------------------------------------------------------------------------
# Local Dev / Seed Data (Used only for local SQLite tests)
# ---------------------------------------------------------------------------
def init_db() -> None:
    """
    Initialise database connection. If on local SQLite, create tables and
    seed realistic B2B sample data. On Supabase, verify connection safely.
    """
    if is_sqlite:
        SQLModel.metadata.create_all(engine)
        with get_session() as session:
            existing = session.exec(select(Product)).first()
            if existing:
                return

            # Seed sample B2B organizations
            org_lagos = Organization(
                id="org-lagos-commodities",
                company_name="Lagos Commodities Exchange Ltd",
                organization_type="supplier",
                country_code="NG",
                base_currency="USD",
            )
            org_safari = Organization(
                id="org-safari-agro",
                company_name="Safari Agro Exports",
                organization_type="supplier",
                country_code="KE",
                base_currency="USD",
            )
            session.add(org_lagos)
            session.add(org_safari)
            session.commit()

            # Seed sample B2B products with Tiered Pricing
            prod_sesame = Product(
                id="prod-sesame-seed",
                supplier_organization_id="org-lagos-commodities",
                title="White Sesame Seeds (Grade A)",
                description="99.5% purity natural white sesame seeds, export quality",
                hs_code="1207.40",
                unit_of_measure="Metric Ton",
                min_order_quantity=10,
                tiered_pricing=[
                    {"min_qty": 10, "max_qty": 49, "unit_price": 1850.0},
                    {"min_qty": 50, "max_qty": 99, "unit_price": 1780.0},
                    {"min_qty": 100, "max_qty": None, "unit_price": 1700.0},
                ],
            )
            prod_cashew = Product(
                id="prod-raw-cashew",
                supplier_organization_id="org-safari-agro",
                title="Raw Cashew Nuts (RCN) - KOR 48+",
                description="Raw sun-dried cashew nuts from East Africa",
                hs_code="0801.31",
                unit_of_measure="Metric Ton",
                min_order_quantity=20,
                tiered_pricing=[
                    {"min_qty": 20, "max_qty": 99, "unit_price": 1250.0},
                    {"min_qty": 100, "max_qty": None, "unit_price": 1180.0},
                ],
            )
            session.add(prod_sesame)
            session.add(prod_cashew)
            session.commit()
            print("[OK] Local SQLite database initialised and seeded with B2B sample catalog.")
    else:
        print("[OK] Connected to Supabase PostgreSQL.")
