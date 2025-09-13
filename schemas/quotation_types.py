# -*- coding: utf-8 -*-
"""
견적서 관련 타입 정의
"""

from typing import TypedDict, Optional
from .base_types import BaseRecord, DateType, DecimalType, CurrencyType

class QuotationDict(BaseRecord):
    """견적서 정보 완전 타입"""
    quotation_id: str
    customer_id: str
    quotation_number: Optional[str]
    quotation_date: DateType
    delivery_date: DateType
    currency: CurrencyType  # default: 'USD'
    exchange_rate: DecimalType
    total_amount: DecimalType
    status: str  # 'draft', 'pending', 'approved', 'rejected'
    notes: Optional[str]
    revision_number: int  # default: 0
    original_quotation_id: Optional[str]
    project_name: Optional[str]
    project_description: Optional[str]
    payment_terms: Optional[str]
    validity_period: Optional[str]
    delivery_terms: Optional[str]
    sales_rep_name: Optional[str]
    sales_rep_email: Optional[str]
    customer_company_name: Optional[str]
    customer_contact_person: Optional[str]
    customer_email: Optional[str]
    customer_phone: Optional[str]
    customer_address: Optional[str]

class QuotationCreateDict(TypedDict, total=False):
    """견적서 생성용 타입"""
    customer_id: str  # 필수
    quotation_date: Optional[DateType]
    delivery_date: Optional[DateType]
    currency: Optional[CurrencyType]
    exchange_rate: Optional[DecimalType]
    total_amount: Optional[DecimalType]
    status: Optional[str]
    notes: Optional[str]
    project_name: Optional[str]
    project_description: Optional[str]
    payment_terms: Optional[str]
    validity_period: Optional[str]
    delivery_terms: Optional[str]
    sales_rep_name: Optional[str]
    sales_rep_email: Optional[str]
    customer_company_name: Optional[str]
    customer_contact_person: Optional[str]
    customer_email: Optional[str]
    customer_phone: Optional[str]
    customer_address: Optional[str]

class QuotationUpdateDict(TypedDict, total=False):
    """견적서 수정용 타입 (모든 필드 선택적)"""
    customer_id: Optional[str]
    quotation_date: Optional[DateType]
    delivery_date: Optional[DateType]
    currency: Optional[CurrencyType]
    exchange_rate: Optional[DecimalType]
    total_amount: Optional[DecimalType]
    status: Optional[str]
    notes: Optional[str]
    project_name: Optional[str]
    project_description: Optional[str]
    payment_terms: Optional[str]
    validity_period: Optional[str]
    delivery_terms: Optional[str]
    sales_rep_name: Optional[str]
    sales_rep_email: Optional[str]
    customer_company_name: Optional[str]
    customer_contact_person: Optional[str]
    customer_email: Optional[str]
    customer_phone: Optional[str]
    customer_address: Optional[str]

class QuotationItemDict(BaseRecord):
    """견적서 아이템 정보 완전 타입"""
    quotation_id: str
    item_number: Optional[int]
    product_name: Optional[str]
    product_code: Optional[str]
    specification: Optional[str]
    quantity: Optional[int]
    unit_price: DecimalType
    total_price: DecimalType
    unit: Optional[str]
    lead_time: Optional[str]
    notes: Optional[str]

class QuotationItemCreateDict(TypedDict, total=False):
    """견적서 아이템 생성용 타입"""
    quotation_id: str  # 필수
    item_number: Optional[int]
    product_name: Optional[str]
    product_code: Optional[str]
    specification: Optional[str]
    quantity: Optional[int]
    unit_price: Optional[DecimalType]
    total_price: Optional[DecimalType]
    unit: Optional[str]
    lead_time: Optional[str]
    notes: Optional[str]

class QuotationItemUpdateDict(TypedDict, total=False):
    """견적서 아이템 수정용 타입 (모든 필드 선택적)"""
    item_number: Optional[int]
    product_name: Optional[str]
    product_code: Optional[str]
    specification: Optional[str]
    quantity: Optional[int]
    unit_price: Optional[DecimalType]
    total_price: Optional[DecimalType]
    unit: Optional[str]
    lead_time: Optional[str]
    notes: Optional[str]

class QuotationSearchDict(TypedDict, total=False):
    """견적서 검색용 타입"""
    quotation_id: Optional[str]
    customer_id: Optional[str]
    quotation_number: Optional[str]
    status: Optional[str]
    project_name: Optional[str]
    sales_rep_name: Optional[str]