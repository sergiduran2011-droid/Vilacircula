from __future__ import annotations

import hashlib
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
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

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
CREATE TABLE IF NOT EXISTS point_events (
    id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL REFERENCES profiles(id),
    description TEXT NOT NULL,
    merchant TEXT NOT NULL,
    points INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS point_events_profile_created_idx ON point_events(profile_id, created_at DESC);
"""


class ProfileCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=32)
    school: str = Field(min_length=1, max_length=40)
    username: str = Field(min_length=3, max_length=24, pattern=r"^[A-Za-z0-9._-]+$")
    password: str = Field(min_length=10, max_length=128)


class ProfileUpdate(BaseModel):
    display_name: str = Field(min_length=1, max_length=32)
    school: str = Field(min_length=1, max_length=40)


class LoginPayload(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=128)


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


PASSWORD_SCRYPT_N = 2**14


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


def timestamp() -> str:
    return datetime.now(UTC).isoformat()


def public_profile(profile: sqlite3.Row) -> dict[str, object]:
    return {
        "id": profile["id"],
        "display_name": profile["display_name"],
        "school": profile["school"],
        "username": profile["username"],
        "balance": profile["balance"],
        "contribution": profile["contribution"],
        "password_setup_required": profile["password_hash"] is None,
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
) -> FastAPI:
    db_path = Path(database_path or os.getenv("VILACIRCULA_DATABASE", DEFAULT_DATABASE))
    key = merchant_key if merchant_key is not None else os.getenv("VILACIRCULA_MERCHANT_KEY", "")
    admin_secret_key = admin_key if admin_key is not None else os.getenv("VILACIRCULA_ADMIN_KEY", "")
    production = os.getenv("VILACIRCULA_ENV", "development").lower() == "production"
    self_redeem_enabled = allow_self_redeem if allow_self_redeem is not None else (
        os.getenv("VILACIRCULA_ALLOW_SELF_REDEEM", "0" if production else "1") == "1"
    )

    def connect() -> sqlite3.Connection:
        connection = sqlite3.connect(db_path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect()) as connection:
        connection.executescript(SCHEMA)
        profile_columns = {row["name"] for row in connection.execute("PRAGMA table_info(profiles)")}
        if "username" not in profile_columns:
            connection.execute("ALTER TABLE profiles ADD COLUMN username TEXT")
        if "password_hash" not in profile_columns:
            connection.execute("ALTER TABLE profiles ADD COLUMN password_hash TEXT")
        coupon_columns = {row["name"] for row in connection.execute("PRAGMA table_info(coupons)")}
        if "merchant_id" not in coupon_columns:
            connection.execute("ALTER TABLE coupons ADD COLUMN merchant_id TEXT REFERENCES merchants(id)")
        if "redeemed_by" not in coupon_columns:
            connection.execute("ALTER TABLE coupons ADD COLUMN redeemed_by TEXT REFERENCES cashier_users(id)")
        connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS profiles_username_idx ON profiles(username) WHERE username IS NOT NULL")
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
                    "INSERT OR IGNORE INTO auth_sessions (token_hash, subject_type, profile_id, created_at, expires_at) VALUES (?, 'citizen', ?, ?, ?)",
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
                    "INSERT OR IGNORE INTO cashier_users (id, username, password_hash, merchant_id, must_change_password, active, created_at) VALUES (?, ?, ?, ?, 1, 1, ?)",
                    (str(uuid.uuid4()), username, hash_password(initial_cashier_password), merchant_id, timestamp()),
                )

    app = FastAPI(title="VilaCircula API", version="1.0.0", description="API de demostración para perfiles, saldo y cupones de VilaCircula.")
    app.state.database_path = db_path
    app.state.demo = True
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("VILACIRCULA_ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000,http://localhost:8001").split(","),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["Authorization", "Content-Type", "X-Admin-Key"],
    )
    bearer = HTTPBearer(auto_error=False)
    dummy_password_hash = hash_password(secrets.token_urlsafe(24))

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

    def clear_login_failures(username: str, client_ip: str) -> None:
        with closing(connect()) as connection:
            connection.execute("DELETE FROM login_attempts WHERE username = ? AND client_ip = ?", (username, client_ip))

    def current_profile(
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
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="La sesión del dispositivo no es válida.")
        if datetime.fromisoformat(profile["session_expires_at"]) <= datetime.now(UTC):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="La sesión ha caducado. Inicia sesión otra vez.")
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
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este cupón ya fue canjeado.")
            if datetime.fromisoformat(coupon["expires_at"]) <= datetime.now(UTC):
                connection.rollback()
                raise HTTPException(status_code=status.HTTP_410_GONE, detail="Este cupón ha caducado.")
            if merchant_id is not None and coupon["merchant_id"] != merchant_id:
                connection.rollback()
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
            return redeemed

    @app.get("/api/v1/health")
    def health() -> dict[str, object]:
        return {"status": "ok", "mode": "demo", "persistent_database": str(db_path.name)}

    @app.post("/api/v1/profiles", status_code=status.HTTP_201_CREATED)
    def create_profile(payload: ProfileCreate) -> dict[str, object]:
        display_name = payload.display_name.strip()
        school = payload.school.strip()
        username = normalize_username(payload.username)
        if not display_name:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Escribe tu nombre o apodo.")
        if school not in SCHOOLS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Selecciona un instituto de Viladecans.")
        profile_id = str(uuid.uuid4())
        with closing(connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "INSERT INTO profiles (id, display_name, school, token_hash, balance, contribution, created_at, username, password_hash) VALUES (?, ?, ?, ?, 150, 0, ?, ?, ?)",
                    (profile_id, display_name, school, token_digest(secrets.token_urlsafe(32)), timestamp(), username, hash_password(payload.password)),
                )
                token = issue_session("citizen", profile_id, connection)
                connection.commit()
            except sqlite3.IntegrityError as error:
                connection.rollback()
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ese nombre de usuario ya está ocupado.") from error
        return {
            "id": profile_id,
            "display_name": display_name,
            "school": school,
            "username": username,
            "balance": 150,
            "contribution": 0,
            "token": token,
            "is_demo": True,
        }

    @app.post("/api/v1/auth/login")
    def login(payload: LoginPayload, request: Request) -> dict[str, object]:
        username = normalize_username(payload.username)
        client_ip = request.client.host if request.client else "unknown"
        if login_is_locked(username, client_ip):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Demasiados intentos. Prueba de nuevo en 15 minutos.")
        with closing(connect()) as connection:
            profile = connection.execute("SELECT * FROM profiles WHERE username = ?", (username,)).fetchone()
        password_hash = profile["password_hash"] if profile else None
        password_valid = verify_password(payload.password, password_hash or dummy_password_hash)
        if profile is None or not password_hash or not password_valid:
            record_login_failure(username, client_ip)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario o contraseña incorrectos.")
        clear_login_failures(username, client_ip)
        with closing(connect()) as connection:
            token = issue_session("citizen", profile["id"], connection)
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
        if login_is_locked(username, client_ip):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Demasiados intentos. Prueba de nuevo en 15 minutos.")
        with closing(connect()) as connection:
            cashier = connection.execute("SELECT * FROM cashier_users WHERE username = ? AND active = 1", (username,)).fetchone()
        password_hash = cashier["password_hash"] if cashier else None
        password_valid = verify_password(payload.password, password_hash or dummy_password_hash)
        if cashier is None or not password_hash or not password_valid:
            record_login_failure(username, client_ip)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario o contraseña de caja incorrectos.")
        clear_login_failures(username, client_ip)
        with closing(connect()) as connection:
            token = issue_session("cashier", cashier["id"], connection)
            merchant = connection.execute("SELECT id, name, is_demo FROM merchants WHERE id = ?", (cashier["merchant_id"],)).fetchone()
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
        return {"id": cashier_id, "username": username, "merchant": merchant["name"], "must_change_password": True}

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(ROOT / "index.html")

    @app.get("/sw.js", include_in_schema=False)
    def service_worker() -> FileResponse:
        return FileResponse(ROOT / "sw.js", media_type="application/javascript", headers={"Service-Worker-Allowed": "/"})

    for asset in ("index.html", "manifest.json", "viladecans.js", "viladecans.css", "api-client.js", "api-client.css", "cashier.css"):
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
