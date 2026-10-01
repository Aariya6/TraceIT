import base64, hashlib, hmac, os, time
from typing import Optional
import jwt
from fastapi import HTTPException, Request
from .config import settings

ALGO = "HS256"

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return "scrypt$16384$8$1$" + base64.urlsafe_b64encode(salt).decode() + "$" + base64.urlsafe_b64encode(digest).decode()

def verify_password(password: str, encoded: str) -> bool:
    try:
        _, n, r, p, salt_b64, digest_b64 = encoded.split("$")
        salt = base64.urlsafe_b64decode(salt_b64.encode())
        expected = base64.urlsafe_b64decode(digest_b64.encode())
        actual = hashlib.scrypt(password.encode(), salt=salt, n=int(n), r=int(r), p=int(p))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False

def create_token(user_id: int, email: str) -> str:
    now = int(time.time())
    payload = {"sub": str(user_id), "email": email, "iat": now, "exp": now + settings.auth_token_hours * 3600}
    return jwt.encode(payload, settings.auth_secret, algorithm=ALGO)

def get_bearer(request: Request) -> Optional[str]:
    value = request.headers.get("Authorization", "")
    if value.lower().startswith("bearer "):
        return value[7:].strip()
    return None

def current_user_id(request: Request) -> int:
    token = get_bearer(request)
    if not token:
        raise HTTPException(401, "Sign in required")
    try:
        payload = jwt.decode(token, settings.auth_secret, algorithms=[ALGO])
        return int(payload["sub"])
    except Exception:
        raise HTTPException(401, "Session expired or invalid")
