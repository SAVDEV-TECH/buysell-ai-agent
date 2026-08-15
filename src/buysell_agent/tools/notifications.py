"""
notifications.py — V6: Real WhatsApp messages via Meta Cloud API.
"""
import httpx
from datetime import datetime
from buysell_agent.config import settings
from buysell_agent.data.repository import OrderRepository

_orders = OrderRepository()

META_API_VERSION = "v21.0"


def send_whatsapp_notification(order_id: str, phone_number: str) -> str:
    """
    Send a WhatsApp order confirmation message to a customer's phone number
    using the Meta Cloud API.

    The phone number must be registered as a test recipient on the Meta
    developer dashboard (for test tokens), or any number in production.

    Args:
        order_id: The order ID to send a notification for (e.g. ORD-1001).
        phone_number: The customer's phone number in international format
                      WITHOUT the + sign (e.g. 2348012345678 for Nigeria).

    Returns:
        A confirmation that the message was sent, or an error message.
    """
    if not settings.whatsapp_token or not settings.whatsapp_phone_number_id:
        return (
            "WhatsApp is not configured. Please add WHATSAPP_TOKEN and "
            "WHATSAPP_PHONE_NUMBER_ID to your .env file."
        )

    order = _orders.get(order_id)
    if not order:
        return f"Cannot send notification: no order found with ID '{order_id}'."

    # Normalise phone number — strip the + if present
    clean_number = phone_number.lstrip("+").replace(" ", "").replace("-", "")

    vat = int(order.total_amount * 0.075)
    grand_total = order.total_amount + vat

    # Build the message body
    message_body = (
        f"*BuySell Order Confirmation*\n"
        f"Order ID: *{order.order_id}*\n"
        f"Product: {order.product_name}\n"
        f"Qty: {order.quantity:,} units\n"
        f"Supplier: {order.supplier}\n"
        f"Total: *N{grand_total:,}* (incl. VAT)\n"
        f"Status: *{order.status.value}*\n"
        f"Thank you for shopping with BuySell!"
    )

    if order.payment_url:
        message_body += f"\n\nComplete payment here:\n{order.payment_url}"

    url = (
        f"https://graph.facebook.com/{META_API_VERSION}/"
        f"{settings.whatsapp_phone_number_id}/messages"
    )

    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": clean_number,
        "type": "text",
        "text": {"body": message_body},
    }

    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=10)
        data = response.json()

        if response.status_code == 200 and data.get("messages"):
            message_id = data["messages"][0].get("id", "unknown")
            timestamp = datetime.now().strftime("%H:%M")
            return (
                f"WhatsApp message sent successfully to +{clean_number} [{timestamp}]\n"
                f"Message ID: {message_id}\n\n"
                f"Message preview:\n{message_body}"
            )
        else:
            error = data.get("error", {})
            return (
                f"Failed to send WhatsApp message.\n"
                f"Error: {error.get('message', 'Unknown error')} "
                f"(code {error.get('code', '?')})"
            )

    except httpx.TimeoutException:
        return "WhatsApp request timed out. Please try again."
    except Exception as e:
        return f"Failed to send WhatsApp notification: {e}"
