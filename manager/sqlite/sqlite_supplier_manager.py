# -*- coding: utf-8 -*-
"""
SQLite 기반 공급업체 관리 시스템
"""

import sqlite3
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SQLiteSupplierManager:
    def __init__(self, db_path="erp_system.db"):
        """SQLite 기반 공급업체 매니저 초기화"""
        self.db_path = db_path
        self.init_tables()
    
    def get_connection(self):
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_tables(self):
        """공급업체 테이블 초기화"""
        with self.get_connection() as conn:
            # suppliers 테이블 (database_manager.py에 이미 정의됨, 필요시 확장)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id TEXT UNIQUE NOT NULL,
                    company_name TEXT NOT NULL,
                    contact_person TEXT,
                    contact_phone TEXT,
                    contact_email TEXT,
                    address TEXT,
                    country TEXT,
                    city TEXT,
                    business_type TEXT,
                    tax_id TEXT,
                    bank_info TEXT,
                    payment_terms TEXT,
                    lead_time_days INTEGER,
                    minimum_order_amount REAL,
                    currency TEXT DEFAULT 'VND',
                    rating REAL DEFAULT 3.0,
                    notes TEXT,
                    status TEXT DEFAULT '활성',
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("공급업체 테이블 초기화 완료")
    
    def generate_supplier_id(self):
        """공급업체 ID를 생성합니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('SELECT COUNT(*) FROM suppliers')
                count = cursor.fetchone()[0]
                next_num = count + 1
                return f'SUP{next_num:03d}'
                
        except Exception as e:
            logger.error(f"공급업체 ID 생성 오류: {e}")
            return f'S{datetime.now().strftime("%m%d%H%M")}'
    
    def add_supplier(self, supplier_data):
        """새 공급업체를 추가합니다."""
        try:
            with self.get_connection() as conn:
                # 중복 확인 (회사명으로 확인)
                cursor = conn.execute('SELECT COUNT(*) FROM suppliers WHERE company_name = ?', 
                                    (supplier_data['company_name'],))
                
                if cursor.fetchone()[0] > 0:
                    return False
                
                # 공급업체 ID가 없으면 생성
                if 'supplier_id' not in supplier_data or not supplier_data['supplier_id']:
                    supplier_data['supplier_id'] = self.generate_supplier_id()
                
                # 기본값 설정
                supplier_data.setdefault('status', '활성')
                supplier_data.setdefault('rating', 3.0)
                supplier_data.setdefault('currency', 'VND')
                supplier_data.setdefault('lead_time_days', 30)
                supplier_data.setdefault('minimum_order_amount', 0)
                
                # 데이터 삽입
                conn.execute('''
                    INSERT INTO suppliers (
                        supplier_id, company_name, contact_person, contact_phone, contact_email,
                        address, country, city, business_type, tax_id, bank_info, payment_terms,
                        lead_time_days, minimum_order_amount, currency, rating, notes, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    supplier_data['supplier_id'],
                    supplier_data['company_name'],
                    supplier_data.get('contact_person', ''),
                    supplier_data.get('contact_phone', ''),
                    supplier_data.get('contact_email', ''),
                    supplier_data.get('address', ''),
                    supplier_data.get('country', ''),
                    supplier_data.get('city', ''),
                    supplier_data.get('business_type', ''),
                    supplier_data.get('tax_id', ''),
                    supplier_data.get('bank_info', ''),
                    supplier_data.get('payment_terms', ''),
                    int(supplier_data.get('lead_time_days', 30)),
                    float(supplier_data.get('minimum_order_amount', 0)),
                    supplier_data.get('currency', 'VND'),
                    float(supplier_data.get('rating', 3.0)),
                    supplier_data.get('notes', ''),
                    supplier_data.get('status', '활성')
                ))
                
                conn.commit()
                logger.info(f"공급업체 추가 성공: {supplier_data['supplier_id']}")
                return True
                
        except Exception as e:
            logger.error(f"공급업체 추가 오류: {str(e)}")
            return False
    
    def get_all_suppliers(self):
        """모든 공급업체 정보를 DataFrame으로 가져옵니다."""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT 
                        supplier_id, company_name, contact_person, contact_phone, contact_email,
                        address, country, city, business_type, tax_id, bank_info, payment_terms,
                        lead_time_days, minimum_order_amount, currency, rating, notes, status,
                        created_date, updated_date
                    FROM suppliers
                    ORDER BY company_name
                '''
                
                df = pd.read_sql_query(query, conn)
                return df
                
        except Exception as e:
            logger.error(f"공급업체 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_supplier_by_id(self, supplier_id):
        """특정 공급업체 정보 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('SELECT * FROM suppliers WHERE supplier_id = ?', (supplier_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"공급업체 조회 오류: {str(e)}")
            return None
    
    def update_supplier(self, supplier_id, supplier_data):
        """공급업체 정보를 업데이트합니다."""
        try:
            with self.get_connection() as conn:
                # 업데이트할 필드들 동적 생성
                fields = []
                values = []
                
                for key, value in supplier_data.items():
                    if key != 'supplier_id':  # ID는 업데이트하지 않음
                        fields.append(f"{key} = ?")
                        values.append(value)
                
                if not fields:
                    return False
                
                # 업데이트 쿼리 실행
                values.append(supplier_id)  # WHERE 절용
                query = f"UPDATE suppliers SET {', '.join(fields)}, updated_date = CURRENT_TIMESTAMP WHERE supplier_id = ?"
                
                conn.execute(query, values)
                conn.commit()
                
                logger.info(f"공급업체 업데이트 성공: {supplier_id}")
                return True
                
        except Exception as e:
            logger.error(f"공급업체 업데이트 오류: {str(e)}")
            return False
    
    def delete_supplier(self, supplier_id):
        """공급업체를 삭제합니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('DELETE FROM suppliers WHERE supplier_id = ?', (supplier_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"공급업체 삭제 성공: {supplier_id}")
                    return True
                else:
                    return False
                    
        except Exception as e:
            logger.error(f"공급업체 삭제 오류: {str(e)}")
            return False
    
    def search_suppliers(self, search_term=""):
        """공급업체 검색 (회사명, 연락처로 검색)"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT * FROM suppliers 
                    WHERE company_name LIKE ? OR contact_person LIKE ? OR contact_email LIKE ?
                    ORDER BY company_name
                '''
                
                search_pattern = f"%{search_term}%"
                df = pd.read_sql_query(query, conn, params=(search_pattern, search_pattern, search_pattern))
                return df
                
        except Exception as e:
            logger.error(f"공급업체 검색 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_suppliers_by_country(self, country):
        """특정 국가의 공급업체들 조회"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT * FROM suppliers 
                    WHERE country = ?
                    ORDER BY company_name
                '''
                
                df = pd.read_sql_query(query, conn, params=(country,))
                return df
                
        except Exception as e:
            logger.error(f"국가별 공급업체 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_suppliers_by_business_type(self, business_type):
        """특정 사업 유형의 공급업체들 조회"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT * FROM suppliers 
                    WHERE business_type = ?
                    ORDER BY company_name
                '''
                
                df = pd.read_sql_query(query, conn, params=(business_type,))
                return df
                
        except Exception as e:
            logger.error(f"사업 유형별 공급업체 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_active_suppliers(self):
        """활성 상태의 공급업체들만 조회"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT * FROM suppliers 
                    WHERE status = '활성'
                    ORDER BY company_name
                '''
                
                df = pd.read_sql_query(query, conn)
                return df
                
        except Exception as e:
            logger.error(f"활성 공급업체 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_supplier_statistics(self):
        """공급업체 통계 정보"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT 
                        COUNT(*) as total_suppliers,
                        SUM(CASE WHEN status = '활성' THEN 1 ELSE 0 END) as active_suppliers,
                        SUM(CASE WHEN status = '비활성' THEN 1 ELSE 0 END) as inactive_suppliers,
                        COUNT(DISTINCT country) as countries_count,
                        AVG(rating) as average_rating,
                        AVG(lead_time_days) as average_lead_time
                    FROM suppliers
                ''')
                
                row = cursor.fetchone()
                return dict(row) if row else {}
                
        except Exception as e:
            logger.error(f"공급업체 통계 조회 오류: {str(e)}")
            return {}
    
    def update_supplier_rating(self, supplier_id, new_rating, notes=""):
        """공급업체 평가 업데이트"""
        try:
            rating = float(new_rating)
            if not (1.0 <= rating <= 5.0):
                return False
            
            with self.get_connection() as conn:
                conn.execute('''
                    UPDATE suppliers 
                    SET rating = ?, notes = ?, updated_date = CURRENT_TIMESTAMP 
                    WHERE supplier_id = ?
                ''', (rating, notes, supplier_id))
                
                conn.commit()
                logger.info(f"공급업체 평가 업데이트 성공: {supplier_id} -> {rating}")
                return True
                
        except Exception as e:
            logger.error(f"공급업체 평가 업데이트 오류: {str(e)}")
            return False
    
    def get_top_rated_suppliers(self, limit=10):
        """평가가 높은 공급업체들 조회"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT * FROM suppliers 
                    WHERE status = '활성'
                    ORDER BY rating DESC, company_name
                    LIMIT ?
                '''
                
                df = pd.read_sql_query(query, conn, params=(limit,))
                return df
                
        except Exception as e:
            logger.error(f"우수 공급업체 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_countries(self):
        """공급업체 국가 목록 조회 (기존 CSV 매니저와 호환)"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT DISTINCT country FROM suppliers 
                    WHERE country IS NOT NULL AND country != ''
                    ORDER BY country
                '''
                
                cursor = conn.execute(query)
                countries = [row[0] for row in cursor.fetchall()]
                return countries
                
        except Exception as e:
            logger.error(f"국가 목록 조회 오류: {str(e)}")
            return []
    
    def get_cities_by_country(self, country):
        """특정 국가의 도시 목록 조회"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT DISTINCT city FROM suppliers 
                    WHERE country = ? AND city IS NOT NULL AND city != ''
                    ORDER BY city
                '''
                
                cursor = conn.execute(query, (country,))
                cities = [row[0] for row in cursor.fetchall()]
                return cities
                
        except Exception as e:
            logger.error(f"도시 목록 조회 오류: {str(e)}")
            return []
    
    def get_business_types(self):
        """사업 유형 목록 조회"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT DISTINCT business_type FROM suppliers 
                    WHERE business_type IS NOT NULL AND business_type != ''
                    ORDER BY business_type
                '''
                
                cursor = conn.execute(query)
                types = [row[0] for row in cursor.fetchall()]
                return types
                
        except Exception as e:
            logger.error(f"사업 유형 목록 조회 오류: {str(e)}")
            return []
    
    def get_filtered_suppliers(self, country_filter=None, business_type_filter=None, search_term=None, status_filter=None):
        """필터링된 공급업체 목록 조회 (기존 CSV 매니저와 완전 호환)"""
        try:
            with self.get_connection() as conn:
                base_query = "SELECT * FROM suppliers"
                conditions = []
                params = []
                
                # 기본적으로 활성 상태만 조회
                if status_filter:
                    conditions.append("status = ?")
                    params.append(status_filter)
                else:
                    conditions.append("status = '활성'")
                
                if country_filter and country_filter != 'All':
                    conditions.append("country = ?")
                    params.append(country_filter)
                
                if business_type_filter and business_type_filter != 'All':
                    conditions.append("business_type = ?")
                    params.append(business_type_filter)
                
                if search_term:
                    conditions.append("(company_name LIKE ? OR contact_person LIKE ? OR supplier_id LIKE ?)")
                    search_param = f"%{search_term}%"
                    params.extend([search_param, search_param, search_param])
                
                if conditions:
                    query = base_query + " WHERE " + " AND ".join(conditions)
                else:
                    query = base_query
                
                query += " ORDER BY company_name"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"필터링된 공급업체 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_all_suppliers(self):
        """모든 공급업체 조회 (기존 매니저와 호환성)"""
        return self.get_filtered_suppliers()
    
    def search_suppliers(self, search_term=""):
        """공급업체 검색 (기존 매니저와 호환성)"""
        return self.get_filtered_suppliers(search_term=search_term)