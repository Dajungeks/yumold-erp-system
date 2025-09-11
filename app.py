# -*- coding: utf-8 -*-
import streamlit as st

# Streamlit 페이지 설정 (가장 먼저 호출되어야 함)
st.set_page_config(
    page_title="ERP 시스템",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

import os
import json
from datetime import datetime
import sys

# 환경 변수 강제 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LC_ALL'] = 'C.UTF-8' 
os.environ['LANG'] = 'C.UTF-8'

# 세션 상태 초기화 함수 정의 (호출은 나중에)
def initialize_session_state():
    """세션 상태를 초기화합니다."""
    defaults = {
        'logged_in': False,
        'user_id': None,
        'user_type': None,
        'access_level': None,
        'user_permissions': {},
        'language': 'ko',
        'selected_system': 'dashboard',
        'language_changed': False,
        'language_just_changed': False,
        'managers_cache': {}
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ---- 캐시 리소스: 견적 매니저 ----
@st.cache_resource
def get_quotation_manager_cached():
    return get_quotation_manager()

# 지연 로딩 UI 구성
@st.cache_resource
def load_ui_config():
    try:
        from config_files.ui_config import (
            is_ui_locked, 
            get_submenu_config, 
            get_menu_layout, 
            get_submenu_styles,
            SIDEBAR_MENU_STRUCTURE
        )
        return {
            'is_ui_locked': is_ui_locked,
            'get_submenu_config': get_submenu_config,
            'get_menu_layout': get_menu_layout,
            'get_submenu_styles': get_submenu_styles,
            'SIDEBAR_MENU_STRUCTURE': SIDEBAR_MENU_STRUCTURE
        }
    except ImportError:
        return None

# 매니저 팩토리 지연 로딩
@st.cache_resource
def load_database_config():
    """데이터베이스 설정만 필요할 때 로드"""
    try:
        from config.database_config import (
            ManagerFactory, 
            DatabaseConfig, 
            get_employee_manager,
            get_customer_manager, 
            get_quotation_manager,
            get_order_manager,
            get_product_manager,
            get_supplier_manager,
            get_auth_manager,
            get_approval_manager,
            get_database_status,
            # 보조 매니저들
            get_cash_flow_manager,
            get_inventory_manager,
            get_shipping_manager,
            get_invoice_manager,
            get_business_process_manager,
            get_expense_request_manager,
            get_vacation_manager,
            get_sales_product_manager,
            get_finished_product_manager,
            get_cash_transaction_manager,
            get_master_product_manager,
            get_notice_manager,
            get_exchange_rate_manager,
            get_system_config_manager,
            get_product_code_manager,
            get_work_status_manager,
            get_weekly_report_manager,
            get_monthly_sales_manager,
            get_note_manager
        )
        return {
            'get_employee_manager': get_employee_manager,
            'get_customer_manager': get_customer_manager,
            'get_quotation_manager': get_quotation_manager,
            'get_order_manager': get_order_manager,
            'get_product_manager': get_product_manager,
            'get_supplier_manager': get_supplier_manager,
            'get_auth_manager': get_auth_manager,
            'get_approval_manager': get_approval_manager,
            'get_database_status': get_database_status,
            'get_cash_flow_manager': get_cash_flow_manager,
            'get_inventory_manager': get_inventory_manager,
            'get_shipping_manager': get_shipping_manager,
            'get_invoice_manager': get_invoice_manager,
            'get_business_process_manager': get_business_process_manager,
            'get_expense_request_manager': get_expense_request_manager,
            'get_vacation_manager': get_vacation_manager,
            'get_sales_product_manager': get_sales_product_manager,
            'get_finished_product_manager': get_finished_product_manager,
            'get_cash_transaction_manager': get_cash_transaction_manager,
            'get_master_product_manager': get_master_product_manager,
            'get_notice_manager': get_notice_manager,
            'get_exchange_rate_manager': get_exchange_rate_manager,
            'get_system_config_manager': get_system_config_manager,
            'get_product_code_manager': get_product_code_manager,
            'get_work_status_manager': get_work_status_manager,
            'get_weekly_report_manager': get_weekly_report_manager,
            'get_monthly_sales_manager': get_monthly_sales_manager,
            'get_note_manager': get_note_manager
        }
    except ImportError as e:
        st.error(f"데이터베이스 설정 로드 실패: {e}")
        return {}

def get_manager(manager_type):
    """필요한 매니저만 지연 로딩"""
    cache_key = f"{manager_type}_manager"
    
    if cache_key in st.session_state.managers_cache:
        return st.session_state.managers_cache[cache_key]
    
    db_config = load_database_config()
    get_func_name = f'get_{manager_type}_manager'
    
    if get_func_name in db_config:
        try:
            manager = db_config[get_func_name]()
            st.session_state.managers_cache[cache_key] = manager
            return manager
        except Exception as e:
            st.warning(f"{manager_type} 매니저 로드 실패: {e}")
            return None
    return None

# 노트 위젯 지연 로딩
def show_page_note_widget():
    """페이지 노트 위젯 지연 로딩"""
    try:
        from components.note_widget import show_page_note_widget as widget_func
        return widget_func()
    except ImportError:
        return None

# 레거시 매니저들 필요할 때만 임포트하도록 함수화
def get_database_manager():
    if 'database_manager' not in st.session_state.managers_cache:
        try:
            from managers.legacy.database_manager import DatabaseManager
            st.session_state.managers_cache['database_manager'] = DatabaseManager()
        except ImportError:
            return None
    return st.session_state.managers_cache.get('database_manager')

def get_pdf_language_manager():
    if 'pdf_language_manager' not in st.session_state.managers_cache:
        try:
            from managers.legacy.pdf_language_manager import PDFLanguageManager
            st.session_state.managers_cache['pdf_language_manager'] = PDFLanguageManager()
        except ImportError:
            return None
    return st.session_state.managers_cache.get('pdf_language_manager')

def get_backup_manager():
    if 'backup_manager' not in st.session_state.managers_cache:
        try:
            from managers.backup_manager import BackupManager as NewBackupManager
            st.session_state.managers_cache['backup_manager'] = NewBackupManager()
        except ImportError:
            return None
    return st.session_state.managers_cache.get('backup_manager')

def get_migration_manager():
    if 'migration_manager' not in st.session_state.managers_cache:
        try:
            from managers.legacy.migration_manager import MigrationManager
            st.session_state.managers_cache['migration_manager'] = MigrationManager()
        except ImportError:
            return None
    return st.session_state.managers_cache.get('migration_manager')

def get_contract_manager():
    if 'contract_manager' not in st.session_state.managers_cache:
        try:
            from managers.legacy.contract_manager import ContractManager
            st.session_state.managers_cache['contract_manager'] = ContractManager()
        except ImportError:
            return None
    return st.session_state.managers_cache.get('contract_manager')

# CSV 기반 매니저들
def get_supply_product_manager():
    if 'supply_product_manager' not in st.session_state.managers_cache:
        try:
            from managers.legacy.supply_product_manager import SupplyProductManager
            st.session_state.managers_cache['supply_product_manager'] = SupplyProductManager()
        except ImportError:
            return None
    return st.session_state.managers_cache.get('supply_product_manager')

def get_product_category_config_manager():
    if 'product_category_config_manager' not in st.session_state.managers_cache:
        try:
            from managers.legacy.product_category_config_manager import ProductCategoryConfigManager
            st.session_state.managers_cache['product_category_config_manager'] = ProductCategoryConfigManager()
        except ImportError:
            return None
    return st.session_state.managers_cache.get('product_category_config_manager')

def get_manual_exchange_rate_manager():
    if 'manual_exchange_rate_manager' not in st.session_state.managers_cache:
        try:
            from managers.legacy.manual_exchange_rate_manager import ManualExchangeRateManager
            st.session_state.managers_cache['manual_exchange_rate_manager'] = ManualExchangeRateManager()
        except ImportError:
            return None
    return st.session_state.managers_cache.get('manual_exchange_rate_manager')

# 언어 관리 최적화
@st.cache_resource
def get_language_manager():
    try:
        from managers.legacy.advanced_language_manager import AdvancedLanguageManager
        return AdvancedLanguageManager()
    except ImportError:
        return None

@st.cache_data(ttl=3600)
def load_language(lang_code):
    """언어 파일을 로드합니다."""
    file_paths = [
        f'locales/{lang_code}.json',
        f'languages/{lang_code}.json',
        'locales/ko.json',
        'languages/ko.json'
    ]
    
    for path in file_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            continue
    return {}

def get_text(key, lang_dict=None, **kwargs):
    """언어 딕셔너리에서 텍스트를 가져옵니다."""
    lang_manager = get_language_manager()
    
    if lang_manager and lang_dict is None:
        current_lang = st.session_state.get('language', 'ko')
        lang_manager.set_language(current_lang)
        return lang_manager.get_text(key, **kwargs)
    
    if lang_dict:
        text = lang_dict.get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, ValueError):
                return text
        return text
    return key

def check_access_level(required_level, user_access_level):
    """권한 레벨 확인 함수"""
    access_hierarchy = {
        'user': 1,
        'admin': 2,
        'ceo': 3,
        'master': 4
    }
    
    user_level = access_hierarchy.get(user_access_level, 0)
    required = access_hierarchy.get(required_level, 0)
    
    return user_level >= required

def check_menu_access(menu_key, user_access_level):
    """메뉴별 접근 권한 확인"""
    menu_permissions = {
        'dashboard': 'user',
        'work_report_management': 'user',
        'work_status_management': 'user',
        'personal_status': 'user',
        'exchange_rate_management': 'user',
        'system_guide': 'user',
        'sales_management': 'user',
        'product_management': 'user',
        'admin_management': 'admin',
        'executive_management': 'ceo',
        'customer_management': 'user',
        'quotation_management': 'user',
        'order_management': 'user',
        'shipping_management': 'user',
        'monthly_sales_management': 'user',
        'business_process_v2_management': 'user',
        'supplier_management': 'user',
        'master_product_management': 'user',
        'sales_product_management': 'user',
        'supply_product_management': 'user',
        'hr_product_registration': 'user',
        'expense_request_management': 'admin',
        'cash_flow_management': 'admin',
        'employee_management': 'admin',
        'asset_management': 'admin',
        'contract_management': 'admin',
        'schedule_task_management': 'admin',
        'purchase_management': 'admin',
        'approval_management': 'ceo',
        'pdf_design_management': 'ceo',
        'system_config_management': 'ceo',
        'backup_management': 'ceo',
        'language_management': 'ceo'
    }
    
    required_level = menu_permissions.get(menu_key, 'user')
    return check_access_level(required_level, user_access_level)

def show_language_selector(location="header"):
    lang_manager = get_language_manager()
    if not lang_manager:
        return

    current_lang = st.session_state.get('language', 'ko')

    language_options = {'ko': '🇰🇷 한국어', 'en': '🇺🇸 English', 'vi': '🇻🇳 Tiếng Việt'}

    # ✅ fallback 인자 호환 처리
    try:
        select_text = lang_manager.get_text("language_selector", fallback="Language")
    except TypeError:
        select_text = lang_manager.get_text("language_selector") or "Language"

    selected_lang = st.selectbox(
        select_text,
        options=list(language_options.keys()),
        format_func=lambda x: language_options[x],
        index=list(language_options.keys()).index(current_lang),
        key=f"language_selector_{location}"
    )

    if selected_lang != current_lang:
        st.session_state.language = selected_lang
        lang_manager.set_language(selected_lang)
        st.session_state.language_just_changed = True
        st.rerun()
def show_download_button():
    """ZIP 파일 다운로드 버튼을 표시합니다."""
    zip_file = "yumold_erp_system_complete.zip"
    if os.path.exists(zip_file):
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📦 시스템 백업")
        
        file_size = os.path.getsize(zip_file) / (1024 * 1024)
        st.sidebar.markdown(f"**파일 크기:** {file_size:.1f}MB")
        
        with open(zip_file, "rb") as file:
            st.sidebar.download_button(
                label="⬇️ 전체 시스템 다운로드",
                data=file,
                file_name=zip_file,
                mime="application/zip",
                help="ERP 시스템 전체 + PostgreSQL DB 백업",
                use_container_width=True
            )

def initialize_managers():
    """매니저 초기화 - 지연 로딩으로 변경"""
    if 'managers_initialized' not in st.session_state:
        st.session_state.managers_initialized = True
    # 실제 매니저들은 필요할 때 get_manager() 함수로 로드됨

# 기존 매니저 함수들을 지연 로딩 버전으로 래핑
def get_employee_manager():
    return get_manager('employee')

def get_customer_manager():
    return get_manager('customer')

def get_quotation_manager():
    return get_manager('quotation')

def get_order_manager():
    return get_manager('order')

def get_product_manager():
    return get_manager('product')

def get_supplier_manager():
    return get_manager('supplier')

def get_auth_manager():
    return get_manager('auth')

def get_approval_manager():
    return get_manager('approval')

def get_cash_flow_manager():
    return get_manager('cash_flow')

def get_inventory_manager():
    return get_manager('inventory')

def get_shipping_manager():
    return get_manager('shipping')

def get_invoice_manager():
    return get_manager('invoice')

def get_business_process_manager():
    return get_manager('business_process')

def get_expense_request_manager():
    return get_manager('expense_request')

def get_vacation_manager():
    return get_manager('vacation')

def get_sales_product_manager():
    return get_manager('sales_product')

def get_finished_product_manager():
    return get_manager('finished_product')

def get_cash_transaction_manager():
    return get_manager('cash_transaction')

def get_master_product_manager():
    return get_manager('master_product')

def get_notice_manager():
    return get_manager('notice')

def get_exchange_rate_manager():
    return get_manager('exchange_rate')

def get_system_config_manager():
    return get_manager('system_config')

def get_product_code_manager():
    return get_manager('product_code')

def get_work_status_manager():
    return get_manager('work_status')

def get_weekly_report_manager():
    return get_manager('weekly_report')

def get_monthly_sales_manager():
    return get_manager('monthly_sales')

def get_note_manager():
    return get_manager('note')

def get_database_status():
    db_config = load_database_config()
    if 'get_database_status' in db_config:
        return db_config['get_database_status']()
    return None

# 백업 스케줄러 지연 로딩
def get_backup_scheduler():
    if 'backup_scheduler' not in st.session_state.managers_cache:
        try:
            from scripts.backup_scheduler import backup_scheduler
            st.session_state.managers_cache['backup_scheduler'] = backup_scheduler
        except ImportError:
            return None
    return st.session_state.managers_cache.get('backup_scheduler')

# 로그인 UI
def show_login_page(lang_dict):
    """로그인 페이지를 표시합니다."""
    # 상단 언어 선택기를 더 좋은 위치에 배치
    st.markdown('<div style="text-align: right; margin-bottom: 20px;">', unsafe_allow_html=True)
    show_language_selector()
    st.markdown('</div>', unsafe_allow_html=True)
    
    app_title = get_text("app_title", lang_dict)
    st.title(f"🏢 {app_title}")
    st.markdown("---")
    
    login_type_text = get_text("login_type_select", lang_dict)
    employee_login_text = get_text("employee_login", lang_dict)
    master_login_text = get_text("master_login", lang_dict)
    login_type = st.selectbox(login_type_text, [employee_login_text, master_login_text])
    
    if login_type == employee_login_text:
        st.subheader(f"👤 {employee_login_text}")
        
        with st.form("employee_login_form"):
            user_id_text = get_text("employee_id", lang_dict)
            password_text = get_text("password", lang_dict)
            login_button_text = get_text("login", lang_dict)
            
            user_id = st.text_input(user_id_text)
            password = st.text_input(password_text, type="password")
            login_submitted = st.form_submit_button(login_button_text, type="primary")
            
        if login_submitted:
            if user_id and password:
                # 직원 인증 로직 (튜플 반환 처리)
                auth_result = st.session_state.auth_manager.authenticate_employee(user_id, password)
                
                if isinstance(auth_result, tuple) and auth_result[0]:
                    success, employee_info = auth_result
                    
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_id
                    st.session_state.user_type = employee_info.get('user_type', 'employee')
                    st.session_state.login_type = "employee"
                    
                    # 권한 정보 설정
                    st.session_state.access_level = employee_info.get('access_level', 'user')
                    st.session_state.user_name = employee_info.get('name', user_id)
                    st.session_state.user_position = employee_info.get('position', '')
                    st.session_state.user_department = employee_info.get('department', '')
                    
                    # 법인장인 경우 특별 처리
                    if st.session_state.user_position == '법인장' or st.session_state.access_level == 'master':
                        st.session_state.user_type = 'master'
                        st.session_state.access_level = 'master'
                    
                    success_msg = get_text("login_success", lang_dict) if 'login_success' in lang_dict else f"로그인 성공! 권한: {st.session_state.access_level}"
                    info_msg = get_text("login_complete", lang_dict) if 'login_complete' in lang_dict else "로그인이 완료되었습니다."
                    st.success(success_msg)
                    st.info(info_msg)
                    st.rerun()
                else:
                    error_msg = get_text("login_failed", lang_dict)
                    st.error(error_msg)
            else:
                warning_msg = get_text("input_credentials", lang_dict)
                st.warning(warning_msg)
    
    elif login_type == master_login_text:  # 마스터 로그인
        st.subheader(f"🔐 {master_login_text}")
        
        with st.form("master_login_form"):
            master_password_text = get_text("master_password", lang_dict)
            master_login_button_text = get_text("login", lang_dict)
            password = st.text_input(master_password_text, type="password")
            master_login_submitted = st.form_submit_button(master_login_button_text, type="primary")
            
        if master_login_submitted:
            # 로그인 시도 전 세션 상태 완전 초기화 (보안 강화)
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.user_type = None
            st.session_state.user_role = None
            st.session_state.login_type = None
            st.session_state.access_level = None
            st.session_state.user_permissions = {}
            
            if password:
                # 마스터 인증 로직
                auth_result = st.session_state.auth_manager.authenticate_master(password)
                print(f"[DEBUG] 마스터 인증 시도: 비밀번호='{password}', 결과={auth_result}")  # 디버깅 로그
                print(f"[DEBUG] auth_result 타입: {type(auth_result)}")  # 타입 확인
                
                # PostgreSQL과 SQLite AuthManager 모두 대응
                if isinstance(auth_result, dict) and auth_result.get('success'):
                    # PostgreSQL AuthManager (딕셔너리 반환)
                    st.session_state.logged_in = True
                    st.session_state.user_id = auth_result.get('user_id', 'master')
                    st.session_state.user_type = "master" 
                    st.session_state.user_role = "master"
                    st.session_state.login_type = "master"
                    st.session_state.access_level = "master"
                    # 마스터는 모든 권한 가짐
                    st.session_state.user_permissions = {
                        'can_access_employee_management': True,
                        'can_access_customer_management': True,
                        'can_access_product_management': True,
                        'can_access_supplier_management': True,
                        'can_access_purchase_order_management': True,
                        'can_access_inventory_management': True,
                        'can_access_shipping_management': True,
                        'can_access_approval_management': True,
                        'can_access_monthly_sales_management': True,
                        'can_access_cash_flow_management': True,
                        'can_access_invoice_management': True,
                        'can_access_sales_product_management': True,
                        'can_access_order_management': True,
                        'can_access_exchange_rate_management': True,
                        'can_access_personal_status': True,
                        'can_access_vacation_management': True,
                        'can_delete_data': True
                    }
                    master_success_msg = get_text("master_login_success", lang_dict) if 'master_login_success' in lang_dict else "마스터 로그인 성공!"
                    st.success(master_success_msg)
                    print(f"[DEBUG] PostgreSQL 마스터 로그인 성공: 세션 설정 완료")
                    st.rerun()
                elif isinstance(auth_result, tuple):
                    # SQLite AuthManager (튜플 반환)
                    success, user_info = auth_result
                    if success is True:
                        st.session_state.logged_in = True
                        st.session_state.user_id = "master"
                        st.session_state.user_type = "master" 
                        st.session_state.user_role = "master"
                        st.session_state.login_type = "master"
                        st.session_state.access_level = "master"
                        # 마스터는 모든 권한 가짐
                        st.session_state.user_permissions = {
                            'can_access_employee_management': True,
                            'can_access_customer_management': True,
                            'can_access_product_management': True,
                            'can_access_supplier_management': True,
                            'can_access_purchase_order_management': True,
                            'can_access_inventory_management': True,
                            'can_access_shipping_management': True,
                            'can_access_approval_management': True,
                            'can_access_monthly_sales_management': True,
                            'can_access_cash_flow_management': True,
                            'can_access_invoice_management': True,
                            'can_access_sales_product_management': True,
                            'can_access_order_management': True,
                            'can_access_exchange_rate_management': True,
                            'can_access_personal_status': True,
                            'can_access_vacation_management': True,
                            'can_delete_data': True
                        }
                        master_success_msg = get_text("master_login_success", lang_dict) if 'master_login_success' in lang_dict else "마스터 로그인 성공!"
                        st.success(master_success_msg)
                        print(f"[DEBUG] SQLite 마스터 로그인 성공: 세션 설정 완료")
                        st.rerun()
                    else:
                        master_error_msg = get_text("master_login_failed", lang_dict)
                        st.error(master_error_msg)
                        print(f"[DEBUG] 마스터 로그인 실패: SQLite 인증 실패 {auth_result}")
                elif auth_result is True:
                    # Legacy AuthManager 대응
                    st.session_state.logged_in = True
                    st.session_state.user_id = "master"
                    st.session_state.user_type = "master" 
                    st.session_state.user_role = "master"
                    st.session_state.login_type = "master"
                    st.session_state.access_level = "master"
                    # 마스터는 모든 권한 가짐 (Legacy 대응)
                    st.session_state.user_permissions = {
                        'can_access_employee_management': True,
                        'can_access_customer_management': True,
                        'can_access_product_management': True,
                        'can_access_supplier_management': True,
                        'can_access_purchase_order_management': True,
                        'can_access_inventory_management': True,
                        'can_access_shipping_management': True,
                        'can_access_approval_management': True,
                        'can_access_monthly_sales_management': True,
                        'can_access_cash_flow_management': True,
                        'can_access_invoice_management': True,
                        'can_access_sales_product_management': True,
                        'can_access_order_management': True,
                        'can_access_exchange_rate_management': True,
                        'can_access_personal_status': True,
                        'can_access_vacation_management': True,
                        'can_delete_data': True
                    }
                    master_success_msg = get_text("master_login_success", lang_dict) if 'master_login_success' in lang_dict else "마스터 로그인 성공!"
                    st.success(master_success_msg)
                    print(f"[DEBUG] 마스터 로그인 성공: Legacy 세션 설정 완료")
                else:
                    master_error_msg = get_text("master_login_failed", lang_dict)
                    st.error(master_error_msg)
                    print(f"[DEBUG] 마스터 로그인 실패: 예상치 못한 반환값: {auth_result}")
            else:
                master_warning_msg = get_text("input_master_password", lang_dict)
                st.warning(master_warning_msg)
                print(f"[DEBUG] 마스터 로그인: 비밀번호 미입력")



# 메인 대시보드
def show_dashboard():
    """메인 대시보드를 표시합니다."""
    st.title("📊 대시보드")
    
    # 사용자 정보 표시
    st.sidebar.markdown(f"**사용자:** {st.session_state.user_id}")
    st.sidebar.markdown(f"**권한:** {st.session_state.access_level}")
    
    # 언어 선택기
    show_language_selector("sidebar")
    
    # 로그아웃 버튼
    if st.sidebar.button("로그아웃"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    # 다운로드 버튼
    show_download_button()
    
    # 메인 컨텐츠
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("총 고객 수", "1,234", "12")
    
    with col2:
        st.metric("이번 달 매출", "₩50,000,000", "5.2%")
    
    with col3:
        st.metric("진행중 주문", "45", "-2")
    
    # 최근 활동
    st.subheader("최근 활동")
    st.info("시스템 활동 내역이 여기에 표시됩니다.")

# 메뉴 시스템
def show_menu():
    ui_config = load_ui_config()
    if not ui_config:
        return "dashboard"

    menu_structure = ui_config.get('SIDEBAR_MENU_STRUCTURE', {})
    user_access_level = st.session_state.get('access_level', 'user')

    options, labels = [], {}
    for key, info in menu_structure.items():
        if check_menu_access(key, user_access_level):
            options.append(key)
            labels[key] = info.get('label', key)

    if options:
        selected = st.sidebar.selectbox(
            "메뉴 선택",
            options=options,
            format_func=lambda x: labels.get(x, x),
            index=0
        )
        return selected

    return "dashboard"


# 각 메뉴별 페이지 함수들 (지연 로딩)
def show_customer_management():
    """고객 관리 페이지"""
    st.title("👥 고객 관리")
    customer_manager = get_customer_manager()
    if customer_manager:
        st.success("고객 관리 모듈이 로드되었습니다.")
        # 고객 관리 UI 구현
    else:
        st.error("고객 관리 모듈을 로드할 수 없습니다.")

def show_quotation_management():
    st.title("💰 견적 관리")
    with st.spinner("견적 모듈 로딩 중..."):
        quotation_manager = get_quotation_manager()
    if quotation_manager:
        st.success("견적 관리 모듈이 로드되었습니다.")
    else:
        st.error("견적 관리 모듈을 로드할 수 없습니다.")


def show_product_management():
    """제품 관리 페이지"""
    st.title("📦 제품 관리")
    product_manager = get_product_manager()
    if product_manager:
        st.success("제품 관리 모듈이 로드되었습니다.")
        # 제품 관리 UI 구현
    else:
        st.error("제품 관리 모듈을 로드할 수 없습니다.")

def show_employee_management():
    """직원 관리 페이지"""
    st.title("👨‍💼 직원 관리")
    if not check_menu_access('employee_management', st.session_state.get('access_level')):
        st.error("접근 권한이 없습니다.")
        return
    
    employee_manager = get_employee_manager()
    if employee_manager:
        st.success("직원 관리 모듈이 로드되었습니다.")
        # 직원 관리 UI 구현
    else:
        st.error("직원 관리 모듈을 로드할 수 없습니다.")

def show_backup_management():
    """백업 관리 페이지"""
    st.title("💾 백업 관리")
    if not check_menu_access('backup_management', st.session_state.get('access_level')):
        st.error("접근 권한이 없습니다.")
        return
    
    backup_manager = get_backup_manager()
    if backup_manager:
        st.success("백업 관리 모듈이 로드되었습니다.")
        # 백업 관리 UI 구현
    else:
        st.error("백업 관리 모듈을 로드할 수 없습니다.")

# 메인 애플리케이션 함수
def main():
    """메인 애플리케이션 함수"""
    # 세션 상태 초기화 (st.set_page_config 이후에 호출)
    initialize_session_state()
    
    # 매니저 초기화 (지연 로딩)
    initialize_managers()
    
    # 로그인 체크
    if not st.session_state.get('logged_in', False):
        show_login()
        return
    
    # 메뉴 선택
    selected_menu = show_menu()
    
    # 페이지 라우팅
    if selected_menu == 'dashboard':
        show_dashboard()
    elif selected_menu == 'customer_management':
        show_customer_management()
    elif selected_menu == 'quotation_management':
        show_quotation_management()
    elif selected_menu == 'product_management':
        show_product_management()
    elif selected_menu == 'employee_management':
        show_employee_management()
    elif selected_menu == 'backup_management':
        show_backup_management()
    else:
        st.title(f"📋 {selected_menu}")
        st.info(f"{selected_menu} 페이지가 구현 중입니다.")
    
    # 페이지 노트 위젯
    show_page_note_widget()

# 실행부
if __name__ == "__main__":
    # 메인 애플리케이션 실행
    main()
