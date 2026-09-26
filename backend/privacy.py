"""Data minimization: strip sensitive details from shopper messages before anything sees or stores them.

The chat never needs payment cards, government IDs, passwords, or phone numbers, so they are
replaced with a placeholder like "[removed: card number]" before the message reaches the model,
the chat history, or the audit trail. Only the *kind* of data removed is recorded, never the value.
"""

from __future__ import annotations

import re

_CARD = re.compile(r"\b\d(?:[ -]?\d){12,18}\b")
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_PHONE = re.compile(r"(?<!\d)(?:\+?1[ .-]?)?\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}(?!\d)")
_PASSWORD = re.compile(r"\b(pass(?:word|code)?|pwd|pin)\s*(?:is|:|=)\s*\S+", re.I)
_CVV = re.compile(r"\b(cvv|cvc|security code)\s*(?:is|:|=)?\s*\d{3,4}\b", re.I)


def _luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for d in reversed(digits):
        n = int(d)
        if alt:
            n = n * 2 - 9 if n * 2 > 9 else n * 2
        total += n
        alt = not alt
    return total % 10 == 0


def redact(text: str) -> tuple[str, list[str]]:
    """Return the message with sensitive data removed, plus the kinds that were removed."""
    kinds: list[str] = []

    def card(m: re.Match) -> str:
        digits = re.sub(r"\D", "", m.group(0))
        if 13 <= len(digits) <= 19 and _luhn_ok(digits):
            kinds.append("card number")
            return "[removed: card number]"
        return m.group(0)

    text = _CARD.sub(card, text)
    for pattern, kind in ((_CVV, "card security code"), (_SSN, "social security number"), (_PASSWORD, "password"), (_PHONE, "phone number")):
        if pattern.search(text):
            kinds.append(kind)
            text = pattern.sub(f"[removed: {kind}]", text)
    return text, list(dict.fromkeys(kinds))
