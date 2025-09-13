# -*- coding: utf-8 -*-
"""
고객 관련 타입 정의
"""

from typing import TypedDict, Optional
from .base_types import BaseRecord, DateTimeType

class CustomerDict(BaseRecord):
    """고객 정보 완전 타입"""
    customer_id: str
    company_name: str
    contact_person: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    country: Optional[str]
    city: Optional[str]
    address: Optional[str]
    business_type: Optional[str]
    status: str  # 'active', 'inactive', 'deleted'
    notes: Optional[str]

class CustomerCreateDict(TypedDict, total=False):
    """고객 생성용 타입"""
    company_name: str  # 필수
    contact_person: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    country: Optional[str]
    city: Optional[str]
    address: Optional[str]
    business_type: Optional[str]
    status: Optional[str]
    notes: Optional[str]

class CustomerUpdateDict(TypedDict, total=False):
    """고객 수정용 타입 (모든 필드 선택적)"""
    company_name: Optional[str]
    contact_person: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    country: Optional[str]
    city: Optional[str]
    address: Optional[str]
    business_type: Optional[str]
    status: Optional[str]
    notes: Optional[str]

class CustomerSearchDict(TypedDict, total=False):
    """고객 검색용 타입"""
    customer_id: Optional[str]
    company_name: Optional[str]
    country: Optional[str]
    city: Optional[str]
    business_type: Optional[str]
    status: Optional[str]