"""
auth_routes.py
==============
JWT-based authentication for Agentic RAG Platform.

Endpoints:
  POST /api/auth/register  — create new account
  POST /api/auth/login     — login, returns JWT
  GET  /api/auth/me        — verify token, return user info

Storage: SQLite (same DB as the rest of the app, via auth_users table).
Passwords: bcrypt-hashed (falls back to hashlib.pbkdf2 if bcrypt not installed).
Tokens: HS256 JWT signed with SECRET_KEY env var (default: random on startup).
"""

import os, sqlite3, time, uuid, hashlib, hmac
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel

# ── JWT (PyJWT) with graceful fallback ───────────────────────────────────────
try:
    import jwt as _jwt
    _JWT_AVAILABLE = True
except ImportError:
    _JWT_AVAILABLE = False

# ── bcrypt with graceful fallback to pbkdf2_hmac ────────────────────────────
try:
    import bcrypt as _bcrypt
    _BCRYPT_AVAILABLE = True
except ImportError:
    _BCRYPT_AVAILABLE = False

# ── Secret key (set SECRET_KEY env var in production!) ───────────────────────
_SECRET = os.environ.get("SECRET_KEY") or os.urandom(32).hex()
_ALGO   = "HS256"
_TOKEN_EXPIRE_HOURS = 72

# ── DB path — same folder as api_server.py ───────────────────────────────────
_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rag_data.db")


# ═══════════════════════════════════════════════════════════════════════════════
# DB helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _get_conn():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_auth_schema():
    """Create auth_users table if it doesn't exist."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS auth_users (
            user_id    TEXT PRIMARY KEY,
            username   TEXT UNIQUE NOT NULL,
            pwd_hash   TEXT NOT NULL,
            created_at REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print("[AUTH] Schema ready (auth_users table).")


# ═══════════════════════════════════════════════════════════════════════════════
# Password hashing
# ═══════════════════════════════════════════════════════════════════════════════

def _hash_password(password: str) -> str:
    if _BCRYPT_AVAILABLE:
        return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()
    # Fallback: PBKDF2-HMAC-SHA256
    salt = os.urandom(16).hex()
    dk   = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000)
    return f"pbkdf2:{salt}:{dk.hex()}"


def _check_password(password: str, pwd_hash: str) -> bool:
    if _BCRYPT_AVAILABLE and pwd_hash.startswith("$2"):
        return _bcrypt.checkpw(password.encode(), pwd_hash.encode())
    # Fallback
    try:
        _, salt, dk_hex = pwd_hash.split(":")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000)
        return hmac.compare_digest(dk.hex(), dk_hex)
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# JWT helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _make_token(user_id: str, username: str) -> str:
    payload = {
        "sub":      user_id,
        "username": username,
        "exp":      int(time.time()) + _TOKEN_EXPIRE_HOURS * 3600,
        "iat":      int(time.time()),
    }
    if _JWT_AVAILABLE:
        return _jwt.encode(payload, _SECRET, algorithm=_ALGO)
    # Minimal fallback: base64-encoded JSON + HMAC signature
    import base64, json
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    sig  = hmac.new(_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def _decode_token(token: str) -> dict:
    if _JWT_AVAILABLE:
        try:
            return _jwt.decode(token, _SECRET, algorithms=[_ALGO])
        except _jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired.")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token.")
    # Fallback
    try:
        import base64, json
        body, sig = token.rsplit(".", 1)
        expected  = hmac.new(_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise HTTPException(status_code=401, detail="Invalid token.")
        payload = json.loads(base64.urlsafe_b64decode(body + "=="))
        if payload.get("exp", 0) < time.time():
            raise HTTPException(status_code=401, detail="Token expired.")
        return payload
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token.")


# ═══════════════════════════════════════════════════════════════════════════════
# Dependency: extract + validate Bearer token
# ═══════════════════════════════════════════════════════════════════════════════

def get_current_user(authorization: Optional[str] = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header.")
    token = authorization.removeprefix("Bearer ").strip()
    return _decode_token(token)


# ═══════════════════════════════════════════════════════════════════════════════
# Request/response models
# ═══════════════════════════════════════════════════════════════════════════════

class RegisterRequest(BaseModel):
    username: str
    password: str
    email:    str = ""   # optional — used to send welcome email

class LoginRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    token:    str
    username: str
    user_id:  str


# ═══════════════════════════════════════════════════════════════════════════════
# Router
# ═══════════════════════════════════════════════════════════════════════════════

# ── MCP Email tool (welcome email on registration) ───────────────────────────
try:
    from mcp_email import mcp_send_welcome_email as _send_welcome
    _EMAIL_MCP_AVAILABLE = True
except ImportError:
    _EMAIL_MCP_AVAILABLE = False
    print("[AUTH] mcp_email.py not found — welcome emails disabled")

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest):
    """Create a new user account and return a JWT."""
    username = req.username.strip().lower()
    password = req.password

    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters.")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    conn = _get_conn()
    try:
        existing = conn.execute(
            "SELECT user_id FROM auth_users WHERE username = ?", (username,)
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Username already taken.")

        user_id  = str(uuid.uuid4())
        pwd_hash = _hash_password(password)
        conn.execute(
            "INSERT INTO auth_users (user_id, username, pwd_hash, created_at) VALUES (?,?,?,?)",
            (user_id, username, pwd_hash, time.time()),
        )
        conn.commit()
    finally:
        conn.close()

    token = _make_token(user_id, username)
    print(f"[AUTH] Registered new user: {username} ({user_id})")

    # ── MCP Tool: send welcome email (fire-and-forget, never blocks) ──────────
    if _EMAIL_MCP_AVAILABLE and req.email.strip():
        import threading
        threading.Thread(
            target=_send_welcome,
            args=(username, req.email.strip()),
            daemon=True,
        ).start()

    return AuthResponse(token=token, username=username, user_id=user_id)


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest):
    """Authenticate and return a fresh JWT."""
    username = req.username.strip().lower()
    password = req.password

    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT user_id, pwd_hash FROM auth_users WHERE username = ?", (username,)
        ).fetchone()
    finally:
        conn.close()

    if not row or not _check_password(password, row["pwd_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    token = _make_token(row["user_id"], username)
    print(f"[AUTH] Login: {username}")
    return AuthResponse(token=token, username=username, user_id=row["user_id"])


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    """Return info about the currently authenticated user."""
    return {
        "user_id":  current_user["sub"],
        "username": current_user["username"],
    }
