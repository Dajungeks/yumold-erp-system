# -*- coding: utf-8 -*-
import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
import locale
import sys
import time
import psycopg2
from psycopg2 import pool
import threading
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

# 컴포넌트 및 유틸리티
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
# 전역 설정 및 상태
# ================================================================================

# 전역 초기화 상태 추적
GLOBAL_STATE = {
    'app_initialized': False,
    'managers_loaded': False,
    'database_pool': None,
    'initialization_lock': threading.Lock()
}

# ================================================================================
# 데이터베이스 연결 풀 관리
# ================================================================================

@st.cache_resource
def get_database_pool():
    """데이터베이스 연결 풀 생성 및 관리"""
    if GLOBAL_STATE['database_pool'] is None:
        try:
            GLOBAL_STATE['database_pool'] = psycopg2.pool.SimpleConnectionPool(
                1, 10,  # 최소 1개, 최대 10개 연결
                host=st.secrets["postgres"]["host"],
                port=st.secrets["postgres"]["port"],
                database=st.secrets["postgres"]["database"],
                user=st.secrets["postgres"]["user"],
                password=st.secrets["postgres"]["password"]
            )
            logger.info("데이터베이스 연결 풀 생성 완료")
        except Exception as e:
            logger.error(f"데이터베이스 연결 풀 생성 실패: {e}")
            st.error(f"데이터베이스 연결 실패: {e}")
            return None
    return GLOBAL_STATE['database_pool']

def get_db_connection():
    """안전한 데이터베이스 연결 획득"""
    pool = get_database_pool()
    if pool:
        try:
            return pool.getconn()
        except Exception as e:
            logger.error(f"데이터베이스 연결 획득 실패: {e}")
            return None
    return None

def return_db_connection(conn):
    """데이터베이스 연결 반환"""
    pool = get_database_pool()
    if pool and conn:
        try:
            pool.putconn(conn)
        except Exception as e:
            logger.error(f"데이터베이스 연결 반환 실패: {e}")

# ================================================================================
# 매니저 캐싱 시스템 - 성능 최적화 및 안정성 개선
# ================================================================================

@st.cache_resource(ttl=3600)  # 1시간 캐시
def get_employee_manager_cached():
    """직원 매니저 캐싱된 버전 - 오류 처리 강화"""
    try:
        return get_employee_manager()
    except Exception as e:
        logger.error(f"Employee manager 로딩 실패: {e}")
        return None

@st.cache_resource(ttl=3600)
def get_customer_manager_cached():
    """고객 매니저 캐싱된 버전 - 오류 처리 강화"""
    try:
        return get_customer_manager()
    except Exception as e:
        logger.error(f"Customer manager 로딩 실패: {e}")
        return None

@st.cache_resource(ttl=3600)
def get_product_manager_cached():
    """제품 매니저 캐싱된 버전"""
    try:
        return get_product_manager()
    except Exception as e:
        logger.error(f"Product manager 로딩 실패: {e}")
        return None

@st.cache_resource(ttl=3600)
def get_quotation_manager_cached():
    """견적 매니저 캐싱된 버전"""
    try:
        return get_quotation_manager()
    except Exception as e:
        logger.error(f"Quotation manager 로딩 실패: {e}")
        return None

@st.cache_resource(ttl=3600)
def get_supplier_manager_cached():
    """공급업체 매니저 캐싱된 버전"""
    try:
        return get_supplier_manager()
    except Exception as e:
        logger.error(f"Supplier manager 로딩 실패: {e}")
        return None

@st.cache_resource(ttl=3600)
def get_auth_manager_cached():
    """인증 매니저 캐싱된 버전"""
    try:
        return get_auth_manager()
    except Exception as e:
        logger.error(f"Auth manager 로딩 실패: {e}")
        # 기본 AuthManager 반환
        return AuthManager()

@st.cache_resource(ttl=3600)
def get_approval_manager_cached():
    """승인 매니저 캐싱된 버전"""
    try:
        return get_approval_manager()
    except Exception as e:
        logger.error(f"Approval manager 로딩 실패: {e}")
        return None

@st.cache_resource(ttl=3600)
def get_order_manager_cached():
    """주문 매니저 캐싱된 버전"""
    try:
        return get_order_manager()
    except Exception as e:
        logger.error(f"Order manager 로딩 실패: {e}")
        return None

@st.cache_resource(ttl=3600)
def get_business_process_manager_cached():
    """비즈니스 프로세스 매니저 캐싱된 버전"""
    try:
        return get_business_process_manager()
    except Exception as e:
        logger.error(f"Business process manager 로딩 실패: {e}")
        return None

@st.cache_resource(ttl=3600)
def get_expense_request_manager_cached():
    """지출 요청 매니저 캐싱된 버전"""
    try:
        return get_expense_request_manager()
    except Exception as e:
        logger.error(f"Expense request manager 로딩 실패: {e}")
        return None

@st.cache_resource(ttl=3600)
def get_vacation_manager_cached():
    """휴가 매니저 캐싱된 버전"""
    try:
        return get_vacation_manager()
    except Exception as e:
        logger.error(f"Vacation manager 로딩 실패: {e}")
        return None

@st.cache_resource(ttl=3600)
def get_exchange_rate_manager_cached():
    """환율 매니저 캐싱된 버전"""
    try:
        return get_exchange_rate_manager()
    except Exception as e:
        logger.error(f"Exchange rate manager 로딩 실패: {e}")
        return None

@st.cache_resource(ttl=3600)
def get_cash_flow_manager_cached():
    """현금 흐름 매니저 캐싱된 버전"""
    try:
        return get_cash_flow_manager()
    except Exception as e:
        logger.error(f"Cash flow manager 로딩 실패: {e}")
        return None

@st.cache_resource(ttl=3600)
def get_inventory_manager_cached():
    """재고 매니저 캐싱된 버전"""
    try:
        return get_inventory_manager()
    except Exception as e:
        logger.error(f"Inventory manager 로딩 실패: {e}")
        return None

@st.cache_resource(ttl=3600)
def get_shipping_manager_cached():
    """배송 매니저 캐싱된 버전"""
    try:
        return get_shipping_manager()
    except Exception as e:
        logger.error(f"Shipping manager 로딩 실패: {e}")
        return None

@st.cache_resource(ttl=3600)
def get_sales_product_manager_cached():
    """판매 제품 매니저 캐싱된 버전"""
    try:
        return get_sales_product_manager()
    except Exception as e:
        logger.error(f"Sales product manager 로딩 실패: {e}")
        return None

@st.cache_resource(ttl=3600)
def get_master_product_manager_cached():
    """마스터 제품 매니저 캐싱된 버전"""
    try:
        return get_master_product_manager()
    except Exception as e:
        logger.error(f"Master product manager 로딩 실패: {e}")
        return None

@st.cache_resource(ttl=3600)
def get_monthly_sales_manager_cached():
    """월별 매출 매니저 캐싱된 버전"""
    try:
        return get_monthly_sales_manager()
    except Exception as e:
        logger.error(f"Monthly sales manager 로딩 실패: {e}")
        return None

@st.cache_resource(ttl=3600)
def get_work_status_manager_cached():
    """작업 상태 매니저 캐싱된 버전"""
    try:
        return get_work_status_manager()
    except Exception as e:
        logger.error(f"Work status manager 로딩 실패: {e}")
        return None

@st.cache_resource(ttl=3600)
def get_product_code_manager_cached():
    """제품 코드 매니저 캐싱된 버전"""
    try:
        return get_product_code_manager()
    except Exception as e:
        logger.error(f"Product code manager 로딩 실패: {e}")
        return None

@st.cache_resource(ttl=3600)
def get_finished_product_manager_cached():
    """완제품 매니저 캐싱된 버전"""
    try:
        return get_finished_product_manager()
    except Exception as e:
        logger.error(f"Finished product manager 로딩 실패: {e}")
        return None

@st.cache_resource(ttl=3600)
def get_invoice_manager_cached():
    """인보이스 매니저 캐싱된 버전"""
    try:
        return get_invoice_manager()
    except Exception as e:
        logger.error(f"Invoice manager 로딩 실패: {e}")
        return None

@st.cache_resource(ttl=3600)
def get_cash_transaction_manager_cached():
    """현금 거래 매니저 캐싱된 버전"""
    try:
        return get_cash_transaction_manager()
    except Exception as e:
        logger.error(f"Cash transaction manager 로딩 실패: {e}")
        return None

@st.cache_resource(ttl=3600)
def get_note_manager_cached():
    """노트 매니저 캐싱된 버전"""
    try:
        return get_note_manager()
    except Exception as e:
        logger.error(f"Note manager 로딩 실패: {e}")
        return None

# ================================================================================
# 언어 및 텍스트 관리 - 성능 최적화
# ================================================================================

@st.cache_data(ttl=3600)  # 1시간 캐싱
def load_language(lang_code):
    """언어 파일 로드 - 오류 처리 강화"""
    try:
        from managers.legacy.advanced_language_manager import AdvancedLanguageManager
        lang_manager = AdvancedLanguageManager()
        lang_manager.load_language_file(lang_code)
        
        # 새로운 locales 폴더에서 로드
        try:
            with open(f'locales/{lang_code}.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 구버전 languages 폴더에서 로드
            try:
                with open(f'languages/{lang_code}.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
            except FileNotFoundError:
                # 기본 언어 파일 로드
                with open('locales/ko.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
    except Exception as e:
        logger.error(f"언어 파일 로드 실패: {e}")
        # 최소한의 기본 텍스트 반환
        return {
            "app_title": "YMV 관리 프로그램",
            "login": "로그인",
            "logout": "로그아웃",
            "language_selector": "언어 선택",
            "error": "오류",
            "success": "성공"
        }

@st.cache_data(ttl=1800)  # 30분 캐싱
def get_text(key, lang_dict=None, **kwargs):
    """텍스트 조회 - 안전한 처리"""
    try:
        if lang_dict is None:
            from managers.legacy.advanced_language_manager import AdvancedLanguageManager
            lang_manager = AdvancedLanguageManager()
            current_lang = st.session_state.get('language', 'ko')
            lang_manager.set_language(current_lang)
            return lang_manager.get_text(key, **kwargs)
        else:
            text = lang_dict.get(key, key)
            if kwargs:
                try:
                    return text.format(**kwargs)
                except (KeyError, ValueError):
                    return text
            return text
    except Exception as e:
        logger.error(f"텍스트 조회 실패: {e}")
        return key  # 키를 그대로 반환

# ================================================================================
# 권한 및 접근 제어
# ================================================================================

def check_access_level(required_level, user_access_level):
    """권한 레벨 확인"""
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

# ================================================================================
# UI 컴포넌트
# ================================================================================

def show_language_selector(location="header"):
    """언어 선택기 - rerun 최적화"""
    try:
        from managers.legacy.advanced_language_manager import AdvancedLanguageManager
        
        lang_manager = AdvancedLanguageManager()
        current_lang = st.session_state.get('language', 'ko')
        
        language_options = {
            'ko': '🇰🇷 한국어',
            'en': '🇺🇸 English', 
            'vi': '🇻🇳 Tiếng Việt'
        }
        
        select_text = lang_manager.get_text("language_selector", fallback="Language")
        
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
    except Exception as e:
        logger.error(f"언어 선택기 오류: {e}")
        st.error("언어 선택기 오류가 발생했습니다.")

def show_download_button():
    """ZIP 파일 다운로드 버튼"""
    zip_file = "yumold_erp_essential_fixed.zip"
    if os.path.exists(zip_file):
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📦 완전한 ERP 시스템")
        
        try:
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
            logger.error(f"다운로드 버튼 오류: {e}")

# ================================================================================
# 초기화 시스템 - 개선된 안정성
# ================================================================================

def initialize_session_state():
    """세션 상태 초기화 - 안전성 강화"""
    try:
        if st.session_state.get('session_initialized', False):
            return
        
        logger.info("세션 상태 초기화 시작")
        
        # 기본 세션 상태 설정
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
            'language_changing': False,
            'session_initialized': True
        }
        
        for key, value in default_states.items():
            if key not in st.session_state:
                st.session_state[key] = value
        
        # 핵심 매니저 초기화
        if 'auth_manager' not in st.session_state:
            try:
                st.session_state.auth_manager = get_auth_manager_cached()
                if st.session_state.auth_manager is None:
                    st.session_state.auth_manager = AuthManager()
                logger.info("인증 매니저 초기화 완료")
            except Exception as e:
                logger.error(f"인증 매니저 초기화 실패: {e}")
                st.session_state.auth_manager = AuthManager()
        
        logger.info("세션 상태 초기화 완료")
        
    except Exception as e:
        logger.error(f"세션 상태 초기화 오류: {e}")
        st.error(f"세션 초기화 중 오류가 발생했습니다: {e}")

def ensure_manager_loaded(manager_name, max_retries=3):
    """매니저 안전 로딩 - 재시도 로직 포함"""
    for attempt in range(max_retries):
        try:
            manager = get_manager_cached(manager_name)
            if manager is not None:
                return manager
            
            # 캐시 클리어 후 재시도
            if attempt < max_retries - 1:
                session_key = f"{manager_name}_cached"
                if session_key in st.session_state:
                    del st.session_state[session_key]
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"{manager_name} 로딩 시도 {attempt + 1} 실패: {e}")
            if attempt == max_retries - 1:
                logger.error(f"{manager_name} 최종 로딩 실패")
    
    return None

def get_manager_cached(manager_name):
    """매니저 캐시 로딩 - 안전성 개선"""
    session_key = f"{manager_name}_cached"
    
    if session_key not in st.session_state:
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
            'finished_product_manager': get_finished_product_manager_cached,
            'invoice_manager': get_invoice_manager_cached,
            'cash_transaction_manager': get_cash_transaction_manager_cached,
            'note_manager': get_note_manager_cached,
        }
        
        if manager_name in cached_manager_loaders:
            try:
                st.session_state[session_key] = cached_manager_loaders[manager_name]()
                logger.info(f"{manager_name} 캐싱 완료")
            except Exception as e:
                logger.error(f"{manager_name} 캐싱 실패: {e}")
                st.session_state[session_key] = None
        else:
            logger.warning(f"{manager_name}에 대한 캐싱 로더가 없습니다.")
            st.session_state[session_key] = None
    
    return st.session_state.get(session_key)

def initialize_managers():
    """매니저 초기화 - 최적화 및 안정성 개선"""
    if st.session_state.get('managers_initialized', False):
        return
    
    try:
        with GLOBAL_STATE['initialization_lock']:
            logger.info("매니저 초기화 시작")
            
            # 핵심 매니저들만 미리 로드
            core_managers = ['auth_manager', 'employee_manager', 'customer_manager']
            
            for manager_name in core_managers:
                try:
                    manager = ensure_manager_loaded(manager_name)
                    if manager:
                        logger.info(f"{manager_name} 초기화 성공")
                    else:
                        logger.warning(f"{manager_name} 초기화 실패 - 계속 진행")
                except Exception as e:
                    logger.error(f"{manager_name} 초기화 오류: {e}")
            
            # 마이그레이션 매니저
            try:
                st.session_state.migration_manager = MigrationManager()
                logger.info("마이그레이션 매니저 초기화 완료")
            except Exception as e:
                logger.error(f"마이그레이션 매니저 초기화 실패: {e}")
            
            st.session_state.managers_initialized = True
            GLOBAL_STATE['managers_loaded'] = True
            logger.info("매니저 초기화 완료")
            
    except Exception as e:
        logger.error(f"매니저 초기화 중 오류: {e}")
        st.session_state.managers_initialized = True  # 오류에도 진행

# ================================================================================
# 로그인 시스템 - 안정성 개선
# ================================================================================

def show_login_page(lang_dict):
    """로그인 페이지 - 안전성 강화"""
    try:
        # 언어 선택기
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
            handle_employee_login(lang_dict)
        elif login_type == master_login_text:
            handle_master_login(lang_dict)
            
    except Exception as e:
        logger.error(f"로그인 페이지 오류: {e}")
        st.error("로그인 페이지에서 오류가 발생했습니다.")
        st.exception(e)

def handle_employee_login(lang_dict):
    """직원 로그인 처리 - 안전성 강화"""
    try:
        st.subheader(f"👤 {get_text('employee_login', lang_dict)}")
        
        with st.form("employee_login_form"):
            user_id_text = get_text("employee_id", lang_dict)
            password_text = get_text("password", lang_dict)
            login_button_text = get_text("login", lang_dict)
            
            user_id = st.text_input(user_id_text)
            password = st.text_input(password_text, type="password")
            login_submitted = st.form_submit_button(login_button_text, type="primary")
        
        if login_submitted and user_id and password:
            try:
                conn = get_db_connection()
                if not conn:
                    st.error("데이터베이스 연결에 실패했습니다.")
                    return
                
                cursor = conn.cursor()
                
                # 계정 잠금 확인
                cursor.execute("""
                    SELECT account_locked_until, login_attempts 
                    FROM employees 
                    WHERE employee_id = %s
                """, (user_id,))
                
                lock_result = cursor.fetchone()
                if lock_result and lock_result[0]:
                    if datetime.now() < lock_result[0]:
                        remaining = int((lock_result[0] - datetime.now()).seconds / 60) + 1
                        st.error(f"🔒 계정이 잠겼습니다. {remaining}분 후 다시 시도하세요.")
                        return
                
                # 사용자 정보 조회
                cursor.execute("""
                    SELECT employee_id, name, position, department, access_level, 
                        password, password_change_required
                    FROM employees 
                    WHERE employee_id = %s
                """, (user_id,))
                
                result = cursor.fetchone()
                
                if result and validate_password(password, result[5]):
                    # 로그인 성공 처리
                    setup_user_session(result, 'employee')
                    
                    # 로그인 시도 초기화
                    cursor.execute("""
                        UPDATE employees 
                        SET login_attempts = 0, account_locked_until = NULL
                        WHERE employee_id = %s
                    """, (user_id,))
                    conn.commit()
                    
                    st.success(get_text("login_success", lang_dict))
                    st.rerun()
                else:
                    handle_login_failure(cursor, conn, user_id, lang_dict)
                    
            except Exception as e:
                logger.error(f"직원 로그인 처리 오류: {e}")
                st.error("로그인 처리 중 오류가 발생했습니다.")
            finally:
                if 'conn' in locals() and conn:
                    return_db_connection(conn)
        elif login_submitted:
            st.warning(get_text("input_credentials", lang_dict))
            
    except Exception as e:
        logger.error(f"직원 로그인 폼 오류: {e}")
        st.error("로그인 폼에서 오류가 발생했습니다.")

def handle_master_login(lang_dict):
    """마스터 로그인 처리 - 안전성 강화"""
    try:
        st.subheader(f"🔐 {get_text('master_login', lang_dict)}")
        
        with st.form("master_login_form"):
            master_password_text = get_text("master_password", lang_dict)
            master_login_button_text = get_text("login", lang_dict)
            password = st.text_input(master_password_text, type="password")
            master_login_submitted = st.form_submit_button(master_login_button_text, type="primary")
        
        if master_login_submitted and password:
            try:
                # 세션 초기화
                clear_session_for_login()
                
                # 마스터 인증
                auth_manager = st.session_state.get('auth_manager')
                if not auth_manager:
                    st.error("인증 시스템을 초기화할 수 없습니다.")
                    return
                
                auth_result = auth_manager.authenticate_master(password)
                
                if validate_master_auth(auth_result):
                    setup_master_session()
                    st.success(get_text("master_login_success", lang_dict))
                    st.rerun()
                else:
                    st.error(get_text("master_login_failed", lang_dict))
                    
            except Exception as e:
                logger.error(f"마스터 로그인 처리 오류: {e}")
                st.error("마스터 로그인 처리 중 오류가 발생했습니다.")
        elif master_login_submitted:
            st.warning(get_text("input_master_password", lang_dict))
            
    except Exception as e:
        logger.error(f"마스터 로그인 폼 오류: {e}")
        st.error("마스터 로그인 폼에서 오류가 발생했습니다.")

def validate_password(password, stored_password):
    """비밀번호 검증 - 안전성 강화"""
    try:
        if stored_password is None:
            return password == "1111"  # 기본 비밀번호
        
        if stored_password.startswith('$2b$'):
            import bcrypt
            return bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
        else:
            return stored_password == password
            
    except Exception as e:
        logger.error(f"비밀번호 검증 오류: {e}")
        return False

def validate_master_auth(auth_result):
    """마스터 인증 결과 검증"""
    try:
        if isinstance(auth_result, dict) and auth_result.get('success'):
            return True
        elif isinstance(auth_result, tuple) and auth_result[0] is True:
            return True
        elif auth_result is True:
            return True
        return False
    except Exception as e:
        logger.error(f"마스터 인증 검증 오류: {e}")
        return False

def setup_user_session(user_data, user_type):
    """사용자 세션 설정"""
    try:
        st.session_state.logged_in = True
        st.session_state.user_id = user_data[0]
        st.session_state.user_type = user_type
        st.session_state.login_type = user_type
        st.session_state.access_level = user_data[4] or 'user'
        st.session_state.user_name = user_data[1] or user_data[0]
        st.session_state.user_position = user_data[2] or ''
        st.session_state.user_department = user_data[3] or ''
        st.session_state.password_change_required = user_data[6] if len(user_data) > 6 else False
        
        # 법인장 처리
        if st.session_state.user_position == '법인장' or st.session_state.access_level == 'master':
            st.session_state.user_type = 'master'
            st.session_state.access_level = 'master'
            
        logger.info(f"사용자 세션 설정 완료: {user_data[0]}")
    except Exception as e:
        logger.error(f"사용자 세션 설정 오류: {e}")

def setup_master_session():
    """마스터 세션 설정"""
    try:
        st.session_state.logged_in = True
        st.session_state.user_id = "master"
        st.session_state.user_type = "master"
        st.session_state.user_role = "master"
        st.session_state.login_type = "master"
        st.session_state.access_level = "master"
        
        # 마스터 권한 설정
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
        logger.info("마스터 세션 설정 완료")
    except Exception as e:
        logger.error(f"마스터 세션 설정 오류: {e}")

def clear_session_for_login():
    """로그인을 위한 세션 클리어"""
    try:
        keys_to_clear = ['logged_in', 'user_id', 'user_type', 'user_role', 
                        'login_type', 'access_level', 'user_permissions']
        for key in keys_to_clear:
            st.session_state[key] = None if key != 'user_permissions' else {}
        st.session_state.logged_in = False
    except Exception as e:
        logger.error(f"세션 클리어 오류: {e}")

def handle_login_failure(cursor, conn, user_id, lang_dict):
    """로그인 실패 처리"""
    try:
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
        
        cursor.execute("SELECT login_attempts FROM employees WHERE employee_id = %s", (user_id,))
        attempts_result = cursor.fetchone()
        
        if attempts_result:
            attempts = attempts_result[0] or 0
            remaining = 5 - attempts
            if remaining > 0:
                st.error(f"로그인 실패 (남은 시도: {remaining}회)")
            else:
                st.error("계정이 잠겼습니다. 5분 후 다시 시도하세요.")
        else:
            st.error(get_text("login_failed", lang_dict))
    except Exception as e:
        logger.error(f"로그인 실패 처리 오류: {e}")
        st.error(get_text("login_failed", lang_dict))

# ================================================================================
# 메인 애플리케이션
# ================================================================================

def show_main_app(lang_dict):
    """메인 애플리케이션 - 안전성 강화"""
    try:
        # 사이드바 메뉴
        show_sidebar_menu(lang_dict)
        
        # 메인 콘텐츠
        show_main_content()
        
    except Exception as e:
        logger.error(f"메인 앱 오류: {e}")
        st.error("메인 애플리케이션에서 오류가 발생했습니다.")
        show_error_recovery_ui()

def show_sidebar_menu(lang_dict):
    """사이드바 메뉴 표시"""
    try:
        with st.sidebar:
            current_system = st.session_state.selected_system
            
            # 메뉴 구조 로드
            from config_files.ui_config import SIDEBAR_MENU_STRUCTURE
            menu_structure = {}
            for key, config in SIDEBAR_MENU_STRUCTURE.items():
                if 'title_key' in config:
                    translated_title = get_text(config['title_key'])
                else:
                    translated_title = config.get('title', key)
                menu_structure[key] = (config['icon'], translated_title)
            
            # 권한 기반 메뉴 표시
            access_level = st.session_state.get('access_level', 'user')
            
            for system_key, (icon, name) in menu_structure.items():
                if has_permission(system_key):
                    if system_key == current_system:
                        st.button(f"{icon} {name}", key=f"current_{system_key}", 
                                use_container_width=True, type="primary", disabled=True)
                    else:
                        if st.button(f"{icon} {name}", key=f"menu_{system_key}", 
                                   use_container_width=True):
                            st.session_state.selected_system = system_key
                            if not st.session_state.get('language_just_changed', False):
                                st.rerun()
                            else:
                                st.session_state.language_just_changed = False
            
            # 로그아웃 및 기타 UI
            st.markdown("---")
            logout_text = get_text("logout")
            if st.button(f"🔐 {logout_text}", key="logout_button", 
                        use_container_width=True, type="secondary"):
                handle_logout()
            
            st.markdown("---")
            show_language_selector("sidebar")
            show_download_button()
            show_user_info()
            
    except Exception as e:
        logger.error(f"사이드바 메뉴 오류: {e}")
        st.sidebar.error("메뉴 로딩 중 오류가 발생했습니다.")

def has_permission(system_key):
    """권한 확인"""
    try:
        if not st.session_state.get('logged_in'):
            return False
        user_access = st.session_state.get('access_level', 'user')
        return check_menu_access(system_key, user_access)
    except Exception as e:
        logger.error(f"권한 확인 오류: {e}")
        return False

def show_user_info():
    """사용자 정보 표시"""
    try:
        st.markdown("---")
        user_type = st.session_state.get('user_type', '')
        user_id = st.session_state.get('user_id', 'Unknown')
        
        menu_type_emoji = "👑" if user_type == 'master' else "👤"
        
        st.markdown(f"""
        <div style="text-align: center; padding: 5px; background-color: #f0f2f6; 
             border-radius: 5px; margin: 5px 0;">
            <span style="color: #333; font-size: 12px;">
                {menu_type_emoji} {user_id}
            </span>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"사용자 정보 표시 오류: {e}")

def handle_logout():
    """로그아웃 처리"""
    try:
        # 중요한 키들만 보존하고 나머지 삭제
        keys_to_keep = ['session_initialized', 'managers_initialized']
        for key in list(st.session_state.keys()):
            if key not in keys_to_keep:
                del st.session_state[key]
        st.rerun()
    except Exception as e:
        logger.error(f"로그아웃 처리 오류: {e}")
        st.error("로그아웃 처리 중 오류가 발생했습니다.")

def show_main_content():
    """메인 콘텐츠 표시"""
    try:
        if 'selected_menu' in st.session_state:
            st.session_state.selected_system = st.session_state['selected_menu']
            del st.session_state['selected_menu']
            if not st.session_state.get('language_just_changed', False):
                st.rerun()
            else:
                st.session_state.language_just_changed = False
        
        current_system = st.session_state.selected_system
        show_page_for_menu(current_system)
        
    except Exception as e:
        logger.error(f"메인 콘텐츠 오류: {e}")
        st.error("페이지 로딩 중 오류가 발생했습니다.")
        st.exception(e)

def show_page_for_menu(system_key):
    """메뉴별 페이지 표시 - 안전성 강화"""
    try:
        # 기본 메뉴들
        if system_key == "dashboard":
            show_dashboard_page()
        elif system_key == "sales_management":
            show_sales_management_page()
        elif system_key == "product_management":
            show_product_management_page()
        elif system_key == "admin_management":
            show_admin_management_page()
        elif system_key == "executive_management":
            show_executive_management_page()
        elif system_key == "employee_management":
            show_employee_management_page()
        elif system_key == "customer_management":
            show_customer_management_page()
        elif system_key == "supplier_management":
            show_supplier_management_page()
        elif system_key == "quotation_management":
            show_quotation_management_page()
        elif system_key == "order_management":
            show_order_management_page()
        elif system_key == "shipping_management":
            show_shipping_management_page()
        elif system_key == "monthly_sales_management":
            show_monthly_sales_management_page()
        elif system_key == "business_process_v2_management":
            show_business_process_management_page()
        elif system_key == "exchange_rate_management":
            show_exchange_rate_management_page()
        elif system_key == "work_report_management":
            show_work_report_management_page()
        elif system_key == "work_status_management":
            show_work_status_management_page()
        elif system_key == "personal_status":
            show_personal_status_page()
        elif system_key == "system_guide":
            show_system_guide_page()
        elif system_key == "expense_request_management":
            show_expense_request_management_page()
        elif system_key == "cash_flow_management":
            show_cash_flow_management_page()
        elif system_key == "approval_management":
            show_approval_management_page()
        elif system_key == "backup_management":
            show_backup_management_page()
        elif system_key == "language_management":
            show_language_management_page()
        elif system_key == "system_config_management":
            show_system_config_management_page()
        elif system_key == "contract_management":
            show_contract_management_page()
        elif system_key == "schedule_task_management":
            show_schedule_task_management_page()
        elif system_key == "purchase_management":
            show_purchase_management_page()
        elif system_key == "asset_management":
            show_asset_management_page()
        else:
            st.info(f"'{system_key}' 기능은 개발 중입니다.")
            
    except Exception as e:
        logger.error(f"페이지 표시 오류 ({system_key}): {e}")
        st.error(f"'{system_key}' 페이지 로딩 중 오류가 발생했습니다.")
        show_error_recovery_ui()

# ================================================================================
# 개별 페이지 함수들 (기본 구현)
# ================================================================================

def show_dashboard_page():
    """대시보드 페이지"""
    try:
        from pages.menu_dashboard import show_main_dashboard
        managers = {
            'employee_manager': ensure_manager_loaded('employee_manager'),
            'customer_manager': ensure_manager_loaded('customer_manager'),
            'product_manager': ensure_manager_loaded('product_manager'),
            'vacation_manager': ensure_manager_loaded('vacation_manager'),
        }
        show_main_dashboard(managers, None, get_text)
    except Exception as e:
        logger.error(f"대시보드 페이지 오류: {e}")
        st.error("대시보드를 로딩할 수 없습니다.")

def show_sales_management_page():
    """영업관리 페이지"""
    try:
        col_header, col_back = st.columns([3, 1])
        with col_header:
            st.header(f"📊 {get_text('sales_management')}")
        with col_back:
            if st.button(f"🏠 {get_text('main_menu')}", key="back_to_main_sales"):
                st.session_state.selected_system = "dashboard"
                st.rerun()
        
        st.info("📋 견적서 관리 시스템이 준비되었습니다.")
        st.markdown("---")
        st.markdown(get_text('select_submenu'))
        
        # 서브메뉴 버튼들
        col1, col2, col3, col4 = st.columns(4)
        submenu_items = [
            ("customer_management", "👥", "customer_management"),
            ("quotation_management", "📋", "quotation_management"),
            ("order_management", "📦", "order_management"),
            ("business_process_v2_management", "🔄", "business_process")
        ]
        
        for i, (key, icon, text_key) in enumerate(submenu_items):
            with [col1, col2, col3, col4][i]:
                if st.button(f"{icon} {get_text(text_key)}", use_container_width=True):
                    st.session_state.selected_system = key
                    st.rerun()
                    
    except Exception as e:
        logger.error(f"영업관리 페이지 오류: {e}")
        st.error("영업관리 페이지를 로딩할 수 없습니다.")

def show_product_management_page():
    """제품관리 페이지"""
    try:
        col_header, col_back = st.columns([3, 1])
        with col_header:
            st.header("📦 제품 등록")
        with col_back:
            if st.button("🏠 메인 메뉴", key="back_to_main_product"):
                st.session_state.selected_system = "dashboard"
                st.rerun()
        
        from pages.product_registration_page import show_product_registration_page
        show_product_registration_page(
            ensure_manager_loaded('master_product_manager'),
            ensure_manager_loaded('finished_product_manager'),
            ensure_manager_loaded('product_code_manager'),
            st.session_state.get('user_permissions', {}),
            get_text
        )
    except Exception as e:
        logger.error(f"제품관리 페이지 오류: {e}")
        st.error("제품관리 페이지를 로딩할 수 없습니다.")

def show_admin_management_page():
    """총무관리 페이지"""
    try:
        col_header, col_back = st.columns([3, 1])
        with col_header:
            st.header(f"🏛️ {get_text('admin_menu')}")
        with col_back:
            if st.button("🏠 메인 메뉴", key="back_to_main_admin"):
                st.session_state.selected_system = "dashboard"
                st.rerun()
        
        st.markdown(get_text('admin_menu_description'))
        
        # 총무 메뉴 버튼들
        col1, col2, col3 = st.columns(3)
        admin_menus = [
            ("cash_flow_management", "💰", "현금 흐름관리"),
            ("employee_management", "👥", "직원 관리"),
            ("asset_management", "🏢", get_text('asset_management')),
            ("contract_management", "📋", get_text('contract_management')),
            ("purchase_management", "🛒", get_text('purchase_product_registration')),
            ("schedule_task_management", "📅", get_text('admin_schedule_management')),
            ("expense_request_management", "📄", get_text('expense_admin_management'))
        ]
        
        for i, (key, icon, title) in enumerate(admin_menus):
            col_idx = i % 3
            with [col1, col2, col3][col_idx]:
                if st.button(f"{icon} {title}", use_container_width=True):
                    st.session_state.selected_system = key
                    st.rerun()
                    
    except Exception as e:
        logger.error(f"총무관리 페이지 오류: {e}")
        st.error("총무관리 페이지를 로딩할 수 없습니다.")

def show_executive_management_page():
    """법인장 메뉴 페이지"""
    try:
        col_header, col_back = st.columns([3, 1])
        with col_header:
            st.header("👑 법인장 메뉴")
        with col_back:
            if st.button("🏠 메인 메뉴", key="back_to_main_executive"):
                st.session_state.selected_system = "dashboard"
                st.rerun()
        
        st.markdown("법인장 전용 메뉴를 선택해주세요.")
        
        col1, col2, col3 = st.columns(3)
        executive_menus = [
            ("approval_management", "✅", "승인관리"),
            ("backup_management", "💾", "백업관리"),
            ("system_config_management", "⚙️", "시스템 설정"),
            ("language_management", "🌍", "다국어 관리")
        ]
        
        for i, (key, icon, title) in enumerate(executive_menus):
            col_idx = i % 3
            with [col1, col2, col3][col_idx]:
                if st.button(f"{icon} {title}", use_container_width=True):
                    st.session_state.selected_system = key
                    st.rerun()
                    
    except Exception as e:
        logger.error(f"법인장 메뉴 페이지 오류: {e}")
        st.error("법인장 메뉴 페이지를 로딩할 수 없습니다.")

# 나머지 페이지 함수들은 기본 구현으로 대체
def show_employee_management_page():
    """직원관리 페이지"""
    try:
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
            st.session_state.get('user_permissions', {}),
            get_text,
            hide_header=True
        )
    except Exception as e:
        logger.error(f"직원관리 페이지 오류: {e}")
        st.error("직원관리 페이지를 로딩할 수 없습니다.")

# 기타 페이지 함수들 (기본 구현)
def show_customer_management_page():
    st.info("고객관리 페이지가 로딩 중입니다.")

def show_supplier_management_page():
    st.info("공급업체관리 페이지가 로딩 중입니다.")

def show_quotation_management_page():
    st.info("견적관리 페이지가 로딩 중입니다.")

def show_order_management_page():
    st.info("주문관리 페이지가 로딩 중입니다.")

def show_shipping_management_page():
    st.info("배송관리 페이지가 로딩 중입니다.")

def show_monthly_sales_management_page():
    st.info("월별매출관리 페이지가 로딩 중입니다.")

def show_business_process_management_page():
    st.info("비즈니스프로세스 페이지가 로딩 중입니다.")

def show_exchange_rate_management_page():
    st.info("환율관리 페이지가 로딩 중입니다.")

def show_work_report_management_page():
    st.info("업무보고 페이지가 로딩 중입니다.")

def show_work_status_management_page():
    st.info("업무현황 페이지가 로딩 중입니다.")

def show_personal_status_page():
    st.info("개인현황 페이지가 로딩 중입니다.")

def show_system_guide_page():
    st.info("시스템가이드 페이지가 로딩 중입니다.")

def show_expense_request_management_page():
    st.info("지출요청관리 페이지가 로딩 중입니다.")

def show_cash_flow_management_page():
    st.info("현금흐름관리 페이지가 로딩 중입니다.")

def show_approval_management_page():
    st.info("승인관리 페이지가 로딩 중입니다.")

def show_backup_management_page():
    st.info("백업관리 페이지가 로딩 중입니다.")

def show_language_management_page():
    st.info("다국어관리 페이지가 로딩 중입니다.")

def show_system_config_management_page():
    st.info("시스템설정 페이지가 로딩 중입니다.")

def show_contract_management_page():
    st.info("계약관리 페이지가 로딩 중입니다.")

def show_schedule_task_management_page():
    st.info("일정관리 페이지가 로딩 중입니다.")

def show_purchase_management_page():
    st.info("구매관리 페이지가 로딩 중입니다.")

def show_asset_management_page():
    st.info("자산관리 페이지가 로딩 중입니다.")

# ================================================================================
# 오류 복구 UI
# ================================================================================

def show_error_recovery_ui():
    """오류 복구 인터페이스"""
    try:
        st.warning("시스템에서 오류가 발생했습니다.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 페이지 새로고침", use_container_width=True):
                st.rerun()
        
        with col2:
            if st.button("🏠 대시보드로 이동", use_container_width=True):
                st.session_state.selected_system = "dashboard"
                st.rerun()
        
        with col3:
            if st.button("🔐 다시 로그인", use_container_width=True):
                handle_logout()
                
        st.info("문제가 지속되면 시스템 관리자에게 문의하세요.")
        
    except Exception as e:
        logger.error(f"오류 복구 UI 오류: {e}")
        st.error("복구 시스템에서도 오류가 발생했습니다.")

# ================================================================================
# 비즈니스 프로세스 V2 페이지 (개선된 버전)
# ================================================================================

def show_business_process_v2_page():
    """비즈니스 프로세스 V2 페이지 - 안전성 강화"""
    try:
        # 매니저 초기화
        if 'bp_manager_v2' not in st.session_state:
            try:
                from scripts.business_process_manager_v2 import BusinessProcessManagerV2
                st.session_state.bp_manager_v2 = BusinessProcessManagerV2()
            except Exception as e:
                logger.error(f"비즈니스 프로세스 매니저 초기화 실패: {e}")
                st.error("비즈니스 프로세스 시스템을 초기화할 수 없습니다.")
                return
        
        # 탭 생성
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 프로세스 대시보드",
            "➕ 새 프로세스 생성", 
            "📋 진행중 프로세스 관리",
            "✏️ 프로세스 편집/수정",
            "📈 성과 분석"
        ])
        
        with tab1:
            show_process_dashboard()
        
        with tab2:
            show_create_process()
        
        with tab3:
            show_manage_processes()
        
        with tab4:
            show_edit_processes()
        
        with tab5:
            show_process_analytics()
            
    except Exception as e:
        logger.error(f"비즈니스 프로세스 V2 페이지 오류: {e}")
        st.error("비즈니스 프로세스 페이지를 로딩할 수 없습니다.")
        show_error_recovery_ui()

def show_process_dashboard():
    """프로세스 대시보드"""
    try:
        st.header("📊 프로세스 현황 대시보드")
        
        # 통계 정보 가져오기
        stats = st.session_state.bp_manager_v2.get_workflow_statistics()
        
        if not stats:
            st.info("아직 생성된 워크플로우가 없습니다.")
        else:
            # 상단 메트릭 카드들
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📈 판매 프로세스", f"{stats.get('sales_workflows', 0)}건")
            
            with col2:
                st.metric("🔧 서비스 프로세스", f"{stats.get('service_workflows', 0)}건")
            
            with col3:
                st.metric("🔄 복합 프로세스", f"{stats.get('mixed_workflows', 0)}건")
            
            with col4:
                st.metric("🎯 평균 진행률", f"{stats.get('average_progress', 0):.1f}%")
                
    except Exception as e:
        logger.error(f"프로세스 대시보드 오류: {e}")
        st.error("대시보드를 로딩할 수 없습니다.")

def show_create_process():
    """새 프로세스 생성"""
    try:
        st.header("➕ 새 워크플로우 생성")
        
        # 견적서 목록 가져오기
        try:
            quotation_manager = ensure_manager_loaded('quotation_manager')
            if quotation_manager is not None:
                quotations_df = quotation_manager.get_all_quotations()
            else:
                quotations_df = pd.DataFrame()
                
            if isinstance(quotations_df, list):
                quotations_df = pd.DataFrame(quotations_df)
            
            available_quotations = quotations_df
        except Exception as e:
            logger.error(f"견적서 데이터 로드 오류: {e}")
            st.error(f"견적서 데이터 로드 오류: {e}")
            available_quotations = pd.DataFrame()
        
        if len(available_quotations) == 0:
            st.warning("생성된 견적서가 없습니다. 먼저 견적서를 작성해주세요.")
        else:
            st.success(f"사용 가능한 견적서 {len(available_quotations)}개를 찾았습니다.")
            
            # 견적서 선택 및 워크플로우 생성 폼
            show_workflow_creation_form(available_quotations)
            
    except Exception as e:
        logger.error(f"프로세스 생성 오류: {e}")
        st.error("프로세스 생성 페이지를 로딩할 수 없습니다.")

def show_workflow_creation_form(available_quotations):
    """워크플로우 생성 폼"""
    try:
        # 견적서 선택 드롭다운
        quotation_options = {}
        for _, quot in available_quotations.iterrows():
            total_usd = quot.get('total_amount_usd', 0) or 0
            display_text = f"{quot.get('quotation_number', quot.get('quotation_id', 'N/A'))} - {quot.get('customer_name', 'N/A')} ({total_usd:,.0f} USD)"
            quotation_options[display_text] = quot['quotation_id']
        
        if quotation_options:
            selected_quotation_display = st.selectbox(
                "견적서를 선택하세요:",
                options=list(quotation_options.keys())
            )
            
            if selected_quotation_display:
                selected_quotation_id = quotation_options[selected_quotation_display]
                
                # 담당자 선택
                col1, col2 = st.columns(2)
                with col1:
                    sales_team = st.text_input("판매팀 담당자:", value="담당자 미정")
                with col2:
                    service_team = st.text_input("서비스팀 담당자:", value="담당자 미정")
                
                notes = st.text_area("초기 메모:", placeholder="워크플로우 생성 시 특이사항이나 메모를 입력하세요.")
                
                if st.button("🚀 워크플로우 생성", type="primary", use_container_width=True):
                    create_workflow_from_quotation(selected_quotation_id, sales_team, service_team, notes)
                    
    except Exception as e:
        logger.error(f"워크플로우 생성 폼 오류: {e}")
        st.error("워크플로우 생성 폼에서 오류가 발생했습니다.")

def create_workflow_from_quotation(quotation_id, sales_team, service_team, notes):
    """견적서로부터 워크플로우 생성"""
    try:
        # 선택된 견적서 데이터 가져오기
        quotation_manager = ensure_manager_loaded('quotation_manager')
        if quotation_manager is not None:
            all_quotations = quotation_manager.get_all_quotations()
        else:
            all_quotations = []
            
        selected_quotation_data = None
        for quotation in all_quotations:
            if quotation.get('quotation_id') == quotation_id:
                selected_quotation_data = quotation
                break
        
        if selected_quotation_data:
            # 담당자 정보 추가
            selected_quotation_data['assigned_sales_team'] = sales_team
            selected_quotation_data['assigned_service_team'] = service_team
            selected_quotation_data['notes'] = notes
            
            success, message = st.session_state.bp_manager_v2.create_workflow_from_quotation(
                quotation_data=selected_quotation_data,
                created_by=st.session_state.get('user_id', '')
            )
            
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
        else:
            st.error("견적서 데이터를 찾을 수 없습니다.")
            
    except Exception as e:
        logger.error(f"워크플로우 생성 오류: {e}")
        st.error("워크플로우 생성 중 오류가 발생했습니다.")

def show_manage_processes():
    """진행중 프로세스 관리"""
    try:
        st.header("📋 진행중 프로세스 관리")
        
        # 워크플로우 목록 가져오기
        try:
            workflows_df = st.session_state.bp_manager_v2.get_all_workflows()
            if isinstance(workflows_df, list):
                valid_workflows = [w for w in workflows_df if isinstance(w, dict)]
                workflows_df = valid_workflows
            else:
                workflows_df = []
        except Exception as e:
            logger.error(f"워크플로우 데이터 로드 오류: {e}")
            st.error(f"워크플로우 데이터 로드 오류: {e}")
            workflows_df = []
        
        if len(workflows_df) == 0:
            st.info("생성된 워크플로우가 없습니다.")
        else:
            st.success(f"총 {len(workflows_df)}개의 워크플로우가 있습니다.")
            show_workflow_table(workflows_df)
            
    except Exception as e:
        logger.error(f"프로세스 관리 오류: {e}")
        st.error("프로세스 관리 페이지를 로딩할 수 없습니다.")

def show_workflow_table(workflows_df):
    """워크플로우 테이블 표시"""
    try:
        # 테이블 헤더
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1, 1.5, 1.5, 2, 1.5, 1, 1, 1.5])
        
        headers = ["식별번호", "이름", "연락처", "이메일", "상태", "진행률", "작업", "상세보기"]
        for i, header in enumerate(headers):
            with [col1, col2, col3, col4, col5, col6, col7, col8][i]:
                st.markdown(f"**{header}**")
        
        st.divider()
        
        # 워크플로우 목록 표시
        for workflow in workflows_df:
            if not isinstance(workflow, dict):
                continue
            
            show_workflow_row(workflow)
            
    except Exception as e:
        logger.error(f"워크플로우 테이블 표시 오류: {e}")
        st.error("워크플로우 테이블을 표시할 수 없습니다.")

def show_workflow_row(workflow):
    """워크플로우 행 표시"""
    try:
        quotation_number = str(workflow.get('quotation_number', ''))
        customer_name = str(workflow.get('customer_name', ''))
        overall_progress = float(workflow.get('overall_progress', 0))
        
        # 연락처와 이메일 정보
        contact_info = workflow.get('customer_phone', workflow.get('contact_info', ''))
        email_info = workflow.get('customer_email', workflow.get('email_info', ''))
        
        # 상태 결정
        if overall_progress >= 100:
            status = "완료"
            status_color = "success"
        elif overall_progress > 0:
            status = "진행중"
            status_color = "warning"
        else:
            status = "대기"
            status_color = "info"
        
        # 테이블 행 표시
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1, 1.5, 1.5, 2, 1.5, 1, 1, 1.5])
        
        with col1:
            st.text(quotation_number)
        with col2:
            st.text(customer_name)
        with col3:
            st.text(contact_info[:15] + "..." if len(contact_info) > 15 else contact_info)
        with col4:
            st.text(email_info[:20] + "..." if len(email_info) > 20 else email_info)
        with col5:
            if status_color == "success":
                st.success(status)
            elif status_color == "warning":
                st.warning(status)
            else:
                st.info(status)
        with col6:
            st.progress(overall_progress / 100)
            st.text(f"{overall_progress:.1f}%")
        with col7:
            workflow_id = workflow.get('workflow_id', '')
            col_edit, col_delete = st.columns(2)
            with col_edit:
                if st.button("✏️", key=f"table_edit_{workflow_id}", help="수정"):
                    st.session_state.selected_workflow_id = workflow_id
                    st.rerun()
            with col_delete:
                if st.button("🗑️", key=f"table_delete_{workflow_id}", help="삭제"):
                    delete_workflow(workflow_id)
        with col8:
            if st.button("📋 상세", key=f"table_detail_{workflow_id}"):
                st.session_state.show_workflow_detail = workflow_id
                st.rerun()
                
    except Exception as e:
        logger.error(f"워크플로우 행 표시 오류: {e}")

def delete_workflow(workflow_id):
    """워크플로우 삭제"""
    try:
        if st.session_state.get('user_type') == 'master':
            success, message = st.session_state.bp_manager_v2.delete_workflow(workflow_id)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
        else:
            st.error("마스터 권한이 필요합니다.")
    except Exception as e:
        logger.error(f"워크플로우 삭제 오류: {e}")
        st.error("워크플로우 삭제 중 오류가 발생했습니다.")

def show_edit_processes():
    """프로세스 편집/수정"""
    try:
        st.header("✏️ 프로세스 편집/수정")
        
        # 마스터 권한 확인
        if st.session_state.get('user_type') != 'master':
            st.warning("🔒 프로세스 편집/수정 기능은 마스터 권한이 필요합니다.")
            return
        
        st.info("프로세스 편집 기능이 개발 중입니다.")
        
    except Exception as e:
        logger.error(f"프로세스 편집 오류: {e}")
        st.error("프로세스 편집 페이지를 로딩할 수 없습니다.")

def show_process_analytics():
    """프로세스 성과 분석"""
    try:
        st.header("📈 성과 분석")
        
        try:
            workflows_df = st.session_state.bp_manager_v2.get_all_workflows()
            if isinstance(workflows_df, list):
                valid_workflows = [w for w in workflows_df if isinstance(w, dict)]
                workflows_df = valid_workflows
            else:
                workflows_df = []
        except Exception as e:
            logger.error(f"분석 데이터 로드 오류: {e}")
            workflows_df = []
        
        if len(workflows_df) > 0:
            # 기본 통계
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("전체 워크플로우", len(workflows_df))
            
            with col2:
                completed_count = len([w for w in workflows_df if w.get('overall_status') == 'completed'])
                st.metric("완료된 워크플로우", completed_count)
            
            with col3:
                progress_values = [w.get('overall_progress', 0) for w in workflows_df if isinstance(w.get('overall_progress'), (int, float))]
                avg_progress = sum(progress_values) / len(progress_values) if progress_values else 0
                st.metric("평균 진행률", f"{avg_progress:.1f}%")
        else:
            st.info("분석할 데이터가 없습니다.")
            
    except Exception as e:
        logger.error(f"프로세스 분석 오류: {e}")
        st.error("성과 분석 페이지를 로딩할 수 없습니다.")

# ================================================================================
# 메인 함수 - 안정성 및 성능 최적화
# ================================================================================

def main():
    """메인 함수 - 완전한 오류 처리 및 성능 최적화"""
    
    # 전역 초기화 체크
    if GLOBAL_STATE['app_initialized']:
        logger.info("앱이 이미 초기화됨 - 빠른 실행")
    else:
        logger.info("앱 최초 초기화 시작")
    
    try:
        # 1. 즉시 페이지 설정 - 빈 화면 방지
        if not st.session_state.get('page_configured', False):
            st.set_page_config(
                page_title="YMV 관리 프로그램",
                page_icon="🏢",
                layout="wide",
                initial_sidebar_state="expanded"
            )
            st.session_state.page_configured = True
            logger.info("페이지 설정 완료")
        
        # 2. 즉시 UI 표시
        st.title("🏢 YMV 관리 프로그램")
        
        # 3. CSS 스타일 적용
        apply_custom_styles()
        
        # 4. 세션 상태 초기화
        initialize_session_state()
        
        # 5. 매니저 초기화 (백그라운드)
        if not st.session_state.get('managers_initialized', False):
            with st.spinner("시스템 초기화 중..."):
                initialize_managers()
        
        # 6. 마이그레이션 (한 번만)
        if not st.session_state.get('migration_completed', False):
            try:
                migration = MigrationManager()
                migration.init_migration_system()
                st.session_state.migration_completed = True
                logger.info("마이그레이션 완료")
            except Exception as e:
                logger.warning(f"마이그레이션 오류 (계속 진행): {e}")
                st.session_state.migration_completed = True
        
        # 7. 언어 설정 로드
        current_lang = st.session_state.get('language', 'ko')
        lang_dict = load_language(current_lang)
        
        # 8. 메인 애플리케이션 실행
        if st.session_state.get('logged_in', False):
            show_main_app(lang_dict)
        else:
            show_login_page(lang_dict)
        
        # 9. 전역 초기화 완료 표시
        if not GLOBAL_STATE['app_initialized']:
            GLOBAL_STATE['app_initialized'] = True
            logger.info("앱 초기화 완료")
            
    except Exception as e:
        logger.error(f"메인 함수 오류: {e}")
        handle_critical_error(e)

def apply_custom_styles():
    """커스텀 CSS 스타일 적용"""
    try:
        st.markdown("""
        <style>
        /* 메인 컨텐츠 영역 최적화 */
        .main .block-container {
            padding-top: 2rem !important;
            max-width: 100% !important;
        }
        
        /* 사이드바 최적화 */
        .stSidebar .stButton {
            margin-bottom: 0.25rem !important;
        }
        
        .stSidebar .stButton > button {
            margin-bottom: 0 !important;
            font-size: 14px !important;
        }
        
        /* 파일 브라우저 완전 숨김 */
        .stSidebar [data-testid="fileUploadDropzone"] { display: none !important; }
        .stSidebar [data-testid="stFileUploadDropzone"] { display: none !important; }
        .stSidebar .uploadedFile { display: none !important; }
        [data-cy="file-tree"] { display: none !important; }
        [data-testid="file-tree"] { display: none !important; }
        [data-testid="stSidebarNav"] { display: none !important; }
        section[data-testid="stSidebar"] > div:first-child > div:first-child { display: none !important; }
        
        /* 성능 최적화 */
        .stDataFrame { 
            border: 1px solid #e6e6e6; 
            border-radius: 5px;
        }
        
        /* 메트릭 카드 스타일 */
        .metric-card {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #dee2e6;
            margin-bottom: 1rem;
        }
        
        /* 버튼 스타일 통일 */
        .stButton > button {
            width: 100%;
            border-radius: 0.5rem;
            transition: all 0.3s;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        /* 로딩 스피너 커스터마이징 */
        .stSpinner {
            text-align: center;
            margin: 2rem 0;
        }
        
        /* 오류 메시지 스타일 */
        .stAlert > div {
            border-radius: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"CSS 스타일 적용 오류: {e}")

def handle_critical_error(error):
    """치명적 오류 처리"""
    try:
        st.title("🏢 YMV 관리 프로그램 - 오류 복구")
        st.error(f"심각한 오류가 발생했습니다: {error}")
        
        with st.expander("오류 세부사항"):
            st.exception(error)
        
        st.markdown("---")
        st.info("복구 옵션:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 앱 재시작", use_container_width=True):
                # 세션 상태 완전 초기화
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                GLOBAL_STATE['app_initialized'] = False
                GLOBAL_STATE['managers_loaded'] = False
                st.rerun()
        
        with col2:
            if st.button("🏠 안전 모드", use_container_width=True):
                st.session_state.safe_mode = True
                st.rerun()
        
        with col3:
            if st.button("📞 지원 요청", use_container_width=True):
                st.info("시스템 관리자에게 문의해주세요.")
                st.code(f"오류 시각: {datetime.now()}\n오류 내용: {str(error)}")
                
    except Exception as e:
        logger.error(f"오류 처리 중 추가 오류: {e}")
        st.markdown("# 시스템 복구 불가")
        st.markdown("브라우저를 새로고침하여 다시 시도해주세요.")

# ================================================================================
# 앱 실행
# ================================================================================

if __name__ == "__main__":
    try:
        main()
    except Exception as critical_error:
        logger.critical(f"앱 실행 중 치명적 오류: {critical_error}")
        handle_critical_error(critical_error)
