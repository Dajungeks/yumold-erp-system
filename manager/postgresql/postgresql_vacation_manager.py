# -*- coding: utf-8 -*-
"""
PostgreSQL Vacation 관리 매니저
"""

from .base_postgresql_manager import BasePostgreSQLManager
from datetime import datetime
import uuid

class PostgreSQLVacationManager(BasePostgreSQLManager):
    """PostgreSQL Vacation 관리 매니저"""
    
    def __init__(self):
        super().__init__()
        self.init_tables()
    
    def init_tables(self):
        """Vacation 관련 테이블 초기화 (SQLite 호환)"""
        connection = None
        try:
            connection = self.get_connection()
            cursor = self.get_cursor(connection)
            
            # 휴가 신청 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vacation_requests (
                    id SERIAL PRIMARY KEY,
                    request_id VARCHAR(50) UNIQUE NOT NULL,
                    employee_id VARCHAR(50) NOT NULL,
                    employee_name VARCHAR(200),
                    department VARCHAR(100),
                    position VARCHAR(100),
                    vacation_type VARCHAR(50) NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    total_days INTEGER DEFAULT 0,
                    business_days INTEGER DEFAULT 0,
                    reason TEXT,
                    emergency_contact VARCHAR(200),
                    emergency_phone VARCHAR(50),
                    handover_person VARCHAR(200),
                    handover_details TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    approver_id VARCHAR(50),
                    approver_name VARCHAR(200),
                    approval_date DATE,
                    approval_comments TEXT,
                    rejection_reason TEXT,
                    submitted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 휴가 잔여일수 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vacation_balances (
                    id SERIAL PRIMARY KEY,
                    balance_id VARCHAR(50) UNIQUE NOT NULL,
                    employee_id VARCHAR(50) NOT NULL,
                    year INTEGER NOT NULL,
                    vacation_type VARCHAR(50) NOT NULL,
                    allocated_days REAL DEFAULT 0,
                    used_days REAL DEFAULT 0,
                    remaining_days REAL DEFAULT 0,
                    carried_over REAL DEFAULT 0,
                    expires_date DATE,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(employee_id, year, vacation_type)
                )
            """)
            
            # 휴가 유형 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vacation_types (
                    id SERIAL PRIMARY KEY,
                    type_id VARCHAR(50) UNIQUE NOT NULL,
                    type_name VARCHAR(100) NOT NULL,
                    type_name_en VARCHAR(100),
                    type_name_vi VARCHAR(100),
                    description TEXT,
                    max_days_per_year REAL DEFAULT 0,
                    max_consecutive_days INTEGER DEFAULT 0,
                    requires_approval INTEGER DEFAULT 1,
                    advance_notice_days INTEGER DEFAULT 1,
                    can_carry_over INTEGER DEFAULT 0,
                    is_paid INTEGER DEFAULT 1,
                    is_active INTEGER DEFAULT 1,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 기본 휴가 유형 추가
            cursor.execute("""
                INSERT INTO vacation_types 
                (type_id, type_name, type_name_en, type_name_vi, description, max_days_per_year, 
                 max_consecutive_days, requires_approval, advance_notice_days, can_carry_over, is_paid, is_active)
                VALUES 
                ('ANNUAL', '연차', 'Annual Leave', 'Nghỉ phép năm', '연간 유급휴가', 15, 10, 1, 3, 1, 1, 1),
                ('SICK', '병가', 'Sick Leave', 'Nghỉ ốm', '질병으로 인한 휴가', 30, 30, 1, 0, 0, 1, 1),
                ('PERSONAL', '개인사유', 'Personal Leave', 'Nghỉ cá nhân', '개인적 사유로 인한 휴가', 5, 3, 1, 1, 0, 0, 1),
                ('MATERNITY', '출산휴가', 'Maternity Leave', 'Nghỉ sinh', '출산 및 육아휴가', 90, 90, 1, 30, 0, 1, 1),
                ('EMERGENCY', '긴급사유', 'Emergency Leave', 'Nghỉ khẩn cấp', '응급상황으로 인한 휴가', 3, 3, 1, 0, 0, 1, 1)
                ON CONFLICT (type_id) DO NOTHING
            """)
            
            self.return_connection(connection)
            self.log_info("Vacation 관련 테이블 초기화 완료")
                
        except Exception as e:
            self.log_error(f"Vacation 테이블 초기화 실패: {e}")
            if 'connection' in locals() and connection:
                self.return_connection(connection)
    
    def get_vacation_summary(self, employee_id=None, year=None):
        """휴가 요약 정보 조회 (SQLite 매니저 호환)"""
        connection = None
        try:
            connection = self.get_connection()
            
            if employee_id:
                # 특정 직원의 휴가 요약
                query = '''
                    SELECT 
                        employee_id,
                        employee_name,
                        COUNT(*) as total_requests,
                        COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_requests,
                        SUM(CASE WHEN status = 'approved' THEN total_days ELSE 0 END) as total_used_days,
                        SUM(CASE WHEN status = 'pending' THEN total_days ELSE 0 END) as pending_days
                    FROM vacation_requests 
                    WHERE employee_id = %s
                '''
                params = [employee_id]
                
                if year:
                    query += " AND EXTRACT(YEAR FROM start_date) = %s"
                    params.append(year)
                    
                query += " GROUP BY employee_id, employee_name"
                
                result = self.execute_query(query, params, fetch_one=True)
                self.return_connection(connection)
                return result if result else {}
            else:
                # 전체 직원 휴가 요약
                query = '''
                    SELECT 
                        employee_id,
                        employee_name,
                        COUNT(*) as total_requests,
                        COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_requests,
                        SUM(CASE WHEN status = 'approved' THEN total_days ELSE 0 END) as total_used_days
                    FROM vacation_requests
                '''
                params = []
                
                if year:
                    query += " WHERE EXTRACT(YEAR FROM start_date) = %s"
                    params.append(year)
                    
                query += " GROUP BY employee_id, employee_name ORDER BY employee_name"
                
                result = self.execute_query(query, params, fetch_all=True)
                self.return_connection(connection)
                return result if result else []
                
        except Exception as e:
            self.log_error(f"휴가 요약 조회 실패: {e}")
            if 'connection' in locals() and connection:
                self.return_connection(connection)
            return {} if employee_id else []
    
    def get_vacations_by_employee(self, employee_id, year=None, status=None):
        """직원별 휴가 내역 조회 (SQLite 매니저 호환)"""
        connection = None
        try:
            connection = self.get_connection()
            query = "SELECT * FROM vacation_requests WHERE employee_id = %s"
            params = [employee_id]
            
            if year:
                query += " AND EXTRACT(YEAR FROM start_date) = %s"
                params.append(str(year))
            if status:
                query += " AND status = %s"
                params.append(status)
            
            query += " ORDER BY submitted_date DESC"
            
            result = self.execute_query(query, params, fetch_all=True)
            self.return_connection(connection)
            
            # pandas DataFrame 형태로 반환 (SQLite 매니저 호환)
            import pandas as pd
            if result:
                return pd.DataFrame(result)
            else:
                return pd.DataFrame()
                
        except Exception as e:
            self.log_error(f"직원별 휴가 내역 조회 실패: {e}")
            if 'connection' in locals() and connection:
                self.return_connection(connection)
            import pandas as pd
            return pd.DataFrame()
    
    def get_statistics(self):
        """통계 조회"""
        connection = None
        try:
            connection = self.get_connection()
            query = "SELECT COUNT(*) as total_count FROM vacation_requests"
            result = self.execute_query(query, fetch_one=True)
            self.return_connection(connection)
            
            # result가 dict인지 확인하고 처리
            if isinstance(result, dict):
                return {'total_count': result.get('total_count', 0)}
            elif isinstance(result, (list, tuple)) and result:
                # result가 리스트나 튜플인 경우 첫 번째 값을 사용
                return {'total_count': result[0] if isinstance(result[0], int) else 0}
            else:
                return {'total_count': 0}
                
        except Exception as e:
            self.log_error(f"통계 조회 실패: {e}")
            if 'connection' in locals() and connection:
                self.return_connection(connection)
            return {'total_count': 0}
