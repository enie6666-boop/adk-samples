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

"""Multi-agent entry point for the ENIE hair consultation and sales assistant."""

import logging
import warnings

from google.adk import Agent

from .config import Config
from .prompts import GLOBAL_INSTRUCTION, INSTRUCTION
from .shared_libraries.callbacks import (
    after_tool,
    before_agent,
    before_tool,
    rate_limit_callback,
)
from .tools.tools import (
    access_cart_information,
    approve_discount,
    calculate_order_summary,
    check_product_availability,
    create_order,
    generate_sales_report,
    get_customer_profile,
    get_product_details,
    handoff_to_human,
    modify_cart,
    record_payment_status,
    record_product_usage_result,
    save_hair_consultation,
    schedule_follow_up,
    search_hair_products,
    sync_ask_for_approval,
    update_salesforce_crm,
)

warnings.filterwarnings("ignore", category=UserWarning, module=".*pydantic.*")

configs = Config()
logger = logging.getLogger(__name__)

_COMMON_AGENT_KWARGS = {
    "model": configs.agent_settings.model,
    "before_tool_callback": before_tool,
    "after_tool_callback": after_tool,
    "before_agent_callback": before_agent,
    "before_model_callback": rate_limit_callback,
}

hair_consultant_agent = Agent(
    name="hair_consultant_agent",
    description=(
        "ผู้เชี่ยวชาญสำหรับซักประวัติเส้นผม ประเมินความเสี่ยงจากงานเคมี "
        "บันทึก Hair Profile และส่งต่อมนุษย์เมื่อมีความเสี่ยง"
    ),
    instruction="""
คุณเป็นช่างที่ปรึกษาด้านเส้นผมของ ENIE
รับผิดชอบเฉพาะการทำความเข้าใจเป้าหมาย สภาพเส้นผม หนังศีรษะ ประวัติเคมี
ประวัติแพ้หรือระคายเคือง และข้อควรระวัง

กฎสำคัญ:
- อ่านโปรไฟล์เดิมก่อนถามข้อมูลซ้ำ
- ถามทีละ 1–2 ประเด็นและสรุปสิ่งที่เข้าใจให้ลูกค้าตรวจสอบ
- ห้ามวินิจฉัยโรค ห้ามรับรองผล และห้ามสร้างสูตรเคมีจากการคาดเดา
- เมื่อมีแผล แสบ บวม ผื่น หายใจลำบาก หรือสงสัยอาการแพ้ ให้แนะนำหยุดใช้
  และส่งต่อบุคลากรทางการแพทย์หรือพนักงานตามความเหมาะสม
- เมื่อผมเปื่อย ขาดง่าย ยืดเหมือนยาง หรือประวัติเคมีไม่ชัด ให้แนะนำชะลอเคมี
  พร้อมเรียก handoff_to_human
- บันทึกข้อมูลด้วย save_hair_consultation หลังลูกค้ายืนยันความถูกต้องและยินยอม
""",
    tools=[
        get_customer_profile,
        save_hair_consultation,
        handoff_to_human,
        update_salesforce_crm,
    ],
    **_COMMON_AGENT_KWARGS,
)

product_expert_agent = Agent(
    name="product_expert_agent",
    description=(
        "ผู้เชี่ยวชาญค้นหา ตรวจสอบ และเปรียบเทียบผลิตภัณฑ์เส้นผมจาก catalog "
        "โดยไม่แต่งราคา สต็อก วิธีใช้ หรือคุณสมบัติ"
    ),
    instruction="""
คุณเป็นผู้เชี่ยวชาญผลิตภัณฑ์ ENIE
ใช้เฉพาะข้อมูลที่ได้จาก Tools และบริบทที่ Hair Consultant ยืนยันแล้ว

แนวทาง:
- ใช้ search_hair_products เพื่อค้นหาตามเป้าหมายและประวัติเคมี
- ใช้ get_product_details ก่อนอธิบายรายละเอียดของสินค้า
- ใช้ check_product_availability ก่อนบอกว่าสินค้ามีจำหน่าย
- เสนอไม่เกิน 3 ตัวเลือกต่อครั้ง พร้อมอธิบายความแตกต่างอย่างเป็นกลาง
- หาก price หรือ stock เป็น 0 หรือ source_status เป็น placeholder ให้แจ้งว่ายังไม่ยืนยัน
- ห้ามสร้างอัตราส่วน สูตรผสม ระยะเวลา หรือขั้นตอนงานเคมีที่ไม่มีในข้อมูลสินค้า
- หากข้อมูลไม่พอ ให้ส่งกลับไปยัง Hair Consultant หรือส่งต่อพนักงาน
""",
    tools=[
        search_hair_products,
        get_product_details,
        check_product_availability,
        get_customer_profile,
        handoff_to_human,
    ],
    **_COMMON_AGENT_KWARGS,
)

sales_agent = Agent(
    name="sales_agent",
    description=(
        "ผู้ช่วยฝ่ายขายสำหรับตะกร้า สรุปยอด ส่วนลด การสร้างออร์เดอร์ "
        "และสถานะการชำระเงิน"
    ),
    instruction="""
คุณเป็นผู้ช่วยฝ่ายขาย ENIE
รับช่วงเมื่อสินค้าที่ลูกค้าสนใจได้รับการยืนยันรายละเอียด ราคา และสต็อกแล้ว

กฎ:
- ตรวจตะกร้าด้วย access_cart_information ก่อนแก้ไขเสมอ
- ขอคำยืนยันก่อน modify_cart และ create_order ทุกครั้ง
- ใช้ calculate_order_summary เพื่อสรุปรายการ จำนวน ราคา ส่วนลด ค่าจัดส่ง และยอดรวม
- ใช้ approve_discount เฉพาะภายในนโยบาย และ sync_ask_for_approval เมื่อเกินขอบเขต
- ห้ามสร้างออร์เดอร์หากสินค้ามีราคา 0 หรือยังเป็นข้อมูล placeholder
- record_payment_status ใช้เฉพาะข้อมูลจาก payment integration ที่เชื่อถือได้
- ไม่กดดันลูกค้า ไม่สร้าง scarcity และไม่กล่าวอ้างโปรโมชั่นที่ระบบไม่ได้ยืนยัน
""",
    tools=[
        access_cart_information,
        modify_cart,
        calculate_order_summary,
        create_order,
        record_payment_status,
        approve_discount,
        sync_ask_for_approval,
        check_product_availability,
        handoff_to_human,
    ],
    **_COMMON_AGENT_KWARGS,
)

after_sales_agent = Agent(
    name="after_sales_agent",
    description=(
        "ผู้ดูแลหลังการขายสำหรับการนัดติดตาม บันทึกผลการใช้ "
        "ตรวจจับอาการผิดปกติ และประสานพนักงาน"
    ),
    instruction="""
คุณเป็นผู้ดูแลหลังการขายของ ENIE
เป้าหมายคือช่วยให้ลูกค้าใช้สินค้าอย่างถูกต้อง ติดตามผล และรับมืออาการผิดปกติ

กฎ:
- ต้องได้รับ consent ก่อนใช้ schedule_follow_up
- สอบถามการได้รับสินค้า วิธีใช้ ผลลัพธ์ และอาการผิดปกติอย่างกระชับ
- บันทึกผลด้วย record_product_usage_result
- หากมี adverse_reaction ให้แนะนำหยุดใช้ทันทีตามความเหมาะสม
  และเรียก handoff_to_human ด้วย priority สูง
- ห้ามขายซ้ำระหว่างที่กำลังจัดการปัญหาความปลอดภัย
""",
    tools=[
        schedule_follow_up,
        record_product_usage_result,
        get_customer_profile,
        handoff_to_human,
    ],
    **_COMMON_AGENT_KWARGS,
)

manager_agent = Agent(
    name="manager_agent",
    description=(
        "ผู้ช่วยผู้จัดการสำหรับรายงานภาพรวมและกรณีที่ต้องใช้อำนาจอนุมัติหรือมนุษย์"
    ),
    instruction="""
คุณเป็นผู้ช่วยผู้จัดการระบบ ENIE
ใช้ generate_sales_report เพื่อสรุปข้อมูล prototype และช่วยจัดลำดับ human handoff
ห้ามตีความข้อมูลตัวอย่างเป็นตัวเลขธุรกิจจริง และต้องระบุข้อจำกัดของ in-memory data
""",
    tools=[generate_sales_report, handoff_to_human, sync_ask_for_approval],
    **_COMMON_AGENT_KWARGS,
)

root_agent = Agent(
    name="enie_hair_sales_coordinator",
    description=(
        "ผู้ประสานงานหลักของ ENIE สำหรับการให้คำปรึกษาเส้นผม แนะนำสินค้า "
        "รับออร์เดอร์ และดูแลหลังการขาย"
    ),
    model=configs.agent_settings.model,
    global_instruction=GLOBAL_INSTRUCTION,
    instruction=INSTRUCTION
    + """

## การมอบหมายงานให้ Specialist

- เรื่องสภาพเส้นผม ประวัติเคมี ความเสี่ยง และการบันทึกคำปรึกษา:
  มอบหมายให้ `hair_consultant_agent`
- เรื่องค้นหา เปรียบเทียบ รายละเอียด และสต็อกสินค้า:
  มอบหมายให้ `product_expert_agent`
- เรื่องตะกร้า ส่วนลด สรุปยอด ออร์เดอร์ และการชำระเงิน:
  มอบหมายให้ `sales_agent`
- เรื่องผลการใช้ การติดตาม และปัญหาหลังการขาย:
  มอบหมายให้ `after_sales_agent`
- เรื่องรายงาน การอนุมัติ หรือภาพรวมการดำเนินงาน:
  มอบหมายให้ `manager_agent`

ผู้ประสานงานต้องรักษาบริบทให้ต่อเนื่องและไม่ให้ลูกค้าต้องเล่าเรื่องเดิมซ้ำ
เมื่อ Specialist ส่งผลกลับมา ให้สรุปด้วยภาษาธรรมชาติ ไม่กล่าวถึงการโอนงานภายใน
""",
    sub_agents=[
        hair_consultant_agent,
        product_expert_agent,
        sales_agent,
        after_sales_agent,
        manager_agent,
    ],
    before_agent_callback=before_agent,
    before_model_callback=rate_limit_callback,
)
