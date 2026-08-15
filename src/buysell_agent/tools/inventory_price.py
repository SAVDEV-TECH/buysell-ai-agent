from buysell_agent.data.repository import ProductRepository

_repo = ProductRepository()


def check_price(product_name: str) -> str:
    """
    Check the current price of a product in the BuySell catalog.

    Args:
        product_name: The name of the product to check the price for.

    Returns:
        A formatted string with the product price, or a message if not found.
    """
    product = _repo.get_by_exact_name(product_name)
    if not product:
        return f"No product found matching '{product_name}'."
    return f"{product.name}: ₦{product.price:,}"


def check_inventory(product_name: str) -> str:
    """
    Check the current stock / inventory level of a product in the BuySell catalog.

    Args:
        product_name: The name of the product to check inventory for.

    Returns:
        A formatted string with the stock level, or a message if not found.
    """
    product = _repo.get_by_exact_name(product_name)
    if not product:
        return f"No product found matching '{product_name}'."
    availability = "In stock" if product.stock > 0 else "Out of stock"
    return f"{product.name}: {product.stock} units available ({availability})"
