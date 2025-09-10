"""
UI 구성 고정 설정 파일
사이드바 메뉴 구조와 서브메뉴 옵션을 고정합니다.
"""

# UI 구조 고정 설정
UI_LOCKED = True

# 사이드바 메뉴 구조 고정 (번역 키 사용)
SIDEBAR_MENU_STRUCTURE = {
    # 메인 메뉴들
    'dashboard': {
        'icon': '🏠',
        'title_key': 'menu_dashboard',
        'submenu_options': []
    },
    'work_report_management': {
        'icon': '📝',
        'title_key': 'menu_work_report',
        'submenu_options': []
    },

    'work_status_management': {
        'icon': '📋',
        'title_key': 'menu_work_status',
        'submenu_options': []
    },
    'personal_status': {
        'icon': '👤',
        'title_key': 'menu_personal',
        'submenu_options': []
    },
    'exchange_rate_management': {
        'icon': '💱',
        'title_key': 'menu_exchange_rate',
        'submenu_options': []
    },
    
    # 영업 관리 섹션
    'sales_management': {
        'icon': '💼',
        'title_key': 'menu_sales_management',
        'submenu_options': [
            'customer_management',
            'quotation_management', 
            'order_management',
            'outsourcing_supply_management',
            'shipping_management',
            'monthly_sales_management',
            'business_process_v2_management',
            'supplier_management'
        ]
    },
    
    # 제품관리 섹션
    'product_management': {
        'icon': '📦',
        'title_key': 'menu_product_management',
        'submenu_options': [
            'master_product_management',
            'sales_product_management',
            'supply_product_management',
            'hr_product_registration'
        ]
    },
    
    # 법인장 메뉴 섹션
    'executive_management': {
        'icon': '👔',
        'title_key': 'menu_executive_management',
        'submenu_options': [
            'approval_management',
            'pdf_design_management',
            'system_config_management',
            'backup_management',
            'language_management'
        ]
    },
    

    
    # 총무 메뉴 섹션 (지출요청서 작성, 진행상태 확인)
    'admin_management': {
        'icon': '📋',
        'title_key': 'menu_admin_management',
        'submenu_options': [
            'expense_request_management',  # 지출요청서 작성 및 진행상태
            'cash_flow_management',
            'employee_management',
            'asset_management',  # 자산 관리 추가
            'contract_management',
            'schedule_task_management',
            'purchase_management'
        ]
    },
    
    
    # 시스템 가이드
    'system_guide': {
        'icon': '📚',
        'title_key': 'menu_system_guide',
        'submenu_options': []
    }
}

def get_allowed_menus(access_level):
    """사용자 권한에 따른 허용 메뉴 목록 반환"""
    if access_level == 'master':
        # 마스터는 모든 메뉴 접근 가능
        return list(SIDEBAR_MENU_STRUCTURE.keys())
    elif access_level == 'ceo':
        # 법인장은 executive_management 포함
        return [
            'dashboard', 'work_report_management', 'work_status_management', 
            'personal_status', 'exchange_rate_management', 'sales_management',
            'product_management', 'executive_management', 'admin_management', 'system_guide'
        ]
    elif access_level == 'admin':
        # 총무는 admin_management 포함, executive_management 제외
        return [
            'dashboard', 'work_report_management', 'work_status_management',
            'personal_status', 'exchange_rate_management', 'sales_management',
            'product_management', 'admin_management', 'system_guide'
        ]
    else:  # 'user' 또는 기타
        # 일반 직원은 기본 메뉴만
        return [
            'dashboard', 'work_report_management', 'work_status_management',
            'personal_status', 'exchange_rate_management', 'sales_management',
            'product_management', 'system_guide'
        ]

# 개별 페이지 정의 (서브메뉴용)
INDIVIDUAL_PAGES = {
    'customer_management': {
        'icon': '👥',
        'title_key': 'menu_customer'
    },
    'quotation_management': {
        'icon': '📋', 
        'title_key': 'menu_quotation'
    },
    'order_management': {
        'icon': '📦',
        'title_key': 'menu_order'
    },
    'outsourcing_supply_management': {
        'icon': '🏭',
        'title_key': 'menu_outsourcing_supply'
    },
    'shipping_management': {
        'icon': '🚚',
        'title_key': 'menu_shipping'
    },
    'monthly_sales_management': {
        'icon': '📊',
        'title_key': 'menu_monthly_sales'
    },
    'business_process_v2_management': {
        'icon': '🔄',
        'title_key': 'menu_business_process'
    },
    'supplier_management': {
        'icon': '🏢',
        'title_key': 'menu_supplier'
    },
    'master_product_management': {
        'icon': '🔧',
        'title_key': 'menu_master_product'
    },
    'sales_product_management': {
        'icon': '💰',
        'title_key': 'menu_sales_product'
    },
    'supply_product_management': {
        'icon': '⚙️',
        'title_key': 'menu_supply_product'
    },
    'approval_management': {
        'icon': '✅',
        'title_key': 'menu_approval'
    },
    'pdf_design_management': {
        'icon': '📄',
        'title_key': 'menu_pdf_design'
    },
    'system_config_management': {
        'icon': '⚙️',
        'title_key': 'menu_system_config'
    },
    'system_settings': {
        'icon': '🔧',
        'title_key': 'menu_system_settings'
    },
    'cash_flow_management': {
        'icon': '💸',
        'title_key': 'menu_cash_flow'
    },
    'employee_management': {
        'icon': '👨‍💼',
        'title_key': 'menu_employee'
    },
    'hr_product_registration': {
        'icon': '🔥',
        'title_key': 'menu_hr_product_registration'
    },
    'contract_management': {
        'icon': '📝',
        'title_key': 'menu_contract_management'
    },
    'expense_request_management': {
        'icon': '💰',
        'title_key': 'menu_expense_request'
    },
    'backup_management': {
        'icon': '💾',
        'title_key': 'menu_backup'
    },
    'language_management': {
        'icon': '🌍',
        'title_key': 'menu_language'
    },
    'schedule_task_management': {
        'icon': '📅',
        'title_key': 'menu_schedule_task'
    },

    'asset_management': {
        'icon': '🏢',
        'title_key': 'menu_asset'
    },
    'purchase_management': {
        'icon': '🛒',
        'title_key': 'menu_purchase'
    }
}

# 메뉴 버튼 레이아웃 고정
MENU_BUTTON_LAYOUT = {
    'column_ratio': [1, 6, 1],  # 아이콘:텍스트:여백 비율
    'icon_alignment': 'left',
    'text_alignment': 'center',
    'current_menu_type': 'primary',
    'other_menu_type': 'default'
}

# 서브메뉴 스타일 고정
SUBMENU_STYLES = {
    'main_menu_style': {
        'background_color': '#fff4e6',
        'border_color': '#ff9800',
        'text_color': '#e65100',
        'font_weight': 'bold',
        'font_size': '14px'
    },
    'sub_menu_style': {
        'background_color': '#f3e5f5',
        'border_color': '#9c27b0',
        'text_color': '#6a1b9a',
        'font_size': '13px'
    }
}

def get_submenu_config(system_key):
    """특정 시스템의 서브메뉴 설정을 반환합니다."""
    if UI_LOCKED and system_key in SIDEBAR_MENU_STRUCTURE:
        return SIDEBAR_MENU_STRUCTURE[system_key]
    return None

def is_ui_locked():
    """UI가 잠겨있는지 확인합니다."""
    return UI_LOCKED

def get_menu_layout():
    """메뉴 레이아웃 설정을 반환합니다."""
    return MENU_BUTTON_LAYOUT

def get_submenu_styles():
    """서브메뉴 스타일 설정을 반환합니다."""
    return SUBMENU_STYLES

def get_current_submenu(system_key):
    """현재 선택된 서브메뉴를 반환합니다."""
    import streamlit as st
    submenu_key = f"selected_submenu_{system_key}"
    if submenu_key in st.session_state:
        return st.session_state[submenu_key]
    return None

# 권한 기반 메뉴 표시 설정 (현재 구성된 메뉴 기준)
PERMISSION_MAPPING = {
    'master': {
        'dashboard': True,
        'notice_management': True,
        'work_status_management': True,
        'employee_management': True,
        'personal_status': True,
        'customer_management': True,
        'master_product_management': True,
        'supplier_management': True,
        'sales_product_management': True,
        'quotation_management': True,
        'order_management': True,
        'supply_product_management': True,
        'exchange_rate_management': True,
        'business_process_v2_management': True,
        'shipping_management': True,
        'approval_management': True,
        'cash_flow_management': True,
        'invoice_management': True,
        'inventory_management': True,
        'purchase_order_management': True,
        'monthly_sales_management': True,
        'system_config_management': True,
        'pdf_design_management': True,
        'system_guide': True,
        'system_config': True,
        'admin_management': True,
        'executive_management': True,
        'contract_management': True,
        'expense_request_management': True,
        'schedule_task_management': True,

        'backup_management': True,
        'language_management': True,
    },
    'employee': {
        'dashboard': True,
        'notice_management': True,  # 직원도 게시판 접근 가능
        'work_status_management': True,  # 업무 진행 상태 접근 가능
        'employee_management': False,  # 직원 관리 불가
        'personal_status': True,  # 개인 상태 관리 가능
        'customer_management': True,  # 고객 관리 가능
        'master_product_management': False,  # 마스터 제품 관리 불가
        'supplier_management': False,  # 공급업체 관리 불가
        'sales_product_management': True,  # 판매 제품 관리 가능
        'quotation_management': True,  # 견적 관리 가능
        'order_management': True,  # 주문 관리 가능
        'supply_product_management': False,  # 외주 공급가 관리 불가
        'exchange_rate_management': False,  # 환율 관리 불가
        'business_process_v2_management': True,  # 비즈니스 프로세스 가능
        'shipping_management': True,  # 배송 관리 가능
        'approval_management': False,  # 승인 관리 불가
        'cash_flow_management': False,  # 현금 흐름 관리 불가
        'invoice_management': False,  # 인보이스 관리 불가
        'inventory_management': False,  # 재고 관리 불가
        'purchase_order_management': False,  # 구매 주문 관리 불가
        'monthly_sales_management': False,  # 월별 매출 관리 불가
        'system_config_management': False,  # 시스템 설정 불가
        'pdf_design_management': False,  # PDF 디자인 관리 불가
        'system_guide': True,  # 시스템 가이드 접근 가능
        'system_config': False,  # 시스템 설정 불가
        'admin_management': True,  # 총무 관리 가능
        'executive_management': False,  # 법인장 관리 불가
        'contract_management': True,  # 계약서 관리 가능
        'expense_request_management': True,  # 지출요청서 관리 가능
        'schedule_task_management': True,  # 일정 관리 가능
  # 문서 인쇄 가능
        'backup_management': False,  # 백업 관리 불가
        'language_management': False,  # 언어 관리 불가
    }
}

def get_permission_mapping():
    """권한 매핑을 반환합니다."""
    return PERMISSION_MAPPING

def get_allowed_menus(access_level):
    """사용자 권한에 따른 접근 가능한 메뉴 목록을 반환합니다."""
    EMPLOYEE_ALLOWED_MENUS = [
        'dashboard', 'notice_management', 'work_status_management',
        'personal_status', 'exchange_rate_management', 
        'sales_management', 'product_management', 'admin_management'
    ]
    
    if access_level == "master":
        return list(SIDEBAR_MENU_STRUCTURE.keys())
    else:
        return EMPLOYEE_ALLOWED_MENUS