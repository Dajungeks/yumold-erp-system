# -*- coding: utf-8 -*-
"""
PostgreSQL 인증 관리 매니저
"""

from .base_postgresql_manager import BasePostgreSQLManager
import uuid
from datetime import datetime
import pandas as pd
import logging

logger = logging.getLogger(__name__)

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
        """사용자 생성 (Enterprise급 bcrypt 보안)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 사용자 ID 생성
                user_id = f"USR{str(uuid.uuid4())[:8].upper()}"
                
                # Enterprise급 bcrypt 해시화 (BasePostgreSQLManager 사용)
                password_hash = self.hash_password(password)
                
                cursor.execute("""
                    INSERT INTO users (user_id, username, email, password_hash, access_level)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (user_id, username, email, password_hash, access_level))
                
                result = cursor.fetchone()
                conn.commit()
                
                logger.info(f"✅ 사용자 {username} ({user_id}) Enterprise급 bcrypt로 생성됨")
                
                return {
                    'success': True,
                    'user_id': user_id,
                    'id': result[0] if result else None
                }
                
        except Exception as e:
            logger.error(f"사용자 생성 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def authenticate_user(self, username, password):
        """사용자 인증 (하위 호환성 + 자동 재해싱)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id, username, email, password_hash, access_level, is_active
                    FROM users 
                    WHERE username = %s AND is_active = true
                """, (username,))
                
                user = cursor.fetchone()
                if not user:
                    # 보안상 동일한 응답 반환 (사용자 존재 여부 숨김)
                    return {'success': False, 'error': '잘못된 사용자명 또는 비밀번호'}
                
                user_id, username_db, email, stored_password, access_level, is_active = user
                
                # BasePostgreSQLManager의 향상된 verify_password 사용 (하위 호환성 지원)
                password_match = self.verify_password(password, stored_password)
                
                if password_match:
                    # 🔄 자동 재해싱 체크 및 수행
                    should_rehash = self.should_rehash_password(stored_password)
                    if should_rehash:
                        try:
                            new_hash = self.hash_password(password)
                            cursor.execute("""
                                UPDATE users 
                                SET password_hash = %s, updated_date = CURRENT_TIMESTAMP
                                WHERE user_id = %s
                            """, (new_hash, user_id))
                            logger.info(f"🔄 사용자 {username_db} ({user_id}) 패스워드 bcrypt로 자동 재해싱됨")
                        except Exception as e:
                            logger.warning(f"자동 재해싱 실패 (로그인은 성공): {e}")
                    
                    # 로그인 시간 업데이트
                    cursor.execute("""
                        UPDATE users SET last_login = CURRENT_TIMESTAMP 
                        WHERE user_id = %s
                    """, (user_id,))
                    conn.commit()
                    
                    logger.info(f"✅ 사용자 {username_db} ({user_id}) 인증 성공")
                    
                    return {
                        'success': True,
                        'user_id': user_id,
                        'username': username_db,
                        'email': email,
                        'access_level': access_level
                    }
                else:
                    logger.warning(f"사용자 {username} 인증 실패 - 잘못된 패스워드")
                    return {'success': False, 'error': '잘못된 사용자명 또는 비밀번호'}
                
        except Exception as e:
            logger.error(f"사용자 인증 실패: {e}")
            return {'success': False, 'error': '인증 중 오류가 발생했습니다.'}
    
    def authenticate_employee(self, user_id, password):
        """직원 인증 - employees 테이블에서 직접 확인 (자동 재해싱 지원)"""
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
                if not employee:
                    # 보안상 동일한 응답 반환 (사용자 존재 여부 숨김)
                    return False, {'error': '잘못된 사번 또는 비밀번호입니다.'}
                
                stored_password = employee[3]  # password 필드
                
                # 비밀번호가 설정되지 않은 경우
                if not stored_password:
                    return False, {'error': '비밀번호가 설정되지 않았습니다. 관리자에게 문의하세요.'}
                
                # BasePostgreSQLManager의 향상된 verify_password 사용 (하위 호환성 지원)
                password_match = self.verify_password(password, stored_password)
                
                if password_match:
                    # 🔄 자동 재해싱 체크 및 수행
                    should_rehash = self.should_rehash_password(stored_password)
                    if should_rehash:
                        try:
                            new_hash = self.hash_password(password)
                            cursor.execute("""
                                UPDATE employees 
                                SET password = %s, updated_date = CURRENT_TIMESTAMP
                                WHERE employee_id = %s
                            """, (new_hash, user_id))
                            logger.info(f"🔄 직원 {user_id} ({employee[1]}) 패스워드 bcrypt로 자동 재해싱됨")
                        except Exception as e:
                            logger.warning(f"자동 재해싱 실패 (로그인은 성공): {e}")
                    
                    # 로그인 시간 업데이트
                    cursor.execute("""
                        UPDATE employees SET updated_date = CURRENT_TIMESTAMP 
                        WHERE employee_id = %s
                    """, (user_id,))
                    conn.commit()
                    
                    logger.info(f"✅ 직원 {user_id} ({employee[1]}) 인증 성공")
                    
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
                    logger.warning(f"직원 {user_id} 인증 실패 - 잘못된 패스워드")
                    return False, {'error': '잘못된 사번 또는 비밀번호입니다.'}
                
        except Exception as e:
            logger.error(f"직원 인증 실패: {e}")
            return False, {'error': '인증 중 오류가 발생했습니다.'}
    
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
    
    def get_all_users(self) -> 'pd.DataFrame':
        """모든 사용자를 DataFrame으로 조회"""
        try:
            import pandas as pd
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
                
                if users:
                    return pd.DataFrame(users)
                else:
                    return pd.DataFrame()
                
        except Exception as e:
            self.log_error(f"사용자 조회 실패: {e}")
            import pandas as pd
            return pd.DataFrame()
    
    def reset_user_password(self, user_id, new_password):
        """사용자 비밀번호 재설정 (Enterprise급 bcrypt)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Enterprise급 bcrypt 해시화 (BasePostgreSQLManager 사용)
                password_hash = self.hash_password(new_password)
                
                # users 테이블에서 직접 비밀번호 업데이트
                cursor.execute("""
                    UPDATE users 
                    SET password_hash = %s, updated_date = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, (password_hash, user_id))
                users_affected = cursor.rowcount
                
                # employees 테이블에서도 비밀번호 업데이트 (존재하는 경우)
                cursor.execute("""
                    UPDATE employees 
                    SET password = %s, updated_date = CURRENT_TIMESTAMP
                    WHERE employee_id = %s
                """, (password_hash, user_id))
                employees_affected = cursor.rowcount
                
                conn.commit()
                
                total_affected = users_affected + employees_affected
                if total_affected > 0:
                    logger.info(f"🔄 사용자 {user_id} 패스워드 Enterprise급 bcrypt로 재설정됨 (users: {users_affected}, employees: {employees_affected})")
                    return True, "비밀번호가 성공적으로 재설정되었습니다."
                else:
                    logger.warning(f"사용자 {user_id} 재설정 실패 - 해당 사용자 없음")
                    return False, "해당 사용자를 찾을 수 없습니다."
                    
        except Exception as e:
            logger.error(f"비밀번호 재설정 실패: {e}")
            return False, f"비밀번호 재설정 중 오류가 발생했습니다: {str(e)}"
    
    def get_user_permissions(self, user_id, user_type=None):
        """사용자 권한을 가져옵니다 (PostgreSQL 버전)"""
        try:
            # 마스터 사용자는 모든 권한
            if user_id == "MASTER" or user_type == "master" or user_id == "master":
                return {
                    'can_access_employee_management': True,
                    'can_access_customer_management': True,
                    'can_access_product_management': True,
                    'can_access_quotation_management': True,
                    'can_access_supplier_management': True,
                    'can_access_business_process_management': True,
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
            
            # 일반 직원 권한 조회 (employees 테이블에서)
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT access_level, position, department 
                    FROM employees 
                    WHERE employee_id = %s AND status = 'active'
                """, (user_id,))
                
                employee = cursor.fetchone()
                if employee:
                    access_level, position, department = employee
                    
                    # 기본 권한 (모든 직원)
                    permissions = {
                        'can_access_employee_management': False,
                        'can_access_customer_management': False,
                        'can_access_product_management': False,
                        'can_access_quotation_management': False,
                        'can_access_supplier_management': False,
                        'can_access_business_process_management': False,
                        'can_access_purchase_order_management': False,
                        'can_access_inventory_management': False,
                        'can_access_shipping_management': False,
                        'can_access_approval_management': False,
                        'can_access_monthly_sales_management': False,
                        'can_access_cash_flow_management': False,
                        'can_access_invoice_management': False,
                        'can_access_sales_product_management': False,
                        'can_access_order_management': False,
                        'can_access_exchange_rate_management': False,
                        'can_access_personal_status': True,  # 개인 상태는 모든 직원 접근 가능
                        'can_access_vacation_management': True,  # 휴가 관리는 모든 직원 접근 가능
                        'can_delete_data': False
                    }
                    
                    # 접근 권한별 설정
                    if access_level in ['admin', 'manager']:
                        # 관리자/매니저 권한
                        permissions.update({
                            'can_access_employee_management': True,
                            'can_access_customer_management': True,
                            'can_access_product_management': True,
                            'can_access_quotation_management': True,
                            'can_access_supplier_management': True,
                            'can_access_business_process_management': True,
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
                            'can_delete_data': True
                        })
                    elif access_level == 'senior':
                        # 시니어 직원 권한
                        permissions.update({
                            'can_access_customer_management': True,
                            'can_access_product_management': True,
                            'can_access_quotation_management': True,
                            'can_access_order_management': True,
                            'can_access_inventory_management': True,
                            'can_access_shipping_management': True,
                            'can_access_sales_product_management': True,
                            'can_access_monthly_sales_management': True
                        })
                    elif access_level == 'junior':
                        # 주니어 직원 권한 (기본 권한 + 일부 조회)
                        permissions.update({
                            'can_access_product_management': True,
                            'can_access_order_management': True,
                            'can_access_inventory_management': True
                        })
                    
                    logger.info(f"사용자 {user_id} 권한 조회 성공 (access_level: {access_level})")
                    return permissions
                else:
                    logger.warning(f"사용자 {user_id} 정보 없음 - 기본 권한 반환")
                    # 사용자 정보가 없으면 최소 권한만 반환
                    return {
                        'can_access_employee_management': False,
                        'can_access_customer_management': False,
                        'can_access_product_management': False,
                        'can_access_quotation_management': False,
                        'can_access_supplier_management': False,
                        'can_access_business_process_management': False,
                        'can_access_purchase_order_management': False,
                        'can_access_inventory_management': False,
                        'can_access_shipping_management': False,
                        'can_access_approval_management': False,
                        'can_access_monthly_sales_management': False,
                        'can_access_cash_flow_management': False,
                        'can_access_invoice_management': False,
                        'can_access_sales_product_management': False,
                        'can_access_order_management': False,
                        'can_access_exchange_rate_management': False,
                        'can_access_personal_status': True,
                        'can_access_vacation_management': True,
                        'can_delete_data': False
                    }
                    
        except Exception as e:
            logger.error(f"사용자 권한 조회 실패: {e}")
            # 오류 시 최소 권한 반환
            return {
                'can_access_employee_management': False,
                'can_access_customer_management': False,
                'can_access_product_management': False,
                'can_access_quotation_management': False,
                'can_access_supplier_management': False,
                'can_access_business_process_management': False,
                'can_access_purchase_order_management': False,
                'can_access_inventory_management': False,
                'can_access_shipping_management': False,
                'can_access_approval_management': False,
                'can_access_monthly_sales_management': False,
                'can_access_cash_flow_management': False,
                'can_access_invoice_management': False,
                'can_access_sales_product_management': False,
                'can_access_order_management': False,
                'can_access_exchange_rate_management': False,
                'can_access_personal_status': True,
                'can_access_vacation_management': True,
                'can_delete_data': False
            }
