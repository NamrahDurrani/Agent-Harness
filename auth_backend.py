"""
auth_backend.py
================
Minimal JWT auth for the Agentic RAG platform. Self-contained SQLite
users table (separate from rag_pipeline.db is fine, or reuse the same
file — see init_auth_db()).

Wire into api_server.py with:

    from auth_backend import auth_router, get_current_user, init_auth_db
    init_auth_db()
    app.include_router(auth_router)

Then protect any route with:

    @app.get("/api/sessions")
    def list_sessions(user: dict = Depends(get_current_user)):
        ...

Endpoints:
    POST /api/auth/register  {username, password}      -> {token, username}
    POST /api/auth/login     {username, password}       -> {token, username}
    GET  /api/auth/me        (Bearer token)              -> {username}

Passwords are hashed with bcrypt (passlib). Tokens are signed JWTs
(python-jose) with a 7-day expiry. This is intentionally simple —
no refresh tokens, no email verification, no password reset — that's
the right scope for a thesis-timeline project. Swap for something
heavier (e.g. fastapi-users) only if you have time to spare, which
you don't today.

pip install python-jose[cryptography] passlib[bcrypt] --break-system-packages
"""

import os
import sqlite3
import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError

# ── Config ────────────────────────────────────────────────────────────────────
# CHANGE THIS in production — put it in an env var. Fine to hardcode for a
# same-day demo, just don't commit it to a public repo.
JWT_SECRET     = os.environ.get("JWT_SECRET", "change-me-please-9hr-deadline")
JWT_ALGORITHM  = "HS256"
JWT_EXPIRE_DAYS = 7

AUTH_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auth.db")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


# ── DB ────────────────────────────────────────────────────────────────────────
def init_auth_db():
    conn = sqlite3.connect(AUTH_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     TEXT PRIMARY KEY,
            username    TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()
    print(f"[AUTH] DB ready at {AUTH_DB_PATH}")


def _get_conn():
    conn = sqlite3.connect(AUTH_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Token helpers ─────────────────────────────────────────────────────────────
def create_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRE_DAYS)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """FastAPI dependency — use `user=Depends(get_current_user)` on any
    route you want to require login for."""
    if creds is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    username = decode_token(creds.credentials)
    conn = _get_conn()
    row = conn.execute("SELECT user_id, username FROM users WHERE username=?",
                        (username,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=401, detail="User not found")
    return {"user_id": row["user_id"], "username": row["username"]}


def get_current_user_optional(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict | None:
    """Same as above but returns None instead of raising — use this if you
    want chat to work for anonymous users too, with extra features for
    logged-in ones."""
    if creds is None:
        return None
    try:
        return get_current_user(creds)
    except HTTPException:
        return None


# ── Router ────────────────────────────────────────────────────────────────────
auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    token: str
    username: str


@auth_router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest):
    username = req.username.strip()
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    conn = _get_conn()
    existing = conn.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=409, detail="Username already taken")

    import uuid
    user_id = str(uuid.uuid4())
    password_hash = pwd_context.hash(req.password)
    conn.execute(
        "INSERT INTO users (user_id, username, password_hash) VALUES (?, ?, ?)",
        (user_id, username, password_hash),
    )
    conn.commit()
    conn.close()

    token = create_token(username)
    return AuthResponse(token=token, username=username)


@auth_router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest):
    conn = _get_conn()
    row = conn.execute("SELECT password_hash FROM users WHERE username=?",
                        (req.username.strip(),)).fetchone()
    conn.close()
    if not row or not pwd_context.verify(req.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_token(req.username.strip())
    return AuthResponse(token=token, username=req.username.strip())


@auth_router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return user
