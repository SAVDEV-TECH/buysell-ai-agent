from buysell_agent.data.repository import ProductRepository

product_repo = ProductRepository()


def search_products(query: str) -> str:
    """
    Search the BuySell B2B marketplace product catalog by name or description.

    Args:
        query: The search term to look for in product titles or descriptions.

    Returns:
        A formatted string of matching products with unit pricing, unit of measure,
        and minimum order quantities (MOQ).
    """
    results = product_repo.search_by_name(query)
    if not results:
        return "No products found matching your query."

    lines = []
    for p in results:
        price_str = f"${p.base_price:,.2f}" if p.base_price > 0 else "Custom RFQ"
        tiers_str = ""
        if isinstance(p.tiered_pricing, list) and len(p.tiered_pricing) > 0:
            tiers_parts = [
                f"{t.get('min_qty')}+ units: ${t.get('unit_price', 0):,.2f}"
                for t in p.tiered_pricing if isinstance(t, dict)
            ]
            tiers_str = f" | Tiers: [{', '.join(tiers_parts)}]"

        desc = f" - {p.description[:60]}..." if p.description else ""
        lines.append(
            f"• {p.title}{desc}\n"
            f"  Price: {price_str} / {p.unit_of_measure} | MOQ: {p.min_order_quantity} {p.unit_of_measure}{tiers_str}"
        )

    return "\n\n".join(lines)
