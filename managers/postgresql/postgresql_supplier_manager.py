# -*- coding: utf-8 -*-
"""
PostgreSQL 공급업체 관리 매니저
"""

from .base_postgresql_manager import BasePostgreSQLManager
from datetime import datetime
import uuid
import pandas as pd

class PostgreSQLSupplierManager(BasePostgreSQLManager):
    """PostgreSQL 공급업체 관리 매니저"""
    
    def __init__(self):
        super().__init__()
        self.init_tables()
    
    def init_tables(self):
        """공급업체 관련 테이블 초기화"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 공급업체 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS suppliers (
                        id SERIAL PRIMARY KEY,
                        supplier_id VARCHAR(50) UNIQUE NOT NULL,
                        company_name VARCHAR(200) NOT NULL,
                        contact_person VARCHAR(100),
                        email VARCHAR(100),
                        phone VARCHAR(50),
                        address TEXT,
                        country VARCHAR(50),
                        city VARCHAR(50),
                        business_type VARCHAR(100),
                        payment_terms VARCHAR(100),
                        credit_limit DECIMAL(15,2) DEFAULT 0,
                        currency VARCHAR(10) DEFAULT 'USD',
                        status VARCHAR(20) DEFAULT 'active',
                        notes TEXT,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                self.log_info("공급업체 테이블 초기화 완료")
                conn.commit()
                
        except Exception as e:
            self.log_error(f"공급업체 테이블 초기화 실패: {e}")
    
    def add_supplier(self, supplier_data):
        """공급업체 추가"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 공급업체 ID 생성
                supplier_id = self._generate_supplier_id()
                
                cursor.execute("""
                    INSERT INTO suppliers (
                        supplier_id, company_name, contact_person, email, phone,
                        address, country, city, business_type, payment_terms,
                        credit_limit, currency, status, notes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    supplier_id,
                    supplier_data.get('company_name'),
                    supplier_data.get('contact_person'),
                    supplier_data.get('email'),
                    supplier_data.get('phone'),
                    supplier_data.get('address'),
                    supplier_data.get('country'),
                    supplier_data.get('city'),
                    supplier_data.get('business_type'),
                    supplier_data.get('payment_terms'),
                    supplier_data.get('credit_limit', 0),
                    supplier_data.get('currency', 'USD'),
                    supplier_data.get('status', 'active'),
                    supplier_data.get('notes', '')
                ))
                
                result = cursor.fetchone()
                conn.commit()
                
                return {
                    'success': True,
                    'supplier_id': supplier_id,
                    'id': result[0] if result else None
                }
                
        except Exception as e:
            self.log_error(f"공급업체 추가 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_all_suppliers(self):
        """모든 공급업체 조회 - DataFrame 반환"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM suppliers 
                    ORDER BY company_name
                """)
                
                columns = [desc[0] for desc in cursor.description]
                results = cursor.fetchall()
                
                # pandas DataFrame으로 반환
                df = pd.DataFrame(results, columns=columns)
                return df
                
        except Exception as e:
            self.log_error(f"공급업체 조회 실패: {e}")
            return pd.DataFrame()
    
    def get_supplier_by_id(self, supplier_id):
        """공급업체 ID로 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM suppliers WHERE supplier_id = %s
                """, (supplier_id,))
                
                result = cursor.fetchone()
                if result:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, result))
                return None
                
        except Exception as e:
            self.log_error(f"공급업체 조회 실패: {e}")
            return None
    
    def update_supplier(self, supplier_id, supplier_data):
        """공급업체 정보 수정"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE suppliers SET
                        company_name = %s,
                        contact_person = %s,
                        email = %s,
                        phone = %s,
                        address = %s,
                        country = %s,
                        city = %s,
                        business_type = %s,
                        payment_terms = %s,
                        credit_limit = %s,
                        currency = %s,
                        status = %s,
                        notes = %s,
                        updated_date = CURRENT_TIMESTAMP
                    WHERE supplier_id = %s
                """, (
                    supplier_data.get('company_name'),
                    supplier_data.get('contact_person'),
                    supplier_data.get('email'),
                    supplier_data.get('phone'),
                    supplier_data.get('address'),
                    supplier_data.get('country'),
                    supplier_data.get('city'),
                    supplier_data.get('business_type'),
                    supplier_data.get('payment_terms'),
                    supplier_data.get('credit_limit'),
                    supplier_data.get('currency'),
                    supplier_data.get('status'),
                    supplier_data.get('notes'),
                    supplier_id
                ))
                
                conn.commit()
                return {'success': True}
                
        except Exception as e:
            self.log_error(f"공급업체 수정 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_supplier(self, supplier_id):
        """공급업체 삭제"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM suppliers WHERE supplier_id = %s", (supplier_id,))
                conn.commit()
                return {'success': True}
                
        except Exception as e:
            self.log_error(f"공급업체 삭제 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_supplier_statistics(self):
        """공급업체 통계 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 총 공급업체 수
                cursor.execute("SELECT COUNT(*) FROM suppliers")
                total_suppliers = cursor.fetchone()[0]
                
                # 활성 공급업체 수
                cursor.execute("SELECT COUNT(*) FROM suppliers WHERE status = 'active'")
                active_suppliers = cursor.fetchone()[0]
                
                # 국가별 공급업체 수
                cursor.execute("""
                    SELECT country, COUNT(*) 
                    FROM suppliers 
                    WHERE country IS NOT NULL 
                    GROUP BY country
                """)
                countries = cursor.fetchall()
                
                return {
                    'total_suppliers': total_suppliers,
                    'active_suppliers': active_suppliers,
                    'countries': dict(countries) if countries else {}
                }
                
        except Exception as e:
            self.log_error(f"공급업체 통계 조회 실패: {e}")
            return {
                'total_suppliers': 0,
                'active_suppliers': 0,
                'countries': {}
            }
    
    def _generate_supplier_id(self):
        """공급업체 ID 생성"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT supplier_id FROM suppliers 
                    WHERE supplier_id LIKE 'SUP%' 
                    ORDER BY supplier_id DESC LIMIT 1
                """)
                
                result = cursor.fetchone()
                if result:
                    last_id = result[0]
                    number = int(last_id[3:]) + 1
                    return f"SUP{number:06d}"
                else:
                    return "SUP000001"
                    
        except Exception as e:
            self.log_error(f"공급업체 ID 생성 오류: {e}")
            return f"SUP{str(uuid.uuid4())[:6].upper()}"
    
    def search_suppliers(self, search_term):
        """공급업체 검색"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM suppliers 
                    WHERE company_name ILIKE %s 
                       OR contact_person ILIKE %s 
                       OR email ILIKE %s
                    ORDER BY company_name
                """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
                
                columns = [desc[0] for desc in cursor.description]
                suppliers = []
                
                for row in cursor.fetchall():
                    supplier = dict(zip(columns, row))
                    suppliers.append(supplier)
                
                return suppliers
                
        except Exception as e:
            self.log_error(f"공급업체 검색 실패: {e}")
            return []
