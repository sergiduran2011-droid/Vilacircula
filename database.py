from __future__ import annotations

import os
import re
import secrets
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path

from auth import hash_password, normalize_username, timestamp
from models import CASHIER_SEEDS, MERCHANTS, REWARDS

ROOT = Path(__file__).resolve().parent
DEFAULT_DATABASE = ROOT / "data" / "vilacircula.sqlite3"

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


def connect_database(db_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(db_path), timeout=10, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def get_database_path(database_path: str | Path | None = None) -> Path:
    return Path(database_path or os.getenv("VILACIRCULA_DATABASE", DEFAULT_DATABASE))


def seed_database(db_path: Path, *, initial_cashier_password: str, production: bool) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect_database(db_path)) as connection:
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
        if initial_cashier_password:
            for username, merchant_id in CASHIER_SEEDS:
                connection.execute(
                    "INSERT OR IGNORE INTO cashier_users (id, username, password_hash, merchant_id, must_change_password, active, created_at) VALUES (?, ?, ?, ?, 1, 1, ?)",
                    (str(uuid.uuid4()), username, hash_password(initial_cashier_password), merchant_id, timestamp()),
                )
