from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from db import is_postgres_url as _is_postgres_url

ROOT = Path(__file__).resolve().parent
DEFAULT_DATABASE = ROOT / "data" / "vilacircula.sqlite3"


def get_database_url() -> str:
    return os.getenv("VILACIRCULA_DATABASE_URL") or os.getenv("DATABASE_URL") or f"sqlite:///{DEFAULT_DATABASE.as_posix()}"


def is_postgres_url(url: str | None) -> bool:
    return _is_postgres_url(url)


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_allowed_origins(value: str | None, fallback: list[str]) -> list[str]:
    if value is None or not value.strip():
        return fallback
    origins = [origin.strip() for origin in value.split(",") if origin.strip()]
    return origins if origins else fallback


@dataclass(frozen=True)
class AppConfig:
    database_path: Path
    database_url: str
    admin_secret_key: str
    merchant_key: str
    environment: str
    production: bool
    self_redeem_enabled: bool
    allowed_origins: list[str]
    initial_cashier_password: str
    google_client_id: str
    admin_emails: frozenset[str]
    school_registration_codes: dict[str, str]

    @classmethod
    def from_env(
        cls,
        *,
        database_path: str | Path | None = None,
        merchant_key: str | None = None,
        allow_self_redeem: bool | None = None,
        admin_key: str | None = None,
        google_client_id: str | None = None,
        environment: str | None = None,
        admin_emails: set[str] | frozenset[str] | None = None,
        school_registration_codes: dict[str, str] | None = None,
    ) -> "AppConfig":
        db_path = Path(database_path or os.getenv("VILACIRCULA_DATABASE", DEFAULT_DATABASE))
        database_url = (
            f"sqlite:///{db_path.as_posix()}"
            if database_path is not None
            else os.getenv("VILACIRCULA_DATABASE_URL") or os.getenv("DATABASE_URL") or f"sqlite:///{db_path.as_posix()}"
        )
        env = (environment or os.getenv("VILACIRCULA_ENV", "development")).strip().lower()
        production = env == "production"
        self_redeem_enabled = allow_self_redeem if allow_self_redeem is not None else parse_bool(
            os.getenv("VILACIRCULA_ALLOW_SELF_REDEEM"), default=not production
        )
        admin_secret = admin_key if admin_key is not None else os.getenv("VILACIRCULA_ADMIN_KEY", "")
        merchant_secret = merchant_key if merchant_key is not None else os.getenv("VILACIRCULA_MERCHANT_KEY", "")
        default_allowed_origins = [
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:8001",
            "http://127.0.0.1:8001",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
        allowed_origins = parse_allowed_origins(os.getenv("VILACIRCULA_ALLOWED_ORIGINS"), default_allowed_origins)
        if production:
            if "*" in allowed_origins or not allowed_origins:
                raise RuntimeError("VILACIRCULA_ALLOWED_ORIGINS must be explicitly configured in production. Do not use wildcard origins.")
            allowed_origins = [origin.rstrip("/") for origin in allowed_origins if origin.rstrip("/")]
            invalid = [origin for origin in allowed_origins if not origin.startswith(("https://", "http://localhost", "http://127.0.0.1"))]
            if invalid:
                raise RuntimeError(f"Forbidden production origins: {invalid}")
        if "*" in allowed_origins:
            allowed_origins = ["*"]
        initial_cashier_password = os.getenv("VILACIRCULA_INITIAL_CASHIER_PASSWORD", "" if production else "Viladecans")
        configured_google_client_id = (
            google_client_id if google_client_id is not None
            else os.getenv("VILACIRCULA_GOOGLE_CLIENT_ID", "")
        ).strip()
        configured_admin_emails = admin_emails if admin_emails is not None else {
            email.strip().casefold()
            for email in os.getenv("VILACIRCULA_ADMIN_EMAILS", "").split(",")
            if email.strip()
        }
        configured_school_codes = school_registration_codes
        if configured_school_codes is None:
            try:
                configured_school_codes = json.loads(os.getenv("VILACIRCULA_SCHOOL_CODES", "{}"))
            except json.JSONDecodeError as error:
                raise RuntimeError("VILACIRCULA_SCHOOL_CODES must be a JSON object mapping school names to registration codes.") from error
        if not isinstance(configured_school_codes, dict):
            raise RuntimeError("VILACIRCULA_SCHOOL_CODES must be a JSON object mapping school names to registration codes.")
        school_registration_codes = {}
        for school, code in configured_school_codes.items():
            if school not in {"Goar", "Torre-roja", "Josep Mestres", "Miramar", "Olímpia", "Sales"}:
                raise RuntimeError(f"Unknown school in VILACIRCULA_SCHOOL_CODES: {school}")
            if not isinstance(code, str) or not code.strip():
                raise RuntimeError(f"Registration code for {school} must be a non-empty string.")
            normalized_code = code.strip().casefold()
            if normalized_code in school_registration_codes.values():
                raise RuntimeError("VILACIRCULA_SCHOOL_CODES must use a unique code for each school.")
            school_registration_codes[school] = normalized_code
        return cls(
            database_path=db_path,
            database_url=database_url,
            admin_secret_key=admin_secret,
            merchant_key=merchant_secret,
            environment=env,
            production=production,
            self_redeem_enabled=self_redeem_enabled,
            allowed_origins=allowed_origins,
            initial_cashier_password=initial_cashier_password,
            google_client_id=configured_google_client_id,
            admin_emails=frozenset(email.strip().casefold() for email in configured_admin_emails),
            school_registration_codes=school_registration_codes,
        )
