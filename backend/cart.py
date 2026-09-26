"""The shopping bag, and the confirmation gate for high-impact agent actions.

The agent may only *propose* adding an item. The proposal is stored as a pending action, and it
becomes real only when a later message from the customer explicitly confirms it. The check is
done here in code, not left to the model: the confirmation must come in a later turn than the
proposal, and the customer's own message must be an unambiguous "yes".
Bags exist only for logged-in customers (guests keep no server-side data).
"""

from __future__ import annotations

import json
import re
import secrets
from datetime import datetime, timedelta, timezone

import tools
from db import connect
from memory import Customer
from models import CartItem, CartView, PendingAction

MAX_PER_LINE = 5
PENDING_MINUTES = 30

_YES = re.compile(r"\b(yes|yeah|yep|yup|sure|ok|okay|confirm(?:ed)?|please do|do it|go ahead|add it|sounds good|absolutely|definitely|correct)\b", re.I)
_NO = re.compile(r"\b(no|nope|not|don't|dont|cancel|stop|wait|hold on|never ?mind|instead|actually)\b", re.I)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def init_cart_tables() -> None:
    with connect(readonly=False) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cart_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                product_id TEXT NOT NULL REFERENCES catalogue(product_id),
                size TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                added_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE (user_id, product_id, size)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pending_actions (
                action_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                kind TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                summary TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
            )
            """
        )


def is_explicit_yes(message: str) -> bool:
    """A clear confirmation: contains a yes-word and no hedging or negation."""
    return bool(_YES.search(message)) and not _NO.search(message)


def view_cart(customer: Customer) -> CartView:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, product_id, size, quantity FROM cart_items WHERE user_id = ? ORDER BY id", (customer.user_id,)
        ).fetchall()
    cards = {c.product_id: c for c in tools.get_product_cards([r["product_id"] for r in rows])}
    items = [
        CartItem(
            item_id=r["id"], product_id=r["product_id"], name=cards[r["product_id"]].name, size=r["size"],
            quantity=r["quantity"], unit_price=cards[r["product_id"]].price, image_url=cards[r["product_id"]].image_url,
        )
        for r in rows
        if r["product_id"] in cards
    ]
    return CartView(items=items, item_count=sum(i.quantity for i in items), subtotal=round(sum(i.quantity * i.unit_price for i in items), 2))


def add_item(customer: Customer, product_id: str, size: str, quantity: int) -> tuple[bool, str]:
    """Add to the bag after checking stock. Used by the site's own button and by confirmed agent actions."""
    size = tools.normalize_size(size)
    stock = tools.get_stock([product_id], size)
    if not stock.results:
        return False, "That product doesn't exist."
    s = stock.results[0].sizes[0]
    if not s.in_stock:
        return False, f"Size {size} is {s.status.replace('_', ' ')}."
    with connect(readonly=False) as conn:
        row = conn.execute(
            "SELECT quantity FROM cart_items WHERE user_id = ? AND product_id = ? AND size = ?", (customer.user_id, product_id, size)
        ).fetchone()
        new_qty = (row["quantity"] if row else 0) + quantity
        if new_qty > min(MAX_PER_LINE, s.quantity):
            return False, f"Only {min(MAX_PER_LINE, s.quantity)} per size can be in the bag (stock: {s.quantity})."
        conn.execute(
            "INSERT INTO cart_items (user_id, product_id, size, quantity) VALUES (?, ?, ?, ?) "
            "ON CONFLICT (user_id, product_id, size) DO UPDATE SET quantity = excluded.quantity",
            (customer.user_id, product_id, size, new_qty),
        )
    return True, "Added."


def remove_item(customer: Customer, item_id: int) -> bool:
    with connect(readonly=False) as conn:
        return conn.execute("DELETE FROM cart_items WHERE id = ? AND user_id = ?", (item_id, customer.user_id)).rowcount > 0


def propose_add(customer: Customer, product_id: str, size: str, quantity: int) -> PendingAction:
    """Create a pending 'add to bag' action. Nothing is added until the customer confirms."""
    size = tools.normalize_size(size)
    quantity = max(1, min(quantity, MAX_PER_LINE))
    stock = tools.get_stock([product_id], size)
    if not stock.results:
        return PendingAction(action_id="", summary="", status="rejected", message=f"No product with id {product_id!r}.")
    r = stock.results[0]
    s = r.sizes[0]
    if not s.in_stock or s.quantity < quantity:
        return PendingAction(action_id="", summary="", status="rejected", message=r.message)
    price = tools.get_prices([product_id]).prices[0].price_usd
    summary = f"Add {quantity} × {r.name} (size {size}, ${price:.0f} each) to your bag"
    action_id = secrets.token_hex(3).upper()
    with connect(readonly=False) as conn:
        conn.execute("UPDATE pending_actions SET status = 'superseded' WHERE user_id = ? AND status = 'pending'", (customer.user_id,))
        conn.execute(
            "INSERT INTO pending_actions (action_id, user_id, kind, payload_json, summary, created_at, expires_at) VALUES (?, ?, 'cart_add', ?, ?, ?, ?)",
            (action_id, customer.user_id, json.dumps({"product_id": product_id, "size": size, "quantity": quantity}),
             summary, _fmt(_now()), _fmt(_now() + timedelta(minutes=PENDING_MINUTES))),
        )
    return PendingAction(
        action_id=action_id, summary=summary, status="awaiting_confirmation",
        message="Nothing has been added yet. Ask the customer to confirm; only call confirm_add_to_cart after they say yes in their next message.",
    )


def pending_for(customer: Customer) -> list[PendingAction]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT action_id, summary FROM pending_actions WHERE user_id = ? AND status = 'pending' AND expires_at > ?",
            (customer.user_id, _fmt(_now())),
        ).fetchall()
    return [PendingAction(action_id=r["action_id"], summary=r["summary"], status="awaiting_confirmation") for r in rows]


def confirm_add(customer: Customer, action_id: str, customer_message: str, turn_started: datetime) -> PendingAction:
    """Carry out a pending action, but only with a clear, separate 'yes' from the customer."""
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM pending_actions WHERE action_id = ? AND user_id = ?", (action_id.upper().strip(), customer.user_id)
        ).fetchone()
    if row is None or row["status"] != "pending" or row["expires_at"] <= _fmt(_now()):
        return PendingAction(action_id=action_id, summary="", status="rejected", message="No pending action with that id. Propose it again.")
    if row["created_at"] >= _fmt(turn_started):
        return PendingAction(action_id=action_id, summary=row["summary"], status="awaiting_confirmation",
                             message="Proposed in this same turn. Ask the customer to confirm first; do not add anything yet.")
    if not is_explicit_yes(customer_message):
        return PendingAction(action_id=action_id, summary=row["summary"], status="awaiting_confirmation",
                             message="The customer's message is not a clear yes. Ask them to confirm explicitly (or cancel).")
    payload = json.loads(row["payload_json"])
    ok, why = add_item(customer, payload["product_id"], payload["size"], payload["quantity"])
    with connect(readonly=False) as conn:
        conn.execute("UPDATE pending_actions SET status = ? WHERE action_id = ?", ("confirmed" if ok else "failed", row["action_id"]))
    return PendingAction(action_id=row["action_id"], summary=row["summary"], status="done" if ok else "rejected", message=why)


def cancel(customer: Customer, action_id: str) -> PendingAction:
    with connect(readonly=False) as conn:
        n = conn.execute(
            "UPDATE pending_actions SET status = 'cancelled' WHERE action_id = ? AND user_id = ? AND status = 'pending'",
            (action_id.upper().strip(), customer.user_id),
        ).rowcount
    return PendingAction(action_id=action_id, summary="", status="cancelled" if n else "rejected",
                         message="Cancelled; nothing was added." if n else "No pending action with that id.")
