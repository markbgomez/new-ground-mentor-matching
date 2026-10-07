"""
HMAC Token Utility for Secure Single-Use Response Links
"""
import hmac
import hashlib
import base64
import json
import time

SECRET_KEY = "new-ground-demo-link-signing-key-32bytes"

def generate_signed_token(payload: dict, expires_in_seconds: int = 86400 * 7) -> str:
    """Generates a base64url-encoded signed token."""
    payload_copy = payload.copy()
    payload_copy["exp"] = int(time.time()) + expires_in_seconds
    data_str = json.dumps(payload_copy, sort_keys=True)
    sig = hmac.new(SECRET_KEY.encode(), data_str.encode(), hashlib.sha256).hexdigest()
    combined = {"data": payload_copy, "sig": sig}
    return base64.urlsafe_b64encode(json.dumps(combined).encode()).decode()

def verify_signed_token(token_str: str) -> dict:
    """Verifies token signature and expiration. Returns payload or raises ValueError."""
    try:
        raw = base64.urlsafe_b64decode(token_str.encode()).decode()
        combined = json.loads(raw)
        data = combined["data"]
        sig = combined["sig"]

        expected_sig = hmac.new(SECRET_KEY.encode(), json.dumps(data, sort_keys=True).encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            raise ValueError("Invalid signature (tampered token)")

        if int(time.time()) > data.get("exp", 0):
            raise ValueError("Token has expired")

        return data
    except Exception as e:
        raise ValueError(f"Token validation failed: {str(e)}")
