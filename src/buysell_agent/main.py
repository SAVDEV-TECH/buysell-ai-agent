import asyncio
import logging

from google import genai
from google.genai import types

from buysell_agent.agent import SYSTEM_INSTRUCTIONS
from buysell_agent.tools.product_search import search_products
from buysell_agent.tools.inventory_price import check_price, check_inventory
from buysell_agent.tools.supplier_quotation import compare_suppliers, generate_quotation
from buysell_agent.tools.order_management import place_order, get_order_status, list_orders
from buysell_agent.tools.payment import generate_payment_link
from buysell_agent.tools.notifications import send_whatsapp_notification
# Import settings to ensure environment variables are loaded and validated on startup
from buysell_agent.config import settings
# Initialise the database (creates tables + seeds data on first run)
from buysell_agent.data.database import init_db

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

async def main():
    # Initialise DB before anything else
    init_db()

    print("=========================")
    print(" BuySell AI Agent (v5) ")
    print("=========================")
    print("Tools: search | price | inventory | suppliers | quotation")
    print("       order  | status | orders | payment | whatsapp")
    print("Type 'exit' to quit.\n")

    client = genai.Client()

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTIONS.strip(),
        tools=[
            search_products, check_price, check_inventory,
            compare_suppliers, generate_quotation,
            place_order, get_order_status, list_orders,
            generate_payment_link, send_whatsapp_notification,
        ],
        temperature=0.0,
    )

    chat = client.chats.create(model=settings.model_name, config=config)

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                break

            response = chat.send_message(user_input)
            print(f"\nAgent: {response.text}\n")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            logging.error(f"An error occurred during agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(main())
