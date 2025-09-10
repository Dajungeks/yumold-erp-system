# -*- coding: utf-8 -*-
"""
PostgreSQL ExpenseRequest 관리 매니저
"""

from .base_postgresql_manager import BasePostgreSQLManager
from datetime import datetime
import uuid

class PostgreSQLExpenseRequestManager(BasePostgreSQLManager):
    """PostgreSQL ExpenseRequest 관리 매니저"""
    
    def __init__(self):
        super().__init__()
        self.init_tables()
    
    def init_tables(self):
        """ExpenseRequest 관련 테이블 초기화"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 완전한 expense_requests 테이블 생성 (SQLite 매니저 참조)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS expense_requests (
                        id SERIAL PRIMARY KEY,
                        request_id VARCHAR(50) UNIQUE NOT NULL,
                        requester_id VARCHAR(50) NOT NULL,
                        requester_name VARCHAR(100) NOT NULL,
                        request_date DATE NOT NULL,
                        expense_title VARCHAR(200) NOT NULL,
                        expense_description TEXT,
                        category VARCHAR(100),
                        amount DECIMAL(15, 2) NOT NULL,
                        currency VARCHAR(10) DEFAULT 'VND',
                        expected_date DATE,
                        status VARCHAR(20) DEFAULT 'pending',
                        current_step INTEGER DEFAULT 1,
                        total_steps INTEGER DEFAULT 1,
                        attachment_path TEXT,
                        notes TEXT,
                        first_approver_id VARCHAR(50),
                        first_approver_name VARCHAR(100),
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                self.log_info("ExpenseRequest 관련 테이블 초기화 완료")
                conn.commit()
                
        except Exception as e:
            self.log_error(f"ExpenseRequest 테이블 초기화 실패: {e}")
    
    def get_all_items(self):
        """모든 항목 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM expense_requests ORDER BY created_date DESC")
                
                columns = [desc[0] for desc in cursor.description]
                items = []
                
                for row in cursor.fetchall():
                    item = dict(zip(columns, row))
                    items.append(item)
                
                return items
                
        except Exception as e:
            self.log_error(f"항목 조회 실패: {e}")
            return []
    
    def get_my_requests(self, user_id):
        """내 지출요청서 목록 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT 
                        request_id,
                        expense_title as expense_type,
                        amount,
                        currency,
                        expected_date as expense_date,
                        expense_description as purpose,
                        notes as additional_notes,
                        status,
                        request_date,
                        requester_name,
                        category,
                        first_approver_name,
                        attachment_path as attachment
                    FROM expense_requests 
                    WHERE requester_id = %s
                    ORDER BY request_date DESC
                """
                
                cursor.execute(query, (user_id,))
                columns = [desc[0] for desc in cursor.description]
                requests = []
                
                for row in cursor.fetchall():
                    request_dict = dict(zip(columns, row))
                    # 추가 필드 매핑
                    request_dict['vendor'] = ''  # 업체 정보는 별도 처리
                    request_dict['priority'] = 'normal'  # 우선순위 기본값
                    requests.append(request_dict)
                
                return requests
                
        except Exception as e:
            self.log_error(f"내 요청서 조회 중 오류: {e}")
            return []
    
    def get_statistics(self):
        """통계 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM expense_requests")
                total_count = cursor.fetchone()[0]
                
                return {'total_count': total_count}
                
        except Exception as e:
            self.log_error(f"통계 조회 실패: {e}")
            return {'total_count': 0}
