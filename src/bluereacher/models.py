"""Typed response shapes for the Blue Reacher API.

These mirror the public OpenAPI spec (version 2026-08-27). They are
``TypedDict``s: the client returns plain dicts that structurally match them,
so type checkers give you field completion without any runtime cost.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict

SendMode = Literal["drip", "instant"]
CapabilityStatus = Literal["imessage", "sms", "unknown", "pending"]


class SendMessageResult(TypedDict, total=False):
    success: bool
    message_id: str
    mode: SendMode
    queued: bool
    scheduled_for: Optional[str]
    estimated_send_time: Optional[str]
    queue_position: int
    status: str
    device_id: Optional[str]


class MessageStatus(TypedDict, total=False):
    success: bool
    message_id: str
    type: Literal["drip_queue", "message", "voice_memo"]
    status: str
    scheduled_for: Optional[str]
    sent_at: Optional[str]
    device_name: Optional[str]
    error: Optional[str]


class Contact(TypedDict, total=False):
    id: str
    phone_number: str
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    company: Optional[str]
    tags: Optional[List[str]]
    custom_fields: Optional[Dict[str, Any]]
    is_imessage: Optional[bool]
    opted_out: Optional[bool]
    last_contacted_at: Optional[str]
    last_message_received_at: Optional[str]
    created_at: str
    updated_at: str


class ContactList(TypedDict, total=False):
    contacts: List[Contact]
    page: int
    per_page: int
    total: int
    has_more: bool


class ConversationMessage(TypedDict, total=False):
    id: str
    direction: Literal["inbound", "outbound"]
    message: Optional[str]
    type: Literal["text", "media", "voice_memo"]
    sent_at: str
    device_name: Optional[str]
    status: str
    delivery_channel: Optional[Literal["imessage", "sms"]]
    reactions: List[Dict[str, Any]]
    ai_generated: bool


class Conversation(TypedDict, total=False):
    success: bool
    phone: str
    group_chat_id: str
    group: Dict[str, Any]
    messages: List[ConversationMessage]
    has_more: bool
    next_cursor: Optional[str]


class OptOutState(TypedDict, total=False):
    success: bool
    phone: str
    opted_out: bool
    opted_out_at: Optional[str]
    known_contact: bool


class SetOptOutResult(TypedDict, total=False):
    success: bool
    phone: str
    opted_out: bool
    already_opted_out: bool
    resubscribed: bool


class CapabilityResult(TypedDict, total=False):
    phone: str
    status: CapabilityStatus
    confidence: Optional[str]
    last_checked: Optional[str]
    probe_queued: bool


class CapabilityResponse(TypedDict, total=False):
    results: List[CapabilityResult]
    probes_enabled: bool
    probes_queued: int


class WebhookRegistration(TypedDict, total=False):
    registered: bool
    url: str
    events: str
    secret: str
