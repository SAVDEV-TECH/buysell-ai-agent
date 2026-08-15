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


WIDGET_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>BuySell AI Agent — Chat Widget</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: #f0f2f5;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      padding: 12px;
    }
    #buysell-widget {
      width: 440px;
      max-width: 100%;
      background: #fff;
      border-radius: 18px;
      box-shadow: 0 8px 40px rgba(0,0,0,0.14);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .widget-header {
      background: linear-gradient(135deg, #1a6b3c 0%, #27ae60 100%);
      color: #fff;
      padding: 18px 20px;
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .widget-header .avatar {
      width: 42px; height: 42px;
      background: rgba(255,255,255,0.2);
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 20px;
    }
    .widget-header .info h3 { font-size: 15px; font-weight: 600; }
    .widget-header .info p  { font-size: 12px; opacity: 0.85; margin-top: 2px; }
    .status-dot {
      width: 8px; height: 8px;
      background: #5fffaa;
      border-radius: 50%;
      display: inline-block;
      margin-right: 5px;
    }
    #messages {
      flex: 1;
      padding: 20px 16px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 12px;
      min-height: 380px;
      max-height: 440px;
      background: #f7f9fc;
    }
    .msg {
      display: flex;
      gap: 8px;
      animation: fadeIn 0.2s ease;
    }
    @keyframes fadeIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:none; } }
    .msg.user  { flex-direction: row-reverse; }
    .bubble {
      max-width: 82%;
      padding: 11px 15px;
      border-radius: 16px;
      font-size: 14px;
      line-height: 1.5;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .msg.agent .bubble {
      background: #fff;
      border: 1px solid #e4e8f0;
      border-radius: 4px 16px 16px 16px;
      color: #1a1a2e;
    }
    .msg.user .bubble {
      background: #1a6b3c;
      color: #fff;
      border-radius: 16px 4px 16px 16px;
    }
    .typing-indicator {
      display: flex; gap: 4px;
      align-items: center;
      padding: 10px 14px;
      background: #fff;
      border: 1px solid #e4e8f0;
      border-radius: 4px 16px 16px 16px;
      width: fit-content;
    }
    .typing-indicator span {
      width: 7px; height: 7px;
      background: #aab;
      border-radius: 50%;
      animation: bounce 1.2s infinite;
    }
    .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
    .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes bounce {
      0%, 80%, 100% { transform: translateY(0); }
      40%           { transform: translateY(-6px); }
    }
    #quick-replies {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      padding: 10px 16px 0;
    }
    .quick-btn {
      background: #eaf4ee;
      color: #1a6b3c;
      border: 1px solid #c3e6ce;
      border-radius: 20px;
      padding: 6px 14px;
      font-size: 12.5px;
      cursor: pointer;
      transition: all 0.15s;
      white-space: nowrap;
    }
    .quick-btn:hover { background: #1a6b3c; color: #fff; }
    .widget-input {
      display: flex;
      gap: 10px;
      padding: 14px 16px;
      border-top: 1px solid #eee;
      background: #fff;
    }
    #user-input {
      flex: 1;
      border: 1.5px solid #e0e4ec;
      border-radius: 24px;
      padding: 10px 16px;
      font-size: 14px;
      outline: none;
      transition: border-color 0.2s;
    }
    #user-input:focus { border-color: #1a6b3c; }
    #send-btn {
      width: 42px; height: 42px;
      background: #1a6b3c;
      border: none;
      border-radius: 50%;
      cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      transition: background 0.2s, transform 0.1s;
      flex-shrink: 0;
    }
    #send-btn:hover  { background: #145c31; }
    #send-btn:active { transform: scale(0.93); }
    #send-btn svg { width: 18px; height: 18px; fill: #fff; }
    .powered-by {
      text-align: center;
      font-size: 11px;
      color: #aaa;
      padding: 6px 0 10px;
    }
  </style>
</head>
<body>
<div id="buysell-widget">
  <div class="widget-header">
    <div class="avatar">🛒</div>
    <div class="info">
      <h3>BuySell AI Agent</h3>
      <p><span class="status-dot"></span>Online — here to help</p>
    </div>
  </div>
  <div id="messages">
    <div class="msg agent">
      <div class="bubble">Hello! I'm the BuySell AI Agent. I can help you search products, check prices, compare suppliers, place orders, and generate payment links. How can I help you today?</div>
    </div>
  </div>
  <div id="quick-replies">
    <button class="quick-btn" onclick="quickSend('Find me Indomie Noodles')">🔍 Search products</button>
    <button class="quick-btn" onclick="quickSend('Compare suppliers for Dangote Sugar')">🏭 Compare suppliers</button>
    <button class="quick-btn" onclick="quickSend('Show me all my orders')">📦 My orders</button>
    <button class="quick-btn" onclick="quickSend('Generate a quote for 100 units of Indomie Noodles')">📄 Get a quote</button>
  </div>
  <div class="widget-input">
    <input id="user-input" type="text" placeholder="Ask me anything..." autocomplete="off" />
    <button id="send-btn" onclick="sendMessage()" title="Send">
      <svg viewBox="0 0 24 24"><path d="M2 21l21-9L2 3v7l15 2-15 2v7z"/></svg>
    </button>
  </div>
  <p class="powered-by">Powered by Gemini AI &amp; BuySell Agent</p>
</div>

<script>
  const API_BASE = "";
  const SESSION_ID = "session-" + Math.random().toString(36).slice(2, 9);
  const messagesEl = document.getElementById("messages");
  const inputEl    = document.getElementById("user-input");

  inputEl.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });

  function quickSend(text) {
    inputEl.value = text;
    sendMessage();
  }

  function appendMessage(role, text) {
    const msg = document.createElement("div");
    msg.className = `msg ${role}`;
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;
    msg.appendChild(bubble);
    messagesEl.appendChild(msg);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return bubble;
  }

  function showTyping() {
    const wrap = document.createElement("div");
    wrap.className = "msg agent";
    wrap.id = "typing";
    wrap.innerHTML = `<div class="typing-indicator"><span></span><span></span><span></span></div>`;
    messagesEl.appendChild(wrap);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function removeTyping() {
    const el = document.getElementById("typing");
    if (el) el.remove();
  }

  async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text) return;
    inputEl.value = "";
    appendMessage("user", text);
    showTyping();

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: SESSION_ID }),
      });
      const data = await res.json();
      removeTyping();

      if (res.ok) {
        appendMessage("agent", data.reply);
      } else {
        appendMessage("agent", "Sorry, something went wrong. Please try again.");
      }
    } catch (err) {
      removeTyping();
      appendMessage("agent", "Cannot reach the BuySell agent. Please check the server.");
    }
  }
</script>
</body>
</html>
"""


@app.get("/widget", response_class=HTMLResponse)
def widget():
    """Serve the chat widget HTML page directly."""
    return HTMLResponse(content=WIDGET_HTML)


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
