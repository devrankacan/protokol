import os
import hashlib
import hmac
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired


SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
APP_PASSWORD = os.getenv("APP_PASSWORD", "genexa2024")
SESSION_COOKIE = "genexa_session"
SESSION_MAX_AGE = 86400 * 7  # 7 days

_serializer = URLSafeTimedSerializer(SECRET_KEY)


def verify_password(password: str) -> bool:
    return hmac.compare_digest(password, APP_PASSWORD)


def create_session_token() -> str:
    return _serializer.dumps({"authenticated": True})


def verify_session_token(token: str) -> bool:
    try:
        data = _serializer.loads(token, max_age=SESSION_MAX_AGE)
        return data.get("authenticated") is True
    except (BadSignature, SignatureExpired):
        return False
