# -*- coding: utf-8 -*-
"""
PostgreSQL 기반 고객 관리 시스템
"""

import pandas as pd
from datetime import datetime
import logging
from .base_postgresql_manager import BasePostgreSQLManager

logger = logging.getLogger(__name__)

class PostgreSQLCustomerManager(BasePostgreSQLManager):
    def __init__(self):
        """PostgreSQL 기반 고객 매니저 초기화"""
        super().__init__()
        self.table_name = "customers"
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """customers 테이블 존재 확인 및 생성"""
        create_sql = """
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                customer_id VARCHAR(50) UNIQUE NOT NULL,
                company_name VARCHAR(200) NOT NULL,
                contact_person VARCHAR(100),
                email VARCHAR(255),
                phone VARCHAR(50),
                country VARCHAR(100),
                city VARCHAR(100),
                address TEXT,
                business_type VARCHAR(100),
                status VARCHAR(20) DEFAULT 'active',
                notes TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        self.create_table_if_not_exists(self.table_name, create_sql)
    
    def get_all_customers(self, limit=100):
        """모든 고객 정보를 가져옵니다."""
        query = """
            SELECT customer_id, company_name, contact_person, email, phone,
                   country, city, address, business_type, status, notes,
                   created_date, updated_date
            FROM customers
            ORDER BY company_name
            LIMIT %s
        """
        try:
            return self.execute_query(query, (limit,), fetch_all=True)
        except Exception as e:
            logger.error(f"고객 목록 조회 오류: {e}")
            return []
    
    def get_all_customers_list(self, limit=100):
        """모든 고객 정보를 리스트로 가져옵니다. (SQLite 호환)"""
        return self.get_all_customers(limit)
    
    def get_customers_dataframe(self):
        """고객 정보를 DataFrame으로 가져옵니다."""
        try:
            customers_list = self.get_all_customers()
            return pd.DataFrame(customers_list)
        except Exception as e:
            logger.error(f"고객 DataFrame 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_customer_by_id(self, customer_id):
        """특정 고객 정보를 가져옵니다."""
        query = "SELECT * FROM customers WHERE customer_id = %s"
        try:
            return self.execute_query(query, (str(customer_id),), fetch_one=True)
        except Exception as e:
            logger.error(f"고객 조회 오류: {e}")
            return None
    
    def add_customer(self, customer_data):
        """새 고객을 추가합니다."""
        try:
            current_time = self.format_timestamp()
            
            # 고객 ID 자동 생성
            customer_id = self._generate_customer_id()
            
            query = """
                INSERT INTO customers (
                    customer_id, company_name, contact_person, email, phone,
                    country, city, address, business_type, status, notes,
                    created_date, updated_date
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """
            
            params = (
                customer_id,
                customer_data['company_name'],
                customer_data.get('contact_person'),
                customer_data.get('email'),
                customer_data.get('phone'),
                customer_data.get('country'),
                customer_data.get('city'),
                customer_data.get('address'),
                customer_data.get('business_type'),
                customer_data.get('status', 'active'),
                customer_data.get('notes'),
                current_time,
                current_time
            )
            
            result = self.execute_query(query, params, fetch_one=True)
            return {'success': True, 'customer_id': customer_id, 'id': result['id']}
            
        except Exception as e:
            logger.error(f"고객 추가 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_customer_id(self):
        """고객 ID 자동 생성 (기존 C001~C442 호환성 유지)"""
        try:
            # 기존 C### 형태 ID 조회
            query = """
                SELECT customer_id FROM customers 
                WHERE customer_id ~ '^C[0-9]+$'
                ORDER BY CAST(SUBSTRING(customer_id FROM 2) AS INTEGER) DESC 
                LIMIT 1
            """
            result = self.execute_query(query, fetch_one=True)
            
            if result:
                last_id = result['customer_id']
                number = int(last_id[1:]) + 1
                return f"C{number:03d}"
            else:
                return "C001"
        except Exception as e:
            logger.error(f"고객 ID 생성 오류: {e}")
            return "C001"
    
    def update_customer(self, customer_id, customer_data):
        """고객 정보를 업데이트합니다."""
        try:
            current_time = self.format_timestamp()
            
            # 동적으로 UPDATE 쿼리 생성
            set_clauses = []
            params = []
            
            for field, value in customer_data.items():
                if field not in ['customer_id', 'id']:  # 기본키는 업데이트하지 않음
                    set_clauses.append(f"{field} = %s")
                    params.append(value)
            
            set_clauses.append("updated_date = %s")
            params.append(current_time)
            params.append(customer_id)
            
            query = f"""
                UPDATE customers 
                SET {', '.join(set_clauses)}
                WHERE customer_id = %s
            """
            
            rows_affected = self.execute_query(query, params)
            return {'success': True, 'rows_affected': rows_affected}
            
        except Exception as e:
            logger.error(f"고객 업데이트 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_customer(self, customer_id):
        """고객을 삭제합니다."""
        try:
            query = "DELETE FROM customers WHERE customer_id = %s"
            rows_affected = self.execute_query(query, (customer_id,))
            return {'success': True, 'rows_affected': rows_affected}
        except Exception as e:
            logger.error(f"고객 삭제 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def search_customers(self, search_term):
        """고객 검색"""
        query = """
            SELECT * FROM customers 
            WHERE company_name ILIKE %s 
               OR contact_person ILIKE %s 
               OR email ILIKE %s
               OR customer_id ILIKE %s
            ORDER BY company_name
        """
        search_pattern = f"%{search_term}%"
        try:
            return self.execute_query(
                query, 
                (search_pattern, search_pattern, search_pattern, search_pattern), 
                fetch_all=True
            )
        except Exception as e:
            logger.error(f"고객 검색 오류: {e}")
            return []
    
    def get_customers_by_country(self, country):
        """국가별 고객 조회"""
        query = "SELECT * FROM customers WHERE country = %s ORDER BY company_name"
        try:
            return self.execute_query(query, (country,), fetch_all=True)
        except Exception as e:
            logger.error(f"국가별 고객 조회 오류: {e}")
            return []
    
    def get_customer_statistics(self):
        """고객 통계 정보"""
        query = """
            SELECT 
                COUNT(*) as total_customers,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_customers,
                COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive_customers,
                COUNT(DISTINCT country) as total_countries,
                COUNT(DISTINCT business_type) as total_business_types
            FROM customers
        """
        try:
            return self.execute_query(query, fetch_one=True)
        except Exception as e:
            logger.error(f"고객 통계 조회 오류: {e}")
            return {}
    
    def bulk_add_customers(self, customers_list):
        """대량 고객 추가"""
        try:
            current_time = self.format_timestamp()
            
            # 배치용 데이터 준비
            batch_data = []
            for customer_data in customers_list:
                customer_id = self._generate_customer_id()
                
                batch_data.append((
                    customer_id,
                    customer_data['company_name'],
                    customer_data.get('contact_person'),
                    customer_data.get('email'),
                    customer_data.get('phone'),
                    customer_data.get('country'),
                    customer_data.get('city'),
                    customer_data.get('address'),
                    customer_data.get('business_type'),
                    customer_data.get('status', 'active'),
                    customer_data.get('notes'),
                    current_time,
                    current_time
                ))
            
            # 대량 삽입
            query = """
                INSERT INTO customers (
                    customer_id, company_name, contact_person, email, phone,
                    country, city, address, business_type, status, notes,
                    created_date, updated_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            rows_affected = self.execute_many(query, batch_data)
            return {'success': True, 'rows_affected': rows_affected}
            
        except Exception as e:
            logger.error(f"대량 고객 추가 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_countries(self):
        """모든 국가 목록을 가져옵니다."""
        query = """
            SELECT DISTINCT country FROM customers 
            WHERE country IS NOT NULL AND country != ''
            ORDER BY country
        """
        try:
            result = self.execute_query(query, fetch_all=True)
            return [row[0] for row in result] if result else []
        except Exception as e:
            logger.error(f"국가 목록 조회 오류: {e}")
            return []
    
    def get_filtered_customers(self, country_filter=None, city_filter=None, business_type_filter=None, search_term=None):
        """필터링된 고객 목록을 DataFrame으로 가져옵니다."""
        try:
            base_query = """
                SELECT customer_id, company_name, contact_person, email, phone,
                       country, city, address, business_type, status, notes,
                       created_date, updated_date
                FROM customers
            """
            conditions = []
            params = []
            
            if country_filter and country_filter != "전체":
                conditions.append("country = %s")
                params.append(country_filter)
            
            if city_filter and city_filter != "전체":
                conditions.append("city = %s")
                params.append(city_filter)
            
            if business_type_filter and business_type_filter != "전체":
                conditions.append("business_type = %s")
                params.append(business_type_filter)
            
            if search_term:
                conditions.append("""
                    (company_name ILIKE %s OR 
                     contact_person ILIKE %s OR 
                     email ILIKE %s OR 
                     customer_id ILIKE %s)
                """)
                search_param = f"%{search_term}%"
                params.extend([search_param, search_param, search_param, search_param])
            
            if conditions:
                query = f"{base_query} WHERE {' AND '.join(conditions)}"
            else:
                query = base_query
            
            query += " ORDER BY company_name"
            
            result = self.execute_query(query, params, fetch_all=True)
            return pd.DataFrame(result) if result else pd.DataFrame()
            
        except Exception as e:
            logger.error(f"필터링된 고객 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_business_types(self):
        """모든 사업 유형 목록을 가져옵니다."""
        query = """
            SELECT DISTINCT business_type FROM customers 
            WHERE business_type IS NOT NULL AND business_type != ''
            ORDER BY business_type
        """
        try:
            result = self.execute_query(query, fetch_all=True)
            business_types = [row[0] for row in result] if result else []
            
            # 기본 사업 유형 추가
            default_types = ["제조업", "무역업", "서비스업", "건설업", "IT/소프트웨어", "유통업", "기타"]
            for btype in default_types:
                if btype not in business_types:
                    business_types.append(btype)
            
            return sorted(business_types)
        except Exception as e:
            logger.error(f"사업 유형 목록 조회 오류: {e}")
            return ["제조업", "무역업", "서비스업", "건설업", "IT/소프트웨어", "유통업", "기타"]
    
    def get_cities_by_country(self, country):
        """특정 국가의 도시 목록을 가져옵니다."""
        query = """
            SELECT DISTINCT city FROM customers 
            WHERE country = %s AND city IS NOT NULL AND city != ''
            ORDER BY city
        """
        try:
            result = self.execute_query(query, (country,), fetch_all=True)
            cities = [row[0] for row in result] if result else []
            
            # 데이터베이스에 도시가 없을 경우 하드코딩된 도시 목록 제공
            if not cities:
                cities_by_country = {
                    "한국": ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "수원", "화성", "창원", "안산", "고양", "용인", "성남", "부천", "남양주", "안양", "평택", "시흥"],
                    "중국": ["베이징", "상하이", "광저우", "선전", "청두", "항저우", "난징", "우한", "시안", "충칭", "톈진", "다롄", "칭다오", "하얼빈", "장춘", "심양"],
                    "태국": ["방콕", "치앙마이", "파타야", "푸켓", "아유타야", "촌부리", "라용", "사뭇프라칸", "사뭇사콘", "나콘랏차시마", "우돈타니", "콘켄"],
                    "베트남": ["하노이", "호치민", "다낭", "나트랑", "후에", "비엔호아", "칸토", "부온마투옷", "롱쑤옌", "하이퐁", "박닌", "박장"],
                    "인도네시아": ["자카르타", "수라바야", "반둥", "메단", "스마랑", "탄게랑", "데포크", "팔렘방", "마카사르", "보고르", "바탐"],
                    "말레이시아": ["쿠알라룸푸르", "조호르바루", "페낭", "이포", "쿠칭", "코타키나발루", "샤알람", "클랑", "말라카", "페탈링자야"]
                }
                cities = cities_by_country.get(country, [])
            
            return cities
        except Exception as e:
            logger.error(f"국가별 도시 목록 조회 오류: {e}")
            return []