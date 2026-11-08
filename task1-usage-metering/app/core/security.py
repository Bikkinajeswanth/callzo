import hmac
import hashlib
from fastapi import HTTPException, status
from app.core.config import settings
from app.core.logging import logger


def compute_signature(payload_bytes: bytes, secret: str) -> str:
    """
    Computes HMAC-SHA256 hex digest of raw request payload bytes.
    """
    return hmac.new(
        secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()


def verify_webhook_signature(payload_bytes: bytes, signature_header: str | None, secret: str = settings.WEBHOOK_SECRET) -> bool:
    """
    Verifies that the provided X-Signature header matches the HMAC-SHA256 of the raw body bytes.
    Uses hmac.compare_digest to prevent timing attacks.
    """
    if not signature_header:
        logger.warning("Webhook rejected: Missing X-Signature header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing signature header"
        )

    computed = compute_signature(payload_bytes, secret)

    # Constant time comparison to prevent timing attacks
    if not hmac.compare_digest(computed, signature_header.strip()):
        logger.warning("Webhook rejected: Invalid signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )

    return True


def verify_api_key(api_key_header: str | None) -> bool:
    """
    Validates API key for internal administrative/usage endpoints.
    """
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key header (X-API-Key or Authorization Bearer)"
        )

    # Remove Bearer prefix if supplied
    cleaned_key = api_key_header
    if cleaned_key.lower().startswith("bearer "):
        cleaned_key = cleaned_key[7:].strip()

    if not hmac.compare_digest(cleaned_key, settings.API_KEY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )

    return True
