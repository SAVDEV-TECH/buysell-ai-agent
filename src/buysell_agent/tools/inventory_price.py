from buysell_agent.data.repository import ProductRepository

_repo = ProductRepository()


def check_price(product_name: str) -> str:
    """
    Check the current unit and tiered pricing of a product in the BuySell B2B catalog.

    Args:
        product_name: The name or title of the product to check.

    Returns:
        A formatted string with the product's base price and volume discount tiers.
    """
    product = _repo.get_by_exact_name(product_name)
    if not product:
        return f"No product found matching '{product_name}' in the B2B catalog."

    price_info = f"${product.base_price:,.2f} per {product.unit_of_measure}"
    tier_info = ""
    if isinstance(product.tiered_pricing, list) and len(product.tiered_pricing) > 0:
        tiers_list = []
        for t in product.tiered_pricing:
            if isinstance(t, dict):
                min_q = t.get("min_qty", 1)
                max_q = t.get("max_qty")
                max_str = f" - {max_q}" if max_q else "+"
                tiers_list.append(f"  • {min_q}{max_str} {product.unit_of_measure}s: ${t.get('unit_price', 0):,.2f}/{product.unit_of_measure}")
        if tiers_list:
            tier_info = "\nVolume Tiers:\n" + "\n".join(tiers_list)

    return f"Price for {product.title}:\nBase: {price_info} (MOQ: {product.min_order_quantity} {product.unit_of_measure}){tier_info}"


def check_inventory(product_name: str) -> str:
    """
    Check the MOQ (Minimum Order Quantity) and availability of a product in the BuySell catalog.

    Args:
        product_name: The name or title of the product to check.

    Returns:
        A formatted string with the product's MOQ, unit of measure, and sourcing availability.
    """
    product = _repo.get_by_exact_name(product_name)
    if not product:
        return f"No product found matching '{product_name}' in the B2B catalog."

    return (
        f"Product: {product.title}\n"
        f"Unit of Measure: {product.unit_of_measure}\n"
        f"Minimum Order Quantity (MOQ): {product.min_order_quantity} {product.unit_of_measure}\n"
        f"Availability: Available for Verified Sourcing & Bulk Orders"
    )
