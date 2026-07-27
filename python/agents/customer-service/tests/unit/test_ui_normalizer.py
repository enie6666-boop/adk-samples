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

from customer_service.tools.frontend_tools import (
    display_order_summary,
    display_product_cards,
)
from customer_service.ui.normalizer import normalize_agent_output


def test_normalize_text_and_product_action() -> None:
    response = normalize_agent_output(
        "session-1",
        [
            "แนะนำสินค้าให้ตามสภาพเส้นผมค่ะ",
            display_product_cards([{"id": "smart-lotion-a1", "name": "SMART LOTION A-1"}]),
        ],
    )

    assert response.session_id == "session-1"
    assert response.state == "completed"
    assert response.messages[0].text == "แนะนำสินค้าให้ตามสภาพเส้นผมค่ะ"
    assert response.actions[0].action_type == "display_product_cards"


def test_confirmation_action_changes_response_state() -> None:
    response = normalize_agent_output(
        "session-2",
        display_order_summary({"items": [], "total": 0}),
    )

    assert response.state == "awaiting_confirmation"
    assert response.actions[0].requires_confirmation is True


def test_invalid_action_is_not_forwarded_to_frontend() -> None:
    response = normalize_agent_output(
        "session-3",
        {
            "status": "frontend_action",
            "action_id": "bad-action",
            "action_type": "unsupported_action",
            "created_at": "2026-07-27T00:00:00+00:00",
            "requires_confirmation": False,
            "payload": {},
        },
    )

    assert response.state == "failed"
    assert response.actions == []
    assert response.error == "Agent returned an invalid frontend action."


def test_empty_output_returns_safe_system_message() -> None:
    response = normalize_agent_output("session-4", None)

    assert response.state == "completed"
    assert response.messages[0].role == "system"
