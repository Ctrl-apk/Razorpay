"""
webhooks.py — Inbound webhook adapters for external systems.

HOW IT WORKS:
─────────────
1. You configure the webhook URL in your external system's dashboard.
   e.g. Razorpay Dashboard → Settings → Webhooks → add URL:
        https://your-server.com/api/v1/webhooks/razorpay

2. When an event happens (payment fails, error occurs, etc.) that
   external system POSTs a JSON payload to this URL automatically.

3. The adapter here translates that payload into our normalized
   telemetry format (LogEvent / MetricEvent / DeploymentEvent)
   and writes it to the database exactly like any other telemetry.

4. From that point the existing correlation engine + AI investigator
   picks it up automatically — no extra code needed.

ADDING A NEW SOURCE:
────────────────────
Copy the razorpay section, change the payload parsing, done.
The investigation pipeline never needs to change.
"""

import hmac
import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models.telemetry import LogEvent, MetricEvent, DeploymentEvent
from ..config import settings

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


# ─────────────────────────────────────────────────────────────────────────────
# Razorpay webhook
# ─────────────────────────────────────────────────────────────────────────────
# Setup (one-time, in your Razorpay dashboard):
#   1. Go to https://dashboard.razorpay.com → Settings → Webhooks
#   2. Add endpoint:  https://your-server/api/v1/webhooks/razorpay
#   3. Select events: payment.failed, payment.authorized, order.paid, etc.
#   4. Copy the "Webhook Secret" Razorpay gives you
#   5. Set it in your .env:  RAZORPAY_WEBHOOK_SECRET=your_secret_here
#
# That's the entire Razorpay configuration. Everything else is automatic.
# ─────────────────────────────────────────────────────────────────────────────

RAZORPAY_SERVICE_NAME = "razorpay-payments"

# Map Razorpay event names → log severity
RAZORPAY_EVENT_SEVERITY = {
    "payment.failed":        "ERROR",
    "payment.authorized":    "INFO",
    "payment.captured":      "INFO",
    "order.paid":            "INFO",
    "refund.failed":         "ERROR",
    "subscription.halted":   "ERROR",
    "subscription.charged":  "INFO",
    "dispute.created":       "WARN",
    "dispute.won":           "INFO",
    "dispute.lost":          "ERROR",
}


def _verify_razorpay_signature(body: bytes, signature: str, secret: str) -> bool:
    """
    Razorpay signs every webhook with HMAC-SHA256.
    We verify the signature before processing to reject fake requests.
    """
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _parse_razorpay_timestamp(ts) -> datetime:
    """Convert Razorpay Unix timestamp (seconds) to datetime."""
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).replace(tzinfo=None)
    except Exception:
        return datetime.utcnow()


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: Optional[str] = Header(None),
):
    """
    Receives Razorpay webhook events and converts them into telemetry.

    Razorpay sends this automatically when configured in their dashboard.
    No polling, no manual data entry — events flow in as they happen.
    """
    body = await request.body()
    payload = await request.json()

    # ── Signature verification (security) ────────────────────────────────────
    # Skip verification in demo mode so you can test without a real secret.
    # In production, always verify.
    webhook_secret = getattr(settings, "razorpay_webhook_secret", None)
    if webhook_secret and x_razorpay_signature:
        if not _verify_razorpay_signature(body, x_razorpay_signature, webhook_secret):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    event_type = payload.get("event", "unknown")
    entity     = payload.get("payload", {})

    # ── Route by event type ───────────────────────────────────────────────────
    if event_type.startswith("payment."):
        await _handle_payment_event(event_type, entity, db)

    elif event_type.startswith("order."):
        await _handle_order_event(event_type, entity, db)

    elif event_type.startswith("refund."):
        await _handle_refund_event(event_type, entity, db)

    elif event_type.startswith("subscription."):
        await _handle_subscription_event(event_type, entity, db)

    elif event_type.startswith("dispute."):
        await _handle_dispute_event(event_type, entity, db)

    else:
        # Unknown event — log it anyway so the AI can see it
        db.add(LogEvent(
            timestamp  = datetime.utcnow(),
            service    = RAZORPAY_SERVICE_NAME,
            level      = "INFO",
            message    = f"razorpay event received: {event_type}",
        ))
        db.commit()

    return {"status": "accepted", "event": event_type}


async def _handle_payment_event(event: str, entity: dict, db: Session):
    """
    payment.failed       → ERROR log + error_rate metric spike
    payment.authorized   → INFO log  + successful transaction metric
    payment.captured     → INFO log
    """
    payment    = entity.get("payment", {}).get("entity", {})
    ts         = _parse_razorpay_timestamp(payment.get("created_at", 0))
    payment_id = payment.get("id", "unknown")
    amount     = payment.get("amount", 0) / 100  # Razorpay stores paise
    currency   = payment.get("currency", "INR")
    level      = RAZORPAY_EVENT_SEVERITY.get(event, "INFO")

    if event == "payment.failed":
        error_code = payment.get("error_code", "UNKNOWN_ERROR")
        error_desc = payment.get("error_description", "Payment failed")
        error_src  = payment.get("error_source", "unknown")
        error_step = payment.get("error_step", "unknown")

        # Log the failure
        db.add(LogEvent(
            timestamp  = ts,
            service    = RAZORPAY_SERVICE_NAME,
            level      = "ERROR",
            message    = f"payment.failed [{error_code}] {error_desc} "
                         f"(source={error_src}, step={error_step}, "
                         f"id={payment_id}, amount={amount} {currency})",
        ))

        # Emit an error_rate metric — 1.0 = one failed transaction
        db.add(MetricEvent(
            timestamp   = ts,
            service     = RAZORPAY_SERVICE_NAME,
            metric_name = "payment_failure_count",
            value       = 1.0,
            unit        = "count",
            labels      = {"error_code": error_code, "payment_id": payment_id},
        ))

    else:
        db.add(LogEvent(
            timestamp  = ts,
            service    = RAZORPAY_SERVICE_NAME,
            level      = level,
            message    = f"{event} — payment {payment_id} "
                         f"{amount} {currency}",
        ))
        # Track successful payment volume
        db.add(MetricEvent(
            timestamp   = ts,
            service     = RAZORPAY_SERVICE_NAME,
            metric_name = "payment_success_count",
            value       = 1.0,
            unit        = "count",
            labels      = {"payment_id": payment_id},
        ))

    db.commit()


async def _handle_order_event(event: str, entity: dict, db: Session):
    order    = entity.get("order", {}).get("entity", {})
    ts       = _parse_razorpay_timestamp(order.get("created_at", 0))
    order_id = order.get("id", "unknown")
    amount   = order.get("amount", 0) / 100
    currency = order.get("currency", "INR")
    level    = RAZORPAY_EVENT_SEVERITY.get(event, "INFO")

    db.add(LogEvent(
        timestamp = ts,
        service   = RAZORPAY_SERVICE_NAME,
        level     = level,
        message   = f"{event} — order {order_id} {amount} {currency}",
    ))
    db.commit()


async def _handle_refund_event(event: str, entity: dict, db: Session):
    refund    = entity.get("refund", {}).get("entity", {})
    ts        = _parse_razorpay_timestamp(refund.get("created_at", 0))
    refund_id = refund.get("id", "unknown")
    amount    = refund.get("amount", 0) / 100
    level     = RAZORPAY_EVENT_SEVERITY.get(event, "INFO")

    db.add(LogEvent(
        timestamp = ts,
        service   = RAZORPAY_SERVICE_NAME,
        level     = level,
        message   = f"{event} — refund {refund_id} amount={amount} INR",
    ))
    db.commit()


async def _handle_subscription_event(event: str, entity: dict, db: Session):
    sub    = entity.get("subscription", {}).get("entity", {})
    ts     = _parse_razorpay_timestamp(sub.get("created_at", 0))
    sub_id = sub.get("id", "unknown")
    level  = RAZORPAY_EVENT_SEVERITY.get(event, "INFO")

    db.add(LogEvent(
        timestamp = ts,
        service   = RAZORPAY_SERVICE_NAME,
        level     = level,
        message   = f"{event} — subscription {sub_id}",
    ))
    db.commit()


async def _handle_dispute_event(event: str, entity: dict, db: Session):
    dispute    = entity.get("dispute", {}).get("entity", {})
    ts         = _parse_razorpay_timestamp(dispute.get("created_at", 0))
    dispute_id = dispute.get("id", "unknown")
    amount     = dispute.get("amount", 0) / 100
    level      = RAZORPAY_EVENT_SEVERITY.get(event, "INFO")

    db.add(LogEvent(
        timestamp = ts,
        service   = RAZORPAY_SERVICE_NAME,
        level     = level,
        message   = f"{event} — dispute {dispute_id} amount={amount} INR",
    ))
    db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# GitHub Deployments webhook
# ─────────────────────────────────────────────────────────────────────────────
# Setup (one-time, in your GitHub repo):
#   1. Go to repo → Settings → Webhooks → Add webhook
#   2. Payload URL:  https://your-server/api/v1/webhooks/github
#   3. Content type: application/json
#   4. Events: Deployments, Deployment statuses
#   5. That's it.
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/github")
async def github_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_github_event: Optional[str] = Header(None),
):
    """
    Receives GitHub deployment webhooks and converts them to DeploymentEvents.
    Automatically correlates with incidents in the same time window.
    """
    payload = await request.json()
    event   = x_github_event or "unknown"

    if event == "deployment":
        dep        = payload.get("deployment", {})
        repo       = payload.get("repository", {})
        service    = repo.get("name", "unknown-service")
        version    = dep.get("ref", "unknown")        # branch / tag / SHA
        sha        = dep.get("sha", "")[:12]
        author     = dep.get("creator", {}).get("login", "unknown")
        env        = dep.get("environment", "production")
        ts_str     = dep.get("created_at", datetime.utcnow().isoformat())
        ts         = datetime.fromisoformat(ts_str.replace("Z", ""))

        db.add(DeploymentEvent(
            timestamp   = ts,
            service     = service,
            version     = version,
            commit_sha  = sha,
            author      = author,
            environment = env,
            status      = "success",
        ))
        db.commit()
        return {"status": "accepted", "event": "deployment", "service": service}

    elif event == "deployment_status":
        status_obj = payload.get("deployment_status", {})
        dep        = payload.get("deployment", {})
        repo       = payload.get("repository", {})
        service    = repo.get("name", "unknown-service")
        state      = status_obj.get("state", "unknown")   # success/failure/error
        ts_str     = status_obj.get("created_at", datetime.utcnow().isoformat())
        ts         = datetime.fromisoformat(ts_str.replace("Z", ""))

        level = "ERROR" if state in ("failure", "error") else "INFO"
        db.add(LogEvent(
            timestamp = ts,
            service   = service,
            level     = level,
            message   = f"deployment {state} — ref={dep.get('ref', '?')} env={dep.get('environment', '?')}",
        ))
        db.commit()

    return {"status": "accepted", "event": event}


# ─────────────────────────────────────────────────────────────────────────────
# Generic webhook — for any system that can POST JSON
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/generic")
async def generic_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Accepts any JSON payload as a log event.
    Useful for custom alerting systems, Grafana alerts, PagerDuty, etc.

    Required fields in payload:
      service   — string
      message   — string
      level     — ERROR | WARN | INFO (optional, defaults to INFO)
      timestamp — ISO8601 (optional, defaults to now)
    """
    payload  = await request.json()
    service  = payload.get("service", "unknown")
    message  = payload.get("message", str(payload))
    level    = payload.get("level", "INFO").upper()
    ts_raw   = payload.get("timestamp")
    ts       = datetime.fromisoformat(ts_raw) if ts_raw else datetime.utcnow()

    db.add(LogEvent(
        timestamp = ts,
        service   = service,
        level     = level,
        message   = message,
    ))
    db.commit()
    return {"status": "accepted", "service": service}
