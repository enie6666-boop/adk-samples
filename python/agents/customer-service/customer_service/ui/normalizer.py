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

"""Convert ADK/tool output into the stable ENIE frontend response contract."""

from collections.abc import Iterable
from typing import Any

from pydantic import ValidationError

from .schema import ChatResponse, FrontendAction, TextMessage


def _walk(value: Any) -> Iterable[Any]:
    """Yield nested values while treating frontend actions as atomic objects."""

    if isinstance(value, dict):
        if value.get("status") == "frontend_action":
            yield value
            return
        for item in value.values():
            yield from _walk(item)
        return

    if isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk(item)
        return

    yield value


def normalize_agent_output(session_id: str, output: Any) -> ChatResponse:
    """Build a renderer-safe response from arbitrary ADK event/tool output.

    Unknown dictionaries are traversed so this function can accept event lists,
    callback envelopes, or direct tool results. Invalid action dictionaries are
    excluded and represented by a non-sensitive error message.
    """

    messages: list[TextMessage] = []
    actions: list[FrontendAction] = []
    invalid_action_found = False

    for item in _walk(output):
        if isinstance(item, str) and item.strip():
            messages.append(TextMessage(text=item.strip()))
            continue

        if isinstance(item, dict) and item.get("status") == "frontend_action":
            try:
                actions.append(FrontendAction.model_validate(item))
            except ValidationError:
                invalid_action_found = True

    awaiting_confirmation = any(action.requires_confirmation for action in actions)
    state = "awaiting_confirmation" if awaiting_confirmation else "completed"
    error = None

    if invalid_action_found:
        state = "failed"
        error = "Agent returned an invalid frontend action."

    if not messages and not actions and not invalid_action_found:
        messages.append(TextMessage(role="system", text="ไม่พบผลลัพธ์ที่แสดงผลได้"))

    return ChatResponse(
        session_id=session_id,
        messages=messages,
        actions=actions,
        state=state,
        error=error,
    )
