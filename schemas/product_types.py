# -*- coding: utf-8 -*-
"""
제품 관련 타입 정의
"""

from typing import TypedDict, Optional
from .base_types import BaseRecord, DecimalType, CurrencyType

class ProductDict(BaseRecord):
    """제품 정보 완전 타입"""
    product_id: str
    product_code: str
    product_name: str
    category: Optional[str]
    subcategory: Optional[str]
    description: Optional[str]
    unit_price: DecimalType
    currency: CurrencyType  # default: 'VND'
    status: str  # 'active', 'inactive', 'deleted'

class ProductCreateDict(TypedDict, total=False):
    """제품 생성용 타입"""
    product_code: str  # 필수
    product_name: str  # 필수
    category: Optional[str]
    subcategory: Optional[str]
    description: Optional[str]
    unit_price: Optional[DecimalType]
    currency: Optional[CurrencyType]
    status: Optional[str]

class ProductUpdateDict(TypedDict, total=False):
    """제품 수정용 타입 (모든 필드 선택적)"""
    product_code: Optional[str]
    product_name: Optional[str]
    category: Optional[str]
    subcategory: Optional[str]
    description: Optional[str]
    unit_price: Optional[DecimalType]
    currency: Optional[CurrencyType]
    status: Optional[str]

class ProductSearchDict(TypedDict, total=False):
    """제품 검색용 타입"""
    product_id: Optional[str]
    product_code: Optional[str]
    product_name: Optional[str]
    category: Optional[str]
    subcategory: Optional[str]
    status: Optional[str]