"""Mock backend tools the specialist agents call into.

In a real deployment these would hit a database / order-management API /
payments gateway. Here they read local JSON so the whole project runs
end-to-end with zero external services.
"""

import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load(filename: str):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_orders() -> dict:
    """Demo orders store their dates relative to today, so the refund
    window examples behave the same whenever someone runs this."""
    today = date.today()
    orders = {}
    for order_id, raw in _load("orders.json").items():
        order = dict(raw)
        placed = today - timedelta(days=order.pop("ordered_days_ago"))
        order["order_date"] = placed.isoformat()
        order["delivery_estimate"] = (placed + timedelta(days=order.pop("delivery_days"))).isoformat()
        orders[order_id] = order
    return orders


def get_order_status(order_id: str) -> dict:
    """Look up an order by ID and return its current status."""
    orders = _load_orders()
    order_id = order_id.strip().upper()
    if order_id not in orders:
        return {"found": False, "order_id": order_id}
    order = orders[order_id]
    return {"found": True, "order_id": order_id, **order}


def process_refund(order_id: str, reason: str = "") -> dict:
    """Evaluate and (mock) process a refund request for an order."""
    orders = _load_orders()
    order_id = order_id.strip().upper()
    if order_id not in orders:
        return {"approved": False, "reason": "order_not_found", "order_id": order_id}

    order = orders[order_id]
    order_date = datetime.strptime(order["order_date"], "%Y-%m-%d").date()
    days_since_order = (date.today() - order_date).days

    if order["status"] not in ("Delivered", "Shipped"):
        return {
            "approved": False,
            "reason": "order_not_yet_delivered",
            "order_id": order_id,
            "status": order["status"],
        }

    if days_since_order > 30:
        return {
            "approved": False,
            "reason": "outside_30_day_window",
            "order_id": order_id,
            "days_since_order": days_since_order,
        }

    ticket_id = f"RF-{random.randint(10000, 99999)}"
    return {
        "approved": True,
        "order_id": order_id,
        "amount": order["amount"],
        "refund_ticket": ticket_id,
        "customer_reason": reason,
    }


def search_faq(query: str) -> dict:
    """Very simple keyword-overlap search over the FAQ knowledge base."""
    faqs = _load("faq.json")
    query_lower = query.lower()

    best_match = None
    best_score = 0
    for entry in faqs:
        score = sum(1 for kw in entry["keywords"] if kw in query_lower)
        if score > best_score:
            best_score = score
            best_match = entry

    if best_match is None or best_score == 0:
        return {"found": False}

    return {"found": True, "question": best_match["question"], "answer": best_match["answer"]}


def create_support_ticket(summary: str) -> dict:
    """Escalate to a human agent by opening a support ticket."""
    ticket_id = f"TCK-{random.randint(10000, 99999)}"
    return {"ticket_id": ticket_id, "summary": summary}
