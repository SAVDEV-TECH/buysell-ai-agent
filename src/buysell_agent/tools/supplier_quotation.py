from datetime import date
from buysell_agent.data.repository import ProductRepository

_repo = ProductRepository()


def compare_suppliers(product_name: str) -> str:
    """
    Compare all available verified B2B suppliers for a given product or commodity,
    ranked by baseline unit price and volume pricing brackets.

    Args:
        product_name: The name or title of the product to compare suppliers for.

    Returns:
        A formatted comparison of verified suppliers sorted by best price.
    """
    suppliers = _repo.get_suppliers_for_product(product_name)
    if not suppliers:
        return f"No verified suppliers found for '{product_name}'."

    sorted_suppliers = sorted(suppliers, key=lambda s: s.unit_price)

    lines = [f"Verified Supplier Comparison for: {product_name}", ""]
    for rank, s in enumerate(sorted_suppliers, start=1):
        tier_text = ""
        if s.tiered_pricing:
            t_items = [
                f"{t.get('min_qty')}+: ${t.get('unit_price', 0):,.2f}"
                for t in s.tiered_pricing if isinstance(t, dict)
            ]
            tier_text = f"\n   Volume Tiers: {', '.join(t_items)}"

        lines.append(
            f"{rank}. {s.name}\n"
            f"   Base Price  : ${s.unit_price:,.2f} per {s.unit_of_measure}\n"
            f"   Min Order   : {s.min_order_qty} {s.unit_of_measure}\n"
            f"   Currency    : {s.currency}"
            f"{tier_text}"
        )

    best = sorted_suppliers[0]
    lines.append(f"\n✅ Recommended Supplier: {best.name} @ ${best.unit_price:,.2f}/{best.unit_of_measure}")
    return "\n".join(lines)


def generate_quotation(product_name: str, quantity: int) -> str:
    """
    Generate a formal B2B price quotation for a given product and quantity.

    Automatically calculates volume-tiered discounts based on order quantity.
    Includes itemized breakdown and 7.5% VAT.

    Args:
        product_name: The name of the product to quote.
        quantity: The number of units required.

    Returns:
        A formatted quotation document with line totals and volume discounts applied.
    """
    product = _repo.get_by_exact_name(product_name)
    suppliers = _repo.get_suppliers_for_product(product_name)

    if not product and not suppliers:
        return f"Cannot generate a quotation: product '{product_name}' not found."

    uom = product.unit_of_measure if product else "unit"
    supplier_name = suppliers[0].name if suppliers else "BuySell Verified Supplier"

    # Calculate unit price based on volume tiers
    unit_price = product.get_unit_price(quantity) if product else (suppliers[0].unit_price if suppliers else 0.0)

    subtotal = unit_price * quantity
    vat = subtotal * 0.075
    grand_total = subtotal + vat
    today = date.today().strftime("%d %b %Y")

    quotation = f"""
====================================================
            BUYSELL B2B FORMAL QUOTATION           
====================================================
  Date         : {today}
  Supplier     : {supplier_name}
----------------------------------------------------
  Item         : {product.title if product else product_name}
  Order Volume : {quantity:,} {uom}s
  Tier Price   : ${unit_price:,.2f} per {uom}
----------------------------------------------------
  Subtotal     : ${subtotal:,.2f}
  VAT (7.5%)   : ${vat:,.2f}
----------------------------------------------------
  GRAND TOTAL  : ${grand_total:,.2f} USD
====================================================
  * Pricing based on verified volume brackets.
  * Quote valid for 48 hours via BuySell Escrow.
""".strip()
    return quotation
