# -*- coding: utf-8 -*-
"""
직원 관련 타입 정의
"""

from typing import TypedDict, Optional, Union
from .base_types import BaseRecord, DateType, DateTimeType

class EmployeeDict(BaseRecord):
    """직원 정보 완전 타입"""
    employee_id: str
    name: str
    english_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    position: Optional[str]
    department: Optional[str]
    hire_date: DateType
    status: str  # 'active', 'inactive', 'deleted'
    region: Optional[str]
    password: Optional[str]
    gender: str  # '남', '여'
    nationality: str  # default: '한국'
    residence_country: str  # default: '한국'
    city: Optional[str]
    address: Optional[str]
    birth_date: DateType
    salary: int  # default: 0
    salary_currency: str  # default: 'KRW'
    driver_license: str  # default: '없음'
    notes: Optional[str]
    work_status: str  # default: '재직'
    access_level: str  # default: 'user'

class EmployeeCreateDict(TypedDict, total=False):
    """직원 생성용 타입 (필수 필드만 total=True)"""
    name: str  # 필수
    english_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    position: Optional[str]
    department: Optional[str]
    hire_date: DateType
    status: Optional[str]
    region: Optional[str]
    password: Optional[str]
    gender: Optional[str]
    nationality: Optional[str]
    residence_country: Optional[str]
    city: Optional[str]
    address: Optional[str]
    birth_date: DateType
    salary: Optional[int]
    salary_currency: Optional[str]
    driver_license: Optional[str]
    notes: Optional[str]
    work_status: Optional[str]
    access_level: Optional[str]

class EmployeeUpdateDict(TypedDict, total=False):
    """직원 수정용 타입 (모든 필드 선택적)"""
    name: Optional[str]
    english_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    position: Optional[str]
    department: Optional[str]
    hire_date: DateType
    status: Optional[str]
    region: Optional[str]
    password: Optional[str]
    gender: Optional[str]
    nationality: Optional[str]
    residence_country: Optional[str]
    city: Optional[str]
    address: Optional[str]
    birth_date: DateType
    salary: Optional[int]
    salary_currency: Optional[str]
    driver_license: Optional[str]
    notes: Optional[str]
    work_status: Optional[str]
    access_level: Optional[str]

class EmployeeSearchDict(TypedDict, total=False):
    """직원 검색용 타입"""
    employee_id: Optional[str]
    name: Optional[str]
    department: Optional[str]
    position: Optional[str]
    status: Optional[str]
    region: Optional[str]
    work_status: Optional[str]
    access_level: Optional[str]