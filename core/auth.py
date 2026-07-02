import base64
import hashlib
import hmac
import json
import os
import time


AUTH_SECRET = os.getenv("DUOLICKGO_SECRET_KEY", "duolickgo-secret-key")
AUTH_COOKIE_NAME = "duolickgo_access_token"
AUTH_TOKEN_TTL_SECONDS = 60 * 60 * 24 * 14


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def create_access_token(subject: str = "duolickgo") -> str:
    now = int(time.time())
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + AUTH_TOKEN_TTL_SECONDS,
    }
    payload_raw = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    payload_part = _b64encode(payload_raw)
    signature = hmac.new(
        AUTH_SECRET.encode("utf-8"),
        payload_part.encode("ascii"),
        hashlib.sha256,
    ).digest()
    signature_part = _b64encode(signature)
    return f"{payload_part}.{signature_part}"


def verify_access_token(token: str):
    value = str(token or "").strip()
    if not value or "." not in value:
        return None

    payload_part, signature_part = value.rsplit(".", 1)
    expected_signature = _b64encode(
        hmac.new(
            AUTH_SECRET.encode("utf-8"),
            payload_part.encode("ascii"),
            hashlib.sha256,
        ).digest()
    )

    if not hmac.compare_digest(signature_part, expected_signature):
        return None

    try:
        payload = json.loads(_b64decode(payload_part).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return None

    exp = int(payload.get("exp") or 0)
    if exp and exp < int(time.time()):
        return None

    return payload


def extract_bearer_token(authorization_header: str | None):
    value = str(authorization_header or "").strip()
    if not value.lower().startswith("bearer "):
        return None
    return value[7:].strip() or None
