# -*- coding: utf-8 -*-
"""
SQLite 기반 고객 관리 시스템
"""

import sqlite3
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SQLiteCustomerManager:
    def __init__(self, db_path="erp_system.db"):
        """SQLite 기반 고객 매니저 초기화"""
        self.db_path = db_path
    
    def get_connection(self):
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_all_customers(self):
        """모든 고객 정보를 가져옵니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT customer_id, company_name, contact_person, email, phone,
                           country, city, address, business_type, status, notes,
                           created_date, updated_date
                    FROM customers
                    ORDER BY company_name
                ''')
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"고객 목록 조회 오류: {e}")
            return []
    
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
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM customers WHERE customer_id = ?
                ''', (str(customer_id),))
                
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"고객 조회 오류: {e}")
            return None
    
    def add_customer(self, customer_data):
        """새 고객을 추가합니다."""
        try:
            with self.get_connection() as conn:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 고객 ID 자동 생성
                customer_id = self._generate_customer_id(conn)
                
                # 기존 customers 테이블 구조에 맞춰 필요한 정보만 저장
                # 추가 정보는 notes 필드에 JSON 형태로 저장
                additional_info = {
                    'position': customer_data.get('position', ''),
                    'contact_phone': customer_data.get('contact_phone', ''),
                    'contact_email': customer_data.get('contact_email', ''),
                    'detail_address': customer_data.get('detail_address', ''),
                    'customer_grade': customer_data.get('customer_grade', ''),
                    'company_size': customer_data.get('company_size', ''),
                    'annual_revenue': customer_data.get('annual_revenue', 0),
                    'payment_terms': customer_data.get('payment_terms', ''),
                    'website': customer_data.get('website', ''),
                    'secondary_contact': customer_data.get('secondary_contact', ''),
                    'main_products': customer_data.get('main_products', ''),
                    'special_requirements': customer_data.get('special_requirements', ''),
                    'kam_manager': customer_data.get('kam_manager', ''),
                    'relationship_level': customer_data.get('relationship_level', ''),
                    'communication_frequency': customer_data.get('communication_frequency', ''),
                    'last_meeting_date': customer_data.get('last_meeting_date', ''),
                    'potential_value': customer_data.get('potential_value', 0),
                    'decision_maker': customer_data.get('decision_maker', ''),
                    'decision_process': customer_data.get('decision_process', ''),
                    'competitive_status': customer_data.get('competitive_status', ''),
                    'sales_strategy': customer_data.get('sales_strategy', ''),
                    'cross_sell_opportunity': customer_data.get('cross_sell_opportunity', ''),
                    'growth_potential': customer_data.get('growth_potential', ''),
                    'risk_factors': customer_data.get('risk_factors', ''),
                    'user_notes': customer_data.get('notes', '')
                }
                
                # JSON으로 변환하여 notes에 저장
                import json
                notes_json = json.dumps(additional_info, ensure_ascii=False)
                
                conn.execute('''
                    INSERT INTO customers (
                        customer_id, company_name, contact_person, email, phone,
                        country, city, address, business_type, status, notes,
                        created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    customer_id,
                    customer_data.get('company_name', ''),
                    customer_data.get('contact_person', ''),
                    customer_data.get('contact_email', ''),
                    customer_data.get('contact_phone', ''),
                    customer_data.get('country', ''),
                    customer_data.get('city', ''),
                    customer_data.get('address', ''),
                    customer_data.get('business_type', ''),
                    customer_data.get('status', 'active'),
                    notes_json,
                    current_time,
                    current_time
                ))
                
                conn.commit()
                logger.info(f"고객 추가 성공: {customer_id}")
                return customer_id
        except Exception as e:
            logger.error(f"고객 추가 오류: {e}")
            return False
    
    def _generate_customer_id(self, conn):
        """고객 ID를 자동 생성합니다. 기존 C### 형식과 호환되도록 개선"""
        try:
            # 모든 고객 ID 패턴 분석
            cursor = conn.execute('''
                SELECT customer_id FROM customers 
                WHERE customer_id NOT LIKE 'CUST_%' 
                AND customer_id LIKE 'C%' 
                AND LENGTH(customer_id) <= 4
                ORDER BY CAST(SUBSTR(customer_id, 2) AS INTEGER) DESC 
                LIMIT 1
            ''')
            
            last_customer = cursor.fetchone()
            if last_customer:
                try:
                    # C001, C123 형식에서 숫자 부분 추출
                    last_id = last_customer['customer_id']
                    if last_id.startswith('C') and len(last_id) <= 4:
                        number_part = last_id[1:]  # C 제거
                        if number_part.isdigit():
                            last_number = int(number_part)
                            new_number = last_number + 1
                            return f"C{new_number:03d}"
                except (ValueError, IndexError) as e:
                    logger.error(f"기존 ID 파싱 오류: {e}")
            
            # 기존 C### 형식이 없으면 C001부터 시작
            # 또는 최대 번호 + 1로 생성
            cursor = conn.execute('''
                SELECT MAX(CAST(SUBSTR(customer_id, 2) AS INTEGER)) as max_num
                FROM customers 
                WHERE customer_id LIKE 'C%' 
                AND customer_id NOT LIKE 'CUST_%'
                AND LENGTH(customer_id) <= 4
                AND SUBSTR(customer_id, 2) GLOB '[0-9]*'
            ''')
            
            result = cursor.fetchone()
            if result and result['max_num']:
                new_number = result['max_num'] + 1
            else:
                new_number = 1
            
            # C001~C999 형식으로 생성, 999 초과시 C1000 형식
            if new_number <= 999:
                return f"C{new_number:03d}"
            else:
                return f"C{new_number}"
            
        except Exception as e:
            logger.error(f"고객 ID 생성 오류: {e}")
            # 안전한 기본값 반환 - 현재 시간 기반
            import time
            timestamp = int(time.time()) % 1000
            return f"C{timestamp:03d}"
    
    def update_customer(self, customer_id, customer_data):
        """고객 정보를 업데이트합니다."""
        try:
            with self.get_connection() as conn:
                # 기존 고객 확인
                cursor = conn.execute('SELECT * FROM customers WHERE customer_id = ?', (str(customer_id),))
                if not cursor.fetchone():
                    return False
                
                # 업데이트 실행
                conn.execute('''
                    UPDATE customers SET
                        company_name = ?, contact_person = ?, email = ?, phone = ?,
                        country = ?, city = ?, address = ?, business_type = ?,
                        status = ?, notes = ?, updated_date = ?
                    WHERE customer_id = ?
                ''', (
                    customer_data.get('company_name', ''),
                    customer_data.get('contact_person', ''),
                    customer_data.get('email', ''),
                    customer_data.get('phone', ''),
                    customer_data.get('country', ''),
                    customer_data.get('city', ''),
                    customer_data.get('address', ''),
                    customer_data.get('business_type', ''),
                    customer_data.get('status', 'active'),
                    customer_data.get('notes', ''),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    str(customer_id)
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"고객 업데이트 오류: {e}")
            return False
    
    def delete_customer(self, customer_id):
        """고객을 삭제합니다."""
        try:
            with self.get_connection() as conn:
                conn.execute('DELETE FROM customers WHERE customer_id = ?', (str(customer_id),))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"고객 삭제 오류: {e}")
            return False
    
    def get_countries(self):
        """모든 국가 목록을 가져옵니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT DISTINCT country FROM customers 
                    WHERE country IS NOT NULL AND country != ''
                    ORDER BY country
                ''')
                results = cursor.fetchall()
                countries = [row['country'] for row in results]
                
                # 기본 국가 목록 추가 (데이터가 없을 경우)
                default_countries = ["한국", "중국", "태국", "베트남", "인도네시아", "말레이시아"]
                for country in default_countries:
                    if country not in countries:
                        countries.append(country)
                
                return sorted(countries)
        except Exception as e:
            logger.error(f"국가 목록 조회 오류: {e}")
            return ["한국", "중국", "태국", "베트남", "인도네시아", "말레이시아"]
    
    def get_cities_by_country(self, country):
        """특정 국가의 도시 목록을 가져옵니다."""
        try:
            # 하드코딩된 도시 목록 (지리 데이터베이스와 동일)
            cities_by_country = {
                "한국": ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "수원", "화성", "창원", "안산", "고양", "용인", "성남", "부천", "남양주", "안양", "평택", "시흥"],
                "중국": ["베이징", "상하이", "광저우", "선전", "청두", "항저우", "난징", "우한", "시안", "충칭", "톈진", "다롄", "칭다오", "하얼빈", "장춘", "심양"],
                "태국": ["방콕", "치앙마이", "파타야", "푸켓", "아유타야", "촌부리", "라용", "사뭇프라칸", "사뭇사콘", "나콘랏차시마", "우돈타니", "콘켄"],
                "베트남": ["하노이", "호치민", "다낭", "나트랑", "후에", "비엔호아", "칸토", "부온마투옷", "롱쑤옌", "하이퐁", "박닌", "박장"],
                "인도네시아": ["자카르타", "수라바야", "반둥", "메단", "스마랑", "탄게랑", "데포크", "팔렘방", "마카사르", "보고르", "바탐"],
                "말레이시아": ["쿠알라룸푸르", "조호르바루", "페낭", "이포", "쿠칭", "코타키나발루", "샤알람", "클랑", "말라카", "페탈링자야"]
            }
            return cities_by_country.get(country, [])
        except Exception as e:
            logger.error(f"도시 목록 조회 오류: {e}")
            return []
    
    def get_business_types(self):
        """모든 사업 유형 목록을 가져옵니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT DISTINCT business_type FROM customers 
                    WHERE business_type IS NOT NULL AND business_type != ''
                    ORDER BY business_type
                ''')
                results = cursor.fetchall()
                business_types = [row['business_type'] for row in results]
                
                # 기본 사업 유형 추가
                default_types = ["제조업", "무역업", "서비스업", "건설업", "IT/소프트웨어", "유통업", "기타"]
                for btype in default_types:
                    if btype not in business_types:
                        business_types.append(btype)
                
                return sorted(business_types)
        except Exception as e:
            logger.error(f"사업 유형 목록 조회 오류: {e}")
            return ["제조업", "무역업", "서비스업", "건설업", "IT/소프트웨어", "유통업", "기타"]
    
    def get_filtered_customers(self, country_filter=None, city_filter=None, business_type_filter=None, search_term=None):
        """필터링된 고객 목록을 DataFrame으로 가져옵니다."""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT customer_id, company_name, contact_person, email, phone,
                           country, city, address, business_type, status, notes,
                           created_date, updated_date
                    FROM customers
                    WHERE 1=1
                '''
                params = []
                
                if country_filter:
                    query += " AND country = ?"
                    params.append(country_filter)
                
                if city_filter:
                    query += " AND city = ?"
                    params.append(city_filter)
                
                if business_type_filter:
                    query += " AND business_type = ?"
                    params.append(business_type_filter)
                
                if search_term:
                    query += " AND (company_name LIKE ? OR contact_person LIKE ? OR customer_id LIKE ?)"
                    search_param = f"%{search_term}%"
                    params.extend([search_param, search_param, search_param])
                
                query += " ORDER BY company_name"
                
                cursor = conn.execute(query, params)
                results = cursor.fetchall()
                customers_list = [dict(row) for row in results]
                
                if customers_list:
                    return pd.DataFrame(customers_list)
                else:
                    return pd.DataFrame({
                        'customer_id': [],
                        'company_name': [],
                        'contact_person': [],
                        'email': [],
                        'phone': [],
                        'country': [],
                        'city': [],
                        'address': [],
                        'business_type': [],
                        'status': [],
                        'notes': [],
                        'created_date': [],
                        'updated_date': []
                    })
        except Exception as e:
            logger.error(f"필터링된 고객 목록 조회 오류: {e}")
            return pd.DataFrame({
                'customer_id': [],
                'company_name': [],
                'contact_person': [],
                'email': [],
                'phone': [],
                'country': [],
                'city': [],
                'address': [],
                'business_type': [],
                'status': [],
                'notes': [],
                'created_date': [],
                'updated_date': []
            })