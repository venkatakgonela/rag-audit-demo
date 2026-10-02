import base64
import hashlib
import hmac
import json
import re


def encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def issue_token(subject: str, key: str) -> str:
    if len(key.encode()) < 32 or not re.fullmatch(
        r"synthetic-[a-z0-9-]{1,100}", subject
    ):
        raise ValueError("Invalid stub configuration or subject")
    payload = encode(json.dumps({"sub": subject}, separators=(",", ":")).encode())
    message = f"v1.{payload}"
    signature = encode(hmac.digest(key.encode(), message.encode(), hashlib.sha256))
    return f"{message}.{signature}"


def verify_token(token: str, key: str) -> str:
    if len(key.encode()) < 32:
        raise ValueError("Invalid stub configuration")
    try:
        if len(token) > 1024 or not re.fullmatch(
            r"v1\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", token
        ):
            raise ValueError("Invalid token")
        version, payload, signature = token.split(".")
        expected = encode(
            hmac.digest(key.encode(), f"{version}.{payload}".encode(), hashlib.sha256)
        )
        if not hmac.compare_digest(signature, expected):
            raise ValueError("Invalid signature")
        decoded = json.loads(
            base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
        )
        if type(decoded) is not dict or set(decoded) != {"sub"}:
            raise ValueError("Invalid claims")
        subject = decoded["sub"]
        if type(subject) is not str or issue_token(subject, key) != token:
            raise ValueError("Noncanonical token")
        return subject
    except Exception:
        raise ValueError("Invalid stub token") from None
