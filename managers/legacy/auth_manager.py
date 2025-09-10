import pandas as pd
import os
import hashlib
from datetime import datetime

class AuthManager:
    def __init__(self):
        self.users_file = 'data/users.csv'
        self.permissions_file = 'data/user_permissions.csv'
        self.master_password = os.getenv('MASTER_PASSWORD', 'ymv2024')
        self.ensure_data_files()
    
    def ensure_data_files(self):
        """필요한 데이터 파일들이 존재하는지 확인하고 없으면 생성합니다."""
        os.makedirs('data', exist_ok=True)
        
        # 사용자 파일 생성
        if not os.path.exists(self.users_file):
            users_df = pd.DataFrame(columns=[
                'user_id', 'password_hash', 'user_type', 'created_date', 'last_login'
            ])
            users_df.to_csv(self.users_file, index=False, encoding='utf-8-sig')
        
        # 권한 파일 생성
        if not os.path.exists(self.permissions_file):
            permissions_df = pd.DataFrame(columns=[
                'user_id', 'can_access_employee_management', 'can_access_product_management',
                'can_access_customer_management', 'can_access_sales_management',
                'can_access_supplier_management', 'can_access_exchange_rate_management',
                'can_delete_data', 'can_access_personal_status', 'updated_date'
            ])
            permissions_df.to_csv(self.permissions_file, index=False, encoding='utf-8-sig')
    
    def hash_password(self, password):
        """비밀번호를 해시화합니다."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def add_user(self, user_id, password="1111", user_type="employee"):
        """새 사용자를 추가합니다."""
        try:
            users_df = pd.read_csv(self.users_file, encoding='utf-8-sig')
            
            # 이미 존재하는 사용자인지 확인
            if user_id in users_df['user_id'].values:
                return True  # 이미 존재하면 성공으로 처리
            
            # 새 사용자 추가
            new_user = {
                'user_id': user_id,
                'password_hash': self.hash_password(password),
                'user_type': user_type,
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_login': None
            }
            
            users_df = pd.concat([users_df, pd.DataFrame([new_user])], ignore_index=True)
            users_df.to_csv(self.users_file, index=False, encoding='utf-8-sig')
            
            # 기본 권한 설정
            self.set_default_permissions(user_id)
            
            return True
        except Exception as e:
            print(f"사용자 추가 중 오류: {e}")
            return False
    
    def set_default_permissions(self, user_id):
        """기본 권한을 설정합니다."""
        try:
            permissions_df = pd.read_csv(self.permissions_file, encoding='utf-8-sig')
            
            # 이미 권한이 설정된 경우 스킵
            if user_id in permissions_df['user_id'].values:
                return
            
            # 기본 권한 설정 (직원은 개인 상태 관리와 환율 관리 접근 가능)
            default_permissions = {
                'user_id': user_id,
                'can_access_employee_management': False,
                'can_access_product_management': False,
                'can_access_customer_management': False,
                'can_access_sales_management': False,
                'can_access_supplier_management': False,
                'can_access_exchange_rate_management': True,
                'can_delete_data': False,
                'can_access_personal_status': True,
                'updated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            permissions_df = pd.concat([permissions_df, pd.DataFrame([default_permissions])], ignore_index=True)
            permissions_df.to_csv(self.permissions_file, index=False, encoding='utf-8-sig')
            
        except Exception as e:
            print(f"기본 권한 설정 중 오류: {e}")
    
    def authenticate_employee(self, user_id, password):
        """직원 로그인을 인증합니다."""
        try:
            # 기본 비밀번호 "1111"로 간단한 인증
            if password != "1111":
                return False
                
            # 직원 데이터에서 확인
            import pandas as pd
            df = pd.read_csv('data/employees.csv', encoding='utf-8-sig')
            df['employee_id'] = df['employee_id'].astype(str)
            user_id = str(user_id)
            
            employee = df[df['employee_id'] == user_id]
            if len(employee) > 0:
                emp_data = employee.iloc[0]
                return {
                    'user_id': user_id,
                    'access_level': emp_data.get('access_level', 'employee'),
                    'name': emp_data.get('name', ''),
                    'position': emp_data.get('position', ''),
                    'department': emp_data.get('department', '')
                }
            
            return False
        except Exception as e:
            print(f"직원 인증 중 오류: {e}")
            return False
    
    def authenticate_user(self, user_id, password):
        """사용자 인증을 수행합니다 (authenticate_employee와 동일)."""
        return self.authenticate_employee(user_id, password)
    
    def authenticate_master(self, password):
        """마스터 로그인을 인증합니다."""
        return password == self.master_password
    
    def update_last_login(self, user_id):
        """마지막 로그인 시간을 업데이트합니다."""
        try:
            users_df = pd.read_csv(self.users_file, encoding='utf-8-sig')
            users_df.loc[users_df['user_id'] == user_id, 'last_login'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            users_df.to_csv(self.users_file, index=False, encoding='utf-8-sig')
        except Exception as e:
            print(f"로그인 시간 업데이트 중 오류: {e}")
    
    def get_user_permissions(self, user_id):
        """사용자 권한을 가져옵니다."""
        try:
            if user_id == "master":
                # 마스터는 모든 권한
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
                    'can_access_cash_flow_management': True,
                    'can_access_invoice_management': True,
                    'can_access_sales_product_management': True,
                    'can_access_exchange_rate_management': True,
                    'can_access_pdf_design_management': True,
                    'can_access_personal_status': True,
                    'can_access_vacation_management': True,
                    'can_delete_data': True
                }
            
            # user_id를 정수형으로 변환
            try:
                user_id_int = int(user_id)
            except (ValueError, TypeError):
                return self._get_default_permissions()
            
            permissions_df = pd.read_csv(self.permissions_file, encoding='utf-8-sig')
            user_permissions = permissions_df[permissions_df['user_id'] == user_id_int]
            
            if len(user_permissions) == 0:
                # 권한이 없으면 기본 권한 설정
                self.set_default_permissions(user_id_int)
                return self._get_default_permissions()
            
            permissions = user_permissions.iloc[0]
            
            # pandas Series에서 안전하게 값 가져오기
            def safe_get_permission(key, default=False):
                try:
                    if key in permissions.index:
                        raw_value = permissions[key]
                        # permission_level은 숫자로 반환
                        if key == 'permission_level':
                            return int(raw_value) if not pd.isna(raw_value) else default
                        # 다른 권한은 boolean으로 변환
                        return self._convert_to_bool(raw_value)
                    return default
                except Exception as e:
                    return default
            
            return {
                'can_access_dashboard': safe_get_permission('can_access_dashboard', True),
                'can_access_employee_management': safe_get_permission('can_access_employee_management', False),
                'can_access_personal_status': safe_get_permission('can_access_personal_status', True),
                'can_access_customer_management': safe_get_permission('can_access_customer_management', False),
                'can_access_master_product_management': safe_get_permission('can_access_master_product_management', False),
                'can_access_supplier_management': safe_get_permission('can_access_supplier_management', False),
                'can_access_sales_product_management': safe_get_permission('can_access_sales_product_management', False),
                'can_access_quotation_management': safe_get_permission('can_access_quotation_management', False),
                'can_access_supply_product_management': safe_get_permission('can_access_supply_product_management', False),
                'can_access_exchange_rate_management': safe_get_permission('can_access_exchange_rate_management', True),
                'can_access_business_process_management': safe_get_permission('can_access_business_process_management', False),
                'can_access_shipping_management': safe_get_permission('can_access_shipping_management', False),
                'can_access_approval_management': safe_get_permission('can_access_approval_management', False),
                'can_access_cash_flow_management': safe_get_permission('can_access_cash_flow_management', False),
                'can_access_pdf_design_management': safe_get_permission('can_access_pdf_design_management', False),
                'can_access_system_guide': safe_get_permission('can_access_system_guide', True),
                'can_delete_data': safe_get_permission('can_delete_data', False),
                'permission_level': safe_get_permission('permission_level', 1)
            }
        except Exception as e:
            print(f"권한 조회 중 오류: {e}")
            return {}
    
    def _get_default_permissions(self):
        """기본 권한을 반환합니다."""
        return {
            'can_access_dashboard': True,
            'can_access_employee_management': False,
            'can_access_personal_status': True,
            'can_access_customer_management': False,
            'can_access_master_product_management': False,
            'can_access_supplier_management': False,
            'can_access_sales_product_management': False,
            'can_access_quotation_management': False,
            'can_access_supply_product_management': False,
            'can_access_exchange_rate_management': True,
            'can_access_business_process_management': False,
            'can_access_shipping_management': False,
            'can_access_approval_management': False,
            'can_access_cash_flow_management': False,
            'can_access_pdf_design_management': False,
            'can_access_system_guide': True,
            'can_delete_data': False,
            'permission_level': 1
        }
    
    def _convert_to_bool(self, value):
        """값을 boolean으로 변환합니다."""
        import numpy as np
        
        if pd.isna(value):
            return False
        
        # numpy boolean 타입 처리
        if isinstance(value, (bool, np.bool_)):
            return bool(value)
        
        # numpy 숫자 타입 처리
        if isinstance(value, (int, float, np.integer, np.floating)):
            return bool(value)
        
        # 문자열 타입 처리
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'y']
        
        return False
    
    def update_user_permissions(self, user_id, permissions):
        """사용자 권한을 업데이트합니다."""
        try:
            permissions_df = pd.read_csv(self.permissions_file, encoding='utf-8-sig')
            
            # 기존 권한 업데이트 또는 새로 추가
            if user_id in permissions_df['user_id'].values:
                for key, value in permissions.items():
                    permissions_df.loc[permissions_df['user_id'] == user_id, key] = value
                permissions_df.loc[permissions_df['user_id'] == user_id, 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            else:
                new_permissions = permissions.copy()
                new_permissions['user_id'] = user_id
                new_permissions['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                permissions_df = pd.concat([permissions_df, pd.DataFrame([new_permissions])], ignore_index=True)
            
            permissions_df.to_csv(self.permissions_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"권한 업데이트 중 오류: {e}")
            return False
    
    def get_all_users(self):
        """모든 사용자 목록을 가져옵니다."""
        try:
            users_df = pd.read_csv(self.users_file, encoding='utf-8-sig')
            return users_df
        except Exception as e:
            print(f"사용자 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def change_password(self, user_id, current_password, new_password):
        """사용자 비밀번호를 변경합니다. (현재 비밀번호 확인 후)"""
        try:
            # 현재 비밀번호 먼저 확인
            if not self.authenticate_employee(user_id, current_password):
                return False, "현재 비밀번호가 올바르지 않습니다."
            
            users_df = pd.read_csv(self.users_file, encoding='utf-8-sig')
            users_df.loc[users_df['user_id'] == user_id, 'password_hash'] = self.hash_password(new_password)
            users_df.to_csv(self.users_file, index=False, encoding='utf-8-sig')
            return True, "비밀번호가 성공적으로 변경되었습니다."
        except Exception as e:
            print(f"비밀번호 변경 중 오류: {e}")
            return False, f"비밀번호 변경 중 오류가 발생했습니다: {str(e)}"
    
    def reset_user_password(self, user_id, new_password):
        """관리자가 사용자 비밀번호를 강제로 재설정합니다. (현재 비밀번호 확인 없음)"""
        try:
            users_df = pd.read_csv(self.users_file, encoding='utf-8-sig')
            
            # user_id를 정수형으로 변환
            try:
                user_id_int = int(user_id)
            except (ValueError, TypeError):
                return False, "올바르지 않은 사용자 ID입니다."
            
            # 사용자가 존재하는지 확인
            user_exists = user_id_int in users_df['user_id'].values
            
            if user_exists:
                # 기존 사용자의 비밀번호만 업데이트
                users_df.loc[users_df['user_id'] == user_id_int, 'password_hash'] = self.hash_password(new_password)
                users_df.to_csv(self.users_file, index=False, encoding='utf-8-sig')
                return True, "비밀번호가 성공적으로 재설정되었습니다."
            else:
                # 새 사용자 생성
                new_user = {
                    'user_id': user_id_int,
                    'password_hash': self.hash_password(new_password),
                    'user_type': 'employee',
                    'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'last_login': None
                }
                
                users_df = pd.concat([users_df, pd.DataFrame([new_user])], ignore_index=True)
                users_df.to_csv(self.users_file, index=False, encoding='utf-8-sig')
                
                # 기본 권한 설정
                self.set_default_permissions(user_id_int)
                
                return True, "새 계정이 생성되고 비밀번호가 설정되었습니다."
                
        except Exception as e:
            print(f"비밀번호 재설정 중 오류: {e}")
            return False, f"비밀번호 재설정 중 오류가 발생했습니다: {str(e)}"
