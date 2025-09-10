# -*- coding: utf-8 -*-
"""
SQLite 기반 직원 관리 시스템
"""

import sqlite3
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SQLiteEmployeeManager:
    def __init__(self, db_path="erp_system.db"):
        """SQLite 기반 직원 매니저 초기화"""
        self.db_path = db_path
    
    def get_connection(self):
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_all_employees_list(self):
        """모든 직원 정보를 리스트로 가져옵니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT employee_id, name, english_name, email, phone, 
                           position, department, hire_date, status, region, 
                           access_level, password, created_date, updated_date 
                    FROM employees
                    ORDER BY name
                ''')
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"직원 목록 조회 오류: {e}")
            return []
    
    def get_all_employees(self):
        """모든 직원 정보를 DataFrame으로 가져옵니다."""
        try:
            employees_list = self.get_all_employees_list()
            if employees_list:
                return pd.DataFrame(employees_list)
            else:
                return pd.DataFrame({
                    'employee_id': [],
                    'name': [],
                    'english_name': [],
                    'email': [],
                    'phone': [],
                    'position': [],
                    'department': [],
                    'hire_date': [],
                    'status': [],
                    'region': [],
                    'access_level': [],  # 누락된 access_level 추가
                    'password': [],
                    'created_date': [],
                    'updated_date': []
                })
        except Exception as e:
            logger.error(f"직원 DataFrame 조회 오류: {e}")
            return pd.DataFrame({
                'employee_id': [],
                'name': [],
                'english_name': [],
                'email': [],
                'phone': [],
                'position': [],
                'department': [],
                'hire_date': [],
                'status': [],
                'region': [],
                'access_level': [],  # 누락된 access_level 추가
                'password': [],
                'created_date': [],
                'updated_date': []
            })
    
    def generate_employee_id(self, hire_date):
        """입사일 기반으로 고유한 사번을 생성합니다. (YYMM + 순서번호 3자리)"""
        try:
            from datetime import datetime, date
            
            if isinstance(hire_date, str):
                hire_date = datetime.strptime(hire_date, '%Y-%m-%d').date()
            elif isinstance(hire_date, datetime):
                hire_date = hire_date.date()
            
            # 기존 직원들의 사번 확인
            try:
                with self.get_connection() as conn:
                    cursor = conn.execute('SELECT employee_id FROM employees')
                    existing_ids = [row['employee_id'] for row in cursor.fetchall()]
            except:
                existing_ids = []
            
            year_month = hire_date.strftime('%y%m')
            
            if existing_ids:
                # 해당 년월의 기존 사번들 확인
                existing_year_month_ids = [emp_id for emp_id in existing_ids if str(emp_id).startswith(year_month)]
                
                # 기존 번호들에서 마지막 3자리 숫자 추출하여 최대값 찾기
                max_num = 0
                for emp_id in existing_year_month_ids:
                    emp_id_str = str(emp_id)
                    if len(emp_id_str) >= 7:  # YYMM + 3자리 숫자
                        try:
                            num = int(emp_id_str[-3:])
                            max_num = max(max_num, num)
                        except ValueError:
                            continue
                
                # 다음 번호는 최대값 + 1
                next_num = max_num + 1
            else:
                # 첫 번째 직원인 경우
                next_num = 1
            
            # 새로운 사번 생성 (YYMM + 3자리 순서번호)
            new_id = f"{year_month}{next_num:03d}"
            logger.info(f"새 직원 ID 생성: {new_id}")
            return new_id
            
        except Exception as e:
            logger.error(f"사번 생성 중 오류: {e}")
            # 오류 발생 시 현재 시간 기준으로 생성
            return f"{datetime.now().strftime('%y%m')}001"
    
    def get_employee_by_id(self, employee_id):
        """특정 직원 정보를 가져옵니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM employees WHERE employee_id = ?
                ''', (str(employee_id),))
                
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"직원 조회 오류: {e}")
            return None
    
    def add_employee(self, employee_data):
        """새 직원을 추가합니다. (확장된 필드 지원)"""
        try:
            with self.get_connection() as conn:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # employee_id가 없으면 자동 생성
                employee_id = employee_data.get('employee_id')
                if not employee_id:
                    hire_date = employee_data.get('hire_date')
                    if hire_date:
                        employee_id = self.generate_employee_id(hire_date)
                        employee_data['employee_id'] = employee_id
                    else:
                        # hire_date가 없으면 현재 날짜 사용
                        from datetime import date
                        employee_id = self.generate_employee_id(date.today())
                        employee_data['employee_id'] = employee_id
                
                # 전화번호 포맷팅
                phone = employee_data.get('phone', employee_data.get('contact', ''))
                if phone:
                    phone = self.format_phone_number(phone)
                
                # 필드 매핑 처리
                nationality = employee_data.get('nationality', employee_data.get('region', '한국'))
                residence_country = employee_data.get('residence_country', employee_data.get('region', '한국'))
                work_status = employee_data.get('work_status', '재직')
                
                conn.execute('''
                    INSERT INTO employees (
                        employee_id, name, english_name, gender, nationality,
                        residence_country, city, address, email, phone,
                        position, department, hire_date, birth_date,
                        salary, salary_currency, driver_license, notes,
                        work_status, status, region, access_level, password,
                        created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    employee_id,
                    employee_data.get('name', ''),
                    employee_data.get('english_name', ''),
                    employee_data.get('gender', '남'),
                    nationality,
                    residence_country,
                    employee_data.get('city', ''),
                    employee_data.get('address', ''),
                    employee_data.get('email', ''),
                    phone,
                    employee_data.get('position', ''),
                    employee_data.get('department', ''),
                    employee_data.get('hire_date', ''),
                    employee_data.get('birth_date', ''),
                    employee_data.get('salary', 0),
                    employee_data.get('salary_currency', 'KRW'),
                    employee_data.get('driver_license', '없음'),
                    employee_data.get('notes', ''),
                    work_status,
                    'active' if work_status == '재직' else 'inactive',
                    nationality,  # region 필드는 nationality와 동일하게 설정
                    employee_data.get('access_level', 'user'),
                    employee_data.get('password', ''),
                    current_time,
                    current_time
                ))
                
                conn.commit()
                logger.info(f"새 직원 {employee_data.get('name', '')} (ID: {employee_id}) 추가 완료")
                return True, f"직원 {employee_data.get('name', '')} (ID: {employee_id})이 성공적으로 등록되었습니다."
        except Exception as e:
            logger.error(f"직원 추가 오류: {e}")
            return False, f"직원 추가 중 오류가 발생했습니다: {str(e)}"
    
    def update_employee(self, employee_id, employee_data):
        """직원 정보를 업데이트합니다. (확장된 필드 지원)"""
        try:
            with self.get_connection() as conn:
                # 기존 직원 확인
                cursor = conn.execute('SELECT * FROM employees WHERE employee_id = ?', (str(employee_id),))
                existing_employee = cursor.fetchone()
                if not existing_employee:
                    logger.error(f"직원 ID {employee_id}를 찾을 수 없습니다.")
                    return False, f"직원 ID {employee_id}를 찾을 수 없습니다."
                
                # 권한만 업데이트하는 경우 (부분 업데이트)
                if len(employee_data) == 1 and 'access_level' in employee_data:
                    conn.execute(
                        'UPDATE employees SET access_level = ?, updated_date = ? WHERE employee_id = ?',
                        (employee_data['access_level'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), str(employee_id))
                    )
                    conn.commit()
                    logger.info(f"직원 {employee_id} 권한이 성공적으로 업데이트되었습니다.")
                    return True, f"권한이 성공적으로 업데이트되었습니다."
                
                # 전체 데이터 업데이트 (기존 로직)
                # 전화번호 포맷팅
                phone = employee_data.get('phone', employee_data.get('contact', ''))
                if phone:
                    phone = self.format_phone_number(phone)
                
                # 필드 매핑 처리
                nationality = employee_data.get('nationality', employee_data.get('region', '한국'))
                residence_country = employee_data.get('residence_country', employee_data.get('region', '한국'))
                work_status = employee_data.get('work_status', '재직')
                if employee_data.get('status') == 'active':
                    work_status = '재직'
                elif employee_data.get('status') == 'inactive':
                    work_status = '퇴사'
                
                # 업데이트 실행 (확장된 필드 포함)
                conn.execute('''
                    UPDATE employees SET
                        name = ?, english_name = ?, gender = ?, nationality = ?,
                        residence_country = ?, city = ?, address = ?, email = ?, phone = ?,
                        position = ?, department = ?, hire_date = ?, birth_date = ?,
                        salary = ?, salary_currency = ?, driver_license = ?, notes = ?,
                        work_status = ?, status = ?, region = ?, access_level = ?, updated_date = ?
                    WHERE employee_id = ?
                ''', (
                    employee_data.get('name', ''),
                    employee_data.get('english_name', ''),
                    employee_data.get('gender', '남'),
                    nationality,
                    residence_country,
                    employee_data.get('city', ''),
                    employee_data.get('address', ''),
                    employee_data.get('email', ''),
                    phone,
                    employee_data.get('position', ''),
                    employee_data.get('department', ''),
                    employee_data.get('hire_date', ''),
                    employee_data.get('birth_date', ''),
                    employee_data.get('salary', 0),
                    employee_data.get('salary_currency', 'KRW'),
                    employee_data.get('driver_license', '없음'),
                    employee_data.get('notes', ''),
                    work_status,
                    'active' if work_status == '재직' else 'inactive',
                    nationality,  # region 필드는 nationality와 동일하게 설정
                    employee_data.get('access_level', 'employee'),  # 권한 레벨 업데이트 추가
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    str(employee_id)
                ))
                
                affected_rows = conn.total_changes
                conn.commit()
                
                if affected_rows > 0:
                    logger.info(f"직원 {employee_id} 정보가 성공적으로 업데이트되었습니다.")
                    return True, f"직원 {employee_data.get('name', employee_id)} 정보가 성공적으로 업데이트되었습니다."
                else:
                    logger.warning(f"직원 {employee_id} 업데이트에서 변경사항이 없습니다.")
                    return False, "업데이트할 변경사항이 없습니다."
                    
        except Exception as e:
            logger.error(f"직원 업데이트 오류: {e}")
            return False, f"직원 업데이트 중 오류가 발생했습니다: {str(e)}"
    
    def delete_employee(self, employee_id):
        """직원을 삭제합니다."""
        try:
            with self.get_connection() as conn:
                # 삭제 전 직원 존재 확인
                cursor = conn.execute('SELECT name FROM employees WHERE employee_id = ?', (str(employee_id),))
                employee = cursor.fetchone()
                if not employee:
                    logger.error(f"직원 ID {employee_id}를 찾을 수 없습니다.")
                    return False, f"직원 ID {employee_id}를 찾을 수 없습니다."
                
                employee_name = employee['name']
                
                # 직원 삭제
                conn.execute('DELETE FROM employees WHERE employee_id = ?', (str(employee_id),))
                affected_rows = conn.total_changes
                conn.commit()
                
                if affected_rows > 0:
                    logger.info(f"직원 {employee_name} (ID: {employee_id})가 성공적으로 삭제되었습니다.")
                    return True, f"직원 {employee_name}이 성공적으로 삭제되었습니다."
                else:
                    logger.warning(f"직원 {employee_id} 삭제에서 변경사항이 없습니다.")
                    return False, "삭제할 수 없습니다. 다시 시도해주세요."
                    
        except Exception as e:
            logger.error(f"직원 삭제 오류: {e}")
            return False, f"직원 삭제 중 오류가 발생했습니다: {str(e)}"
    
    def get_employee_name(self, employee_id):
        """직원 이름을 가져옵니다."""
        employee = self.get_employee_by_id(employee_id)
        return employee['name'] if employee else None
    
    def authenticate_user(self, employee_id, password):
        """사용자 인증을 처리합니다."""
        try:
            employee = self.get_employee_by_id(employee_id)
            if employee and employee.get('password') == password:
                return True, employee
            return False, None
        except Exception as e:
            logger.error(f"사용자 인증 오류: {e}")
            return False, None
    
    def get_regions(self):
        """모든 지역 목록을 가져옵니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT DISTINCT region FROM employees 
                    WHERE region IS NOT NULL AND region != ''
                    ORDER BY region
                ''')
                results = cursor.fetchall()
                return [row['region'] for row in results]
        except Exception as e:
            logger.error(f"지역 목록 조회 오류: {e}")
            return []
    
    def get_filtered_employees(self, status_filter=None, region_filter=None, search_term=None):
        """필터 조건에 따라 직원 목록을 DataFrame으로 가져옵니다."""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT employee_id, name, english_name, email, phone, 
                           position, department, hire_date, status, region, 
                           password, created_date, updated_date 
                    FROM employees WHERE 1=1
                '''
                params = []
                
                if status_filter and status_filter != "전체":
                    # 리스트 형태의 상태 필터 지원 (한국어/영어 호환)
                    if isinstance(status_filter, list):
                        placeholders = ",".join(["?" for _ in status_filter])
                        query += f" AND status IN ({placeholders})"
                        params.extend(status_filter)
                    else:
                        query += " AND status = ?"
                        params.append(status_filter)
                
                if region_filter and region_filter != "전체":
                    query += " AND region = ?"
                    params.append(region_filter)
                
                if search_term:
                    query += " AND (name LIKE ? OR employee_id LIKE ? OR english_name LIKE ?)"
                    search_param = f"%{search_term}%"
                    params.extend([search_param, search_param, search_param])
                
                query += " ORDER BY name"
                
                cursor = conn.execute(query, params)
                results = cursor.fetchall()
                employees_list = [dict(row) for row in results]
                
                if employees_list:
                    return pd.DataFrame(employees_list)
                else:
                    return pd.DataFrame({
                        'employee_id': [],
                        'name': [],
                        'english_name': [],
                        'email': [],
                        'phone': [],
                        'position': [],
                        'department': [],
                        'hire_date': [],
                        'status': [],
                        'region': [],
                        'password': [],
                        'created_date': [],
                        'updated_date': []
                    })
        except Exception as e:
            logger.error(f"필터링된 직원 목록 조회 오류: {e}")
            return pd.DataFrame({
                'employee_id': [],
                'name': [],
                'english_name': [],
                'email': [],
                'phone': [],
                'position': [],
                'department': [],
                'hire_date': [],
                'status': [],
                'region': [],
                'access_level': [],  # 누락된 access_level 추가
                'password': [],
                'created_date': [],
                'updated_date': []
            })
    
    def get_departments(self):
        """모든 부서 목록을 가져옵니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT DISTINCT department FROM employees 
                    WHERE department IS NOT NULL AND department != ''
                    ORDER BY department
                ''')
                results = cursor.fetchall()
                return [row['department'] for row in results]
        except Exception as e:
            logger.error(f"부서 목록 조회 오류: {e}")
            return []
    
    def get_positions(self):
        """모든 직급 목록을 가져옵니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT DISTINCT position FROM employees 
                    WHERE position IS NOT NULL AND position != ''
                    ORDER BY position
                ''')
                results = cursor.fetchall()
                return [row['position'] for row in results]
        except Exception as e:
            logger.error(f"직급 목록 조회 오류: {e}")
            return []
    
    def get_cities_by_country(self, country):
        """특정 국가의 도시 목록을 가져옵니다."""
        try:
            # 간단한 하드코딩된 도시 목록 (나중에 지리 데이터베이스로 확장 가능)
            cities_by_country = {
                "한국": ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"],
                "중국": ["베이징", "상하이", "광저우", "선전", "청두", "시안", "난징", "항저우", "우한", "충칭"],
                "태국": ["방콕", "치앙마이", "파타야", "푸켓", "핫야이", "콘깬", "우돈타니", "나콘라차시마"],
                "베트남": ["하노이", "호치민", "다낭", "하이퐁", "껀터", "빈", "후에", "나트랑", "달랏"],
                "인도네시아": ["자카르타", "수라바야", "반둥", "메단", "스마랑", "팔렘방", "마카사르", "족자카르타"],
                "말레이시아": ["쿠알라룸푸르", "조호르바루", "페낭", "이포", "쿠칭", "코타키나발루", "말라카", "쿠안탄"]
            }
            return cities_by_country.get(country, [])
        except Exception as e:
            logger.error(f"도시 목록 조회 오류: {e}")
            return []
    
    def format_phone_number(self, phone_number):
        """전화번호를 한국 표준 형식(XXX-XXXX-XXXX)으로 포맷팅"""
        if not phone_number:
            return ""
        
        # 숫자만 추출
        digits = ''.join(filter(str.isdigit, str(phone_number)))
        
        # 길이에 따른 포맷팅
        if len(digits) == 11:  # 휴대폰 번호 (010-XXXX-XXXX)
            return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
        elif len(digits) == 10:  # 지역번호 포함 일반전화 (0XX-XXX-XXXX)
            if digits.startswith('02'):  # 서울 (02-XXXX-XXXX)
                return f"{digits[:2]}-{digits[2:6]}-{digits[6:]}"
            else:  # 기타 지역 (0XX-XXX-XXXX)
                return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        elif len(digits) == 9:  # 서울 지역번호 없는 경우 (XXX-XXXX)
            return f"{digits[:3]}-{digits[3:]}"
        elif len(digits) == 8:  # 지역번호 없는 일반전화 (XXX-XXXX)
            return f"{digits[:4]}-{digits[4:]}"
        else:
            # 기본적으로 원본 반환
            return phone_number
