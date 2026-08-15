"""
payment.py — V5: Paystack payment link generation.
"""
import httpx
from datetime import datetime
from buysell_agent.config import settings
from buysell_agent.data.repository import OrderRepository

_orders = OrderRepository()

PAYSTACK_API = "https://api.paystack.co"


def generate_payment_link(order_id: str, customer_email: str) -> str:
    """
    Generate a Paystack checkout payment link for a confirmed order.

    The link can be shared with the customer to complete payment online.
    Requires PAYSTACK_SECRET_KEY to be set in the .env file.

    Args:
        order_id: The order ID to generate a payment link for (e.g. ORD-1001).
        customer_email: The customer's email address (required by Paystack).

    Returns:
        A message containing the Paystack checkout URL,
        or an error message if the order is not found or the API call fails.
    """
    if not settings.paystack_secret_key:
        return (
            "⚠️  Paystack is not configured. To enable payments, add your "
            "PAYSTACK_SECRET_KEY to the .env file and restart the agent."
        )

    order = _orders.get(order_id)
    if not order:
        return f"No order found with ID '{order_id}'."

    # If a link was already generated, return the existing one
    if order.payment_url:
        return (
            f"A payment link already exists for {order_id}:\n"
            f"🔗 {order.payment_url}\n"
            f"Reference: {order.payment_reference}"
        )

    vat = int(order.total_amount * 0.075)
    grand_total_kobo = (order.total_amount + vat) * 100  # Paystack uses kobo

    # Use a unique reference each time to avoid Paystack duplicate reference errors
    unique_ref = f"{order_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    headers = {
        "Authorization": f"Bearer {settings.paystack_secret_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "amount": grand_total_kobo,
        "currency": "NGN",
        "email": customer_email,
        "reference": unique_ref,
        "metadata": {
            "order_id": order_id,
            "product": order.product_name,
            "quantity": order.quantity,
        },
    }

    try:
        response = httpx.post(
            f"{PAYSTACK_API}/transaction/initialize",
            json=payload,
            headers=headers,
            timeout=10,
        )
        data = response.json()

        if not data.get("status"):
            error_msg = data.get('message', 'Unknown error')
            return f"Paystack error: {error_msg}"

        auth_url = data["data"]["authorization_url"]
        reference = data["data"]["reference"]

        # Persist the payment URL to the order record
        _orders.update_payment(order_id, reference, auth_url)

        return (
            f"✅ Payment link generated for order {order_id}!\n"
            f"   Product    : {order.product_name}\n"
            f"   Amount     : ₦{order.total_amount + vat:,} (incl. VAT)\n"
            f"   Reference  : {reference}\n\n"
            f"🔗 Payment URL:\n{auth_url}\n\n"
            f"Share this link with your customer to complete payment."
        )

    except httpx.TimeoutException:
        return "❌ Request to Paystack timed out. Please try again."
    except Exception as e:
        return f"❌ Failed to generate payment link: {e}"
