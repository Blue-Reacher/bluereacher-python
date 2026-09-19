"""Synchronous client for the Blue Reacher API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from .errors import BlueReacherError
from .models import (
    CapabilityResponse,
    Contact,
    ContactList,
    Conversation,
    MessageStatus,
    OptOutState,
    SendMessageResult,
    SetOptOutResult,
    WebhookRegistration,
)

DEFAULT_BASE_URL = "https://api.bluereacher.com/v1"


def _clean(data: Dict[str, Any]) -> Dict[str, Any]:
    """Drop None values so they are never serialized."""
    return {k: v for k, v in data.items() if v is not None}


class BlueReacher:
    """Client for the Blue Reacher API.

    Send iMessage from your CRM, app, or agent over a dedicated line.
    See https://docs.bluereacher.com for the full API.

    Example:
        >>> br = BlueReacher("brk_test_your_key")
        >>> res = br.send_message(to="+13035550101", message="Hi")
        >>> br.get_status(res["message_id"])["status"]

    Test keys (``brk_test_``) hit a simulator: no message is ever sent.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        client: Optional[httpx.Client] = None,
    ) -> None:
        if not api_key:
            raise ValueError(
                "A Blue Reacher API key is required (brk_live_ or brk_test_)."
            )
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._owns_client = client is None
        self._http = client or httpx.Client(timeout=timeout)

    # -- lifecycle ---------------------------------------------------------

    def close(self) -> None:
        if self._owns_client:
            self._http.close()

    def __enter__(self) -> "BlueReacher":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    # -- transport ---------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        request_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": "bluereacher-python",
        }
        if headers:
            request_headers.update(headers)

        try:
            response = self._http.request(
                method,
                self.base_url + path,
                params=_clean(params) if params else None,
                json=json,
                headers=request_headers,
            )
        except httpx.TimeoutException as exc:
            raise BlueReacherError(f"Request to {path} timed out", 0) from exc
        except httpx.HTTPError as exc:
            raise BlueReacherError(
                f"Network error calling {path}: {exc}", 0
            ) from exc

        body: Any = None
        if response.content:
            try:
                body = response.json()
            except ValueError:
                body = response.text

        if response.status_code >= 400:
            data = body if isinstance(body, dict) else {}
            raise BlueReacherError(
                data.get("error") or f"Request failed with status {response.status_code}",
                response.status_code,
                code=data.get("error_code"),
                help=data.get("help"),
                body=body,
            )
        return body

    # -- messages ----------------------------------------------------------

    def send_message(
        self,
        *,
        to: Optional[str] = None,
        message: Optional[str] = None,
        group_chat_id: Optional[str] = None,
        create_group_phones: Optional[List[str]] = None,
        media_urls: Optional[List[str]] = None,
        send_mode: Optional[str] = None,
        message_effect: Optional[str] = None,
        device_id: Optional[str] = None,
        delay_minutes: Optional[int] = None,
        idempotency_key: Optional[str] = None,
    ) -> SendMessageResult:
        """Send a text and/or media iMessage. Drip-paced by default, or instant.

        Pass exactly one of ``to``, ``group_chat_id``, or ``create_group_phones``.
        """
        payload = _clean(
            {
                "to": to,
                "message": message,
                "group_chat_id": group_chat_id,
                "create_group_phones": create_group_phones,
                "media_urls": media_urls,
                "send_mode": send_mode,
                "message_effect": message_effect,
                "device_id": device_id,
                "delay_minutes": delay_minutes,
            }
        )
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self._request("POST", "/messages", json=payload, headers=headers)

    def get_status(self, message_id: str) -> MessageStatus:
        """Delivery status of a queued or sent item."""
        return self._request("GET", f"/status/{message_id}")

    # -- conversations -----------------------------------------------------

    def get_conversation(
        self,
        *,
        phone: Optional[str] = None,
        group_chat_id: Optional[str] = None,
        limit: Optional[int] = None,
        before: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> Conversation:
        """Conversation history for a phone number or group chat."""
        return self._request(
            "GET",
            "/conversations",
            params={
                "phone": phone,
                "group_chat_id": group_chat_id,
                "limit": limit,
                "before": before,
                "device_id": device_id,
            },
        )

    def get_contact_messages(
        self,
        contact_id: str,
        *,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
    ) -> Conversation:
        """Paginated message history for a known contact."""
        return self._request(
            "GET",
            f"/conversations/{contact_id}/messages",
            params={"page": page, "per_page": per_page, "before": before, "after": after},
        )

    # -- contacts ----------------------------------------------------------

    def list_contacts(
        self,
        *,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        tag: Optional[str] = None,
        created_after: Optional[str] = None,
        search: Optional[str] = None,
    ) -> ContactList:
        """Search and list contacts."""
        return self._request(
            "GET",
            "/contacts",
            params={
                "page": page,
                "per_page": per_page,
                "phone": phone,
                "email": email,
                "tag": tag,
                "created_after": created_after,
                "search": search,
            },
        )

    def upsert_contact(
        self,
        *,
        phone_number: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        company: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Contact]:
        """Create or update a contact, keyed by phone number."""
        payload = _clean(
            {
                "phone_number": phone_number,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "company": company,
                "tags": tags,
                "notes": notes,
                "custom_fields": custom_fields,
            }
        )
        return self._request("POST", "/contacts", json=payload)

    def update_contact(
        self,
        contact_id: str,
        *,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        company: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
        opted_out: Optional[bool] = None,
    ) -> Dict[str, Contact]:
        """Update an existing contact by id, including opt-out state."""
        payload = _clean(
            {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "company": company,
                "tags": tags,
                "notes": notes,
                "custom_fields": custom_fields,
                "opted_out": opted_out,
            }
        )
        return self._request("PATCH", f"/contacts/{contact_id}", json=payload)

    # -- opt-out -----------------------------------------------------------

    def get_opt_out(self, phone: str) -> OptOutState:
        """Read a contact's opt-out state by phone."""
        return self._request("GET", "/opt-out", params={"phone": phone})

    def set_opt_out(
        self, *, phone: str, opted_out: bool, confirm_resubscribe: bool = False
    ) -> SetOptOutResult:
        """Opt a contact out, or opt them back in.

        Re-subscribing (``opted_out=False``) requires ``confirm_resubscribe=True``.
        """
        payload: Dict[str, Any] = {"phone": phone, "opted_out": opted_out}
        if not opted_out:
            payload["confirm_resubscribe"] = confirm_resubscribe
        return self._request("POST", "/opt-out", json=payload)

    # -- capability --------------------------------------------------------

    def check_capability(
        self, phones: List[str], *, probe: bool = True
    ) -> CapabilityResponse:
        """Check iMessage vs SMS capability for up to 100 phone numbers."""
        return self._request(
            "POST", "/capability", json={"phones": phones, "probe": probe}
        )

    # -- usage & lines -----------------------------------------------------

    def get_usage(self) -> Dict[str, Any]:
        """Usage by key and endpoint."""
        return self._request("GET", "/usage")

    def list_lines(self) -> Dict[str, Any]:
        """List sending lines and their live capacity."""
        return self._request("GET", "/devices")

    # -- webhooks ----------------------------------------------------------

    def register_webhook(
        self, url: str, events: Optional[str] = None
    ) -> WebhookRegistration:
        """Register your inbound webhook endpoint.

        Returns a signing secret once; store it and verify each delivery with
        ``verify_webhook_signature``.
        """
        return self._request("POST", "/webhooks", json=_clean({"url": url, "events": events}))

    def get_webhook(self) -> Dict[str, Any]:
        """Read your current webhook registration."""
        return self._request("GET", "/webhooks")

    def delete_webhook(self) -> Dict[str, Any]:
        """Remove your webhook endpoint."""
        return self._request("DELETE", "/webhooks")
