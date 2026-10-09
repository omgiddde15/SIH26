"""
LunarReg — Authentication Layer (UI-only access control).

Isolated module. Never touches registration mathematics or matching algorithms.

Provides:
  - SQLite-backed user accounts at data/users.db
  - PBKDF2-HMAC-SHA256 password hashing with random 16-byte salt
  - Email normalized to lowercase
  - Duplicate-email rejection at sign-up
  - Streamlit session-state login/logout helpers
  - render_auth_page() — polished Login / Sign Up UI (lunar/space theme)
"""

import os
import sys
import sqlite3
import hashlib
import secrets
import base64
from pathlib import Path
from typing import Optional, Tuple

import streamlit as st

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(APP_DIR)

__all__ = [
    "DB_DIR",
    "DB_PATH",
    "HERO_IMAGE_PATH",
    "init_auth_db",
    "hash_password",
    "verify_password",
    "create_user",
    "authenticate_user",
    "is_authenticated",
    "set_authenticated",
    "logout_user",
    "DEMO_USER_NAME",
    "DEMO_USER_EMAIL",
    "get_or_create_demo_user",
    "is_demo_session",
    "handle_quick_demo_access",
    "render_auth_page",
]

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DB_DIR = os.path.join(PROJECT_DIR, "data")
DB_PATH = os.path.join(DB_DIR, "users.db")

HERO_IMAGE_PATH = str((Path(APP_DIR) / "assets" / "lunar_login_background.png").resolve())


def _hero_image_data_uri(image_path: str) -> str:
    """Return a robust data URI for a local image so Streamlit can render it reliably."""
    path = Path(image_path).resolve()
    print(f"[LunarReg] Hero image path: {path} exists={path.exists()}")
    if not path.exists():
        return ""

    suffix = path.suffix.lower()
    if suffix == ".png":
        mime_type = "image/png"
    elif suffix in {".jpg", ".jpeg"}:
        mime_type = "image/jpeg"
    elif suffix == ".webp":
        mime_type = "image/webp"
    else:
        mime_type = "application/octet-stream"

    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


# ---------------------------------------------------------------------------
# Crypto
# ---------------------------------------------------------------------------

_PBKDF2_ITERATIONS = 240_000
_SALT_BYTES = 16
_HASH_ALGO = "sha256"
_SEPARATOR = "$"


def hash_password(password: str) -> str:
    """Return a salted PBKDF2-HMAC hash string. Never stores plaintext."""
    salt = secrets.token_bytes(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(
        _HASH_ALGO,
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )
    salt_b64 = base64.b64encode(salt).decode("ascii")
    hash_b64 = base64.b64encode(dk).decode("ascii")
    return f"{_PBKDF2_ITERATIONS}{_SEPARATOR}{salt_b64}{_SEPARATOR}{hash_b64}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a plaintext password against a stored hash string."""
    if not isinstance(stored_hash, str) or stored_hash.count(_SEPARATOR) != 2:
        return False
    try:
        iter_str, salt_b64, hash_b64 = stored_hash.split(_SEPARATOR)
        iterations = int(iter_str)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
    except Exception:
        return False
    dk = hashlib.pbkdf2_hmac(
        _HASH_ALGO,
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return secrets.compare_digest(dk, expected)


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def init_auth_db() -> None:
    """Create data/users.db (idempotent) with the users table and ensure schema matches."""
    os.makedirs(DB_DIR, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        # Check if table exists and has proper columns
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cur.fetchone() is not None:
            cur.execute("PRAGMA table_info(users)")
            cols = {col[1] for col in cur.fetchall()}
            if "salt" in cols and "email" in cols and "password_hash" in cols:
                # Legacy table detected with salt NOT NULL; clean up to modern schema
                cur.execute("ALTER TABLE users RENAME TO users_legacy_backup")
                cur.execute(
                    """
                    CREATE TABLE users (
                        id           INTEGER PRIMARY KEY AUTOINCREMENT,
                        full_name    TEXT NOT NULL,
                        email        TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        created_at   TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                    """
                )
                cur.execute("DROP TABLE users_legacy_backup")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name    TEXT NOT NULL,
                email        TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at   TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()

    _bootstrap_deployment_user()


def _get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def create_user(full_name: str, email: str, password: str) -> Tuple[bool, str]:
    """
    Insert a new user record.
    Returns (success: bool, message: str).
    Rejects duplicate emails (lowercase comparison).
    """
    if not full_name or not full_name.strip():
        return False, "Full name is required."
    if not email or "@" not in email:
        return False, "Please enter a valid email address."
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters."

    email_norm = email.strip().lower()
    name_clean = full_name.strip()

    with _get_conn() as conn:
        cur = conn.execute("SELECT id FROM users WHERE email = ?", (email_norm,))
        if cur.fetchone() is not None:
            return False, "An account with this email already exists. Please sign in instead."

        pw_hash = hash_password(password)
        try:
            conn.execute(
                "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
                (name_clean, email_norm, pw_hash),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return False, "An account with this email already exists. Please sign in instead."

    return True, "Account created successfully. You may now sign in."


def _get_bootstrap_secret(key: str) -> Optional[str]:
    """Safely retrieve a bootstrap secret from Streamlit secrets or environment variables."""
    # 1. Attempt Streamlit secrets retrieval
    try:
        if key in st.secrets:
            val = st.secrets[key]
            if val is not None and str(val).strip():
                return str(val)
        key_lower = key.lower()
        if key_lower in st.secrets:
            val = st.secrets[key_lower]
            if val is not None and str(val).strip():
                return str(val)
        for section in ("auth", "lunarreg", "general"):
            if section in st.secrets and isinstance(st.secrets[section], dict):
                sec_dict = st.secrets[section]
                if key in sec_dict and sec_dict[key] is not None and str(sec_dict[key]).strip():
                    return str(sec_dict[key])
                if key_lower in sec_dict and sec_dict[key_lower] is not None and str(sec_dict[key_lower]).strip():
                    return str(sec_dict[key_lower])
    except Exception:
        pass

    # 2. Fallback to environment variables
    if key in os.environ:
        val = os.environ[key]
        if val is not None and str(val).strip():
            return str(val)
    key_lower = key.lower()
    if key_lower in os.environ:
        val = os.environ[key_lower]
        if val is not None and str(val).strip():
            return str(val)

    return None


def _bootstrap_deployment_user() -> None:
    """
    Optionally provision an initial deployment operator account from Streamlit secrets
    or environment variables.
    Idempotent: skips provisioning if user already exists or secrets are absent.
    Never overwrites existing passwords.
    Surfaces unexpected database/programming errors for deployment diagnostics.
    """
    name = _get_bootstrap_secret("LUNARREG_BOOTSTRAP_NAME")
    email = _get_bootstrap_secret("LUNARREG_BOOTSTRAP_EMAIL")
    password = _get_bootstrap_secret("LUNARREG_BOOTSTRAP_PASSWORD")

    if not (name and email and password):
        return

    name_clean = name.strip()
    email_norm = email.strip().lower()

    if not name_clean or not email_norm:
        return

    conn = _get_conn()
    try:
        cur = conn.execute("SELECT id FROM users WHERE email = ?", (email_norm,))
        if cur.fetchone() is not None:
            return
    finally:
        conn.close()

    create_user(name_clean, email_norm, password)


def authenticate_user(email: str, password: str) -> Optional[Tuple[str, str, str]]:
    """
    Verify credentials.
    Returns (user_id, full_name, email) on success, or None.
    """
    if not email or not password:
        return None
    email_norm = email.strip().lower()
    with _get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT id, full_name, email, password_hash FROM users WHERE email = ?",
            (email_norm,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    if not verify_password(password, row["password_hash"]):
        return None
    return (str(row["id"]), row["full_name"], row["email"])


# ---------------------------------------------------------------------------
# Session-state helpers
# ---------------------------------------------------------------------------

def is_authenticated() -> bool:
    return bool(
        st.session_state.get("auth_authenticated", False)
        and st.session_state.get("auth_email")
    )


def set_authenticated(user_id: str, full_name: str, email: str) -> None:
    st.session_state["auth_authenticated"] = True
    st.session_state["auth_user_id"] = user_id
    st.session_state["auth_name"] = full_name
    st.session_state["auth_email"] = email


def logout_user() -> None:
    """Clear the complete per-browser session before returning to authentication.

    This function is invoked from a Streamlit button callback, which runs before
    the next script render.  Clearing state there means navigation widgets are
    recreated cleanly on a later authenticated session and no result, upload, or
    operator data can remain visible after sign-out.
    """
    for key in list(st.session_state.keys()):
        del st.session_state[key]


# ---------------------------------------------------------------------------
# Quick Demo Access for Evaluation / Demonstration
# ---------------------------------------------------------------------------

DEMO_USER_NAME = "LunarReg Demo User"
DEMO_USER_EMAIL = "lunarreg.demo@example.com"


def get_or_create_demo_user() -> Tuple[str, str, str]:
    """
    Ensure the dedicated demo evaluator account exists in the database.
    Returns (user_id, full_name, email).
    Never overwrites existing real accounts or user passwords.
    """
    email_norm = DEMO_USER_EMAIL.strip().lower()
    with _get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT id, full_name, email FROM users WHERE email = ?",
            (email_norm,),
        )
        row = cur.fetchone()
        if row is not None:
            return (str(row["id"]), row["full_name"], row["email"])

    # If demo user does not exist, provision using a random secure password
    demo_pass = secrets.token_urlsafe(24)
    create_user(DEMO_USER_NAME, email_norm, demo_pass)

    with _get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT id, full_name, email FROM users WHERE email = ?",
            (email_norm,),
        )
        row = cur.fetchone()
        if row is not None:
            return (str(row["id"]), row["full_name"], row["email"])
        else:
            return ("demo_1", DEMO_USER_NAME, email_norm)


def is_demo_session() -> bool:
    """Return True if the active authenticated session is a Quick Demo session."""
    return bool(
        is_authenticated()
        and st.session_state.get("auth_is_demo", False)
        and str(st.session_state.get("auth_email", "")).lower() == DEMO_USER_EMAIL.lower()
    )


def handle_quick_demo_access() -> None:
    """
    Callback for the Quick Demo Access button.
    Runs as a pre-rerun callback before the next script render cycle.
    1. Clear any stale authentication/session state.
    2. Provision or retrieve the dedicated demo user.
    3. Set authenticated state with demo identity.
    4. Set navigation target to 'overview'.
    Streamlit will automatically rerun the script following this callback.
    DO NOT call st.rerun() inside this callback!
    """
    # 1. Clear complete per-browser session to remove any stale results/imagery/metadata
    logout_user()

    # 2. Provision or retrieve dedicated demo user
    uid, name, eml = get_or_create_demo_user()

    # 3. Set authenticated session with demo identity
    set_authenticated(uid, name, eml)
    st.session_state["auth_is_demo"] = True

    # 4. Clean navigation state starting at Overview
    st.session_state["nav_page"] = "overview"
    st.session_state["sidebar_page"] = "Overview"
    st.session_state["pending_nav_target"] = "overview"


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def _auth_css() -> str:
    return """
    <style>
        /* Hide sidebar and Streamlit chrome on auth page */
        section[data-testid="stSidebar"],
        div[data-testid="collapsedControl"],
        div[data-testid="stSidebarCollapseButton"] {
            display: none !important;
        }
        .stApp > header[data-testid="stHeader"] {
            height: 0 !important;
            visibility: hidden !important;
        }
        /* Expand the page to fill the viewport for auth stage */
        .block-container {
            padding: 0 !important;
            max-width: 100% !important;
            margin: 0 !important;
            min-height: 100vh !important;
        }
        section.main { background: transparent !important; min-height: 100vh !important; }
        section.main > div { min-height: 100vh !important; }
        section.main > div > div[data-testid="stVerticalBlockBorderWrapper"] {
            min-height: 100vh !important;
        }

        /* Two-column stage layout — target columns produced by st.columns([1.1, 0.9]) */
        section.main [data-testid="stHorizontalBlock"] {
            width: 100% !important;
            max-width: 100% !important;
            margin: 0 !important;
            gap: 0 !important;
            min-height: 100vh !important;
        }
        section.main [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            min-height: 100vh !important;
            padding: 0 !important;
            overflow: hidden;
            display: flex !important;
            align-items: stretch !important;
        }
        section.main [data-testid="stHorizontalBlock"] > [data-testid="column"] > div {
            width: 100% !important;
            flex-grow: 1 !important;
        }

        /* Hero column (left) */
        .lunar-auth-hero {
            position: relative;
            width: 100%;
            min-height: 100vh;
            height: 100vh;
            overflow: hidden;
            display: block;
        }
        .lunar-auth-hero img {
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            object-position: center 48%;
            display: block;
            filter: contrast(1.02) saturate(0.95);
        }
        .lunar-auth-hero::after {
            content: "";
            position: absolute;
            inset: 0;
            display: block;
            background:
                linear-gradient(
                    90deg,
                    rgba(3,8,18,0.08) 0%,
                    rgba(3,8,18,0.18) 50%,
                    rgba(3,8,18,0.60) 85%
                ),
                linear-gradient(
                    180deg,
                    rgba(3,8,18,0.06) 0%,
                    rgba(3,8,18,0.0) 40%,
                    rgba(3,8,18,0.50) 100%
                );
            pointer-events: none;
        }
        .lunar-auth-hero-inner {
            position: absolute;
            inset: 0;
            padding: 64px 64px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            z-index: 2;
            pointer-events: none;
        }
        .hero-meta {
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
            font-weight: 600;
            font-size: 0.86rem;
            letter-spacing: 0.24em;
            color: rgba(201,209,217,0.9);
            text-transform: uppercase;
            line-height: 1.6;
        }
        .hero-quote {
            max-width: 520px;
            font-size: 2.05rem;
            line-height: 1.08;
            color: #ffffff;
            font-weight: 700;
            letter-spacing: 0.2px;
            text-shadow: 0 6px 28px rgba(2,6,23,0.45);
        }
        .hero-quote-rule {
            width: 64px;
            height: 3px;
            background: #58a6ff;
            margin: 20px 0 18px 0;
            border-radius: 4px;
            box-shadow: 0 6px 22px rgba(35,96,255,0.12);
        }
        .hero-footer {
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
            font-size: 0.78rem;
            letter-spacing: 0.24em;
            color: rgba(203,213,224,0.8);
            text-transform: uppercase;
        }
        .hero-footer span + span::before {
            content: "   |   ";
            color: rgba(30,38,46,0.6);
        }

        /* Auth column (right) */
        .lunar-auth-main {
            width: 100%;
            min-height: 100vh;
            height: 100vh;
            background:
                radial-gradient(
                    1200px 600px at 120% -20%,
                    rgba(88, 166, 255, 0.10),
                    transparent 60%
                ),
                radial-gradient(
                    800px 500px at -10% 110%,
                    rgba(0, 242, 255, 0.06),
                    transparent 55%
                ),
                linear-gradient(180deg,#05060a 0%, #07101a 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 48px 56px;
            box-sizing: border-box;
            overflow-y: auto;
        }
        .lunar-auth-card {
            width: 100%;
            max-width: 480px;
            background: rgba(10, 14, 20, 0.62);
            backdrop-filter: blur(12px) saturate(140%);
            -webkit-backdrop-filter: blur(12px) saturate(140%);
            border: 1px solid rgba(56, 76, 102, 0.26);
            border-radius: 14px;
            padding: 34px 34px 28px 34px;
            box-shadow:
                0 22px 68px rgba(2, 6, 23, 0.6),
                inset 0 1px 0 rgba(255, 255, 255, 0.02);
            box-sizing: border-box;
        }
        .auth-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 10px;
        }
        .auth-brand-mark {
            width: 44px;
            height: 44px;
            border-radius: 10px;
            display: grid;
            place-items: center;
            background: linear-gradient(145deg, #0d2847, #081425);
            border: 1px solid #1c3b64;
            color: #7dd3fc;
            font-size: 1.3rem;
            flex-shrink: 0;
        }
        .auth-brand-name {
            font-size: 1.88rem;
            font-weight: 800;
            letter-spacing: 0.2px;
            color: #ffffff;
            line-height: 1;
        }
        .auth-brand-name span {
            color: #58a6ff;
        }
        .auth-subtitle {
            font-family: Inter, sans-serif;
            font-size: 0.72rem;
            letter-spacing: 0.45em;
            color: rgba(203,213,224,0.85);
            text-transform: uppercase;
            margin: 0 0 10px 56px;
        }
        .auth-tagline {
            font-size: 0.95rem;
            color: rgba(201,209,217,0.95);
            margin: 0 0 8px 56px;
        }
        .auth-rule {
            width: 28px;
            height: 2px;
            background: #58a6ff;
            margin: 12px 0 22px 56px;
        }

        .auth-feature-chip {
            display: flex;
            align-items: center;
            gap: 10px;
            background: rgba(88, 166, 255, 0.06);
            border: 1px solid rgba(88, 166, 255, 0.14);
            border-radius: 10px;
            padding: 10px 12px;
            margin-bottom: 18px;
            color: #c9d1d9;
            font-size: 0.86rem;
            line-height: 1.45;
        }
        .auth-feature-chip .chip-ico { color: #7dd3fc; font-size: 1.1rem; flex-shrink: 0; }
        .auth-feature-chip strong { color: #e6edf3; font-weight: 600; }

        /* Streamlit widgets inside the card */
        [data-testid="stTabs"] { margin-bottom: 8px !important; }
        [data-baseweb="tab-list"] {
            gap: 6px !important;
            background: transparent !important;
            border-bottom: 1px solid #1f2a3a !important;
            padding-bottom: 0 !important;
            margin-bottom: 18px !important;
        }
        [data-baseweb="tab"] {
            color: rgba(139,148,158,0.95) !important;
            background: transparent !important;
            border: none !important;
            font-weight: 700 !important;
            padding: 8px 6px !important;
            font-size: 0.96rem !important;
        }
        [data-baseweb="tab"][aria-selected="true"] { color: #58a6ff !important; }
        [data-baseweb="tab-highlight"] { background: #58a6ff !important; height: 2px !important; }

        [data-testid="stTextInput"] label,
        [data-testid="stForm"] label,
        [data-testid="stMarkdownContainer"] p {
            color: #8b949e !important;
            font-size: 0.76rem !important;
        }
        [data-testid="stTextInput"] {
            margin-bottom: 2px !important;
        }
        [data-testid="stForm"] > div {
            gap: 10px !important;
        }
        [data-testid="stTextInput"] > div > div > input {
            background: rgba(6,10,14,0.65) !important;
            color: #e6edf3 !important;
            border: 1px solid rgba(40,56,78,0.6) !important;
            border-radius: 8px !important;
            padding: 8px 12px !important;
            font-size: 0.90rem !important;
            min-height: 38px !important;
        }
        [data-testid="stTextInput"] > div > div > input:focus {
            border-color: #58a6ff !important;
            box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.15) !important;
        }

        .auth-primary-btn button,
        .lunar-auth-card [data-testid="stFormSubmitButton"] button {
            background: linear-gradient(180deg, #18283f 0%, #111c2e 100%) !important;
            color: #c9d1d9 !important;
            border: 1px solid #283e5e !important;
            border-radius: 8px !important;
            padding: 8px 14px !important;
            font-weight: 600 !important;
            font-size: 0.88rem !important;
            letter-spacing: 0.2px !important;
            width: 100% !important;
            min-height: 38px !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25) !important;
            transition: all 0.2s ease !important;
        }
        .auth-primary-btn button:hover,
        .lunar-auth-card [data-testid="stFormSubmitButton"] button:hover {
            background: linear-gradient(180deg, #223756 0%, #18283f 100%) !important;
            border-color: #3b5a87 !important;
            color: #ffffff !important;
        }
        .auth-primary-btn button p,
        .lunar-auth-card [data-testid="stFormSubmitButton"] button p {
            color: inherit !important;
            font-size: inherit !important;
            font-weight: inherit !important;
            margin: 0 !important;
        }

        /* Quick Demo Access Action Button - Prominent Accent Treatment */
        .lunar-auth-card .stButton,
        .lunar-auth-card div[data-testid="stButton"] {
            width: 100% !important;
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }
        .lunar-auth-card .stButton > button,
        .lunar-auth-card div[data-testid="stButton"] > button {
            background: linear-gradient(180deg, #1b4273 0%, #122e52 100%) !important;
            color: #ffffff !important;
            border: 1.5px solid #388bfd !important;
            border-radius: 8px !important;
            padding: 11px 18px !important;
            min-height: 44px !important;
            font-weight: 700 !important;
            font-size: 0.94rem !important;
            letter-spacing: 0.35px !important;
            width: 100% !important;
            box-shadow:
                0 4px 16px rgba(10, 45, 90, 0.45),
                inset 0 1px 0 rgba(255, 255, 255, 0.18) !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
            cursor: pointer !important;
        }
        .lunar-auth-card .stButton > button:hover,
        .lunar-auth-card div[data-testid="stButton"] > button:hover {
            background: linear-gradient(180deg, #225694 0%, #173b68 100%) !important;
            border-color: #58a6ff !important;
            color: #ffffff !important;
            box-shadow:
                0 0 18px rgba(88, 166, 255, 0.40),
                0 6px 20px rgba(2, 10, 25, 0.55),
                inset 0 1px 0 rgba(255, 255, 255, 0.28) !important;
            transform: translateY(-1px);
        }
        .lunar-auth-card .stButton > button:active,
        .lunar-auth-card div[data-testid="stButton"] > button:active {
            transform: translateY(0px);
            background: #122e52 !important;
            box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.6) !important;
        }
        .lunar-auth-card .stButton > button p,
        .lunar-auth-card div[data-testid="stButton"] > button p {
            color: #ffffff !important;
            font-size: inherit !important;
            font-weight: inherit !important;
            letter-spacing: inherit !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        .auth-footnote {
            text-align: center;
            margin-top: 14px;
            color: #6e7681;
            font-size: 0.72rem;
        }
        .auth-footnote span + span::before {
            content: "   |   ";
            color: #30363d;
        }

        .auth-feature-row {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            margin-top: 20px;
            padding-top: 18px;
            border-top: 1px solid #1a2333;
        }
        .auth-feature-cell {
            text-align: center;
            padding: 8px 4px;
            border-radius: 8px;
        }
        .auth-feature-cell:hover { background: rgba(88, 166, 255, 0.05); }
        .afc-icon { color: #58a6ff; font-size: 1.25rem; margin-bottom: 4px; }
        .afc-title { color: #c9d1d9; font-size: 0.78rem; font-weight: 600; margin-bottom: 2px; }
        .afc-sub { color: #6e7681; font-size: 0.68rem; }

        @media (max-width: 980px) {
            section.main [data-testid="stHorizontalBlock"] {
                display: block !important;
            }
            section.main [data-testid="stHorizontalBlock"] > [data-testid="column"] {
                min-height: auto !important;
                width: 100% !important;
            }
            .lunar-auth-hero { display: none !important; }
            .lunar-auth-main { padding: 28px 20px; min-height: auto; }
        }
        /* Unified stage overrides. One bordered Streamlit container owns every
           header, native form and footer element in the authentication card. */
        header[data-testid="stHeader"] { display: none !important; }
        section.main { background: #05070c !important; }
        section.main, section.main > div { height: 100vh !important; overflow: hidden !important; }
        section.main [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2) {
            background:
                radial-gradient(1000px 540px at 110% -10%, rgba(88,166,255,.11), transparent 60%),
                radial-gradient(700px 460px at -10% 110%, rgba(0,242,255,.05), transparent 55%),
                linear-gradient(180deg, #05060a, #07101a) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            padding: clamp(10px, 2.5vh, 24px) clamp(20px, 4vw, 56px) !important;
            box-sizing: border-box !important;
            overflow-y: auto !important;
        }
        section.main [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2)
        [data-testid="stVerticalBlockBorderWrapper"] {
            width: 100% !important;
            max-width: 460px !important;
            margin: 0 auto !important;
            background: rgba(10,14,20,.68) !important;
            border: 1px solid rgba(56,76,102,.42) !important;
            border-radius: 14px !important;
            box-shadow: 0 22px 68px rgba(2,6,23,.6), inset 0 1px 0 rgba(255,255,255,.02) !important;
            backdrop-filter: blur(12px) saturate(140%);
            -webkit-backdrop-filter: blur(12px) saturate(140%);
        }
        section.main [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2)
        [data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: 20px 28px 16px !important;
        }
        .auth-unified-header { margin-bottom: 2px; }
        .auth-unified-header .auth-brand { margin-bottom: 4px; gap: 10px; }
        .auth-unified-header .auth-brand-mark { width: 34px; height: 34px; font-size: 1.05rem; }
        .auth-unified-header .auth-brand-name { font-size: 1.55rem; }
        .auth-unified-header .auth-subtitle { font-size: .65rem; letter-spacing: .28em; margin: 0 0 3px 44px; }
        .auth-unified-header .auth-tagline { font-size: .84rem; margin: 0 0 3px 44px; }
        .auth-unified-header .auth-rule { margin: 4px 0 8px 44px; height: 2px; }
        .auth-unified-footer { margin-top: 8px; padding-top: 8px; border-top: 1px solid #1a2333; }
        .auth-unified-feature { color: #b8c5d4; font-size: .74rem; line-height: 1.45; }
        .auth-unified-feature span { color: #7dd3fc; font-weight: 800; padding-right: 6px; }
        .auth-unified-footer .auth-footnote { margin-top: 5px; font-size: .68rem; }
        .hero-support { max-width: 340px; margin-top: 16px; color: rgba(226,232,240,.9); font-size: .92rem; line-height: 1.55; }
        @media (max-width: 980px) {
            section.main, section.main > div { height: auto !important; overflow: visible !important; }
            .lunar-auth-hero { display: block !important; min-height: 280px; height: 280px; }
            .lunar-auth-hero-inner { padding: 30px 32px; }
            .hero-quote { font-size: 1.6rem; }
            section.main [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2) {
                min-height: auto !important;
                padding: 28px 20px !important;
            }
        }
    </style>
    """


def _render_hero(hero_html_path: Optional[str]) -> str:
    """Return a fully self-closing hero column HTML block (no open tags)."""
    image_uri = _hero_image_data_uri(HERO_IMAGE_PATH if hero_html_path is None else hero_html_path)
    if image_uri:
        img_tag = (
            '<img src="' + image_uri + '" alt="Lunar surface with deep space and spacecraft" '
            'style="position:absolute; inset:0; width:100%; height:100%; object-fit:cover; display:block;" />'
        )
    else:
        img_tag = (
            '<div style="position:absolute; inset:0;'
            ' background:'
            ' radial-gradient(ellipse at 35% 50%, #c9c9c9 0%, #8a8a8a 18%, #555555 35%, #2a2a2a 55%, #0e0e12 80%),'
            ' #05070c;'
            ' filter: contrast(1.08) saturate(0.95);"></div>'
            '<div style="position:absolute; inset:0;'
            ' background-image:'
            ' radial-gradient(1px 1px at 10% 15%, #ffffff 50%, transparent 51%),'
            ' radial-gradient(1px 1px at 80% 20%, #c9e6ff 50%, transparent 51%),'
            ' radial-gradient(1px 1px at 25% 80%, #ffffff 50%, transparent 51%),'
            ' radial-gradient(1.4px 1.4px at 70% 75%, #d7eaff 50%, transparent 51%),'
            ' radial-gradient(1px 1px at 92% 55%, #ffffff 50%, transparent 51%),'
            ' radial-gradient(1.2px 1.2px at 5% 60%, #bfe2ff 50%, transparent 51%);'
            ' opacity: 0.85;"></div>'
        )

    html = (
        '<div class="lunar-auth-hero">'
        + img_tag
        + '<div class="lunar-auth-hero-inner">'
        + '<div class="hero-meta">EXPLORING TODAY<br />FOR A BRIGHTER<br />TOMORROW</div>'
        + '<div><div class="hero-quote">&ldquo;From the Moon,<br />for a Better Earth.&rdquo;</div>'
        + '<div class="hero-quote-rule"></div>'
        + '<div class="hero-support">Adaptive lunar image registration<br />for reliable scientific analysis.</div></div>'
        + '<div class="hero-footer"><span>CHANDRAYAAN-2</span><span>EXPLORE</span>'
        + '<span>ALIGN</span><span>DISCOVER</span></div>'
        + '</div></div>'
    )
    return html.strip()


def _render_card_header_and_feature_chip() -> str:
    """Fully self-closing HTML block for the branding section inside the card."""
    html = (
        '<div class="auth-brand">'
        + '<div class="auth-brand-mark">🌙</div>'
        + '<div class="auth-brand-name">Lunar<span>Reg</span></div>'
        + '</div>'
        + '<div class="auth-subtitle">Adaptive Lunar Image Registration System</div>'
        + '<div class="auth-tagline">Aligning Perspectives. Unlocking Discoveries.</div>'
        + '<div class="auth-rule"></div>'
        + '<div class="auth-feature-chip">'
        + '<span class="chip-ico">🌕</span>'
        + '<div><strong>Register lunar images with sub-pixel accuracy</strong>'
        + '<div style="color:#8b949e;">for scientific discovery.</div>'
        + '</div></div>'
    )
    return html.strip()


def _render_card_footer() -> str:
    """Fully self-closing HTML block for the feature row + footnote."""
    html = (
        '<div class="auth-feature-row">'
        + '<div class="auth-feature-cell"><div class="afc-icon">🖼️</div>'
        + '<div class="afc-title">Upload Images</div>'
        + '<div class="afc-sub">Source &amp; Reference</div></div>'
        + '<div class="auth-feature-cell"><div class="afc-icon">⚙️</div>'
        + '<div class="afc-title">Run Registration</div>'
        + '<div class="afc-sub">AI-Powered Matching</div></div>'
        + '<div class="auth-feature-cell"><div class="afc-icon">📊</div>'
        + '<div class="afc-title">View Results</div>'
        + '<div class="afc-sub">Metrics &amp; Visualization</div></div>'
        + '</div>'
        + '<div class="auth-footnote">'
        + '<span>Research Prototype</span>'
        + '<span>Student-Built</span>'
        + '<span>SIH 2026</span>'
        + '</div>'
    )
    return html.strip()


def _render_unified_card_header() -> str:
    """Return a self-contained, compact brand block for the native card."""
    return (
        '<div class="auth-unified-header">'
        '<div class="auth-brand">'
        '<div class="auth-brand-mark">&#127769;</div>'
        '<div class="auth-brand-name">Lunar<span>Reg</span></div>'
        '</div>'
        '<div class="auth-subtitle">Adaptive Lunar Image Registration System</div>'
        '<div class="auth-tagline">Aligning Perspectives. Unlocking Discoveries.</div>'
        '<div class="auth-rule"></div>'
        '</div>'
    )


def _render_unified_card_footer() -> str:
    """Return the required research highlights and prototype provenance."""
    return (
        '<div class="auth-unified-footer">'
        '<div class="auth-unified-feature"><span>&#10003;</span>Sub-pixel registration</div>'
        '<div class="auth-unified-feature"><span>&#10003;</span>Spatially reliable correspondences</div>'
        '<div class="auth-unified-feature"><span>&#10003;</span>Independent validation</div>'
        '<div class="auth-footnote"><span>Research Prototype</span>'
        '<span>Student-Built</span><span>SIH 2026</span></div>'
        '</div>'
    )


def render_auth_page() -> None:
    """
    Render the full-screen Login / Sign Up auth page.

    **********************************************************************
    ** NO-RAW-HTML-LEAK RULE (ABSOLUTE):                                **
    ** Every st.markdown() call that contains HTML MUST be a FULLY     **
    ** BALANCED, SELF-CLOSING block.                                   **
    ** We never open a HTML tag in st.markdown(A) and close it in a    **
    ** later st.markdown(B) call — Streamlit renders native widgets   **
    ** inside their own isolated React roots, so any dangling open/    **
    ** close tags across two markdown calls get escaped & rendered as  **
    ** literal text on the page.                                       **
    **********************************************************************

    Layout strategy:
      st.columns([1.1, 0.9])    — hero : auth
        ├ col_hero  → single self-closing hero HTML block
        └ col_auth  → three stacked self-closing .lunar-auth-card blocks
                         (1) header card (branding + feature chip)
                         (2) middle card (holds ALL native widgets)
                         (3) footer card (feature row + footnote)
                      Each block is balanced/self-closing.
    """
    # A single native container keeps Streamlit's widgets and static HTML in
    # one visual card; no HTML tag is opened around widgets.
    st.markdown(_auth_css().strip(), unsafe_allow_html=True)
    col_hero, col_auth = st.columns([1, 1], gap="small")

    with col_hero:
        st.markdown(_render_hero(HERO_IMAGE_PATH), unsafe_allow_html=True)

    with col_auth:
        with st.container(border=True):
            st.markdown(_render_unified_card_header(), unsafe_allow_html=True)

            tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

            with tab_login:
                with st.form("lunarreg_login_form", clear_on_submit=False):
                    email_login = st.text_input(
                        "Email",
                        key="auth_login_email",
                        placeholder="you@research.edu",
                    )
                    pass_login = st.text_input(
                        "Password",
                        type="password",
                        key="auth_login_password",
                        placeholder="Enter your password",
                    )
                    submitted_login = st.form_submit_button("Sign In  \u2192")

                if submitted_login:
                    result = authenticate_user(email_login, pass_login)
                    if result is None:
                        st.error("Invalid email or password. Please try again.")
                    else:
                        uid, name, eml = result
                        set_authenticated(uid, name, eml)
                        st.success(f"Welcome back, {name.split()[0]}! Redirecting…")
                        st.rerun()

                # --- QUICK DEMO ACCESS FOR SIH / EVALUATORS ---
                st.markdown(
                    '<div style="display: flex; align-items: center; margin: 10px 0 8px 0;">'
                    '<div style="flex-grow: 1; height: 1px; background: #212c3d;"></div>'
                    '<span style="padding: 0 10px; color: #8b949e; font-size: 0.68rem; font-weight: 600; letter-spacing: 1.5px;">OR</span>'
                    '<div style="flex-grow: 1; height: 1px; background: #212c3d;"></div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

                st.button(
                    "Quick Demo Access",
                    key="btn_quick_demo_access",
                    type="secondary",
                    width="stretch",
                    on_click=handle_quick_demo_access,
                )

                st.markdown(
                    '<p style="text-align: center; color: #8b949e; font-size: 0.72rem; margin: 3px 0 8px 0; letter-spacing: 0.2px;">'
                    'For evaluation / demonstration</p>',
                    unsafe_allow_html=True,
                )

                st.markdown(
                    '<p style="text-align: center; color: #6e7681; font-size: 0.74rem; margin: 2px 0 0 0;">'
                    'Don&apos;t have an account? Switch to the <strong>Sign Up</strong> tab.</p>',
                    unsafe_allow_html=True,
                )

            with tab_signup:
                with st.form("lunarreg_signup_form", clear_on_submit=False):
                    full_name = st.text_input(
                        "Full Name",
                        key="auth_signup_name",
                        placeholder="e.g. Priya Sharma",
                    )
                    email_signup = st.text_input(
                        "Email",
                        key="auth_signup_email",
                        placeholder="you@research.edu",
                    )
                    pass_signup = st.text_input(
                        "Password",
                        type="password",
                        key="auth_signup_password",
                        placeholder="At least 6 characters",
                    )
                    pass_confirm = st.text_input(
                        "Confirm Password",
                        type="password",
                        key="auth_signup_confirm",
                        placeholder="Re-enter your password",
                    )
                    submitted_signup = st.form_submit_button("Create Account  \u2192")

                if submitted_signup:
                    if not full_name.strip():
                        st.warning("Please enter your full name.")
                    elif "@" not in email_signup:
                        st.warning("Please enter a valid email address.")
                    elif len(pass_signup) < 6:
                        st.warning("Password must be at least 6 characters long.")
                    elif pass_signup != pass_confirm:
                        st.error("Passwords do not match. Please re-enter.")
                    else:
                        ok, msg = create_user(full_name, email_signup, pass_signup)
                        if ok:
                            st.success(msg)
                            st.info("Switch to the **Login** tab above to sign in.")
                        else:
                            st.error(msg)

                st.markdown(
                    '<p style="text-align:center; color:#8b949e; font-size:.78rem; margin:6px 0 0;">'
                    'Already have an account? Switch to the <strong>Login</strong> tab.</p>',
                    unsafe_allow_html=True,
                )

            st.markdown(_render_unified_card_footer(), unsafe_allow_html=True)
