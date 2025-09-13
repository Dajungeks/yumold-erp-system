# -*- coding: utf-8 -*-
"""
ERP 시스템 타입 정의 모듈
"""

from .base_types import (
    BaseRecord,
    APIResponse,
    PaginatedResponse,
    ErrorResponse,
    SuccessResponse
)

from .employee_types import (
    EmployeeDict,
    EmployeeCreateDict,
    EmployeeUpdateDict,
    EmployeeSearchDict
)

from .customer_types import (
    CustomerDict,
    CustomerCreateDict,
    CustomerUpdateDict,
    CustomerSearchDict
)

from .product_types import (
    ProductDict,
    ProductCreateDict,
    ProductUpdateDict,
    ProductSearchDict
)

from .quotation_types import (
    QuotationDict,
    QuotationCreateDict,
    QuotationUpdateDict,
    QuotationItemDict,
    QuotationItemCreateDict,
    QuotationItemUpdateDict,
    QuotationSearchDict
)

from .vacation_types import (
    VacationRequestDict,
    VacationRequestCreateDict,
    VacationRequestUpdateDict,
    VacationBalanceDict,
    VacationBalanceCreateDict,
    VacationBalanceUpdateDict,
    VacationSummaryDict
)

__all__ = [
    # Base types
    'BaseRecord',
    'APIResponse',
    'PaginatedResponse',
    'ErrorResponse',
    'SuccessResponse',
    
    # Employee types
    'EmployeeDict',
    'EmployeeCreateDict',
    'EmployeeUpdateDict',
    'EmployeeSearchDict',
    
    # Customer types
    'CustomerDict',
    'CustomerCreateDict',
    'CustomerUpdateDict',
    'CustomerSearchDict',
    
    # Product types
    'ProductDict',
    'ProductCreateDict',
    'ProductUpdateDict',
    'ProductSearchDict',
    
    # Quotation types
    'QuotationDict',
    'QuotationCreateDict',
    'QuotationUpdateDict',
    'QuotationItemDict',
    'QuotationItemCreateDict',
    'QuotationItemUpdateDict',
    'QuotationSearchDict',
    
    # Vacation types
    'VacationRequestDict',
    'VacationRequestCreateDict',
    'VacationRequestUpdateDict',
    'VacationBalanceDict',
    'VacationBalanceCreateDict',
    'VacationBalanceUpdateDict',
    'VacationSummaryDict',
]