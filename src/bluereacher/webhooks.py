"""Verify signed Blue Reacher webhook deliveries."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any, Dict, Optional, Union

Body = Union[str, bytes]


def verify_webhook_signature(
    raw_body: Body, signature: Optional[str], secret: str
) -> bool:
    """Verify a webhook delivery.

    Each delivery carries an ``X-BlueReacher-Signature`` header of the form
    ``sha256=HMAC-SHA256(secret, raw_body)``. Compute the same HMAC over the
    exact raw request body and compare in constant time.

    Args:
        raw_body: The exact raw request body (str or bytes). Do not parse and
            re-serialize it first; the bytes must match.
        signature: The value of the ``X-BlueReacher-Signature`` header.
        secret: The signing secret returned once by ``register_webhook``.

    Returns:
        True when the signature is valid.
    """
    if not signature or not secret:
        return False

    body_bytes = raw_body.encode("utf-8") if isinstance(raw_body, str) else raw_body
    expected = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
    provided = signature[len("sha256=") :] if signature.startswith("sha256=") else signature
    return hmac.compare_digest(expected, provided)


def construct_event(
    raw_body: Body, signature: Optional[str], secret: str
) -> Dict[str, Any]:
    """Verify a delivery and return the parsed event.

    Raises ``ValueError`` if the signature is invalid, so a handler can never
    act on an unverified payload.
    """
    if not verify_webhook_signature(raw_body, signature, secret):
        raise ValueError("Invalid Blue Reacher webhook signature")
    text = raw_body.decode("utf-8") if isinstance(raw_body, bytes) else raw_body
    return json.loads(text)
