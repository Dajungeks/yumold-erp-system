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
    
    # 총무 메뉴 섹션
    'admin_management': {
        'icon': '📋',
        'title_key': 'menu_admin_management',
        'submenu_options': [
            'expense_request_management',
            'cash_flow_management',
            'employee_management',
            'asset_management',
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
        return list(SIDEBAR_MENU_STRUCTURE.keys())
    elif access_level == 'ceo':
        return [
            'dashboard', 'work_report_management', 'work_status_management', 
            'personal_status', 'exchange_rate_management', 'sales_management',
            'product_management', 'executive_management', 'admin_management', 'system_guide'
        ]
    elif access_level == 'admin':
        return [
            'dashboard', 'work_report_management', 'work_status_management',
            'personal_status', 'exchange_rate_management', 'sales_management',
            'product_management', 'admin_management', 'system_guide'
        ]
    else:
        return [
            'dashboard', 'work_report_management', 'work_status_management',
            'personal_status', 'exchange_rate_management', 'sales_management',
            'product_management', 'system_guide'
        ]

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
    return {
        'column_ratio': [1, 6, 1],
        'icon_alignment': 'left',
        'text_alignment': 'center',
        'current_menu_type': 'primary',
        'other_menu_type': 'default'
    }

def get_submenu_styles():
    """서브메뉴 스타일 설정을 반환합니다."""
    return {
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
