"""
order_management.py — V6: B2B Order Placement with volume pricing & Supabase schema compatibility.
"""
from buysell_agent.data.models import Order, OrderStatus
from buysell_agent.data.repository import OrderRepository, ProductRepository

_products = ProductRepository()
_orders = OrderRepository()


def place_order(product_name: str, quantity: int) -> str:
    """
    Place a confirmed B2B purchase order for a product.

    Automatically calculates volume tier pricing, validates against MOQ,
    and assigns the verified supplier organization.

    Args:
        product_name: The title or name of the product to order.
        quantity: The number of units or metric tons to order.

    Returns:
        A confirmation message with the order ID and full summary,
        or an error message if the order does not meet minimum order quantity.
    """
    product = _products.get_by_exact_name(product_name)
    if not product:
        return f"Cannot place order: product '{product_name}' not found in the marketplace catalog."

    if quantity < product.min_order_quantity:
        return (
            f"Cannot place order: {quantity} {product.unit_of_measure}s is below the Minimum Order Quantity "
            f"(MOQ is {product.min_order_quantity} {product.unit_of_measure}s for '{product.title}')."
        )

    suppliers = _products.get_suppliers_for_product(product_name)
    supplier_name = suppliers[0].name if suppliers else "BuySell Verified Supplier"
    currency = suppliers[0].currency if suppliers else "USD"

    # Dynamic tiered unit price
    unit_price = product.get_unit_price(quantity)
    total = unit_price * quantity
    order_id = _orders.new_id()

    order = Order(
        order_id=order_id,
        product_name=product.title,
        quantity=quantity,
        unit_price=unit_price,
        currency=currency,
        supplier=supplier_name,
        total_amount=total,
        status=OrderStatus.CONFIRMED,
    )
    saved_order = _orders.place(order)

    vat = total * 0.075
    grand_total = total + vat

    return (
        f"[ORDER CONFIRMED]\n"
        f"   Order ID   : {saved_order.order_id}\n"
        f"   Item       : {product.title}\n"
        f"   Volume     : {quantity:,} {product.unit_of_measure}s\n"
        f"   Supplier   : {supplier_name}\n"
        f"   Tier Price : ${unit_price:,.2f} / {product.unit_of_measure}\n"
        f"   Subtotal   : ${total:,.2f} {currency}\n"
        f"   VAT (7.5%) : ${vat:,.2f} {currency}\n"
        f"   Total      : ${grand_total:,.2f} {currency}\n"
        f"   Status     : {saved_order.status.value}\n\n"
        f"Tip: Provide customer email to generate an escrow payment link for {saved_order.order_id}."
    )


def get_order_status(order_id: str) -> str:
    """
    Retrieve the current status and full details of an order by its order ID.

    Args:
        order_id: The order ID (e.g. ORD-1001).

    Returns:
        A formatted string with the order details and current status.
    """
    order = _orders.get(order_id)
    if not order:
        return f"No order found with ID '{order_id}'. Please check the order ID and try again."

    vat = order.total_amount * 0.075
    payment_info = ""
    if order.payment_url:
        payment_info = f"\n   Payment URL: {order.payment_url}"

    return (
        f"[ORDER DETAILS]\n"
        f"   Order ID   : {order.order_id}\n"
        f"   Product    : {order.product_name}\n"
        f"   Quantity   : {order.quantity:,}\n"
        f"   Supplier   : {order.supplier}\n"
        f"   Unit Price : ${order.unit_price:,.2f}\n"
        f"   Subtotal   : ${order.total_amount:,.2f} {order.currency}\n"
        f"   VAT (7.5%) : ${vat:,.2f} {order.currency}\n"
        f"   Total      : ${order.total_amount + vat:,.2f} {order.currency}\n"
        f"   Status     : {order.status.value}\n"
        f"   Placed At  : {order.created_at.strftime('%d %b %Y, %H:%M')}"
        f"{payment_info}"
    )


def list_orders() -> str:
    """
    List all orders in the database, from newest to oldest.

    Returns:
        A formatted table of all orders, or a message if no orders have been placed yet.
    """
    orders = _orders.all()
    if not orders:
        return "No orders have been placed yet."

    lines = [f"{'Order ID':<12} {'Product':<28} {'Qty':>6} {'Total':>14} {'Status'}"]
    lines.append("-" * 70)
    for o in orders:
        grand = o.total_amount + (o.total_amount * 0.075)
        lines.append(
            f"{o.order_id:<12} {o.product_name[:26]:<28} {o.quantity:>6} "
            f"${grand:>11,.2f} {o.status.value}"
        )
    lines.append("-" * 70)
    lines.append(f"Total orders: {len(orders)}")
    return "\n".join(lines)
