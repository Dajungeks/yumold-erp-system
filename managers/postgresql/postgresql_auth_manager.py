# -*- coding: utf-8 -*-
"""
PostgreSQL 인증 관리 매니저
"""

from .base_postgresql_manager import BasePostgreSQLManager
import uuid
try:
    import bcrypt
except ImportError:
    bcrypt = None
from datetime import datetime

class PostgreSQLAuthManager(BasePostgreSQLManager):
    """PostgreSQL 인증 관리 매니저"""
    
    def __init__(self):
        super().__init__()
        self.init_tables()
    
    def init_tables(self):
        """인증 관련 테이블 초기화"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 사용자 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(50) UNIQUE NOT NULL,
                        username VARCHAR(100) UNIQUE NOT NULL,
                        email VARCHAR(100) UNIQUE,
                        password_hash VARCHAR(255) NOT NULL,
                        access_level VARCHAR(20) DEFAULT 'user',
                        is_active BOOLEAN DEFAULT true,
                        last_login TIMESTAMP,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 세션 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id SERIAL PRIMARY KEY,
                        session_id VARCHAR(100) UNIQUE NOT NULL,
                        user_id VARCHAR(50) NOT NULL,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_date TIMESTAMP,
                        is_active BOOLEAN DEFAULT true,
                        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                    )
                """)
                
                self.log_info("인증 관련 테이블 초기화 완료")
                conn.commit()
                
        except Exception as e:
            self.log_error(f"인증 테이블 초기화 실패: {e}")
    
    def create_user(self, username, email, password, access_level='user'):
        """사용자 생성"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 사용자 ID 생성
                user_id = f"USR{str(uuid.uuid4())[:8].upper()}"
                
                # 비밀번호 해시화
                if bcrypt:
                    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                else:
                    # 간단한 해시 (실제 운영시에는 bcrypt 사용 권장)
                    import hashlib
                    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
                
                cursor.execute("""
                    INSERT INTO users (user_id, username, email, password_hash, access_level)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (user_id, username, email, password_hash, access_level))
                
                result = cursor.fetchone()
                conn.commit()
                
                return {
                    'success': True,
                    'user_id': user_id,
                    'id': result[0] if result else None
                }
                
        except Exception as e:
            self.log_error(f"사용자 생성 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def authenticate_user(self, username, password):
        """사용자 인증"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id, username, email, password_hash, access_level, is_active
                    FROM users 
                    WHERE username = %s AND is_active = true
                """, (username,))
                
                user = cursor.fetchone()
                if user:
                    # 비밀번호 확인
                    if bcrypt and len(user[3]) > 32:  # bcrypt hash
                        password_match = bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8'))
                    else:  # simple hash
                        import hashlib
                        password_match = hashlib.sha256(password.encode('utf-8')).hexdigest() == user[3]
                    
                    if password_match:
                        # 로그인 시간 업데이트
                        cursor.execute("""
                            UPDATE users SET last_login = CURRENT_TIMESTAMP 
                            WHERE user_id = %s
                        """, (user[0],))
                        conn.commit()
                        
                        return {
                            'success': True,
                            'user_id': user[0],
                            'username': user[1],
                            'email': user[2],
                            'access_level': user[4]
                        }
                    else:
                        return {'success': False, 'error': '잘못된 사용자명 또는 비밀번호'}
                else:
                    return {'success': False, 'error': '잘못된 사용자명 또는 비밀번호'}
                
        except Exception as e:
            self.log_error(f"사용자 인증 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def authenticate_employee(self, user_id, password):
        """직원 인증 - employees 테이블에서 직접 확인"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT employee_id, name, email, password, position, department, 
                           access_level, status, english_name, hire_date
                    FROM employees 
                    WHERE employee_id = %s AND status = 'active'
                """, (user_id,))
                
                employee = cursor.fetchone()
                if employee:
                    stored_password = employee[3]  # password 필드
                    
                    # 비밀번호가 설정되지 않은 경우
                    if not stored_password:
                        return False, {'error': '비밀번호가 설정되지 않았습니다. 관리자에게 문의하세요.'}
                    
                    # 비밀번호 확인
                    password_match = False
                    if bcrypt and stored_password.startswith('$2b$'):  # bcrypt hash
                        password_match = bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
                    else:  # simple hash 또는 일반 텍스트
                        import hashlib
                        password_match = hashlib.sha256(password.encode('utf-8')).hexdigest() == stored_password
                    
                    if password_match:
                        # 로그인 시간 업데이트
                        cursor.execute("""
                            UPDATE employees SET updated_date = CURRENT_TIMESTAMP 
                            WHERE employee_id = %s
                        """, (user_id,))
                        conn.commit()
                        
                        return True, {
                            'employee_id': employee[0],
                            'name': employee[1],
                            'email': employee[2],
                            'position': employee[4],
                            'department': employee[5],
                            'access_level': employee[6] or 'user',
                            'user_type': 'employee',
                            'english_name': employee[8],
                            'hire_date': str(employee[9]) if employee[9] else None
                        }
                    else:
                        return False, {'error': '잘못된 사번 또는 비밀번호입니다.'}
                else:
                    return False, {'error': '잘못된 사번 또는 비밀번호입니다.'}
                
        except Exception as e:
            self.log_error(f"직원 인증 실패: {e}")
            return False, {'error': f'인증 중 오류가 발생했습니다: {str(e)}'}
    
    def authenticate_master(self, password):
        """마스터 관리자 인증"""
        # 기본 마스터 비밀번호 체크 (실제 환경에서는 더 안전한 방법 사용)
        master_password = "master123"  # 실제로는 환경변수나 안전한 저장소에서 가져와야 함
        
        if password == master_password:
            return {
                'success': True,
                'user_id': 'MASTER',
                'username': 'Master Admin',
                'access_level': 'master'
            }
        else:
            return {'success': False, 'error': '잘못된 마스터 비밀번호'}
    
    def get_all_users(self):
        """모든 사용자 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id, username, email, access_level, is_active, 
                           last_login, created_date 
                    FROM users 
                    ORDER BY created_date DESC
                """)
                
                columns = ['user_id', 'username', 'email', 'access_level', 'is_active', 'last_login', 'created_date']
                users = []
                
                for row in cursor.fetchall():
                    user = dict(zip(columns, row))
                    users.append(user)
                
                return users
                
        except Exception as e:
            self.log_error(f"사용자 조회 실패: {e}")
            return []
    
    def reset_user_password(self, user_id, new_password):
        """사용자 비밀번호 재설정"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 비밀번호 해시화
                if bcrypt:
                    password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                else:
                    # 간단한 해시 (실제 운영시에는 bcrypt 사용 권장)
                    import hashlib
                    password_hash = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
                
                # users 테이블에서 직접 비밀번호 업데이트
                cursor.execute("""
                    UPDATE users 
                    SET password_hash = %s, updated_date = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, (password_hash, user_id))
                
                # employees 테이블에서도 비밀번호 업데이트 (존재하는 경우)
                cursor.execute("""
                    UPDATE employees 
                    SET password = %s, updated_date = CURRENT_TIMESTAMP
                    WHERE employee_id = %s
                """, (password_hash, user_id))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    return True, "비밀번호가 성공적으로 재설정되었습니다."
                else:
                    return False, "해당 사용자를 찾을 수 없습니다."
                    
        except Exception as e:
            self.log_error(f"비밀번호 재설정 실패: {e}")
            return False, f"비밀번호 재설정 중 오류가 발생했습니다: {str(e)}"