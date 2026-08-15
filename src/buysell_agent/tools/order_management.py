"""
order_management.py — V5: place_order, get_order_status, list_orders
All backed by the real SQLite database via OrderRepository.
"""
from buysell_agent.data.models import Order, OrderStatus
from buysell_agent.data.repository import OrderRepository, ProductRepository

_products = ProductRepository()
_orders = OrderRepository()


def place_order(product_name: str, quantity: int) -> str:
    """
    Place a confirmed purchase order for a product.

    Automatically selects the best (lowest-price) available supplier.
    The order is persisted to the database and a unique order ID is returned.

    Args:
        product_name: The name of the product to order.
        quantity: The number of units to order.

    Returns:
        A confirmation message with the order ID and full summary,
        or an error message if the product or stock is insufficient.
    """
    product = _products.get_by_exact_name(product_name)
    if not product:
        return f"Cannot place order: product '{product_name}' not found in catalog."

    if product.stock < quantity:
        return (
            f"Cannot place order: only {product.stock} units of "
            f"'{product_name}' available, but {quantity} were requested."
        )

    suppliers = _products.get_suppliers_for_product(product_name)
    if suppliers:
        best = min(suppliers, key=lambda s: s.unit_price)
        unit_price = best.unit_price
        supplier_name = best.name
    else:
        unit_price = product.price
        supplier_name = "BuySell Catalog"

    total = unit_price * quantity
    order_id = _orders.new_id()

    order = Order(
        order_id=order_id,
        product_name=product.name,
        quantity=quantity,
        unit_price=unit_price,
        supplier=supplier_name,
        total_amount=total,
        status=OrderStatus.CONFIRMED,
    )
    saved_order = _orders.place(order)

    # Deduct stock
    _products.update_stock(product.id, product.stock - quantity)

    vat = int(total * 0.075)
    return (
        f"✅ Order Confirmed!\n"
        f"   Order ID   : {saved_order.order_id}\n"
        f"   Product    : {product.name}\n"
        f"   Quantity   : {quantity:,} units\n"
        f"   Supplier   : {supplier_name}\n"
        f"   Unit Price : ₦{unit_price:,}\n"
        f"   Subtotal   : ₦{total:,}\n"
        f"   VAT (7.5%) : ₦{vat:,}\n"
        f"   Total Paid : ₦{total + vat:,}\n"
        f"   Status     : {saved_order.status.value}\n\n"
        f"💡 Tip: Use 'generate payment link for {saved_order.order_id}' to send a Paystack checkout link."
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

    vat = int(order.total_amount * 0.075)
    payment_info = ""
    if order.payment_url:
        payment_info = f"\n   Payment URL: {order.payment_url}"

    return (
        f"📦 Order Details\n"
        f"   Order ID   : {order.order_id}\n"
        f"   Product    : {order.product_name}\n"
        f"   Quantity   : {order.quantity:,} units\n"
        f"   Supplier   : {order.supplier}\n"
        f"   Unit Price : ₦{order.unit_price:,}\n"
        f"   Subtotal   : ₦{order.total_amount:,}\n"
        f"   VAT (7.5%) : ₦{vat:,}\n"
        f"   Total      : ₦{order.total_amount + vat:,}\n"
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

    lines = [f"{'Order ID':<12} {'Product':<28} {'Qty':>5} {'Total':>12} {'Status'}"]
    lines.append("─" * 65)
    for o in orders:
        grand = o.total_amount + int(o.total_amount * 0.075)
        lines.append(
            f"{o.order_id:<12} {o.product_name:<28} {o.quantity:>5} "
            f"₦{grand:>10,} {o.status.value}"
        )
    lines.append("─" * 65)
    lines.append(f"Total orders: {len(orders)}")
    return "\n".join(lines)
