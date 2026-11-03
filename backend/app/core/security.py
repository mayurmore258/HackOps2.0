"""
THERMOS AI - Core Security Module

Password hashing, JWT token creation/verification, and API security.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
import secrets
import hashlib
import hmac

from app.core.config import settings
from app.core.exceptions import ThermosBaseException


class AuthenticationError(ThermosBaseException):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Could not validate credentials"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_FAILED",
            status_code=401
        )


class PermissionDeniedError(ThermosBaseException):
    """Raised when user lacks required permission."""
    def __init__(self, message: str = "Permission denied for this operation"):
        super().__init__(
            message=message,
            code="PERMISSION_DENIED",
            status_code=403
        )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password (PBKDF2-HMAC-SHA256)."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_hash = bytes.fromhex(parts[3])
        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), salt, iterations
        )
        return hmac.compare_digest(expected_hash, calculated_hash)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with random salt."""
    salt = secrets.token_bytes(16)
    iterations = 100_000
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return f"pbkdf2_sha256${iterations}${salt.hex()}${hash_bytes.hex()}"


def create_access_token(
    subject: Union[str, Any],
    role: str = "analyst",
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a signed JWT-compatible token (or payload signature)."""
    import base64
    import json
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
    payload = {
        "sub": str(subject),
        "role": role,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "iss": "thermos-ai"
    }
    
    header = {"alg": "HS256", "typ": "JWT"}
    
    header_b64 = base64.urlsafe_b64encode(
        json.dumps(header).encode("utf-8")
    ).decode("utf-8").rstrip("=")
    
    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(payload).encode("utf-8")
    ).decode("utf-8").rstrip("=")
    
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256
    ).digest()
    
    signature_b64 = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and verify a signed token."""
    import base64
    import json
    
    parts = token.split(".")
    if len(parts) != 3:
        raise AuthenticationError("Invalid token format")
        
    header_b64, payload_b64, signature_b64 = parts
    
    # Verify signature
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256
    ).digest()
    
    # Re-encode expected
    expected_b64 = base64.urlsafe_b64encode(expected_signature).decode("utf-8").rstrip("=")
    if not hmac.compare_digest(expected_b64, signature_b64):
        raise AuthenticationError("Token signature verification failed")
        
    # Pad payload base64
    padded_payload_b64 = payload_b64 + "=" * (-len(payload_b64) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded_payload_b64).decode("utf-8"))
    
    # Check expiration
    if "exp" in payload and datetime.now(timezone.utc).timestamp() > payload["exp"]:
        raise AuthenticationError("Token has expired")
        
    return payload

