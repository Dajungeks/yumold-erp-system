# -*- coding: utf-8 -*-
"""
SQLite 기반 인증 관리 시스템
"""

import sqlite3
import pandas as pd
from datetime import datetime
import logging
import hashlib

logger = logging.getLogger(__name__)

class SQLiteAuthManager:
    def __init__(self, db_path="erp_system.db"):
        """SQLite 기반 인증 매니저 초기화"""
        self.db_path = db_path
        self.init_tables()
    
    def get_connection(self):
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_tables(self):
        """인증 관련 테이블 초기화"""
        with self.get_connection() as conn:
            # 로그인 히스토리 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS login_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    user_type TEXT NOT NULL,
                    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    logout_time TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    success BOOLEAN DEFAULT TRUE,
                    notes TEXT
                )
            ''')
            
            # 사용자 세션 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    user_type TEXT NOT NULL,
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    expires_at TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("인증 관련 테이블 초기화 완료")
    
    def hash_password(self, password):
        """패스워드 해시 생성"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate_employee(self, employee_id, password):
        """직원 인증 (법인장 포함)"""
        try:
            with self.get_connection() as conn:
                # 직원 정보 조회 (모든 필드 포함)
                cursor = conn.execute('''
                    SELECT employee_id, name, position, status, password, access_level, department, phone, email
                    FROM employees 
                    WHERE employee_id = ? AND status = 'active'
                ''', (employee_id,))
                
                row = cursor.fetchone()
                if not row:
                    self._log_login_attempt(employee_id, 'employee', False, '직원 정보 없음')
                    return False, None
                
                # Row 객체를 딕셔너리로 변환
                employee = {
                    'employee_id': row[0],
                    'name': row[1],
                    'position': row[2],
                    'status': row[3],
                    'password': row[4],
                    'access_level': row[5],
                    'department': row[6],
                    'phone': row[7] if len(row) > 7 else '',
                    'email': row[8] if len(row) > 8 else ''
                }
                
                # 패스워드 검증
                stored_password = employee['password'] or ''
                
                # 평문 패스워드와 해시된 패스워드 모두 지원
                if stored_password == password or (stored_password and self.hash_password(password) == stored_password):
                    # 권한 설정 로직 개선
                    position = employee['position'] or ''
                    department = employee['department'] or ''
                    stored_access_level = employee['access_level'] or ''
                    
                    # 권한 설정 우선순위 (일반/총무/법인장):
                    # 1. 법인장 권한: 직책이 법인장인 경우
                    if position == '법인장':
                        access_level = 'ceo'  # 법인장
                        user_type = 'ceo'
                    # 2. 총무 권한: 부서가 총무인 경우
                    elif department == '총무':
                        access_level = 'admin'  # 총무
                        user_type = 'admin'
                    # 3. 마스터 권한: 하드코딩된 master 권한
                    elif stored_access_level == 'master':
                        access_level = 'master'  # 마스터
                        user_type = 'master'
                    # 4. 일반 직원
                    else:
                        access_level = 'user'  # 일반
                        user_type = 'user'
                    
                    self._log_login_attempt(employee_id, user_type, True)
                    
                    employee_info = {
                        'user_id': employee['employee_id'],
                        'name': employee['name'],
                        'position': position,
                        'department': department,
                        'phone': employee['phone'],
                        'email': employee['email'],
                        'user_type': user_type,
                        'access_level': access_level
                    }
                    
                    return True, employee_info
                else:
                    self._log_login_attempt(employee_id, 'employee', False, '패스워드 불일치')
                    return False, None
                    
        except Exception as e:
            logger.error(f"직원 인증 오류: {str(e)}")
            return False, None
    
    def authenticate_master(self, password):
        """마스터(법인장) 인증"""
        try:
            # 하드코딩된 마스터 패스워드 (실제 운영에서는 DB에 저장 권장)
            MASTER_PASSWORD = "ymv2024"
            
            if password == MASTER_PASSWORD:
                self._log_login_attempt('master', 'master', True)
                
                master_info = {
                    'user_id': 'master',
                    'name': '법인장',
                    'position': 'CEO',
                    'department': '경영진',
                    'phone': '091-4888000',
                    'email': 'ceo@yumold.vn',
                    'user_type': 'master',
                    'access_level': 'master'
                }
                
                return True, master_info
            else:
                self._log_login_attempt('master', 'master', False, '마스터 패스워드 불일치')
                return False, None
                
        except Exception as e:
            logger.error(f"마스터 인증 오류: {str(e)}")
            return False, None
    
    def reset_user_password(self, employee_id, new_password):
        """직원 비밀번호 재설정"""
        try:
            with self.get_connection() as conn:
                # 직원이 존재하는지 확인
                cursor = conn.execute('''
                    SELECT employee_id, name FROM employees 
                    WHERE employee_id = ?
                ''', (employee_id,))
                
                employee = cursor.fetchone()
                
                if not employee:
                    return False, "직원 정보를 찾을 수 없습니다."
                
                # 비밀번호 업데이트 (평문으로 저장)
                conn.execute('''
                    UPDATE employees 
                    SET password = ?, updated_date = CURRENT_TIMESTAMP 
                    WHERE employee_id = ?
                ''', (new_password, employee_id))
                
                conn.commit()
                
                # 로그 기록
                self._log_password_reset(employee_id)
                
                logger.info(f"직원 {employee_id}의 비밀번호가 재설정되었습니다.")
                return True, f"직원 {employee['name']}의 비밀번호가 성공적으로 재설정되었습니다."
                
        except Exception as e:
            logger.error(f"비밀번호 재설정 오류: {str(e)}")
            return False, f"비밀번호 재설정 중 오류가 발생했습니다: {str(e)}"
    
    def change_password(self, employee_id, current_password, new_password):
        """직원 비밀번호 변경 (본인이 변경하는 경우)"""
        try:
            with self.get_connection() as conn:
                # 현재 비밀번호 확인
                cursor = conn.execute('''
                    SELECT password FROM employees 
                    WHERE employee_id = ? AND status = 'active'
                ''', (employee_id,))
                
                employee = cursor.fetchone()
                
                if not employee:
                    return False, "직원 정보를 찾을 수 없습니다."
                
                stored_password = employee['password'] or ''
                
                # 현재 비밀번호 검증
                if stored_password != current_password and self.hash_password(current_password) != stored_password:
                    return False, "현재 비밀번호가 올바르지 않습니다."
                
                # 새 비밀번호로 업데이트
                conn.execute('''
                    UPDATE employees 
                    SET password = ?, updated_date = CURRENT_TIMESTAMP 
                    WHERE employee_id = ?
                ''', (new_password, employee_id))
                
                conn.commit()
                
                logger.info(f"직원 {employee_id}가 비밀번호를 변경했습니다.")
                return True, "비밀번호가 성공적으로 변경되었습니다."
                
        except Exception as e:
            logger.error(f"비밀번호 변경 오류: {str(e)}")
            return False, f"비밀번호 변경 중 오류가 발생했습니다: {str(e)}"
    
    def _log_password_reset(self, employee_id):
        """비밀번호 재설정 기록"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO login_history (user_id, user_type, success, notes)
                    VALUES (?, ?, ?, ?)
                ''', (employee_id, 'employee', True, '비밀번호 재설정'))
                conn.commit()
        except Exception as e:
            logger.error(f"비밀번호 재설정 기록 오류: {str(e)}")
    
    def _log_login_attempt(self, user_id, user_type, success, notes=""):
        """로그인 시도 기록"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO login_history (user_id, user_type, success, notes)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, user_type, success, notes))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"로그인 기록 오류: {str(e)}")
    
    def create_session(self, user_id, user_type):
        """사용자 세션 생성"""
        try:
            import uuid
            session_id = str(uuid.uuid4())
            
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO user_sessions (session_id, user_id, user_type)
                    VALUES (?, ?, ?)
                ''', (session_id, user_id, user_type))
                
                conn.commit()
                return session_id
                
        except Exception as e:
            logger.error(f"세션 생성 오류: {str(e)}")
            return None
    
    def validate_session(self, session_id):
        """세션 유효성 검증"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT user_id, user_type, is_active 
                    FROM user_sessions 
                    WHERE session_id = ? AND is_active = TRUE
                ''', (session_id,))
                
                session = cursor.fetchone()
                
                if session:
                    # 마지막 활동 시간 업데이트
                    conn.execute('''
                        UPDATE user_sessions 
                        SET last_activity = CURRENT_TIMESTAMP 
                        WHERE session_id = ?
                    ''', (session_id,))
                    conn.commit()
                    
                    return True, dict(session)
                else:
                    return False, None
                    
        except Exception as e:
            logger.error(f"세션 검증 오류: {str(e)}")
            return False, None
    
    def end_session(self, session_id):
        """세션 종료"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    UPDATE user_sessions 
                    SET is_active = FALSE, logout_time = CURRENT_TIMESTAMP 
                    WHERE session_id = ?
                ''', (session_id,))
                
                # 로그인 히스토리 업데이트
                conn.execute('''
                    UPDATE login_history 
                    SET logout_time = CURRENT_TIMESTAMP 
                    WHERE user_id = (
                        SELECT user_id FROM user_sessions WHERE session_id = ?
                    ) AND logout_time IS NULL
                ''', (session_id,))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"세션 종료 오류: {str(e)}")
            return False
    
    def get_login_history(self, user_id=None, limit=100):
        """로그인 히스토리 조회"""
        try:
            with self.get_connection() as conn:
                if user_id:
                    query = '''
                        SELECT * FROM login_history 
                        WHERE user_id = ? 
                        ORDER BY login_time DESC 
                        LIMIT ?
                    '''
                    df = pd.read_sql_query(query, conn, params=[user_id, limit])
                else:
                    query = '''
                        SELECT * FROM login_history 
                        ORDER BY login_time DESC 
                        LIMIT ?
                    '''
                    df = pd.read_sql_query(query, conn, params=[limit])
                
                return df
                
        except Exception as e:
            logger.error(f"로그인 히스토리 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_active_sessions(self):
        """활성 세션 목록 조회"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT s.*, e.name as user_name
                    FROM user_sessions s
                    LEFT JOIN employees e ON s.user_id = e.employee_id
                    WHERE s.is_active = TRUE
                    ORDER BY s.last_activity DESC
                '''
                
                df = pd.read_sql_query(query, conn)
                return df
                
        except Exception as e:
            logger.error(f"활성 세션 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def cleanup_expired_sessions(self):
        """만료된 세션 정리"""
        try:
            with self.get_connection() as conn:
                # 24시간 이상 비활성 세션 정리
                conn.execute('''
                    UPDATE user_sessions 
                    SET is_active = FALSE 
                    WHERE is_active = TRUE 
                    AND datetime(last_activity) < datetime('now', '-24 hours')
                ''')
                
                conn.commit()
                logger.info("만료된 세션 정리 완료")
                return True
                
        except Exception as e:
            logger.error(f"세션 정리 오류: {str(e)}")
            return False
    
    def change_employee_password(self, employee_id, old_password, new_password):
        """직원 패스워드 변경"""
        try:
            with self.get_connection() as conn:
                # 현재 패스워드 확인
                cursor = conn.execute('''
                    SELECT password FROM employees WHERE employee_id = ?
                ''', (employee_id,))
                
                current = cursor.fetchone()
                if not current:
                    return False
                
                # 기존 패스워드 검증
                stored_password = current['password']
                hashed_old = self.hash_password(old_password)
                
                if stored_password != old_password and stored_password != hashed_old:
                    return False
                
                # 새 패스워드로 업데이트 (해시화)
                hashed_new = self.hash_password(new_password)
                conn.execute('''
                    UPDATE employees 
                    SET password = ?, updated_date = CURRENT_TIMESTAMP 
                    WHERE employee_id = ?
                ''', (hashed_new, employee_id))
                
                conn.commit()
                logger.info(f"직원 패스워드 변경 성공: {employee_id}")
                return True
                
        except Exception as e:
            logger.error(f"패스워드 변경 오류: {str(e)}")
            return False
    
    def get_user_permissions(self, user_id, user_type):
        """사용자 권한 조회"""
        try:
            if user_type == 'master':
                # 마스터는 모든 권한
                return {
                    'can_manage_employees': True,
                    'can_manage_customers': True,
                    'can_manage_products': True,
                    'can_manage_orders': True,
                    'can_manage_suppliers': True,
                    'can_approve_expenses': True,
                    'can_view_reports': True,
                    'can_manage_system': True
                }
            elif user_type == 'employee':
                # 직원 기본 권한 (추후 직급/부서별로 세분화 가능)
                return {
                    'can_manage_employees': False,
                    'can_manage_customers': True,
                    'can_manage_products': True,
                    'can_manage_orders': True,
                    'can_manage_suppliers': True,
                    'can_approve_expenses': False,
                    'can_view_reports': True,
                    'can_manage_system': False
                }
            else:
                return {}
                
        except Exception as e:
            logger.error(f"권한 조회 오류: {str(e)}")
            return {}

    def get_all_users(self):
        """모든 사용자 목록 조회 (직원 + 마스터)"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT 
                        employee_id as user_id,
                        name as user_name,
                        position,
                        department,
                        'employee' as user_type,
                        status,
                        created_date
                    FROM employees
                    WHERE status = 'active'
                    ORDER BY department, position, name
                '''
                
                df = pd.read_sql_query(query, conn)
                
                # 마스터 사용자 추가
                master_row = {
                    'user_id': 'master',
                    'user_name': 'System Master',
                    'position': 'Administrator',
                    'department': 'System',
                    'user_type': 'master',
                    'status': 'active',
                    'created_date': '2024-01-01'
                }
                
                master_df = pd.DataFrame([master_row])
                df = pd.concat([df, master_df], ignore_index=True)
                
                return df
                
        except Exception as e:
            logger.error(f"사용자 목록 조회 오류: {str(e)}")
            return pd.DataFrame()