from fastapi import Request, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.security import verify_webhook_signature, verify_api_key


async def get_raw_body(request: Request) -> bytes:
    """
    Extracts raw unparsed bytes directly from the request stream.
    Critically, this preserves exact whitespace and byte sequence for HMAC verification.
    """
    return await request.body()


async def verify_signature_header(
    request: Request,
    raw_body: bytes = Depends(get_raw_body),
    x_signature: str | None = Header(None, alias="X-Signature")
) -> bytes:
    """
    Validates HMAC-SHA256 signature against original request bytes.
    Rejects missing or invalid signatures with HTTP 401.
    """
    verify_webhook_signature(raw_body, x_signature)
    return raw_body


def authenticate_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    authorization: str | None = Header(None, alias="Authorization")
) -> bool:
    """
    Authenticates administrative/usage API calls.
    Supports either X-API-Key header or Authorization: Bearer <token>.
    """
    token = x_api_key or authorization
    return verify_api_key(token)
