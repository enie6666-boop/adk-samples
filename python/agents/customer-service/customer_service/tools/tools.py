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

"""Prototype business tools for the ENIE hair consultation and sales agent.

The in-memory stores in this module are for local development only. Replace them
with authenticated catalog, CRM, inventory, order and messaging integrations
before production deployment.
"""

import logging
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

MAX_DISCOUNT_RATE = 10.0
MAX_FIXED_DISCOUNT_THB = 200.0

_PRODUCT_CATALOG: dict[str, dict] = {
    "smart-lotion-a1": {
        "product_id": "smart-lotion-a1",
        "name": "SMART LOTION A-1",
        "category": "professional_hair_service",
        "concerns": ["ดัดผม", "ผมธรรมชาติ", "ผมแข็งแรง"],
        "description": "ข้อมูลตัวอย่างสำหรับทดสอบระบบ โปรดเชื่อมฐานข้อมูลสินค้า ENIE จริงก่อนใช้งานขาย",
        "price": 0.0,
        "currency": "THB",
        "stock": 0,
        "usage": "ตรวจสอบฉลากและคู่มือผลิตภัณฑ์ฉบับจริงก่อนใช้งาน",
        "warnings": ["ทดสอบการแพ้และทดสอบปอยผมตามคู่มือผลิตภัณฑ์"],
        "source_status": "placeholder",
    },
    "smart-lotion-a2": {
        "product_id": "smart-lotion-a2",
        "name": "SMART LOTION A-2",
        "category": "professional_hair_service",
        "concerns": ["ดัดผม", "ผมผ่านเคมี", "ผมไวต่อสารเคมี"],
        "description": "ข้อมูลตัวอย่างสำหรับทดสอบระบบ โปรดเชื่อมฐานข้อมูลสินค้า ENIE จริงก่อนใช้งานขาย",
        "price": 0.0,
        "currency": "THB",
        "stock": 0,
        "usage": "ตรวจสอบฉลากและคู่มือผลิตภัณฑ์ฉบับจริงก่อนใช้งาน",
        "warnings": ["ทดสอบการแพ้และทดสอบปอยผมตามคู่มือผลิตภัณฑ์"],
        "source_status": "placeholder",
    },
}

_CARTS: dict[str, list[dict]] = {}
_ORDERS: dict[str, dict] = {}
_CRM_NOTES: dict[str, list[dict]] = {}
_HAIR_PROFILES: dict[str, dict] = {}
_FOLLOW_UPS: dict[str, dict] = {}
_HUMAN_HANDOFFS: dict[str, dict] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_customer_profile(customer_id: str) -> dict:
    """Return the saved prototype hair profile for a customer."""

    return {
        "status": "success",
        "customer_id": customer_id,
        "hair_profile": _HAIR_PROFILES.get(customer_id, {}),
        "crm_notes": _CRM_NOTES.get(customer_id, []),
    }


def save_hair_consultation(
    customer_id: str,
    customer_goal: str,
    hair_condition: list[str],
    chemical_history: list[str],
    scalp_condition: str,
    allergy_or_irritation_history: str,
    recommendations: list[str],
    safety_notes: list[str],
    channel: str = "unknown",
) -> dict:
    """Save structured consultation information after customer consent."""

    consultation_id = str(uuid.uuid4())
    record = {
        "consultation_id": consultation_id,
        "created_at": _now_iso(),
        "channel": channel,
        "customer_goal": customer_goal,
        "hair_condition": hair_condition,
        "chemical_history": chemical_history,
        "scalp_condition": scalp_condition,
        "allergy_or_irritation_history": allergy_or_irritation_history,
        "recommendations": recommendations,
        "safety_notes": safety_notes,
    }
    _HAIR_PROFILES[customer_id] = {
        "current_goal": customer_goal,
        "current_condition": hair_condition,
        "chemical_history": chemical_history,
        "scalp_condition": scalp_condition,
        "allergy_or_irritation_history": allergy_or_irritation_history,
        "last_updated_at": record["created_at"],
    }
    _CRM_NOTES.setdefault(customer_id, []).append(record)
    return {"status": "success", "consultation": record}


def search_hair_products(
    concern: str,
    chemical_history: str = "",
    professional_use_only: bool = False,
) -> dict:
    """Search the prototype catalog without inventing price or stock."""

    query = f"{concern} {chemical_history}".lower()
    matches = []
    for product in _PRODUCT_CATALOG.values():
        haystack = " ".join(
            [product["name"], product["category"], *product["concerns"]]
        ).lower()
        if any(token in haystack for token in query.split()):
            matches.append(product.copy())

    if professional_use_only:
        matches = [p for p in matches if p["category"] == "professional_hair_service"]

    return {
        "status": "success",
        "query": concern,
        "recommendations": matches[:3],
        "notice": "ราคาและสต็อกที่เป็นศูนย์หมายถึงยังไม่ได้เชื่อมข้อมูลสินค้าจริง",
    }


def get_product_details(product_id: str) -> dict:
    """Return verified fields currently available in the prototype catalog."""

    product = _PRODUCT_CATALOG.get(product_id)
    if not product:
        return {"status": "not_found", "product_id": product_id}
    return {"status": "success", "product": product.copy()}


def check_product_availability(product_id: str, store_id: str = "online") -> dict:
    """Check prototype stock; zero stock must not be presented as available."""

    product = _PRODUCT_CATALOG.get(product_id)
    if not product:
        return {"status": "not_found", "available": False, "quantity": 0}
    quantity = int(product.get("stock", 0))
    return {
        "status": "success",
        "available": quantity > 0,
        "quantity": quantity,
        "store": store_id,
        "source_status": product.get("source_status", "unknown"),
    }


def access_cart_information(customer_id: str) -> dict:
    """Return the customer's current in-memory cart with totals in THB."""

    items = _CARTS.get(customer_id, [])
    subtotal = round(sum(i["unit_price"] * i["quantity"] for i in items), 2)
    return {
        "status": "success",
        "customer_id": customer_id,
        "items": items,
        "subtotal": subtotal,
        "currency": "THB",
    }


def modify_cart(
    customer_id: str,
    items_to_add: list[dict],
    items_to_remove: list[dict],
) -> dict:
    """Add or remove confirmed items from the prototype cart."""

    cart = _CARTS.setdefault(customer_id, [])
    remove_ids = {item.get("product_id") for item in items_to_remove}
    cart[:] = [item for item in cart if item["product_id"] not in remove_ids]

    for requested in items_to_add:
        product_id = requested.get("product_id", "")
        quantity = int(requested.get("quantity", 1))
        product = _PRODUCT_CATALOG.get(product_id)
        if not product or quantity < 1:
            continue
        existing = next((i for i in cart if i["product_id"] == product_id), None)
        if existing:
            existing["quantity"] += quantity
        else:
            cart.append(
                {
                    "product_id": product_id,
                    "name": product["name"],
                    "quantity": quantity,
                    "unit_price": float(product["price"]),
                    "currency": product["currency"],
                }
            )

    result = access_cart_information(customer_id)
    result["message"] = "Cart updated. Confirm product price and stock before checkout."
    return result


def calculate_order_summary(
    customer_id: str,
    shipping_fee: float = 0.0,
    discount_amount: float = 0.0,
) -> dict:
    """Calculate a transparent order summary in Thai baht."""

    cart = access_cart_information(customer_id)
    subtotal = float(cart["subtotal"])
    shipping_fee = max(float(shipping_fee), 0.0)
    discount_amount = max(min(float(discount_amount), subtotal), 0.0)
    total = round(subtotal + shipping_fee - discount_amount, 2)
    return {
        "status": "success",
        "items": cart["items"],
        "subtotal": subtotal,
        "shipping_fee": shipping_fee,
        "discount_amount": discount_amount,
        "total": total,
        "currency": "THB",
    }


def create_order(
    customer_id: str,
    shipping_address: dict,
    payment_method: str,
    customer_confirmed: bool,
) -> dict:
    """Create an order only after explicit customer confirmation."""

    if not customer_confirmed:
        return {"status": "confirmation_required"}
    summary = calculate_order_summary(customer_id)
    if not summary["items"]:
        return {"status": "rejected", "message": "Cart is empty."}
    if any(item["unit_price"] <= 0 for item in summary["items"]):
        return {
            "status": "rejected",
            "message": "Product prices are not connected to a verified catalog yet.",
        }
    order_id = f"ENIE-{uuid.uuid4().hex[:10].upper()}"
    order = {
        "order_id": order_id,
        "customer_id": customer_id,
        "created_at": _now_iso(),
        "shipping_address": shipping_address,
        "payment_method": payment_method,
        "payment_status": "pending",
        "order_status": "created",
        **summary,
    }
    _ORDERS[order_id] = order
    _CARTS[customer_id] = []
    return {"status": "success", "order": order}


def record_payment_status(
    order_id: str,
    payment_status: str,
    reference: str = "",
) -> dict:
    """Record a payment status supplied by a trusted payment integration."""

    order = _ORDERS.get(order_id)
    if not order:
        return {"status": "not_found", "order_id": order_id}
    allowed = {"pending", "paid", "failed", "refunded"}
    if payment_status not in allowed:
        return {"status": "rejected", "allowed_statuses": sorted(allowed)}
    order["payment_status"] = payment_status
    order["payment_reference"] = reference
    order["updated_at"] = _now_iso()
    return {"status": "success", "order": order}


def schedule_follow_up(
    customer_id: str,
    order_id: str,
    follow_up_at: str,
    purpose: str,
    channel: str,
    customer_consented: bool,
) -> dict:
    """Schedule a post-sale follow-up only when the customer has consented."""

    if not customer_consented:
        return {"status": "consent_required"}
    follow_up_id = str(uuid.uuid4())
    follow_up = {
        "follow_up_id": follow_up_id,
        "customer_id": customer_id,
        "order_id": order_id,
        "follow_up_at": follow_up_at,
        "purpose": purpose,
        "channel": channel,
        "status": "scheduled",
        "created_at": _now_iso(),
    }
    _FOLLOW_UPS[follow_up_id] = follow_up
    return {"status": "success", "follow_up": follow_up}


def record_product_usage_result(
    customer_id: str,
    order_id: str,
    result_summary: str,
    adverse_reaction: bool,
    next_action: str,
) -> dict:
    """Record post-sale usage feedback and flag possible adverse reactions."""

    record = {
        "type": "post_sale_result",
        "created_at": _now_iso(),
        "order_id": order_id,
        "result_summary": result_summary,
        "adverse_reaction": adverse_reaction,
        "next_action": next_action,
    }
    _CRM_NOTES.setdefault(customer_id, []).append(record)
    return {
        "status": "success",
        "record": record,
        "requires_human_review": adverse_reaction,
    }


def handoff_to_human(
    customer_id: str,
    reason: str,
    conversation_summary: str,
    priority: str = "normal",
) -> dict:
    """Create a human-agent handoff with concise context."""

    handoff_id = str(uuid.uuid4())
    handoff = {
        "handoff_id": handoff_id,
        "customer_id": customer_id,
        "reason": reason,
        "conversation_summary": conversation_summary,
        "priority": priority,
        "status": "queued",
        "created_at": _now_iso(),
    }
    _HUMAN_HANDOFFS[handoff_id] = handoff
    return {"status": "success", "handoff": handoff}


def generate_sales_report() -> dict:
    """Return a small operational report from prototype in-memory data."""

    paid_orders = [o for o in _ORDERS.values() if o["payment_status"] == "paid"]
    revenue = round(sum(float(o["total"]) for o in paid_orders), 2)
    return {
        "status": "success",
        "orders_total": len(_ORDERS),
        "paid_orders": len(paid_orders),
        "revenue": revenue,
        "currency": "THB",
        "consultations": sum(len(v) for v in _CRM_NOTES.values()),
        "follow_ups_scheduled": len(_FOLLOW_UPS),
        "human_handoffs": len(_HUMAN_HANDOFFS),
    }


def approve_discount(discount_type: str, value: float, reason: str) -> dict:
    """Approve a discount within prototype policy limits."""

    limit = MAX_DISCOUNT_RATE if discount_type == "percentage" else MAX_FIXED_DISCOUNT_THB
    if value < 0 or value > limit:
        return {"status": "rejected", "limit": limit, "reason": reason}
    return {"status": "approved", "discount_type": discount_type, "value": value}


def sync_ask_for_approval(discount_type: str, value: float, reason: str) -> dict:
    """Create a placeholder manager-approval request."""

    return {
        "status": "pending_manager_approval",
        "request_id": str(uuid.uuid4()),
        "discount_type": discount_type,
        "value": value,
        "reason": reason,
    }


def update_salesforce_crm(customer_id: str, details: dict) -> dict:
    """Compatibility adapter that stores a generic CRM note."""

    note = {"type": "crm_update", "created_at": _now_iso(), "details": details}
    _CRM_NOTES.setdefault(customer_id, []).append(note)
    return {"status": "success", "message": "CRM note saved.", "note": note}


def send_care_instructions(
    customer_id: str,
    plant_type: str,
    delivery_method: str,
) -> dict:
    """Compatibility adapter for sending hair aftercare instructions."""

    return {
        "status": "queued",
        "customer_id": customer_id,
        "topic": plant_type,
        "delivery_method": delivery_method,
        "message": "Aftercare delivery requires a configured messaging provider.",
    }


def get_product_recommendations(plant_type: str, customer_id: str) -> dict:
    """Compatibility adapter to the hair-product search tool."""

    return search_hair_products(concern=plant_type)


def send_call_companion_link(phone_number: str) -> dict:
    """Return a placeholder response for a future secure image/video flow."""

    return {
        "status": "not_configured",
        "phone_number": phone_number,
        "message": "Secure media consultation provider is not configured.",
    }


def schedule_planting_service(
    customer_id: str,
    date: str,
    time_range: str,
    details: str,
) -> dict:
    """Deprecated adapter; salon appointment integration is not configured."""

    return {
        "status": "not_configured",
        "customer_id": customer_id,
        "date": date,
        "time_range": time_range,
        "details": details,
    }


def get_available_planting_times(date: str) -> list:
    """Deprecated adapter returning no invented salon appointment slots."""

    logger.info("Appointment availability requested for %s", date)
    return []


def generate_qr_code(
    customer_id: str,
    discount_value: float,
    discount_type: str,
    expiration_days: int,
) -> dict:
    """Return a placeholder until a real promotion service is configured."""

    return {
        "status": "not_configured",
        "customer_id": customer_id,
        "discount_value": discount_value,
        "discount_type": discount_type,
        "expiration_days": expiration_days,
    }
