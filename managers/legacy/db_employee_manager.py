"""
SQLite 기반 직원 관리자
기존 employee_manager.py의 SQLite 버전
"""
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
from .database_manager import DatabaseManager

class DBEmployeeManager:
    def __init__(self, db_path="erp_system.db"):
        """SQLite 기반 직원 관리자 초기화"""
        self.db_manager = DatabaseManager(db_path)
    
    def get_all_employees(self):
        """모든 직원 정보 반환"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM employees ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_employee_by_id(self, employee_id):
        """특정 직원 정보 반환"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM employees WHERE employee_id = ?", (employee_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def add_employee(self, employee_data):
        """새 직원 추가"""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute('''
                    INSERT INTO employees 
                    (employee_id, name, english_name, email, phone, position, department, 
                     hire_date, status, region, password)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    employee_data.get('employee_id'),
                    employee_data.get('name'),
                    employee_data.get('english_name', ''),
                    employee_data.get('email', ''),
                    employee_data.get('phone', ''),
                    employee_data.get('position', ''),
                    employee_data.get('department', ''),
                    employee_data.get('hire_date', ''),
                    employee_data.get('status', 'active'),
                    employee_data.get('region', ''),
                    employee_data.get('password', '')
                ))
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # 중복 ID
        except Exception as e:
            print(f"직원 추가 오류: {e}")
            return False
    
    def update_employee(self, employee_id, employee_data):
        """직원 정보 업데이트"""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute('''
                    UPDATE employees 
                    SET name=?, english_name=?, email=?, phone=?, position=?, department=?,
                        hire_date=?, status=?, region=?, updated_date=CURRENT_TIMESTAMP
                    WHERE employee_id=?
                ''', (
                    employee_data.get('name'),
                    employee_data.get('english_name', ''),
                    employee_data.get('email', ''),
                    employee_data.get('phone', ''),
                    employee_data.get('position', ''),
                    employee_data.get('department', ''),
                    employee_data.get('hire_date', ''),
                    employee_data.get('status', 'active'),
                    employee_data.get('region', ''),
                    employee_id
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"직원 업데이트 오류: {e}")
            return False
    
    def delete_employee(self, employee_id):
        """직원 삭제 (비활성화)"""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute('''
                    UPDATE employees 
                    SET status='inactive', updated_date=CURRENT_TIMESTAMP
                    WHERE employee_id=?
                ''', (employee_id,))
                conn.commit()
            return True
        except Exception as e:
            print(f"직원 삭제 오류: {e}")
            return False
    
    def authenticate_employee(self, employee_id, password):
        """직원 인증"""
        employee = self.get_employee_by_id(employee_id)
        if not employee:
            return False
        
        # 비밀번호 검증 (실제 구현에서는 해시 비교)
        return employee.get('password') == password
    
    def get_departments(self):
        """모든 부서 목록 반환"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT DISTINCT department FROM employees WHERE department IS NOT NULL AND department != ''")
            return [row[0] for row in cursor.fetchall()]
    
    def get_positions(self):
        """모든 직급 목록 반환"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT DISTINCT position FROM employees WHERE position IS NOT NULL AND position != ''")
            return [row[0] for row in cursor.fetchall()]
    
    def get_regions(self):
        """모든 지역 목록 반환"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT DISTINCT region FROM employees WHERE region IS NOT NULL AND region != ''")
            return [row[0] for row in cursor.fetchall()]
    
    def get_filtered_employees(self, status_filter=None, region_filter=None, search_term=None):
        """필터링된 직원 목록 반환"""
        query = "SELECT * FROM employees WHERE 1=1"
        params = []
        
        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)
        
        if region_filter:
            query += " AND region = ?"
            params.append(region_filter)
        
        if search_term:
            query += " AND (name LIKE ? OR employee_id LIKE ? OR english_name LIKE ?)"
            search_param = f"%{search_term}%"
            params.extend([search_param, search_param, search_param])
        
        query += " ORDER BY name"
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_employee_count(self):
        """총 직원 수 반환"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM employees WHERE status = 'active'")
            return cursor.fetchone()[0]
    
    def get_employee_statistics(self):
        """직원 통계 반환"""
        with self.db_manager.get_connection() as conn:
            stats = {}
            
            # 총 직원 수
            cursor = conn.execute("SELECT COUNT(*) FROM employees WHERE status = 'active'")
            stats['total_employees'] = cursor.fetchone()[0]
            
            # 부서별 통계
            cursor = conn.execute('''
                SELECT department, COUNT(*) 
                FROM employees 
                WHERE status = 'active' AND department IS NOT NULL AND department != ''
                GROUP BY department
            ''')
            stats['department_distribution'] = dict(cursor.fetchall())
            
            # 직급별 통계
            cursor = conn.execute('''
                SELECT position, COUNT(*) 
                FROM employees 
                WHERE status = 'active' AND position IS NOT NULL AND position != ''
                GROUP BY position
            ''')
            stats['position_distribution'] = dict(cursor.fetchall())
            
            # 지역별 통계
            cursor = conn.execute('''
                SELECT region, COUNT(*) 
                FROM employees 
                WHERE status = 'active' AND region IS NOT NULL AND region != ''
                GROUP BY region
            ''')
            stats['region_distribution'] = dict(cursor.fetchall())
            
            return stats
    
    def update_password(self, employee_id, new_password):
        """직원 비밀번호 업데이트"""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute('''
                    UPDATE employees 
                    SET password=?, updated_date=CURRENT_TIMESTAMP
                    WHERE employee_id=?
                ''', (new_password, employee_id))
                conn.commit()
            return True
        except Exception as e:
            print(f"비밀번호 업데이트 오류: {e}")
            return False
    
    def export_to_dataframe(self):
        """직원 데이터를 DataFrame으로 반환"""
        employees = self.get_all_employees()
        return pd.DataFrame(employees)