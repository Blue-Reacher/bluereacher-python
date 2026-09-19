# bluereacher-python

Official Python client for the [Blue Reacher](https://bluereacher.com) API. Send iMessage from your CRM, app, or AI agent over a dedicated line, read replies, manage contacts, and verify webhooks.

- Typed with `TypedDict` response shapes and full type hints
- Built on `httpx`, one dependency
- Python 3.8+
- No A2P registration required

Docs: https://docs.bluereacher.com  
OpenAPI: https://docs.bluereacher.com/openapi.json

## Install

```bash
pip install bluereacher
```

## Quickstart

```python
import os
from bluereacher import BlueReacher

br = BlueReacher(os.environ["BLUEREACHER_API_KEY"])
# Test keys (brk_test_) hit a simulator: no message is ever sent.

res = br.send_message(to="+13035550101", message="Hey, following up on your quote.")
print(res["message_id"], res["mode"])

status = br.get_status(res["message_id"])
print(status["status"])
```

Every example here uses the placeholder key `brk_test_your_key`. Keep live keys (`brk_live_`) in environment variables, never in source.

Use it as a context manager to close the underlying HTTP connection pool:

```python
with BlueReacher(os.environ["BLUEREACHER_API_KEY"]) as br:
    br.send_message(to="+13035550101", message="Reminder for tomorrow.")
```

## Sending

By default a send is queued through the paced drip pipeline. Pass `send_mode="instant"` to dispatch now.

```python
# Instant, with a native effect
br.send_message(
    to="+13035550101",
    message="You are confirmed",
    send_mode="instant",
    message_effect="confetti",
)

# Media
br.send_message(
    to="+13035550101",
    message="Your receipt",
    media_urls=["https://example.com/receipt.pdf"],
)
```

## Contacts and opt-out

```python
br.upsert_contact(phone_number="+13035550101", first_name="Jordan", tags=["lead"])

state = br.get_opt_out("+13035550101")
if not state["opted_out"]:
    br.send_message(to="+13035550101", message="...")

# Honor an opt-out
br.set_opt_out(phone="+13035550101", opted_out=True)
```

## Capability check

```python
cap = br.check_capability(["+13035550101", "+13035550102"])
for r in cap["results"]:
    print(r["phone"], r["status"])  # "imessage" | "sms" | "unknown" | "pending"
```

## Webhooks

Register your endpoint, store the signing secret, and verify every delivery. Each request carries an `X-BlueReacher-Signature` header of the form `sha256=HMAC-SHA256(secret, raw_body)`.

```python
from bluereacher import verify_webhook_signature, construct_event

reg = br.register_webhook("https://example.com/hooks/bluereacher")
secret = reg["secret"]  # store this

# In your handler, pass the EXACT raw body bytes (not a re-serialized dict):
if not verify_webhook_signature(raw_body, signature_header, secret):
    ...  # reject with 400

event = construct_event(raw_body, signature_header, secret)
print(event["event"], event["data"])
```

Flask example:

```python
from flask import Flask, request, abort
from bluereacher import construct_event

app = Flask(__name__)

@app.post("/hooks/bluereacher")
def hook():
    try:
        event = construct_event(
            request.get_data(),  # raw bytes
            request.headers.get("X-BlueReacher-Signature"),
            os.environ["BLUEREACHER_WEBHOOK_SECRET"],
        )
    except ValueError:
        abort(400)
    # handle event["event"] ...
    return "", 200
```

## Error handling

Non-2xx responses raise `BlueReacherError` with `status`, `code`, and `help`.

```python
from bluereacher import BlueReacherError

try:
    br.send_message(to="+13035550101", message="Hi")
except BlueReacherError as err:
    print(err.status, err.code, err)
```

## API surface

| Method | Endpoint |
| --- | --- |
| `send_message(...)` | `POST /v1/messages` |
| `get_status(message_id)` | `GET /v1/status/{message_id}` |
| `get_conversation(...)` | `GET /v1/conversations` |
| `get_contact_messages(contact_id, ...)` | `GET /v1/conversations/{contact_id}/messages` |
| `list_contacts(...)` | `GET /v1/contacts` |
| `upsert_contact(...)` | `POST /v1/contacts` |
| `update_contact(contact_id, ...)` | `PATCH /v1/contacts/{contact_id}` |
| `get_opt_out(phone)` | `GET /v1/opt-out` |
| `set_opt_out(...)` | `POST /v1/opt-out` |
| `check_capability(phones)` | `POST /v1/capability` |
| `get_usage()` | `GET /v1/usage` |
| `list_lines()` | `GET /v1/devices` |
| `register_webhook(url, events)` | `POST /v1/webhooks` |
| `get_webhook()` | `GET /v1/webhooks` |
| `delete_webhook()` | `DELETE /v1/webhooks` |

## Development

```bash
pip install -e .
python -c "import bluereacher; print(bluereacher.__version__)"
```

## License

MIT. Copyright 2026 Sagency International LLC (Blue Reacher).
