# -*- coding: utf-8 -*-
"""
휴가 관련 타입 정의
"""

from typing import TypedDict, Optional
from .base_types import BaseRecord, DateType, DateTimeType

class VacationRequestDict(BaseRecord):
    """휴가 신청 정보 완전 타입"""
    request_id: str
    employee_id: str
    employee_name: Optional[str]
    department: Optional[str]
    position: Optional[str]
    vacation_type: str
    start_date: DateType
    end_date: DateType
    total_days: int  # default: 0
    business_days: int  # default: 0
    reason: Optional[str]
    emergency_contact: Optional[str]
    emergency_phone: Optional[str]
    handover_person: Optional[str]
    handover_details: Optional[str]
    status: str  # 'pending', 'approved', 'rejected'
    approver_id: Optional[str]
    approver_name: Optional[str]
    approval_date: DateType
    approval_comments: Optional[str]
    rejection_reason: Optional[str]
    submitted_date: DateTimeType

class VacationRequestCreateDict(TypedDict, total=False):
    """휴가 신청 생성용 타입"""
    employee_id: str  # 필수
    vacation_type: str  # 필수
    start_date: DateType  # 필수
    end_date: DateType  # 필수
    employee_name: Optional[str]
    department: Optional[str]
    position: Optional[str]
    total_days: Optional[int]
    business_days: Optional[int]
    reason: Optional[str]
    emergency_contact: Optional[str]
    emergency_phone: Optional[str]
    handover_person: Optional[str]
    handover_details: Optional[str]
    status: Optional[str]

class VacationRequestUpdateDict(TypedDict, total=False):
    """휴가 신청 수정용 타입 (모든 필드 선택적)"""
    vacation_type: Optional[str]
    start_date: Optional[DateType]
    end_date: Optional[DateType]
    total_days: Optional[int]
    business_days: Optional[int]
    reason: Optional[str]
    emergency_contact: Optional[str]
    emergency_phone: Optional[str]
    handover_person: Optional[str]
    handover_details: Optional[str]
    status: Optional[str]
    approver_id: Optional[str]
    approver_name: Optional[str]
    approval_date: Optional[DateType]
    approval_comments: Optional[str]
    rejection_reason: Optional[str]

class VacationBalanceDict(BaseRecord):
    """휴가 잔여일수 정보 완전 타입"""
    balance_id: str
    employee_id: str
    year: int
    vacation_type: str
    allocated_days: float  # default: 0
    used_days: float  # default: 0
    remaining_days: float  # default: 0
    carried_over: float  # default: 0
    expires_date: DateType

class VacationBalanceCreateDict(TypedDict, total=False):
    """휴가 잔여일수 생성용 타입"""
    employee_id: str  # 필수
    year: int  # 필수
    vacation_type: str  # 필수
    allocated_days: Optional[float]
    used_days: Optional[float]
    remaining_days: Optional[float]
    carried_over: Optional[float]
    expires_date: Optional[DateType]

class VacationBalanceUpdateDict(TypedDict, total=False):
    """휴가 잔여일수 수정용 타입 (모든 필드 선택적)"""
    allocated_days: Optional[float]
    used_days: Optional[float]
    remaining_days: Optional[float]
    carried_over: Optional[float]
    expires_date: Optional[DateType]

class VacationSummaryDict(TypedDict):
    """휴가 요약 정보 타입 (아키텍트 요청사항)"""
    employee_id: str
    employee_name: str
    department: Optional[str]
    total_allocated: float
    total_used: float
    total_remaining: float
    pending_requests: int
    approved_requests: int
    vacation_types: list[str]