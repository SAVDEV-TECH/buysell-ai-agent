from buysell_agent.data.repository import ProductRepository

product_repo = ProductRepository()

def search_products(query: str) -> str:
    """
    Search the BuySell product catalog by name.

    Args:
        query: The search term to look for in product names.

    Returns:
        A formatted string of matching products with price and stock,
        or a message if no products are found.
    """
    results = product_repo.search_by_name(query)
    if not results:
        return "No products found."
    return "\n".join(
        f"{p.name} | ₦{p.price:,} | Stock: {p.stock}"
        for p in results
    )
