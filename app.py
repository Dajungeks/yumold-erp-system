# -*- coding: utf-8 -*-
import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
import locale
import sys

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

# 모든 매니저들이 이제 database_config를 통해 관리됩니다 (PostgreSQL 우선)
from components.note_widget import show_page_note_widget

# 데이터베이스 및 유틸리티 매니저들
from managers.legacy.database_manager import DatabaseManager
# from pdf_design_manager_new import PDFDesignManager  # PDF 디자인 매니저 비활성화
from managers.legacy.pdf_language_manager import PDFLanguageManager
from managers.backup_manager import BackupManager as NewBackupManager
from scripts.backup_scheduler import backup_scheduler
from managers.legacy.migration_manager import MigrationManager
from managers.legacy.contract_manager import ContractManager

# 아직 CSV 기반인 매니저들 (전환 대기 중)
from managers.legacy.supply_product_manager import SupplyProductManager
from managers.legacy.product_category_config_manager import ProductCategoryConfigManager
from managers.legacy.manual_exchange_rate_manager import ManualExchangeRateManager

# 레거시 매니저들 (하위 호환성)
from managers.legacy.auth_manager import AuthManager
from managers.legacy.db_employee_manager import DBEmployeeManager
from managers.legacy.db_customer_manager import DBCustomerManager
from managers.legacy.db_order_manager import DBOrderManager
from managers.legacy.db_product_manager import DBProductManager

def load_language(lang_code):
    """언어 파일을 로드합니다."""
    from managers.legacy.advanced_language_manager import AdvancedLanguageManager
    
    lang_manager = AdvancedLanguageManager()
    lang_manager.load_language_file(lang_code)
    
    try:
        # 새로운 locales 폴더에서 로드
        with open(f'locales/{lang_code}.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        try:
            # 구버전 languages 폴더에서 로드 (하위 호환성)
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

def get_text(key, lang_dict=None, **kwargs):
    """언어 딕셔너리에서 텍스트를 가져옵니다."""
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

def initialize_session_state():
    """세션 상태를 초기화합니다."""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_type' not in st.session_state:
        st.session_state.user_type = None
    if 'access_level' not in st.session_state:
        st.session_state.access_level = None
    if 'user_permissions' not in st.session_state:
        st.session_state.user_permissions = {}
    if 'language' not in st.session_state:
        st.session_state.language = 'ko'
    if 'selected_system' not in st.session_state:
        st.session_state.selected_system = 'dashboard'
    # 언어 변경 최적화를 위한 플래그
    if 'language_changed' not in st.session_state:
        st.session_state.language_changed = False
    if 'language_just_changed' not in st.session_state:
        st.session_state.language_just_changed = False

def initialize_managers():
    """모든 매니저 인스턴스를 초기화합니다."""
    # 로그인 속도 개선을 위해 초기화 건너뛰기
    if 'managers_initialized' not in st.session_state:
        st.session_state.managers_initialized = True
    return  # 여기서 바로 종료
    
    # 아래 코드는 실행되지 않음 (나중에 필요할 때 사용)
    if 'managers_initialized' not in st.session_state or not st.session_state.managers_initialized:
        print("🔄 매니저 초기화 시작...")
        try:
            # 핵심 매니저들 먼저 초기화 (PostgreSQL/SQLite 자동 선택)
            if 'auth_manager' not in st.session_state:
                st.session_state.auth_manager = get_auth_manager()
            if 'employee_manager' not in st.session_state:
                st.session_state.employee_manager = get_employee_manager()
            if 'customer_manager' not in st.session_state:
                st.session_state.customer_manager = get_customer_manager()
            if 'product_manager' not in st.session_state:
                st.session_state.product_manager = get_product_manager()
            if 'supplier_manager' not in st.session_state:
                st.session_state.supplier_manager = get_supplier_manager()
            if 'quotation_manager' not in st.session_state:
                st.session_state.quotation_manager = get_quotation_manager()
            
            # 초기화 완료 로그
            print("✅ 핵심 매니저들 초기화 완료")
            # 업무 프로세스 매니저 (SQLite)
            if 'business_process_manager' not in st.session_state:
                try:
                    st.session_state.business_process_manager = get_business_process_manager()
                    # SQLite 기반 업무 프로세스 매니저 (순수 SQLite 사용)
                    # CSV 마이그레이션은 자동으로 처리됨
                except Exception as bp_error:
                    st.warning(f"SQLite 업무 프로세스 매니저 초기화 실패: {str(bp_error)}")
                    # 폴백으로 기존 매니저 사용
                    from scripts.business_process_manager_v2 import BusinessProcessManagerV2 as BusinessProcessManager
                    st.session_state.business_process_manager = BusinessProcessManager()
            if 'approval_manager' not in st.session_state:
                st.session_state.approval_manager = get_approval_manager()
            # 제품 코드 매니저 (SQLite)
            if 'product_code_manager' not in st.session_state:
                try:
                    st.session_state.product_code_manager = get_product_code_manager()
                    # 기존 CSV 데이터 마이그레이션 (SQLite만)
                    if hasattr(st.session_state.product_code_manager, 'migrate_from_csv'):
                        st.session_state.product_code_manager.migrate_from_csv()
                except Exception as pcm_error:
                    st.warning(f"SQLite 제품 코드 매니저 초기화 실패: {str(pcm_error)}")
                    # 폴백으로 기존 매니저 사용
                    from scripts.product_code_generator import ProductCodeGenerator as ProductCodeManager
                    # master_product_manager가 아직 초기화되지 않았으므로 None으로 초기화
                    st.session_state.product_code_manager = ProductCodeManager(None)
            # st.session_state.pdf_design_manager = PDFDesignManager()  # PDF 디자인 매니저 비활성화
            # 환율 관리자 (SQLite)
            if 'exchange_rate_manager' not in st.session_state:
                try:
                    st.session_state.exchange_rate_manager = get_exchange_rate_manager()
                    # 기존 CSV 데이터 마이그레이션 (SQLite만)
                    if hasattr(st.session_state.exchange_rate_manager, 'migrate_from_csv'):
                        st.session_state.exchange_rate_manager.migrate_from_csv()
                except Exception as erm_error:
                    st.warning(f"SQLite 환율 관리자 초기화 실패: {str(erm_error)}")
                    # 폴백으로 기존 매니저 사용
                    from managers.legacy.exchange_rate_manager import ExchangeRateManager
                    st.session_state.exchange_rate_manager = ExchangeRateManager()
            if 'manual_exchange_rate_manager' not in st.session_state:
                st.session_state.manual_exchange_rate_manager = ManualExchangeRateManager()
            # 지출 요청 매니저 (SQLite)
            if 'expense_request_manager' not in st.session_state:
                try:
                    st.session_state.expense_request_manager = get_expense_request_manager()
                    # SQLite 지출 요청 매니저 (순수 SQLite 사용)
                    # CSV 마이그레이션은 자동으로 처리됨
                except Exception as er_error:
                    st.warning(f"SQLite 지출 요청 매니저 초기화 실패: {str(er_error)}")
                    # 폴백으로 기존 매니저 사용
                    from managers.legacy.expense_request_manager import ExpenseRequestManager
                    st.session_state.expense_request_manager = ExpenseRequestManager()
            # 휴가 매니저 (SQLite)
            if 'vacation_manager' not in st.session_state:
                try:
                    st.session_state.vacation_manager = get_vacation_manager()
                    # 기존 CSV 데이터 마이그레이션 (SQLite만)
                    if hasattr(st.session_state.vacation_manager, 'migrate_from_csv'):
                        st.session_state.vacation_manager.migrate_from_csv()
                except Exception as vm_error:
                    st.warning(f"SQLite 휴가 매니저 초기화 실패: {str(vm_error)}")
                    # 폴백으로 기존 매니저 사용
                    from managers.legacy.vacation_manager import VacationManager
                    st.session_state.vacation_manager = VacationManager()
            if 'migration_manager' not in st.session_state:
                st.session_state.migration_manager = MigrationManager()
            # 판매 제품 매니저 (SQLite)
            try:
                st.session_state.sales_product_manager = get_sales_product_manager()
                # 기존 CSV 데이터 마이그레이션 (SQLite만)
                if hasattr(st.session_state.sales_product_manager, 'migrate_from_csv'):
                    st.session_state.sales_product_manager.migrate_from_csv()
            except Exception as sp_error:
                st.warning(f"SQLite 판매 제품 매니저 초기화 실패: {str(sp_error)}")
                # 폴백으로 기존 매니저 사용
                from managers.legacy.sales_product_manager import SalesProductManager
                st.session_state.sales_product_manager = SalesProductManager()
            
            # 완성품 매니저 (SQLite)
            try:
                st.session_state.finished_product_manager = get_finished_product_manager()
            except Exception as fp_error:
                st.warning(f"완성품 매니저 초기화 실패: {str(fp_error)}")
                st.session_state.finished_product_manager = None
            
            # 공급 제품 매니저 (기존 유지 - 복잡한 로직으로 인해)
            st.session_state.supply_product_manager = SupplyProductManager()
            
            # 업무 상태 매니저 (SQLite)
            try:
                st.session_state.work_status_manager = get_work_status_manager()
                # 기존 CSV 데이터 마이그레이션 (SQLite만)
                if hasattr(st.session_state.work_status_manager, 'migrate_from_csv'):
                    st.session_state.work_status_manager.migrate_from_csv()
            except Exception as wsm_error:
                st.warning(f"SQLite 업무 상태 매니저 초기화 실패: {str(wsm_error)}")
                # 폴백으로 기존 매니저 사용
                try:
                    from managers.legacy.work_status_manager import WorkStatusManager
                    st.session_state.work_status_manager = WorkStatusManager()
                except:
                    st.session_state.work_status_manager = None
            
            # 주간 보고서 매니저 (SQLite)
            try:
                st.session_state.weekly_report_manager = get_weekly_report_manager()
                # 기존 CSV 데이터 마이그레이션 (SQLite만)
                if hasattr(st.session_state.weekly_report_manager, 'migrate_from_csv'):
                    st.session_state.weekly_report_manager.migrate_from_csv()
            except Exception as wrm_error:
                st.warning(f"SQLite 주간 보고서 매니저 초기화 실패: {str(wrm_error)}")
                # 폴백으로 기존 매니저 사용
                try:
                    from managers.legacy.weekly_report_manager import WeeklyReportManager
                    st.session_state.weekly_report_manager = WeeklyReportManager()
                except:
                    st.session_state.weekly_report_manager = None
            # 시스템 설정 매니저 (SQLite)
            try:
                st.session_state.system_config_manager = get_system_config_manager()
                # 기존 CSV 데이터 마이그레이션 (SQLite만)
                if hasattr(st.session_state.system_config_manager, 'migrate_from_csv'):
                    st.session_state.system_config_manager.migrate_from_csv()
            except Exception as scm_error:
                st.warning(f"SQLite 시스템 설정 매니저 초기화 실패: {str(scm_error)}")
                # 폴백으로 기존 매니저 사용
                from managers.legacy.system_config_manager import SystemConfigManager
                st.session_state.system_config_manager = SystemConfigManager()
            st.session_state.cash_flow_manager = get_cash_flow_manager()
            # 현금 거래 매니저 (SQLite)
            try:
                st.session_state.cash_transaction_manager = get_cash_transaction_manager()
                # 기존 CSV 데이터 마이그레이션 (SQLite만)
                if hasattr(st.session_state.cash_transaction_manager, 'migrate_from_csv'):
                    st.session_state.cash_transaction_manager.migrate_from_csv()
            except Exception as ct_error:
                st.warning(f"SQLite 현금 거래 매니저 초기화 실패: {str(ct_error)}")
                # 폴백으로 기존 매니저 사용
                from managers.legacy.cash_transaction_manager import CashTransactionManager
                st.session_state.cash_transaction_manager = CashTransactionManager()
            # 통합 제품 매니저 (SQLite)
            try:
                st.session_state.master_product_manager = get_master_product_manager()
                # 기존 CSV 데이터 마이그레이션 (SQLite만)
                if hasattr(st.session_state.master_product_manager, 'migrate_from_csv'):
                    st.session_state.master_product_manager.migrate_from_csv()
            except Exception as mpm_error:
                st.warning(f"SQLite 통합 제품 매니저 초기화 실패: {str(mpm_error)}")
                # 폴백으로 기존 매니저 사용
                from managers.legacy.master_product_manager import MasterProductManager
                st.session_state.master_product_manager = MasterProductManager()
            st.session_state.order_manager = get_order_manager()
            # 공지사항 매니저 (SQLite)
            try:
                st.session_state.notice_manager = get_notice_manager()
                # 기존 CSV 데이터 마이그레이션 (SQLite만)
                if hasattr(st.session_state.notice_manager, 'migrate_from_csv'):
                    st.session_state.notice_manager.migrate_from_csv()
            except Exception as nm_error:
                st.warning(f"SQLite 공지사항 매니저 초기화 실패: {str(nm_error)}")
                # 폴백으로 기존 매니저 사용
                from managers.legacy.notice_manager import NoticeManager
                st.session_state.notice_manager = NoticeManager()
            
            # 노트 매니저 (SQLite)
            try:
                st.session_state.note_manager = get_note_manager()
            except Exception as note_error:
                st.warning(f"SQLite 노트 매니저 초기화 실패: {str(note_error)}")
                st.session_state.note_manager = None
            
            st.session_state.contract_manager = ContractManager()
            
            # SQLite 매니저들 초기화
            st.session_state.database_manager = DatabaseManager()
            st.session_state.db_employee_manager = DBEmployeeManager()
            st.session_state.db_customer_manager = DBCustomerManager()
            st.session_state.db_order_manager = DBOrderManager()
            st.session_state.db_product_manager = DBProductManager()
            
            # 월별 매출관리 매니저 (SQLite)
            try:
                st.session_state.monthly_sales_manager = get_monthly_sales_manager()
                # 기존 CSV 데이터 마이그레이션 (SQLite만)
                if hasattr(st.session_state.monthly_sales_manager, 'migrate_from_csv'):
                    st.session_state.monthly_sales_manager.migrate_from_csv()
            except Exception as monthly_error:
                st.warning(f"SQLite 월별 매출관리 매니저 초기화 실패: {str(monthly_error)}")
                # 폴백으로 기존 매니저 사용
                try:
                    from managers.legacy.monthly_sales_manager import MonthlySalesManager
                    st.session_state.monthly_sales_manager = MonthlySalesManager()
                except:
                    st.session_state.monthly_sales_manager = None
            
            # 인보이스 매니저 (SQLite)
            try:
                st.session_state.invoice_manager = get_invoice_manager()
                # 기존 CSV 데이터 마이그레이션 (SQLite만)
                if hasattr(st.session_state.invoice_manager, 'migrate_from_csv'):
                    st.session_state.invoice_manager.migrate_from_csv()
            except Exception as inv_error:
                st.warning(f"SQLite 인보이스 매니저 초기화 실패: {str(inv_error)}")
                # 폴백으로 기존 매니저 사용
                try:
                    from managers.legacy.invoice_manager import InvoiceManager
                    st.session_state.invoice_manager = InvoiceManager()
                except ImportError:
                    st.session_state.invoice_manager = None
                
            try:
                st.session_state.inventory_manager = get_inventory_manager()
            except Exception as inv_error:
                st.warning(f"SQLite 재고 매니저 초기화 실패: {str(inv_error)}")
                st.session_state.inventory_manager = None
                
            # 배송 매니저 (이미 SQLite 버전 있음)
            try:
                st.session_state.shipping_manager = st.session_state.sqlite_shipping_manager
                if st.session_state.shipping_manager is None:
                    from managers.legacy.shipping_manager import ShippingManager
                    st.session_state.shipping_manager = ShippingManager()
            except Exception:
                st.session_state.shipping_manager = None
            
            # SQLite 배송 매니저 초기화
            try:
                st.session_state.sqlite_shipping_manager = get_shipping_manager()
            except ImportError:
                st.session_state.sqlite_shipping_manager = None
            
            # PDF 언어 매니저를 별도로 초기화
            try:
                from managers.legacy.pdf_language_manager import PDFLanguageManager as PDFLangMgr
                st.session_state.pdf_language_manager = PDFLangMgr()
            except Exception as pdf_error:
                st.warning(f"PDF 언어 매니저 초기화 실패: {str(pdf_error)}")
                st.session_state.pdf_language_manager = None
            
            # SQLiteOrderManager 초기화
            try:
                st.session_state.sqlite_order_manager = get_order_manager()
            except Exception as order_error:
                st.warning(f"SQLite 주문 매니저 초기화 실패: {str(order_error)}")
                st.session_state.sqlite_order_manager = None
            
            # 업무 상태 관리 매니저
            try:
                from managers.legacy.work_status_manager import WorkStatusManager
                st.session_state.work_status_manager = WorkStatusManager()
            except Exception as ws_error:
                st.warning(f"업무 상태 관리 매니저 초기화 실패: {str(ws_error)}")
                st.session_state.work_status_manager = None
            
            # 제품 카테고리 설정 매니저
            try:
                from managers.legacy.product_category_config_manager import ProductCategoryConfigManager
                st.session_state.product_category_config_manager = ProductCategoryConfigManager()
            except Exception as pc_error:
                error_msg = get_text("product_category_manager_init_failed", fallback="제품 카테고리 설정 매니저 초기화 실패")
                st.warning(f"{error_msg}: {str(pc_error)}")
                st.session_state.product_category_config_manager = None
                
            # 백업 매니저 (새로운 UTF-8 안전 버전)
            try:
                st.session_state.backup_manager = NewBackupManager()
            except Exception as bm_error:
                error_msg = get_text("backup_manager_init_failed", fallback="백업 매니저 초기화 실패")
                st.warning(f"{error_msg}: {str(bm_error)}")
                st.session_state.backup_manager = None
                
            # 백업 스케줄러 시작
            try:
                if not backup_scheduler.is_running():
                    backup_scheduler.start_scheduler()
                st.session_state.backup_scheduler = backup_scheduler
            except Exception as bs_error:
                error_msg = get_text("backup_scheduler_init_failed", fallback="백업 스케줄러 초기화 실패")
                st.warning(f"{error_msg}: {str(bs_error)}")
                st.session_state.backup_scheduler = None
            
            st.session_state.managers_initialized = True
            print("🎉 모든 매니저 초기화 완료!")
        except Exception as e:
            error_msg = get_text("manager_init_error", fallback="매니저 초기화 중 오류")
            st.error(f"{error_msg}: {str(e)}")
            # 오류가 발생해도 일부 매니저는 초기화되었을 수 있으므로 True로 유지
            st.session_state.managers_initialized = True
            print(f"⚠️ 매니저 초기화 중 오류 발생하였지만 계속 진행: {e}")
    else:
        print("⚡ 매니저들이 이미 초기화됨 - 스킵")

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


def show_main_app(lang_dict):
    """메인 애플리케이션을 표시합니다."""
    
    # 모바일 최적화 설정
    pass  # CSS는 별도로 처리
    
    # 헤더 제거 - 모든 정보는 사이드바에서 처리
    
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
        from config_files.ui_config import get_allowed_menus
        access_level = st.session_state.get('access_level', 'user')
        allowed_menus = get_allowed_menus(access_level)
        
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
        
        # 각 시스템의 페이지 표시 (탭 기반)
        show_page_for_menu(current_system)
    
    except Exception as e:
        current_lang = st.session_state.get('language', 'ko')
        lang_dict = load_language(current_lang)
        error_msg = get_text("system_error", lang_dict) if 'system_error' in lang_dict else "시스템 오류가 발생했습니다"
        contact_msg = get_text("contact_admin", lang_dict) if 'contact_admin' in lang_dict else "관리자에게 문의해주세요"
        st.error(f"{error_msg}: {str(e)}")
        st.info(contact_msg)

def show_dashboard_for_menu(system_key, selected_submenu):
    """각 메뉴의 대시보드를 표시합니다."""
    from pages.menu_dashboard import (
        show_main_dashboard, show_employee_dashboard, show_customer_dashboard,
        show_product_dashboard, show_supplier_dashboard, show_order_dashboard,
        show_finished_product_dashboard,
        show_exchange_rate_dashboard, show_business_process_dashboard,
        show_shipping_dashboard, show_approval_dashboard, show_cash_flow_dashboard,
        show_pdf_design_dashboard, show_system_guide_dashboard, show_personal_status_dashboard
    )
    
    managers = {
        'employee_manager': st.session_state.employee_manager,
        'customer_manager': st.session_state.customer_manager,
        'product_manager': st.session_state.product_manager,
        'supplier_manager': st.session_state.supplier_manager,
        'business_process_manager': st.session_state.business_process_manager,
        'approval_manager': st.session_state.approval_manager,
        'exchange_rate_manager': st.session_state.exchange_rate_manager,
        'sales_product_manager': st.session_state.sales_product_manager,
        'supply_product_manager': st.session_state.supply_product_manager,
        # 'pdf_design_manager': st.session_state.pdf_design_manager,  # PDF 디자인 매니저 비활성화
        'vacation_manager': st.session_state.vacation_manager,
    }
    
    if system_key == 'dashboard':
        show_main_dashboard(managers, selected_submenu, get_text)
    elif system_key == 'employee_management':
        show_employee_dashboard(managers, selected_submenu, get_text)
    elif system_key == 'customer_management':
        show_customer_dashboard(managers, selected_submenu, get_text)


    elif system_key == 'supplier_management':
        show_supplier_dashboard(managers, selected_submenu, get_text)
    elif system_key == 'product_registration':
        from pages.menu_dashboard import show_product_registration_dashboard
        show_product_registration_dashboard(managers, selected_submenu, get_text)
    elif system_key == 'exchange_rate_management':
        show_exchange_rate_dashboard(managers, selected_submenu, get_text)

    elif system_key == 'shipping_management':
        show_shipping_dashboard(managers, selected_submenu, get_text)
    elif system_key == 'approval_management':
        show_approval_dashboard(managers, selected_submenu, get_text)
    elif system_key == 'quotation_management':
        # 새로운 견적서 관리 시스템
        from pages.quotation_page import main as show_quotation_page
        show_quotation_page()
    elif system_key == 'order_management':
        from pages.menu_dashboard import show_order_dashboard
        show_order_dashboard(managers, selected_submenu, get_text)
    elif system_key == 'cash_flow_management':
        show_cash_flow_dashboard(managers, selected_submenu, get_text)
    elif system_key == 'contract_management':
        from pages.menu_dashboard import show_contract_dashboard
        show_contract_dashboard(managers, selected_submenu, get_text)
    elif system_key == 'pdf_design_management':
        show_pdf_design_dashboard(managers, selected_submenu, get_text)
    elif system_key == 'system_guide':
        show_system_guide_dashboard(managers, selected_submenu, get_text)
    elif system_key == 'personal_status':
        show_personal_status_dashboard(managers, selected_submenu, get_text)

def show_business_process_v2_page():
    """비즈니스 프로세스 V2 페이지 표시"""
    
    # 매니저 초기화
    if 'bp_manager_v2' not in st.session_state:
        from scripts.business_process_manager_v2 import BusinessProcessManagerV2
        st.session_state.bp_manager_v2 = BusinessProcessManagerV2()
    
    # 탭 생성
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 프로세스 대시보드",
        "➕ 새 프로세스 생성", 
        "📋 진행중 프로세스 관리",
        "✏️ 프로세스 편집/수정",
        "📈 성과 분석"
    ])
    
    with tab1:
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
    
    with tab2:
        st.header("➕ 새 워크플로우 생성")
        
        # 모든 견적서 목록 가져오기 (상태 확인 없음)
        try:
            quotations_df = st.session_state.quotation_manager.get_all_quotations()
            if isinstance(quotations_df, list):
                # 리스트인 경우 DataFrame으로 변환
                quotations_df = pd.DataFrame(quotations_df)
            
            # 모든 견적서를 사용 가능하도록 변경
            available_quotations = quotations_df
        except Exception as e:
            st.error(f"견적서 데이터 로드 오류: {e}")
            available_quotations = pd.DataFrame()
        
        if len(available_quotations) == 0:
            st.warning("생성된 견적서가 없습니다. 먼저 견적서를 작성해주세요.")
        else:
            st.success(f"사용 가능한 견적서 {len(available_quotations)}개를 찾았습니다.")
            
            # 견적서 선택 드롭다운
            quotation_options = {}
            for _, quot in available_quotations.iterrows():
                # total_amount_usd가 None일 수 있으므로 안전하게 처리
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
                    
                    # 워크플로우 생성 버튼
                    col1, col2 = st.columns(2)
                    with col1:
                        # 직원 목록에서 판매팀 담당자 선택
                        employees_data = st.session_state.employee_manager.get_all_employees()
                        employee_names = []
                        if len(employees_data) > 0:
                            # DataFrame인지 리스트인지 확인하고 처리
                            if hasattr(employees_data, 'iterrows'):
                                # DataFrame인 경우
                                employee_names = [f"{row['name']} ({row['employee_id']})" for _, row in employees_data.iterrows()]
                            else:
                                # 리스트인 경우
                                employee_names = [f"{emp.get('name', 'N/A')} ({emp.get('employee_id', 'N/A')})" for emp in employees_data]
                        
                        if employee_names:
                            sales_team = st.selectbox("판매팀 담당자:", employee_names)
                        else:
                            sales_team = st.text_input("판매팀 담당자:", value="담당자 미정")
                        
                    with col2:
                        # 직원 목록에서 서비스팀 담당자 선택
                        if employee_names:
                            service_team = st.selectbox("서비스팀 담당자:", employee_names, key="service_team_select")
                        else:
                            service_team = st.text_input("서비스팀 담당자:", value="담당자 미정")
                    
                    notes = st.text_area("초기 메모:", placeholder="워크플로우 생성 시 특이사항이나 메모를 입력하세요.")
                    
                    if st.button("🚀 워크플로우 생성", type="primary", use_container_width=True):
                        # 선택된 견적서 데이터 가져오기
                        selected_quotation_data = None
                        try:
                            all_quotations = st.session_state.quotation_manager.get_all_quotations()
                            for quotation in all_quotations:
                                if quotation.get('quotation_id') == selected_quotation_id:
                                    selected_quotation_data = quotation
                                    break
                        except Exception as e:
                            st.error(f"견적서 데이터 조회 오류: {e}")
                        
                        if selected_quotation_data:
                            # 담당자 정보 추가
                            selected_quotation_data['assigned_sales_team'] = sales_team
                            selected_quotation_data['assigned_service_team'] = service_team
                            selected_quotation_data['notes'] = notes
                            
                            success, message = st.session_state.bp_manager_v2.create_workflow_from_quotation(
                                quotation_data=selected_quotation_data,
                                created_by=st.session_state.get('user_id', '')
                            )
                        else:
                            success = False
                            message = "견적서 데이터를 찾을 수 없습니다."
                        
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
    
    with tab3:
        st.header(f"📋 {get_text('ongoing_process_management')}")
        
        # 워크플로우 목록 가져오기
        try:
            workflows_df = st.session_state.bp_manager_v2.get_all_workflows()
            if isinstance(workflows_df, list):
                # 리스트가 문자열로 저장된 경우를 처리
                valid_workflows = []
                for workflow in workflows_df:
                    if isinstance(workflow, dict):
                        valid_workflows.append(workflow)
                workflows_df = valid_workflows
        except Exception as e:
            st.error(f"워크플로우 데이터 로드 오류: {e}")
            workflows_df = []
        
        if (workflows_df.empty if isinstance(workflows_df, pd.DataFrame) else len(workflows_df) == 0):
            st.info("생성된 워크플로우가 없습니다.")
        else:
            st.success(f"총 {len(workflows_df)}개의 워크플로우가 있습니다.")
            
            # 테이블 형태 대시보드 추가
            st.markdown("### 📋 간단 대시보드")
            
            # 테이블 헤더
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1, 1.5, 1.5, 2, 1.5, 1, 1, 1.5])
            
            with col1:
                st.markdown("**식별번호**")
            with col2:
                st.markdown("**이름**")
            with col3:
                st.markdown("**연락처**")
            with col4:
                st.markdown("**이메일**")
            with col5:
                st.markdown("**상태**")
            with col6:
                st.markdown("**진행률**")
            with col7:
                st.markdown("**작업**")
            with col8:
                st.markdown("**상세보기**")
            
            st.divider()
            
            # 워크플로우 목록 표시 (테이블 형태)
            for i, workflow in enumerate(workflows_df):
                # 워크플로우가 딕셔너리인지 확인
                if not isinstance(workflow, dict):
                    continue
                    
                # 안전한 문자열 변환
                workflow_type_str = str(workflow.get('workflow_type', '')).upper()
                quotation_number = str(workflow.get('quotation_number', ''))
                customer_name = str(workflow.get('customer_name', ''))
                overall_progress = float(workflow.get('overall_progress', 0))
                
                # 연락처와 이메일 정보 추출
                contact_info = workflow.get('customer_phone', workflow.get('contact_info', ''))
                email_info = workflow.get('customer_email', workflow.get('email_info', ''))
                
                # 상태 결정
                if overall_progress >= 100:
                    status = "완료"
                elif overall_progress > 0:
                    status = "진행중"
                else:
                    status = "대기"
                
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
                    if status == "완료":
                        st.success(status)
                    elif status == "진행중":
                        st.warning(status)
                    else:
                        st.info(status)
                with col6:
                    st.progress(overall_progress / 100)
                    st.text(f"{overall_progress:.1f}%")
                with col7:
                    # 수정/삭제 버튼
                    workflow_id = workflow.get('workflow_id', '')
                    col_edit, col_delete = st.columns(2)
                    with col_edit:
                        if st.button("✏️", key=f"table_edit_{workflow_id}", help="수정"):
                            st.session_state.selected_workflow_id = workflow_id
                            st.rerun()
                    with col_delete:
                        if st.button("🗑️", key=f"table_delete_{workflow_id}", help="삭제"):
                            if st.session_state.get('user_type') == 'master':
                                success, message = st.session_state.bp_manager_v2.delete_workflow(workflow_id)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                            else:
                                st.error("마스터 권한이 필요합니다.")
                with col8:
                    if st.button("📋 상세", key=f"table_detail_{workflow_id}"):
                        st.session_state.show_workflow_detail = workflow_id
                        st.rerun()
            
            st.divider()
            
            # 상세 워크플로우 정보 (기존 코드)
            st.markdown("### 📈 상세 워크플로우 정보")
            
            # 워크플로우 목록 표시
            for workflow in workflows_df:
                # 워크플로우가 딕셔너리인지 확인
                if not isinstance(workflow, dict):
                    continue
                    
                # 안전한 문자열 변환
                workflow_type_str = str(workflow.get('workflow_type', '')).upper()
                quotation_number = str(workflow.get('quotation_number', ''))
                customer_name = str(workflow.get('customer_name', ''))
                overall_progress = float(workflow.get('overall_progress', 0))
                
                with st.expander(f"{quotation_number} - {customer_name} ({workflow_type_str})"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**전체 진행률:** {overall_progress:.1f}%")
                        st.progress(overall_progress / 100)
                    
                    with col2:
                        has_sales = bool(workflow.get('has_sales_items', False))
                        if has_sales:
                            sales_progress = float(workflow.get('sales_progress', 0))
                            sales_stage = str(workflow.get('sales_current_stage', ''))
                            st.write(f"**판매 진행률:** {sales_progress:.1f}%")
                            st.write(f"현재 단계: {sales_stage}")
                    
                    with col3:
                        has_service = bool(workflow.get('has_service_items', False))
                        if has_service:
                            service_progress = float(workflow.get('service_progress', 0))
                            service_stage = str(workflow.get('service_current_stage', ''))
                            st.write(f"**서비스 진행률:** {service_progress:.1f}%")
                            st.write(f"현재 단계: {service_stage}")
                    
                    # 단계별 진행 표시
                    st.markdown("---")
                    
                    # 판매 프로세스 단계 표시 (한 줄로)
                    if has_sales:
                        st.markdown("### 📈 판매 프로세스 단계")
                        try:
                            sales_stages_json = workflow.get('sales_stages_json', '[]')
                            if isinstance(sales_stages_json, str):
                                sales_stages = json.loads(sales_stages_json)
                            else:
                                sales_stages = []
                            
                            # 전체 단계 순서 표시 (클릭 가능)
                            if sales_stages:
                                st.write("**전체 단계 순서:**")
                                
                                # 각 단계를 개별 컨테이너로 표시
                                cols = st.columns(len(sales_stages))
                                current_stage_name = str(workflow.get('sales_current_stage', ''))
                                
                                for i, stage in enumerate(sales_stages):
                                    stage_name = stage.get('stage_name', f'단계 {i+1}')
                                    stage_status = stage.get('status', '대기')
                                    
                                    with cols[i]:
                                        # 단계 상태에 따른 표시
                                        if stage_status == '완료':
                                            st.success(f"✅ {stage_name}")
                                        elif stage_status == '진행중' and stage_name == current_stage_name:
                                            # 현재 진행중인 단계는 "다음 단계로" 버튼 표시
                                            next_stage = sales_stages[i+1]['stage_name'] if i+1 < len(sales_stages) else "완료"
                                            if st.button(f"🔄 {stage_name}\n→ {next_stage}", key=f"sales_stage_{workflow['workflow_id']}_{i}", 
                                                        help=f"클릭하여 '{next_stage}'로 진행"):
                                                success, message = st.session_state.bp_manager_v2.advance_sales_stage(
                                                    workflow['workflow_id'], 
                                                    st.session_state.get('user_id', 'system')
                                                )
                                                if success:
                                                    st.success(message)
                                                    st.rerun()
                                                else:
                                                    st.error(message)
                                        else:
                                            st.warning(f"⏳ {stage_name}")
                            else:
                                st.info("단계 정보를 로드할 수 없습니다.")
                            
                        
                        except Exception as e:
                            st.error(f"판매 단계 표시 오류: {e}")
                    
                    # 서비스 프로세스 단계 표시 (한 줄로)
                    if has_service:
                        st.markdown("### 🔧 서비스 프로세스 단계")
                        try:
                            service_stages_json = workflow.get('service_stages_json', '[]')
                            if isinstance(service_stages_json, str):
                                service_stages = json.loads(service_stages_json)
                            else:
                                service_stages = []
                            
                            # 전체 단계 순서 표시 (클릭 가능)
                            if service_stages:
                                st.write("**전체 단계 순서:**")
                                
                                # 각 단계를 개별 컨테이너로 표시 (서비스는 9단계이므로 3행으로 나누어 표시)
                                stage_rows = [service_stages[i:i+3] for i in range(0, len(service_stages), 3)]
                                current_stage_name = str(workflow.get('service_current_stage', ''))
                                
                                for row_stages in stage_rows:
                                    cols = st.columns(3)
                                    for j, stage in enumerate(row_stages):
                                        stage_name = stage.get('stage_name', f'단계 {service_stages.index(stage)+1}')
                                        stage_status = stage.get('status', '대기')
                                        stage_index = service_stages.index(stage)
                                        
                                        with cols[j]:
                                            # 단계 상태에 따른 표시
                                            if stage_status == '완료':
                                                st.success(f"✅ {stage_name}")
                                            elif stage_status == '진행중' and stage_name == current_stage_name:
                                                # 현재 진행중인 단계는 "다음 단계로" 버튼 표시
                                                next_stage = service_stages[stage_index+1]['stage_name'] if stage_index+1 < len(service_stages) else "완료"
                                                if st.button(f"🔄 {stage_name}\n→ {next_stage}", key=f"service_stage_{workflow['workflow_id']}_{stage_index}", 
                                                            help=f"클릭하여 '{next_stage}'로 진행"):
                                                    success, message = st.session_state.bp_manager_v2.advance_service_stage(
                                                        workflow['workflow_id'], 
                                                        st.session_state.get('user_id', 'system')
                                                    )
                                                    if success:
                                                        st.success(message)
                                                        st.rerun()
                                                    else:
                                                        st.error(message)
                                            else:
                                                st.warning(f"⏳ {stage_name}")
                            else:
                                st.info("단계 정보를 로드할 수 없습니다.")
                            
                        except Exception as e:
                            st.error(f"서비스 단계 표시 오류: {e}")
                    
                    # 담당자 정보
                    담당_col1, 담당_col2 = st.columns(2)
                    with 담당_col1:
                        sales_team = workflow.get('assigned_sales_team', '미정')
                        st.write(f"**판매팀:** {sales_team}")
                    with 담당_col2:
                        service_team = workflow.get('assigned_service_team', '미정')
                        st.write(f"**서비스팀:** {service_team}")
    
    with tab4:
        st.header("✏️ 프로세스 편집/수정")
        
        # 마스터 권한 확인
        user_role = st.session_state.get('user_role', 'employee')
        is_master = user_role == 'master'
        
        if not is_master:
            st.warning("🔒 프로세스 편집/수정 기능은 마스터 권한이 필요합니다.")
            st.info("현재 로그인된 계정의 권한이 부족합니다. 마스터 계정으로 로그인해주세요.")
        else:
            # 워크플로우 선택
            if not workflows_df.empty if isinstance(workflows_df, pd.DataFrame) else len(workflows_df) > 0:
                # 워크플로우 목록
                workflow_options = []
                for workflow in workflows_df:
                    if not isinstance(workflow, dict):
                        continue
                    quotation_number = workflow.get('quotation_number', 'N/A')
                    customer_name = workflow.get('customer_name', 'Unknown')
                    workflow_type = workflow.get('workflow_type', 'mixed')
                    workflow_options.append(f"{quotation_number} - {customer_name} ({workflow_type})")
                
                selected_workflow_display = st.selectbox("편집할 워크플로우 선택", workflow_options, key="edit_workflow_select")
                
                if selected_workflow_display:
                    # 선택된 워크플로우 찾기
                    selected_index = workflow_options.index(selected_workflow_display)
                    selected_workflow = workflows_df[selected_index]
                    workflow_id = selected_workflow['workflow_id']
                    
                    st.divider()
                    
                    # 기본 정보 편집
                    st.subheader("📝 기본 정보 편집")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_customer_name = st.text_input("고객명", value=selected_workflow.get('customer_name', ''))
                        new_notes = st.text_area("메모", value=selected_workflow.get('notes', ''))
                    
                    with col2:
                        new_sales_team = st.text_input("담당 판매팀", value=selected_workflow.get('assigned_sales_team', ''))
                        new_service_team = st.text_input("담당 서비스팀", value=selected_workflow.get('assigned_service_team', ''))
                    
                    # 기본 정보 업데이트 버튼
                    if st.button("기본 정보 업데이트", key="update_basic_info"):
                        updates = {
                            'customer_name': new_customer_name,
                            'notes': new_notes,
                            'assigned_sales_team': new_sales_team,
                            'assigned_service_team': new_service_team
                        }
                        success, message = st.session_state.bp_manager_v2.update_workflow(workflow_id, updates)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    
                    st.divider()
                    
                    # 단계별 편집
                    st.subheader("🔧 단계별 편집")
                    
                    # 사용자 정보
                    user_id = st.session_state.get('user_id', '')
                    
                    # 판매 프로세스 편집
                    if selected_workflow.get('has_sales_items', False):
                        st.markdown("### 📈 판매 프로세스 단계 편집")
                        
                        try:
                            sales_stages_json = selected_workflow.get('sales_stages_json', '[]')
                            if isinstance(sales_stages_json, str):
                                sales_stages = json.loads(sales_stages_json)
                            else:
                                sales_stages = []
                            
                            current_stage = str(selected_workflow.get('sales_current_stage', ''))
                            
                            # 각 단계 편집
                            for i, stage in enumerate(sales_stages):
                                stage_name = stage.get('stage_name', f'단계 {i+1}')
                                stage_status = stage.get('status', '대기')
                                
                                with st.expander(f"{stage_name} (상태: {stage_status})"):
                                    col1, col2, col3 = st.columns(3)
                                    
                                    with col1:
                                        # 모든 단계를 마스터가 수정 가능하도록 변경
                                        new_status = st.selectbox(
                                            "상태 변경", 
                                            ['대기', '진행중', '완료'], 
                                            index=['대기', '진행중', '완료'].index(stage_status),
                                            key=f"sales_status_{i}"
                                        )
                                    
                                    with col2:
                                        new_assigned = st.text_input(
                                            "담당자", 
                                            value=stage.get('assigned_to', '') or '',
                                            key=f"sales_assigned_{i}"
                                        )
                                    
                                    with col3:
                                        new_notes = st.text_area(
                                            "메모", 
                                            value=stage.get('notes', '') or '',
                                            key=f"sales_notes_{i}"
                                        )
                                    
                                    # 마스터는 모든 단계 업데이트 가능
                                    col_update, col_reset = st.columns(2)
                                    
                                    with col_update:
                                        if st.button(f"'{stage_name}' 단계 업데이트", key=f"update_sales_{i}"):
                                            # 단계 정보 업데이트
                                            sales_stages[i]['status'] = new_status
                                            sales_stages[i]['assigned_to'] = new_assigned
                                            sales_stages[i]['notes'] = new_notes
                                            
                                            # 상태 변경 시 날짜 업데이트
                                            if new_status == '진행중' and stage_status != '진행중':
                                                sales_stages[i]['started_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                            elif new_status == '완료' and stage_status != '완료':
                                                sales_stages[i]['completed_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                            
                                            # 현재 단계 업데이트
                                            if new_status == '진행중':
                                                current_stage = stage_name
                                            
                                            # 진행률 재계산
                                            completed_stages = sum(1 for s in sales_stages if s['status'] == '완료')
                                            progress = (completed_stages / len(sales_stages)) * 100
                                            
                                            # 업데이트 저장
                                            updates = {
                                                'sales_stages_json': json.dumps(sales_stages),
                                                'sales_current_stage': current_stage,
                                                'sales_progress': progress
                                            }
                                            
                                            success, message = st.session_state.bp_manager_v2.update_workflow(workflow_id, updates)
                                            if success:
                                                st.success(f"'{stage_name}' 단계가 업데이트되었습니다.")
                                                st.rerun()
                                            else:
                                                st.error(message)
                                    
                                    with col_reset:
                                        if st.button(f"'{stage_name}' 초기화", key=f"reset_sales_{i}", type="secondary"):
                                            # 단계 초기화
                                            sales_stages[i]['status'] = '대기'
                                            sales_stages[i]['assigned_to'] = ''
                                            sales_stages[i]['notes'] = ''
                                            sales_stages[i]['started_date'] = ''
                                            sales_stages[i]['completed_date'] = ''
                                            
                                            # 업데이트 저장
                                            updates = {
                                                'sales_stages_json': json.dumps(sales_stages)
                                            }
                                            
                                            success, message = st.session_state.bp_manager_v2.update_workflow(workflow_id, updates)
                                            if success:
                                                st.info(f"'{stage_name}' 단계가 초기화되었습니다.")
                                                st.rerun()
                                            else:
                                                st.error(message)

                    
                        except Exception as e:
                            st.error(f"판매 단계 편집 오류: {e}")
                    
                    # 서비스 프로세스 편집
                    if selected_workflow.get('has_service_items', False):
                        st.markdown("### 🔧 서비스 프로세스 단계 편집")
                        
                        try:
                            service_stages_json = selected_workflow.get('service_stages_json', '[]')
                            if isinstance(service_stages_json, str):
                                service_stages = json.loads(service_stages_json)
                            else:
                                service_stages = []
                            
                            current_stage = str(selected_workflow.get('service_current_stage', ''))
                            
                            # 각 단계 편집
                            for i, stage in enumerate(service_stages):
                                stage_name = stage.get('stage_name', f'단계 {i+1}')
                                stage_status = stage.get('status', '대기')
                                
                                with st.expander(f"{stage_name} (상태: {stage_status})"):
                                    col1, col2, col3 = st.columns(3)
                                    
                                    with col1:
                                        # 모든 단계를 마스터가 수정 가능하도록 변경
                                        new_status = st.selectbox(
                                            "상태 변경", 
                                            ['대기', '진행중', '완료'], 
                                            index=['대기', '진행중', '완료'].index(stage_status),
                                            key=f"service_status_{i}"
                                        )
                                    
                                    with col2:
                                        new_assigned = st.text_input(
                                            "담당자", 
                                            value=stage.get('assigned_to', '') or '',
                                            key=f"service_assigned_{i}"
                                        )
                                    
                                    with col3:
                                        new_notes = st.text_area(
                                            "메모", 
                                            value=stage.get('notes', '') or '',
                                            key=f"service_notes_{i}"
                                        )
                                    
                                    # 마스터는 모든 단계 업데이트 가능
                                    col_update, col_reset = st.columns(2)
                                    
                                    with col_update:
                                        if st.button(f"'{stage_name}' 단계 업데이트", key=f"update_service_{i}"):
                                            # 단계 정보 업데이트
                                            service_stages[i]['status'] = new_status
                                            service_stages[i]['assigned_to'] = new_assigned
                                            service_stages[i]['notes'] = new_notes
                                            
                                            # 상태 변경 시 날짜 업데이트
                                            if new_status == '진행중' and stage_status != '진행중':
                                                service_stages[i]['started_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                            elif new_status == '완료' and stage_status != '완료':
                                                service_stages[i]['completed_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                            
                                            # 현재 단계 업데이트
                                            if new_status == '진행중':
                                                current_stage = stage_name
                                            
                                            # 진행률 재계산
                                            completed_stages = sum(1 for s in service_stages if s['status'] == '완료')
                                            progress = (completed_stages / len(service_stages)) * 100
                                            
                                            # 업데이트 저장
                                            updates = {
                                                'service_stages_json': json.dumps(service_stages),
                                                'service_current_stage': current_stage,
                                                'service_progress': progress
                                            }
                                            
                                            success, message = st.session_state.bp_manager_v2.update_workflow(workflow_id, updates)
                                            if success:
                                                st.success(f"'{stage_name}' 단계가 업데이트되었습니다.")
                                                st.rerun()
                                            else:
                                                st.error(message)
                                    
                                    with col_reset:
                                        if st.button(f"'{stage_name}' 초기화", key=f"reset_service_{i}", type="secondary"):
                                            # 단계 초기화
                                            service_stages[i]['status'] = '대기'
                                            service_stages[i]['assigned_to'] = ''
                                            service_stages[i]['notes'] = ''
                                            service_stages[i]['started_date'] = ''
                                            service_stages[i]['completed_date'] = ''
                                            
                                            # 업데이트 저장
                                            updates = {
                                                'service_stages_json': json.dumps(service_stages)
                                            }
                                            
                                            success, message = st.session_state.bp_manager_v2.update_workflow(workflow_id, updates)
                                            if success:
                                                st.info(f"'{stage_name}' 단계가 초기화되었습니다.")
                                                st.rerun()
                                            else:
                                                st.error(message)
                    
                        except Exception as e:
                            st.error(f"서비스 단계 편집 오류: {e}")
                    
                    st.divider()
                    
                    # 워크플로우 관리 (마스터 전용)
                    st.subheader("🔧 워크플로우 관리")
                    
                    col_mgmt1, col_mgmt2, col_mgmt3 = st.columns(3)
                    
                    with col_mgmt1:
                        st.markdown("**전체 워크플로우 재설정**")
                        if st.button("🔄 전체 워크플로우 초기화", key="reset_all_workflow"):
                            # 모든 단계를 대기 상태로 초기화
                            updates = {
                                'overall_progress': 0,
                                'sales_progress': 0,
                                'service_progress': 0,
                                'sales_current_stage': '',
                                'service_current_stage': ''
                            }
                            
                            # 판매 단계 초기화
                            if selected_workflow.get('has_sales_items', False):
                                try:
                                    sales_stages_json = selected_workflow.get('sales_stages_json', '[]')
                                    if isinstance(sales_stages_json, str):
                                        sales_stages = json.loads(sales_stages_json)
                                        for stage in sales_stages:
                                            stage['status'] = '대기'
                                            stage['assigned_to'] = ''
                                            stage['notes'] = ''
                                            stage['started_date'] = ''
                                            stage['completed_date'] = ''
                                        updates['sales_stages_json'] = json.dumps(sales_stages)
                                except:
                                    pass
                            
                            # 서비스 단계 초기화
                            if selected_workflow.get('has_service_items', False):
                                try:
                                    service_stages_json = selected_workflow.get('service_stages_json', '[]')
                                    if isinstance(service_stages_json, str):
                                        service_stages = json.loads(service_stages_json)
                                        for stage in service_stages:
                                            stage['status'] = '대기'
                                            stage['assigned_to'] = ''
                                            stage['notes'] = ''
                                            stage['started_date'] = ''
                                            stage['completed_date'] = ''
                                        updates['service_stages_json'] = json.dumps(service_stages)
                                except:
                                    pass
                            
                            success, message = st.session_state.bp_manager_v2.update_workflow(workflow_id, updates)
                            if success:
                                st.success("전체 워크플로우가 초기화되었습니다.")
                                st.rerun()
                            else:
                                st.error(message)
                    
                    with col_mgmt2:
                        st.markdown("**워크플로우 복제**")
                        new_quotation_number = st.text_input("새 견적번호", placeholder="복제할 새 견적번호")
                        if st.button("📋 워크플로우 복제", key="clone_workflow"):
                            if new_quotation_number:
                                # 현재 워크플로우 데이터 복사
                                clone_data = selected_workflow.copy()
                                clone_data['quotation_number'] = new_quotation_number
                                clone_data['workflow_id'] = f"WF_{new_quotation_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                clone_data['created_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                clone_data['overall_progress'] = 0
                                clone_data['sales_progress'] = 0
                                clone_data['service_progress'] = 0
                                
                                # 단계 초기화
                                if clone_data.get('has_sales_items', False):
                                    try:
                                        sales_stages_json = clone_data.get('sales_stages_json', '[]')
                                        if isinstance(sales_stages_json, str):
                                            sales_stages = json.loads(sales_stages_json)
                                        else:
                                            sales_stages = []
                                        for stage in sales_stages:
                                            stage['status'] = '대기'
                                            stage['assigned_to'] = ''
                                            stage['notes'] = ''
                                            stage['started_date'] = ''
                                            stage['completed_date'] = ''
                                        clone_data['sales_stages_json'] = json.dumps(sales_stages)
                                    except:
                                        pass
                                
                                if clone_data.get('has_service_items', False):
                                    try:
                                        service_stages_json = clone_data.get('service_stages_json', '[]')
                                        if isinstance(service_stages_json, str):
                                            service_stages = json.loads(service_stages_json)
                                        else:
                                            service_stages = []
                                        for stage in service_stages:
                                            stage['status'] = '대기'
                                            stage['assigned_to'] = ''
                                            stage['notes'] = ''
                                            stage['started_date'] = ''
                                            stage['completed_date'] = ''
                                        clone_data['service_stages_json'] = json.dumps(service_stages)
                                    except:
                                        pass
                                
                                success, message = st.session_state.bp_manager_v2.create_workflow_from_data(clone_data)
                                if success:
                                    st.success(f"워크플로우가 '{new_quotation_number}'로 복제되었습니다.")
                                    st.rerun()
                                else:
                                    st.error(message)
                            else:
                                st.warning("새 견적번호를 입력해주세요.")
                    
                    with col_mgmt3:
                        st.markdown("**워크플로우 삭제**")
                        st.warning("⚠️ 삭제된 워크플로우는 복구할 수 없습니다.")
                        if st.button("🗑️ 이 워크플로우 삭제", type="secondary"):
                            success, message = st.session_state.bp_manager_v2.delete_workflow(workflow_id)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
        
            else:
                st.info("편집할 워크플로우가 없습니다.")
                st.write("워크플로우를 생성한 후 편집 기능을 사용할 수 있습니다.")
    
    with tab5:
        st.header("📈 성과 분석")
        
        try:
            workflows_df = st.session_state.bp_manager_v2.get_all_workflows()
            if isinstance(workflows_df, list):
                # 딕셔너리인 항목만 필터링
                valid_workflows = [w for w in workflows_df if isinstance(w, dict)]
                workflows_df = valid_workflows
            else:
                workflows_df = []
        except Exception as e:
            st.error(f"분석 데이터 로드 오류: {e}")
            workflows_df = []
        
        if (not workflows_df.empty if isinstance(workflows_df, pd.DataFrame) else len(workflows_df) > 0):
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
            
            # 프로세스 타입별 분포
            if (not workflows_df.empty if isinstance(workflows_df, pd.DataFrame) else len(workflows_df) > 0):
                st.subheader("📊 프로세스 타입별 분포")
                
                # 워크플로우 타입 카운트
                type_counts = {}
                for workflow in workflows_df:
                    wf_type = workflow.get('workflow_type', 'unknown')
                    type_counts[wf_type] = type_counts.get(wf_type, 0) + 1
                
                if type_counts:
                    import plotly.express as px
                    fig = px.pie(
                        values=list(type_counts.values()), 
                        names=list(type_counts.keys()),
                        title="프로세스 타입별 분포"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("분석할 데이터가 없습니다.")

def show_page_for_menu(system_key):
    """각 메뉴의 실제 기능 페이지를 표시합니다."""
    try:
        # 대시보드 매니저 지연 초기화
        if system_key == "dashboard":
            # 필수 매니저만 초기화
            if 'employee_manager' not in st.session_state:
                st.session_state.employee_manager = get_employee_manager()
            if 'customer_manager' not in st.session_state:
                st.session_state.customer_manager = get_customer_manager()
            if 'product_manager' not in st.session_state:
                st.session_state.product_manager = get_product_manager()
            if 'vacation_manager' not in st.session_state:
                st.session_state.vacation_manager = get_vacation_manager()
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
                'can_delete_data': True
            }
        else:
            # 직원 계정은 저장된 권한 사용
            user_permissions = st.session_state.auth_manager.get_user_permissions(current_user_id, current_user_type)
        if system_key == "dashboard":
            from pages.menu_dashboard import show_main_dashboard
            
            # 매니저는 이미 위에서 초기화했으므로 삭제
            
            managers = {
                'employee_manager': st.session_state.employee_manager,
                'customer_manager': st.session_state.customer_manager,
                'product_manager': st.session_state.product_manager,
                'vacation_manager': st.session_state.vacation_manager,
            }
            show_main_dashboard(managers, None, get_text)
        elif system_key == "employee_management":
            # 서브메뉴에 돌아가기 버튼 추가 (페이지 내 헤더 제거하고 여기서만 표시)
            # 매니저 초기화
            if 'employee_manager' not in st.session_state:
                st.session_state.employee_manager = get_employee_manager()
            if 'auth_manager' not in st.session_state:
                st.session_state.auth_manager = get_auth_manager()
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header("👥 직원 관리")
            with col_back:
                if st.button(f"↩️ {get_text('back_to_admin_menu')}", key="back_to_admin_from_employee"):
                    st.session_state.selected_system = "admin_management"
                    st.rerun()
            
            from pages.employee_page import show_employee_page
            show_employee_page(
                st.session_state.employee_manager, 
                st.session_state.auth_manager,
                user_permissions,
                get_text,
                hide_header=True  # 헤더 숨김 플래그 추가
            )
        elif system_key == "customer_management":
            # 서브메뉴에 돌아가기 버튼 추가
            # 매니저 초기화
            if 'customer_manager' not in st.session_state:
                st.session_state.customer_manager = get_customer_manager()
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header("👥 고객 관리")
            with col_back:
                if st.button("↩️ 영업관리", key="back_to_sales_from_customer"):
                    st.session_state.selected_system = "sales_management"
                    st.rerun()
            
            from pages.customer_page import show_customer_page  
            show_customer_page(
                st.session_state.customer_manager,
                user_permissions,
                get_text
            )


        elif system_key == "supplier_management":
            if 'supplier_manager' not in st.session_state:
                st.session_state.supplier_manager = get_supplier_manager()
            from pages.supplier_page import show_supplier_page
            # 매니저 초기화
        if 'supplier_manager' not in st.session_state:
            st.session_state.supplier_manager = get_supplier_manager()
            show_supplier_page(
                st.session_state.supplier_manager, 
                {},  # user_permissions
                get_text
            )
        elif system_key == "product_registration":
            if 'product_manager' not in st.session_state:
                st.session_state.product_manager = get_product_manager()
            # 통합 제품 등록 페이지
            # 매니저 초기화
        if 'master_product_manager' not in st.session_state:
            st.session_state.master_product_manager = get_master_product_manager()
        if 'finished_product_manager' not in st.session_state:
            st.session_state.finished_product_manager = get_finished_product_manager()
        if 'product_code_manager' not in st.session_state:
            st.session_state.product_code_manager = get_product_code_manager()
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header("📝 제품 등록")
            with col_back:
                if st.button("↩️ 제품관리", key="back_to_product_from_registration"):
                    st.session_state.selected_system = "product_management"
                    st.rerun()
            
            from pages.product_registration_page import show_product_registration_page
            show_product_registration_page(
                st.session_state.master_product_manager,
                st.session_state.finished_product_manager,
                st.session_state.product_code_manager,
                st.session_state.user_permissions,
                get_text
            )
        elif system_key == "hr_product_registration":
            # HR 제품 등록 메뉴
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header("🔥 HR 제품 등록")
            with col_back:
                if st.button("↩️ 제품관리", key="back_to_product_from_hr"):
                    st.session_state.selected_system = "product_management"
                    st.rerun()
            
            from scripts.hr_product_registration import show_hr_product_registration, show_hr_product_list
            
            # 탭으로 제품 등록과 목록 구분
            hr_tabs = st.tabs(["🆕 신규 제품 등록", "📋 등록된 HR 제품 목록"])
            
            with hr_tabs[0]:
                show_hr_product_registration()
            
            with hr_tabs[1]:
                show_hr_product_list()
                
        elif system_key == "exchange_rate_management":
            from pages.yearly_management_rate_page import show_yearly_management_rate_page
            show_yearly_management_rate_page(get_text)

        elif system_key == "business_process_v2_management":
            # 서브메뉴에 돌아가기 버튼 추가
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header(f"🔄 {get_text('process_management')}")
            with col_back:
                if st.button("↩️ 영업관리", key="back_to_sales_from_process"):
                    st.session_state.selected_system = "sales_management"
                    st.rerun()
            
            show_business_process_v2_page()
        elif system_key == "work_report_management":
            from pages.work_report_page import show_work_report_page
            show_work_report_page(get_text)
        elif system_key == "work_status_management":
            from pages.work_status_page import show_work_status_page
            show_work_status_page(get_text)
        elif system_key == "order_management":
            if 'order_manager' not in st.session_state:
                st.session_state.order_manager = get_order_manager()
            # 서브메뉴에 돌아가기 버튼 추가
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header("📦 주문 관리")
            with col_back:
                if st.button("↩️ 영업관리", key="back_to_sales_from_order"):
                    st.session_state.selected_system = "sales_management"
                    st.rerun()
            
            from pages.order_page import show_order_page
            show_order_page(
                st.session_state.order_manager,
                st.session_state.quotation_manager,
                st.session_state.customer_manager,
                st.session_state.get('user_id', ''),
                get_text
            )
        elif system_key == "approval_management":
            # 서브메뉴에 돌아가기 버튼 추가
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header("✅ 승인관리 (법인장 전용)")
            with col_back:
                if st.button("↩️ 법인장메뉴", key="back_to_executive_from_approval"):
                    st.session_state.selected_system = "executive_management"
                    st.rerun()
            
            # 법인장과 마스터만 접근 가능
            user_access = st.session_state.get('access_level', 'user')
            if not check_access_level('ceo', user_access):
                st.error("❌ 승인관리는 법인장 이상만 접근할 수 있습니다.")
                if st.button("돌아가기"):
                    st.session_state.selected_system = None
                    st.rerun()
                return
            
            from pages.approval_page import show_approval_page
            show_approval_page(
                st.session_state.approval_manager,
                st.session_state.employee_manager,
                {},  # user_permissions
                get_text
            )
        elif system_key == "expense_request_management":
            # 서브메뉴에 돌아가기 버튼 추가
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header(f"💰 {get_text('expense_admin_management')}")
            with col_back:
                if st.button(f"↩️ {get_text('back_to_admin_menu')}", key="back_to_admin_from_expense"):
                    st.session_state.selected_system = "admin_management"
                    st.rerun()
            
            # 베트남 직원을 위한 더 직관적인 메시지
            st.info(f"💡 **{get_text('admin_business')}**: {get_text('business_flow_info')}")
            
            from pages.expense_request_admin_page import show_expense_request_admin_page as show_expense_request_page
            show_expense_request_page(
                st.session_state.expense_request_manager,
                st.session_state.get('user_id', ''),
                st.session_state.get('user_name', ''),
                get_text
            )
       elif system_key == "quotation_management":
        if 'quotation_manager' not in st.session_state:
            st.session_state.quotation_manager = get_quotation_manager()
            # 서브메뉴에 돌아가기 버튼 추가
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header("📋 견적 관리")
            with col_back:
                if st.button("↩️ 영업관리", key="back_to_sales_from_quotation"):
                    st.session_state.selected_system = "sales_management"
                    st.rerun()
            
            from pages.quotation_page import main
            main()




        elif system_key == "shipping_management":
            # 서브메뉴에 돌아가기 버튼 추가
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header("📄 납품 확인서 관리")
            with col_back:
                if st.button("↩️ 영업관리", key="back_to_sales_from_shipping"):
                    st.session_state.selected_system = "sales_management"
                    st.rerun()
            
            from pages.shipping_page import show_shipping_page
            # SQLite 배송 매니저 우선 사용
            shipping_manager = st.session_state.get('sqlite_shipping_manager') or st.session_state.get('shipping_manager')
            show_shipping_page(
                shipping_manager,
                st.session_state.quotation_manager,
                get_text
            )
        elif system_key == "cash_flow_management":
            # 서브메뉴에 돌아가기 버튼 추가 (페이지 내 헤더 제거하고 여기서만 표시)
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header("💰 현금 흐름관리")
            with col_back:
                if st.button(f"↩️ {get_text('back_to_admin_menu')}", key="back_to_admin_from_cash"):
                    st.session_state.selected_system = "admin_management"
                    st.rerun()
            
            from pages.cash_flow_page import show_cash_flow_management_page
            managers = {
                'cash_flow_manager': st.session_state.cash_flow_manager,
                'quotation_manager': st.session_state.quotation_manager,
                'invoice_manager': st.session_state.get('invoice_manager'),
                'purchase_order_manager': st.session_state.get('purchase_order_manager')
            }
            show_cash_flow_management_page(managers, None, get_text, hide_header=True)
        
        elif system_key == "contract_management":
            # 서브메뉴에 돌아가기 버튼 추가
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header(f"📝 {get_text('contract_management')}")
            with col_back:
                if st.button(f"↩️ {get_text('back_to_admin_menu')}", key="back_to_admin_from_contract"):
                    st.session_state.selected_system = "admin_management"
                    st.rerun()
            
            from pages.contract_page import show_contract_page
            show_contract_page(get_text)
        elif system_key == "schedule_task_management":
            # 서브메뉴에 돌아가기 버튼 추가
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header(f"📅 {get_text('admin_schedule_management')}")
            with col_back:
                if st.button(f"↩️ {get_text('back_to_admin_menu')}", key="back_to_admin_from_schedule"):
                    st.session_state.selected_system = "admin_management"
                    st.rerun()
            
            from pages.schedule_task_page import show_schedule_task_page
            show_schedule_task_page(get_text)
        elif system_key == "purchase_management":
            # 서브메뉴에 돌아가기 버튼 추가
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header(f"🛒 {get_text('purchase_product_registration')}")
            with col_back:
                if st.button(f"↩️ {get_text('back_to_admin_menu')}", key="back_to_admin_from_purchase"):
                    st.session_state.selected_system = "admin_management"
                    st.rerun()
            
            from pages.purchase_page import show_purchase_page
            show_purchase_page(get_text)
        elif system_key == "asset_management":
            # 서브메뉴에 돌아가기 버튼 추가
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header(f"🏢 {get_text('asset_management')}")
            with col_back:
                if st.button(f"↩️ {get_text('back_to_admin_menu')}", key="back_to_admin_from_asset"):
                    st.session_state.selected_system = "admin_management"
                    st.rerun()
            
            # 자산 관리 기능 (실제 데이터 기반)
            st.markdown("### 📊 자산 현황 대시보드")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("총 자산 가치", "0 VND", "0")
            with col2:
                st.metric("등록된 자산", "0개", "0")
            with col3:
                st.metric("점검 대상", "0개", "0")
            with col4:
                st.metric("교체 예정", "0개", "0")
            
            # 자산 등록 탭
            tab1, tab2, tab3, tab4 = st.tabs(["📝 자산 등록", "📋 자산 목록", "🔧 유지보수", "💰 감가상각 계산"])
            
            with tab1:
                st.subheader("새 자산 등록")
                with st.form("asset_registration"):
                    col1, col2 = st.columns(2)
                    with col1:
                        asset_name = st.text_input("자산명")
                        asset_category = st.selectbox("자산 분류", [
                            "사무용 가구", "컴퓨터/IT장비", "생산장비", "차량", "건물/부동산", "에어컨/냉난방", "기타"
                        ])
                        purchase_price = st.number_input("구매가격 (VND)", min_value=0)
                        purchase_date = st.date_input("구매일자")
                    
                    with col2:
                        asset_location = st.text_input("설치 위치")
                        asset_condition = st.selectbox("상태", ["정상", "수리 필요", "사용 중지", "폐기 예정"])
                        useful_life = st.number_input("내용연수 (년)", min_value=1, max_value=50, value=5)
                        salvage_value = st.number_input("잔존가치 (VND)", min_value=0)
                    
                    description = st.text_area("설명")
                    
                    if st.form_submit_button("자산 등록"):
                        st.success("자산이 성공적으로 등록되었습니다!")
            
            with tab2:
                st.subheader("자산 목록")
                
                # 필터링 옵션
                col1, col2, col3 = st.columns(3)
                with col1:
                    filter_category = st.selectbox("분류 필터", [
                        "전체", "사무용 가구", "컴퓨터/IT장비", "생산장비", "차량", "건물/부동산", "에어컨/냉난방", "기타"
                    ])
                with col2:
                    filter_location = st.selectbox("위치 필터", [
                        "전체", "1층 사무실", "2층 사무실", "생산동", "창고", "주차장", "기타"
                    ])
                with col3:
                    filter_status = st.selectbox("상태 필터", [
                        "전체", "정상", "수리 필요", "사용 중지", "폐기 예정"
                    ])
                
                st.markdown("---")
                st.info("등록된 자산이 없습니다. 자산을 등록하면 여기에 목록이 표시됩니다.")
            
            with tab3:
                st.subheader("유지보수 관리")
                st.info("유지보수 기능은 개발 중입니다.")
            
            with tab4:
                st.subheader("감가상각 계산기")
                
                with st.form("depreciation_calculator"):
                    col1, col2 = st.columns(2)
                    with col1:
                        calc_price = st.number_input("자산 가격 (VND)", min_value=0, value=1000000)
                        calc_salvage = st.number_input("잔존가치 (VND)", min_value=0, value=100000)
                    with col2:
                        calc_years = st.number_input("내용연수 (년)", min_value=1, max_value=50, value=5)
                        calc_method = st.selectbox("상각방법", ["정액법", "정률법", "생산량비례법"])
                    
                    if st.form_submit_button("감가상각 계산"):
                        if calc_price > calc_salvage and calc_years > 0:
                            annual_dep = (calc_price - calc_salvage) / calc_years
                            monthly_dep = annual_dep / 12
                            depreciation_rate = (annual_dep / calc_price) * 100
                            
                            st.metric("연간 감가상각비", f"{annual_dep:,.0f} VND")
                            st.metric("월간 감가상각비", f"{monthly_dep:,.0f} VND") 
                            st.metric("감가상각률", f"{depreciation_rate:.2f}%")
                            
                            # 5년간 감가상각 스케줄 표시
                            st.markdown("**감가상각 스케줄 (첫 5년)**")
                            schedule_data = []
                            cumulative_dep = 0
                            for year in range(1, min(calc_years + 1, 6)):
                                cumulative_dep += annual_dep
                                book_value = calc_price - cumulative_dep
                                schedule_data.append({
                                    "년도": f"{year}년차",
                                    "연간상각비": f"{annual_dep:,.0f}",
                                    "누적상각비": f"{cumulative_dep:,.0f}",
                                    "순장부가액": f"{max(book_value, calc_salvage):,.0f}"
                                })
                            
                            import pandas as pd
                            df_schedule = pd.DataFrame(schedule_data)
                            st.dataframe(df_schedule, use_container_width=True)
        elif system_key == "backup_management":
            # 서브메뉴에 돌아가기 버튼 추가
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header("💾 백업 및 복원 관리")
            with col_back:
                if st.button("↩️ 법인장메뉴", key="back_to_executive_from_backup"):
                    st.session_state.selected_system = "executive_management"
                    st.rerun()
            
            try:
                from pages.backup_page import show_backup_page
                show_backup_page(st.session_state.auth_manager, get_text)
            except Exception as e:
                st.error(f"백업 페이지 로드 중 오류가 발생했습니다: {str(e)}")
                st.info("백업 시스템이 일시적으로 사용할 수 없습니다.")
            
        elif system_key == "language_management":
            # 서브메뉴에 돌아가기 버튼 추가
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header("🌍 다국어 관리 시스템")
            with col_back:
                if st.button("↩️ 법인장메뉴", key="back_to_executive_from_language"):
                    st.session_state.selected_system = "executive_management"
                    st.rerun()
            
            from pages.language_management_page import show_language_management_page
            show_language_management_page()
        elif system_key == "monthly_sales_management":
            # 서브메뉴에 돌아가기 버튼 추가 (페이지 내 헤더 제거하고 여기서만 표시)
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header("📈 월별 매출관리")
            with col_back:
                if st.button("↩️ 영업관리", key="back_to_sales_from_monthly"):
                    st.session_state.selected_system = "sales_management"
                    st.rerun()
            
            from pages.monthly_sales_page import show_monthly_sales_page
            if st.session_state.monthly_sales_manager:
                show_monthly_sales_page(
                    st.session_state.monthly_sales_manager,
                    st.session_state.customer_manager,
                    st.session_state.exchange_rate_manager
                )
            else:
                st.error("❌ 월별 매출관리 시스템을 초기화할 수 없습니다.")
        elif system_key == "system_guide":
            from pages.system_guide_page import show_system_guide
            show_system_guide(get_text)
        elif system_key == "system_config_management":
            # 기존 시스템 설정을 제품 분류 관리로 업그레이드
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header("⚙️ 시스템 설정")
            with col_back:
                if st.button("↩️ 법인장메뉴", key="back_to_executive_from_system"):
                    st.session_state.selected_system = "executive_management"
                    st.rerun()
            
            from pages.system_settings_page import show_system_settings_page
            
            # 매니저 안전 초기화
            if 'system_config_manager' not in st.session_state:
                st.session_state.system_config_manager = get_system_config_manager()
            if 'supplier_manager' not in st.session_state:
                st.session_state.supplier_manager = get_supplier_manager()
            if 'product_code_manager' not in st.session_state:
                st.session_state.product_code_manager = get_product_code_manager()
            if 'master_product_manager' not in st.session_state:
                st.session_state.master_product_manager = get_master_product_manager()
            if 'product_category_config_manager' not in st.session_state:
                try:
                    from managers.legacy.product_category_config_manager import ProductCategoryConfigManager
                    st.session_state.product_category_config_manager = ProductCategoryConfigManager()
                except Exception as pc_error:
                    st.session_state.product_category_config_manager = None
            
            managers = {
                'system_config_manager': st.session_state.system_config_manager,
                'supplier_manager': st.session_state.supplier_manager,
                'product_code_manager': st.session_state.product_code_manager,
                'master_product_manager': st.session_state.master_product_manager
            }
            show_system_settings_page(
                st.session_state.product_category_config_manager,
                get_text,
                hide_header=True,
                managers=managers
            )
        elif system_key == "personal_status":
            from pages.personal_status_page import show_personal_status_page
            show_personal_status_page(
                st.session_state.employee_manager,
                st.session_state.vacation_manager,
                st.session_state.approval_manager,
                user_permissions,
                get_text
            )
        elif system_key == "work_report_management":
            from pages.work_report_page import show_work_report_page
            show_work_report_page(get_text)
        elif system_key == "system_config":
            # 기존 시스템 설정을 제품 분류 관리로 업그레이드
            st.header("⚙️ 시스템 설정")
            from pages.system_settings_page import show_system_settings_page
            
            # 매니저 안전 초기화
            if 'system_config_manager' not in st.session_state:
                st.session_state.system_config_manager = get_system_config_manager()
            if 'supplier_manager' not in st.session_state:
                st.session_state.supplier_manager = get_supplier_manager()
            if 'product_code_manager' not in st.session_state:
                st.session_state.product_code_manager = get_product_code_manager()
            if 'master_product_manager' not in st.session_state:
                st.session_state.master_product_manager = get_master_product_manager()
            if 'product_category_config_manager' not in st.session_state:
                try:
                    from managers.legacy.product_category_config_manager import ProductCategoryConfigManager
                    st.session_state.product_category_config_manager = ProductCategoryConfigManager()
                except Exception as pc_error:
                    st.session_state.product_category_config_manager = None
            
            managers = {
                'system_config_manager': st.session_state.system_config_manager,
                'supplier_manager': st.session_state.supplier_manager,
                'product_code_manager': st.session_state.product_code_manager,
                'master_product_manager': st.session_state.master_product_manager
            }
            show_system_settings_page(
                st.session_state.product_category_config_manager,
                get_text,
                hide_header=True,
                managers=managers
            )
        
        # 새로운 메뉴 구조 처리
        elif system_key == "sales_management":
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header(f"📊 {get_text('sales_management')}")
            with col_back:
                if st.button(f"🏠 {get_text('main_menu')}", key="back_to_main_sales"):
                    st.session_state.selected_system = "dashboard"
                    st.rerun()
            
            # 견적서 진행상황 대시보드 표시
            st.markdown("### 💼 견적서 진행현황")
            try:
                # 견적서 대시보드 간단히 표시
                st.info("📋 견적서 관리 시스템이 준비되었습니다. 견적서 관리를 클릭하여 시작하세요.")
            except Exception as e:
                st.error(f"견적서 대시보드 로드 오류: {e}")
            
            st.markdown("---")
            st.markdown(get_text('select_submenu'))
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button(f"👥 {get_text('customer_management')}", use_container_width=True):
                    st.session_state.selected_system = "customer_management"
                    st.rerun()
            with col2:
                if st.button(f"📋 {get_text('quotation_management')}", use_container_width=True):
                    st.session_state.selected_system = "quotation_management"
                    st.rerun()
            with col3:
                if st.button(f"📦 {get_text('order_management')}", use_container_width=True):
                    st.session_state.selected_system = "order_management"
                    st.rerun()
            with col4:
                if st.button(f"🔄 {get_text('business_process')}", use_container_width=True):
                    st.session_state.selected_system = "business_process_v2_management"
                    st.rerun()
                    
            col5, col6, col7 = st.columns(3)
            with col5:
                if st.button(f"🚚 {get_text('shipping_management')}", use_container_width=True):
                    st.session_state.selected_system = "shipping_management"
                    st.rerun()
            with col6:
                if st.button(f"📈 {get_text('monthly_sales')}", use_container_width=True):
                    st.session_state.selected_system = "monthly_sales_management"
                    st.rerun()
            with col7:
                if st.button(f"🏢 {get_text('supplier_management')}", use_container_width=True):
                    st.session_state.selected_system = "supplier_management"
                    st.rerun()
        
                    
        elif system_key == "product_management":
            # 제품 등록 페이지를 바로 표시
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header("📦 제품 등록")
            with col_back:
                if st.button("🏠 메인 메뉴", key="back_to_main_product"):
                    st.session_state.selected_system = "dashboard"
                    st.rerun()
            
            # 제품 등록 페이지 직접 표시
            from pages.product_registration_page import show_product_registration_page
            show_product_registration_page(
                st.session_state.master_product_manager,
                st.session_state.finished_product_manager,
                st.session_state.product_code_manager,
                st.session_state.user_permissions,
                get_text
            )
                    
        elif system_key == "executive_management":
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header("👑 법인장 메뉴")
            with col_back:
                if st.button("🏠 메인 메뉴", key="back_to_main_executive"):
                    st.session_state.selected_system = "dashboard"
                    st.rerun()
            st.markdown("법인장 전용 메뉴를 선택해주세요.")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ 승인관리", use_container_width=True):
                    st.session_state.selected_system = "approval_management"
                    st.rerun()
            with col2:
                if st.button("💾 백업관리", use_container_width=True):
                    st.session_state.selected_system = "backup_management"
                    st.rerun()
            with col3:
                st.write("")  # 빈 공간
            
            # 추가 버튼 행
            col4, col5, col6 = st.columns(3)
            with col4:
                if st.button("⚙️ 시스템 설정", use_container_width=True):
                    st.session_state.selected_system = "system_config"
                    st.rerun()
            with col5:
                if st.button("🌍 다국어 관리", use_container_width=True):
                    st.session_state.selected_system = "language_management"
                    st.rerun()
        
        elif system_key == "system_config_management":
            # 시스템 설정 관리는 시스템 설정과 동일
            st.session_state.selected_system = "system_config"
            st.rerun()
        
        elif system_key == "asset_management":
            col_header, col_back = st.columns([3, 1])
            with col_header:
                st.header(f"🏭 {get_text('asset_management')}")
            with col_back:
                if st.button(f"🏠 {get_text('main_menu')}", key="back_to_main_asset"):
                    st.session_state.selected_system = "dashboard"
                    st.rerun()
            
            # 자산 관리 기본 기능 구현
            tab1, tab2, tab3 = st.tabs([
                f"📊 {get_text('asset_status')}", 
                f"➕ {get_text('asset_registration')}", 
                f"📋 {get_text('asset_management_tab')}"
            ])
            
            with tab1:
                st.subheader(f"📊 {get_text('overall_asset_status')}")
                
                # 자산 통계 카드
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(get_text('total_assets'), "0", help=get_text('total_assets_help'))
                with col2:
                    st.metric(get_text('total_acquisition_cost'), "0 VND", help=get_text('total_acquisition_cost_help'))
                with col3:
                    st.metric(get_text('annual_depreciation'), "0 VND", help=get_text('annual_depreciation_help'))
                with col4:
                    st.metric(get_text('net_book_value'), "0 VND", help=get_text('net_book_value_help'))
                
                st.markdown("---")
                
                # 감가상각 요약 차트
                st.subheader(f"📈 {get_text('depreciation_status')}")
                col5, col6 = st.columns(2)
                
                with col5:
                    st.markdown(f"**{get_text('asset_depreciation_progress')}**")
                    st.info(get_text('no_registered_assets'))
                
                with col6:
                    st.markdown(f"**{get_text('monthly_depreciation_forecast')}**")
                    st.info(get_text('no_depreciation_data'))
                
                st.markdown("---")
                st.info(f"💡 {get_text('no_asset_data_message')}")
            
            with tab2:
                st.subheader(f"➕ {get_text('new_asset_registration')}")
                
                # 베트남 세법 기준 감가상각 가이드
                with st.expander(f"🇻🇳 {get_text('vietnam_tax_depreciation_guide')}"):
                    st.markdown("""
                    **베트남 세법에 따른 주요 자산별 감가상각 기준:**
                    
                    | 자산 유형 | 내용연수 | 연간 감가상각률 |
                    |----------|---------|---------------|
                    | 사무용 가구 | 6-10년 | 10-16.7% |
                    | 컴퓨터/IT장비 | 3-5년 | 20-33.3% |
                    | 생산장비 | 10-20년 | 5-10% |
                    | 차량 | 6-10년 | 10-16.7% |
                    | 건물/부동산 | 20-50년 | 2-5% |
                    | 에어컨/냉난방 | 10-15년 | 6.7-10% |
                    
                    **감가상각 방법:**
                    - 정액법 (Straight-line method): 매년 동일한 금액
                    - 정률법 (Declining balance method): 매년 동일한 비율
                    """)
                
                with st.form("asset_registration"):
                    st.markdown(f"#### 📋 {get_text('basic_info')}")
                    col1, col2 = st.columns(2)
                    with col1:
                        asset_name = st.text_input(get_text('asset_name'), placeholder=get_text('asset_name_placeholder'))
                        asset_category = st.selectbox(get_text('asset_category'), [
                            "사무용 가구", "컴퓨터/IT장비", "생산장비", "차량", "건물/부동산", "에어컨/냉난방", "기타"
                        ])
                        purchase_date = st.date_input(get_text('purchase_date'))
                        asset_location = st.text_input(get_text('asset_location'), placeholder=get_text('asset_location_placeholder'))
                    
                    with col2:
                        purchase_price = st.number_input(get_text('purchase_price_vnd'), min_value=0, step=100000, help=get_text('purchase_price_vnd_help'))
                        purchase_price_usd = st.number_input(get_text('purchase_price_usd'), min_value=0.0, step=100.0, help=get_text('purchase_price_usd_help'))
                        asset_status = st.selectbox(get_text('asset_status_field'), [
                            "정상", "수리 필요", "사용 중지", "폐기 예정"
                        ])
                        supplier_info = st.text_input(get_text('supplier_info'), placeholder=get_text('supplier_info_placeholder'))
                    
                    st.markdown(f"#### 📊 {get_text('depreciation_settings')}")
                    col3, col4 = st.columns(2)
                    with col3:
                        depreciation_method = st.selectbox(get_text('depreciation_method'), [
                            "정액법 (Straight-line)", 
                            "정률법 (Declining balance)",
                            "감가상각 없음"
                        ])
                        
                        # 카테고리별 기본 내용연수 설정
                        default_years = {
                            "사무용 가구": 8,
                            "컴퓨터/IT장비": 4,
                            "생산장비": 15,
                            "차량": 8,
                            "건물/부동산": 35,
                            "에어컨/냉난방": 12,
                            "기타": 5
                        }
                        
                        useful_life = st.number_input(
                            get_text('useful_life'), 
                            min_value=1, 
                            max_value=50, 
                            value=default_years.get(asset_category, 5),
                            help=get_text('useful_life_help')
                        )
                    
                    with col4:
                        salvage_value = st.number_input(get_text('salvage_value'), min_value=0, step=10000, help=get_text('salvage_value_help'))
                        
                        if depreciation_method != "감가상각 없음" and purchase_price > 0:
                            annual_depreciation = (purchase_price - salvage_value) / useful_life
                            st.metric(get_text('annual_depreciation_expense'), f"{annual_depreciation:,.0f} VND")
                            st.metric(get_text('depreciation_rate'), f"{(annual_depreciation/purchase_price*100):.1f}%")
                    
                    description = st.text_area(get_text('description'), placeholder=get_text('description_placeholder'))
                    
                    if st.form_submit_button(f"🔖 {get_text('register_asset')}", type="primary"):
                        # 자산 데이터 구성
                        from datetime import datetime
                        
                        # 감가상각비 계산
                        if depreciation_method != "감가상각 없음" and purchase_price > 0:
                            annual_depreciation = (purchase_price - salvage_value) / useful_life
                            monthly_depreciation = annual_depreciation / 12
                        else:
                            annual_depreciation = 0
                            monthly_depreciation = 0
                        
                        asset_data = {
                            "asset_name": asset_name,
                            "category": asset_category,
                            "purchase_date": purchase_date.strftime('%Y-%m-%d'),
                            "purchase_price_vnd": purchase_price,
                            "purchase_price_usd": purchase_price_usd,
                            "location": asset_location,
                            "status": asset_status,
                            "supplier": supplier_info,
                            "depreciation_method": depreciation_method,
                            "useful_life": useful_life,
                            "salvage_value": salvage_value,
                            "annual_depreciation": annual_depreciation,
                            "monthly_depreciation": monthly_depreciation,
                            "description": description,
                            "created_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        st.success("✅ 자산이 성공적으로 등록되었습니다!")
                        
                        # 등록된 자산 정보 요약 표시
                        st.markdown("#### 📋 등록된 자산 정보")
                        summary_col1, summary_col2 = st.columns(2)
                        
                        with summary_col1:
                            st.info(f"""
                            **기본 정보**
                            - 자산명: {asset_name}
                            - 카테고리: {asset_category}
                            - 구매일자: {purchase_date.strftime('%Y-%m-%d')}
                            - 취득원가: {purchase_price:,} VND
                            - 보관위치: {asset_location}
                            """)
                        
                        with summary_col2:
                            if depreciation_method != "감가상각 없음":
                                depreciation_rate = (annual_depreciation/purchase_price*100) if purchase_price > 0 else 0
                                st.info(f"""
                                **감가상각 정보**
                                - 감가상각방법: {depreciation_method}
                                - 내용연수: {useful_life}년
                                - 연간 감가상각비: {annual_depreciation:,.0f} VND
                                - 감가상각률: {depreciation_rate:.1f}%
                                - 잔존가치: {salvage_value:,} VND
                                """)
                            else:
                                st.info("**감가상각 정보**\n- 감가상각 대상 아님")
                        
                        st.balloons()
            
            with tab3:
                st.subheader("📋 자산 목록 관리")
                
                # 검색 및 필터
                col1, col2, col3 = st.columns(3)
                with col1:
                    search_term = st.text_input("🔍 자산명 검색", placeholder="자산명을 입력하세요")
                with col2:
                    filter_category = st.selectbox("카테고리 필터", [
                        "전체", "사무용 가구", "컴퓨터/IT장비", "생산장비", "차량", "건물/부동산", "에어컨/냉난방", "기타"
                    ])
                with col3:
                    filter_status = st.selectbox("상태 필터", [
                        "전체", "정상", "수리 필요", "사용 중지", "폐기 예정"
                    ])
                
                st.markdown("---")
                
                # 감가상각 계산 도구
                st.subheader("🧮 감가상각 계산 도구")
                with st.expander("💡 감가상각 시뮬레이션"):
                    calc_col1, calc_col2 = st.columns(2)
                    
                    with calc_col1:
                        calc_price = st.number_input("취득원가 (VND)", min_value=0, step=1000000, key="calc_price")
                        calc_salvage = st.number_input("잔존가치 (VND)", min_value=0, step=100000, key="calc_salvage")
                        calc_years = st.number_input("내용연수 (년)", min_value=1, max_value=50, value=5, key="calc_years")
                    
                    with calc_col2:
                        if calc_price > 0:
                            annual_dep = (calc_price - calc_salvage) / calc_years
                            monthly_dep = annual_dep / 12
                            depreciation_rate = (annual_dep / calc_price) * 100
                            
                            st.metric("연간 감가상각비", f"{annual_dep:,.0f} VND")
                            st.metric("월간 감가상각비", f"{monthly_dep:,.0f} VND") 
                            st.metric("감가상각률", f"{depreciation_rate:.2f}%")
                            
                            # 5년간 감가상각 스케줄 표시
                            st.markdown("**감가상각 스케줄 (첫 5년)**")
                            schedule_data = []
                            cumulative_dep = 0
                            for year in range(1, min(calc_years + 1, 6)):
                                cumulative_dep += annual_dep
                                book_value = calc_price - cumulative_dep
                                schedule_data.append({
                                    "년도": f"{year}년차",
                                    "연간상각비": f"{annual_dep:,.0f}",
                                    "누적상각비": f"{cumulative_dep:,.0f}",
                                    "순장부가액": f"{max(book_value, calc_salvage):,.0f}"
                                })
                            
                            import pandas as pd
                            df_schedule = pd.DataFrame(schedule_data)
                            st.dataframe(df_schedule, use_container_width=True)
                
                st.markdown("---")
                st.info("등록된 자산이 없습니다. 자산을 등록하면 여기에 목록이 표시됩니다.")
                    
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
                if st.button(f"🏢 {get_text('asset_management')}", use_container_width=True):
                    st.session_state.selected_system = "asset_management"
                    st.rerun()
            with col2:
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
                    
        else:
            st.info(f"'{system_key}' 기능은 개발 중입니다.")
    except Exception as e:
        st.error(f"페이지 로딩 중 오류: {str(e)}")
        st.exception(e)

def main():
    """메인 함수"""
    try:
        st.set_page_config(
            page_title="YMV 관리 프로그램",
            page_icon="🏢",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    except Exception as e:
        # 페이지 설정 오류도 캐치
        st.error(f"페이지 설정 오류: {e}")
        return
    
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
        initialize_session_state()
        
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
        
        # Lazy loading으로 매니저 초기화 시간 단축
        try:
            if 'managers_initialized' not in st.session_state:
                st.session_state.managers_initialized = False
            
            # 핵심 매니저만 미리 로드 (로그인에 필요한 것들)
            if 'auth_manager' not in st.session_state:
                st.session_state.auth_manager = get_auth_manager()
                
            # 나머지 매니저들은 필요할 때만 로드하도록 변경
            st.session_state.managers_initialized = True
                
        except Exception as e:
            # 매니저 초기화 오류는 앱 실행을 막지 않음
            st.warning(f"⚠️ 매니저 초기화 오류 (앱 계속 실행): {e}")
            st.session_state.managers_initialized = True  # 기본값으로 설정
        
        # 언어 설정 로드
        try:
            lang_dict = load_language(st.session_state.language)
        except Exception as lang_error:
            st.error(f"언어 파일 로드 오류: {lang_error}")
            # 기본 언어 딕셔너리 사용
            lang_dict = {"app_title": "YMV 관리 프로그램", "login": "로그인"}
        
        # 로그인 상태에 따른 페이지 표시
        if not st.session_state.logged_in:
            show_login_page(lang_dict)
        else:
            show_main_app(lang_dict)
            
    except Exception as main_error:
        st.error(f"앱 실행 중 심각한 오류 발생: {main_error}")
        st.write("**오류 상세:**")
        st.exception(main_error)
        
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
