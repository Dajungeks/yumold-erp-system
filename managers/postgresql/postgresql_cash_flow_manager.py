# -*- coding: utf-8 -*-
"""
PostgreSQL CashFlow 관리 매니저
"""

from .base_postgresql_manager import BasePostgreSQLManager
from datetime import datetime
import uuid

class PostgreSQLCashFlowManager(BasePostgreSQLManager):
    """PostgreSQL CashFlow 관리 매니저"""
    
    def __init__(self):
        super().__init__()
        self.init_tables()
    
    def init_tables(self):
        """CashFlow 관련 테이블 초기화"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 현금 흐름 거래 테이블 (완전한 구조)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cash_flows (
                        id SERIAL PRIMARY KEY,
                        transaction_id VARCHAR(50) UNIQUE NOT NULL,
                        reference_id VARCHAR(50),
                        reference_type VARCHAR(50),
                        transaction_type VARCHAR(20) NOT NULL,
                        amount DECIMAL(15,2) NOT NULL DEFAULT 0,
                        currency VARCHAR(3) DEFAULT 'USD',
                        transaction_date DATE,
                        description TEXT,
                        status VARCHAR(20) DEFAULT 'active',
                        account VARCHAR(100),
                        created_by VARCHAR(100),
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 현금 흐름 결제 테이블
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cash_flow_payments (
                        id SERIAL PRIMARY KEY,
                        payment_id VARCHAR(50) UNIQUE NOT NULL,
                        invoice_id VARCHAR(50),
                        amount DECIMAL(15,2) NOT NULL DEFAULT 0,
                        currency VARCHAR(3) DEFAULT 'USD',
                        payment_date DATE,
                        payment_method VARCHAR(50),
                        status VARCHAR(20) DEFAULT 'pending',
                        notes TEXT,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                self.log_info("CashFlow 관련 테이블 초기화 완료")
                conn.commit()
                
        except Exception as e:
            self.log_error(f"CashFlow 테이블 초기화 실패: {e}")
    
    def get_all_items(self):
        """모든 항목 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM cash_flows ORDER BY created_date DESC")
                
                columns = [desc[0] for desc in cursor.description]
                items = []
                
                for row in cursor.fetchall():
                    item = dict(zip(columns, row))
                    items.append(item)
                
                return items
                
        except Exception as e:
            self.log_error(f"항목 조회 실패: {e}")
            return []
    
    def get_statistics(self):
        """통계 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM cash_flows")
                total_count = cursor.fetchone()[0]
                
                return {'total_count': total_count}
                
        except Exception as e:
            self.log_error(f"통계 조회 실패: {e}")
            return {'total_count': 0}
    
    def get_cash_flow_summary(self, start_date=None, end_date=None):
        """현금 흐름 요약 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                base_query = """
                    SELECT 
                        SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as total_income,
                        SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) as total_expense
                    FROM cash_flows
                    WHERE status = 'active'
                """
                
                params = []
                if start_date:
                    base_query += " AND created_date >= %s"
                    params.append(start_date)
                if end_date:
                    base_query += " AND created_date <= %s"
                    params.append(end_date)
                
                cursor.execute(base_query, params)
                result = cursor.fetchone()
                
                if result:
                    total_income = float(result[0] or 0)
                    total_expense = float(result[1] or 0)
                    return {
                        'total_income': total_income,
                        'total_expense': total_expense,
                        'current_balance': total_income - total_expense
                    }
                else:
                    return {'total_income': 0, 'total_expense': 0, 'current_balance': 0}
                    
        except Exception as e:
            self.log_error(f"현금 흐름 요약 조회 실패: {e}")
            return {'total_income': 0, 'total_expense': 0, 'current_balance': 0}
    
    def get_all_transactions(self):
        """모든 거래 내역 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM cash_flows 
                    WHERE status = 'active'
                    ORDER BY created_date DESC
                """)
                
                columns = [desc[0] for desc in cursor.description]
                transactions = []
                
                for row in cursor.fetchall():
                    transaction = dict(zip(columns, row))
                    transactions.append(transaction)
                
                return transactions
                
        except Exception as e:
            self.log_error(f"거래 내역 조회 실패: {e}")
            return []
    
    def get_monthly_cash_flow(self):
        """월별 현금 흐름 요약 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        TO_CHAR(transaction_date, 'YYYY-MM') as month,
                        SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as income,
                        SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) as expense,
                        COUNT(*) as transaction_count
                    FROM cash_flows 
                    WHERE status = 'active' AND transaction_date IS NOT NULL
                    GROUP BY TO_CHAR(transaction_date, 'YYYY-MM')
                    ORDER BY month DESC
                    LIMIT 12
                """)
                
                monthly_data = []
                for row in cursor.fetchall():
                    month, income, expense, count = row
                    monthly_data.append({
                        'month': month,
                        'income': float(income or 0),
                        'expense': float(expense or 0),
                        'net_income': float((income or 0) - (expense or 0)),
                        'transaction_count': int(count or 0)
                    })
                
                return monthly_data
                
        except Exception as e:
            self.log_error(f"월별 현금 흐름 조회 실패: {e}")
            return []
