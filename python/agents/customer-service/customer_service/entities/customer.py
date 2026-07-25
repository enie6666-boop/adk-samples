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

"""Customer and hair-consultation entities for the ENIE sales agent."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Address(BaseModel):
    """Customer shipping or billing address."""

    street: str = ""
    district: str = ""
    province: str = ""
    postal_code: str = ""
    country: str = "TH"
    model_config = ConfigDict(from_attributes=True)


class Product(BaseModel):
    """Product recorded in an order history."""

    product_id: str
    name: str
    quantity: int = Field(ge=1)
    unit_price: float | None = Field(default=None, ge=0)
    model_config = ConfigDict(from_attributes=True)


class Purchase(BaseModel):
    """Completed customer purchase."""

    order_id: str
    date: str
    items: list[Product]
    total_amount: float = Field(ge=0)
    status: str = "completed"
    model_config = ConfigDict(from_attributes=True)


class CommunicationPreferences(BaseModel):
    """Consent and preferred channels for customer communication."""

    line: bool = True
    messenger: bool = False
    email: bool = False
    phone: bool = False
    marketing_consent: bool = False
    follow_up_consent: bool = False
    preferred_channel: str = "line"
    model_config = ConfigDict(from_attributes=True)


class ChemicalService(BaseModel):
    """A chemical service previously performed on the customer's hair."""

    service_type: str
    performed_at: str | None = None
    notes: str = ""
    model_config = ConfigDict(from_attributes=True)


class HairProfile(BaseModel):
    """Structured information used to provide safer hair recommendations."""

    strand_thickness: str | None = None
    density: str | None = None
    porosity: str | None = None
    scalp_condition: str | None = None
    current_condition: list[str] = Field(default_factory=list)
    chemical_history: list[ChemicalService] = Field(default_factory=list)
    allergy_or_irritation_history: str | None = None
    current_goal: str | None = None
    professional_notes: list[str] = Field(default_factory=list)
    last_updated_at: str | None = None
    model_config = ConfigDict(from_attributes=True)


class ConsultationRecord(BaseModel):
    """Summary of a consultation between the agent and customer."""

    consultation_id: str
    created_at: str
    channel: str
    customer_goal: str
    observations: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    follow_up_required: bool = False
    model_config = ConfigDict(from_attributes=True)


class Customer(BaseModel):
    """Customer CRM record used by the ENIE hair sales agent."""

    account_number: str
    customer_id: str
    customer_first_name: str
    customer_last_name: str = ""
    email: str = ""
    phone_number: str = ""
    line_user_id: str | None = None
    messenger_user_id: str | None = None
    customer_start_date: str = ""
    years_as_customer: int = Field(default=0, ge=0)
    shipping_address: Address = Field(default_factory=Address)
    purchase_history: list[Purchase] = Field(default_factory=list)
    loyalty_points: int = Field(default=0, ge=0)
    preferred_store: str = "ENIE Online"
    communication_preferences: CommunicationPreferences = Field(
        default_factory=CommunicationPreferences
    )
    hair_profile: HairProfile = Field(default_factory=HairProfile)
    consultation_history: list[ConsultationRecord] = Field(default_factory=list)
    scheduled_follow_ups: dict = Field(default_factory=dict)
    model_config = ConfigDict(from_attributes=True)

    def to_json(self) -> str:
        """Return the customer record as formatted JSON."""

        return self.model_dump_json(indent=4)

    @staticmethod
    def get_customer(current_customer_id: str) -> Optional["Customer"]:
        """Return a development customer until a real CRM is configured."""

        return Customer(
            customer_id=current_customer_id,
            account_number="ENIE-DEMO-001",
            customer_first_name="ลูกค้า",
            customer_start_date="2026-01-01",
            years_as_customer=0,
            line_user_id="line-demo-user",
            shipping_address=Address(),
            purchase_history=[],
            loyalty_points=0,
            preferred_store="ENIE Online",
            communication_preferences=CommunicationPreferences(
                line=True,
                messenger=False,
                marketing_consent=False,
                follow_up_consent=False,
                preferred_channel="line",
            ),
            hair_profile=HairProfile(),
            consultation_history=[],
            scheduled_follow_ups={},
        )
