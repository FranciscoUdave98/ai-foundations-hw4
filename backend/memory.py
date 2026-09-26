"""Customer memory: saved chat history for logged-in shoppers, plus what the agent may know about them.

Only logged-in customers get memory. Every function takes the user_id from the verified session
(never from the browser or the model), so one customer can never read another's history.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass

import tools
from db import connect
from models import ChatTurn, CustomerProfile, PageContext, PastProduct, PastProducts


@dataclass(frozen=True)
class Customer:
    """The logged-in shopper, as loaded from `users` via their session cookie."""

    user_id: int
    first_name: str
    last_name: str
    email: str
    member_since: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Customer:
        first, last = row["first_name"], row["last_name"]
        if not first:  # older rows only filled `name`
            first, _, last = (row["name"] or "").partition(" ")
        return cls(row["id"], first or "", last or "", row["email"], row["created_at"])


@dataclass(frozen=True)
class SavedMessage:
    id: int
    role: str
    content: str
    matches: list[tuple[str, str]]  # (product_id, match note)
    results_title: str | None
    created_at: str


def init_chat_tables() -> None:
    """Add the Problem 8 columns and index to chat_messages (safe to run on every start)."""
    with connect(readonly=False) as conn:
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(chat_messages)")}
        if "results_title" not in cols:
            conn.execute("ALTER TABLE chat_messages ADD COLUMN results_title TEXT")
        if "page_context_json" not in cols:
            conn.execute("ALTER TABLE chat_messages ADD COLUMN page_context_json TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages(user_id, id)")
        # Problem 9: one row per chat answer, to measure how often the cheaper model is used.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                model TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                reason TEXT,
                escalated INTEGER NOT NULL DEFAULT 0,
                input_tokens INTEGER NOT NULL DEFAULT 0,
                output_tokens INTEGER NOT NULL DEFAULT 0,
                requests INTEGER NOT NULL DEFAULT 0,
                logged_in INTEGER NOT NULL DEFAULT 0
            )
            """
        )


def _parse_matches(products_json: str | None) -> list[tuple[str, str]]:
    """(product_id, note) pairs from products_json (older seed rows hold full cards without notes)."""
    if not products_json:
        return []
    try:
        items = json.loads(products_json)
    except (ValueError, TypeError):
        return []
    return [(p["product_id"], p.get("match_note", "")) for p in items if isinstance(p, dict) and "product_id" in p]


def save_turn(
    customer: Customer,
    message: str,
    reply: str,
    matches: list[tuple[str, str]],
    results_title: str | None,
    page: PageContext | None,
) -> None:
    """Store the shopper's message and the assistant's reply together, in one transaction."""
    products_json = json.dumps([{"product_id": pid, "match_note": note} for pid, note in matches]) if matches else None
    page_json = page.model_dump_json(exclude_defaults=True) if page else None
    with connect(readonly=False) as conn:  # commits both rows or neither
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, page_context_json) VALUES (?, 'user', ?, ?)",
            (customer.user_id, message, page_json),
        )
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json, results_title) VALUES (?, 'assistant', ?, ?, ?)",
            (customer.user_id, reply, products_json, results_title),
        )


def load_messages(customer: Customer, limit: int) -> list[SavedMessage]:
    """The customer's most recent `limit` messages, oldest first."""
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, role, content, products_json, results_title, created_at
            FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?
            """,
            (customer.user_id, limit),
        ).fetchall()
    return [
        SavedMessage(r["id"], r["role"], r["content"], _parse_matches(r["products_json"]), r["results_title"], r["created_at"])
        for r in reversed(rows)
    ]


def history_for_agent(customer: Customer, turns: int) -> list[ChatTurn]:
    return [ChatTurn(role=m.role, content=m.content) for m in load_messages(customer, turns) if m.role in ("user", "assistant")]


def clear_history(customer: Customer) -> int:
    with connect(readonly=False) as conn:
        return conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (customer.user_id,)).rowcount


def customer_profile(customer: Customer | None) -> CustomerProfile:
    if customer is None:
        return CustomerProfile(logged_in=False)
    with connect() as conn:
        count, last = conn.execute(
            "SELECT COUNT(*), MAX(created_at) FROM chat_messages WHERE user_id = ?", (customer.user_id,)
        ).fetchone()
    return CustomerProfile(
        logged_in=True,
        first_name=customer.first_name,
        last_name=customer.last_name,
        email=customer.email,
        member_since=customer.member_since,
        saved_messages=count,
        last_chat_at=last,
    )


def past_products(customer: Customer | None, limit: int = 8) -> PastProducts:
    """Products the assistant showed this customer before, newest first, one entry per product."""
    if customer is None:
        return PastProducts(logged_in=False, note="The shopper is a guest, so there is no saved history.")
    with connect() as conn:
        rows = conn.execute(
            "SELECT products_json, created_at FROM chat_messages WHERE user_id = ? AND role = 'assistant' "
            "AND products_json IS NOT NULL ORDER BY id DESC",
            (customer.user_id,),
        ).fetchall()
    seen: dict[str, dict] = {}
    for row in rows:
        for pid, _ in _parse_matches(row["products_json"]):
            entry = seen.setdefault(pid, {"last": row["created_at"], "times": 0})
            entry["times"] += 1
    cards = {c.product_id: c for c in tools.get_product_cards(list(seen))}
    products = [
        PastProduct(product_id=pid, name=cards[pid].name, category=cards[pid].category, last_discussed=v["last"], times_shown=v["times"])
        for pid, v in seen.items()
        if pid in cards
    ][: max(1, min(limit, 12))]
    return PastProducts(logged_in=True, products=products, note="" if products else "No products in earlier chats yet.")


def log_run(model: str, difficulty: str, reason: str, escalated: bool, input_tokens: int, output_tokens: int,
            requests: int, logged_in: bool) -> None:
    """Record which model answered (no message text or customer id, just cost data)."""
    with connect(readonly=False) as conn:
        conn.execute(
            "INSERT INTO agent_runs (model, difficulty, reason, escalated, input_tokens, output_tokens, requests, logged_in) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (model, difficulty, reason[:160], int(escalated), input_tokens, output_tokens, requests, int(logged_in)),
        )
