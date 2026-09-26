"""Campus Customs shop API: products, stock, accounts, and the shop chatbot.

Run from HW4/backend with the virtual environment active:
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Cookie, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded

import cart
import memory
import tools
from audit import AuditRun
from privacy import redact
from agent import QUICK_MODEL, ShopDeps, resolve_page_context, run_chat
from auth import ensure_seed_user, init_auth_tables, user_from_token
from auth import router as auth_router
from db import DATA_DIR, DB_PATH
from memory import Customer
from status import StatusFeed
from models import (
    CartAddRequest,
    CartView,
    ChatHistoryMessage,
    ChatReply,
    ChatRequest,
    MatchedProduct,
    ProductCard,
    ProductDetail,
    RelatedProduct,
)

log = logging.getLogger("uvicorn.error")
HISTORY_TURNS = 12  # earlier messages sent to the agent for context
HISTORY_SHOWN = 40  # messages restored in the chat widget
FILTERED_REPLY = (
    "I can only help with Campus Customs products, sizes, prices, and stock. "
    "What can I help you find today?"
)


def _is_content_filter(err: ModelHTTPError) -> bool:
    body = err.body if isinstance(err.body, dict) else {}
    return body.get("code") == "content_filter" or "content_filter" in str(body)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_auth_tables()
    memory.init_chat_tables()
    cart.init_cart_tables()
    ensure_seed_user()
    yield


app = FastAPI(title="Campus Customs API", version="0.3.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)
app.include_router(auth_router)
# Only the product photos are public; the database file next to them is not.
app.mount("/images/products", StaticFiles(directory=DATA_DIR / "products"), name="product-images")
# Optional AI-generated on-model photos (data/on_model/<product_id>.jpg); the folder may be empty.
(DATA_DIR / "on_model").mkdir(exist_ok=True)
app.mount("/images/on_model", StaticFiles(directory=DATA_DIR / "on_model"), name="on-model-images")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "database": DB_PATH.exists()}


# --- Products -------------------------------------------------------------------------------


@app.get("/api/products", response_model=list[ProductCard])
def list_products(q: str | None = None, category_name: str | None = None) -> list[ProductCard]:
    if q or category_name:
        return tools.search_cards(query=q, category_name=category_name)
    return tools.list_product_cards()


@app.get("/api/products/{product_id}/related", response_model=list[RelatedProduct])
def related(product_id: str, limit: int = 10) -> list[RelatedProduct]:
    if tools.get_product_info(product_id) is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return tools.related_products(product_id, limit)


@app.get("/api/products/{product_id}", response_model=ProductDetail)
def get_product(product_id: str) -> ProductDetail:
    detail = tools.get_product_detail(product_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return detail


# --- Chat -----------------------------------------------------------------------------------


def _current_customer(cc_session: str | None) -> Customer | None:
    """The logged-in shopper from the verified session cookie, or None for a guest."""
    row = user_from_token(cc_session)
    return Customer.from_row(row) if row else None


def _matched_products(matches: list[tuple[str, str]]) -> list[MatchedProduct]:
    """Build page-ready cards from (product_id, note) pairs using live catalogue data."""
    notes = dict(matches)
    cards = tools.get_product_cards([pid for pid, _ in matches])
    return [MatchedProduct(**c.model_dump(), match_note=notes.get(c.product_id, "")) for c in cards]


async def _answer(request: ChatRequest, customer: Customer | None, status: StatusFeed) -> ChatReply:
    """One chat turn: redact, route to a model, run the agent, build cards, save history, audit and log cost."""
    # Data minimization: sensitive details never reach the model, the history, or the audit trail.
    message, removed = redact(request.message)
    request = request.model_copy(update={"message": message})
    audit = AuditRun()
    audit(
        "run_start",
        args={"customer": "logged_in" if customer else "guest", "page": request.page.page_type if request.page else None,
              "message_chars": len(message), "removed": removed},
        reason="New shopper message",
    )
    if customer:  # logged in: the saved conversation is the source of truth
        history = memory.history_for_agent(customer, HISTORY_TURNS)
    else:  # guest: the browser sends the conversation so far; nothing is stored
        history = request.history[-HISTORY_TURNS:]
    deps = ShopDeps(customer=customer, page=resolve_page_context(request.page), status=status, audit=audit, redacted=removed)

    try:
        outcome = await run_chat(request.message, history, deps)
    except ModelHTTPError as err:
        if not _is_content_filter(err):
            log.exception("Chat agent failed")
            raise HTTPException(503, "Our shopping assistant is unavailable right now. Please try again in a moment.") from None
        # The provider's safety filter blocked the message (e.g. a jailbreak attempt): answer politely.
        log.info("Chat message blocked by the provider's content filter")
        audit("run_end", result="blocked by provider content filter", reason="Safety filter")
        return ChatReply(reply=FILTERED_REPLY)
    except UsageLimitExceeded:
        log.warning("Chat hit the agent usage limit")
        audit("run_end", result="usage limit exceeded", reason="Loop limit reached")
        raise HTTPException(503, "That question took too many steps. Could you ask it a bit more simply?") from None
    except Exception as err:
        log.exception("Chat agent failed")
        audit("run_end", result=f"error: {type(err).__name__}", reason="Agent failure")
        raise HTTPException(503, "Our shopping assistant is unavailable right now. Please try again in a moment.") from None

    output = outcome.output
    log.info(
        "chat answered by %s (%s%s): %s | tokens in=%d out=%d",
        outcome.model, outcome.difficulty, ", escalated" if outcome.escalated else "", outcome.reason,
        outcome.input_tokens, outcome.output_tokens,
    )
    memory.log_run(
        outcome.model, outcome.difficulty, outcome.reason, outcome.escalated,
        outcome.input_tokens, outcome.output_tokens, outcome.requests, customer is not None,
    )
    matches = [(m.product_id, m.why) for m in output.matches]
    products = _matched_products(matches)
    title = output.results_title if products else None
    if customer:
        memory.save_turn(customer, request.message, output.reply, matches, title, request.page)
    audit(
        "run_end",
        result={"model": outcome.model, "matches": [p.product_id for p in products], "reply_chars": len(output.reply),
                "tokens_in": outcome.input_tokens, "tokens_out": outcome.output_tokens, "escalated": outcome.escalated},
        reason=f"Answered ({outcome.difficulty})",
    )
    return ChatReply(
        reply=output.reply,
        results_title=title,
        products=products,
        answered_by="quick" if outcome.model == QUICK_MODEL else "expert",
    )


@app.post("/api/chat", response_model=ChatReply)
async def chat(request: ChatRequest, cc_session: str | None = Cookie(default=None)) -> ChatReply:
    return await _answer(request, _current_customer(cc_session), StatusFeed())


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest, cc_session: str | None = Cookie(default=None)) -> StreamingResponse:
    """Same as /api/chat, but streams newline-delimited JSON: status lines while the agent works, then the reply.

    {"type": "status", "text": "Hunting for Mediums…"}
    {"type": "reply", "reply": "...", "results_title": ..., "products": [...], "answered_by": "quick"}
    {"type": "error", "detail": "..."}
    """
    customer = _current_customer(cc_session)
    queue: asyncio.Queue[dict | None] = asyncio.Queue()
    status = StatusFeed(lambda text: queue.put_nowait({"type": "status", "text": text}))

    async def work() -> None:
        try:
            reply = await _answer(request, customer, status)
            queue.put_nowait({"type": "reply", **reply.model_dump()})
        except HTTPException as err:
            queue.put_nowait({"type": "error", "detail": err.detail})
        finally:
            queue.put_nowait(None)

    async def events() -> AsyncIterator[str]:
        task = asyncio.create_task(work())
        try:
            while (item := await queue.get()) is not None:
                yield json.dumps(item) + "\n"
        finally:
            if not task.done():  # the shopper closed the chat mid-answer
                task.cancel()

    return StreamingResponse(events(), media_type="application/x-ndjson", headers={"Cache-Control": "no-cache"})


@app.get("/api/chat/history", response_model=list[ChatHistoryMessage])
def chat_history(cc_session: str | None = Cookie(default=None)) -> list[ChatHistoryMessage]:
    customer = _current_customer(cc_session)
    if customer is None:
        raise HTTPException(401, "Log in to see your saved chat.")
    return [
        ChatHistoryMessage(
            id=m.id,
            role=m.role,
            content=m.content,
            results_title=m.results_title,
            products=_matched_products(m.matches),
            created_at=m.created_at,
        )
        for m in memory.load_messages(customer, HISTORY_SHOWN)
    ]


@app.delete("/api/chat/history")
def clear_chat_history(cc_session: str | None = Cookie(default=None)) -> dict:
    customer = _current_customer(cc_session)
    if customer is None:
        raise HTTPException(401, "Log in to manage your saved chat.")
    return {"deleted": memory.clear_history(customer)}


# --- Bag (logged-in customers only) -------------------------------------------------------------


def _require_customer(cc_session: str | None) -> Customer:
    customer = _current_customer(cc_session)
    if customer is None:
        raise HTTPException(401, "Log in to use your bag.")
    return customer


@app.get("/api/cart", response_model=CartView)
def get_cart(cc_session: str | None = Cookie(default=None)) -> CartView:
    customer = _current_customer(cc_session)
    return cart.view_cart(customer) if customer else CartView()


@app.post("/api/cart", response_model=CartView)
def add_to_cart(body: CartAddRequest, cc_session: str | None = Cookie(default=None)) -> CartView:
    """The site's "Add to bag" button: the customer's own click is the explicit authorization."""
    customer = _require_customer(cc_session)
    ok, why = cart.add_item(customer, body.product_id, body.size, body.quantity)
    if not ok:
        raise HTTPException(409, why)
    AuditRun()("cart_add", tool="site_button", args=body.model_dump(), result="added", reason="Customer clicked Add to bag")
    return cart.view_cart(customer)


@app.delete("/api/cart/{item_id}", response_model=CartView)
def remove_from_cart(item_id: int, cc_session: str | None = Cookie(default=None)) -> CartView:
    customer = _require_customer(cc_session)
    if not cart.remove_item(customer, item_id):
        raise HTTPException(404, "That item isn't in your bag.")
    AuditRun()("cart_remove", tool="site_button", args={"item_id": item_id}, result="removed", reason="Customer clicked Remove")
    return cart.view_cart(customer)
