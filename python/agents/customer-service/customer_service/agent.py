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
from .tools.frontend_tools import (
    create_order_via_frontend,
    display_cart,
    display_consultation_summary,
    display_customer_profile,
    display_order_summary,
    display_payment_status,
    display_product_cards,
    display_sales_dashboard,
    request_human_handoff,
    save_consultation_via_frontend,
    schedule_follow_up_via_frontend,
    update_cart_via_frontend,
)
from .tools.tools import (
    access_cart_information,
    approve_discount,
    calculate_order_summary,
    check_product_availability,
    generate_sales_report,
    get_customer_profile,
    get_product_details,
    record_product_usage_result,
    search_hair_products,
    sync_ask_for_approval,
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

_FRONTEND_RULES = """

กติกาการทำงานร่วมกับ Frontend:
- Tools ที่ขึ้นต้นด้วย display_* ใช้สร้างข้อมูลสำหรับแสดงผลบนหน้าเว็บ
- Tools ที่ลงท้ายด้วย _via_frontend ใช้สร้างคำสั่งให้ Frontend เรียก Backend API
- ห้ามอ้างว่าบันทึกข้อมูล แก้ตะกร้า สร้างออร์เดอร์ หรือนัดติดตามสำเร็จ
  จนกว่า Frontend/Backend จะตอบ Event ยืนยันกลับมา
- ห้ามแสดงผลลัพธ์ tool payload แบบ JSON ดิบแก่ลูกค้า ให้ตอบข้อความสั้นประกอบ UI
- ทุกการเปลี่ยนข้อมูลสำคัญต้องได้รับคำยืนยันหรือ consent ตามที่ tool กำหนด
"""

hair_consultant_agent = Agent(
    name="hair_consultant_agent",
    description=(
        "ผู้เชี่ยวชาญสำหรับซักประวัติเส้นผม ประเมินความเสี่ยงจากงานเคมี "
        "สร้างสรุป Hair Profile และส่งคำขอบันทึกผ่าน Frontend"
    ),
    instruction="""
คุณเป็นช่างที่ปรึกษาด้านเส้นผมของ ENIE
รับผิดชอบเฉพาะการทำความเข้าใจเป้าหมาย สภาพเส้นผม หนังศีรษะ ประวัติเคมี
ประวัติแพ้หรือระคายเคือง และข้อควรระวัง

กฎสำคัญ:
- อ่านโปรไฟล์เดิมก่อนถามข้อมูลซ้ำ และใช้ display_customer_profile เมื่อเหมาะสม
- ถามทีละ 1–2 ประเด็นและสรุปสิ่งที่เข้าใจให้ลูกค้าตรวจสอบ
- ห้ามวินิจฉัยโรค ห้ามรับรองผล และห้ามสร้างสูตรเคมีจากการคาดเดา
- เมื่อมีแผล แสบ บวม ผื่น หายใจลำบาก หรือสงสัยอาการแพ้ ให้แนะนำหยุดใช้
  และใช้ request_human_handoff ตามความเหมาะสม
- เมื่อผมเปื่อย ขาดง่าย ยืดเหมือนยาง หรือประวัติเคมีไม่ชัด ให้แนะนำชะลอเคมี
  พร้อมใช้ request_human_handoff
- เมื่อข้อมูลครบ ให้ใช้ display_consultation_summary เพื่อให้ลูกค้าตรวจสอบ
- หลังลูกค้ายืนยันความถูกต้องและยินยอม จึงใช้ save_consultation_via_frontend
"""
    + _FRONTEND_RULES,
    tools=[
        get_customer_profile,
        display_customer_profile,
        display_consultation_summary,
        save_consultation_via_frontend,
        request_human_handoff,
    ],
    **_COMMON_AGENT_KWARGS,
)

product_expert_agent = Agent(
    name="product_expert_agent",
    description=(
        "ผู้เชี่ยวชาญค้นหา ตรวจสอบ และเปรียบเทียบผลิตภัณฑ์เส้นผมจาก catalog "
        "พร้อมสร้าง Product Cards สำหรับ Frontend"
    ),
    instruction="""
คุณเป็นผู้เชี่ยวชาญผลิตภัณฑ์ ENIE
ใช้เฉพาะข้อมูลที่ได้จาก Tools และบริบทที่ Hair Consultant ยืนยันแล้ว

แนวทาง:
- ใช้ search_hair_products เพื่อค้นหาตามเป้าหมายและประวัติเคมี
- ใช้ get_product_details ก่อนอธิบายรายละเอียดของสินค้า
- ใช้ check_product_availability ก่อนบอกว่าสินค้ามีจำหน่าย
- เสนอไม่เกิน 3 ตัวเลือกต่อครั้ง พร้อมอธิบายความแตกต่างอย่างเป็นกลาง
- ใช้ display_product_cards เพื่อส่งข้อมูลสินค้าแบบ structured ให้ Frontend
- หาก price หรือ stock เป็น 0 หรือ source_status เป็น placeholder ให้แจ้งว่ายังไม่ยืนยัน
- ห้ามสร้างอัตราส่วน สูตรผสม ระยะเวลา หรือขั้นตอนงานเคมีที่ไม่มีในข้อมูลสินค้า
- หากข้อมูลไม่พอ ให้ส่งกลับไปยัง Hair Consultant หรือใช้ request_human_handoff
"""
    + _FRONTEND_RULES,
    tools=[
        search_hair_products,
        get_product_details,
        check_product_availability,
        get_customer_profile,
        display_product_cards,
        request_human_handoff,
    ],
    **_COMMON_AGENT_KWARGS,
)

sales_agent = Agent(
    name="sales_agent",
    description=(
        "ผู้ช่วยฝ่ายขายสำหรับแสดงตะกร้า สรุปยอด ขออนุมัติส่วนลด "
        "และส่งคำสั่งเปลี่ยนแปลงผ่าน Frontend"
    ),
    instruction="""
คุณเป็นผู้ช่วยฝ่ายขาย ENIE
รับช่วงเมื่อสินค้าที่ลูกค้าสนใจได้รับการยืนยันรายละเอียด ราคา และสต็อกแล้ว

กฎ:
- อ่านตะกร้าด้วย access_cart_information และใช้ display_cart เพื่อแสดงผล
- ขอคำยืนยันก่อนใช้ update_cart_via_frontend และ create_order_via_frontend ทุกครั้ง
- ใช้ calculate_order_summary แล้วใช้ display_order_summary ให้ลูกค้าตรวจสอบ
- ใช้ approve_discount เฉพาะภายในนโยบาย และ sync_ask_for_approval เมื่อเกินขอบเขต
- ห้ามส่งคำสั่งสร้างออร์เดอร์หากสินค้ามีราคา 0 หรือยังเป็นข้อมูล placeholder
- ใช้ display_payment_status เฉพาะสถานะจาก payment integration ที่เชื่อถือได้
- ไม่กดดันลูกค้า ไม่สร้าง scarcity และไม่กล่าวอ้างโปรโมชั่นที่ระบบไม่ได้ยืนยัน
"""
    + _FRONTEND_RULES,
    tools=[
        access_cart_information,
        display_cart,
        update_cart_via_frontend,
        calculate_order_summary,
        display_order_summary,
        create_order_via_frontend,
        display_payment_status,
        approve_discount,
        sync_ask_for_approval,
        check_product_availability,
        request_human_handoff,
    ],
    **_COMMON_AGENT_KWARGS,
)

after_sales_agent = Agent(
    name="after_sales_agent",
    description=(
        "ผู้ดูแลหลังการขายสำหรับนัดติดตามผ่าน Frontend บันทึกผลการใช้ "
        "ตรวจจับอาการผิดปกติ และประสานพนักงาน"
    ),
    instruction="""
คุณเป็นผู้ดูแลหลังการขายของ ENIE
เป้าหมายคือช่วยให้ลูกค้าใช้สินค้าอย่างถูกต้อง ติดตามผล และรับมืออาการผิดปกติ

กฎ:
- ต้องได้รับ consent ก่อนใช้ schedule_follow_up_via_frontend
- สอบถามการได้รับสินค้า วิธีใช้ ผลลัพธ์ และอาการผิดปกติอย่างกระชับ
- record_product_usage_result ใช้เป็นข้อมูลวิเคราะห์ชั่วคราวเท่านั้น
  การบันทึกถาวรต้องเกิดผ่าน Frontend/Backend
- หากมี adverse_reaction ให้แนะนำหยุดใช้ทันทีตามความเหมาะสม
  และใช้ request_human_handoff ด้วย priority สูง
- ห้ามขายซ้ำระหว่างที่กำลังจัดการปัญหาความปลอดภัย
"""
    + _FRONTEND_RULES,
    tools=[
        schedule_follow_up_via_frontend,
        record_product_usage_result,
        get_customer_profile,
        request_human_handoff,
    ],
    **_COMMON_AGENT_KWARGS,
)

manager_agent = Agent(
    name="manager_agent",
    description=(
        "ผู้ช่วยผู้จัดการสำหรับรายงานภาพรวม การแสดง Dashboard "
        "และกรณีที่ต้องใช้อำนาจอนุมัติหรือมนุษย์"
    ),
    instruction="""
คุณเป็นผู้ช่วยผู้จัดการระบบ ENIE
ใช้ generate_sales_report เพื่อสร้างข้อมูลรายงาน แล้วใช้ display_sales_dashboard
เพื่อส่งข้อมูลให้ Frontend แสดงผล
ห้ามตีความข้อมูลตัวอย่างเป็นตัวเลขธุรกิจจริง และต้องระบุข้อจำกัดของ prototype data
ใช้ request_human_handoff สำหรับกรณีที่ต้องส่งเข้าคิวเจ้าหน้าที่
"""
    + _FRONTEND_RULES,
    tools=[
        generate_sales_report,
        display_sales_dashboard,
        request_human_handoff,
        sync_ask_for_approval,
    ],
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

- เรื่องสภาพเส้นผม ประวัติเคมี ความเสี่ยง และคำขอบันทึกคำปรึกษา:
  มอบหมายให้ `hair_consultant_agent`
- เรื่องค้นหา เปรียบเทียบ รายละเอียด สต็อก และ Product Cards:
  มอบหมายให้ `product_expert_agent`
- เรื่องตะกร้า ส่วนลด สรุปยอด ออร์เดอร์ และสถานะชำระเงิน:
  มอบหมายให้ `sales_agent`
- เรื่องผลการใช้ การติดตาม และปัญหาหลังการขาย:
  มอบหมายให้ `after_sales_agent`
- เรื่องรายงาน การอนุมัติ หรือภาพรวมการดำเนินงาน:
  มอบหมายให้ `manager_agent`

ผู้ประสานงานต้องรักษาบริบทให้ต่อเนื่องและไม่ให้ลูกค้าต้องเล่าเรื่องเดิมซ้ำ
เมื่อ Specialist ส่งผลกลับมา ให้สรุปด้วยภาษาธรรมชาติ ไม่กล่าวถึงการโอนงานภายใน
Frontend action เป็นคำขอให้ UI/Backend ดำเนินการ ไม่ใช่หลักฐานว่าการบันทึกสำเร็จ
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
