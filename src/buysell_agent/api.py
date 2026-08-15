"""
api.py — BuySell AI Agent REST API (FastAPI)

Exposes all agent tools as HTTP endpoints AND a /chat endpoint
that lets a website talk to the full Gemini-powered AI agent.
"""
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from google import genai
from google.genai import types

from buysell_agent.agent import SYSTEM_INSTRUCTIONS
from buysell_agent.config import settings
from buysell_agent.data.database import init_db
from buysell_agent.tools.product_search import search_products
from buysell_agent.tools.inventory_price import check_price, check_inventory
from buysell_agent.tools.supplier_quotation import compare_suppliers, generate_quotation
from buysell_agent.tools.order_management import place_order, get_order_status, list_orders
from buysell_agent.tools.payment import generate_payment_link
from buysell_agent.tools.notifications import send_whatsapp_notification

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# ---------------------------------------------------------------------------
# Gemini client — created once at module level, shared across all requests
# ---------------------------------------------------------------------------
_genai_client = genai.Client()

_genai_config = types.GenerateContentConfig(
    system_instruction=SYSTEM_INSTRUCTIONS.strip(),
    tools=[
        search_products, check_price, check_inventory,
        compare_suppliers, generate_quotation,
        place_order, get_order_status, list_orders,
        generate_payment_link, send_whatsapp_notification,
    ],
    temperature=0.0,
)

# ---------------------------------------------------------------------------
# In-memory chat sessions (keyed by session_id)
# ---------------------------------------------------------------------------
_sessions: dict = {}


def _get_or_create_session(session_id: str):
    if session_id not in _sessions:
        _sessions[session_id] = _genai_client.chats.create(
            model=settings.model_name, config=_genai_config
        )
    return _sessions[session_id]


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logging.info("BuySell Agent API started.")
    yield
    logging.info("BuySell Agent API shutting down.")


app = FastAPI(
    title="BuySell AI Agent API",
    description="Enterprise AI agent for product search, ordering, payments and notifications.",
    version="5.0.0",
    lifespan=lifespan,
)

# Allow all origins so your website (on any domain) can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    reply: str
    session_id: str

class SearchRequest(BaseModel):
    query: str

class OrderRequest(BaseModel):
    product_name: str
    quantity: int

class QuoteRequest(BaseModel):
    product_name: str
    quantity: int

class PaymentRequest(BaseModel):
    order_id: str
    customer_email: str

class NotifyRequest(BaseModel):
    order_id: str
    phone_number: str


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {"status": "ok", "agent": "BuySell AI Agent", "version": "5.0.0"}


@app.get("/widget", response_class=HTMLResponse)
def widget():
    """Serve the chat widget HTML page."""
    widget_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "chat_widget.html"
    )
    widget_path = os.path.abspath(widget_path)
    with open(widget_path, "r", encoding="utf-8") as f:
        html = f.read()
    # Replace localhost placeholder with the same origin so it works when deployed
    html = html.replace(
        'const API_BASE = "http://localhost:8000"',
        'const API_BASE = ""',  # empty = same origin
    )
    return HTMLResponse(content=html)


# ---------------------------------------------------------------------------
# /chat — Full AI agent (the main endpoint for website integration)
# ---------------------------------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Send any natural language message to the AI agent.
    The agent picks the right tool automatically.
    Supports multi-turn conversations via session_id.
    """
    chat_session = _get_or_create_session(req.session_id)
    response = chat_session.send_message(req.message)
    return ChatResponse(reply=response.text, session_id=req.session_id)


# ---------------------------------------------------------------------------
# Direct tool endpoints (for website components that need structured data)
# ---------------------------------------------------------------------------
@app.post("/search")
def api_search(req: SearchRequest):
    return {"result": search_products(req.query)}

@app.get("/product/{name}/price")
def api_price(name: str):
    return {"result": check_price(name)}

@app.get("/product/{name}/inventory")
def api_inventory(name: str):
    return {"result": check_inventory(name)}

@app.post("/suppliers")
def api_suppliers(req: SearchRequest):
    return {"result": compare_suppliers(req.query)}

@app.post("/quote")
def api_quote(req: QuoteRequest):
    return {"result": generate_quotation(req.product_name, req.quantity)}

@app.post("/order")
def api_order(req: OrderRequest):
    return {"result": place_order(req.product_name, req.quantity)}

@app.get("/order/{order_id}")
def api_order_status(order_id: str):
    return {"result": get_order_status(order_id)}

@app.get("/orders")
def api_list_orders():
    return {"result": list_orders()}

@app.post("/payment-link")
def api_payment(req: PaymentRequest):
    return {"result": generate_payment_link(req.order_id, req.customer_email)}

@app.post("/notify")
def api_notify(req: NotifyRequest):
    return {"result": send_whatsapp_notification(req.order_id, req.phone_number)}
