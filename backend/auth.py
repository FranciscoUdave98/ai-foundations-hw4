"""Accounts: create account, log in, log out, and "who am I" for the Campus Customs site.

Passwords are never stored. Each user row keeps a salted PBKDF2-SHA256 hash; sessions are
random tokens sent in an HttpOnly cookie, and only a SHA-256 of each token is stored.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator

from db import connect

router = APIRouter(prefix="/api/auth", tags=["auth"])

# --- Password hashing -------------------------------------------------------------------

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000  # OWASP 2023 recommendation for PBKDF2-HMAC-SHA256
LEGACY_ITERATIONS = 120_000  # hashes in the provided seed database: pbkdf2_sha256$salt$hash
SALT_BYTES = 16


def hash_password(password: str, *, iterations: int = ITERATIONS, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()
    return f"{ALGORITHM}${iterations}${salt}${digest}"


def _parse(stored: str) -> tuple[int, str, str] | None:
    parts = stored.split("$")
    if parts[0] != ALGORITHM:
        return None
    if len(parts) == 4:
        return int(parts[1]), parts[2], parts[3]
    if len(parts) == 3:
        return LEGACY_ITERATIONS, parts[1], parts[2]
    return None


def verify_password(password: str, stored: str) -> bool:
    parsed = _parse(stored)
    if parsed is None:
        return False
    iterations, salt, digest = parsed
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()
    return hmac.compare_digest(candidate, digest)


def needs_rehash(stored: str) -> bool:
    parsed = _parse(stored)
    return parsed is None or parsed[0] < ITERATIONS


# Used when an email isn't registered, so a failed login takes the same time either way.
_DUMMY_HASH = hash_password(secrets.token_hex(16))

# --- Sessions ---------------------------------------------------------------------------

SESSION_COOKIE = "cc_session"
SESSION_DAYS = 7
COOKIE_SECURE = False  # set True when served over HTTPS


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def init_auth_tables() -> None:
    with connect(readonly=False) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                expires_at TEXT NOT NULL
            )
            """
        )
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (_fmt(_now()),))


def ensure_seed_user() -> None:
    """The test account must always exist: test@campuscustoms.yale.edu / password."""
    with connect(readonly=False) as conn:
        exists = conn.execute("SELECT 1 FROM users WHERE email = ?", ("test@campuscustoms.yale.edu",)).fetchone()
        if not exists:
            conn.execute(
                "INSERT INTO users (name, first_name, last_name, email, password_hash) VALUES (?, ?, ?, ?, ?)",
                ("Test User", "Test", "User", "test@campuscustoms.yale.edu", hash_password("password")),
            )


def _start_session(response: Response, user_id: int) -> None:
    token = secrets.token_urlsafe(32)
    with connect(readonly=False) as conn:
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
            (_token_hash(token), user_id, _fmt(_now() + timedelta(days=SESSION_DAYS))),
        )
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_DAYS * 24 * 3600,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        path="/",
    )


def user_from_token(token: str | None):
    if not token:
        return None
    with connect() as conn:
        return conn.execute(
            """
            SELECT u.id, u.first_name, u.last_name, u.name, u.email, u.created_at
            FROM sessions s JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = ? AND s.expires_at > ?
            """,
            (_token_hash(token), _fmt(_now())),
        ).fetchone()


# --- Brute-force protection -------------------------------------------------------------

MAX_FAILURES = 5
WINDOW_SECONDS = 15 * 60
_failures: dict[str, deque[float]] = defaultdict(deque)


def _limit_key(request: Request, email: str) -> str:
    return f"{request.client.host if request.client else '?'}|{email}"


def _check_rate_limit(key: str) -> None:
    attempts = _failures[key]
    while attempts and attempts[0] < time.monotonic() - WINDOW_SECONDS:
        attempts.popleft()
    if len(attempts) >= MAX_FAILURES:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many failed attempts. Please wait a few minutes and try again.",
        )


# --- API models -------------------------------------------------------------------------

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _clean_email(value: str) -> str:
    value = value.strip().lower()
    if not EMAIL_RE.match(value) or len(value) > 254:
        raise ValueError("Enter a valid email address.")
    return value


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    email: str
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str

    @field_validator("first_name", "last_name")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("This field is required.")
        return v

    @field_validator("email")
    @classmethod
    def _valid_email(cls, v: str) -> str:
        return _clean_email(v)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    created_at: str


def _user_out(row) -> UserOut:
    first, last = row["first_name"], row["last_name"]
    if not first:  # older rows only filled `name`
        first, _, last = (row["name"] or "").partition(" ")
    return UserOut(id=row["id"], first_name=first or "", last_name=last or "", email=row["email"], created_at=row["created_at"])


# --- Routes -----------------------------------------------------------------------------


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, response: Response) -> UserOut:
    if body.password != body.confirm_password:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Passwords don't match.")
    with connect(readonly=False) as conn:
        if conn.execute("SELECT 1 FROM users WHERE email = ?", (body.email,)).fetchone():
            raise HTTPException(status.HTTP_409_CONFLICT, "An account with that email already exists. Try logging in.")
        cur = conn.execute(
            "INSERT INTO users (name, first_name, last_name, email, password_hash) VALUES (?, ?, ?, ?, ?)",
            (f"{body.first_name} {body.last_name}", body.first_name, body.last_name, body.email, hash_password(body.password)),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    _start_session(response, row["id"])
    return _user_out(row)


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, request: Request, response: Response) -> UserOut:
    key = _limit_key(request, body.email)
    _check_rate_limit(key)
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (body.email,)).fetchone()
    stored = row["password_hash"] if row else _DUMMY_HASH
    valid = verify_password(body.password, stored)  # always hash, even for unknown emails
    if row is None or not valid:
        _failures[key].append(time.monotonic())
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password.")
    _failures.pop(key, None)
    if needs_rehash(stored):  # upgrade older, weaker hashes now that we know the password
        with connect(readonly=False) as conn:
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(body.password), row["id"]))
    _start_session(response, row["id"])
    return _user_out(row)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(cc_session: str | None = Cookie(default=None)) -> Response:
    if cc_session:
        with connect(readonly=False) as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(cc_session),))
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@router.get("/me", response_model=UserOut)
def me(cc_session: str | None = Cookie(default=None)) -> UserOut:
    row = user_from_token(cc_session)
    if row is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not logged in.")
    return _user_out(row)
