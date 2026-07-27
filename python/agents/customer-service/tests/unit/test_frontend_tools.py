"""Unit tests for ENIE frontend action contracts."""

from customer_service.tools.frontend_tools import (
    create_order_via_frontend,
    display_product_cards,
    save_consultation_via_frontend,
    schedule_follow_up_via_frontend,
    update_cart_via_frontend,
)


def test_display_product_cards_returns_render_action():
    result = display_product_cards(
        products=[{"id": "smart-lotion-a1", "name": "SMART LOTION A-1"}]
    )

    assert result["status"] == "frontend_action"
    assert result["action_type"] == "display_product_cards"
    assert result["requires_confirmation"] is False
    assert result["payload"]["products"][0]["id"] == "smart-lotion-a1"
    assert result["action_id"]
    assert result["created_at"]


def test_save_consultation_requires_confirmation():
    result = save_consultation_via_frontend(
        consultation={"customer_id": "customer-1"},
        customer_confirmed=False,
    )

    assert result == {"status": "confirmation_required"}


def test_confirmed_consultation_returns_persistence_action():
    result = save_consultation_via_frontend(
        consultation={"customer_id": "customer-1"},
        customer_confirmed=True,
    )

    assert result["action_type"] == "save_consultation"
    assert result["payload"]["consultation"]["customer_id"] == "customer-1"


def test_cart_update_requires_confirmation():
    result = update_cart_via_frontend(
        customer_id="customer-1",
        items_to_add=[{"product_id": "a1", "quantity": 1}],
        items_to_remove=[],
        customer_confirmed=False,
    )

    assert result == {"status": "confirmation_required"}


def test_order_creation_requires_confirmation():
    result = create_order_via_frontend(
        order={"customer_id": "customer-1", "items": []},
        customer_confirmed=False,
    )

    assert result == {"status": "confirmation_required"}


def test_follow_up_requires_consent():
    result = schedule_follow_up_via_frontend(
        customer_id="customer-1",
        order_id="order-1",
        follow_up_at="2026-08-01T10:00:00+07:00",
        purpose="ติดตามผลการใช้สินค้า",
        channel="line",
        customer_consented=False,
    )

    assert result == {"status": "consent_required"}
