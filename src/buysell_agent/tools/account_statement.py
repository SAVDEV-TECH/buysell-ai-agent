from buysell_agent.data.repository import OrderRepository

_orders = OrderRepository()


def generate_account_statement(period: str = "all_time") -> str:
    """
    Generate a summarized statement of accounts showing order totals, VAT, and summary statistics.
    
    Args:
        period: Time period for the statement - "today", "week", "month", or "all_time"
        
    Returns:
        A formatted financial statement with totals, VAT breakdown, and summary statistics.
    """
    orders = _orders.all()
    
    if not orders:
        return "No orders found to generate account statement."
    
    # Filter by period (simplified - would need date filtering in production)
    filtered_orders = []
    
    # For all_time, use all orders
    if period == "all_time":
        filtered_orders = orders
    else:
        # Note: In production, would filter by date
        # This is a simplified version that uses all orders for now
        filtered_orders = orders
    
    # Calculate summary statistics
    total_subtotal = 0
    total_vat = 0
    total_grand = 0
    order_count = len(filtered_orders)
    
    for order in filtered_orders:
        subtotal = order.total_amount
        vat = int(subtotal * 0.075)
        grand_total = subtotal + vat
        
        total_subtotal += subtotal
        total_vat += vat
        total_grand += grand_total
    
    # Generate formatted statement
    statement = f"""
╔══════════════════════════════════════════════════════════╗
║              BUYSELL ACCOUNT STATEMENT                   ║
╠══════════════════════════════════════════════════════════╣
║ Period       : {period.replace('_', ' ').title()}
║ Generated    : {filtered_orders[-1].created_at.strftime('%d %b %Y, %H:%M') if filtered_orders else 'N/A'}
║ Total Orders : {order_count}
╠══════════════════════════════════════════════════════════╣
║ FINANCIAL SUMMARY                                     ║
╠══════════════════════════════════════════════════════════╣
"
    
    # Add order details table header
    statement += f"║ {'Order ID':<12} {'Date':<16} {'Product':<25} {'Qty':>4} {'Total':>14} {'Status'}\n"
    statement += "║ " + "─" * 90 + " ║\n"
    
    for order in filtered_orders[-10:]:  # Show last 10 orders
        vat = int(order.total_amount * 0.075)
        grand_total = order.total_amount + vat
        status = order.status.value
        
        statement += f"║ {order.order_id:<12} {order.created_at.strftime('%d %b %Y'):<16} {order.product_name:<25} {order.quantity:>4} ₦{grand_total:>12,} {status}\n"
    
    if len(filtered_orders) > 10:
        statement += f"║ ... and {len(filtered_orders) - 10} more orders\n"
    
    statement += f"║\n╠══════════════════════════════════════════════════════════╣\n"
    statement += f"║ SUMMARY BREAKDOWN                                      ║\n"
    statement += f"║ Subtotal (orders): ₦{total_subtotal:,}                        ║\n"
    statement += f"║ VAT (7.5%):       ₦{total_vat:,}                        ║\n"
    statement += f"║ Grand Total:       ₦{total_grand:,}                        ║\n"
    statement += f"╠══════════════════════════════════════════════════════════╣\n"
    statement += f"║ Average per order: ₦{total_grand // order_count if order_count > 0 else 0:,}           ║\n"
    statement += f"╚══════════════════════════════════════════════════════════╝\n"
    
    return statement.strip()