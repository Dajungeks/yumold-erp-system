# -*- coding: utf-8 -*-
"""
PostgreSQL 기반 직원 관리 시스템
"""

import pandas as pd
from datetime import datetime
import logging
from .base_postgresql_manager import BasePostgreSQLManager

logger = logging.getLogger(__name__)

class PostgreSQLEmployeeManager(BasePostgreSQLManager):
    def __init__(self):
        """PostgreSQL 기반 직원 매니저 초기화"""
        super().__init__()
        self.table_name = "employees"
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """employees 테이블 존재 확인 및 생성"""
        create_sql = """
            CREATE TABLE IF NOT EXISTS employees (
                id SERIAL PRIMARY KEY,
                employee_id VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                english_name VARCHAR(100),
                email VARCHAR(255),
                phone VARCHAR(50),
                position VARCHAR(100),
                department VARCHAR(100),
                hire_date DATE,
                status VARCHAR(20) DEFAULT 'active',
                region VARCHAR(100),
                password VARCHAR(255),
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                gender VARCHAR(10) DEFAULT '남',
                nationality VARCHAR(50) DEFAULT '한국',
                residence_country VARCHAR(50) DEFAULT '한국',
                city VARCHAR(100),
                address TEXT,
                birth_date DATE,
                salary INTEGER DEFAULT 0,
                salary_currency VARCHAR(10) DEFAULT 'KRW',
                driver_license VARCHAR(50) DEFAULT '없음',
                notes TEXT,
                work_status VARCHAR(20) DEFAULT '재직',
                access_level VARCHAR(20) DEFAULT 'user'
            );
        """
        self.create_table_if_not_exists(self.table_name, create_sql)
    
    def get_all_employees_list(self, limit=100):
        """모든 직원 정보를 리스트로 가져옵니다."""
        query = """
            SELECT employee_id, name, english_name, email, phone, 
                   position, department, hire_date, status, region, 
                   access_level, password, created_date, updated_date,
                   gender, nationality, residence_country, city, address,
                   birth_date, salary, salary_currency, driver_license,
                   notes, work_status
            FROM employees
            ORDER BY name
            LIMIT %s
        """
        try:
            return self.execute_query(query, (limit,), fetch_all=True)
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
                    'access_level': [],
                    'password': [],
                    'created_date': [],
                    'updated_date': [],
                    'gender': [],
                    'nationality': [],
                    'residence_country': [],
                    'city': [],
                    'address': [],
                    'birth_date': [],
                    'salary': [],
                    'salary_currency': [],
                    'driver_license': [],
                    'notes': [],
                    'work_status': []
                })
        except Exception as e:
            logger.error(f"직원 DataFrame 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_employee_by_id(self, employee_id):
        """특정 직원 정보를 가져옵니다."""
        query = "SELECT * FROM employees WHERE employee_id = %s"
        try:
            return self.execute_query(query, (employee_id,), fetch_one=True)
        except Exception as e:
            logger.error(f"직원 조회 오류: {e}")
            return None
    
    def add_employee(self, employee_data):
        """새 직원을 추가합니다."""
        try:
            current_time = self.format_timestamp()
            
            # 직원 ID 자동 생성 (기존 SQLite 방식과 동일)
            employee_id = self._generate_employee_id()
            
            query = """
                INSERT INTO employees (
                    employee_id, name, english_name, email, phone,
                    position, department, hire_date, status, region,
                    password, gender, nationality, residence_country,
                    city, address, birth_date, salary, salary_currency,
                    driver_license, notes, work_status, access_level,
                    created_date, updated_date
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                ) RETURNING id
            """
            
            params = (
                employee_id,
                employee_data['name'],
                employee_data.get('english_name'),
                employee_data.get('email'),
                employee_data.get('phone'),
                employee_data.get('position'),
                employee_data.get('department'),
                employee_data.get('hire_date'),
                employee_data.get('status', 'active'),
                employee_data.get('region'),
                employee_data.get('password'),
                employee_data.get('gender', 'Male'),
                employee_data.get('nationality', 'Korea'),
                employee_data.get('residence_country', 'Korea'),
                employee_data.get('city'),
                employee_data.get('address'),
                employee_data.get('birth_date'),
                employee_data.get('salary', 0),
                employee_data.get('salary_currency', 'KRW'),
                employee_data.get('driver_license', 'None'),
                employee_data.get('notes'),
                employee_data.get('work_status', 'Active'),
                employee_data.get('access_level', 'user'),
                current_time,
                current_time
            )
            
            result = self.execute_query(query, params, fetch_one=True)
            if result:
                return True  # employee_page.py에서 boolean 값을 기대
            else:
                return False
            
        except Exception as e:
            logger.error(f"직원 추가 오류: {e}")
            return False  # employee_page.py에서 boolean 값을 기대
    
    def _generate_employee_id(self):
        """직원 ID 자동 생성"""
        query = """
            SELECT employee_id FROM employees 
            WHERE employee_id LIKE %s 
            ORDER BY employee_id DESC LIMIT 1
        """
        try:
            result = self.execute_query(query, params=('EMP%',), fetch_one=True)
            if result:
                # dict 형태로 반환되는 경우 처리
                if isinstance(result, dict):
                    last_id = result.get('employee_id', '')
                # tuple 형태로 반환되는 경우 처리
                elif isinstance(result, (tuple, list)) and len(result) > 0:
                    last_id = result[0]
                else:
                    last_id = ''
                
                if last_id and last_id.startswith('EMP'):
                    number = int(last_id[3:]) + 1
                    return f"EMP{number:03d}"
                else:
                    return "EMP001"
            else:
                return "EMP001"
        except Exception as e:
            logger.error(f"직원 ID 생성 오류: {e}")
            return "EMP001"
    
    def update_employee(self, employee_id, employee_data):
        """직원 정보를 업데이트합니다."""
        try:
            current_time = self.format_timestamp()
            
            # 동적으로 UPDATE 쿼리 생성
            set_clauses = []
            params = []
            
            for field, value in employee_data.items():
                if field != 'employee_id':  # employee_id는 업데이트하지 않음
                    set_clauses.append(f"{field} = %s")
                    params.append(value)
            
            # updated_date가 이미 포함되어 있지 않으면 추가
            if 'updated_date' not in employee_data:
                set_clauses.append("updated_date = %s")
                params.append(current_time)
            params.append(employee_id)
            
            query = f"""
                UPDATE employees 
                SET {', '.join(set_clauses)}
                WHERE employee_id = %s
            """
            
            rows_affected = self.execute_query(query, params)
            return {'success': True, 'rows_affected': rows_affected}
            
        except Exception as e:
            logger.error(f"직원 업데이트 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_employee(self, employee_id):
        """직원을 삭제합니다."""
        try:
            query = "DELETE FROM employees WHERE employee_id = %s"
            rows_affected = self.execute_query(query, (employee_id,))
            return {'success': True, 'rows_affected': rows_affected}
        except Exception as e:
            logger.error(f"직원 삭제 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def search_employees(self, search_term):
        """직원 검색"""
        query = """
            SELECT * FROM employees 
            WHERE name ILIKE %s 
               OR english_name ILIKE %s 
               OR email ILIKE %s
               OR employee_id ILIKE %s
            ORDER BY name
        """
        search_pattern = f"%{search_term}%"
        try:
            return self.execute_query(
                query, 
                (search_pattern, search_pattern, search_pattern, search_pattern), 
                fetch_all=True
            )
        except Exception as e:
            logger.error(f"직원 검색 오류: {e}")
            return []
    
    def get_employees_by_department(self, department):
        """부서별 직원 조회"""
        query = "SELECT * FROM employees WHERE department = %s ORDER BY name"
        try:
            return self.execute_query(query, (department,), fetch_all=True)
        except Exception as e:
            logger.error(f"부서별 직원 조회 오류: {e}")
            return []
    
    def get_employee_statistics(self):
        """직원 통계 정보"""
        query = """
            SELECT 
                COUNT(*) as total_employees,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_employees,
                COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive_employees,
                COUNT(DISTINCT department) as total_departments,
                COUNT(DISTINCT position) as total_positions
            FROM employees
        """
        try:
            return self.execute_query(query, fetch_one=True)
        except Exception as e:
            logger.error(f"직원 통계 조회 오류: {e}")
            return {}
    
    def get_regions(self):
        """모든 지역 목록을 가져옵니다."""
        query = """
            SELECT DISTINCT region FROM employees 
            WHERE region IS NOT NULL AND region != ''
            ORDER BY region
        """
        try:
            result = self.execute_query(query, fetch_all=True)
            return [row['region'] for row in result] if result else []
        except Exception as e:
            logger.error(f"지역 목록 조회 오류: {e}")
            return []
    
    def get_filtered_employees(self, search_term=None, region_filter=None, department_filter=None, status_filter=None):
        """필터링된 직원 목록 조회 (기존 CSV 매니저와 완전 호환)"""
        try:
            base_query = """
                SELECT employee_id, name, english_name, email, phone, 
                       position, department, hire_date, status, region, 
                       access_level, password, created_date, updated_date,
                       gender, nationality, residence_country, city, address,
                       birth_date, salary, salary_currency, driver_license,
                       notes, work_status
                FROM employees
            """
            conditions = []
            params = []
            
            if search_term:
                conditions.append("""
                    (name ILIKE %s OR 
                     english_name ILIKE %s OR 
                     email ILIKE %s OR 
                     employee_id ILIKE %s)
                """)
                search_param = f"%{search_term}%"
                params.extend([search_param, search_param, search_param, search_param])
            
            if region_filter and region_filter != "전체":
                conditions.append("region = %s")
                params.append(region_filter)
            
            if department_filter and department_filter != "전체":
                conditions.append("department = %s")
                params.append(department_filter)
            
            if status_filter and status_filter != "전체":
                conditions.append("status = %s")
                params.append(status_filter)
            
            if conditions:
                query = f"{base_query} WHERE {' AND '.join(conditions)}"
            else:
                query = base_query
            
            query += " ORDER BY name"
            
            result = self.execute_query(query, params, fetch_all=True)
            return pd.DataFrame(result) if result else pd.DataFrame()
            
        except Exception as e:
            logger.error(f"필터링된 직원 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_countries(self):
        """모든 국가 목록을 가져옵니다."""
        query = """
            SELECT DISTINCT residence_country FROM employees 
            WHERE residence_country IS NOT NULL AND residence_country != ''
            ORDER BY residence_country
        """
        try:
            result = self.execute_query(query, fetch_all=True)
            countries = [row['residence_country'] for row in result] if result else []
            
            # 데이터베이스에 국가가 없을 경우 기본 국가 목록 제공 (한국어 우선)
            if not countries:
                countries = ["한국", "베트남", "중국", "태국", "일본", "미국", "인도네시아", "말레이시아", "기타"]
            
            return countries
        except Exception as e:
            logger.error(f"국가 목록 조회 오류: {e}")
            return ["한국", "베트남", "중국", "태국", "일본", "미국", "인도네시아", "말레이시아", "기타"]
    
    def get_cities_by_country(self, country):
        """특정 국가의 도시 목록을 가져옵니다."""
        query = """
            SELECT DISTINCT city FROM employees 
            WHERE residence_country = %s AND city IS NOT NULL AND city != ''
            ORDER BY city
        """
        try:
            result = self.execute_query(query, (country,), fetch_all=True)
            cities = [row['city'] for row in result] if result else []
            
            # 데이터베이스에 도시가 없을 경우 하드코딩된 도시 목록 제공 (한국어/영어 모두 지원)
            if not cities:
                cities_by_country = {
                    # 한국어 국가명
                    "한국": ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "수원", "안산", "고양", "용인", "성남", "부천"],
                    "베트남": ["하노이", "호치민", "다낭", "나트랑", "후에", "비엔호아", "칸토", "부온마투옷", "박닌", "하이퐁"],
                    "중국": ["베이징", "상하이", "광저우", "선전", "청두", "항저우", "난징", "우한", "시안", "충칭"],
                    "태국": ["방콕", "치앙마이", "파타야", "푸켓", "아유타야", "촌부리", "라용", "사뭇프라칸"],
                    "일본": ["도쿄", "오사카", "요코하마", "나고야", "삿포로", "고베", "교토", "후쿠오카"],
                    "미국": ["뉴욕", "로스앤젤레스", "시카고", "휴스턴", "피닉스", "필라델피아"],
                    # 영어 국가명 (기존 데이터 호환)
                    "Korea": ["Seoul", "Busan", "Daegu", "Incheon", "Gwangju", "Daejeon", "Ulsan", "Sejong", "Suwon", "Ansan"],
                    "China": ["Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Chengdu", "Hangzhou", "Nanjing", "Wuhan", "Xian", "Chongqing"],
                    "Thailand": ["Bangkok", "Chiang Mai", "Pattaya", "Phuket", "Ayutthaya", "Chonburi", "Rayong", "Samut Prakan"],
                    "Vietnam": ["Hanoi", "Ho Chi Minh", "Da Nang", "Nha Trang", "Hue", "Bien Hoa", "Can Tho", "Buon Ma Thuot", "Bac Ninh"],
                    "Indonesia": ["Jakarta", "Surabaya", "Bandung", "Medan", "Semarang", "Tangerang", "Depok", "Palembang"],
                    "Malaysia": ["Kuala Lumpur", "Johor Bahru", "Penang", "Ipoh", "Kuching", "Kota Kinabalu", "Shah Alam"],
                    "Japan": ["Tokyo", "Osaka", "Yokohama", "Nagoya", "Sapporo", "Kobe", "Kyoto", "Fukuoka"],
                    "USA": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego"]
                }
                cities = cities_by_country.get(country, [])
            
            return cities
        except Exception as e:
            logger.error(f"국가별 도시 목록 조회 오류: {e}")
            return []
    
    def get_departments(self):
        """모든 부서 목록을 가져옵니다."""
        query = """
            SELECT DISTINCT department FROM employees 
            WHERE department IS NOT NULL AND department != ''
            ORDER BY department
        """
        try:
            result = self.execute_query(query, fetch_all=True)
            return [row['department'] for row in result] if result else []
        except Exception as e:
            logger.error(f"부서 목록 조회 오류: {e}")
            return []
    
    def get_positions(self):
        """모든 직급 목록을 가져옵니다."""
        query = """
            SELECT DISTINCT position FROM employees 
            WHERE position IS NOT NULL AND position != ''
            ORDER BY position
        """
        try:
            result = self.execute_query(query, fetch_all=True)
            return [row['position'] for row in result] if result else []
        except Exception as e:
            logger.error(f"직급 목록 조회 오류: {e}")
            return []