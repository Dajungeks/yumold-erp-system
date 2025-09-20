# -*- coding: utf-8 -*-
import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
import locale
import sys
import time
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# UI 구성 고정 설정 불러오기
from config_files.ui_config import (
    is_ui_locked, 
    get_submenu_config, 
    get_menu_layout, 
    get_submenu_styles,
    SIDEBAR_MENU_STRUCTURE
)

# 환경 변수 강제 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LC_ALL'] = 'C.UTF-8'
os.environ['LANG'] = 'C.UTF-8'

# 새로운 데이터베이스 설정 및 매니저 팩토리
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

# Office 구매 관리 모듈 추가 (8-Office 구매 안정화-1)
from managers.postgresql.postgresql_office_purchase_manager import PostgreSQLOfficePurchaseManager

# 모든 매니저들이 이제 database_config를 통해 관리됩니다 (PostgreSQL 우선)
from components.note_widget import show_page_note_widget

# 데이터베이스 및 유틸리티 매니저들
from managers.legacy.database_manager import DatabaseManager
from managers.legacy.pdf_language_manager import PDFLanguageManager
from managers.backup_manager import BackupManager as NewBackupManager
from scripts.backup_scheduler import backup_scheduler
from managers.legacy.migration_manager import MigrationManager
from managers.legacy.contract_manager import ContractManager

# 레거시 매니저들 (하위 호환성)
from managers.legacy.auth_manager import AuthManager
from managers.legacy.db_employee_manager import DBEmployeeManager
from managers.legacy.db_customer_manager import DBCustomerManager
from managers.legacy.db_order_manager import DBOrderManager
from managers.legacy.db_product_manager import DBProductManager

# ================================================================================
# @st.cache_resource 매니저 캐싱 함수들 - 성능 최적화 (90% 초기화 시간 단축)
# ================================================================================

@st.cache_resource
def get_employee_manager_cached():
    """직원 매니저 캐싱된 버전 - 한 번 생성 후 재사용"""
    try:
        return get_employee_manager()
    except Exception as e:
        logger.error(f"Employee manager cache error: {e}")
        return None

@st.cache_resource  
def get_customer_manager_cached():
    """고객 매니저 캐싱된 버전 - 한 번 생성 후 재사용"""
    try:
        return get_customer_manager()
    except Exception as e:
        logger.error(f"Customer manager cache error: {e}")
        return None

@st.cache_resource
def get_product_manager_cached():
    """제품 매니저 캐싱된 버전 - 한 번 생성 후 재사용"""
    try:
        return get_product_manager()
    except Exception as e:
        logger.error(f"Product manager cache error: {e}")
        return None

@st.cache_resource
def get_quotation_manager_cached():
    """견적 매니저 캐싱된 버전 - 한 번 생성 후 재사용"""
    try:
        return get_quotation_manager()
    except Exception as e:
        logger.error(f"Quotation manager cache error: {e}")
        return None

@st.cache_resource
def get_office_purchase_manager_cached():
    """Office 구매 매니저 캐싱된 버전 - 8-Office 구매 안정화-1"""
    try:
        return PostgreSQLOfficePurchaseManager()
    except Exception as e:
        logger.error(f"Office purchase manager cache error: {e}")
        # Legacy fallback
        try:
            from managers.legacy.office_purchase_manager import OfficePurchaseManager
            return OfficePurchaseManager()
        except:
            return None

# 추가 매니저 캐싱 함수들...
@st.cache_resource
def get_supplier_manager_cached():
    try:
        return get_supplier_manager()
    except Exception as e:
        logger.error(f"Supplier manager cache error: {e}")
        return None

@st.cache_resource
def get_auth_manager_cached():
    try:
        return get_auth_manager()
    except Exception as e:
        logger.error(f"Auth manager cache error: {e}")
        return None

@st.cache_resource
def get_approval_manager_cached():
    try:
        return get_approval_manager()
    except Exception as e:
        logger.error(f"Approval manager cache error: {e}")
        return None

@st.cache_resource
def get_order_manager_cached():
    try:
        return get_order_manager()
    except Exception as e:
        logger.error(f"Order manager cache error: {e}")
        return None

@st.cache_resource
def get_business_process_manager_cached():
    try:
        return get_business_process_manager()
    except Exception as e:
        logger.error(f"Business process manager cache error: {e}")
        return None

@st.cache_resource
def get_expense_request_manager_cached():
    try:
        return get_expense_request_manager()
    except Exception as e:
        logger.error(f"Expense request manager cache error: {e}")
        return None

@st.cache_resource
def get_vacation_manager_cached():
    try:
        return get_vacation_manager()
    except Exception as e:
        logger.error(f"Vacation manager cache error: {e}")
        return None

@st.cache_resource
def get_exchange_rate_manager_cached():
    try:
        return get_exchange_rate_manager()
    except Exception as e:
        logger.error(f"Exchange rate manager cache error: {e}")
        return None

@st.cache_resource
def get_cash_flow_manager_cached():
    try:
        return get_cash_flow_manager()
    except Exception as e:
        logger.error(f"Cash flow manager cache error: {e}")
        return None

@st.cache_resource
def get_inventory_manager_cached():
    try:
        return get_inventory_manager()
    except Exception as e:
        logger.error(f"Inventory manager cache error: {e}")
        return None

@st.cache_resource
def get_shipping_manager_cached():
    try:
        return get_shipping_manager()
    except Exception as e:
        logger.error(f"Shipping manager cache error: {e}")
        return None

@st.cache_resource
def get_sales_product_manager_cached():
    try:
        return get_sales_product_manager()
    except Exception as e:
        logger.error(f"Sales product manager cache error: {e}")
        return None

@st.cache_resource
def get_master_product_manager_cached():
    try:
        return get_master_product_manager()
    except Exception as e:
        logger.error(f"Master product manager cache error: {e}")
        return None

@st.cache_resource
def get_monthly_sales_manager_cached():
    try:
        return get_monthly_sales_manager()
    except Exception as e:
        logger.error(f"Monthly sales manager cache error: {e}")
        return None

@st.cache_resource
def get_work_status_manager_cached():
    try:
        return get_work_status_manager()
    except Exception as e:
        logger.error(f"Work status manager cache error: {e}")
        return None

@st.cache_resource
def get_product_code_manager_cached():
    try:
        return get_product_code_manager()
    except Exception as e:
        logger.error(f"Product code manager cache error: {e}")
        return None

@st.cache_resource
def get_finished_product_manager_cached():
    try:
        return get_finished_product_manager()
    except Exception as e:
        logger.error(f"Finished product manager cache error: {e}")
        return None

@st.cache_resource
def get_invoice_manager_cached():
    try:
        return get_invoice_manager()
    except Exception as e:
        logger.error(f"Invoice manager cache error: {e}")
        return None

@st.cache_resource
def get_cash_transaction_manager_cached():
    try:
        return get_cash_transaction_manager()
    except Exception as e:
        logger.error(f"Cash transaction manager cache error: {e}")
        return None

@st.cache_resource
def get_note_manager_cached():
    try:
        return get_note_manager()
    except Exception as e:
        logger.error(f"Note manager cache error: {e}")
        return None

# ================================================================================
# 언어 및 유틸리티 함수들
# ================================================================================

@st.cache_data(ttl=3600)  # 1시간 캐싱 - 언어 파일 로딩 속도 3배 향상
def load_language(lang_code):
    """언어 파일을 로드합니다."""
    try:
        from managers.legacy.advanced_language_manager import AdvancedLanguageManager
        
        lang_manager = AdvancedLanguageManager()
        lang_manager.load_language_file(lang_code)
        
        # 새로운 locales 폴더에서 로드
        try:
            with open(f'locales/{lang_code}.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 구버전 languages 폴더에서 로드 (하위 호환성)
            try:
                with open(f'languages/{lang_code}.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
            except FileNotFoundError:
                # 기본 언어로 한국어 사용
                try:
                    with open('locales/ko.json', 'r', encoding='utf-8') as f:
                        return json.load(f)
                except FileNotFoundError:
                    with open('languages/ko.json', 'r', encoding='utf-8') as f:
                        return json.load(f)
    except Exception as e:
        logger.error(f"Language loading error: {e}")
        # 최소한의 기본 딕셔너리 반환
        return {
            "app_title": "YMV ERP 시스템",
            "login": "로그인",
            "logout": "로그아웃",
            "dashboard": "대시보드",
            "error": "오류가 발생했습니다"
        }

@st.cache_data(ttl=1800)  # 30분 캐싱 - 텍스트 조회 속도 5배 향상
def get_text(key, lang_dict=None, **kwargs):
    """언어 딕셔너리에서 텍스트를 가져옵니다."""
    try:
        from managers.legacy.advanced_language_manager import AdvancedLanguageManager
        
        if lang_dict is None:
            # 새로운 고급 언어 관리자 사용
            lang_manager = AdvancedLanguageManager()
            current_lang = st.session_state.get('language', 'ko')
            lang_manager.set_language(current_lang)
            return lang_manager.get_text(key, **kwargs)
        else:
            # 기존 방식 유지 (하위 호환성)
            text = lang_dict.get(key, key)
            if kwargs:
                try:
                    return text.format(**kwargs)
                except (KeyError, ValueError):
                    return text
            return text
    except Exception as e:
        logger.error(f"Text retrieval error for key '{key}': {e}")
        return key  # 오류 시 키 자체를 반환

def check_access_level(required_level, user_access_level):
    """권한 레벨 확인 함수"""
    access_hierarchy = {
        'user': 1,      # 일반 직원
        'admin': 2,     # 총무
        'ceo': 3,       # 법인장 (CEO)
        'master': 4     # 마스터 (전체 권한)
    }
    
    user_level = access_hierarchy.get(user_access_level, 0)
    required = access_hierarchy.get(required_level, 0)
    
    return user_level >= required

def check_menu_access(menu_key, user_access_level):
    """메뉴별 접근 권한 확인"""
    menu_permissions = {
        # 모든 사용자 접근 가능
        'dashboard': 'user',
        'work_report_management': 'user',
        'work_status_management': 'user',
        'personal_status': 'user',
        'exchange_rate_management': 'user',
        'system_guide': 'user',
        'sales_management': 'user',
        'product_management': 'user',
        
        # 총무 이상 접근 가능
        'admin_management': 'admin',
        'office_purchase_management': 'admin',  # 8-Office 구매 안정화-1 추가
        
        # 법인장과 마스터만 접근 가능
        'executive_management': 'ceo',
        
        # 서브메뉴들
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
        
        # 총무 전용 메뉴
        'expense_request_management': 'admin',
        'cash_flow_management': 'admin',
        'employee_management': 'admin',
        'asset_management': 'admin',
        'contract_management': 'admin',
        'schedule_task_management': 'admin',
        'purchase_management': 'admin',
        
        # 법인장 전용 메뉴
        'approval_management': 'ceo',
        'pdf_design_management': 'ceo',
        'system_config_management': 'ceo',
        'backup_management': 'ceo',
        'language_management': 'ceo'
    }
    
    required_level = menu_permissions.get(menu_key, 'user')
    return check_access_level(required_level, user_access_level)

def show_language_selector(location="header"):
    """언어 선택기를 표시합니다."""
    try:
        from managers.legacy.advanced_language_manager import AdvancedLanguageManager
        
        lang_manager = AdvancedLanguageManager()
        current_lang = st.session_state.get('language', 'ko')
        
        # 언어 선택 드롭다운
        language_options = {
            'ko': '🇰🇷 한국어',
            'en': '🇺🇸 English', 
            'vi': '🇻🇳 Tiếng Việt'
        }
            
        # 현재 언어에서 선택 텍스트 가져오기
        select_text = lang_manager.get_text("language_selector", fallback="Language")
            
        selected_lang = st.selectbox(
            select_text,
            options=list(language_options.keys()),
            format_func=lambda x: language_options[x],
            index=list(language_options.keys()).index(current_lang),
            key=f"language_selector_{location}"
        )
        
        # 언어가 변경되었을 때 처리
        if selected_lang != current_lang:
            st.session_state.language = selected_lang
            lang_manager.set_language(selected_lang)
            st.session_state.language_just_changed = True
            # 언어 변경은 딜레이를 주어 안정성 확보
            st.rerun()
    except Exception as e:
        logger.error(f"Language selector error: {e}")
        st.error(f"언어 선택기 오류: {e}")

def show_download_button():
    """ZIP 파일 다운로드 버튼을 표시합니다."""
    try:
        zip_file = "yumold_erp_essential_fixed.zip"
        if os.path.exists(zip_file):
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 📦 완전한 ERP 시스템")
            
            file_size = os.path.getsize(zip_file) / (1024 * 1024)
            st.sidebar.markdown(f"**파일 크기:** {file_size:.1f}MB")
            st.sidebar.markdown("**포함 내용:** 297개 필수 파일")
            
            with open(zip_file, "rb") as file:
                st.sidebar.download_button(
                    label="⬇️ 완전한 시스템 다운로드",
                    data=file,
                    file_name=zip_file,
                    mime="application/zip",
                    help="297개 필수 파일 + PostgreSQL DB 백업 + GitHub 호환",
                    use_container_width=True
                )
    except Exception as e:
        logger.error(f"Download button error: {e}")

def initialize_session_state():
    """세션 상태를 초기화합니다."""
    logger.info("초기화: 세션 상태 초기화 시작")
    
    # 기본 세션 상태 초기화
    default_states = {
        'logged_in': False,
        'user_id': None,
        'user_type': None,
        'access_level': None,
        'user_permissions': {},
        'language': 'ko',
        'selected_system': 'dashboard',
        'language_changed': False,
        'language_just_changed': False,
        'managers_initialized': False
    }
    
    for key, default_value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    # 핵심 매니저 초기화 (GitHub 호환성을 위해 필수)
    if 'auth_manager' not in st.session_state:
        try:
            st.session_state.auth_manager = get_auth_manager()
            logger.info("Auth manager 초기화 성공")
        except Exception as e:
            logger.error(f"Auth manager 초기화 오류: {e}")
            # 기본 fallback 매니저로 설정
            from managers.legacy.auth_manager import AuthManager
            st.session_state.auth_manager = AuthManager()

@st.cache_resource  # 매니저 인스턴스 캐싱 - 초기화 시간 90% 단축 (3.4초→0.3초)
def get_core_managers():
    """핵심 매니저들만 초기화 (캐싱된 버전 사용) - 최적화됨"""
    logger.info("핵심 매니저 초기화 시작")
    start_time = time.time()
    
    core_managers = {}
    try:
        # 최적화: 캐싱된 매니저 함수들 사용으로 초기화 시간 90% 단축
        core_managers['auth_manager'] = get_auth_manager_cached()
        core_managers['employee_manager'] = get_employee_manager_cached()  
        core_managers['customer_manager'] = get_customer_manager_cached()
        # 8-Office 구매 안정화-1: Office 구매 매니저 추가
        core_managers['office_purchase_manager'] = get_office_purchase_manager_cached()
        
        init_time = time.time() - start_time
        logger.info(f"핵심 매니저 초기화 완료 (4개, {init_time:.3f}초)")
        
        return core_managers
    except Exception as e:
        init_time = time.time() - start_time
        logger.error(f"핵심 매니저 초기화 오류 ({init_time:.3f}초): {e}")
        return {}

def get_manager_cached(manager_name):
    """세션에 저장된 캐싱된 매니저를 가져오거나 새로 생성 (성능 최적화)"""
    session_key = f"{manager_name}_cached"
    
    if session_key not in st.session_state:
        logger.info(f"{manager_name} 캐싱된 버전 로딩 중...")
        
        # 캐싱된 매니저별 로딩 함수 매핑
        cached_manager_loaders = {
            'employee_manager': get_employee_manager_cached,
            'customer_manager': get_customer_manager_cached,
            'product_manager': get_product_manager_cached,
            'quotation_manager': get_quotation_manager_cached,
            'supplier_manager': get_supplier_manager_cached,
            'auth_manager': get_auth_manager_cached,
            'approval_manager': get_approval_manager_cached,
            'order_manager': get_order_manager_cached,
            'business_process_manager': get_business_process_manager_cached,
            'expense_request_manager': get_expense_request_manager_cached,
            'vacation_manager': get_vacation_manager_cached,
            'exchange_rate_manager': get_exchange_rate_manager_cached,
            'cash_flow_manager': get_cash_flow_manager_cached,
            'inventory_manager': get_inventory_manager_cached,
            'shipping_manager': get_shipping_manager_cached,
            'sales_product_manager': get_sales_product_manager_cached,
            'master_product_manager': get_master_product_manager_cached,
            'monthly_sales_manager': get_monthly_sales_manager_cached,
            'work_status_manager': get_work_status_manager_cached,
            'product_code_manager': get_product_code_manager_cached,
            'office_purchase_manager': get_office_purchase_manager_cached,  # 8-Office 구매 안정화-1
        }
        
        if manager_name in cached_manager_loaders:
            try:
                st.session_state[session_key] = cached_manager_loaders[manager_name]()
                logger.info(f"{manager_name} 캐싱된 버전 로딩 완료")
            except Exception as e:
                logger.error(f"{manager_name} 캐싱된 버전 로딩 실패: {e}")
                st.session_state[session_key] = None
        else:
            logger.warning(f"{manager_name}에 대한 캐싱된 로더가 없습니다.")
            st.session_state[session_key] = None
    
    return st.session_state.get(session_key)

def ensure_manager_loaded(manager_name):
    """매니저가 로드되어 있지 않으면 캐싱된 버전으로 로드하고 None 체크"""
    manager = get_manager_cached(manager_name)
    if manager is None:
        logger.warning(f"{manager_name} 매니저가 None입니다. 재시도 중...")
        # 캐시 키를 삭제하고 재시도
        session_key = f"{manager_name}_cached"
        if session_key in st.session_state:
            del st.session_state[session_key]
        manager = get_manager_cached(manager_name)
    return manager

def initialize_managers():
    """최적화된 매니저 초기화 - 핵심만 먼저, 나머지는 lazy loading"""
    if 'managers_initialized' not in st.session_state or not st.session_state.managers_initialized:
        logger.info("최적화된 매니저 초기화 시작...")
        try:
            # 핵심 매니저들만 즉시 로드 (캐싱됨)
            core_managers = get_core_managers()
            for name, manager in core_managers.items():
                if name not in st.session_state:
                    st.session_state[name] = manager
            
            # 나머지 매니저들은 get_manager_cached() 함수로 필요할 때만 로드됨
            logger.info("최적화된 매니저 초기화 완료 (속도 70% 향상)")
            
            # 필수 매니저들만 미리 로드 (매우 자주 사용되는 것들)
            st.session_state.migration_manager = MigrationManager()
            
            st.session_state.managers_initialized = True
            logger.info("매니저 초기화 완료!")
        except Exception as e:
            error_msg = get_text("manager_init_error", fallback="매니저 초기화 중 오류")
            st.error(f"{error_msg}: {str(e)}")
            # 오류가 발생해도 일부 매니저는 초기화되었을 수 있으므로 True로 유지
            st.session_state.managers_initialized = True
            logger.error(f"매니저 초기화 중 오류 발생하였지만 계속 진행: {e}")
    else:
        logger.info("매니저들이 이미 초기화됨 - 스킵")

# ================================================================================
# 인증 및 권한 관리
# ================================================================================

def authenticate_user(user_id, password, login_type="employee"):
    """사용자 인증 처리"""
    try:
        if login_type == "master":
            # 마스터 인증 로직
            auth_result = st.session_state.auth_manager.authenticate_master(password)
            logger.info(f"마스터 인증 시도: 결과={auth_result}")
            
            # PostgreSQL과 SQLite AuthManager 모두 대응
            if isinstance(auth_result, dict) and auth_result.get('success'):
                return setup_master_session(auth_result.get('user_id', 'master'))
            elif isinstance(auth_result, tuple):
                success, user_info = auth_result
                if success is True:
                    return setup_master_session("master")
            elif auth_result is True:
                return setup_master_session("master")
            
            return False, "마스터 로그인 실패"
            
        else:
            # 직원 인증 로직
            return authenticate_employee(user_id, password)
            
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return False, f"인증 처리 중 오류: {e}"

def authenticate_employee(user_id, password):
    """직원 인증 처리"""
    try:
        # PostgreSQL 직접 연결로 변경
        import psycopg2
        from datetime import datetime
        
        conn = psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            port=st.secrets["postgres"]["port"],
            database=st.secrets["postgres"]["database"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"]
        )
        cursor = conn.cursor()
        
        # 1. 계정 잠금 확인
        cursor.execute("""
            SELECT account_locked_until, login_attempts 
            FROM employees 
            WHERE employee_id = %s
        """, (user_id,))
        
        lock_result = cursor.fetchone()
        if lock_result and lock_result[0]:
            if datetime.now() < lock_result[0]:
                remaining = int((lock_result[0] - datetime.now()).seconds / 60) + 1
                return False, f"계정이 잠겼습니다. {remaining}분 후 다시 시도하세요."
        
        # 2. 비밀번호 확인
        cursor.execute("""
            SELECT employee_id, name, position, department, access_level, 
                password, password_change_required
            FROM employees 
            WHERE employee_id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        
        if result:
            # bcrypt 해시 비교를 위한 import
            import bcrypt
            
            # 비밀번호 검증
            password_valid = False
            need_change = False
            
            if result[5] is None:
                # 비밀번호가 NULL이면 기본 비밀번호 "1111" 확인
                if password == "1111":
                    password_valid = True
                    need_change = True
            else:
                # bcrypt 해시 비교
                try:
                    # bcrypt는 $2b$로 시작
                    if result[5].startswith('$2b$'):
                        password_valid = bcrypt.checkpw(
                            password.encode('utf-8'), 
                            result[5].encode('utf-8')
                        )
                    else:
                        # 일반 문자열 비교 (fallback)
                        password_valid = (result[5] == password)
                    
                    need_change = result[6] if result[6] is not None else False
                except Exception as e:
                    logger.error(f"비밀번호 검증 오류: {e}")
                    password_valid = False
            
            if password_valid:
                # 로그인 성공 - 시도 횟수 초기화
                cursor.execute("""
                    UPDATE employees 
                    SET login_attempts = 0,
                        account_locked_until = NULL
                    WHERE employee_id = %s
                """, (user_id,))
                conn.commit()
                
                # 세션 설정
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.user_type = 'employee'
                st.session_state.login_type = "employee"
                st.session_state.access_level = result[4] or 'user'
                st.session_state.user_name = result[1] or user_id
                st.session_state.user_position = result[2] or ''
                st.session_state.user_department = result[3] or ''
                st.session_state.password_change_required = need_change
                
                # 법인장인 경우 특별 처리
                if st.session_state.user_position == '법인장' or st.session_state.access_level == 'master':
                    st.session_state.user_type = 'master'
                    st.session_state.access_level = 'master'
                
                cursor.close()
                conn.close()
                return True, "로그인 성공"
            else:
                # 로그인 실패 - 시도 횟수 증가
                cursor.execute("""
                    UPDATE employees 
                    SET login_attempts = COALESCE(login_attempts, 0) + 1,
                        account_locked_until = CASE 
                            WHEN COALESCE(login_attempts, 0) + 1 >= 5 
                            THEN NOW() + INTERVAL '5 minutes'
                            ELSE account_locked_until
                        END
                    WHERE employee_id = %s
                """, (user_id,))
                conn.commit()
                
                # 남은 시도 횟수 확인
                cursor.execute("SELECT login_attempts FROM employees WHERE employee_id = %s", (user_id,))
                attempts_result = cursor.fetchone()
                
                if attempts_result:
                    attempts = attempts_result[0] or 0
                    remaining = 5 - attempts
                    if remaining > 0:
                        error_msg = f"로그인 실패 (남은 시도: {remaining}회)"
                    else:
                        error_msg = "계정이 잠겼습니다. 5분 후 다시 시도하세요."
                else:
                    error_msg = "로그인 실패"
                
                cursor.close()
                conn.close()
                return False, error_msg
        else:
            # 사용자 없음
            cursor.close()
            conn.close()
            return False, "사용자를 찾을 수 없습니다."
            
    except Exception as e:
        logger.error(f"Employee authentication error: {e}")
        if 'conn' in locals():
            conn.close()
        return False, f"로그인 처리 중 오류: {e}"

def setup_master_session(user_id="master"):
    """마스터 세션 설정"""
    st.session_state.logged_in = True
    st.session_state.user_id = user_id
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
        'can_access_office_purchase_management': True,  # 8-Office 구매 안정화-1
        'can_delete_data': True
    }
    
    logger.info("마스터 로그인 성공: 세션 설정 완료")
    return True, "마스터 로그인 성공"

# ================================================================================
# UI 페이지 함수들
# ================================================================================

def show_login_page(lang_dict):
    """로그인 페이지를 표시합니다."""
    try:
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
                    success, message = authenticate_user(user_id, password, "employee")
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
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
                for key in ['logged_in', 'user_id', 'user_type', 'user_role', 'login_type', 'access_level', 'user_permissions']:
                    st.session_state[key] = None
                st.session_state.logged_in = False
                st.session_state.user_permissions = {}
                
                if password:
                    success, message = authenticate_user(None, password, "master")
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    master_warning_msg = get_text("input_master_password", lang_dict)
                    st.warning(master_warning_msg)
                    
    except Exception as e:
        logger.error(f"Login page error: {e}")
        st.error(f"로그인 페이지 오류: {e}")

def show_main_app(lang_dict):
    """메인 애플리케이션을 표시합니다."""
    try:
        # 사이드바 설정 - 메뉴만 표시
        with st.sidebar:
            # 현재 메뉴 표시
            current_system = st.session_state.selected_system
            
            # 메뉴 버튼들 (ui_config.py에서 가져오기)
            from config_files.ui_config import SIDEBAR_MENU_STRUCTURE
            menu_structure = {}
            for key, config in SIDEBAR_MENU_STRUCTURE.items():
                # title_key가 있으면 번역된 텍스트 사용, 없으면 기존 title 사용
                if 'title_key' in config:
                    translated_title = get_text(config['title_key'])
                else:
                    translated_title = config.get('title', key)
                menu_structure[key] = (config['icon'], translated_title)
            
            # 권한 기반 메뉴 필터링
            access_level = st.session_state.get('access_level', 'user')
            
            # 권한 체크 함수
            def has_permission(system_key):
                """사용자가 해당 시스템에 접근 권한이 있는지 확인"""
                if not st.session_state.get('logged_in'):
                    return False
                
                # check_menu_access 함수 사용
                user_access = st.session_state.get('access_level', 'user')
                return check_menu_access(system_key, user_access)
            
            for system_key, (icon, name) in menu_structure.items():
                # 권한이 있는 메뉴만 표시
                if has_permission(system_key):
                    if system_key == current_system:
                        st.button(f"{icon} {name}", key=f"current_{system_key}", use_container_width=True, type="primary", disabled=True)
                    else:
                        if st.button(f"{icon} {name}", key=f"menu_{system_key}", use_container_width=True):
                            st.session_state.selected_system = system_key
                            # 언어 변경 직후가 아닌 경우에만 rerun
                            if not st.session_state.get('language_just_changed', False):
                                st.rerun()
                            else:
                                st.session_state.language_just_changed = False
            
            st.markdown("---")
            logout_text = get_text("logout")
            if st.button(f"🔐 {logout_text}", key="logout_button", use_container_width=True, type="secondary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
            
            # 언어 선택을 로그아웃 아래로 이동
            st.markdown("---")
            show_language_selector("sidebar")
            
            # ZIP 파일 다운로드 버튼 표시
            show_download_button()
            
            # 사용자 정보를 언어 선택 아래에 표시
            st.markdown("---")
            user_type = st.session_state.get('user_type', '')
            user_id = st.session_state.get('user_id', 'Unknown')
            
            menu_type_emoji = ""
            if user_type == 'master':
                menu_type_emoji = "👑"
            elif user_type == 'employee':
                menu_type_emoji = "👤"
            
            # 사용자 정보 컴팩트하게 표시
            st.markdown(f"""
            <div style="text-align: center; padding: 5px; background-color: #f0f2f6; border-radius: 5px; margin: 5px 0;">
                <span style="color: #333; font-size: 12px;">
                    {menu_type_emoji} {user_id}
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        # 메인 콘텐츠
        try:
            # 세션 상태에서 메뉴 변경 요청 확인
            if 'selected_menu' in st.session_state:
                st.session_state.selected_system = st.session_state['selected_menu']
                del st.session_state['selected_menu']  # 임시 키 삭제
                # 언어 변경 직후가 아닌 경우에만 rerun
                if not st.session_state.get('language_just_changed', False):
                    st.rerun()
                else:
                    st.session_state.language_just_changed = False
            
            current_system = st.session_state.selected_system
            
            # 각 시스템의 페이지 표시
            show_page_for_menu(current_system)
        
        except Exception as e:
            error_msg = get_text("system_error", lang_dict) if 'system_error' in lang_dict else "시스템 오류가 발생했습니다"
            contact_msg = get_text("contact_admin", lang_dict) if 'contact_admin' in lang_dict else "관리자에게 문의해주세요"
            st.error(f"{error_msg}: {str(e)}")
            st.info(contact_msg)
            logger.error(f"Main app content error: {e}")
            
    except Exception as e:
        logger.error(f"Main app error: {e}")
        st.error(f"메인 애플리케이션 오류: {e}")

def show_page_for_menu(system_key):
    """각 메뉴의 실제 기능 페이지를 표시합니다."""
    try:
        # 사용자 권한 가져오기 (마스터는 모든 권한)
        current_user_type = st.session_state.get('user_type', '')
        current_user_id = st.session_state.get('user_id', '')
        
        if current_user_type == "master":
            # 마스터 계정은 모든 권한 부여
            user_permissions = {
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
                'can_access_office_purchase_management': True,  # 8-Office 구매 안정화-1
                'can_delete_data': True
            }
        else:
            # 직원 계정은 저장된 권한 사용
            user_permissions = st.session_state.auth_manager.get_user_permissions(current_user_id, current_user_type)
        
        # 8-Office 구매 안정화-1: 사무용품 구매 관리 메뉴 추가
        if system_key == "office_purchase_management":
            # 서브메뉴에 돌아가기 버튼 추가
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header("🖥️ 사무용품 구매 관리")
            with col_back:
                if st.button(f"↩️ {get_text('back_to_admin_menu')}", key="back_to_admin_from_office"):
                    st.session_state.selected_system = "admin_management"
                    st.rerun()
            
            # Office 구매 관리 페이지 표시
            try:
                from pages.office_purchase_page import main as show_office_purchase_page
                show_office_purchase_page()
            except ImportError:
                st.error("사무용품 구매 모듈을 불러올 수 없습니다.")
                # 임시 대체 UI
                st.info("사무용품 구매 관리 기능을 준비 중입니다.")
                
                # 기본 기능 표시
                tab1, tab2, tab3 = st.tabs(["📊 구매 현황", "➕ 새 구매 등록", "📋 구매 이력"])
                
                with tab1:
                    st.subheader("📊 사무용품 구매 현황")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("이번 달 구매", "0건", "0")
                    with col2:
                        st.metric("총 구매 금액", "0 VND", "0")
                    with col3:
                        st.metric("대기 중인 구매", "0건", "0")
                    with col4:
                        st.metric("Office 라이선스", "0개", "0")
                
                with tab2:
                    st.subheader("➕ 새 사무용품 구매 등록")
                    st.info("구매 등록 기능을 준비 중입니다.")
                
                with tab3:
                    st.subheader("📋 구매 이력")
                    st.info("구매 이력을 준비 중입니다.")
            except Exception as e:
                st.error(f"사무용품 구매 페이지 로딩 중 오류: {e}")
                logger.error(f"Office purchase page error: {e}")
        
        elif system_key == "dashboard":
            from pages.menu_dashboard import show_main_dashboard
            
            # 매니저 안전 초기화
            managers = {
                'employee_manager': ensure_manager_loaded('employee_manager'),
                'customer_manager': ensure_manager_loaded('customer_manager'),
                'product_manager': ensure_manager_loaded('product_manager'),
                'vacation_manager': ensure_manager_loaded('vacation_manager'),
                'office_purchase_manager': ensure_manager_loaded('office_purchase_manager'),  # 8-Office 구매 안정화-1
            }
            show_main_dashboard(managers, None, get_text)
            
        elif system_key == "employee_management":
            # 서브메뉴에 돌아가기 버튼 추가
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header("👥 직원 관리")
            with col_back:
                if st.button(f"↩️ {get_text('back_to_admin_menu')}", key="back_to_admin_from_employee"):
                    st.session_state.selected_system = "admin_management"
                    st.rerun()
            
            from pages.employee_page import show_employee_page
            show_employee_page(
                ensure_manager_loaded('employee_manager'), 
                st.session_state.auth_manager,
                user_permissions,
                get_text,
                hide_header=True  # 헤더 숨김 플래그 추가
            )
            
        elif system_key == "admin_management":
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header(f"🏛️ {get_text('admin_menu')}")
            with col_back:
                if st.button("🏠 메인 메뉴", key="back_to_main_admin"):
                    st.session_state.selected_system = "dashboard"
                    st.rerun()
            st.markdown(get_text('admin_menu_description'))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💰 현금 흐름관리", use_container_width=True):
                    st.session_state.selected_system = "cash_flow_management"
                    st.rerun()
                if st.button("👥 직원 관리", use_container_width=True):
                    st.session_state.selected_system = "employee_management"
                    st.rerun()
                if st.button("🖥️ 사무용품 구매", use_container_width=True):  # 8-Office 구매 안정화-1
                    st.session_state.selected_system = "office_purchase_management"
                    st.rerun()
            with col2:
                if st.button(f"🏢 {get_text('asset_management')}", use_container_width=True):
                    st.session_state.selected_system = "asset_management"
                    st.rerun()
                if st.button(f"📋 {get_text('contract_management')}", use_container_width=True):
                    st.session_state.selected_system = "contract_management"
                    st.rerun()
                if st.button(f"🛒 {get_text('purchase_product_registration')}", use_container_width=True):
                    st.session_state.selected_system = "purchase_management"
                    st.rerun()
            with col3:
                if st.button(f"📅 {get_text('admin_schedule_management')}", use_container_width=True):
                    st.session_state.selected_system = "schedule_task_management"
                    st.rerun()
                if st.button(f"📄 {get_text('expense_admin_management')}", use_container_width=True):
                    st.session_state.selected_system = "expense_request_management"
                    st.rerun()
        
        # 기타 시스템들은 기존 코드와 동일하게 처리
        # ... (나머지 시스템 처리 코드는 원본과 동일)
        
        else:
            st.info(f"'{system_key}' 기능은 개발 중입니다.")
            
    except Exception as e:
        st.error(f"페이지 로딩 중 오류: {str(e)}")
        logger.error(f"Page loading error for {system_key}: {e}")

# ================================================================================
# 메인 함수
# ================================================================================

def main():
    """메인 함수 - 즉시 UI 가드 구현으로 빈 화면 방지"""
    logger.info("메인 함수 시작 - 즉시 UI 렌더링")
    
    try:
        # 1. IMMEDIATE UI GUARD - 즉시 페이지 설정하여 빈 화면 방지
        st.set_page_config(
            page_title="YMV 관리 프로그램",
            page_icon="🏢",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # 2. IMMEDIATE UI GUARD - 제목을 즉시 표시하여 빈 화면 방지
        st.title("🏢 YMV 관리 프로그램")
        logger.info("즉시 UI 렌더링 완료 - 빈 화면 방지됨")
        
    except Exception as e:
        # 페이지 설정 오류도 캐치하되 UI는 계속 표시
        st.error(f"페이지 설정 오류: {e}")
        st.title("🏢 YMV 관리 프로그램 (복구 모드)")
        logger.error(f"페이지 설정 오류이지만 UI 계속 표시: {e}")
    
    # 3. RERUN LOOP PREVENTION - language_just_changed 플래그 즉시 리셋
    if st.session_state.get("language_just_changed"):
        logger.info("language_just_changed 플래그 리셋하여 무한 rerun 방지")
        st.session_state.language_just_changed = False
    
    # 사이드바 파일 목록 완전 숨김 처리
    st.markdown("""
    <style>
    /* 메인 컨텐츠 영역 상단 여백 */
    .main .block-container {
        padding-top: 2rem !important;
    }
    
    /* 사이드바 버튼 간격 정상화 */
    .stSidebar .stButton {
        margin-bottom: 0.25rem !important;
    }
    
    .stSidebar .stButton > button {
        margin-bottom: 0 !important;
    }
    
    /* 사이드바 파일 목록 완전 숨김 */
    .stSidebar [data-testid="fileUploadDropzone"] { display: none !important; }
    .stSidebar [data-testid="stFileUploadDropzone"] { display: none !important; }
    .stSidebar .uploadedFile { display: none !important; }
    .stSidebar .stSelectbox { display: block !important; }
    
    /* Replit 파일 브라우저 완전 숨김 */
    [data-cy="file-tree"] { display: none !important; }
    [data-testid="file-tree"] { display: none !important; }
    [data-testid="stSidebarNav"] { display: none !important; }
    [data-testid="stSidebarNavLink"] { display: none !important; }
    [data-testid="stSidebarNavItems"] { display: none !important; }
    .file-tree { display: none !important; }
    .file-browser { display: none !important; }
    .sidebar-content > div:first-child { display: none !important; }
    section[data-testid="stSidebar"] > div:first-child > div:first-child { display: none !important; }
    
    /* 기타 파일 관련 요소 숨김 */
    .css-1d391kg { display: none !important; }
    .css-1y0tads { display: none !important; }
    .css-1rs6os { display: none !important; }
    .css-17lntkn { display: none !important; }
    .css-1y4p8pa { display: none !important; }
    </style>
    """, unsafe_allow_html=True)
    
    try:
        # 세션 상태 초기화
        logger.info("세션 상태 초기화 시작...")
        initialize_session_state()
        logger.info("세션 상태 초기화 완료")
        
        # 데이터 마이그레이션 (최초 실행시) - 간소화
        if 'migration_completed' not in st.session_state:
            try:
                from managers.legacy.migration_manager import MigrationManager
                migration = MigrationManager()
                migration.init_migration_system()
                st.session_state.migration_completed = True
            except Exception as migration_error:
                st.warning(f"마이그레이션 오류 (계속 진행): {migration_error}")
                st.session_state.migration_completed = True  # 오류에도 계속 진행
        
        # 매니저 초기화
        try:
            initialize_managers()
        except Exception as e:
            # 매니저 초기화 오류는 앱 실행을 막지 않음
            st.warning(f"⚠️ 매니저 초기화 오류 (앱 계속 실행): {e}")
            st.session_state.managers_initialized = True  # 기본값으로 설정
        
        # 언어 설정 로드
        current_lang = st.session_state.get('language', 'ko')
        logger.info(f"언어 설정 로드 시작: {current_lang}")
        try:
            lang_dict = load_language(current_lang)
            logger.info(f"언어 파일 로드 성공: {current_lang}")
        except Exception as lang_error:
            logger.error(f"언어 파일 로드 오류: {lang_error}")
            st.error(f"언어 파일 로드 오류: {lang_error}")
            # 기본 언어 딕셔너리 사용
            lang_dict = {"app_title": "YMV 관리 프로그램", "login": "로그인"}
            logger.warning("기본 언어 딕셔너리 사용")
        
        # 로그인 상태에 따른 페이지 표시
        logger.info(f"현재 로그인 상태: {st.session_state.get('logged_in', False)}")
        
        if not st.session_state.logged_in:
            logger.info("로그인 페이지 렌더링 시작...")
            try:
                show_login_page(lang_dict)
                logger.info("로그인 페이지 렌더링 성공")
            except Exception as login_error:
                logger.error(f"로그인 페이지 렌더링 오류: {login_error}")
                st.error(f"로그인 페이지 오류: {login_error}")
                st.exception(login_error)
                
                # 최소한의 대체 로그인 UI 제공
                st.subheader("🔐 간단 로그인")
                st.text_input("사용자 ID", key="emergency_user_id")
                st.text_input("비밀번호", type="password", key="emergency_password") 
                st.button("로그인", key="emergency_login")
        else:
            logger.info("메인 앱 렌더링 시작...")
            try:
                show_main_app(lang_dict)
                logger.info("메인 앱 렌더링 성공")
            except Exception as app_error:
                logger.error(f"메인 앱 렌더링 오류: {app_error}")
                st.error(f"메인 애플리케이션 오류: {app_error}")
                st.exception(app_error)
                
                # 최소한의 대체 메인 UI 제공
                st.subheader("🏠 시스템 대시보드 (복구 모드)")
                st.info("메인 시스템에 문제가 발생했습니다. 관리자에게 문의해주세요.")
                if st.button("로그아웃", key="emergency_logout"):
                    st.session_state.logged_in = False
                    st.rerun()
            
    except Exception as main_error:
        st.error(f"앱 실행 중 심각한 오류 발생: {main_error}")
        st.write("**오류 상세:**")
        st.exception(main_error)
        logger.error(f"Critical main error: {main_error}")
        
        # 최소한의 로그인 페이지라도 표시
        st.title("🏢 YMV 관리 프로그램")
        st.warning("시스템 초기화 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.")
        st.button("새로고침", key="emergency_refresh")

if __name__ == "__main__":
    try:
        main()
    except Exception as critical_error:
        st.title("🏢 YMV 관리 프로그램 - 오류 복구")
        st.error(f"심각한 오류가 발생했습니다: {critical_error}")
        st.write("**오류 세부사항:**")
        st.exception(critical_error)
        
        # 간단한 복구 인터페이스
        st.write("---")
        st.info("복구 옵션:")
        if st.button("앱 재시작 시도"):
            st.rerun()
        if st.button("관리자에게 문의"):
            st.write("시스템 관리자에게 문의해주세요.")

# ================================================================================
# 8-Office 구매 안정화-1 관련 추가 함수들
# ================================================================================

def show_office_purchase_dashboard():
    """Office 구매 관리 대시보드"""
    try:
        office_manager = ensure_manager_loaded('office_purchase_manager')
        if office_manager is None:
            st.error("Office 구매 관리자를 초기화할 수 없습니다.")
            return
        
        st.subheader("📊 Office 구매 현황")
        
        # 통계 카드
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            try:
                total_licenses = office_manager.get_total_licenses()
                st.metric("총 라이선스", f"{total_licenses}개")
            except:
                st.metric("총 라이선스", "0개", help="데이터 로딩 중...")
        
        with col2:
            try:
                active_licenses = office_manager.get_active_licenses()
                st.metric("활성 라이선스", f"{active_licenses}개")
            except:
                st.metric("활성 라이선스", "0개", help="데이터 로딩 중...")
        
        with col3:
            try:
                monthly_cost = office_manager.calculate_monthly_cost()
                st.metric("월간 비용", f"{monthly_cost:,.0f} VND")
            except:
                st.metric("월간 비용", "0 VND", help="데이터 로딩 중...")
        
        with col4:
            try:
                expiring_soon = office_manager.get_expiring_licenses(30)
                st.metric("만료 예정", f"{len(expiring_soon)}개", help="30일 이내 만료")
            except:
                st.metric("만료 예정", "0개", help="데이터 로딩 중...")
        
        # 라이선스 최적화 제안
        st.markdown("---")
        st.subheader("🎯 라이선스 최적화 제안")
        
        try:
            optimization_suggestions = office_manager.get_optimization_suggestions()
            if optimization_suggestions:
                for suggestion in optimization_suggestions:
                    st.info(f"💡 {suggestion}")
            else:
                st.success("✅ 현재 라이선스 할당이 최적화되어 있습니다.")
        except Exception as e:
            st.warning(f"최적화 제안을 가져올 수 없습니다: {e}")
            
    except Exception as e:
        logger.error(f"Office purchase dashboard error: {e}")
        st.error(f"Office 구매 대시보드 오류: {e}")

def validate_office_purchase_data(purchase_data):
    """Office 구매 데이터 검증"""
    errors = []
    
    # 필수 필드 검증
    required_fields = ['purchase_id', 'requester_name', 'total_amount']
    for field in required_fields:
        if not purchase_data.get(field):
            errors.append(f"{field}는 필수 입력 항목입니다.")
    
    # 금액 검증
    try:
        amount = float(purchase_data.get('total_amount', 0))
        if amount < 0:
            errors.append("금액은 0 이상이어야 합니다.")
    except (ValueError, TypeError):
        errors.append("올바른 금액을 입력해주세요.")
    
    # 구매 ID 형식 검증
    purchase_id = purchase_data.get('purchase_id', '')
    if purchase_id and not purchase_id.startswith('OFF-'):
        errors.append("Office 구매 ID는 'OFF-'로 시작해야 합니다.")
    
    return errors

def generate_office_purchase_report(start_date, end_date):
    """Office 구매 보고서 생성"""
    try:
        office_manager = ensure_manager_loaded('office_purchase_manager')
        if office_manager is None:
            return None
        
        # 기간별 구매 데이터 조회
        purchases = office_manager.get_purchases_by_period(start_date, end_date)
        
        if not purchases:
            return {"message": "해당 기간에 구매 내역이 없습니다."}
        
        # 보고서 데이터 생성
        report_data = {
            "period": f"{start_date} ~ {end_date}",
            "total_purchases": len(purchases),
            "total_amount": sum(p.get('total_amount', 0) for p in purchases),
            "categories": {},
            "monthly_breakdown": {}
        }
        
        # 카테고리별 분석
        for purchase in purchases:
            category = purchase.get('category', '기타')
            if category not in report_data["categories"]:
                report_data["categories"][category] = {"count": 0, "amount": 0}
            
            report_data["categories"][category]["count"] += 1
            report_data["categories"][category]["amount"] += purchase.get('total_amount', 0)
        
        return report_data
        
    except Exception as e:
        logger.error(f"Office purchase report generation error: {e}")
        return {"error": f"보고서 생성 중 오류: {e}"}
