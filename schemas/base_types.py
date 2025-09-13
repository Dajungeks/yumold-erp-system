# -*- coding: utf-8 -*-
"""
기본 타입 정의
"""

from typing import TypedDict, Optional, Any, List, Dict, Union, Literal
from datetime import datetime, date
from decimal import Decimal

class BaseRecord(TypedDict, total=False):
    """기본 레코드 타입"""
    id: Optional[int]
    created_date: Optional[datetime]
    updated_date: Optional[datetime]

class APIResponse(TypedDict, total=False):
    """API 응답 기본 타입"""
    success: bool
    error: Optional[str]
    message: Optional[str]
    data: Optional[Any]

class SuccessResponse(TypedDict):
    """성공 응답 타입"""
    success: bool  # True
    data: Optional[Any]
    message: Optional[str]

class ErrorResponse(TypedDict):
    """에러 응답 타입"""
    success: bool  # False
    error: str
    message: Optional[str]

class PaginatedResponse(TypedDict, total=False):
    """페이징된 응답 타입"""
    success: bool
    data: List[Any]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool

# 공통 상태 타입
StatusType = Union[Literal["active"], Literal["inactive"], Literal["deleted"], Literal["draft"], Literal["pending"], Literal["approved"], Literal["rejected"]]

# 통화 타입
CurrencyType = Union[Literal["USD"], Literal["VND"], Literal["KRW"], Literal["EUR"], Literal["JPY"]]

# 날짜 타입 (Union for flexibility)
DateType = Union[date, str, None]
DateTimeType = Union[datetime, str, None]

# 숫자 타입 (Union for database compatibility)
DecimalType = Union[Decimal, float, int, str, None]