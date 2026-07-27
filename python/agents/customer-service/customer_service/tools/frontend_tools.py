# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Frontend action tools for the ENIE assistant.

These tools do not write to a database. They return deterministic action
payloads that a web frontend can render and persist through its own API layer.
"""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def _action(action_type: str, payload: dict[str, Any], requires_confirmation: bool = False) -> dict:
    return {
        "status": "frontend_action",
        "action_id": str(uuid4()),
        "action_type": action_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "requires_confirmation": requires_confirmation,
        "payload": payload,
    }


def display_customer_profile(customer: dict) -> dict:
    """Ask the frontend to display a customer profile panel."""

    return _action("display_customer_profile", {"customer": customer})


def display_consultation_summary(
    customer_id: str,
    customer_goal: str,
    hair_condition: list[str],
    chemical_history: list[str],
    scalp_condition: str,
    allergy_or_irritation_history: str,
    recommendations: list[str],
    safety_notes: list[str],
) -> dict:
    """Ask the frontend to render a consultation summary before saving."""

    return _action(
        "display_consultation_summary",
        {
            "customer_id": customer_id,
            "customer_goal": customer_goal,
            "hair_condition": hair_condition,
            "chemical_history": chemical_history,
            "scalp_condition": scalp_condition,
            "allergy_or_irritation_history": allergy_or_irritation_history,
            "recommendations": recommendations,
            "safety_notes": safety_notes,
        },
        requires_confirmation=True,
    )


def save_consultation_via_frontend(consultation: dict, customer_confirmed: bool) -> dict:
    """Ask the frontend to persist a confirmed consultation through its API."""

    if not customer_confirmed:
        return {"status": "confirmation_required"}
    return _action("save_consultation", {"consultation": consultation})


def display_product_cards(products: list[dict], title: str = "สินค้าแนะนำ") -> dict:
    """Ask the frontend to render structured product cards."""

    return _action("display_product_cards", {"title": title, "products": products})


def display_cart(cart: dict) -> dict:
    """Ask the frontend to render the current cart."""

    return _action("display_cart", {"cart": cart})


def update_cart_via_frontend(
    customer_id: str,
    items_to_add: list[dict],
    items_to_remove: list[dict],
    customer_confirmed: bool,
) -> dict:
    """Ask the frontend to persist a confirmed cart change."""

    if not customer_confirmed:
        return {"status": "confirmation_required"}
    return _action(
        "update_cart",
        {
            "customer_id": customer_id,
            "items_to_add": items_to_add,
            "items_to_remove": items_to_remove,
        },
    )


def display_order_summary(order_summary: dict) -> dict:
    """Ask the frontend to show an order-review screen."""

    return _action(
        "display_order_summary",
        {"order_summary": order_summary},
        requires_confirmation=True,
    )


def create_order_via_frontend(order: dict, customer_confirmed: bool) -> dict:
    """Ask the frontend to create an order through its backend API."""

    if not customer_confirmed:
        return {"status": "confirmation_required"}
    return _action("create_order", {"order": order})


def display_payment_status(order_id: str, payment_status: str, reference: str = "") -> dict:
    """Ask the frontend to display payment status."""

    return _action(
        "display_payment_status",
        {
            "order_id": order_id,
            "payment_status": payment_status,
            "reference": reference,
        },
    )


def schedule_follow_up_via_frontend(
    customer_id: str,
    order_id: str,
    follow_up_at: str,
    purpose: str,
    channel: str,
    customer_consented: bool,
) -> dict:
    """Ask the frontend to save a follow-up after customer consent."""

    if not customer_consented:
        return {"status": "consent_required"}
    return _action(
        "schedule_follow_up",
        {
            "customer_id": customer_id,
            "order_id": order_id,
            "follow_up_at": follow_up_at,
            "purpose": purpose,
            "channel": channel,
        },
    )


def display_sales_dashboard(report: dict) -> dict:
    """Ask the frontend to render sales and service metrics."""

    return _action("display_sales_dashboard", {"report": report})


def request_human_handoff(
    customer_id: str,
    reason: str,
    conversation_summary: str,
    priority: str = "normal",
) -> dict:
    """Ask the frontend to create a human support ticket."""

    return _action(
        "request_human_handoff",
        {
            "customer_id": customer_id,
            "reason": reason,
            "conversation_summary": conversation_summary,
            "priority": priority,
        },
    )
