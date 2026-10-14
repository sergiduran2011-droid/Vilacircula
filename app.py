from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import secrets
import sqlite3
import uuid
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import id_token as google_id_token
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

from config import AppConfig
from db import connect_database, is_postgres_url
from services import AnalyticsService

ROOT = Path(__file__).resolve().parent
DEFAULT_DATABASE = ROOT / "data" / "vilacircula.sqlite3"
SCHOOLS = ("Goar", "Torre-roja", "Josep Mestres", "Miramar", "Olímpia", "Sales")

MERCHANTS = (
    {
        "id": "osm-12752947043",
        "name": "Café Marco",
        "category": "Cafeterías",
        "type": "Cafetería · comercio local",
        "initials": "CM",
        "latitude": 41.3173588,
        "longitude": 2.0257551,
        "address": "Carrer de Guifré el Pelós, Barri de Sales, Viladecans",
        "source": "OpenStreetMap",
        "source_url": "https://www.openstreetmap.org/node/12752947043",
        "is_demo": False,
        "offer": "Ficha y ubicación proceden de OpenStreetMap; confirma las condiciones con el local.",
        "reward": "Sin recompensas verificadas todavía.",
    },
    {
        "id": "osm-11432296231",
        "name": "a.m bakery & coffee",
        "category": "Alimentación",
        "type": "Panadería y café · comercio local",
        "initials": "AM",
        "latitude": 41.3122261,
        "longitude": 2.0023559,
        "address": "Carrer de Can Trias, Can Guardiola, Viladecans",
        "source": "OpenStreetMap",
        "source_url": "https://www.openstreetmap.org/node/11432296231",
        "is_demo": False,
        "offer": "Ficha y ubicación proceden de OpenStreetMap; confirma las condiciones con el local.",
        "reward": "Sin recompensas verificadas todavía.",
    },
    {
        "id": "demo-papeleria",
        "name": "Papelería de ejemplo",
        "category": "Papelería",
        "type": "Papelería · ficha ilustrativa",
        "initials": "PE",
        "latitude": None,
        "longitude": None,
        "address": None,
        "source": "VilaCircula · ejemplo",
        "source_url": None,
        "is_demo": True,
        "offer": "Ficha ilustrativa; no representa un comercio adherido confirmado.",
        "reward": "Los descuentos de esta ficha son de demostración.",
    },
    {
        "id": "demo-moda",
        "name": "Moda Circular · ejemplo",
        "category": "Moda",
        "type": "Moda · ficha ilustrativa",
        "initials": "ME",
        "latitude": None,
        "longitude": None,
        "address": None,
        "source": "VilaCircula · ejemplo",
        "source_url": None,
        "is_demo": True,
        "offer": "Ficha ilustrativa; no representa un comercio adherido confirmado.",
        "reward": "Los descuentos de esta ficha son de demostración.",
    },
)

REWARDS = (
    {"id": "bread", "name": "2 € en pan artesano", "store": "a.m bakery & coffee", "merchant_id": "osm-11432296231", "cost": 50, "art": "bread", "icon": "croissant", "description": "Descuento ilustrativo; consulta condiciones en el local.", "is_demo": True},
    {"id": "coffee", "name": "Un café de la casa", "store": "Café Marco", "merchant_id": "osm-12752947043", "cost": 45, "art": "coffee", "icon": "coffee", "description": "Premio ilustrativo; consulta condiciones en el local.", "is_demo": True},
    {"id": "book", "name": "2 € en material escolar", "store": "Papelería de ejemplo", "merchant_id": "demo-papeleria", "cost": 50, "art": "book", "icon": "notebook-pen", "description": "Recompensa y comercio de demostración.", "is_demo": True},
    {"id": "market", "name": "Cesta de temporada", "store": "Comercio de alimentación · ejemplo", "merchant_id": "demo-papeleria", "cost": 80, "art": "market", "icon": "carrot", "description": "Recompensa de demostración.", "is_demo": True},
    {"id": "shirt", "name": "10% en moda circular", "store": "Moda Circular · ejemplo", "merchant_id": "demo-moda", "cost": 60, "art": "shirt", "icon": "shirt", "description": "Recompensa y comercio de demostración.", "is_demo": True},
    {"id": "plant", "name": "Planta aromática", "store": "Comercio de alimentación · ejemplo", "merchant_id": "demo-papeleria", "cost": 40, "art": "plant", "icon": "sprout", "description": "Recompensa de demostración.", "is_demo": True},
)

CASHIER_SEEDS = (
    ("caja.cafe-marco", "osm-12752947043"),
    ("caja.am-bakery", "osm-11432296231"),
    ("caja.papeleria-demo", "demo-papeleria"),
    ("caja.moda-demo", "demo-moda"),
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles (
    id TEXT PRIMARY KEY,
    google_sub TEXT,
    display_name TEXT NOT NULL,
    school TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    balance INTEGER NOT NULL DEFAULT 150 CHECK (balance >= 0),
    contribution INTEGER NOT NULL DEFAULT 0 CHECK (contribution >= 0),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS merchants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    type TEXT NOT NULL,
    initials TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    address TEXT,
    source TEXT NOT NULL,
    source_url TEXT,
    is_demo INTEGER NOT NULL DEFAULT 1,
    offer TEXT NOT NULL,
    reward TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cashier_users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    merchant_id TEXT NOT NULL REFERENCES merchants(id),
    must_change_password INTEGER NOT NULL DEFAULT 1,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS auth_sessions (
    token_hash TEXT PRIMARY KEY,
    subject_type TEXT NOT NULL CHECK (subject_type IN ('citizen', 'cashier')),
    profile_id TEXT REFERENCES profiles(id),
    cashier_id TEXT REFERENCES cashier_users(id),
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS auth_sessions_profile_idx ON auth_sessions(profile_id, expires_at);
CREATE TABLE IF NOT EXISTS login_attempts (
    username TEXT NOT NULL,
    client_ip TEXT NOT NULL,
    failed_count INTEGER NOT NULL DEFAULT 0,
    window_started_at TEXT NOT NULL,
    locked_until TEXT,
    PRIMARY KEY (username, client_ip)
);
CREATE TABLE IF NOT EXISTS coupons (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    profile_id TEXT NOT NULL REFERENCES profiles(id),
    merchant_id TEXT REFERENCES merchants(id),
    reward_id TEXT NOT NULL,
    name TEXT NOT NULL,
    store TEXT NOT NULL,
    cost INTEGER NOT NULL CHECK (cost > 0),
    status TEXT NOT NULL CHECK (status IN ('active', 'redeemed')),
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    redeemed_at TEXT,
    redeemed_by TEXT REFERENCES cashier_users(id)
);
CREATE INDEX IF NOT EXISTS coupons_profile_status_idx ON coupons(profile_id, status);
CREATE TABLE IF NOT EXISTS coupon_validations (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL,
    coupon_id TEXT NOT NULL,
    profile_id TEXT NOT NULL REFERENCES profiles(id),
    merchant_id TEXT REFERENCES merchants(id),
    cashier_id TEXT REFERENCES cashier_users(id),
    validated_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('success', 'failed')),
    reason TEXT,
    details TEXT
);
CREATE INDEX IF NOT EXISTS coupon_validations_cashier_idx ON coupon_validations(cashier_id, validated_at DESC);
CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    actor_type TEXT,
    actor_id TEXT,
    target_type TEXT,
    target_id TEXT,
    message TEXT,
    metadata TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS audit_logs_created_idx ON audit_logs(created_at DESC);
CREATE TABLE IF NOT EXISTS point_events (
    id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL REFERENCES profiles(id),
    description TEXT NOT NULL,
    merchant TEXT NOT NULL,
    points INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS point_events_profile_created_idx ON point_events(profile_id, created_at DESC);
CREATE TABLE IF NOT EXISTS eco_id_tokens (
    code TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL REFERENCES profiles(id),
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    scanned_at TEXT,
    cashier_id TEXT REFERENCES cashier_users(id)
);
CREATE INDEX IF NOT EXISTS eco_id_tokens_profile_created_idx ON eco_id_tokens(profile_id, created_at DESC);
"""


class ProfileUpdate(BaseModel):
    display_name: str = Field(min_length=1, max_length=32)
    school: str = Field(min_length=1, max_length=40)


class LoginPayload(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class GoogleAuthPayload(BaseModel):
    credential: str = Field(min_length=1, max_length=8192)
    username: str | None = Field(default=None, min_length=3, max_length=24, pattern=r"^[A-Za-z0-9._-]+$")
    password: str | None = Field(default=None, min_length=1, max_length=128)
    display_name: str | None = Field(default=None, min_length=1, max_length=32)
    school: str | None = Field(default=None, min_length=1, max_length=40)


class CredentialsUpdate(BaseModel):
    username: str = Field(min_length=3, max_length=24, pattern=r"^[A-Za-z0-9._-]+$")
    password: str = Field(min_length=10, max_length=128)
    current_password: str | None = Field(default=None, max_length=128)


class PasswordUpdate(BaseModel):
    password: str = Field(min_length=10, max_length=128)
    current_password: str | None = Field(default=None, max_length=128)


class CashierProvision(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9._-]+$")
    merchant_id: str = Field(min_length=1, max_length=64)


class RewardRedeem(BaseModel):
    reward_id: str = Field(min_length=1, max_length=40)


class CouponScan(BaseModel):
    code: str = Field(min_length=8, max_length=40, pattern=r"^VC-[A-Z0-9]+$")


class EcoIdScan(BaseModel):
    code: str = Field(min_length=37, max_length=37, pattern=r"^VCID-[A-F0-9]{32}$")


PASSWORD_SCRYPT_N = 2**14
logger = logging.getLogger("vilacircula")


def log_event(event: str, **context: object) -> None:
    payload = {"timestamp": datetime.now(UTC).isoformat(), "event": event, **context}
    logger.info(json.dumps(payload, ensure_ascii=False, default=str))


def normalize_username(username: str) -> str:
    return username.strip().lower()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=PASSWORD_SCRYPT_N, r=8, p=1)
    return f"scrypt${PASSWORD_SCRYPT_N}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, n_value, salt_hex, digest_hex = encoded_hash.split("$", maxsplit=3)
        if algorithm != "scrypt":
            return False
        candidate = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n_value),
            r=8,
            p=1,
        )
        return secrets.compare_digest(candidate.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_google_id_token(credential: str, client_id: str) -> dict[str, object]:
    claims = google_id_token.verify_oauth2_token(credential, GoogleAuthRequest(), client_id)
    return claims


def timestamp() -> str:
    return datetime.now(UTC).isoformat()


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_allowed_origins(value: str | None, fallback: list[str]) -> list[str]:
    if value is None or not value.strip():
        return fallback
    origins = [origin.strip() for origin in value.split(",") if origin.strip()]
    return origins if origins else fallback


def public_profile(profile: sqlite3.Row) -> dict[str, object]:
    return {
        "id": profile["id"],
        "display_name": profile["display_name"],
        "school": profile["school"],
        "username": profile["username"],
        "balance": profile["balance"],
        "contribution": profile["contribution"],
        "password_setup_required": profile["password_hash"] is None and profile["google_sub"] is None,
        "has_password": profile["password_hash"] is not None,
        "is_demo": True,
    }


def public_coupon(row: sqlite3.Row) -> dict[str, object]:
    return {
        "code": row["code"],
        "name": row["name"],
        "store": row["store"],
        "cost": row["cost"],
        "merchant_id": row["merchant_id"],
        "expiry": datetime.fromisoformat(row["expires_at"]).strftime("%-d %b"),
        "status": row["status"],
        "redeemed_at": row["redeemed_at"],
    }


def create_app(
    database_path: str | Path | None = None,
    merchant_key: str | None = None,
    allow_self_redeem: bool | None = None,
    admin_key: str | None = None,
    google_client_id: str | None = None,
) -> FastAPI:
    config = AppConfig.from_env(
        database_path=database_path,
        merchant_key=merchant_key,
        allow_self_redeem=allow_self_redeem,
        admin_key=admin_key,
        google_client_id=google_client_id,
    )
    db_path = config.database_path
    key = config.merchant_key
    admin_secret_key = config.admin_secret_key
    production = config.production
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO, format="%(message)s")
    allowed_origins = config.allowed_origins
    self_redeem_enabled = config.self_redeem_enabled

    def connect():
        return connect_database(config.database_url, db_path)

    if not is_postgres_url(config.database_url):
        db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect()) as connection:
        connection.executescript(SCHEMA)
        if is_postgres_url(config.database_url):
            connection.execute("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS google_sub TEXT")
            connection.execute("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS username TEXT")
            connection.execute("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS password_hash TEXT")
            connection.execute("ALTER TABLE coupons ADD COLUMN IF NOT EXISTS merchant_id TEXT REFERENCES merchants(id)")
            connection.execute("ALTER TABLE coupons ADD COLUMN IF NOT EXISTS redeemed_by TEXT REFERENCES cashier_users(id)")
        else:
            profile_columns = {row["name"] for row in connection.execute("PRAGMA table_info(profiles)")}
            coupon_columns = {row["name"] for row in connection.execute("PRAGMA table_info(coupons)")}
        if not is_postgres_url(config.database_url) and "google_sub" not in profile_columns:
            connection.execute("ALTER TABLE profiles ADD COLUMN google_sub TEXT")
        if not is_postgres_url(config.database_url) and "username" not in profile_columns:
            connection.execute("ALTER TABLE profiles ADD COLUMN username TEXT")
        if not is_postgres_url(config.database_url) and "password_hash" not in profile_columns:
            connection.execute("ALTER TABLE profiles ADD COLUMN password_hash TEXT")
        if not is_postgres_url(config.database_url) and "merchant_id" not in coupon_columns:
            connection.execute("ALTER TABLE coupons ADD COLUMN merchant_id TEXT REFERENCES merchants(id)")
        if not is_postgres_url(config.database_url) and "redeemed_by" not in coupon_columns:
            connection.execute("ALTER TABLE coupons ADD COLUMN redeemed_by TEXT REFERENCES cashier_users(id)")
        connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS profiles_username_idx ON profiles(username) WHERE username IS NOT NULL")
        connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS profiles_google_sub_idx ON profiles(google_sub) WHERE google_sub IS NOT NULL")
        legacy_profiles = connection.execute("SELECT id, display_name, token_hash, username, password_hash FROM profiles").fetchall()
        for legacy in legacy_profiles:
            if not legacy["username"]:
                base_username = re.sub(r"[^a-z0-9._-]+", "", normalize_username(legacy["display_name"]))[:14] or "ciudadano"
                username = base_username
                while connection.execute("SELECT 1 FROM profiles WHERE username = ?", (username,)).fetchone():
                    username = f"{base_username[:10]}-{secrets.token_hex(2)}"
                connection.execute("UPDATE profiles SET username = ? WHERE id = ?", (username, legacy["id"]))
            if legacy["password_hash"] is None:
                connection.execute(
                    "INSERT INTO auth_sessions (token_hash, subject_type, profile_id, created_at, expires_at) VALUES (?, 'citizen', ?, ?, ?) ON CONFLICT(token_hash) DO NOTHING",
                    (legacy["token_hash"], legacy["id"], timestamp(), (datetime.now(UTC) + timedelta(days=30)).isoformat()),
                )
        for merchant in MERCHANTS:
            connection.execute(
                "INSERT INTO merchants (id, name, category, type, initials, latitude, longitude, address, source, source_url, is_demo, offer, reward) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET name=excluded.name, category=excluded.category, type=excluded.type, initials=excluded.initials, latitude=excluded.latitude, longitude=excluded.longitude, address=excluded.address, source=excluded.source, source_url=excluded.source_url, is_demo=excluded.is_demo, offer=excluded.offer, reward=excluded.reward",
                (merchant["id"], merchant["name"], merchant["category"], merchant["type"], merchant["initials"], merchant["latitude"], merchant["longitude"], merchant["address"], merchant["source"], merchant["source_url"], int(merchant["is_demo"]), merchant["offer"], merchant["reward"]),
            )
        for reward in REWARDS:
            connection.execute(
                "UPDATE coupons SET merchant_id = ? WHERE reward_id = ? AND merchant_id IS NULL",
                (reward["merchant_id"], reward["id"]),
            )
        initial_cashier_password = os.getenv("VILACIRCULA_INITIAL_CASHIER_PASSWORD", "" if production else "Viladecans")
        if initial_cashier_password:
            for username, merchant_id in CASHIER_SEEDS:
                connection.execute(
                    "INSERT INTO cashier_users (id, username, password_hash, merchant_id, must_change_password, active, created_at) VALUES (?, ?, ?, ?, 1, 1, ?) ON CONFLICT(username) DO NOTHING",
                    (str(uuid.uuid4()), username, hash_password(initial_cashier_password), merchant_id, timestamp()),
                )

    app = FastAPI(title="VilaCircula API", version="1.0.0", description="API de demostración para perfiles, saldo y cupones de VilaCircula.")
    app.state.database_path = db_path
    app.state.database_backend = "postgresql" if is_postgres_url(config.database_url) else "sqlite"
    app.state.config = config
    app.state.google_client_id = config.google_client_id
    app.state.google_token_verifier = verify_google_id_token
    app.state.demo = not production
    app.state.production = production
    app.state.self_redeem_enabled = self_redeem_enabled
    app.state.allowed_origins = allowed_origins
    app.state.rate_limit_buckets = {}
    analytics_service = AnalyticsService(connect, production=production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Admin-Key", "X-Requested-With"],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "0"
        if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    bearer = HTTPBearer(auto_error=False)
    dummy_password_hash = hash_password(secrets.token_urlsafe(24))

    def add_audit_event(event_type: str, *, actor_type: str | None = None, actor_id: str | None = None, target_type: str | None = None, target_id: str | None = None, message: str | None = None, metadata: dict[str, object] | None = None) -> None:
        with closing(connect()) as connection:
            connection.execute(
                "INSERT INTO audit_logs (id, event_type, actor_type, actor_id, target_type, target_id, message, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    str(uuid.uuid4()),
                    event_type,
                    actor_type,
                    actor_id,
                    target_type,
                    target_id,
                    message,
                    json.dumps(metadata or {}, ensure_ascii=False),
                    timestamp(),
                ),
            )

    def is_rate_limited(key: str, limit: int = 10, window_seconds: int = 60) -> bool:
        now = datetime.now(UTC).timestamp()
        bucket = app.state.rate_limit_buckets.setdefault(key, [])
        app.state.rate_limit_buckets[key] = [ts for ts in bucket if now - ts < window_seconds]
        if len(app.state.rate_limit_buckets[key]) >= limit:
            return True
        app.state.rate_limit_buckets[key].append(now)
        return False

    def record_validation_event(coupon_id: str, code: str, profile_id: str, merchant_id: str | None, cashier_id: str | None, status: str, reason: str | None = None, details: dict[str, object] | None = None) -> None:
        with closing(connect()) as connection:
            connection.execute(
                "INSERT INTO coupon_validations (id, code, coupon_id, profile_id, merchant_id, cashier_id, validated_at, status, reason, details) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), code, coupon_id, profile_id, merchant_id, cashier_id, timestamp(), status, reason, json.dumps(details or {}, ensure_ascii=False)),
            )

    def issue_session(subject_type: str, subject_id: str, connection: sqlite3.Connection) -> str:
        token = secrets.token_urlsafe(32)
        now = datetime.now(UTC)
        profile_id = subject_id if subject_type == "citizen" else None
        cashier_id = subject_id if subject_type == "cashier" else None
        connection.execute(
            "INSERT INTO auth_sessions (token_hash, subject_type, profile_id, cashier_id, created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?)",
            (token_digest(token), subject_type, profile_id, cashier_id, now.isoformat(), (now + timedelta(days=30)).isoformat()),
        )
        return token

    def record_login_failure(username: str, client_ip: str) -> None:
        now = datetime.now(UTC)
        with closing(connect()) as connection:
            attempt = connection.execute(
                "SELECT failed_count, window_started_at FROM login_attempts WHERE username = ? AND client_ip = ?",
                (username, client_ip),
            ).fetchone()
            if attempt is None or datetime.fromisoformat(attempt["window_started_at"]) < now - timedelta(minutes=15):
                connection.execute(
                    "INSERT INTO login_attempts (username, client_ip, failed_count, window_started_at, locked_until) VALUES (?, ?, 1, ?, NULL) ON CONFLICT(username, client_ip) DO UPDATE SET failed_count = 1, window_started_at = excluded.window_started_at, locked_until = NULL",
                    (username, client_ip, now.isoformat()),
                )
                return
            failed_count = attempt["failed_count"] + 1
            locked_until = (now + timedelta(minutes=15)).isoformat() if failed_count >= 8 else None
            connection.execute(
                "UPDATE login_attempts SET failed_count = ?, locked_until = ? WHERE username = ? AND client_ip = ?",
                (failed_count, locked_until, username, client_ip),
            )

    def login_is_locked(username: str, client_ip: str) -> bool:
        with closing(connect()) as connection:
            attempt = connection.execute(
                "SELECT locked_until FROM login_attempts WHERE username = ? AND client_ip = ?",
                (username, client_ip),
            ).fetchone()
        return bool(attempt and attempt["locked_until"] and datetime.fromisoformat(attempt["locked_until"]) > datetime.now(UTC))

    def rate_limit_key_for_ip(request: Request) -> str:
        return request.client.host if request.client else "unknown"

    def clear_login_failures(username: str, client_ip: str) -> None:
        with closing(connect()) as connection:
            connection.execute("DELETE FROM login_attempts WHERE username = ? AND client_ip = ?", (username, client_ip))

    def profile_for_google_link(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    ) -> sqlite3.Row:
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inicia sesión para continuar.")
        with closing(connect()) as connection:
            profile = connection.execute(
                "SELECT profiles.*, auth_sessions.expires_at AS session_expires_at FROM auth_sessions JOIN profiles ON profiles.id = auth_sessions.profile_id WHERE auth_sessions.token_hash = ? AND auth_sessions.subject_type = 'citizen'",
                (token_digest(credentials.credentials),),
            ).fetchone()
        if profile is None:
            log_event("auth_error", event_type="missing_profile_session", token_hash=token_digest(credentials.credentials)[:12])
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="La sesión del dispositivo no es válida.")
        if datetime.fromisoformat(profile["session_expires_at"]) <= datetime.now(UTC):
            log_event("auth_error", event_type="expired_session", profile_id=profile["id"], expires_at=profile["session_expires_at"])
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="La sesión ha caducado. Inicia sesión otra vez.")
        return profile

    def current_profile(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    ) -> sqlite3.Row:
        profile = profile_for_google_link(credentials)
        if profile["google_sub"] is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vincula una cuenta de Google para continuar.")
        return profile

    def current_cashier(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    ) -> sqlite3.Row:
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inicia sesión en la caja del comercio.")
        with closing(connect()) as connection:
            cashier = connection.execute(
                "SELECT cashier_users.*, merchants.name AS merchant_name, merchants.is_demo AS merchant_is_demo, auth_sessions.expires_at AS session_expires_at FROM auth_sessions JOIN cashier_users ON cashier_users.id = auth_sessions.cashier_id JOIN merchants ON merchants.id = cashier_users.merchant_id WHERE auth_sessions.token_hash = ? AND auth_sessions.subject_type = 'cashier' AND cashier_users.active = 1",
                (token_digest(credentials.credentials),),
            ).fetchone()
        if cashier is None or datetime.fromisoformat(cashier["session_expires_at"]) <= datetime.now(UTC):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="La sesión de caja ha caducado. Inicia sesión otra vez.")
        return cashier

    def coupon_by_code(code: str, merchant_id: str | None = None, cashier_id: str | None = None) -> dict[str, object]:
        with closing(connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            coupon = connection.execute("SELECT * FROM coupons WHERE code = ?", (code,)).fetchone()
            if coupon is None:
                connection.rollback()
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cupón no encontrado.")
            if coupon["status"] != "active":
                connection.rollback()
                record_validation_event(coupon["id"], code, coupon["profile_id"], coupon["merchant_id"], cashier_id, "failed", "already_redeemed", {"code": code})
                log_event("coupon_error", event_type="already_redeemed", code=code, merchant_id=merchant_id, cashier_id=cashier_id)
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este cupón ya fue canjeado.")
            if datetime.fromisoformat(coupon["expires_at"]) <= datetime.now(UTC):
                connection.rollback()
                record_validation_event(coupon["id"], code, coupon["profile_id"], coupon["merchant_id"], cashier_id, "failed", "expired", {"code": code})
                log_event("coupon_error", event_type="expired_coupon", code=code, merchant_id=merchant_id)
                raise HTTPException(status_code=status.HTTP_410_GONE, detail="Este cupón ha caducado.")
            if merchant_id is not None and coupon["merchant_id"] != merchant_id:
                connection.rollback()
                record_validation_event(coupon["id"], code, coupon["profile_id"], coupon["merchant_id"], cashier_id, "failed", "merchant_mismatch", {"expected_merchant_id": merchant_id, "actual_merchant_id": coupon["merchant_id"]})
                log_event("coupon_error", event_type="merchant_mismatch", code=code, expected_merchant_id=merchant_id, actual_merchant_id=coupon["merchant_id"], cashier_id=cashier_id)
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Este cupón pertenece a otro comercio.")
            redeemed_at = timestamp()
            cursor = connection.execute(
                "UPDATE coupons SET status = 'redeemed', redeemed_at = ?, redeemed_by = ? WHERE id = ? AND status = 'active' AND expires_at > ?",
                (redeemed_at, cashier_id, coupon["id"], redeemed_at),
            )
            if cursor.rowcount != 1:
                connection.rollback()
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este cupón ya fue canjeado.")
            connection.commit()
            redeemed = dict(coupon)
            redeemed["status"] = "redeemed"
            redeemed["redeemed_at"] = redeemed_at
            redeemed["redeemed_by"] = cashier_id
            record_validation_event(coupon["id"], code, coupon["profile_id"], coupon["merchant_id"], cashier_id, "success", None, {"merchant_id": merchant_id, "status": "redeemed"})
            add_audit_event("coupon_redeemed", actor_type="cashier", actor_id=cashier_id, target_type="coupon", target_id=coupon["id"], message="Cupón validado", metadata={"code": code, "merchant_id": merchant_id, "profile_id": coupon["profile_id"]})
            return redeemed

    @app.get("/api/v1/health")
    def health() -> dict[str, object]:
        return {
            "status": "ok",
            "mode": "production" if production else "demo",
            "persistent_database": app.state.database_backend,
            "production": production,
            "self_redeem_enabled": self_redeem_enabled,
            "allowed_origins": allowed_origins,
        }

    def verified_google_claims(credential: str, request: Request) -> tuple[str, str, str]:
        if not config.google_client_id:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="El inicio de sesión con Google todavía no está configurado.")
        try:
            claims = app.state.google_token_verifier(credential, config.google_client_id)
        except (GoogleAuthError, ValueError) as error:
            log_event("auth_error", event_type="invalid_google_credential", client_ip=request.client.host if request.client else "unknown")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No se pudo verificar tu cuenta de Google.") from error
        google_sub = claims.get("sub")
        email = claims.get("email")
        email_verified = claims.get("email_verified")
        google_name = claims.get("name")
        if not isinstance(google_sub, str) or not google_sub or not isinstance(email, str) or email_verified not in (True, "true"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google no confirmó una cuenta de correo válida.")
        return google_sub, email, google_name if isinstance(google_name, str) else ""

    @app.get("/api/v1/auth/google/link-status")
    def google_link_status(profile: sqlite3.Row = Depends(profile_for_google_link)) -> dict[str, object]:
        return {
            "link_required": profile["google_sub"] is None,
            "display_name": profile["display_name"],
            "school": profile["school"],
        }

    @app.post("/api/v1/auth/google/link")
    def link_google_to_current_profile(
        payload: GoogleAuthPayload,
        request: Request,
        profile: sqlite3.Row = Depends(profile_for_google_link),
    ) -> dict[str, object]:
        if is_rate_limited(rate_limit_key_for_ip(request), limit=12, window_seconds=60):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Demasiados intentos. Espera un momento antes de probar otra vez.")
        google_sub, email, _ = verified_google_claims(payload.credential, request)
        with closing(connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            current = connection.execute("SELECT google_sub FROM profiles WHERE id = ?", (profile["id"],)).fetchone()
            if current is None or current["google_sub"] is not None:
                connection.rollback()
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este perfil ya tiene una cuenta de Google vinculada.")
            try:
                connection.execute("UPDATE profiles SET google_sub = ? WHERE id = ? AND google_sub IS NULL", (google_sub, profile["id"]))
            except sqlite3.IntegrityError as error:
                connection.rollback()
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Esta cuenta de Google ya está vinculada a otro perfil.") from error
            connection.execute("DELETE FROM auth_sessions WHERE profile_id = ?", (profile["id"],))
            token = issue_session("citizen", profile["id"], connection)
            updated_profile = connection.execute("SELECT * FROM profiles WHERE id = ?", (profile["id"],)).fetchone()
            connection.commit()
        add_audit_event(
            "google_account_linked",
            actor_type="citizen",
            actor_id=profile["id"],
            target_type="profile",
            target_id=profile["id"],
            message="Cuenta de Google vinculada desde una sesión existente",
            metadata={"email": email},
        )
        return {"token": token, "profile": public_profile(updated_profile)}

    @app.post("/api/v1/profiles", status_code=status.HTTP_201_CREATED)
    def create_profile() -> dict[str, object]:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Crea tu cuenta con Google desde la pantalla de acceso.")

    @app.post("/api/v1/auth/login")
    def login() -> dict[str, object]:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="El acceso con usuario y contraseña ya no está disponible. Inicia sesión con Google.")

    @app.get("/api/v1/auth/google/config")
    def google_auth_config() -> dict[str, str]:
        return {"client_id": config.google_client_id}

    @app.post("/api/v1/auth/google")
    def google_login(payload: GoogleAuthPayload, request: Request) -> dict[str, object]:
        if is_rate_limited(rate_limit_key_for_ip(request), limit=12, window_seconds=60):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Demasiados intentos. Espera un momento antes de probar otra vez.")
        google_sub, email, google_name = verified_google_claims(payload.credential, request)

        with closing(connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            profile = connection.execute("SELECT * FROM profiles WHERE google_sub = ?", (google_sub,)).fetchone()
            if profile is not None:
                token = issue_session("citizen", profile["id"], connection)
                connection.commit()
                return {"token": token, "profile": public_profile(profile)}

            linking_existing = payload.username is not None or payload.password is not None
            creating_profile = payload.display_name is not None or payload.school is not None
            if linking_existing and creating_profile:
                connection.rollback()
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Elige vincular tu perfil actual o crear uno nuevo.")
            if linking_existing:
                if not payload.username or not payload.password:
                    connection.rollback()
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Escribe el usuario y la contraseña de tu perfil actual.")
                existing = connection.execute(
                    "SELECT * FROM profiles WHERE username = ?",
                    (normalize_username(payload.username),),
                ).fetchone()
                password_hash = existing["password_hash"] if existing else None
                if existing is None or existing["google_sub"] or not password_hash or not verify_password(payload.password, password_hash):
                    connection.rollback()
                    log_event("auth_error", event_type="google_account_link_failed", client_ip=request.client.host if request.client else "unknown")
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No se pudo vincular el perfil. Comprueba tu usuario y contraseña.")
                profile_id = existing["id"]
                try:
                    connection.execute("UPDATE profiles SET google_sub = ? WHERE id = ?", (google_sub, profile_id))
                except sqlite3.IntegrityError as error:
                    connection.rollback()
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Esta cuenta de Google ya está vinculada a otro perfil.") from error
            elif creating_profile:
                display_name = (payload.display_name or str(google_name or "")).strip()
                school = (payload.school or "").strip()
                if not display_name or school not in SCHOOLS:
                    connection.rollback()
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Escribe tu nombre y selecciona un instituto de Viladecans.")
                email_name = email.split("@", 1)[0]
                base_username = re.sub(r"[^a-z0-9._-]+", "", normalize_username(email_name))[:18].strip("._-")
                base_username = base_username if len(base_username) >= 3 else f"eco{google_sub[:8].lower()}"
                username = base_username
                suffix = 1
                while connection.execute("SELECT 1 FROM profiles WHERE username = ?", (username,)).fetchone():
                    suffix_text = f"-{suffix}"
                    username = f"{base_username[:24 - len(suffix_text)]}{suffix_text}"
                    suffix += 1
                profile_id = str(uuid.uuid4())
                try:
                    connection.execute(
                        "INSERT INTO profiles (id, google_sub, display_name, school, token_hash, balance, contribution, created_at, username, password_hash) VALUES (?, ?, ?, ?, ?, 150, 0, ?, ?, NULL)",
                        (profile_id, google_sub, display_name[:32], school, token_digest(secrets.token_urlsafe(32)), timestamp(), username),
                    )
                except sqlite3.IntegrityError as error:
                    connection.rollback()
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No se pudo crear el perfil; esta cuenta de Google o nombre de usuario ya está en uso.") from error
            else:
                connection.rollback()
                return {
                    "link_required": True,
                    "email": email,
                    "display_name": google_name if isinstance(google_name, str) else "",
                }
            profile = connection.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
            token = issue_session("citizen", profile_id, connection)
            connection.commit()
        add_audit_event(
            "google_account_linked" if linking_existing else "google_profile_created",
            actor_type="citizen",
            actor_id=profile_id,
            target_type="profile",
            target_id=profile_id,
            message="Cuenta de Google vinculada" if linking_existing else "Perfil creado con Google",
            metadata={"email": email},
        )
        return {"token": token, "profile": public_profile(profile)}

    @app.post("/api/v1/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
    def logout(profile: sqlite3.Row = Depends(current_profile), credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> None:
        with closing(connect()) as connection:
            connection.execute("DELETE FROM auth_sessions WHERE token_hash = ?", (token_digest(credentials.credentials),))

    @app.put("/api/v1/account/credentials")
    def update_credentials(
        payload: CredentialsUpdate,
        profile: sqlite3.Row = Depends(current_profile),
    ) -> dict[str, object]:
        username = normalize_username(payload.username)
        if profile["password_hash"] and (not payload.current_password or not verify_password(payload.current_password, profile["password_hash"])):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="La contraseña actual no es correcta.")
        with closing(connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "UPDATE profiles SET username = ?, password_hash = ? WHERE id = ?",
                    (username, hash_password(payload.password), profile["id"]),
                )
                connection.execute("DELETE FROM auth_sessions WHERE profile_id = ?", (profile["id"],))
                token = issue_session("citizen", profile["id"], connection)
                connection.commit()
            except sqlite3.IntegrityError as error:
                connection.rollback()
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ese nombre de usuario ya está ocupado.") from error
        return {"token": token, "username": username}

    @app.get("/api/v1/profile")
    def get_profile(profile: sqlite3.Row = Depends(current_profile)) -> dict[str, object]:
        return public_profile(profile)

    @app.post("/api/v1/eco-id")
    def issue_eco_id(profile: sqlite3.Row = Depends(current_profile)) -> dict[str, object]:
        code = f"VCID-{secrets.token_hex(16).upper()}"
        created_at = datetime.now(UTC)
        expires_at = created_at + timedelta(seconds=45)
        with closing(connect()) as connection:
            connection.execute(
                "INSERT INTO eco_id_tokens (code, profile_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
                (code, profile["id"], created_at.isoformat(), expires_at.isoformat()),
            )
        return {"code": code, "expires_at": expires_at.isoformat(), "lifetime_seconds": 45}

    @app.put("/api/v1/profile")
    def update_profile(
        payload: ProfileUpdate,
        profile: sqlite3.Row = Depends(current_profile),
    ) -> dict[str, object]:
        display_name = payload.display_name.strip()
        school = payload.school.strip()
        if not display_name or school not in SCHOOLS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Revisa el nombre y el instituto seleccionados.")
        with closing(connect()) as connection:
            connection.execute("UPDATE profiles SET display_name = ?, school = ? WHERE id = ?", (display_name, school, profile["id"]))
        return {"id": profile["id"], "display_name": display_name, "school": school}

    @app.post("/api/v1/auth/cashier/login")
    def cashier_login(payload: LoginPayload, request: Request) -> dict[str, object]:
        username = normalize_username(payload.username)
        client_ip = request.client.host if request.client else "unknown"
        if is_rate_limited(rate_limit_key_for_ip(request), limit=12, window_seconds=60):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Demasiados intentos. Espera un momento antes de probar otra vez.")
        if login_is_locked(username, client_ip):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Demasiados intentos. Prueba de nuevo en 15 minutos.")
        with closing(connect()) as connection:
            cashier = connection.execute("SELECT * FROM cashier_users WHERE username = ? AND active = 1", (username,)).fetchone()
        password_hash = cashier["password_hash"] if cashier else None
        password_valid = verify_password(payload.password, password_hash or dummy_password_hash)
        if cashier is None or not password_hash or not password_valid:
            record_login_failure(username, client_ip)
            add_audit_event("cashier_login_failed", actor_type="cashier", actor_id=cashier["id"] if cashier else None, target_type="cashier", target_id=cashier["id"] if cashier else None, message="Login de caja fallido", metadata={"username": username, "client_ip": client_ip})
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario o contraseña de caja incorrectos.")
        clear_login_failures(username, client_ip)
        with closing(connect()) as connection:
            token = issue_session("cashier", cashier["id"], connection)
            merchant = connection.execute("SELECT id, name, is_demo FROM merchants WHERE id = ?", (cashier["merchant_id"],)).fetchone()
        add_audit_event("cashier_login_success", actor_type="cashier", actor_id=cashier["id"], target_type="merchant", target_id=merchant["id"], message="Login de caja correcto", metadata={"username": username, "client_ip": client_ip})
        return {
            "token": token,
            "username": username,
            "must_change_password": bool(cashier["must_change_password"]),
            "merchant": {"id": merchant["id"], "name": merchant["name"], "is_demo": bool(merchant["is_demo"])},
        }

    @app.get("/api/v1/cashier/me")
    def cashier_me(cashier: sqlite3.Row = Depends(current_cashier)) -> dict[str, object]:
        return {
            "username": cashier["username"],
            "merchant_id": cashier["merchant_id"],
            "merchant_name": cashier["merchant_name"],
            "must_change_password": bool(cashier["must_change_password"]),
            "is_demo": bool(cashier["merchant_is_demo"]),
        }

    @app.put("/api/v1/cashier/password")
    def cashier_change_password(
        payload: PasswordUpdate,
        cashier: sqlite3.Row = Depends(current_cashier),
        credentials: HTTPAuthorizationCredentials = Depends(bearer),
    ) -> dict[str, str]:
        if not cashier["must_change_password"] and (
            not payload.current_password or not verify_password(payload.current_password, cashier["password_hash"])
        ):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="La contraseña actual no es correcta.")
        with closing(connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "UPDATE cashier_users SET password_hash = ?, must_change_password = 0 WHERE id = ?",
                (hash_password(payload.password), cashier["id"]),
            )
            connection.execute("DELETE FROM auth_sessions WHERE cashier_id = ?", (cashier["id"],))
            token = issue_session("cashier", cashier["id"], connection)
            connection.commit()
        return {"token": token, "username": cashier["username"]}

    @app.post("/api/v1/auth/cashier/logout", status_code=status.HTTP_204_NO_CONTENT)
    def cashier_logout(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> None:
        if credentials is None:
            return
        with closing(connect()) as connection:
            connection.execute("DELETE FROM auth_sessions WHERE token_hash = ? AND subject_type = 'cashier'", (token_digest(credentials.credentials),))

    @app.get("/api/v1/dashboard")
    def dashboard(profile: sqlite3.Row = Depends(current_profile)) -> dict[str, object]:
        with closing(connect()) as connection:
            schools = connection.execute(
                "SELECT school, SUM(contribution) AS points FROM profiles GROUP BY school ORDER BY points DESC, school ASC"
            ).fetchall()
            events = connection.execute(
                "SELECT description, merchant, points, created_at FROM point_events WHERE profile_id = ? ORDER BY created_at DESC LIMIT 8",
                (profile["id"],),
            ).fetchall()
            personal_rank = connection.execute(
                "SELECT COUNT(*) + 1 AS rank FROM profiles WHERE school = ? AND contribution > ?",
                (profile["school"], profile["contribution"]),
            ).fetchone()["rank"]
        board = [{"school": row["school"], "points": row["points"], "is_demo": True} for row in schools]
        own_rank = next((index for index, row in enumerate(board, 1) if row["school"] == profile["school"]), 1)
        return {
            "balance": profile["balance"],
            "contribution": profile["contribution"],
            "steps": {"count": 0, "goal": 8000, "source": "Sincronización pendiente", "is_demo": True},
            "school": profile["school"],
            "school_rank": own_rank,
            "personal_rank": personal_rank,
            "school_points": next((row["points"] for row in board if row["school"] == profile["school"]), 0),
            "league": board,
            "activity": [
                {
                    "description": row["description"],
                    "merchant": row["merchant"],
                    "points": row["points"],
                    "created_at": row["created_at"],
                    "is_demo": True,
                }
                for row in events
            ],
            "is_demo": True,
        }

    @app.post("/api/v1/demo/eco-scan")
    def demo_eco_scan(profile: sqlite3.Row = Depends(current_profile)) -> dict[str, object]:
        if production:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Los puntos solo los puede conceder una caja de comercio autorizada.")
        created_at = timestamp()
        with closing(connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "UPDATE profiles SET balance = balance + 10, contribution = contribution + 10 WHERE id = ?",
                (profile["id"],),
            )
            connection.execute(
                "INSERT INTO point_events (id, profile_id, description, merchant, points, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), profile["id"], "Escaneo de caja simulado", "Comercio de demostración", 10, created_at),
            )
            connection.commit()
            updated = connection.execute("SELECT balance, contribution FROM profiles WHERE id = ?", (profile["id"],)).fetchone()
        return {"balance": updated["balance"], "contribution": updated["contribution"], "points": 10, "is_demo": True}

    @app.get("/api/v1/merchants")
    def merchants() -> dict[str, object]:
        with closing(connect()) as connection:
            rows = connection.execute("SELECT * FROM merchants ORDER BY is_demo ASC, name ASC").fetchall()
        items = [
            {**dict(row), "is_demo": bool(row["is_demo"])}
            for row in rows
        ]
        return {"items": items, "source": "OpenStreetMap", "is_demo": True}

    @app.get("/api/v1/rewards")
    def rewards() -> dict[str, object]:
        return {"items": list(REWARDS), "is_demo": True}

    @app.get("/api/v1/coupons")
    def coupons(profile: sqlite3.Row = Depends(current_profile)) -> dict[str, object]:
        with closing(connect()) as connection:
            rows = connection.execute(
                "SELECT * FROM coupons WHERE profile_id = ? ORDER BY created_at DESC",
                (profile["id"],),
            ).fetchall()
        items = [public_coupon(row) for row in rows]
        return {
            "active": [item for item in items if item["status"] == "active"],
            "redeemed": [item for item in items if item["status"] == "redeemed"],
        }

    @app.post("/api/v1/coupons", status_code=status.HTTP_201_CREATED)
    def create_coupon(
        payload: RewardRedeem,
        profile: sqlite3.Row = Depends(current_profile),
    ) -> dict[str, object]:
        reward = next((item for item in REWARDS if item["id"] == payload.reward_id), None)
        if reward is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recompensa no encontrada.")
        code = f"VC-{secrets.token_hex(16).upper()}"
        coupon_id = str(uuid.uuid4())
        created = datetime.now(UTC)
        expires = created + timedelta(days=45)
        with closing(connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            updated = connection.execute(
                "UPDATE profiles SET balance = balance - ? WHERE id = ? AND balance >= ?",
                (reward["cost"], profile["id"], reward["cost"]),
            )
            if updated.rowcount != 1:
                connection.rollback()
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No tienes saldo suficiente para este vale.")
            connection.execute(
                "INSERT INTO coupons (id, code, profile_id, merchant_id, reward_id, name, store, cost, status, created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)",
                (coupon_id, code, profile["id"], reward["merchant_id"], reward["id"], reward["name"], reward["store"], reward["cost"], created.isoformat(), expires.isoformat()),
            )
            connection.commit()
            coupon = connection.execute("SELECT * FROM coupons WHERE id = ?", (coupon_id,)).fetchone()
            balance = connection.execute("SELECT balance FROM profiles WHERE id = ?", (profile["id"],)).fetchone()["balance"]
        return {"coupon": public_coupon(coupon), "balance": balance}

    @app.post("/api/v1/coupons/redeem")
    def self_redeem_coupon(
        payload: CouponScan,
        profile: sqlite3.Row = Depends(current_profile),
    ) -> dict[str, object]:
        if not self_redeem_enabled:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El canje debe confirmarlo el comercio desde su caja.")
        with closing(connect()) as connection:
            owns_coupon = connection.execute(
                "SELECT 1 FROM coupons WHERE profile_id = ? AND code = ?",
                (profile["id"], payload.code),
            ).fetchone()
        if owns_coupon is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ese cupón no pertenece a este monedero.")
        coupon = coupon_by_code(payload.code)
        return {"coupon": public_coupon_from_dict(coupon), "status": "redeemed", "is_demo": True}

    @app.post("/api/v1/merchant/coupons/redeem")
    @app.post("/api/v1/cashier/coupons/redeem")
    def merchant_redeem_coupon(
        payload: CouponScan,
        cashier: sqlite3.Row = Depends(current_cashier),
    ) -> dict[str, object]:
        if cashier["must_change_password"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cambia la contraseña inicial antes de escanear cupones.")
        coupon = coupon_by_code(payload.code, cashier["merchant_id"], cashier["id"])
        return {
            "coupon": public_coupon_from_dict(coupon),
            "status": "redeemed",
            "merchant": cashier["merchant_name"],
            "is_demo": bool(cashier["merchant_is_demo"]),
        }

    @app.post("/api/v1/cashier/eco-id/scan")
    def cashier_scan_eco_id(
        payload: EcoIdScan,
        cashier: sqlite3.Row = Depends(current_cashier),
    ) -> dict[str, object]:
        if cashier["must_change_password"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cambia la contraseña inicial antes de escanear EcoID.")
        now = datetime.now(UTC)
        scanned_at = now.isoformat()
        with closing(connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            eco_id = connection.execute("SELECT * FROM eco_id_tokens WHERE code = ?", (payload.code,)).fetchone()
            if eco_id is None:
                connection.rollback()
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EcoID no válido o ya no disponible.")
            if eco_id["scanned_at"] is not None:
                connection.rollback()
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este EcoID ya se ha utilizado.")
            if datetime.fromisoformat(eco_id["expires_at"]) <= now:
                connection.rollback()
                raise HTTPException(status_code=status.HTTP_410_GONE, detail="El EcoID ha caducado. Pide a la persona que genere otro.")
            claimed = connection.execute(
                "UPDATE eco_id_tokens SET scanned_at = ?, cashier_id = ? WHERE code = ? AND scanned_at IS NULL AND expires_at > ?",
                (scanned_at, cashier["id"], payload.code, scanned_at),
            )
            if claimed.rowcount != 1:
                connection.rollback()
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este EcoID ya se ha utilizado.")
            connection.execute(
                "UPDATE profiles SET balance = balance + 10, contribution = contribution + 10 WHERE id = ?",
                (eco_id["profile_id"],),
            )
            connection.execute(
                "INSERT INTO point_events (id, profile_id, description, merchant, points, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), eco_id["profile_id"], "EcoID validado en caja", cashier["merchant_name"], 10, scanned_at),
            )
            person = connection.execute("SELECT display_name, balance FROM profiles WHERE id = ?", (eco_id["profile_id"],)).fetchone()
            connection.commit()
        add_audit_event(
            "ecoid_awarded",
            actor_type="cashier",
            actor_id=cashier["id"],
            target_type="profile",
            target_id=eco_id["profile_id"],
            message="EcoID validado · +10 puntos",
            metadata={"merchant_id": cashier["merchant_id"], "points": 10},
        )
        return {
            "display_name": person["display_name"],
            "points": 10,
            "balance": person["balance"],
            "merchant": cashier["merchant_name"],
            "is_demo": bool(cashier["merchant_is_demo"]),
        }

    @app.post("/api/v1/admin/cashiers", status_code=status.HTTP_201_CREATED)
    def provision_cashier(
        payload: CashierProvision,
        admin_secret: Annotated[str | None, Header(alias="X-Admin-Key")] = None,
    ) -> dict[str, object]:
        if not admin_secret_key or not secrets.compare_digest(admin_secret or "", admin_secret_key):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credencial municipal no válida.")
        username = normalize_username(payload.username)
        with closing(connect()) as connection:
            merchant = connection.execute("SELECT id, name FROM merchants WHERE id = ?", (payload.merchant_id,)).fetchone()
            if merchant is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comercio no encontrado.")
            cashier_id = str(uuid.uuid4())
            try:
                connection.execute(
                    "INSERT INTO cashier_users (id, username, password_hash, merchant_id, must_change_password, active, created_at) VALUES (?, ?, ?, ?, 1, 1, ?)",
                    (cashier_id, username, hash_password("Viladecans"), merchant["id"], timestamp()),
                )
            except sqlite3.IntegrityError as error:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ese usuario de caja ya existe.") from error
        add_audit_event("cashier_created", actor_type="admin", actor_id="admin", target_type="cashier", target_id=cashier_id, message="Caja creada por admin", metadata={"username": username, "merchant_id": payload.merchant_id})
        return {"id": cashier_id, "username": username, "merchant": merchant["name"], "must_change_password": True}

    @app.get("/api/v1/admin/audit")
    def admin_audit(admin_secret: Annotated[str | None, Header(alias="X-Admin-Key")] = None) -> dict[str, object]:
        if not admin_secret_key or not secrets.compare_digest(admin_secret or "", admin_secret_key):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credencial municipal no válida.")
        with closing(connect()) as connection:
            rows = connection.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 50").fetchall()
        return {"items": [{"id": row["id"], "event_type": row["event_type"], "message": row["message"], "created_at": row["created_at"], "metadata": json.loads(row["metadata"] or "{}") } for row in rows]}

    @app.get("/api/v1/admin/analytics")
    def admin_analytics(admin_secret: Annotated[str | None, Header(alias="X-Admin-Key")] = None) -> dict[str, object]:
        if not admin_secret_key or not secrets.compare_digest(admin_secret or "", admin_secret_key):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credencial municipal no válida.")
        report = analytics_service.get_summary()
        report["summary"]["production"] = production
        return report

    @app.get("/api/v1/cashier/validations")
    def cashier_validations(cashier: sqlite3.Row = Depends(current_cashier)) -> dict[str, object]:
        with closing(connect()) as connection:
            rows = connection.execute(
                "SELECT * FROM coupon_validations WHERE cashier_id = ? ORDER BY validated_at DESC LIMIT 30",
                (cashier["id"],),
            ).fetchall()
        return {"items": [{"id": row["id"], "code": row["code"], "status": row["status"], "reason": row["reason"], "validated_at": row["validated_at"], "details": json.loads(row["details"] or "{}") } for row in rows]}

    @app.get("/api/v1/cashier/dashboard")
    def cashier_dashboard(cashier: sqlite3.Row = Depends(current_cashier)) -> dict[str, object]:
        now = datetime.now(UTC)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        week_start = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        with closing(connect()) as connection:
            today_coupon_rows = connection.execute(
                "SELECT status, COUNT(*) AS total FROM coupon_validations WHERE cashier_id = ? AND validated_at >= ? GROUP BY status",
                (cashier["id"], day_start),
            ).fetchall()
            week_coupon_rows = connection.execute(
                "SELECT validated_at, status FROM coupon_validations WHERE cashier_id = ? AND validated_at >= ? ORDER BY validated_at DESC LIMIT 500",
                (cashier["id"], week_start),
            ).fetchall()
            week_ecoid_rows = connection.execute(
                "SELECT created_at FROM audit_logs WHERE actor_id = ? AND event_type = 'ecoid_awarded' AND created_at >= ? ORDER BY created_at DESC LIMIT 500",
                (cashier["id"], week_start),
            ).fetchall()
            recent_coupons = connection.execute(
                "SELECT code, status, reason, validated_at FROM coupon_validations WHERE cashier_id = ? ORDER BY validated_at DESC LIMIT 8",
                (cashier["id"],),
            ).fetchall()
            recent_ecoids = connection.execute(
                "SELECT message, created_at FROM audit_logs WHERE actor_id = ? AND event_type = 'ecoid_awarded' ORDER BY created_at DESC LIMIT 8",
                (cashier["id"],),
            ).fetchall()
            today_points = connection.execute(
                "SELECT COUNT(*) AS total FROM eco_id_tokens WHERE cashier_id = ? AND scanned_at >= ?",
                (cashier["id"], day_start),
            ).fetchone()["total"]
        today_counts = {row["status"]: row["total"] for row in today_coupon_rows}
        daily_activity: dict[str, dict[str, int | str]] = {}
        for row in week_coupon_rows:
            day = row["validated_at"][:10]
            daily_activity.setdefault(day, {"date": day, "coupons": 0, "ecoids": 0})
            if row["status"] == "success":
                daily_activity[day]["coupons"] += 1
        for row in week_ecoid_rows:
            day = row["created_at"][:10]
            daily_activity.setdefault(day, {"date": day, "coupons": 0, "ecoids": 0})
            daily_activity[day]["ecoids"] += 1
        return {
            "merchant": cashier["merchant_name"],
            "is_demo": bool(cashier["merchant_is_demo"]),
            "today": {
                "successful_coupons": today_counts.get("success", 0),
                "failed_coupons": today_counts.get("failed", 0),
                "ecoid_scans": today_points,
            },
            "week": {
                "successful_coupons": sum(row["status"] == "success" for row in week_coupon_rows),
                "ecoid_scans": len(week_ecoid_rows),
            },
            "activity_by_day": sorted(daily_activity.values(), key=lambda item: item["date"]),
            "recent_coupons": [dict(row) for row in recent_coupons],
            "recent_ecoids": [dict(row) for row in recent_ecoids],
        }

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(ROOT / "index.html")

    @app.get("/sw.js", include_in_schema=False)
    def service_worker() -> FileResponse:
        return FileResponse(ROOT / "sw.js", media_type="application/javascript", headers={"Service-Worker-Allowed": "/"})

    for asset in ("index.html", "manifest.json", "viladecans.js", "viladecans.css", "api-client.js", "api-client.css", "cashier.css", "cashier-dashboard.css"):
        app.add_api_route(f"/{asset}", lambda asset=asset: FileResponse(ROOT / asset), methods=["GET"], include_in_schema=False)

    app.mount("/icons", StaticFiles(directory=ROOT / "icons"), name="icons")
    return app


def public_coupon_from_dict(coupon: dict[str, object]) -> dict[str, object]:
    expiry = datetime.fromisoformat(str(coupon["expires_at"])).strftime("%-d %b")
    return {
        "code": coupon["code"],
        "name": coupon["name"],
        "store": coupon["store"],
        "cost": coupon["cost"],
        "expiry": expiry,
        "status": coupon["status"],
        "redeemed_at": coupon["redeemed_at"],
    }


app = create_app()
