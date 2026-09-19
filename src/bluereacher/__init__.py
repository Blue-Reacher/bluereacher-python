"""Blue Reacher Python client.

Send iMessage from your CRM, app, or AI agent over a dedicated line.
See https://docs.bluereacher.com for the full API.
"""

from __future__ import annotations

from .client import BlueReacher
from .errors import BlueReacherError
from .webhooks import construct_event, verify_webhook_signature

__version__ = "0.1.0"

__all__ = [
    "BlueReacher",
    "BlueReacherError",
    "verify_webhook_signature",
    "construct_event",
    "__version__",
]
