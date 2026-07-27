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

"""Pydantic models for responses rendered by ENIE frontend clients."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class TextMessage(BaseModel):
    """A human-readable message displayed alongside structured UI actions."""

    model_config = ConfigDict(extra="forbid")

    role: Literal["assistant", "system"] = "assistant"
    text: str = Field(min_length=1)


class FrontendAction(BaseModel):
    """A validated command that a frontend renderer can display or execute."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["frontend_action"] = "frontend_action"
    action_id: str = Field(min_length=1)
    action_type: Literal[
        "display_customer_profile",
        "display_consultation_summary",
        "save_consultation",
        "display_product_cards",
        "display_cart",
        "update_cart",
        "display_order_summary",
        "create_order",
        "display_payment_status",
        "schedule_follow_up",
        "display_sales_dashboard",
        "request_human_handoff",
    ]
    created_at: datetime
    requires_confirmation: bool = False
    payload: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Stable API response consumed by web, LINE, and Messenger renderers."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1)
    messages: list[TextMessage] = Field(default_factory=list)
    actions: list[FrontendAction] = Field(default_factory=list)
    state: Literal["completed", "awaiting_confirmation", "failed"] = "completed"
    error: str | None = None
