# -*- coding: utf-8 -*-
"""
SQLite 기반 현금흐름 관리 시스템
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

class SQLiteCashFlowManager:
    def __init__(self, db_path="erp_system.db"):
        """SQLite 기반 현금흐름 매니저 초기화"""
        self.db_path = db_path
        self.init_tables()
    
    def get_connection(self):
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_tables(self):
        """현금흐름 관련 테이블 초기화"""
        with self.get_connection() as conn:
            # 현금흐름 기본 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cash_flows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    flow_id TEXT UNIQUE NOT NULL,
                    transaction_date TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'VND',
                    flow_type TEXT NOT NULL CHECK (flow_type IN ('inflow', 'outflow')),
                    account_type TEXT,
                    reference_id TEXT,
                    reference_type TEXT,
                    created_by TEXT,
                    notes TEXT,
                    status TEXT DEFAULT 'confirmed',
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 예산 계획 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS budget_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    budget_id TEXT UNIQUE NOT NULL,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT,
                    planned_amount REAL NOT NULL,
                    currency TEXT DEFAULT 'VND',
                    description TEXT,
                    status TEXT DEFAULT 'active',
                    created_by TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 은행 계좌 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS bank_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT UNIQUE NOT NULL,
                    account_name TEXT NOT NULL,
                    account_number TEXT,
                    bank_name TEXT,
                    currency TEXT DEFAULT 'VND',
                    account_type TEXT,
                    initial_balance REAL DEFAULT 0,
                    current_balance REAL DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    notes TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("현금흐름 관련 테이블 초기화 완료")
    
    def generate_flow_id(self):
        """현금흐름 ID 생성"""
        today = datetime.now().strftime("%Y%m%d")
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT COUNT(*) FROM cash_flows 
                WHERE flow_id LIKE ?
            ''', (f"CF{today}%",))
            
            count = cursor.fetchone()[0]
            sequence = count + 1
            
        return f"CF{today}{sequence:03d}"
    
    def add_cash_flow(self, flow_data):
        """현금흐름 항목 추가"""
        try:
            with self.get_connection() as conn:
                # ID 자동 생성
                if 'flow_id' not in flow_data or not flow_data['flow_id']:
                    flow_data['flow_id'] = self.generate_flow_id()
                
                # 필수 데이터 검증
                required_fields = ['transaction_date', 'description', 'category', 'amount', 'flow_type']
                for field in required_fields:
                    if field not in flow_data or not flow_data[field]:
                        return False, f"필수 필드가 누락되었습니다: {field}"
                
                # 데이터 삽입
                conn.execute('''
                    INSERT INTO cash_flows (
                        flow_id, transaction_date, description, category, subcategory,
                        amount, currency, flow_type, account_type, reference_id, 
                        reference_type, created_by, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    flow_data['flow_id'],
                    flow_data['transaction_date'],
                    flow_data['description'],
                    flow_data['category'],
                    flow_data.get('subcategory', ''),
                    float(flow_data['amount']),
                    flow_data.get('currency', 'VND'),
                    flow_data['flow_type'],
                    flow_data.get('account_type', ''),
                    flow_data.get('reference_id', ''),
                    flow_data.get('reference_type', ''),
                    flow_data.get('created_by', ''),
                    flow_data.get('notes', '')
                ))
                
                conn.commit()
                logger.info(f"현금흐름 추가 성공: {flow_data['flow_id']}")
                return True, "현금흐름이 성공적으로 추가되었습니다."
                
        except Exception as e:
            logger.error(f"현금흐름 추가 오류: {str(e)}")
            return False, f"현금흐름 추가 중 오류가 발생했습니다: {str(e)}"
    
    def get_cash_flows(self, start_date=None, end_date=None, flow_type=None, category=None):
        """현금흐름 조회"""
        try:
            with self.get_connection() as conn:
                base_query = "SELECT * FROM cash_flows"
                
                conditions = []
                params = []
                
                if start_date:
                    conditions.append("DATE(transaction_date) >= ?")
                    params.append(start_date)
                
                if end_date:
                    conditions.append("DATE(transaction_date) <= ?")
                    params.append(end_date)
                
                if flow_type:
                    conditions.append("flow_type = ?")
                    params.append(flow_type)
                
                if category:
                    conditions.append("category = ?")
                    params.append(category)
                
                if conditions:
                    query = base_query + " WHERE " + " AND ".join(conditions)
                else:
                    query = base_query
                
                query += " ORDER BY transaction_date DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"현금흐름 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_cash_flow_summary(self, start_date=None, end_date=None):
        """현금흐름 요약 통계"""
        try:
            with self.get_connection() as conn:
                base_query = '''
                    SELECT 
                        flow_type,
                        currency,
                        SUM(amount) as total_amount,
                        COUNT(*) as transaction_count,
                        AVG(amount) as average_amount
                    FROM cash_flows
                '''
                
                conditions = []
                params = []
                
                if start_date:
                    conditions.append("DATE(transaction_date) >= ?")
                    params.append(start_date)
                
                if end_date:
                    conditions.append("DATE(transaction_date) <= ?")
                    params.append(end_date)
                
                if conditions:
                    query = base_query + " WHERE " + " AND ".join(conditions)
                else:
                    query = base_query
                
                query += " GROUP BY flow_type, currency ORDER BY flow_type, currency"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"현금흐름 요약 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_monthly_cash_flow(self, year=None, month=None):
        """월별 현금흐름 분석"""
        try:
            with self.get_connection() as conn:
                if year and month:
                    # 특정 년월
                    query = '''
                        SELECT 
                            strftime('%Y-%m-%d', transaction_date) as date,
                            flow_type,
                            SUM(amount) as daily_amount
                        FROM cash_flows
                        WHERE strftime('%Y', transaction_date) = ? 
                        AND strftime('%m', transaction_date) = ?
                        GROUP BY DATE(transaction_date), flow_type
                        ORDER BY date
                    '''
                    params = (str(year), f"{month:02d}")
                else:
                    # 최근 12개월
                    query = '''
                        SELECT 
                            strftime('%Y-%m', transaction_date) as month,
                            flow_type,
                            SUM(amount) as monthly_amount
                        FROM cash_flows
                        WHERE DATE(transaction_date) >= DATE('now', '-12 months')
                        GROUP BY strftime('%Y-%m', transaction_date), flow_type
                        ORDER BY month
                    '''
                    params = ()
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"월별 현금흐름 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_category_analysis(self, start_date=None, end_date=None):
        """카테고리별 현금흐름 분석"""
        try:
            with self.get_connection() as conn:
                base_query = '''
                    SELECT 
                        category,
                        subcategory,
                        flow_type,
                        SUM(amount) as total_amount,
                        COUNT(*) as transaction_count,
                        AVG(amount) as average_amount
                    FROM cash_flows
                '''
                
                conditions = []
                params = []
                
                if start_date:
                    conditions.append("DATE(transaction_date) >= ?")
                    params.append(start_date)
                
                if end_date:
                    conditions.append("DATE(transaction_date) <= ?")
                    params.append(end_date)
                
                if conditions:
                    query = base_query + " WHERE " + " AND ".join(conditions)
                else:
                    query = base_query
                
                query += " GROUP BY category, subcategory, flow_type ORDER BY total_amount DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"카테고리별 분석 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def add_budget_plan(self, budget_data):
        """예산 계획 추가"""
        try:
            with self.get_connection() as conn:
                # ID 자동 생성
                if 'budget_id' not in budget_data or not budget_data['budget_id']:
                    today = datetime.now().strftime("%Y%m%d")
                    cursor = conn.execute("SELECT COUNT(*) FROM budget_plans WHERE budget_id LIKE ?", (f"BUD{today}%",))
                    count = cursor.fetchone()[0]
                    budget_data['budget_id'] = f"BUD{today}{count+1:03d}"
                
                # 데이터 삽입
                conn.execute('''
                    INSERT INTO budget_plans (
                        budget_id, period_start, period_end, category, subcategory,
                        planned_amount, currency, description, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    budget_data['budget_id'],
                    budget_data['period_start'],
                    budget_data['period_end'],
                    budget_data['category'],
                    budget_data.get('subcategory', ''),
                    float(budget_data['planned_amount']),
                    budget_data.get('currency', 'VND'),
                    budget_data.get('description', ''),
                    budget_data.get('created_by', '')
                ))
                
                conn.commit()
                logger.info(f"예산 계획 추가 성공: {budget_data['budget_id']}")
                return True, "예산 계획이 성공적으로 추가되었습니다."
                
        except Exception as e:
            logger.error(f"예산 계획 추가 오류: {str(e)}")
            return False, f"예산 계획 추가 중 오류가 발생했습니다: {str(e)}"
    
    def get_budget_vs_actual(self, start_date, end_date):
        """예산 대비 실적 분석"""
        try:
            with self.get_connection() as conn:
                # 예산 조회
                budget_query = '''
                    SELECT category, subcategory, SUM(planned_amount) as budgeted
                    FROM budget_plans
                    WHERE period_start <= ? AND period_end >= ?
                    GROUP BY category, subcategory
                '''
                
                # 실적 조회
                actual_query = '''
                    SELECT category, subcategory, SUM(amount) as actual
                    FROM cash_flows
                    WHERE DATE(transaction_date) BETWEEN ? AND ?
                    AND flow_type = 'outflow'
                    GROUP BY category, subcategory
                '''
                
                budget_df = pd.read_sql_query(budget_query, conn, params=(start_date, end_date))
                actual_df = pd.read_sql_query(actual_query, conn, params=(start_date, end_date))
                
                # 데이터 병합
                result = budget_df.merge(actual_df, on=['category', 'subcategory'], how='outer').fillna(0)
                result['variance'] = result['actual'] - result['budgeted']
                result['variance_pct'] = (result['variance'] / result['budgeted'] * 100).fillna(0)
                
                return result
                
        except Exception as e:
            logger.error(f"예산 대비 실적 분석 오류: {str(e)}")
            return pd.DataFrame()
    
    def delete_cash_flow(self, flow_id):
        """현금흐름 항목 삭제"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('DELETE FROM cash_flows WHERE flow_id = ?', (flow_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"현금흐름 삭제 성공: {flow_id}")
                    return True, "현금흐름이 성공적으로 삭제되었습니다."
                else:
                    return False, "해당 현금흐름을 찾을 수 없습니다."
                    
        except Exception as e:
            logger.error(f"현금흐름 삭제 오류: {str(e)}")
            return False, f"현금흐름 삭제 중 오류가 발생했습니다: {str(e)}"
    
    def update_cash_flow(self, flow_id, flow_data):
        """현금흐름 항목 업데이트"""
        try:
            with self.get_connection() as conn:
                # 업데이트할 필드들 동적 생성
                fields = []
                values = []
                
                for key, value in flow_data.items():
                    if key != 'flow_id':  # ID는 업데이트하지 않음
                        fields.append(f"{key} = ?")
                        values.append(value)
                
                if not fields:
                    return False, "업데이트할 정보가 없습니다."
                
                # 업데이트 쿼리 실행
                values.append(flow_id)  # WHERE 절용
                query = f"UPDATE cash_flows SET {', '.join(fields)}, updated_date = CURRENT_TIMESTAMP WHERE flow_id = ?"
                
                cursor = conn.execute(query, values)
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"현금흐름 업데이트 성공: {flow_id}")
                    return True, "현금흐름이 성공적으로 업데이트되었습니다."
                else:
                    return False, "해당 현금흐름을 찾을 수 없습니다."
                    
        except Exception as e:
            logger.error(f"현금흐름 업데이트 오류: {str(e)}")
            return False, f"현금흐름 업데이트 중 오류가 발생했습니다: {str(e)}"
    def get_all_transactions(self):
        """모든 현금흐름 거래 내역을 조회합니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        flow_id,
                        transaction_date,
                        description,
                        category,
                        subcategory,
                        amount,
                        currency,
                        flow_type,
                        account_type,
                        reference_id,
                        reference_type,
                        created_by,
                        notes,
                        status,
                        created_date
                    FROM cash_flows
                    ORDER BY transaction_date DESC, created_date DESC
                """)
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"현금흐름 거래 조회 오류: {e}")
            return []

    def get_transactions_by_date_range(self, start_date, end_date):
        """날짜 범위별 거래 내역 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM cash_flows
                    WHERE transaction_date BETWEEN ? AND ?
                    ORDER BY transaction_date DESC
                """, (start_date, end_date))
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"날짜별 거래 조회 오류: {e}")
            return []

    def get_transactions_by_category(self, category):
        """카테고리별 거래 내역 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM cash_flows
                    WHERE category = ?
                    ORDER BY transaction_date DESC
                """, (category,))
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"카테고리별 거래 조회 오류: {e}")
            return []

    def get_balance_summary(self):
        """현금 잔액 요약"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        SUM(CASE WHEN flow_type = "inflow" THEN amount ELSE 0 END) as total_inflow,
                        SUM(CASE WHEN flow_type = "outflow" THEN amount ELSE 0 END) as total_outflow,
                        SUM(CASE WHEN flow_type = "inflow" THEN amount ELSE -amount END) as net_balance
                    FROM cash_flows
                    WHERE status = "confirmed"
                """)
                result = cursor.fetchone()
                if result:
                    return {
                        "total_inflow": result["total_inflow"] or 0,
                        "total_outflow": result["total_outflow"] or 0,
                        "net_balance": result["net_balance"] or 0
                    }
                return {"total_inflow": 0, "total_outflow": 0, "net_balance": 0}
        except Exception as e:
            logger.error(f"잔액 요약 조회 오류: {e}")
            return {"total_inflow": 0, "total_outflow": 0, "net_balance": 0}

