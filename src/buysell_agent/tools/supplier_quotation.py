from datetime import date
from buysell_agent.data.repository import ProductRepository

_repo = ProductRepository()


def compare_suppliers(product_name: str) -> str:
    """
    Compare all available suppliers for a given product, ranked by unit price.

    Args:
        product_name: The name of the product to compare suppliers for.

    Returns:
        A formatted comparison table of suppliers sorted by best price,
        or a message if no suppliers are found for that product.
    """
    suppliers = _repo.get_suppliers_for_product(product_name)
    if not suppliers:
        return f"No suppliers found for '{product_name}'."

    sorted_suppliers = sorted(suppliers, key=lambda s: s.unit_price)

    lines = [f"Supplier comparison for: {sorted_suppliers[0].product_name}", ""]
    for rank, s in enumerate(sorted_suppliers, start=1):
        lines.append(
            f"{rank}. {s.name}\n"
            f"   Price:        ₦{s.unit_price:,} per unit\n"
            f"   Lead time:    {s.lead_time_days} day(s)\n"
            f"   Min. order:   {s.min_order_qty} units"
        )
    lines.append(f"\n✅ Best price: {sorted_suppliers[0].name} @ ₦{sorted_suppliers[0].unit_price:,}")
    return "\n".join(lines)


def generate_quotation(product_name: str, quantity: int) -> str:
    """
    Generate a formal price quotation for a given product and quantity.

    Uses the best available supplier price. Includes 7.5% VAT.

    Args:
        product_name: The name of the product to quote.
        quantity: The number of units required.

    Returns:
        A formatted quotation document with line totals and grand total.
    """
    suppliers = _repo.get_suppliers_for_product(product_name)
    product = _repo.get_by_exact_name(product_name)

    if not product and not suppliers:
        return f"Cannot generate a quotation: product '{product_name}' not found."

    if suppliers:
        best = min(suppliers, key=lambda s: s.unit_price)
        unit_price = best.unit_price
        source = best.name
    else:
        unit_price = product.price
        source = "BuySell Catalog"

    subtotal = unit_price * quantity
    vat = int(subtotal * 0.075)
    grand_total = subtotal + vat
    today = date.today().strftime("%d %b %Y")

    quotation = f"""
╔══════════════════════════════════════════╗
║         BUYSELL PRICE QUOTATION          ║
╚══════════════════════════════════════════╝
  Date         : {today}
  Supplier     : {source}
──────────────────────────────────────────
  Item         : {product_name}
  Qty          : {quantity:,} units
  Unit Price   : ₦{unit_price:,}
──────────────────────────────────────────
  Subtotal     : ₦{subtotal:,}
  VAT (7.5%)   : ₦{vat:,}
──────────────────────────────────────────
  GRAND TOTAL  : ₦{grand_total:,}
══════════════════════════════════════════
  Quote valid for 48 hours.
""".strip()
    return quotation
