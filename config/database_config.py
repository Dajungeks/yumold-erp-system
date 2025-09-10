# -*- coding: utf-8 -*-
"""
데이터베이스 설정 및 매니저 팩토리
"""

import os
import streamlit as st
from typing import Union

# SQLite 매니저들 (전체 import - 하위 호환성)
from managers.sqlite.sqlite_employee_manager import SQLiteEmployeeManager
from managers.sqlite.sqlite_customer_manager import SQLiteCustomerManager
from managers.sqlite.sqlite_quotation_manager import SQLiteQuotationManager
from managers.sqlite.sqlite_order_manager import SQLiteOrderManager
from managers.sqlite.sqlite_product_manager import SQLiteProductManager
from managers.sqlite.sqlite_supplier_manager import SQLiteSupplierManager
from managers.sqlite.sqlite_auth_manager import SQLiteAuthManager
from managers.sqlite.sqlite_approval_manager import SQLiteApprovalManager

# 보조 SQLite 매니저들 (하위 호환성)
from managers.sqlite.sqlite_cash_flow_manager import SQLiteCashFlowManager
from managers.sqlite.sqlite_inventory_manager import SQLiteInventoryManager
from managers.sqlite.sqlite_shipping_manager import SQLiteShippingManager
from managers.sqlite.sqlite_invoice_manager import SQLiteInvoiceManager
from managers.sqlite.sqlite_business_process_manager import SQLiteBusinessProcessManager
from managers.sqlite.sqlite_expense_request_manager import SQLiteExpenseRequestManager
from managers.sqlite.sqlite_vacation_manager import SQLiteVacationManager
from managers.sqlite.sqlite_sales_product_manager import SQLiteSalesProductManager
from managers.sqlite.sqlite_finished_product_manager import SQLiteFinishedProductManager
from managers.sqlite.sqlite_cash_transaction_manager import SQLiteCashTransactionManager
from managers.sqlite.sqlite_master_product_manager import SQLiteMasterProductManager
from managers.sqlite.sqlite_notice_manager import SQLiteNoticeManager
from managers.sqlite.sqlite_exchange_rate_manager import SQLiteExchangeRateManager
from managers.sqlite.sqlite_system_config_manager import SQLiteSystemConfigManager
from managers.sqlite.sqlite_product_code_manager import SQLiteProductCodeManager
from managers.sqlite.sqlite_work_status_manager import SQLiteWorkStatusManager
from managers.sqlite.sqlite_weekly_report_manager import SQLiteWeeklyReportManager
from managers.sqlite.sqlite_monthly_sales_manager import SQLiteMonthlySalesManager
from managers.sqlite.sqlite_note_manager import SQLiteNoteManager

# PostgreSQL 매니저들 (전체 import)
from managers.postgresql.postgresql_employee_manager import PostgreSQLEmployeeManager
from managers.postgresql.postgresql_customer_manager import PostgreSQLCustomerManager
from managers.postgresql.postgresql_quotation_manager import PostgreSQLQuotationManager
from managers.postgresql.postgresql_order_manager import PostgreSQLOrderManager
from managers.postgresql.postgresql_product_manager import PostgreSQLProductManager
from managers.postgresql.postgresql_supplier_manager import PostgreSQLSupplierManager
from managers.postgresql.postgresql_auth_manager import PostgreSQLAuthManager
from managers.postgresql.postgresql_approval_manager import PostgreSQLApprovalManager

# 보조 PostgreSQL 매니저들
from managers.postgresql.postgresql_cash_flow_manager import PostgreSQLCashFlowManager
from managers.postgresql.postgresql_inventory_manager import PostgreSQLInventoryManager
from managers.postgresql.postgresql_shipping_manager import PostgreSQLShippingManager
from managers.postgresql.postgresql_invoice_manager import PostgreSQLInvoiceManager
from managers.postgresql.postgresql_business_process_manager import PostgreSQLBusinessProcessManager
from managers.postgresql.postgresql_expense_request_manager import PostgreSQLExpenseRequestManager
from managers.postgresql.postgresql_vacation_manager import PostgreSQLVacationManager
from managers.postgresql.postgresql_sales_product_manager import PostgreSQLSalesProductManager
from managers.postgresql.postgresql_finished_product_manager import PostgreSQLFinishedProductManager
from managers.postgresql.postgresql_cash_transaction_manager import PostgreSQLCashTransactionManager
from managers.postgresql.postgresql_master_product_manager import PostgreSQLMasterProductManager
from managers.postgresql.postgresql_notice_manager import PostgreSQLNoticeManager
from managers.postgresql.postgresql_exchange_rate_manager import PostgreSQLExchangeRateManager
from managers.postgresql.postgresql_system_config_manager import PostgreSQLSystemConfigManager
from managers.postgresql.postgresql_product_code_manager import PostgreSQLProductCodeManager
from managers.postgresql.postgresql_work_status_manager import PostgreSQLWorkStatusManager
from managers.postgresql.postgresql_weekly_report_manager import PostgreSQLWeeklyReportManager
from managers.postgresql.postgresql_monthly_sales_manager import PostgreSQLMonthlySalesManager
from managers.postgresql.postgresql_note_manager import PostgreSQLNoteManager

class DatabaseConfig:
    """데이터베이스 설정 관리"""
    
    @staticmethod
    def get_database_type():
        """데이터베이스 타입 반환 (환경변수 또는 기본값)"""
        # 환경변수 확인
        if os.getenv('DATABASE_URL'):
            return 'postgresql'
        
        # 세션 상태 확인 (사용자 설정)
        if hasattr(st, 'session_state') and 'database_type' in st.session_state:
            return st.session_state.database_type
        
        # 기본값: SQLite
        return 'sqlite'
    
    @staticmethod
    def set_database_type(db_type: str):
        """데이터베이스 타입 설정"""
        if hasattr(st, 'session_state'):
            st.session_state.database_type = db_type

class ManagerFactory:
    """매니저 팩토리 클래스"""
    
    @staticmethod
    def get_employee_manager() -> Union[SQLiteEmployeeManager, PostgreSQLEmployeeManager]:
        """Employee 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLEmployeeManager()
        else:
            return SQLiteEmployeeManager()
    
    @staticmethod
    def get_customer_manager() -> Union[SQLiteCustomerManager, PostgreSQLCustomerManager]:
        """Customer 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLCustomerManager()
        else:
            return SQLiteCustomerManager()
    
    @staticmethod
    def get_quotation_manager() -> Union[SQLiteQuotationManager, PostgreSQLQuotationManager]:
        """Quotation 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLQuotationManager()
        else:
            return SQLiteQuotationManager()
    
    @staticmethod
    def get_order_manager() -> Union[SQLiteOrderManager, PostgreSQLOrderManager]:
        """Order 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLOrderManager()
        else:
            return SQLiteOrderManager()
    
    @staticmethod
    def get_product_manager() -> Union[SQLiteProductManager, PostgreSQLProductManager]:
        """Product 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLProductManager()
        else:
            return SQLiteProductManager()
    
    @staticmethod
    def get_supplier_manager() -> Union[SQLiteSupplierManager, PostgreSQLSupplierManager]:
        """Supplier 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLSupplierManager()
        else:
            return SQLiteSupplierManager()
    
    @staticmethod
    def get_auth_manager() -> Union[SQLiteAuthManager, PostgreSQLAuthManager]:
        """Auth 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLAuthManager()
        else:
            return SQLiteAuthManager()
    
    @staticmethod
    def get_approval_manager() -> Union[SQLiteApprovalManager, PostgreSQLApprovalManager]:
        """Approval 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLApprovalManager()
        else:
            return SQLiteApprovalManager()
    
    # 보조 매니저들
    @staticmethod
    def get_cash_flow_manager():
        """Cash Flow 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLCashFlowManager()
        else:
            return SQLiteCashFlowManager()
    
    @staticmethod
    def get_inventory_manager():
        """Inventory 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLInventoryManager()
        else:
            return SQLiteInventoryManager()
    
    @staticmethod
    def get_shipping_manager():
        """Shipping 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLShippingManager()
        else:
            return SQLiteShippingManager()
    
    @staticmethod
    def get_invoice_manager():
        """Invoice 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLInvoiceManager()
        else:
            return SQLiteInvoiceManager()
    
    @staticmethod
    def get_business_process_manager():
        """Business Process 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLBusinessProcessManager()
        else:
            return SQLiteBusinessProcessManager()
    
    @staticmethod
    def get_expense_request_manager():
        """Expense Request 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLExpenseRequestManager()
        else:
            return SQLiteExpenseRequestManager()
    
    @staticmethod
    def get_vacation_manager():
        """Vacation 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLVacationManager()
        else:
            return SQLiteVacationManager()
    
    @staticmethod
    def get_sales_product_manager():
        """Sales Product 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLSalesProductManager()
        else:
            return SQLiteSalesProductManager()
    
    @staticmethod
    def get_finished_product_manager():
        """Finished Product 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLFinishedProductManager()
        else:
            return SQLiteFinishedProductManager()
    
    @staticmethod
    def get_cash_transaction_manager():
        """Cash Transaction 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLCashTransactionManager()
        else:
            return SQLiteCashTransactionManager()
    
    @staticmethod
    def get_master_product_manager():
        """Master Product 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLMasterProductManager()
        else:
            return SQLiteMasterProductManager()
    
    @staticmethod
    def get_notice_manager():
        """Notice 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLNoticeManager()
        else:
            return SQLiteNoticeManager()
    
    @staticmethod
    def get_exchange_rate_manager():
        """Exchange Rate 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLExchangeRateManager()
        else:
            return SQLiteExchangeRateManager()
    
    @staticmethod
    def get_system_config_manager():
        """System Config 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLSystemConfigManager()
        else:
            return SQLiteSystemConfigManager()
    
    @staticmethod
    def get_product_code_manager():
        """Product Code 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLProductCodeManager()
        else:
            return SQLiteProductCodeManager()
    
    @staticmethod
    def get_work_status_manager():
        """Work Status 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLWorkStatusManager()
        else:
            return SQLiteWorkStatusManager()
    
    @staticmethod
    def get_weekly_report_manager():
        """Weekly Report 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLWeeklyReportManager()
        else:
            return SQLiteWeeklyReportManager()
    
    @staticmethod
    def get_monthly_sales_manager():
        """Monthly Sales 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLMonthlySalesManager()
        else:
            return SQLiteMonthlySalesManager()
    
    @staticmethod
    def get_note_manager():
        """Note 매니저 반환"""
        db_type = DatabaseConfig.get_database_type()
        if db_type == 'postgresql':
            return PostgreSQLNoteManager()
        else:
            return SQLiteNoteManager()
    
    @staticmethod
    def get_database_status():
        """현재 데이터베이스 상태 반환"""
        db_type = DatabaseConfig.get_database_type()
        
        status = {
            'type': db_type,
            'postgresql_available': bool(os.getenv('DATABASE_URL')),
            'sqlite_available': True,  # 항상 사용 가능
        }
        
        # PostgreSQL 연결 테스트
        if status['postgresql_available']:
            try:
                from managers.postgresql.base_postgresql_manager import BasePostgreSQLManager
                test_manager = BasePostgreSQLManager()
                test_manager.get_connection().close()
                status['postgresql_connected'] = True
            except Exception as e:
                status['postgresql_connected'] = False
                status['postgresql_error'] = str(e)
        
        return status

# 편의 함수들
def get_employee_manager():
    return ManagerFactory.get_employee_manager()

def get_customer_manager():
    return ManagerFactory.get_customer_manager()

def get_quotation_manager():
    return ManagerFactory.get_quotation_manager()

def get_order_manager():
    return ManagerFactory.get_order_manager()

def get_product_manager():
    return ManagerFactory.get_product_manager()

def get_supplier_manager():
    return ManagerFactory.get_supplier_manager()

def get_auth_manager():
    return ManagerFactory.get_auth_manager()

def get_approval_manager():
    return ManagerFactory.get_approval_manager()

def get_database_status():
    return ManagerFactory.get_database_status()

# 보조 매니저 편의 함수들
def get_cash_flow_manager():
    return ManagerFactory.get_cash_flow_manager()

def get_inventory_manager():
    return ManagerFactory.get_inventory_manager()

def get_shipping_manager():
    return ManagerFactory.get_shipping_manager()

def get_invoice_manager():
    return ManagerFactory.get_invoice_manager()

def get_business_process_manager():
    return ManagerFactory.get_business_process_manager()

def get_expense_request_manager():
    return ManagerFactory.get_expense_request_manager()

def get_vacation_manager():
    return ManagerFactory.get_vacation_manager()

def get_sales_product_manager():
    return ManagerFactory.get_sales_product_manager()

def get_finished_product_manager():
    return ManagerFactory.get_finished_product_manager()

def get_cash_transaction_manager():
    return ManagerFactory.get_cash_transaction_manager()

def get_master_product_manager():
    return ManagerFactory.get_master_product_manager()

def get_notice_manager():
    return ManagerFactory.get_notice_manager()

def get_exchange_rate_manager():
    return ManagerFactory.get_exchange_rate_manager()

def get_system_config_manager():
    return ManagerFactory.get_system_config_manager()

def get_product_code_manager():
    return ManagerFactory.get_product_code_manager()

def get_work_status_manager():
    return ManagerFactory.get_work_status_manager()

def get_weekly_report_manager():
    return ManagerFactory.get_weekly_report_manager()

def get_monthly_sales_manager():
    return ManagerFactory.get_monthly_sales_manager()

def get_note_manager():
    return ManagerFactory.get_note_manager()