"""
SQLite 기반 고객 관리자
기존 customer_manager.py의 SQLite 버전
"""
import sqlite3
import pandas as pd
from datetime import datetime
from .database_manager import DatabaseManager

class DBCustomerManager:
    def __init__(self, db_path="erp_system.db"):
        """SQLite 기반 고객 관리자 초기화"""
        self.db_manager = DatabaseManager(db_path)
    
    def get_all_customers(self):
        """모든 고객 정보 반환"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM customers ORDER BY company_name")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_customer_by_id(self, customer_id):
        """특정 고객 정보 반환"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def add_customer(self, customer_data):
        """새 고객 추가"""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute('''
                    INSERT INTO customers 
                    (customer_id, company_name, contact_person, email, phone, 
                     country, city, address, business_type, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    customer_data.get('customer_id'),
                    customer_data.get('company_name'),
                    customer_data.get('contact_person', ''),
                    customer_data.get('email', ''),
                    customer_data.get('phone', ''),
                    customer_data.get('country', ''),
                    customer_data.get('city', ''),
                    customer_data.get('address', ''),
                    customer_data.get('business_type', ''),
                    customer_data.get('status', 'active'),
                    customer_data.get('notes', '')
                ))
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # 중복 ID
        except Exception as e:
            print(f"고객 추가 오류: {e}")
            return False
    
    def update_customer(self, customer_id, customer_data):
        """고객 정보 업데이트"""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute('''
                    UPDATE customers 
                    SET company_name=?, contact_person=?, email=?, phone=?, 
                        country=?, city=?, address=?, business_type=?, 
                        status=?, notes=?, updated_date=CURRENT_TIMESTAMP
                    WHERE customer_id=?
                ''', (
                    customer_data.get('company_name'),
                    customer_data.get('contact_person', ''),
                    customer_data.get('email', ''),
                    customer_data.get('phone', ''),
                    customer_data.get('country', ''),
                    customer_data.get('city', ''),
                    customer_data.get('address', ''),
                    customer_data.get('business_type', ''),
                    customer_data.get('status', 'active'),
                    customer_data.get('notes', ''),
                    customer_id
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"고객 업데이트 오류: {e}")
            return False
    
    def delete_customer(self, customer_id):
        """고객 삭제 (비활성화)"""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute('''
                    UPDATE customers 
                    SET status='inactive', updated_date=CURRENT_TIMESTAMP
                    WHERE customer_id=?
                ''', (customer_id,))
                conn.commit()
            return True
        except Exception as e:
            print(f"고객 삭제 오류: {e}")
            return False
    
    def get_countries(self):
        """모든 국가 목록 반환"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT DISTINCT country FROM customers WHERE country IS NOT NULL AND country != ''")
            return [row[0] for row in cursor.fetchall()]
    
    def get_cities(self, country=None):
        """도시 목록 반환 (국가별 필터링 가능)"""
        query = "SELECT DISTINCT city FROM customers WHERE city IS NOT NULL AND city != ''"
        params = []
        
        if country:
            query += " AND country = ?"
            params.append(country)
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [row[0] for row in cursor.fetchall()]
    
    def get_business_types(self):
        """모든 사업 유형 목록 반환"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT DISTINCT business_type FROM customers WHERE business_type IS NOT NULL AND business_type != ''")
            return [row[0] for row in cursor.fetchall()]
    
    def get_filtered_customers(self, country_filter=None, city_filter=None, 
                             business_type_filter=None, status_filter=None, search_term=None):
        """필터링된 고객 목록 반환"""
        query = "SELECT * FROM customers WHERE 1=1"
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
        
        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)
        
        if search_term:
            query += " AND (company_name LIKE ? OR contact_person LIKE ? OR customer_id LIKE ?)"
            search_param = f"%{search_term}%"
            params.extend([search_param, search_param, search_param])
        
        query += " ORDER BY company_name"
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_customer_count(self):
        """총 고객 수 반환"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM customers WHERE status = 'active'")
            return cursor.fetchone()[0]
    
    def get_customer_statistics(self):
        """고객 통계 반환"""
        with self.db_manager.get_connection() as conn:
            stats = {}
            
            # 총 고객 수
            cursor = conn.execute("SELECT COUNT(*) FROM customers WHERE status = 'active'")
            stats['total_customers'] = cursor.fetchone()[0]
            
            # 국가별 통계
            cursor = conn.execute('''
                SELECT country, COUNT(*) 
                FROM customers 
                WHERE status = 'active' AND country IS NOT NULL AND country != ''
                GROUP BY country
                ORDER BY COUNT(*) DESC
            ''')
            stats['country_distribution'] = dict(cursor.fetchall())
            
            # 사업 유형별 통계
            cursor = conn.execute('''
                SELECT business_type, COUNT(*) 
                FROM customers 
                WHERE status = 'active' AND business_type IS NOT NULL AND business_type != ''
                GROUP BY business_type
            ''')
            stats['business_type_distribution'] = dict(cursor.fetchall())
            
            # 도시별 통계 (상위 10개)
            cursor = conn.execute('''
                SELECT city, COUNT(*) 
                FROM customers 
                WHERE status = 'active' AND city IS NOT NULL AND city != ''
                GROUP BY city
                ORDER BY COUNT(*) DESC
                LIMIT 10
            ''')
            stats['city_distribution'] = dict(cursor.fetchall())
            
            return stats
    
    def search_customers(self, search_term):
        """고객 검색"""
        return self.get_filtered_customers(search_term=search_term)
    
    def get_customers_by_country(self, country):
        """특정 국가의 고객 목록"""
        return self.get_filtered_customers(country_filter=country)
    
    def get_customers_by_business_type(self, business_type):
        """특정 사업 유형의 고객 목록"""
        return self.get_filtered_customers(business_type_filter=business_type)
    
    def export_to_dataframe(self):
        """고객 데이터를 DataFrame으로 반환"""
        customers = self.get_all_customers()
        return pd.DataFrame(customers)
    
    def generate_customer_id(self):
        """새 고객 ID 생성"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT MAX(CAST(SUBSTR(customer_id, 2) AS INTEGER)) FROM customers WHERE customer_id LIKE 'C%'")
            max_id = cursor.fetchone()[0]
            if max_id:
                return f"C{max_id + 1:04d}"
            else:
                return "C0001"