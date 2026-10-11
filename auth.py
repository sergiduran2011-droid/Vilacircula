from __future__ import annotations

import hashlib
import json
import logging
import secrets
from datetime import UTC, datetime
from typing import Any

PASSWORD_SCRYPT_N = 2**14
logger = logging.getLogger("vilacircula.security")


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


def log_security_event(event: str, **context: Any) -> None:
    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event": event,
        **context,
    }
    logger.info(json.dumps(payload, ensure_ascii=False, default=str))
