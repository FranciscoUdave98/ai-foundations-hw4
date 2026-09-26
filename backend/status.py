"""Fun, specific "thinking" messages the chat shows while the agent works.

Each agent step or tool call announces what it is doing ("Hunting for Mediums…"). Messages are
picked at random from themed pools, filled in with the real search details, and never repeat
back to back.
"""

from __future__ import annotations

import random
from collections.abc import Callable

SIZE_PLURALS = {"XS": "Extra Smalls", "S": "Smalls", "M": "Mediums", "L": "Larges", "XL": "XLs", "XXL": "Double XLs"}

MESSAGES: dict[str, list[str]] = {
    "routing": [
        "Reading your question like the last page of a blue book…",
        "Sizing up your question (pun fully intended)…",
        "Putting on our thinking cap. Yale blue, naturally…",
    ],
    "route_simple": [
        "Easy one! Sending our speediest Bulldog…",
        "Quick question, quick paws. On it!",
        "This one's a layup. Grabbing it now…",
    ],
    "route_complex": [
        "Ooh, a thinker! Calling in the senior Bulldog…",
        "This one deserves the full seminar treatment…",
        "Big question energy. Bringing out the expert…",
    ],
    "search": [
        "Rummaging through the Broadway stockroom for {query}…",
        "Asking Handsome Dan to sniff out {query}…",
        "Flipping through every hanger for {query}…",
    ],
    "search_size": [
        "Hunting for {size_plural}. They vanish faster than move-in week snacks…",
        "Measuring twice, searching for {size_plural} once…",
        "Checking which racks still have {size_plural}…",
    ],
    "search_color": [
        "Sorting the {color} gear from the rest of the rack…",
        "Squinting at every shade of {color} we own…",
        "Holding {color} swatches up to the light…",
    ],
    "stock": [
        "Counting sizes in the back room (no Bulldogs were harmed)…",
        "Checking the shelves, the back room, and under the counter…",
        "Doing inventory faster than a Commons lunch line…",
    ],
    "stock_size": [
        "Checking if a {size} is hiding in the back…",
        "Counting {size_plural} one by one…",
        "Asking the stockroom: any {size_plural} left?",
    ],
    "prices": [
        "Reading the price tags (no haggling, we promise)…",
        "Consulting the cash register…",
        "Checking prices. Sadly there's no Harvard discount…",
    ],
    "info": [
        "Reading the fine print on the tag…",
        "Taking a closer look at the stitching…",
        "Inspecting the crest up close…",
    ],
    "overview": [
        "Taking a quick lap around the whole store…",
        "Walking every aisle, from tees to fleece…",
    ],
    "profile": [
        "Checking the name on the shopping bag…",
        "Looking up your account, politely…",
    ],
    "memory": [
        "Flipping back through our chat notebook…",
        "Remembering what caught your eye last time…",
    ],
    "page": [
        "Peeking at what's on your screen…",
        "Checking which page you're browsing…",
    ],
    "recheck": [
        "Double-checking the numbers with the cashier…",
        "Our fact-checker (strict, like a TA) wants one more look…",
    ],
    "escalate": [
        "Handing this one to the senior Bulldog for a second opinion…",
        "Getting a second opinion from the expert…",
    ],
    "writing": [
        "Folding everything neatly into an answer…",
        "Wrapping it up with a bow (Yale blue, of course)…",
    ],
}


class StatusFeed:
    """Sends status lines to a callback (the streaming chat route), skipping immediate repeats."""

    def __init__(self, send: Callable[[str], None] | None = None, rng: random.Random | None = None):
        self._send = send
        self._rng = rng or random.Random()
        self._last = ""
        self.sent: list[str] = []

    def __call__(self, key: str, **details: str | None) -> None:
        if self._send is None:
            return
        size = (details.get("size") or "").upper() or None
        fill = {
            "query": (details.get("query") or "the perfect pick").strip()[:40],
            "color": (details.get("color") or "").strip()[:20],
            "size": size or "",
            "size_plural": SIZE_PLURALS.get(size or "", f"size {size}s" if size else "sizes"),
        }
        options = [m.format(**fill) for m in MESSAGES.get(key, [])] or ["Working on it…"]
        choices = [m for m in options if m != self._last] or options
        text = self._rng.choice(choices)
        self._last = text
        self.sent.append(text)
        self._send(text)
